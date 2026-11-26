#!/usr/bin/env python
"""T1@128 vs T1-256 盲评拼图（2026-11-14）

口径（老师确认的盲评 6 条规则）
  * 4 seed × 8 固定条件全展示，每列一个条件
  * **行级随机**（协议 §3 第 1 条）：每个 seed 整行随机标 A/B，A 行 = 同一实验的 8 列，
    B 行 = 另一实验的 8 列 → 可以整行整体评；key 单独存，评分前不揭盲
  * T1@128 用 Lanczos 放大到 256 显示，与 T1-256 原生 256 同尺寸比较
  * 评分五维 1–5：血管细节 / 视盘结构 / 伪影 / 多样性 / 整体

输出（默认 judgment/t1_256/）
  blind_sheet_seed{S}.png   条件 + A + B 三行 × 8 列（192 seed 一张，便于逐张打分）
  blind_key.json             逐列揭盲表（评分完成前不要打开）
  blind_score_template.csv   空白评分表（可直接填）

用法
  python tools/make_t1_256_blind_sheet.py --dry-run
  python tools/make_t1_256_blind_sheet.py
"""
import argparse
import csv
import datetime as dt
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
FONT_CANDIDATES = (
    "C:/Windows/Fonts/msyh.ttc",     # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",   # 黑体
    "C:/Windows/Fonts/simsun.ttc",   # 宋体
)


def get_font(size: int = 16):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()
SEEDS = (42, 1042, 2042, 3042)
N_COLS = 8
T1_PATTERN = "t1/cfm128_hrsevere_t1_ac_raw_seed{seed}/singles"
T256_PATTERN = "t1_256/cfm256_hrsevere_t1_ac_raw_seed{seed}/singles"

CELL = 256          # 显示尺寸 = 256 原生，128 图 Lanczos 放大
LABEL_W = 96
PAD = 6
BAR = 30
RNG_SEED = 20261114  # 决定 A/B 随机分配的固定种子（仅影响分组，不影响图像）

DIMS = ("vessel", "disc", "artifact", "diversity", "overall")


