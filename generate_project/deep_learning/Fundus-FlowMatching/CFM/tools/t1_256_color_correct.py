#!/usr/bin/env python
"""T1-256 后处理颜色校正臂（零 GPU，最省档）

把 generate.py 的 apply_color_correct 直接作用在**已有** 32 张 T1-256 输出上：
每张图按通道归一到真实训练集（hrsevere_61_sq256）的 RGB 均值/标准差。
用来回答：人工盲评的「整体外观 −12.5」里，有多少只是全局颜色统计偏移。

输出
  results/t1_256_contour_diag/cc_seed{42,1042,2042,3042}/singles/*.png
  judgment/t1_256/contour_diag_cc.json

用法
  python tools/t1_256_color_correct.py --dry-run
  python tools/t1_256_color_correct.py
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t1_256_contour_diag import CFM, GRID, PROJ, SEEDS, load_rgb, measure  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = CFM / "judgment" / "t1_256"
OUT = CFM / "results" / "t1_256_contour_diag"
REAL_DIR = PROJ / "fundus" / "hrsevere_61_sq256"


def real_stats() -> tuple[np.ndarray, np.ndarray]:
    pixels = []
    for f in sorted(REAL_DIR.iterdir()):
        if f.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        arr = load_rgb(f, GRID).reshape(-1, 3)
        pixels.append(arr)
    px = np.concatenate(pixels, axis=0)
    return px.mean(axis=0), px.std(axis=0)


def correct(rgb: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    """rgb in [0,1] -> 按通道归一到目标 mean/std，再裁回 [0,1]。"""
    m = rgb.reshape(-1, 3).mean(axis=0)
    s = rgb.reshape(-1, 3).std(axis=0)
    s = np.maximum(s, 1e-6)
    out = (rgb - m) / s * std + mean
    return np.clip(out, 0.0, 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not REAL_DIR.is_dir():
        print(f"[FAIL] 找不到真实参照: {REAL_DIR}")
        return 1
    mean, std = real_stats()
    print(f"目标 RGB 均值 {np.round(mean, 4)}  标准差 {np.round(std, 4)}")

    summary = {}
    for seed in SEEDS:
        src = SRC / f"cfm256_hrsevere_t1_ac_raw_seed{seed}" / "singles"
        if not src.is_dir():
            print(f"[WARN] 缺少 {src}")
            continue
        dst = OUT / f"cc_seed{seed}" / "singles"
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src.glob("*.png")):
            rgb = load_rgb(f)
            cc = correct(rgb, mean, std)
            if not args.dry_run:
                Image.fromarray((cc * 255).round().astype(np.uint8)).save(dst / f.name)
            summary[f"seed{seed}/{f.stem}"] = measure(cc)
        print(f"[OK] seed{seed}: {len(list(src.glob('*.png')))} 张")

    if args.dry_run:
        print("[dry-run] 不写文件")
        return 0
    out = CFM / "judgment" / "t1_256" / "contour_diag_cc.json"
    out.write_text(json.dumps({"per_image": summary,
                               "target_mean": mean.tolist(),
                               "target_std": std.tolist()},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入: {out}")

    # 与原始 T1-256 配对对比
    base = CFM / "judgment" / "t1_256" / "contour_diag.json"
    if base.is_file():
        d = json.loads(base.read_text(encoding="utf-8"))
        orig = d.get("per_image", {}).get("t1_256_native", {})
        common = sorted(set(orig) & set(summary))
        print(f"\n[paired] CC − 原始（n={len(common)}）")
        for m in ("fov_area", "circularity", "border_lum", "hf_energy",
                  "hp_std", "center_outer"):
            a = np.array([orig[k][m] for k in common])
            b = np.array([summary[k][m] for k in common])
            ok = np.isfinite(a) & np.isfinite(b)
            a, b = a[ok], b[ok]
            if a.size < 2:
                continue
            diff = b - a
            print(f"  {m:12s} {a.mean():.4f} -> {b.mean():.4f}  "
                  f"Δ={diff.mean():+.4f}  win={np.mean(diff > 0):.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
