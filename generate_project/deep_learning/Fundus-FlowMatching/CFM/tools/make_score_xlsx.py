#!/usr/bin/env python
"""把评分表做成 Excel（.xlsx），供作者直接填。

两个目标
  t1_256 : 由 blind_score_template.csv 转换（见 make_t1_256_blind_sheet.py）
           → judgment/t1_256/评分表_T1_256盲评.xlsx
           盲评：只出现 A / B，不暴露哪行是 T1@128、哪行是 T1-256
  t1     : 由 judgment/t1/评分表_T1.md 的四张表转换
           → judgment/t1/评分表_T1.xlsx

Excel 特性
  * 中文表头；分值列 1–5 整数下拉校验；偏好列 A/B/平手 下拉
  * 表头冻结 + 自动筛选；输入格浅黄底、表头深蓝底
  * 末页「说明」写口径与对应图

用法
  python tools/make_score_xlsx.py --target t1_256
  python tools/make_score_xlsx.py --target t1
"""
import argparse
import csv
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
DIMS = ("overall", "vessel", "disc", "artifact", "diversity")
DIM_ZH = {"overall": "整体外观", "vessel": "血管细节", "disc": "视盘结构",
          "artifact": "伪影", "diversity": "多样性"}

HDR_FILL = PatternFill("solid", fgColor="1F3864")
HDR_FONT = Font(color="FFFFFF", bold=True, size=11, name="微软雅黑")
CELL_FONT = Font(size=11, name="微软雅黑")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
NOTE_FILL = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)


def style_header(ws, row=1):
    for c in ws[row]:
        c.fill, c.font, c.alignment, c.border = HDR_FILL, HDR_FONT, CENTER, BORDER


def set_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def add_score_validation(ws, col_letters, first_row, last_row):
    dv = DataValidation(type="whole", operator="between", formula1=1, formula2=5,
                        allow_blank=True, showErrorMessage=True,
                        errorTitle="分值需为 1–5 的整数",
                        error="请输入 1、2、3、4、5（整数）")
    ws.add_data_validation(dv)
    for col in col_letters:
        dv.add(f"{col}{first_row}:{col}{last_row}")


def add_prefer_validation(ws, col_letter, first_row, last_row, options="A,B,平手"):
    dv = DataValidation(type="list", formula1=f'"{options}"', allow_blank=True,
                        showErrorMessage=True, errorTitle="请选 A / B / 平手",
                        error="只能填 A、B 或 平手")
    ws.add_data_validation(dv)
    dv.add(f"{col_letter}{first_row}:{col_letter}{last_row}")


# ---------------------------------------------------------------- T1-256 盲评
def build_t1_256():
    src = CFM / "judgment/t1_256/blind_score_template.csv"
    if not src.is_file():
        print(f"[FAIL] 找不到 {src}，先跑 make_t1_256_blind_sheet.py")
        return 1
    rows = list(csv.DictReader(src.open(encoding="utf-8-sig")))
    out = CFM / "judgment/t1_256/评分表_T1_256盲评.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "评分"
    headers = (["seed", "对照图", "偏好（A/B/平手）"]
               + [f"A·{DIM_ZH[d]}" for d in DIMS]
               + [f"B·{DIM_ZH[d]}" for d in DIMS]
               + ["备注"])
    ws.append(headers)
    style_header(ws)

    for r in rows:
        ws.append([int(r["seed"]), f"blind_sheet_seed{r['seed']}.png", "",
                   None, None, None, None, None,
                   None, None, None, None, None,
                   ""])

    last = ws.max_row
    for row in ws.iter_rows(min_row=2, max_row=last, max_col=len(headers)):
        for c in row:
            c.font, c.border = CELL_FONT, BORDER
            c.alignment = LEFT if c.column == 2 else CENTER
            if 3 <= c.column <= 13:
                c.fill = INPUT_FILL
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{last}"
    set_widths(ws, [7, 28, 16] + [11] * 10 + [34])

    add_score_validation(ws, [get_column_letter(i) for i in range(4, 14)], 2, last)
    add_prefer_validation(ws, "C", 2, last)

    # ---- 说明页 ----
    ws2 = wb.create_sheet("说明")
    notes = [
        ("T1-256 盲评评分表（2026-11-14）", True),
        ("", False),
        ("对应图", True),
        ("judgment/t1_256/blind_sheet_seed42.png（seed 42，8 列条件）", False),
        ("judgment/t1_256/blind_sheet_seed1042.png", False),
        ("judgment/t1_256/blind_sheet_seed2042.png", False),
        ("judgment/t1_256/blind_sheet_seed3042.png", False),
        ("每张图三行：条件 mask / A / B。A、B 中有一行是 T1@128（Lanczos 放大到 256），"
         "另一行是 T1-256（原生 256）。哪行是哪个由 blind_key.json 记录，评分完成前不要打开。", False),
        ("★ 行级分组：A 行 8 列全部来自同一个实验，B 行 8 列全部来自另一个实验 → 可以把每行当作一个实验整体评。", False),
        ("", False),
        ("五维打分（1–5，整数）", True),
        ("整体外观：远看是否像真实眼底彩照", False),
        ("血管细节：血管走行、分支是否清晰明确", False),
        ("视盘结构：视盘位置、轮廓、结构是否合理（有无「像没有」）", False),
        ("伪影：分越高 = 伪影越少；含边界是否呈正圆/椭圆、异常纹理与色块", False),
        ("多样性：8 列条件是否拉得开，不是同一种图反复出现", False),
        ("", False),
        ("偏好列", True),
        ("在偏好（A/B/平手）里填 A、B 或 平手，表示该 seed 整体更喜欢哪一行。", False),
        ("", False),
        ("纪律", True),
        ("1. 4 个 seed、8 个条件全部展示，不挑图、不删 seed；", False),
        ("2. 4 个 seed 全部打分（每 seed 10 个数），缺分会拒绝汇总；", False),
        ("3. 打分完成后一次性揭盲，再运行 tools/score_t1_256_blind.py 汇总；", False),
        ("4. 尽量请老师对其中 1–2 个 seed 独立盲评，作第二评分者。", False),
    ]
    for i, (text, bold) in enumerate(notes, start=1):
        cell = ws2.cell(row=i, column=1, value=text)
        cell.font = Font(name="微软雅黑", size=11, bold=bold)
        cell.alignment = LEFT
    ws2.column_dimensions["A"].width = 110

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"已生成 {out}（{len(rows)} 行 × {len(headers)} 列，含「说明」页）")
    return 0


