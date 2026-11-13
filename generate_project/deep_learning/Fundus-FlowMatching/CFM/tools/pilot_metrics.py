#!/usr/bin/env python
"""T0 / T1 试点客观指标（沿用 E2/E3 的统一口径）。

指标
  * 梯度能量   —— 前向差分 |Δx|、|Δy| 的均值（RGB），衡量高频细节/噪点
  * 中心/外环  —— 圆形中心区（r < 0.25R）与外环（0.25R ≤ r ≤ R）亮度比
  * 多样性     —— 批内 8 条件两两 MSE（同 seed 内条件间差异）

用法
  python tools/pilot_metrics.py --out judgment/t1/metrics_t1.json
  python tools/pilot_metrics.py --t1-dir judgment/t1 --out ...

默认目录
  T0: judgment/e3/cfm128_hrsevere_20000_raw_seed{42,1042,2042,3042}/singles
  T1: judgment/t1/cfm128_hrsevere_t1_ac_raw_seed{42,1042,2042,3042}/singles
"""
import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
SEEDS = (42, 1042, 2042, 3042)

T0_PATTERN = "e3/cfm128_hrsevere_20000_raw_seed{seed}/singles"
T1_PATTERN = "t1/cfm128_hrsevere_t1_ac_raw_seed{seed}/singles"


def load_batch(d: Path):
    files = sorted(d.glob("*.png"))
    if not files:
        raise FileNotFoundError(f"目录下没有 PNG: {d}")
    return [np.asarray(Image.open(f).convert("RGB"), dtype=np.float32) / 255.0 for f in files]


def gradient_energy(img: np.ndarray) -> float:
    dx = np.abs(np.diff(img, axis=1)).mean()
    dy = np.abs(np.diff(img, axis=0)).mean()
    return float((dx + dy) / 2)


def center_outer_ratio(img: np.ndarray, c: float = 0.25) -> float:
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx = (h - 1) / 2, (w - 1) / 2
    r = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    R = min(h, w) / 2
    center = img[r < c * R].mean()
    outer = img[(r >= c * R) & (r <= R)].mean()
    return float(center / max(outer, 1e-8))


def diversity(imgs) -> float:
    vals = []
    for a, b in combinations(imgs, 2):
        vals.append(float(((a - b) ** 2).mean()))
    return float(np.mean(vals)) if vals else float("nan")


def evaluate_dir(d: Path) -> dict:
    imgs = load_batch(d)
    return {
        "n": len(imgs),
        "gradient_energy": float(np.mean([gradient_energy(i) for i in imgs])),
        "center_outer": float(np.mean([center_outer_ratio(i) for i in imgs])),
        "diversity": diversity(imgs),
    }


def summarize(per_seed: dict) -> dict:
    keys = ("gradient_energy", "center_outer", "diversity")
    out = {}
    for k in keys:
        v = np.array([s[k] for s in per_seed.values() if not np.isnan(s[k])])
        out[k] = {"mean": float(v.mean()), "std": float(v.std())} if v.size else {"mean": None, "std": None}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-dir", default=str(CFM / "judgment"), help="judgment 根目录")
    ap.add_argument("--t0-pattern", default=T0_PATTERN)
    ap.add_argument("--t1-pattern", default=T1_PATTERN)
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    ap.add_argument("--real-dir", default=None, help="可选：真实图目录，算同口径参照")
    ap.add_argument("--out", default=str(CFM / "judgment/t1/metrics_t1.json"))
    a = ap.parse_args()

    judge = Path(a.judge_dir)
    result = {}

    for name, pat in (("t0", a.t0_pattern), ("t1", a.t1_pattern)):
        per_seed, missing = {}, []
        for s in a.seeds:
            d = judge / pat.format(seed=s)
            if not d.is_dir():
                missing.append(str(d))
                continue
            per_seed[s] = evaluate_dir(d)
        if missing:
            print(f"[WARN] {name} 缺失 {len(missing)} 个目录: {missing[:2]}...")
        if per_seed:
            result[name] = {"seeds": {str(k): v for k, v in per_seed.items()}, "summary": summarize(per_seed)}

    if a.real_dir:
        result["real"] = {"summary": evaluate_dir(Path(a.real_dir))}

    # ---- markdown 表 ----
    print("\n| 组 | 梯度能量 | 中心/外环 | 多样性 MSE |")
    print("|---|---:|---:|---:|")
    for name in ("t0", "t1", "real"):
        if name not in result:
            continue
        if name == "real":
            s = result["real"]["summary"]
            print(f"| 真实参照 | {s['gradient_energy']:.4f} | {s['center_outer']:.3f} | — |")
        else:
            s = result[name]["summary"]
            print(f"| {name.upper()} | {s['gradient_energy']['mean']:.4f} ± {s['gradient_energy']['std']:.4f} "
                  f"| {s['center_outer']['mean']:.3f} ± {s['center_outer']['std']:.3f} "
                  f"| {s['diversity']['mean']:.4f} ± {s['diversity']['std']:.4f} |")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已写入 {out}")


if __name__ == "__main__":
    main()
