# -*- coding: utf-8 -*-
"""DL-EX-032 诊断脚本：定位"同 seed 重复训练指标波动"的来源。

分两层：
  第一层（默认）：两次 1-epoch 同配置运行，比较
      初始化参数哈希 / DataLoader 实际取图顺序 / 首个 step 梯度哈希 /
      训练后参数哈希 / 前向反向探针 / 指标 / 耗时
  第二层（--deterministic）：用与 train_classifier.py --deterministic 同一套
      严格设置（warn_only=False）重复同样比较

用法（须在仓库根目录）：
    CUBLAS_WORKSPACE_CONFIG=:4096:8 python classify_project/scripts/diagnose_determinism.py
    CUBLAS_WORKSPACE_CONFIG=:4096:8 python classify_project/scripts/diagnose_determinism.py --deterministic

注意：本脚本只做诊断，不写正式结果、不改训练代码。
CUBLAS_WORKSPACE_CONFIG 必须在 CUDA 初始化前设置（脚本顶部已兜底）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "classify_project/scripts"))
import train_classifier as T  # noqa: E402


def hash_state(model: torch.nn.Module) -> str:
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()[:16]


def param_hash(model: torch.nn.Module) -> str:
    return hash_state(model)


def grads_hash(opt) -> str:
    h = hashlib.sha256()
    for g in opt.param_groups:
        for p in g["params"]:
            if p.grad is not None:
                h.update(p.grad.detach().cpu().numpy().tobytes())
    return h.hexdigest()[:16]


def run_once(args, tag: str) -> dict:
    order: list[int] = []
    init_hash = {"v": ""}
    model_ref = {}
    first_grad = {"v": ""}

    orig_getitem = T.FundusFolder.__getitem__
    orig_build = T.build_model
    orig_step = torch.optim.AdamW.step

    def patched_getitem(self, i):
        order.append(i)
        return orig_getitem(self, i)

    def patched_build(size):
        m = orig_build(size)
        init_hash["v"] = hash_state(m)
        model_ref["m"] = m
        return m

    def patched_step(self, *a, **k):
        if not first_grad["v"]:              # 第一个 optimizer step 之前的梯度
            first_grad["v"] = grads_hash(self)
        return orig_step(self, *a, **k)

    T.FundusFolder.__getitem__ = patched_getitem
    T.build_model = patched_build
    torch.optim.AdamW.step = patched_step
    try:
        t0 = time.time()
        r = T.train_one(256, Path(args.data), args.seed, args.epochs, 16, 1e-4, 1e-4,
                        "cuda" if torch.cuda.is_available() else "cpu",
                        True, 0, True,
                        class_weights=args.class_weights,
                        fixed_draws=552 if args.synth_dir else None,
                        extra_train_severe_dir=args.synth_dir)
        elapsed = time.time() - t0
    finally:
        T.FundusFolder.__getitem__ = orig_getitem
        T.build_model = orig_build
        torch.optim.AdamW.step = orig_step

    # train_one 结束前会 load 最优检查点，model_ref 反映了最终参与评估的权重
    final_hash = param_hash(model_ref["m"]) if "m" in model_ref else None
    return {
        "tag": tag,
        "init_hash": init_hash["v"],
        "first_grad_hash": first_grad["v"] or None,
        "final_param_hash": final_hash,
        "order_len": len(order),
        "order_head": order[:40],
        "order_hash": hashlib.sha256(
            np.asarray(order, dtype=np.int64).tobytes()).hexdigest()[:16],
        "qwk": round(r["qwk"], 6),
        "val_qwk": round(r["val_qwk"], 6),
        "acc": round(r["acc"], 6),
        "elapsed_s": round(elapsed, 1),
        "optimizer_steps": r["optimizer_steps"],
    }


def forward_probe(args) -> dict:
    """同一模型、同一 batch 连续前向/反向两次，看是否逐位一致。"""
    torch.manual_seed(args.seed)
    model = T.build_model(256).to("cuda" if torch.cuda.is_available() else "cpu")
    dev = next(model.parameters()).device
    x = torch.rand(8, 3, 256, 256, device=dev)
    outs = []
    for _ in range(2):
        with torch.no_grad():
            outs.append(model(x).clone())
    d_fwd = float((outs[0] - outs[1]).abs().max().item())

    # 反向：两次 zero_grad → backward，比较梯度
    model.train()
    grads = []
    for _ in range(2):
        model.zero_grad(set_to_none=True)
        loss = model(x).sum()
        loss.backward()
        grads.append(torch.cat([p.grad.flatten() for p in model.parameters()
                                if p.grad is not None]).clone())
    d_bwd = float((grads[0] - grads[1]).abs().max().item())
    return {"forward_max_abs_diff": d_fwd, "grad_max_abs_diff": d_bwd}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="fundus/HRSG_4_758_sq256")
    ap.add_argument("--synth-dir", default="fundus/t3_synth_128",
                    help="传空字符串则为 A0 配置")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--class-weights", type=float, nargs=4,
                    default=[1.15, 0.985714, 0.985714, 0.907895])
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--deterministic", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.deterministic:
        # 与 train_classifier.py --deterministic 完全同一套设置（warn_only=False）
        T.enable_determinism()
        print(f"[mode] deterministic=True  CUBLAS_WORKSPACE_CONFIG={os.environ.get('CUBLAS_WORKSPACE_CONFIG')}")
    else:
        print(f"[mode] deterministic=False  cudnn.benchmark={torch.backends.cudnn.benchmark}")

    res = {"deterministic": bool(args.deterministic),
           "seed": args.seed, "synth_dir": args.synth_dir,
           "state": T.determinism_state(),
           "forward_probe": forward_probe(args)}

    r1 = run_once(args, "run1")
    r2 = run_once(args, "run2")
    res["run1"], res["run2"] = r1, r2
    res["compare"] = {
        "init_hash_same": r1["init_hash"] == r2["init_hash"],
        "batch_order_same": r1["order_hash"] == r2["order_hash"],
        "first_grad_same": r1["first_grad_hash"] == r2["first_grad_hash"],
        "final_param_same": r1["final_param_hash"] == r2["final_param_hash"],
        "qwk_same": r1["qwk"] == r2["qwk"],
        "val_qwk_same": r1["val_qwk"] == r2["val_qwk"],
        "qwk_abs_diff": round(abs(r1["qwk"] - r2["qwk"]), 6),
        "val_qwk_abs_diff": round(abs(r1["val_qwk"] - r2["val_qwk"]), 6),
    }

    print(json.dumps(res, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