# ---------------------------------------------------------------- T1（T0 vs T1）
SEED_NOTES = {
    "T0": "整体真实；血管/视盘明显弱于 T1；伪影与边界不圆更严重",
    "T1": "整体真实；血管/视盘明显更好；仍需更明确的血管；视盘偶有结构性缺失感",
}


def build_t1():
    out = CFM / "judgment/t1/评分表_T1.xlsx"
    seeds = (42, 1042, 2042, 3042)

    wb = Workbook()
    ws = wb.active
    ws.title = "评分"
    headers = (["seed", "对照图", "组", "整体外观", "血管细节", "视盘结构",
                "伪影", "多样性", "备注（2026-11-13 原话摘要）"])
    ws.append(headers)
    style_header(ws)

    for s in seeds:
        for arm in ("T0", "T1"):
            note = SEED_NOTES[arm] if s == 42 else f"同 seed 42：{SEED_NOTES[arm]}"
            ws.append([s, f"T0_vs_T1_seed{s}.png", arm,
                       None, None, None, None, None, note])

    last = ws.max_row
    for row in ws.iter_rows(min_row=2, max_row=last, max_col=len(headers)):
        for c in row:
            c.font, c.border = CELL_FONT, BORDER
            c.alignment = LEFT if c.column in (2, 9) else CENTER
            if 4 <= c.column <= 8:
                c.fill = INPUT_FILL
            elif c.column == 9:
                c.fill = NOTE_FILL
    ws.freeze_panes = "D2"
    set_widths(ws, [7, 24, 7, 11, 11, 11, 11, 11, 52])
    add_score_validation(ws, ["D", "E", "F", "G", "H"], 2, last)

    # ---- 原判定页 ----
    ws2 = wb.create_sheet("原判定（2026-11-13）")
    ws2.append(["维度", "T0 vs T1（作者定性）", "说明"])
    style_header(ws2)
    summary = [
        ("整体外观", "持平", "两者「远看」都真实；T1 不劣化"),
        ("血管细节", "T1 明显更好", "但 T1 仍需更明确地画血管"),
        ("视盘结构", "T1 明显更好", "T1 视盘偶有「结构上像没有」的稳定性问题"),
        ("伪影", "T1 更少", "T1 仍有边界不呈完整圆形/椭圆，但比 T0 轻"),
        ("多样性", "T1 更好", "—"),
    ]
    for row in summary:
        ws2.append(row)
    for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row, max_col=3):
        for c in row:
            c.font, c.border, c.alignment = CELL_FONT, BORDER, LEFT
    set_widths(ws2, [14, 20, 60])
    ws2.append([])
    ws2.append(["结论", "迁移有效 = 是（血管细节 / 视盘结构至少一项稳定优于 T0，整体外观不劣化）", ""])
    for c in ws2[ws2.max_row]:
        c.font, c.alignment = CELL_FONT, LEFT

    # ---- 说明页 ----
    ws3 = wb.create_sheet("说明")
    notes = [
        ("T1 人工评分表（补分值）", True),
        ("", False),
        ("对应图", True),
        ("judgment/t1/T0_vs_T1_seed42.png（三行：条件 mask / T0 / T1，8 列条件）", False),
        ("judgment/t1/T0_vs_T1_seed1042.png", False),
        ("judgment/t1/T0_vs_T1_seed2042.png", False),
        ("judgment/t1/T0_vs_T1_seed3042.png", False),
        ("", False),
        ("背景", True),
        ("2026-11-13 作者已给出逐 seed 定性判定（见「原判定」页），未逐项给 1–5 分值。", False),
        ("本表用于补分值：T0、T1 各自五维打分，不要求与定性结论一致；如有出入写在备注。", False),
        ("", False),
        ("五维打分（1–5，整数）", True),
        ("整体外观 / 血管细节 / 视盘结构 / 多样性：分越高越好", False),
        ("伪影：分越高 = 伪影越少", False),
        ("", False),
        ("备注", True),
        ("已预填 2026-11-13 的原话摘要，可对照，也可改写。", False),
    ]
    for i, (text, bold) in enumerate(notes, start=1):
        cell = ws3.cell(row=i, column=1, value=text)
        cell.font = Font(name="微软雅黑", size=11, bold=bold)
        cell.alignment = LEFT
    ws3.column_dimensions["A"].width = 110

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"已生成 {out}（8 行评分 + 原判定页 + 说明页）")
    return 0


