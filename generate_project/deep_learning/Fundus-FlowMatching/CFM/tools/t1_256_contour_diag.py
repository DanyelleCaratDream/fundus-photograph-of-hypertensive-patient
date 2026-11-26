#!/usr/bin/env python
"""T1-256 轮廓退化诊断（2026-11-14，最省档第一步：不训练、不重新生成）

问题：T1-256 人工盲评「血管 +10、整体外观 −12.5、轮廓退」。本脚本只回答
一件事——轮廓退化在像素上是什么，以及在 256 网格上是否真的比 T1@128 差。

输入（全部为已有产物）
  real    : fundus/hrsevere_61_sq256
  t1_256  : judgment/t1_256/cfm256_hrsevere_t1_ac_raw_seed{42,1042,2042,3042}/singles
  t1_128  : judgment/t1/cfm128_hrsevere_t1_ac_raw_seed{...}/singles

指标（每张图，256 网格）
  * fov_area      —— 前景（非黑）最大连通域面积占比
  * circularity   —— 4πA/P²，1=完美圆
  * radial_cv     —— 360 条射线边界半径 r(θ) 的变异系数（越大越不圆）
  * radial_p95    —— r(θ) 偏离中位数的 95 分位（相对值，量化「齿轮状」缺角）
  * border_lum    —— 边界内环（0.85–0.95R）平均亮度
  * bg_leak       —— 前景外像素平均亮度（背景不干净/发亮）
  * hf_energy     —— 前景内梯度能量
  * hp_std        —— 前景内高通残差 std（颗粒/噪点）
  * rgb_mean/std  —— 前景内三通道均值/标准差
  * center_outer  —— 中心区/外环亮度比（沿用 pilot_metrics 口径）

配对比较
  T1-256 原生 vs T1@128 Lanczos→256（同 seed 同 sample 序号）
  另做 128 网格复核：T1@128 原生 vs T1-256 Lanczos→128

用法
  python tools/t1_256_contour_diag.py --dry-run
  python tools/t1_256_contour_diag.py
  python tools/t1_256_contour_diag.py --out judgment/t1_256/contour_diag.json
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from scipy import stats

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
PROJ = CFM.parents[3]
SEEDS = (42, 1042, 2042, 3042)
REAL_DIR = PROJ / "fundus" / "hrsevere_61_sq256"
T1_PATTERN = "t1/cfm128_hrsevere_t1_ac_raw_seed{seed}/singles"
T256_PATTERN = "t1_256/cfm256_hrsevere_t1_ac_raw_seed{seed}/singles"
GRID = 256
THRESH = 0.06          # 前景阈值（亮度，0–1）
THRESH_SENS = (0.04, 0.08)


def load_rgb(path: Path, size: int | None = None) -> np.ndarray:
    im = Image.open(path).convert("RGB")
    if size is not None and im.size != (size, size):
        im = im.resize((size, size), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0


def luminance(rgb: np.ndarray) -> np.ndarray:
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def fov_mask(lum: np.ndarray, thresh: float = THRESH) -> np.ndarray:
    """最大连通域 + 填洞。真实眼底四角为黑，生成图偶有外圈噪点。"""
    m = (lum > thresh).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n <= 1:
        return m.astype(bool)
    # 取面积最大的非背景连通域
    idx = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = (lab == idx).astype(np.uint8)
    # 填洞：从边界泛洪背景，未泛洪到的就是洞
    ff = m.copy()
    h, w = ff.shape
    mask_ff = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, mask_ff, (0, 0), 2)
    holes = (ff != 2) & (m == 0)
    m[holes] = 1
    return m.astype(bool)


def radial_profile(mask: np.ndarray, n_angles: int = 360) -> np.ndarray:
    """用外轮廓点求 r(θ)：每 1° 取该角度上的最大半径（快且与射线法等价）。"""
    cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL,
                               cv2.CHAIN_APPROX_NONE)
    if not cnts:
        return np.array([])
    c = max(cnts, key=cv2.contourArea).reshape(-1, 2).astype(np.float64)  # x, y
    ys, xs = np.nonzero(mask)
    cy, cx = ys.mean(), xs.mean()
    dx, dy = c[:, 0] - cx, c[:, 1] - cy
    ang = (np.arctan2(dy, dx) + 2 * np.pi) % (2 * np.pi)
    rad = np.hypot(dx, dy)
    bins = np.minimum((ang / (2 * np.pi) * n_angles).astype(int), n_angles - 1)
    rs = np.full(n_angles, np.nan)
    for b in range(n_angles):
        sel = rad[bins == b]
        if sel.size:
            rs[b] = sel.max()
    return rs[~np.isnan(rs)]


def high_pass_std(lum: np.ndarray, mask: np.ndarray) -> float:
    blur = cv2.GaussianBlur(lum, (0, 0), 2.0)
    hp = (lum - blur)[mask]
    return float(hp.std()) if hp.size else float("nan")


def gradient_energy(lum: np.ndarray, mask: np.ndarray) -> float:
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    g = np.abs(gx) + np.abs(gy)
    return float(g[mask].mean()) if mask.any() else float("nan")


def center_outer(lum: np.ndarray, mask: np.ndarray) -> float:
    ys, xs = np.nonzero(mask)
    cy, cx = ys.mean(), xs.mean()
    yy, xx = np.mgrid[0:lum.shape[0], 0:lum.shape[1]]
    r = np.hypot(yy - cy, xx - cx)
    r_norm = r / max(np.percentile(r[mask], 99), 1e-8)
    center = lum[mask & (r_norm < 0.5)]
    outer = lum[mask & (r_norm >= 0.5) & (r_norm <= 1.0)]
    if center.size == 0 or outer.size == 0:
        return float("nan")
    return float(center.mean() / max(outer.mean(), 1e-8))


def measure(rgb: np.ndarray) -> dict:
    lum = luminance(rgb)
    mask = fov_mask(lum)
    area = float(mask.mean())
    cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if cnts:
        c = max(cnts, key=cv2.contourArea)
        per = float(cv2.arcLength(c, True))
        circ = float(4 * np.pi * cv2.contourArea(c) / (per * per)) if per > 0 else float("nan")
    else:
        circ = float("nan")
    rs = radial_profile(mask)
    if rs.size:
        r_mean = float(rs.mean())
        radial_cv = float(rs.std() / max(r_mean, 1e-8))
        radial_p95 = float(np.percentile(np.abs(rs - np.median(rs)), 95) / max(r_mean, 1e-8))
        # 边界内环亮度
        ys, xs = np.nonzero(mask)
        cy, cx = ys.mean(), xs.mean()
        yy, xx = np.mgrid[0:lum.shape[0], 0:lum.shape[1]]
        rr = np.hypot(yy - cy, xx - cx) / max(r_mean, 1e-8)
        ring = mask & (rr >= 0.85) & (rr <= 0.95)
        border_lum = float(lum[ring].mean()) if ring.any() else float("nan")
    else:
        radial_cv = radial_p95 = border_lum = float("nan")
    bg = lum[~mask]
    out = {
        "fov_area": area,
        "circularity": circ,
        "radial_cv": radial_cv,
        "radial_p95": radial_p95,
        "border_lum": border_lum,
        "bg_leak": float(bg.mean()) if bg.size else float("nan"),
        "hf_energy": gradient_energy(lum, mask),
        "hp_std": high_pass_std(lum, mask),
        "center_outer": center_outer(lum, mask),
        "rgb_mean": [float(rgb[..., i][mask].mean()) for i in range(3)],
        "rgb_std": [float(rgb[..., i][mask].std()) for i in range(3)],
    }
    # 阈值敏感性（只对面积/圆度）
    for t in THRESH_SENS:
        m2 = fov_mask(lum, t)
        out[f"fov_area_t{int(t*100):02d}"] = float(m2.mean())
    return out


def collect(pattern: str, size: int | None) -> dict:
    """返回 {"seed/sample": metrics}。"""
    out = {}
    for seed in SEEDS:
        d = CFM / "judgment" / pattern.format(seed=seed)
        if not d.is_dir():
            print(f"[WARN] 缺少目录: {d}")
            continue
        for f in sorted(d.glob("*.png")):
            key = f"seed{seed}/{f.stem}"
            out[key] = measure(load_rgb(f, size))
    return out


def collect_real() -> dict:
    out = {}
    if not REAL_DIR.is_dir():
        print(f"[WARN] 缺少真实参照: {REAL_DIR}")
        return out
    for f in sorted(REAL_DIR.iterdir()):
        if f.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        out[f.stem] = measure(load_rgb(f, GRID))
    return out


METRICS = ("fov_area", "circularity", "radial_cv", "radial_p95", "border_lum",
           "bg_leak", "hf_energy", "hp_std", "center_outer")


def summarize(group: dict) -> dict:
    vals_list = [v for v in group.values() if all(m in v for m in METRICS)]
    out = {"n": len(vals_list)}
    for m in METRICS:
        vals = np.array([v[m] for v in vals_list if np.isfinite(v[m])])
        out[m] = {"mean": float(vals.mean()) if vals.size else float("nan"),
                  "std": float(vals.std(ddof=1)) if vals.size > 1 else float("nan")}
    return out


def paired(a: dict, b: dict, name: str) -> dict:
    common = sorted(set(a) & set(b))
    out = {"n": len(common), "delta": name}
    for m in METRICS:
        va = np.array([a[k][m] for k in common])
        vb = np.array([b[k][m] for k in common])
        ok = np.isfinite(va) & np.isfinite(vb)
        va, vb = va[ok], vb[ok]
        if va.size < 2:
            out[m] = {"n": int(va.size)}
            continue
        d = vb - va
        t, p = stats.ttest_rel(vb, va)
        out[m] = {
            "n": int(va.size),
            "mean_a": float(va.mean()), "mean_b": float(vb.mean()),
            "delta_mean": float(d.mean()), "delta_std": float(d.std(ddof=1)),
            "win_rate": float((d > 0).mean()),
            "p": float(p),
        }
    return out


def fmt_summary(name: str, s: dict) -> str:
    lines = [f"\n[{name}] n={s['n']}"]
    for m in METRICS:
        if m in s and np.isfinite(s[m]["mean"]):
            lines.append(f"  {m:14s} {s[m]['mean']:.4f} ± {s[m]['std']:.4f}")
    return "\n".join(lines)


def fmt_paired(p: dict) -> str:
    lines = [f"\n[paired] {p['delta']}  n={p['n']}"]
    for m in METRICS:
        if m in p and "delta_mean" in p[m]:
            x = p[m]
            lines.append(
                f"  {m:14s} A={x['mean_a']:.4f} B={x['mean_b']:.4f} "
                f"Δ={x['delta_mean']:+.4f}±{x['delta_std']:.4f} "
                f"win={x['win_rate']:.0%} p={x['p']:.3g}"
            )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(CFM / "judgment" / "t1_256" / "contour_diag.json"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("读取：real / t1_128 / t1_256")
    real = collect_real()
    t1 = collect(T1_PATTERN, GRID)        # 放大到 256 网格
    t256 = collect(T256_PATTERN, None)    # 原生 256
    # 128 网格复核
    t1_128 = collect(T1_PATTERN, None)    # 原生 128
    t256_128 = collect(T256_PATTERN, 128) # 缩到 128

    if not t1 or not t256:
        print("[FAIL] 找不到生成图目录")
        return 1

    groups = {
        "real": summarize(real),
        "t1_128_up256": summarize(t1),
        "t1_256_native": summarize(t256),
        "t1_128_native": summarize(t1_128),
        "t1_256_down128": summarize(t256_128),
    }
    pairs = {
        "grid256": paired(t1, t256, "T1-256 − T1@128up"),
        "grid128": paired(t1_128, t256_128, "T1-256down − T1@128"),
    }

    for name, s in groups.items():
        print(fmt_summary(name, s))
    for p in pairs.values():
        print(fmt_paired(p))

    result = {"groups": groups, "paired": pairs,
              "per_image": {"real": real, "t1_128_up256": t1, "t1_256_native": t256,
                            "t1_128_native": t1_128, "t1_256_down128": t256_128},
              "config": {"grid": GRID, "thresh": THRESH, "real_dir": str(REAL_DIR)}}
    if args.dry_run:
        print("\n[dry-run] 不写文件")
        return 0
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
