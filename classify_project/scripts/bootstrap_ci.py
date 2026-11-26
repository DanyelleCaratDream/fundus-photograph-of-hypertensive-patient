# -*- coding: utf-8 -*-
"""分类器 pilot 的分层 bootstrap 95% CI 与配对 Δ（DL-EX-027 secondary analysis）。

输入：`train_classifier.py --dump-predictions` 产出的 `{arm}_seed{seed}.json`
      （每张 test 图的 y_true / y_pred / probs，顺序与 test loader 一致）。

口径：
  * **按类别分层重采样**，保持每类样本数不变（severe 仍 13 张）；
  * 每类内独立有放回抽样，1000 次；
  * 主指标 QWK，次指标 balanced accuracy / macro-F1 / severe recall / 每类 recall；
  * 配对比较：同一组重采样索引同时用于参考 arm 与对照 arm，输出 Δ 的 95% CI
    （Δ = 对照 − 参考；A1/A2 vs A0）。
  * test 上不调任何超参；本脚本只做不确定性量化。

用法：
  python classify_project/scripts/bootstrap_ci.py \
    --pred-dir classify_project/results/pilot_predictions_20261115 \
    --arms A0 A1 A2 --ref A0 --n-boot 1000 \
    --out classify_project/results/pilot_ci_20261115.json
  python classify_project/scripts/bootstrap_ci.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import (balanced_accuracy_score, cohen_kappa_score,
                             confusion_matrix, f1_score)

CLASSES = ["normal", "mild", "moderate", "severe"]
NUM_CLASSES = len(CLASSES)


def metrics_from_preds(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    severe = CLASSES.index("severe")
    out = {
        "qwk": float(cohen_kappa_score(y_true, y_pred, weights="quadratic")),
        "balanced_acc": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "severe_recall": float((y_pred[y_true == severe] == severe).mean())
        if (y_true == severe).any() else float("nan"),
    }
    for i, c in enumerate(CLASSES):
        m = y_true == i
        out[f"recall_{c}"] = float((y_pred[m] == i).mean()) if m.any() else float("nan")
    out["confusion"] = confusion_matrix(y_true, y_pred,
                                        labels=range(NUM_CLASSES)).tolist()
    return out


def load_arm(pred_dir: Path, arm: str) -> tuple[dict, list[int]]:
    """返回 ({path: {y_true, pred: {seed: y_pred}}}, seed 列表)。"""
    files = sorted(pred_dir.glob(f"{arm}_seed*.json"))
    if not files:
        raise FileNotFoundError(f"{pred_dir} 下没有 {arm}_seed*.json")
    by_path: dict[str, dict] = {}
    seeds = []
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        seed = int(d["seed"])
        seeds.append(seed)
        for im in d["images"]:
            rec = by_path.setdefault(im["path"], {"y_true": int(im["y_true"]), "pred": {}})
            if rec["y_true"] != int(im["y_true"]):
                raise RuntimeError(f"{arm}: {im['path']} 的 y_true 跨 seed 不一致")
            rec["pred"][seed] = int(im["y_pred"])
    for p, rec in by_path.items():
        missing = set(seeds) - set(rec["pred"])
        if missing:
            raise RuntimeError(f"{arm}: {p} 缺少 seed {sorted(missing)}")
    return by_path, sorted(seeds)


def align(arms: dict[str, dict]) -> tuple[list[str], dict[str, np.ndarray], list[int]]:
    """对齐后返回 (common paths, {arm: [n_paths, n_seeds] 预测}, 共用 seeds)。"""
    common = sorted(set.intersection(*(set(a) for a in arms.values())))
    if not common:
        raise RuntimeError("各 arm 的 test 路径没有交集")
    first = next(iter(arms))
    y_true = np.array([arms[first][p]["y_true"] for p in common])
    seeds = sorted(set.intersection(*(set(a[p]["pred"]) for a in arms.values() for p in common)))
    out = {"y_true": y_true}
    for name, a in arms.items():
        yt = np.array([a[p]["y_true"] for p in common])
        if not np.array_equal(yt, y_true):
            raise RuntimeError(f"{name} 的 y_true 与参考不一致")
        out[name] = np.array([[a[p]["pred"][s] for s in seeds] for p in common])
    return common, out, seeds


def stratified_indices(y_true: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    parts = [rng.choice(np.where(y_true == c)[0], size=int((y_true == c).sum()),
                        replace=True) for c in range(NUM_CLASSES)]
    return np.concatenate(parts)


def ci(arr: np.ndarray, lo: float = 2.5, hi: float = 97.5) -> list[float]:
    return [float(np.percentile(arr, lo)), float(np.percentile(arr, hi))]


METRIC_KEYS = ("qwk", "balanced_acc", "macro_f1", "severe_recall",
               "recall_normal", "recall_mild", "recall_moderate", "recall_severe")


def metrics_multi(y_true: np.ndarray, preds2d: np.ndarray) -> tuple[dict, list[dict]]:
    """逐 seed 算指标，再对 seed 取平均（与现有 summary 的均值口径一致）。"""
    ms = [metrics_from_preds(y_true, preds2d[:, j]) for j in range(preds2d.shape[1])]
    avg = {k: float(np.nanmean([m[k] for m in ms])) for k in METRIC_KEYS}
    return avg, ms


def summarize_arm(y_true, preds2d, n_boot, rng) -> dict:
    point, per_seed = metrics_multi(y_true, preds2d)
    boots = {k: [] for k in METRIC_KEYS}
    for _ in range(n_boot):
        idx = stratified_indices(y_true, rng)
        avg, _ = metrics_multi(y_true[idx], preds2d[idx])
        for k in METRIC_KEYS:
            boots[k].append(avg[k])
    return {
        "n": int(len(y_true)),
        "n_seeds": int(preds2d.shape[1]),
        "point": point,
        "ci95": {k: ci(np.array(boots[k])) for k in METRIC_KEYS},
        "per_seed": [{k: m[k] for k in METRIC_KEYS} for m in per_seed],
        "confusion_per_seed": [m["confusion"] for m in per_seed],
    }


def paired_delta(y_ref, y_arm, y_true, n_boot, rng) -> dict:
    pa, _ = metrics_multi(y_true, y_arm)
    pr, _ = metrics_multi(y_true, y_ref)
    point = {k: pa[k] - pr[k] for k in METRIC_KEYS}
    boots = {k: [] for k in METRIC_KEYS}
    for _ in range(n_boot):
        idx = stratified_indices(y_true, rng)
        ma, _ = metrics_multi(y_true[idx], y_arm[idx])
        mr, _ = metrics_multi(y_true[idx], y_ref[idx])
        for k in METRIC_KEYS:
            boots[k].append(ma[k] - mr[k])
    out = {}
    for k in METRIC_KEYS:
        d = np.array(boots[k])
        out[k] = {
            "delta": point[k],
            "ci95": ci(d),
            "p_two_sided": float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))),
        }
    return out


def self_test() -> int:
    rng = np.random.default_rng(20261115)
    n = 71
    y_true = np.array([0] * 18 + [1] * 20 + [2] * 20 + [3] * 13)
    # 合成两个 seed 的预测：与真值中等相关 + 噪声
    p1 = np.where(rng.random(n) < 0.65, y_true, rng.integers(0, 4, size=n))
    p2 = np.where(rng.random(n) < 0.65, y_true, rng.integers(0, 4, size=n))
    preds2d = np.stack([p1, p2], axis=1)
    s = summarize_arm(y_true, preds2d, 200, rng)
    ok = True
    for k in METRIC_KEYS:
        lo, hi = s["ci95"][k]
        inside = lo <= s["point"][k] <= hi
        print(f"  {k:16s} point {s['point'][k]:.4f}  CI [{lo:.4f}, {hi:.4f}]  "
              f"{'OK' if inside else 'FAIL'}")
        ok &= inside
    print("[self-test]", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-dir", default=None)
    ap.add_argument("--arms", nargs="+", default=None)
    ap.add_argument("--ref", default="A0")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261115)
    ap.add_argument("--out", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.pred_dir:
        print("需要 --pred-dir（或用 --self-test）", file=sys.stderr)
        return 2

    pred_dir = Path(args.pred_dir)
    if args.arms:
        arms = args.arms
    else:
        arms = sorted({p.name.rsplit("_seed", 1)[0] for p in pred_dir.glob("*_seed*.json")})
    print(f"arms: {arms}  ref: {args.ref}  n_boot: {args.n_boot}")

    loaded = {a: load_arm(pred_dir, a)[0] for a in arms}
    common, arr, seeds = align(loaded)
    print(f"对齐后 test n = {len(common)}  seeds = {seeds}")

    rng = np.random.default_rng(args.seed)
    results = {"n_boot": args.n_boot, "seed": args.seed,
               "n_test": len(common), "arms": {}, "paired_vs": args.ref}
    for a in arms:
        results["arms"][a] = summarize_arm(arr["y_true"], arr[a], args.n_boot, rng)
        s = results["arms"][a]
        print(f"\n[{a}] n={s['n']}")
        for k in ("qwk", "balanced_acc", "macro_f1", "severe_recall"):
            lo, hi = s["ci95"][k]
            print(f"  {k:16s} {s['point'][k]:.4f}  95% CI [{lo:.4f}, {hi:.4f}]")

    results["paired"] = {}
    for a in arms:
        if a == args.ref:
            continue
        results["paired"][a] = paired_delta(arr[args.ref], arr[a], arr["y_true"],
                                            args.n_boot, rng)
        p = results["paired"][a]["qwk"]
        print(f"\n[Δ {a} − {args.ref}] QWK {p['delta']:+.4f}  "
              f"95% CI [{p['ci95'][0]:+.4f}, {p['ci95'][1]:+.4f}]  "
              f"p≈{p['p_two_sided']:.3f}")

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n写入: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