# ---------------------------------------------------------------- T0 内部检查点
def _style_score_grid(ws, first_row, last_row, score_cols, left_cols=()):
    for row in ws.iter_rows(min_row=first_row, max_row=last_row, max_col=ws.max_column):
        for c in row:
            c.font, c.border = CELL_FONT, BORDER
            c.alignment = LEFT if c.column in left_cols else CENTER
            if c.column in score_cols:
                c.fill = INPUT_FILL
    letters = [get_column_letter(i) for i in score_cols]
    add_score_validation(ws, letters, first_row, last_row)


def _add_notes_sheet(ws, notes, width=110):
    for i, (text, bold) in enumerate(notes, start=1):
        cell = ws.cell(row=i, column=1, value=text)
        cell.font = Font(name="微软雅黑", size=11, bold=bold)
        cell.alignment = LEFT
    ws.column_dimensions["A"].width = width


DIM_COLS = [f"{DIM_ZH[d]}" for d in DIMS]


def build_t0_ckpt():
    out = CFM / "judgment/评分表_T0检查点.xlsx"
    seeds = (42, 1042, 2042, 3042)
    ckpts = (
        ("9,600 步", "e2/E2_9600_4seeds.png", "checkpoint 9600（E2）"),
        ("15,000 步", "e2/E2_15000_4seeds.png", "checkpoint 15000（E2）"),
        ("20,010 步（T0 冻结）", "e3/E3_20000_4seeds.png", "final 20,010（E3）"),
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "评分"
    ws.append(["检查点", "seed", "对照图", "图内行"] + DIM_COLS + ["备注"])
    style_header(ws)
    for label, png, _note in ckpts:
        for i, s in enumerate(seeds, start=1):
            ws.append([label, s, png, f"第 {i} 行（seed{s}）",
                       None, None, None, None, None, ""])
    last = ws.max_row
    _style_score_grid(ws, 2, last, score_cols=(5, 6, 7, 8, 9), left_cols=(3, 4, 10))
    ws.freeze_panes = "E2"
    set_widths(ws, [22, 7, 26, 18] + [11] * 5 + [34])
    ws.auto_filter.ref = f"A1:J{last}"

    # ---- 30k 扫描页（seed 42 单 seed）----
    ws2 = wb.create_sheet("30k 扫描（seed42）")
    ws2.append(["检查点（步数）", "对照图", "图内行"] + DIM_COLS + ["备注"])
    style_header(ws2)
    scan = ("15,000", "20,010", "21,000", "22,500", "24,000",
            "25,500", "27,000", "28,500", "30,000")
    for i, label in enumerate(scan, start=1):
        ws2.append([label, "scan30k/scan_15k_to_30k.png", f"第 {i} 行",
                    None, None, None, None, None, ""])
    last2 = ws2.max_row
    _style_score_grid(ws2, 2, last2, score_cols=(4, 5, 6, 7, 8), left_cols=(2, 9))
    ws2.freeze_panes = "D2"
    set_widths(ws2, [16, 30, 12] + [11] * 5 + [34])

    ws3 = wb.create_sheet("说明")
    _add_notes_sheet(ws3, [
        ("T0（HR-severe 61 张 @128）内部检查点评分表", True),
        ("", False),
        ("对应图", True),
        ("judgment/e2/E2_9600_4seeds.png（4 行 = seed42 / 1042 / 2042 / 3042，每行 8 个固定条件，无条件行）", False),
        ("judgment/e2/E2_15000_4seeds.png（同上）", False),
        ("judgment/e3/E3_20000_4seeds.png（同上）", False),
        ("judgment/scan30k/scan_15k_to_30k.png（9 行检查点，seed 42）", False),
        ("", False),
        ("口径", True),
        ("非盲评：检查点按步数从旧到新排列，已知各行的训练步数。", False),
        ("「评分」页 = 3 个检查点 × 4 seed = 12 行；「30k 扫描」页 = 20,010 → 30,000 的逐检查点（seed 42）。", False),
        ("五维 1–5：整体外观 / 血管细节 / 视盘结构 / 伪影（分越高=越少）/ 多样性。", False),
        ("参考：真实 61 张的梯度能量 0.0156、中心/外环 1.80；20,010 步为 0.0139 / 2.50。", False),
        ("", False),
        ("已有定性结论（2026-11-09/10，供对照，可改）", True),
        ("9,600：raw 稳定、有结构底子，但细节不足（视盘过亮、血管级细节欠缺）。", False),
        ("15,000→20,010：眼底基础圆形轮廓明显改善，边界凹陷大幅减少。", False),
        ("20,010→30,000：不是单调变好，是逐检查点震荡。", False),
    ])

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"已生成 {out}（12 行评分 + 30k 扫描 9 行 + 说明页）")
    return 0


