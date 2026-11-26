#!/usr/bin/env python
"""T1-256 色调（亮度）校正臂 —— 零 GPU，DL-EX-030 后续

诊断发现：T1-256 相对 T1@128 的主要差异是**整体变暗**（全图平均亮度 0.286→0.241），
径向衰减形状几乎一样（按中心归一后 0.60 vs 0.60；真实约 0.70）。
本臂只做一件事：把每张图的前景平均亮度用**保色相的 gamma** 校正到真实训练集前景均值，
背景保持纯黑（0^γ=0），检验「整体外观 −12.5」里有多少只是色调偏移。

输出
  results/t1_256_contour_diag/tone_seed{...}/singles/*.png
  judgment/t1_256/contour_diag_tone.json

用法
  python tools/t1_256_tone_correct.py --dry-run
  python tools/t1_256_tone_correct.py
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t1_256_contour_diag import (CFM, GRID, PROJ, REAL_DIR, SEEDS, fov_mask,  # noqa: E402
                                 load_rgb, luminance, measure)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = CFM / "judgment" / "t1_256"
OUT = CFM / "results" / "t1_256_contour_diag"


def target_lum() -> float:
    vals = []
    for f in sorted(REAL_DIR.iterdir()):
        if f.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        rgb = load_rgb(f, GRID)
        lum = luminance(rgb)
        m = fov_mask(lum)
        vals.append(float(lum[m].mean()))
    return float(np.mean(vals))


def gamma_to_match(lum: np.ndarray, mask: np.ndarray, target: float) -> float:
    """在 [0.2, 5.0] 内二分 gamma，使 mask 内 mean(lum**gamma) = target。"""
    lo, hi = 0.2, 5.0
    src = np.clip(lum[mask], 1e-6, 1.0)
    for _ in range(40):
        g = 0.5 * (lo + hi)
        if (src ** g).mean() < target:
            hi = g          # 太暗 → gamma 调小（更亮）
        else:
            lo = g
    # 只提亮、不压暗；下限 0.85 防止极暗图被提过头（作者盲评指出「太亮」）
    return float(np.clip(0.5 * (lo + hi), 0.85, 1.0))


def apply_gamma(rgb: np.ndarray, gamma: float, mask: np.ndarray) -> np.ndarray:
    """只改前景亮度、保色相：前景 rgb * (lum^γ / lum)；背景保持原样。

    作者盲评指出：整幅缩放会把边界外的近黑噪点放大成红色 → 必须按 FOV mask 限定。
    """
    lum = np.clip(luminance(rgb), 1e-6, 1.0)
    scale = (lum ** gamma) / lum
    out = np.clip(rgb * scale[..., None], 0, 1)
    out[~mask] = rgb[~mask]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    target = target_lum()
    print(f"真实前景平均亮度目标: {target:.4f}")

    summary, gammas = {}, {}
    for seed in SEEDS:
        src = SRC / f"cfm256_hrsevere_t1_ac_raw_seed{seed}" / "singles"
        if not src.is_dir():
            print(f"[WARN] 缺少 {src}")
            continue
        dst = OUT / f"tone_seed{seed}" / "singles"
        dst.mkdir(parents=True, exist_ok=True)
        gs = []
        for f in sorted(src.glob("*.png")):
            rgb = load_rgb(f)
            lum = luminance(rgb)
            m = fov_mask(lum)
            g = gamma_to_match(lum, m, target)
            out = apply_gamma(rgb, g, m)
            gs.append(g)
            if not args.dry_run:
                Image.fromarray((out * 255).round().astype(np.uint8)).save(dst / f.name)
            summary[f"seed{seed}/{f.stem}"] = measure(out)
        gammas[seed] = gs
        print(f"[OK] seed{seed}: gamma 均值 {np.mean(gs):.3f}（{min(gs):.3f}–{max(gs):.3f}）")

    if args.dry_run:
        print("[dry-run] 不写文件")
        return 0
    out_path = CFM / "judgment" / "t1_256" / "contour_diag_tone.json"
    out_path.write_text(json.dumps({"per_image": summary, "target_lum": target,
                                    "gammas": {str(k): v for k, v in gammas.items()}},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入: {out_path}")

    base = CFM / "judgment" / "t1_256" / "contour_diag.json"
    if base.is_file():
        d = json.loads(base.read_text(encoding="utf-8"))
        orig = d.get("per_image", {}).get("t1_256_native", {})
        common = sorted(set(orig) & set(summary))
        print(f"\n[paired] tone − 原始（n={len(common)}）")
        for m in ("fov_area", "border_lum", "radial_cv", "hf_energy", "hp_std",
                  "center_outer"):
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
