#!/usr/bin/env python
"""生成 T0 vs T1 对比拼图（每个 seed 一张：条件 / T0 / T1 三行 × 8 列）。

用法
  python tools/make_t1_sheet.py --out judgment/t1

默认读取
  T0: judgment/e3/cfm128_hrsevere_20000_raw_seed{42,1042,2042,3042}/singles
  T1: judgment/t1/cfm128_hrsevere_t1_ac_raw_seed{42,1042,2042,3042}/singles
条件 mask: data/conditions_hrsevere_61_128（排序前 8 张，与 generate.py 的 1:1 取值一致）
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
SEEDS = (42, 1042, 2042, 3042)
T0_PATTERN = "e3/cfm128_hrsevere_20000_raw_seed{seed}/singles"
T1_PATTERN = "t1/cfm128_hrsevere_t1_ac_raw_seed{seed}/singles"

CELL = 192
LABEL_W = 120
PAD = 6
BAR = 26


def load_sorted(d: Path, n: int = 8):
    files = sorted(d.glob("*.png"))[:n]
    return [Image.open(f).convert("RGB").resize((CELL, CELL), Image.LANCZOS) for f in files]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-dir", default=str(CFM / "judgment"))
    ap.add_argument("--cond-dir", default=str(CFM / "data/conditions_hrsevere_61_128"))
    ap.add_argument("--t0-pattern", default=T0_PATTERN)
    ap.add_argument("--t1-pattern", default=T1_PATTERN)
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    ap.add_argument("--out", default=str(CFM / "judgment/t1"))
    a = ap.parse_args()

    judge, out = Path(a.judge_dir), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    conds = load_sorted(Path(a.cond_dir))
    n_cols = len(conds)

    rows = [("条件 mask", conds)]
    for s in a.seeds:
        d0 = judge / a.t0_pattern.format(seed=s)
        d1 = judge / a.t1_pattern.format(seed=s)
        if not (d0.is_dir() and d1.is_dir()):
            print(f"[WARN] seed {s} 缺目录，跳过（T0={d0.is_dir()} T1={d1.is_dir()}）")
            continue
        rows.append((f"T0  seed{s}", load_sorted(d0)))
        rows.append((f"T1  seed{s}", load_sorted(d1)))

    width = LABEL_W + n_cols * (CELL + PAD) + PAD
    height = BAR + len(rows) * (CELL + PAD + BAR) + PAD
    sheet = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(sheet)

    d.text((8, 6), f"T0 vs T1（A_clean 初始化）  {n_cols} 固定条件 × {len(a.seeds)} seed", fill="black")
    y = BAR
    for label, imgs in rows:
        d.text((6, y + CELL // 2), label, fill="black")
        for j, im in enumerate(imgs):
            sheet.paste(im, (LABEL_W + j * (CELL + PAD), y))
        y += CELL + PAD + BAR

    path = out / "T0_vs_T1_sheet.png"
    sheet.save(path)
    print(f"已生成 {path}（{width}×{height}，{len(rows) - 1} 行样本）")

    # 每个 seed 单独一张，便于专家逐张打分
    for s in a.seeds:
        d0 = judge / a.t0_pattern.format(seed=s)
        d1 = judge / a.t1_pattern.format(seed=s)
        if not (d0.is_dir() and d1.is_dir()):
            continue
        sub = [("T0", load_sorted(d0)), ("T1", load_sorted(d1))]
        h = len(sub) * (CELL + PAD)
        im = Image.new("RGB", (width, BAR + h + PAD), "white")
        dr = ImageDraw.Draw(im)
        dr.text((8, 6), f"seed {s}", fill="black")
        yy = BAR
        for label, imgs in sub:
            dr.text((6, yy + CELL // 2), label, fill="black")
            for j, x in enumerate(imgs):
                im.paste(x, (LABEL_W + j * (CELL + PAD), yy))
            yy += CELL + PAD
        p = out / f"T0_vs_T1_seed{s}.png"
        im.save(p)
        print(f"已生成 {p}")


if __name__ == "__main__":
    main()