# ---------------------------------------------------------------- DL-EX-028 四格
def build_t1_explore():
    out = CFM / "judgment/t1_explore/评分表_T1推理侧四格.xlsx"
    variants = ("raw × 50（主结果）", "EMA × 50", "raw × 100", "EMA × 100")

    wb = Workbook()
    ws = wb.active
    ws.title = "评分"
    ws.append(["seed", "变体", "对照图", "图内行"] + DIM_COLS + ["备注"])
    style_header(ws)
    for s in (42, 1042):
        for i, v in enumerate(variants, start=2):  # 第 1 行是条件
            ws.append([s, v, f"t1_explore/T1_explore_seed{s}.png",
                       f"第 {i} 行", None, None, None, None, None, ""])
    last = ws.max_row
    _style_score_grid(ws, 2, last, score_cols=(5, 6, 7, 8, 9), left_cols=(3, 4, 10))
    ws.freeze_panes = "E2"
    set_widths(ws, [7, 22, 34, 10] + [11] * 5 + [34])
    ws.auto_filter.ref = f"A1:J{last}"

    ws2 = wb.create_sheet("原判定")
    ws2.append(["项", "内容"])
    style_header(ws2)
    rows = [
        ("客观指标（2 seed 均值）", "raw×50 0.0103 / EMA×50 0.0100 / raw×100 0.0106 / EMA×100 0.0102（梯度能量）；"
                                   "中心/外环 1.406 / 1.457 / 1.407 / 1.456；多样性 MSE 0.0469 / 0.0464 / 0.0467 / 0.0466"),
        ("作者定性（2026-11-13）", "四格没有可辨识的赢家；「要不是仔细看甚至觉得都一样」。"
                                  "若强制排序，先指 raw×100、随即改选 EMA×100，判断不稳定。"),
        ("结论", "采样不是瓶颈；主结果保持 raw × 50。"),
    ]
    for r in rows:
        ws2.append(r)
    for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row, max_col=2):
        for c in row:
            c.font, c.border, c.alignment = CELL_FONT, BORDER, LEFT
    set_widths(ws2, [24, 100])

    ws3 = wb.create_sheet("说明")
    _add_notes_sheet(ws3, [
        ("DL-EX-028 T1 推理侧四格评分表（补分值）", True),
        ("", False),
        ("对应图", True),
        ("judgment/t1_explore/T1_explore_seed42.png（条件 + 4 行变体，每行 8 个固定条件）", False),
        ("judgment/t1_explore/T1_explore_seed1042.png", False),
        ("图内行顺序：raw × 50（主结果）/ EMA × 50 / raw × 100 / EMA × 100。", False),
        ("", False),
        ("口径", True),
        ("非盲评：变体名称已知，本表只补齐 2026-11-13 未给的 1–5 分值。", False),
        ("五维 1–5：整体外观 / 血管细节 / 视盘结构 / 伪影（分越高=越少）/ 多样性。", False),
        ("若四格确实分不出高下，可以给同分——结论「无可辨识差异」本身就是有效结果。", False),
    ])

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"已生成 {out}（8 行评分 + 原判定页 + 说明页）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, choices=["t1_256", "t1", "t0_ckpt", "t1_explore"])
    a = ap.parse_args()
    builders = {"t1_256": build_t1_256, "t1": build_t1,
                "t0_ckpt": build_t0_ckpt, "t1_explore": build_t1_explore}
    return builders[a.target]()


if __name__ == "__main__":
    sys.exit(main())
