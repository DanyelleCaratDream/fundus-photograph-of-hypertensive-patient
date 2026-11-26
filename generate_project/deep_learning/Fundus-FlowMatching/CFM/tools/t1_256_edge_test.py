#!/usr/bin/env python
"""T1-256 边缘零填充检验（DL-EX-030 的后续，最省档）

假设：暗边来自 UNet 在图像边界的零填充（zero-padding）。
检验：同权重在 288 / 320 生成，再**中心裁回 256**；若暗边随裁边消失，
      说明它是「边界驱动」；若仍存在，说明暗边跟着视网膜半径走（模型/数据侧）。

对照臂
  base256      : judgment/t1_256/..._raw_seed42/singles（原生 256，基线）
  gen288_full  : 288 原生
  gen288_crop  : 288 中心裁 256
  gen320_full  : 320 原生
  gen320_crop  : 320 中心裁 256
  t1_128_up256 : T1@128 Lanczos→256
  real         : fundus/hrsevere_61_sq256

另输出径向亮度剖面（归一化半径 0→1，32 bin），直接看暗带位置。

用法
  python tools/t1_256_edge_test.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t1_256_contour_diag import (CFM, GRID, PROJ, REAL_DIR, load_rgb, measure)  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = CFM / "judgment" / "t1_256" / "cfm256_hrsevere_t1_ac_raw_seed42" / "singles"
T1_128 = CFM / "judgment" / "t1" / "cfm128_hrsevere_t1_ac_raw_seed42" / "singles"
EXP = CFM / "results" / "t1_256_contour_diag"


def crop_center(arr: np.ndarray, size: int = GRID) -> np.ndarray:
    h, w = arr.shape[:2]
    y0, x0 = (h - size) // 2, (w - size) // 2
    return arr[y0:y0 + size, x0:x0 + size]


def radial_lum(rgb: np.ndarray, bins: int = 32) -> np.ndarray:
    """按归一化半径（到图像中心，1 = 半宽）分箱的平均亮度。"""
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx = (h - 1) / 2, (w - 1) / 2
    r = np.hypot(yy - cy, xx - cx) / (min(h, w) / 2)
    idx = np.clip((r * bins).astype(int), 0, bins - 1)
    out = np.full(bins, np.nan)
    for b in range(bins):
        sel = idx == b
        if sel.any():
            out[b] = lum[sel].mean()
    return out


def load_arm(d: Path, size: int | None = None, crop: int | None = None):
    out = {}
    if not d.is_dir():
        print(f"[WARN] 缺少 {d}")
        return out
    for f in sorted(d.iterdir()):
        if f.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        rgb = load_rgb(f, size)
        if crop is not None:
            rgb = crop_center(rgb, crop)
        out[f.stem] = rgb
    return out


def summarize(name: str, imgs: dict) -> dict:
    if not imgs:
        return {"n": 0}
    ms = {k: measure(v) for k, v in imgs.items()}
    keys = ("fov_area", "border_lum", "radial_cv", "circularity", "hf_energy", "hp_std")
    s = {"n": len(ms)}
    for m in keys:
        a = np.array([v[m] for v in ms.values()])
        a = a[np.isfinite(a)]
        s[m] = float(a.mean()) if a.size else float("nan")
    prof = np.nanmean(np.array([radial_lum(v) for v in imgs.values()]), axis=0)
    s["radial_profile"] = [float(x) for x in prof]
    return s


def main():
    arm_defs = {
        "base256": (BASE, None, None),
        "gen288_full": (EXP / "gen288_seed42" / "singles", None, None),
        "gen288_crop": (EXP / "gen288_seed42" / "singles", None, GRID),
        "gen320_full": (EXP / "gen320_seed42" / "singles", None, None),
        "gen320_crop": (EXP / "gen320_seed42" / "singles", None, GRID),
        "t1_128_up256": (T1_128, GRID, None),
    }
    arms = {k: load_arm(*v) for k, v in arm_defs.items()}
    real = load_arm(REAL_DIR, GRID, None)
    arms["real"] = real

    out = {k: summarize(k, v) for k, v in arms.items()}
    print(f"{'arm':14s} {'n':>2s} {'fov_area':>9s} {'border_lum':>10s} "
          f"{'radial_cv':>9s} {'circular':>9s} {'hp_std':>8s}")
    for k, s in out.items():
        if not s["n"]:
            continue
        print(f"{k:14s} {s['n']:2d} {s['fov_area']:9.4f} {s['border_lum']:10.4f} "
              f"{s['radial_cv']:9.4f} {s['circularity']:9.4f} {s['hp_std']:8.4f}")

    print("\n径向亮度剖面（归一化半径 0→1，每 1/16）")
    for k in ("real", "t1_128_up256", "base256", "gen288_full", "gen288_crop",
              "gen320_full", "gen320_crop"):
        if k in out and out[k]["n"]:
            p = out[k]["radial_profile"]
            print(f"{k:14s} " + " ".join(f"{p[i]:.3f}" for i in range(0, 32, 2)))

    print("\n径向剖面按中心归一（形状；1.00 = 中心亮度）")
    for k in ("real", "t1_128_up256", "base256", "gen288_full", "gen288_crop",
              "gen320_full", "gen320_crop"):
        if k in out and out[k]["n"]:
            p = np.array(out[k]["radial_profile"])
            q = p / max(p[0], 1e-8)
            print(f"{k:14s} " + " ".join(f"{q[i]:.2f}" for i in range(0, 32, 2)))

    out_path = CFM / "judgment" / "t1_256" / "contour_diag_edge.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
