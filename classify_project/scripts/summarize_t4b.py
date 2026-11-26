# -*- coding: utf-8 -*-
"""DL-EX-034（口径 B）结果汇总：指标 + 同 seed 配对 Δ + 图像层分层 bootstrap。

只读 `results/t4_dedupB_20261125/predictions/`，不重训。
配对方式与组员 A 的复算一致：图像层分层重抽样（按 y_true 分层），
B=1000，Generator seed=20261117，三 seed 共用同一组重采样索引，先逐 seed 算 Δ 再平均。

用法（仓库根目录）：
    python -X utf8 classify_project/scripts/summarize_t4b.py
输出：results/t4_dedupB_20261125/summary_20261125.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (balanced_accuracy_score, cohen_kappa_score,
                             f1_score)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "classify_project/results/t4_dedupB_20261125"
SEEDS = [42, 52, 62]
ARMS = ["A0", "A1"]
B = 1000
RNG_SEED = 20261117


def load(arm: str, seed: int) -> dict:
    d = json.load(open(OUT / "predictions" / f"{arm}_seed{seed}.json", encoding="utf-8"))
    out = {}
    for im in d["images"]:
        yp = max(range(4), key=lambda j: im["logits"][j])
        assert yp == im["y_pred"], f"{arm}/seed{seed}: argmax != y_pred"
        out[im["path"]] = (im["y_true"], yp)
    return out


def metrics(yt: np.ndarray, yp: np.ndarray) -> dict:
    sev = yt == 3
    return {
        "qwk": float(cohen_kappa_score(yt, yp, weights="quadratic", labels=[0, 1, 2, 3])),
        "bacc": float(balanced_accuracy_score(yt, yp)),
        "macro_f1": float(f1_score(yt, yp, average="macro", zero_division=0, labels=[0, 1, 2, 3])),
        "severe_recall": float((yp[sev] == 3).mean()),
    }


def main() -> int:
    data = {(a, s): load(a, s) for a in ARMS for s in SEEDS}
    paths = sorted(data[("A0", 42)])
    for a in ARMS:
        for s in SEEDS:
            assert sorted(data[(a, s)]) == paths, f"路径集合不一致 {a}{s}"
            assert all(data[(a, s)][p][0] == data[("A0", 42)][p][0] for p in paths)
    yt = np.array([data[("A0", 42)][p][0] for p in paths])
    yp = {(a, s): np.array([data[(a, s)][p][1] for p in paths]) for a in ARMS for s in SEEDS}

    per = {(a, s): metrics(yt, yp[(a, s)]) for a in ARMS for s in SEEDS}
    delta = {s: {k: per[("A1", s)][k] - per[("A0", s)][k] for k in per[("A1", s)]} for s in SEEDS}

    # 分层 bootstrap：类内按原样本量有放回抽样；三 seed 共用索引
    rng = np.random.Generator(np.random.PCG64(RNG_SEED))
    cls_idx = [np.where(yt == c)[0] for c in range(4)]
    boot = {k: [] for k in ("qwk", "bacc", "macro_f1", "severe_recall")}
    for _ in range(B):
        idx = np.concatenate([rng.choice(ix, size=len(ix), replace=True) for ix in cls_idx])
        ys = yt[idx]
        ds = {k: [] for k in boot}
        for s in SEEDS:
            m0 = metrics(ys, yp[("A0", s)][idx])
            m1 = metrics(ys, yp[("A1", s)][idx])
            for k in boot:
                ds[k].append(m1[k] - m0[k])
        for k in boot:
            boot[k].append(float(np.mean(ds[k])))
    ci = {k: [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))] for k, v in boot.items()}

    summary = {
        "experiment": "DL-EX-034 (T4B strict dedup)",
        "n_test": int(len(paths)),
        "class_counts": {str(c): int((yt == c).sum()) for c in range(4)},
        "per_arm_seed": {f"{a}_seed{s}": per[(a, s)] for a in ARMS for s in SEEDS},
        "delta": {f"seed{s}": delta[s] for s in SEEDS},
        "delta_mean": {k: float(np.mean([delta[s][k] for s in SEEDS])) for k in boot},
        "delta_sd": {k: float(np.std([delta[s][k] for s in SEEDS], ddof=1)) for k in boot},
        "ci95": ci,
        "bootstrap": {"B": B, "seed": RNG_SEED, "unit": "test image (stratified by y_true)",
                      "seeds": SEEDS, "shared_indices": True},
    }
    (OUT / "summary_20261125.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    for a in ARMS:
        q = [per[(a, s)]["qwk"] for s in SEEDS]
        print(f"{a} QWK per seed: " + " / ".join(f"{x:.4f}" for x in q)
              + f"  mean {np.mean(q):.4f}")
    print("A1-A0 ΔQWK: " + " / ".join(f"{delta[s]['qwk']:+.4f}" for s in SEEDS)
          + f"  mean {summary['delta_mean']['qwk']:+.4f}"
          + f"  CI [{ci['qwk'][0]:+.4f}, {ci['qwk'][1]:+.4f}]")
    for k in ("bacc", "macro_f1", "severe_recall"):
        print(f"  Δ{k}: mean {summary['delta_mean'][k]:+.4f}"
              f"  CI [{ci[k][0]:+.4f}, {ci[k][1]:+.4f}]")
    print(f"已写 {OUT / 'summary_20261125.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
