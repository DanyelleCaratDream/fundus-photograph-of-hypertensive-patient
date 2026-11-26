#!/usr/bin/env python
"""T1@128 vs T1-256 两层客观指标（2026-11-14，按 T1_256_PROTOCOL.md §3）

第一层 原生分辨率
  T1@128 在 128 上算、T1-256 在 256 上算。梯度能量随分辨率变化，**禁止横比**，
  只看各自 seed 间一致性。

第二层 共同网格
  a) 都放大/统一到 256：T1@128 用 Lanczos 放大，T1-256 原生；
  b) 都统一到 128：T1-256 用 Lanczos 缩小，T1@128 原生。
  同一网格下可横比，但**缩放本身改变梯度能量，只作描述，不单独裁决**。
  逐图配对（同 seed 同条件）给出 Δ = T1-256 − T1@128 的均值、标准差、胜率。

用法
  python tools/t1_256_common_grid.py --dry-run
  python tools/t1_256_common_grid.py
  python tools/t1_256_common_grid.py --real-dir ../../fundus/xxx_256   # 可选真实参照
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_metrics import center_outer_ratio, diversity, gradient_energy  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
SEEDS = (42, 1042, 2042, 3042)
T1_PATTERN = "t1/cfm128_hrsevere_t1_ac_raw_seed{seed}/singles"
T256_PATTERN = "t1_256/cfm256_hrsevere_t1_ac_raw_seed{seed}/singles"


def load_dir(d: Path, size: int | None = None):
    """返回 {文件名: float32 数组}，size=None 保持原生分辨率。"""
    out = {}
    for f in sorted(d.glob("*.png")):
        im = Image.open(f).convert("RGB")
        if size is not None:
            im = im.resize((size, size), Image.LANCZOS)
        out[f.name] = np.asarray(im, dtype=np.float32) / 255.0
    return out


def set_stats(imgs: dict) -> dict:
    vals = list(imgs.values())
    if not vals:
        return {"n": 0}
    return {
        "n": len(vals),
        "h": int(vals[0].shape[0]),
        "gradient_energy": float(np.mean([gradient_energy(i) for i in vals])),
        "center_outer": float(np.mean([center_outer_ratio(i) for i in vals])),
        "diversity": diversity(vals),
    }


def paired(a: dict, b: dict, name: str) -> dict:
    """按文件名配对，Δ = b − a。"""
    common = sorted(set(a) & set(b))
    if not common:
        return {"n": 0}
    dg = np.array([gradient_energy(b[k]) - gradient_energy(a[k]) for k in common])
    dc = np.array([center_outer_ratio(b[k]) - center_outer_ratio(a[k]) for k in common])
    return {
        "n": len(common),
        "delta_gradient_energy": {"mean": float(dg.mean()), "std": float(dg.std(ddof=1)) if len(dg) > 1 else 0.0,
                                  "win_rate": float((dg > 0).mean())},
        "delta_center_outer": {"mean": float(dc.mean()), "std": float(dc.std(ddof=1)) if len(dc) > 1 else 0.0,
                               "win_rate": float((dc > 0).mean())},
        "note": f"Δ = {name}；win_rate = Δ>0 的图占比",
    }


def table(rows):
    print("| 组 | N | 尺寸 | 梯度能量 | 中心/外环 | 集合多样性 MSE |")
    print("|---|---:|---:|---:|---:|---:|")
    for label, s in rows:
        if not s or not s.get("n"):
            continue
        print(f"| {label} | {s['n']} | {s['h']} | {s['gradient_energy']:.4f} "
              f"| {s['center_outer']:.3f} | {s['diversity']:.4f} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-dir", default=str(CFM / "judgment"))
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    ap.add_argument("--out", default=str(CFM / "judgment/t1_256/metrics_t1_256.json"))
    ap.add_argument("--real-dir", default=None, help="可选：真实图目录（256），算同网格参照")
    ap.add_argument("--dry-run", action="store_true", help="只检查目录，不算指标")
    a = ap.parse_args()

    judge = Path(a.judge_dir)
    dirs = []
    for s in a.seeds:
        d128 = judge / T1_PATTERN.format(seed=s)
        d256 = judge / T256_PATTERN.format(seed=s)
        if not (d128.is_dir() and d256.is_dir()):
            print(f"[FAIL] seed {s} 缺目录：T1@128={d128.is_dir()} T1-256={d256.is_dir()}")
            return 1
        dirs.append((s, d128, d256))
    print(f"目录齐全：{len(dirs)} seed × 两臂")
    if a.dry_run:
        print("[dry-run] 不算指标")
        return 0

    result = {"protocol": "T1_256_PROTOCOL.md §3 两层指标", "seeds": list(a.seeds)}

    # ---------- 第一层：原生分辨率 ----------
    nat = {}
    for s, d128, d256 in dirs:
        nat[f"seed{s}"] = {"t1_128": set_stats(load_dir(d128)), "t1_256": set_stats(load_dir(d256))}
    result["native"] = {
        "per_seed": nat,
        "note": "T1@128 在 128 上、T1-256 在 256 上；梯度能量随分辨率变化，禁止横比，只看 seed 间一致性",
    }
    print("\n### 第一层 原生分辨率（不可横比）")
    table([(f"seed{s} T1@128", nat[f"seed{s}"]["t1_128"]) for s in a.seeds])
    table([(f"seed{s} T1-256", nat[f"seed{s}"]["t1_256"]) for s in a.seeds])

    # ---------- 第二层：共同网格 ----------
    result["common_grid"] = {}
    for grid in (256, 128):
        a_imgs, b_imgs = {}, {}
        for s, d128, d256 in dirs:
            for name, arr in load_dir(d128, grid).items():
                a_imgs[f"{s}/{name}"] = arr
            for name, arr in load_dir(d256, grid).items():
                b_imgs[f"{s}/{name}"] = arr
        sa, sb = set_stats(a_imgs), set_stats(b_imgs)
        pr = paired(a_imgs, b_imgs, "T1-256 − T1@128")
        entry = {
            "t1_128_at_grid": sa,
            "t1_256_at_grid": sb,
            "paired": {"gradient_energy": pr["delta_gradient_energy"],
                       "center_outer": pr["delta_center_outer"],
                       "n": pr["n"]},
            "note": "同网格可横比；缩放会改变梯度能量，只作描述，不单独裁决",
        }
        if a.real_dir:
            entry["real_at_grid"] = set_stats(load_dir(Path(a.real_dir), grid))
        result["common_grid"][str(grid)] = entry

        print(f"\n### 第二层 共同网格 {grid}px")
        rows = [(f"T1@128 {'(Lanczos 放大)' if grid == 256 else '(原生)'}", sa),
                (f"T1-256 {'(原生)' if grid == 256 else '(Lanczos 缩小)'}", sb)]
        if a.real_dir:
            rows.append(("真实参照", entry["real_at_grid"]))
        table(rows)
        p = entry["paired"]
        print(f"\n逐图配对（N={p['n']}，Δ = T1-256 − T1@128）：")
        print(f"- 梯度能量：{p['gradient_energy']['mean']:+.4f} ± {p['gradient_energy']['std']:.4f}"
              f"（Δ>0 {p['gradient_energy']['win_rate']:.0%}）")
        print(f"- 中心/外环：{p['center_outer']['mean']:+.3f} ± {p['center_outer']['std']:.3f}"
              f"（Δ>0 {p['center_outer']['win_rate']:.0%}）")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
