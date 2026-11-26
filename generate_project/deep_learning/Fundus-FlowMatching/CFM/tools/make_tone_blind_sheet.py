#!/usr/bin/env python
"""色调校正 vs 原始 T1-256 小盲评拼图（DL-EX-030 后续）

只回答一个问题：**保色相 gamma 色调校正能否救回「整体外观 / 边界」**。
血管细节不是本表的目的（DL-EX-029 已评）。

设计
  * 2 seed（42、2042 最差 seed）× 8 固定条件 = 16 对；
  * 每列一对，**逐列随机** A/B（不是整行，因为比较的是单张图的后处理）；
  * 不标原图/校正图，key 单独存；评分前不打开；
  * 评分两项：整体外观、边界形状（0–100）。

输出（judgment/t1_256/）
  tone_blind_seed{42,2042}.png
  tone_blind_key.json
  tone_blind_score_template.csv

用法
  python tools/make_tone_blind_sheet.py --dry-run
  python tools/make_tone_blind_sheet.py
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
JUDGE = CFM / "judgment" / "t1_256"
ORIG_PATTERN = "cfm256_hrsevere_t1_ac_raw_seed{seed}"
TONE_DIR = CFM / "results" / "t1_256_contour_diag"
SEEDS = (42, 2042)
N_COLS = 8
CELL = 256
LABEL_W = 80
PAD = 6
BAR = 34
RNG_SEED = 20261114

FONT_CANDIDATES = (
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
)


def get_font(size: int = 16):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB").resize((CELL, CELL), Image.LANCZOS)


def make_sheet(seed: int, key: dict, rng: random.Random) -> Image.Image:
    orig = sorted((JUDGE / ORIG_PATTERN.format(seed=seed) / "singles").glob("*.png"))[:N_COLS]
    tone = sorted((TONE_DIR / f"tone_seed{seed}" / "singles").glob("*.png"))[:N_COLS]
    if len(orig) != N_COLS or len(tone) != N_COLS:
        raise FileNotFoundError(f"seed{seed}: orig={len(orig)} tone={len(tone)}")

    w = LABEL_W + N_COLS * (CELL + PAD) + PAD
    h = BAR + 2 * (CELL + PAD) + PAD
    sheet = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(sheet)
    font = get_font(16)
    font_small = get_font(13)

    draw.text((PAD, 8), f"seed {seed} — 每列一对；只评整体外观与边界形状（0–100）",
              fill="black", font=font)
    for c in range(N_COLS):
        x = LABEL_W + PAD + c * (CELL + PAD)
        draw.text((x + 4, 8), f"#{c + 1}", fill="black", font=font_small)

    # 每列只掷一次硬币；A/B 两行共用同一结果
    orig_is_a = [rng.random() < 0.5 for _ in range(N_COLS)]
    for c, flag in enumerate(orig_is_a):
        key[str(c)] = {"A": "orig" if flag else "tone",
                       "B": "tone" if flag else "orig"}

    for row, tag in enumerate(("A", "B")):
        y = BAR + row * (CELL + PAD)
        draw.text((PAD, y + CELL // 2 - 10), tag, fill="black", font=font)
        for c in range(N_COLS):
            x = LABEL_W + PAD + c * (CELL + PAD)
            take_orig = (tag == "A") == orig_is_a[c]
            src = orig[c] if take_orig else tone[c]
            sheet.paste(load(src), (x, y))
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    JUDGE.mkdir(parents=True, exist_ok=True)
    rng = random.Random(RNG_SEED)
    all_keys = {}
    for seed in SEEDS:
        key = {}
        sheet = make_sheet(seed, key, rng)
        all_keys[str(seed)] = key
        if args.dry_run:
            print(f"[dry-run] seed{seed}: {sheet.size}")
            continue
        out = JUDGE / f"tone_blind_seed{seed}.png"
        sheet.save(out)
        print(f"写入: {out}  {sheet.size}")

    if args.dry_run:
        return 0

    (JUDGE / "tone_blind_key.json").write_text(
        json.dumps(all_keys, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = JUDGE / "tone_blind_score_template.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["seed", "column", "A_整体外观", "A_边界形状",
                     "B_整体外观", "B_边界形状", "偏好(A/B/平)", "备注"])
        for seed in SEEDS:
            for c in range(N_COLS):
                wr.writerow([seed, c + 1, "", "", "", "", "", ""])

    print(f"写入: {JUDGE / 'tone_blind_key.json'}")
    print(f"写入: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