def sorted_pngs(d: Path, n: int = N_COLS):
    return sorted(d.glob("*.png"))[:n]


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB").resize((CELL, CELL), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-dir", default=str(CFM / "judgment"))
    ap.add_argument("--cond-dir", default=str(CFM / "data/conditions_hrsevere_61_256"),
                    help="条件行显示用的 mask（默认 256 版，与 T1-256 训练条件一致）")
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    ap.add_argument("--out", default=str(CFM / "judgment/t1_256"))
    ap.add_argument("--dry-run", action="store_true", help="只检查文件，不写图")
    ap.add_argument("--force-key", action="store_true",
                    help="允许覆盖 A/B 映射与已有 blind_key.json 不同的情况（默认拒绝）")
    a = ap.parse_args()

    judge, out = Path(a.judge_dir), Path(a.out)
    conds = sorted_pngs(Path(a.cond_dir))
    if len(conds) != N_COLS:
        print(f"[FAIL] 条件图数量 {len(conds)} != {N_COLS}: {a.cond_dir}")
        return 1
    print(f"条件：{len(conds)} 张（{conds[0].name} … {conds[-1].name}）")

    # 先做完整性检查，缺任何一张都不出图
    plan = []
    missing = []
    for s in a.seeds:
        d128 = judge / T1_PATTERN.format(seed=s)
        d256 = judge / T256_PATTERN.format(seed=s)
        f128, f256 = sorted_pngs(d128), sorted_pngs(d256)
        if len(f128) != N_COLS or len(f256) != N_COLS:
            missing.append(f"seed{s}: T1@128={len(f128)}/8, T1-256={len(f256)}/8")
        elif [x.name for x in f128] != [x.name for x in f256]:
            missing.append(f"seed{s}: 两侧文件名不一致")
        else:
            plan.append((s, f128, f256))
    if missing:
        print("[FAIL] 文件不完整，未生成：")
        for m in missing:
            print("   ", m)
        return 1
    for s, _, _ in plan:
        print(f"seed {s}: 8 对就绪")

    if a.dry_run:
        print("[dry-run] 不写文件")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(RNG_SEED)

    # A/B 映射先整体算出，再画图；与绘图逻辑解耦，便于和已有 key 比对。
    # 行级随机（协议 §3 第 1 条）：每个 seed 整行随机，A 行 = 一个实验的全部 8 列，
    # B 行 = 另一个实验的全部 8 列 → 可以整行整体评。
    mapping = {}
    for s, f128, f256 in plan:
        top = "t1_128" if rng.random() < 0.5 else "t1_256"
        bottom = "t1_256" if top == "t1_128" else "t1_128"
        mapping[f"seed{s}"] = {"A": top, "B": bottom}

    # 已存在 key 且映射不同 → 拒绝（防止把已看过的图悄悄换了 A/B）
    kp = out / "blind_key.json"
    if kp.exists() and not a.force_key:
        old_items = json.loads(kp.read_text(encoding="utf-8")).get("items")
        if old_items != mapping:
            print("[FAIL] 现有 blind_key.json 的 A/B 映射与本次不同，拒绝覆盖。")
            print("       如确需重做盲评（旧评分作废），加 --force-key")
            return 1

    key = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "rng_seed": RNG_SEED,
        "protocol": "行级随机：每个 seed 整行随机，A=上行、B=下行；A/B 之一为 t1_128"
                    "（Lanczos 放大到 256），另一为 t1_256（原生 256）",
        "display_cell": CELL,
        "items": mapping,
    }

    width = LABEL_W + N_COLS * (CELL + PAD) + PAD
    score_rows = []

    for s, f128, f256 in plan:
        header_h = BAR
        height = header_h + 3 * (CELL + PAD + BAR) + PAD
        sheet = Image.new("RGB", (width, height), "white")
        font = get_font(18)
        dr = ImageDraw.Draw(sheet)
        dr.text((8, 8), f"seed {s} — A/B 盲评（T1@128 放大 vs T1-256）", fill="black", font=font)

        y = header_h
        for label, files in (("条件", conds), ("A", None), ("B", None)):
            dr.text((6, y + CELL // 2), label, fill="black", font=font)
            if files is not None:
                for j, f in enumerate(files):
                    sheet.paste(load(f), (LABEL_W + j * (CELL + PAD), y))
            y += CELL + PAD + BAR

        # 按预先算好的映射贴图（整行 = 一个实验）
        ab = mapping[f"seed{s}"]
        yA, yB = header_h + (CELL + PAD + BAR), header_h + 2 * (CELL + PAD + BAR)
        for j in range(N_COLS):
            im_of = {"t1_128": load(f128[j]), "t1_256": load(f256[j])}
            sheet.paste(im_of[ab["A"]], (LABEL_W + j * (CELL + PAD), yA))
            sheet.paste(im_of[ab["B"]], (LABEL_W + j * (CELL + PAD), yB))

        row = {"seed": s, "prefer": ""}
        for side in ("A", "B"):
            for dim in DIMS:
                row[f"{side}_{dim}"] = ""
        score_rows.append(row)

        p = out / f"blind_sheet_seed{s}.png"
        sheet.save(p)
        print(f"已生成 {p}（{width}×{height}，A 行 = 8 列同一实验）")

    kp = out / "blind_key.json"
    kp.write_text(json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {kp}（评分完成前不要打开）")

    cp = out / "blind_score_template.csv"
    fields = ["seed", "prefer"] + [f"{s}_{d}" for s in ("A", "B") for d in DIMS]
    with cp.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(score_rows)
    print(f"已生成 {cp}（{len(score_rows)} 行 = 每 seed 一行，整行整体评）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
