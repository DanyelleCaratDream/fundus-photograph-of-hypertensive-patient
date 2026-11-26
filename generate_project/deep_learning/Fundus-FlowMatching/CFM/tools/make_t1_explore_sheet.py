#!/usr/bin/env python
"""T1 推理侧探索对比图与指标（2026-11-13）

四格：raw×50（主结果，复用 judgment/t1）、EMA×50、raw×100、EMA×100。
输出：judgment/t1_explore/T1_explore_seed{S}.png（条件 + 四格，各 8 列）
      以及同口径的三项客观指标（gradient_energy / center_outer / diversity）。

用法
  python tools/make_t1_explore_sheet.py
  python tools/make_t1_explore_sheet.py --seeds 42 1042 --out judgment/t1_explore
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_metrics import evaluate_dir, summarize  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
CELL = 192
LABEL_W = 150
PAD = 6
BAR = 26
SEEDS = (42, 1042)
VARIANTS = (
    ("raw x50 (main)", "t1/cfm128_hrsevere_t1_ac_raw_seed{seed}/singles"),
    ("EMA x50", "t1_explore/ema50_seed{seed}/singles"),
    ("raw x100", "t1_explore/raw100_seed{seed}/singles"),
    ("EMA x100", "t1_explore/ema100_seed{seed}/singles"),
)


def load_sorted(d: Path, n: int = 8):
    files = sorted(d.glob("*.png"))[:n]
    return [Image.open(f).convert("RGB").resize((CELL, CELL), Image.LANCZOS) for f in files]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-dir", default=str(CFM / "judgment"))
    ap.add_argument("--cond-dir", default=str(CFM / "data/conditions_hrsevere_61_128"))
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    ap.add_argument("--out", default=str(CFM / "judgment/t1_explore"))
    a = ap.parse_args()

    judge, out = Path(a.judge_dir), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    conds = load_sorted(Path(a.cond_dir))
    n_cols = len(conds)
    width = LABEL_W + n_cols * (CELL + PAD) + PAD

    print("\n| seed | 变体 | 梯度能量 | 中心/外环 | 多样性 MSE |")
    print("|---|---|---:|---:|---:|")
    per_variant = {label: [] for label, _ in VARIANTS}

    for s in a.seeds:
        rows = [("条件 mask", conds)]
        for label, pat in VARIANTS:
            d = judge / pat.format(seed=s)
            if not d.is_dir():
                print(f"[WARN] 缺目录: {d}")
                continue
            imgs = load_sorted(d)
            rows.append((label, imgs))
            m = evaluate_dir(d)
            per_variant[label].append(m)
            print(f"| {s} | {label} | {m['gradient_energy']:.4f} | "
                  f"{m['center_outer']:.3f} | {m['diversity']:.4f} |")

        h = BAR + len(rows) * (CELL + PAD + BAR) + PAD
        sheet = Image.new("RGB", (width, h), "white")
        dr = ImageDraw.Draw(sheet)
        dr.text((8, 6), f"T1 inference-side exploration  seed {s} ({n_cols} fixed conds)", fill="black")
        y = BAR
        for label, imgs in rows:
            dr.text((6, y + CELL // 2), label, fill="black")
            for j, im in enumerate(imgs):
                sheet.paste(im, (LABEL_W + j * (CELL + PAD), y))
            y += CELL + PAD + BAR
        p = out / f"T1_explore_seed{s}.png"
        sheet.save(p)
        print(f"已生成 {p}")

    print("\n| 变体 | 梯度能量 | 中心/外环 | 多样性 MSE |")
    print("|---|---:|---:|---:|")
    for label, _ in VARIANTS:
        ms = per_variant[label]
        if not ms:
            continue
        sm = summarize({i: m for i, m in enumerate(ms)})
        print(f"| {label} | {sm['gradient_energy']['mean']:.4f} ± {sm['gradient_energy']['std']:.4f} "
              f"| {sm['center_outer']['mean']:.3f} ± {sm['center_outer']['std']:.3f} "
              f"| {sm['diversity']['mean']:.4f} ± {sm['diversity']['std']:.4f} |")
    print("\n注意：探索性结果，不替换预注册主结果（raw×50）。")


if __name__ == "__main__":
    main()
