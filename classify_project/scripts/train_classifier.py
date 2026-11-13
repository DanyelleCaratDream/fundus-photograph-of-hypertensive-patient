# -*- coding: utf-8 -*-
"""HR 四级分级分类器 —— 用于分辨率消融实验（128 / 256 / 512 哪个够用）。

设计取舍（为了让"分辨率"成为唯一变量）：
  · 训练时**不做数据增强**，只 resize + 归一化
  · 固定用数据集自带的 train/val/test 划分（不重新切分，保持与老师协议一致）
  · 多个随机种子重复训练，报告 均值 ± 标准差

用法：
    python classify_project/scripts/train_classifier.py --data fundus/HRSG_4_758_square --size 256
    python classify_project/scripts/train_classifier.py --data ... --size 256 --seeds 42 52 62
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import (balanced_accuracy_score, cohen_kappa_score,
                             confusion_matrix, f1_score)
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import models, transforms

Image.MAX_IMAGE_PIXELS = None
CLASSES = ["normal", "mild", "moderate", "severe"]   # 有序！0<1<2<3
NUM_CLASSES = len(CLASSES)


class FundusFolder(Dataset):
    """按 {root}/{split}/{class}/*.jpg 读取。"""

    def __init__(self, root: Path, split: str, size: int, train: bool):
        self.items: list[tuple[Path, int]] = []
        for ci, cname in enumerate(CLASSES):
            d = root / split / cname
            if not d.is_dir():
                continue
            for f in sorted(d.iterdir()):
                if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"):
                    self.items.append((f, ci))
        self.size = size
        # 训练/评估用同一套预处理（只是缩放+归一化），保证分辨率是唯一变量
        self.tf = transforms.Compose([
            transforms.Resize((size, size), antialias=True),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i: int):
        path, label = self.items[i]
        with Image.open(path) as im:
            im = im.convert("RGB")
        return self.tf(im), label


def build_model(size: int, pretrained: bool = True) -> nn.Module:
    weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
    m = models.resnet18(weights=weights)
    m.fc = nn.Linear(m.fc.in_features, NUM_CLASSES)
    return m


def metrics_from_preds(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    severe = CLASSES.index("severe")
    rec = {}
    for i, c in enumerate(CLASSES):
        m = y_true == i
        rec[f"recall_{c}"] = float((y_pred[m] == i).mean()) if m.any() else float("nan")
    return {
        "acc": float((y_true == y_pred).mean()),
        "balanced_acc": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "qwk": float(cohen_kappa_score(y_true, y_pred, weights="quadratic")),
        "severe_recall": rec["recall_severe"],
        "n": int(len(y_true)),
        "confusion": confusion_matrix(y_true, y_pred, labels=range(NUM_CLASSES)).tolist(),
    }


@torch.no_grad()
def collect_logits(model, loader, device) -> tuple[np.ndarray, np.ndarray]:
    """返回 (y_true, logits)，供 logit adjustment 在 val/test 上复用。"""
    model.eval()
    ys, zs = [], []
    for x, y in loader:
        x = x.to(device)
        zs.append(model(x).cpu().numpy())
        ys.append(y.numpy())
    return np.concatenate(ys), np.concatenate(zs)


def apply_logit_adjust(logits: np.ndarray, prior: np.ndarray, tau: float) -> np.ndarray:
    """post-hoc logit adjustment：z - tau * log(pi)。"""
    return logits - tau * np.log(np.clip(prior, 1e-12, None))


def tune_tau(logits: np.ndarray, y_true: np.ndarray, prior: np.ndarray,
             grid=(0.0, 0.25, 0.5, 0.75, 1.0)) -> tuple[float, dict]:
    """只在 val 上选 tau；返回 (tau, 对应 val 指标)。"""
    best_tau, best = 0.0, {"qwk": -2.0}
    for tau in grid:
        pred = apply_logit_adjust(logits, prior, tau).argmax(1)
        m = metrics_from_preds(y_true, pred)
        if m["qwk"] > best["qwk"] + 1e-12:
            best_tau, best = float(tau), m
    return best_tau, best


def class_counts(items) -> np.ndarray:
    return np.bincount([y for _, y in items], minlength=NUM_CLASSES).astype(np.float64)


def make_balanced_sampler(items) -> WeightedRandomSampler:
    """按逆频率采样，供 DRC 阶段2 用。"""
    cnt = class_counts(items)
    w = torch.tensor([1.0 / cnt[y] for _, y in items], dtype=torch.double)
    return WeightedRandomSampler(w, num_samples=len(w), replacement=True)


def freeze_backbone_reset_head(model: nn.Module, device: str) -> nn.Module:
    """DRC 阶段2：冻结全部参数，重初始化并只训练 fc。"""
    for p in model.parameters():
        p.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES).to(device)
    for p in model.fc.parameters():
        p.requires_grad = True
    return model


@torch.no_grad()
def evaluate(model, loader, device) -> tuple[dict, np.ndarray, np.ndarray]:
    y_true, z = collect_logits(model, loader, device)
    y_pred = z.argmax(1)
    return metrics_from_preds(y_true, y_pred), y_true, y_pred


def train_one(size: int, root: Path, seed: int, epochs: int, bs: int,
              lr: float, weight_decay: float, device: str, weighted: bool,
              num_workers: int, quiet: bool, logit_adjust: bool = False,
              drc: bool = False, drc_stage2_epochs: int = 10,
              drc_stage2_lr: float = 1e-3) -> dict:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)

    tr = FundusFolder(root, "train", size, train=True)
    va = FundusFolder(root, "val", size, train=False)
    te = FundusFolder(root, "test", size, train=False)
    if not tr.items or not te.items:
        raise RuntimeError(f"数据为空：train={len(tr)} test={len(te)}")

    dl_tr = DataLoader(tr, batch_size=bs, shuffle=True, num_workers=num_workers,
                       pin_memory=True, drop_last=False)
    dl_va = DataLoader(va, batch_size=bs, shuffle=False, num_workers=num_workers)
    dl_te = DataLoader(te, batch_size=bs, shuffle=False, num_workers=num_workers)

    model = build_model(size).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    if weighted:
        cnt = class_counts(tr.items).astype(np.float32)
        w = torch.tensor((cnt.sum() / (cnt + 1e-6)) / NUM_CLASSES, device=device)
        crit = nn.CrossEntropyLoss(weight=w)
    else:
        crit = nn.CrossEntropyLoss()

    best = {"qwk": -2.0}
    best_state = None
    for ep in range(1, epochs + 1):
        model.train()
        tot = 0.0
        for x, y in dl_tr:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            loss = crit(model(x), y)
            loss.backward(); opt.step()
            tot += loss.item() * len(y)
        sched.step()
        if ep % 5 == 0 or ep == epochs:
            m, _, _ = evaluate(model, dl_va, device) if len(va) else ({"qwk": 0}, None, None)
            if not quiet:
                print(f"      seed{seed} ep{ep:3d}  train_loss {tot/len(tr):.4f}  val_qwk {m['qwk']:.4f}")
            if m["qwk"] > best["qwk"]:
                best = m
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    extra = {"mode": "drc" if drc else ("logit_adjust" if logit_adjust else "a0")}

    # ---- A2：DRC 阶段2——冻结骨干，重初始化分类头，类别平衡采样 ----
    if drc:
        freeze_backbone_reset_head(model, device)
        dl_bal = DataLoader(tr, batch_size=bs, sampler=make_balanced_sampler(tr.items),
                            num_workers=num_workers, pin_memory=True, drop_last=False)
        opt2 = torch.optim.AdamW(model.fc.parameters(), lr=drc_stage2_lr,
                                 weight_decay=weight_decay)
        crit2 = nn.CrossEntropyLoss()   # 采样已平衡，不再加权
        best2 = {"qwk": -2.0}
        best2_state = None
        for ep in range(1, drc_stage2_epochs + 1):
            model.train()
            # 冻结 BN 统计：backbone 保持 eval，只让 fc 更新
            for m_ in model.modules():
                if isinstance(m_, nn.BatchNorm2d):
                    m_.eval()
            tot = 0.0
            for x, y in dl_bal:
                x, y = x.to(device), y.to(device)
                opt2.zero_grad(set_to_none=True)
                loss = crit2(model(x), y)
                loss.backward(); opt2.step()
                tot += loss.item() * len(y)
            if len(va):
                m, _, _ = evaluate(model, dl_va, device)
                if not quiet:
                    print(f"      seed{seed} drc-ep{ep:3d}  loss {tot/len(tr):.4f}  val_qwk {m['qwk']:.4f}")
                if m["qwk"] > best2["qwk"]:
                    best2 = m
                    best2_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        if best2_state is not None:
            model.load_state_dict(best2_state)
        extra["drc_stage2_epochs"] = drc_stage2_epochs
        extra["drc_stage2_lr"] = drc_stage2_lr
        extra["drc_val_qwk"] = best2["qwk"]

    # ---- A1：post-hoc logit adjustment（tau 只在 val 上选）／测试集只评一次 ----
    if logit_adjust:
        prior = class_counts(tr.items) / class_counts(tr.items).sum()
        if len(va):
            y_va, z_va = collect_logits(model, dl_va, device)
            tau, va_m = tune_tau(z_va, y_va, prior)
            extra["tau"] = tau
            extra["val_qwk_adjusted"] = va_m["qwk"]
        else:
            tau = 0.0
            extra["tau"] = tau
        y_true, z_te = collect_logits(model, dl_te, device)
        te_m = metrics_from_preds(y_true, apply_logit_adjust(z_te, prior, tau).argmax(1))
    else:
        te_m, y_true, y_pred = evaluate(model, dl_te, device)

    te_m["seed"] = seed
    te_m["val_qwk"] = best["qwk"] if not drc else extra.get("drc_val_qwk", best["qwk"])
    te_m["train_n"] = len(tr)
    te_m["test_n"] = len(te)
    te_m.update(extra)
    return te_m


def main() -> int:
    ap = argparse.ArgumentParser(description="HR 分级分类器（分辨率消融）")
    ap.add_argument("--data", required=True, help="正方形数据集根目录")
    ap.add_argument("--size", type=int, required=True, help="输入分辨率")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 52, 62])
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--no-weighted", action="store_true", help="不加类别权重")
    ap.add_argument("--no-pretrained", action="store_true", help="不用 ImageNet 预训练")
    ap.add_argument("--logit-adjust", action="store_true",
                    help="A1：post-hoc logit adjustment，tau 只在 val 上选")
    ap.add_argument("--drc", action="store_true",
                    help="A2：DRC 两阶段（冻结骨干 + 类平衡重训分类头）")
    ap.add_argument("--drc-stage2-epochs", type=int, default=10,
                    help="DRC 阶段2 轮数（默认 10）")
    ap.add_argument("--drc-stage2-lr", type=float, default=1e-3,
                    help="DRC 阶段2 分类头学习率（默认 1e-3）")
    ap.add_argument("--num-workers", type=int, default=4)
    ap.add_argument("--out", default=None, help="结果 JSON 路径")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    root = Path(args.data)
    if not root.is_dir():
        print(f"错误：数据目录不存在 {root}\n先跑 prep_square.py", file=sys.stderr)
        return 1

    device = "cuda" if torch.cuda.is_available() else "cpu"
    weighted = not args.no_weighted

    print(f"{'='*66}")
    print(f"  分辨率 {args.size}×{args.size}   设备 {device}   种子 {args.seeds}")
    print(f"  数据 {root}")
    print(f"{'='*66}")

    runs = []
    for s in args.seeds:
        t0 = time.time()
        try:
            r = train_one(args.size, root, s, args.epochs, args.batch_size, args.lr,
                          args.weight_decay, device, weighted, args.num_workers, args.quiet,
                          logit_adjust=args.logit_adjust, drc=args.drc,
                          drc_stage2_epochs=args.drc_stage2_epochs,
                          drc_stage2_lr=args.drc_stage2_lr)
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print(f"  seed{s} ❌ 显存不足，跳过")
                torch.cuda.empty_cache()
                continue
            raise
        runs.append(r)
        print(f"  seed{s:<3d} → acc {r['acc']:.4f}  bAcc {r['balanced_acc']:.4f}  "
              f"macroF1 {r['macro_f1']:.4f}  QWK {r['qwk']:.4f}  "
              f"severe召回 {r['severe_recall']:.4f}   ({time.time()-t0:.0f}s)")

    if not runs:
        print("  全部失败")
        return 2

    def agg(k):
        v = np.array([r[k] for r in runs], dtype=float)
        return float(v.mean()), float(v.std())

    summary = {k: agg(k) for k in ("acc", "balanced_acc", "macro_f1", "qwk", "severe_recall")}
    print(f"\n  ── 分辨率 {args.size} 汇总（{len(runs)} 个种子）──")
    for k, (m, s) in summary.items():
        print(f"     {k:16s} {m:.4f} ± {s:.4f}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"size": args.size, "seeds": args.seeds, "weighted": weighted,
                       "pretrained": not args.no_pretrained, "epochs": args.epochs,
                       "logit_adjust": args.logit_adjust, "drc": args.drc,
                       "drc_stage2_epochs": args.drc_stage2_epochs,
                       "summary": {k: {"mean": m, "std": s} for k, (m, s) in summary.items()},
                       "runs": runs}, f, ensure_ascii=False, indent=2)
        print(f"\n  已写 {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
