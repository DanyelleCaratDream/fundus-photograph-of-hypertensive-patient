# -*- coding: utf-8 -*-
"""生成 T3 合成池质量审计材料：接触表（8 张/页）+ 评分表。

输入：fundus/t3_synth_128、fundus/t3_synth_256（各 32 张，同名条件配对）
输出：CFM/judgment/t3_pool_audit_20261117/
    contact_128_page1..4.png / contact_256_page1..4.png
    评分表_T3合成池质量.xlsx
    README.md

用法（仓库根目录）：
    python -X utf8 generate_project/deep_learning/Fundus-FlowMatching/CFM/tools/t3_pool_audit_sheets.py
"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[5]
POOLS = [("128", ROOT / "fundus/t3_synth_128"),
         ("256", ROOT / "fundus/t3_synth_256")]
OUT = ROOT / "generate_project/deep_learning/Fundus-FlowMatching/CFM/judgment/t3_pool_audit_20261117"

CELL = 300          # 单格宽
IMG = 280           # 图边长
LABEL_H = 34
COLS, ROWS = 2, 4   # 每页 8 张
MARGIN = 16


def _font(size=18):
    for p in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def list_conditions(pool: Path):
    items = []
    for p in sorted(pool.iterdir()):
        if p.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        m = re.match(r"seed(\d+)_sample_(\d+)", p.stem)
        if not m:
            continue
        items.append((int(m.group(1)), int(m.group(2)), p))
    items.sort(key=lambda x: (x[0], x[1]))
    return items


def contact_sheet(tag: str, items, page: int, out: Path):
    page_items = items[(page - 1) * COLS * ROWS: page * COLS * ROWS]
    w = MARGIN * 2 + COLS * CELL
    h = MARGIN * 2 + ROWS * (IMG + LABEL_H)
    canvas = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(canvas)
    f = _font(15)
    for i, (seed, idx, path) in enumerate(page_items):
        r, c = divmod(i, COLS)
        x = MARGIN + c * CELL
        y = MARGIN + r * (IMG + LABEL_H)
        with Image.open(path) as im:
            im = im.convert("RGB").resize((IMG, IMG), Image.LANCZOS)
            canvas.paste(im, (x + (CELL - IMG) // 2, y))
        cond = f"S{seed:04d}-{idx:02d}  [{tag}]"
        draw.text((x + (CELL - draw.textlength(cond, font=f)) / 2, y + IMG + 6),
                  cond, fill="black", font=f)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=95)
    return len(page_items)


def build_xlsx(items):
    wb = Workbook()
    ws = wb.active
    ws.title = "评分"
    headers = ["条件ID", "生成seed", "样本序号",
               "视盘_128", "视盘_256", "过生成_128", "过生成_256",
               "亮度_128", "亮度_256", "备注"]
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        ws.cell(row=1, column=c).font = Font(bold=True)
        ws.cell(row=1, column=c).alignment = Alignment(horizontal="center")
    for i, (seed, idx, _) in enumerate(items, 1):
        ws.append([f"C{i:02d}", seed, idx, None, None, None, None, None, None, ""])
    widths = [9, 10, 9, 10, 10, 11, 11, 10, 10, 26]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"

    scale = wb.create_sheet("量表")
    scale.append(["项目", "取值", "含义"])
    for c in range(1, 4):
        scale.cell(row=1, column=c).font = Font(bold=True)
    rows = [
        ("视盘可见", "0", "不可见"),
        ("视盘可见", "1", "部分可见 / 模糊"),
        ("视盘可见", "2", "清晰"),
        ("血管过生成", "0", "无（与典型真实图相当）"),
        ("血管过生成", "1", "轻度：血管数量偏多"),
        ("血管过生成", "2", "明显：密集成团、超出真实图可达程度"),
        ("亮度", "0", "偏暗"),
        ("亮度", "1", "适中"),
        ("亮度", "2", "偏亮"),
        ("不确定", "留空", "看不清或无法判断时留空，不强行填"),
    ]
    for r in rows:
        scale.append(list(r))
    for i, w in enumerate([14, 10, 46], 1):
        scale.column_dimensions[get_column_letter(i)].width = w
    return wb


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    base = list_conditions(POOLS[0][1])
    if len(base) != 32:
        raise SystemExit(f"合成池应为 32 张，实际 {len(base)}")
    names = {p.name for _, _, p in base}
    for tag, pool in POOLS:
        items = list_conditions(pool)
        if len(items) != 32 or {p.name for _, _, p in items} != names:
            raise SystemExit(f"{pool} 与 128 池文件名不一致")
        n_pages = (len(items) + COLS * ROWS - 1) // (COLS * ROWS)
        for page in range(1, n_pages + 1):
            out = OUT / f"contact_{tag}_page{page}.png"
            contact_sheet(tag, items, page, out)
        print(f"{tag}: {n_pages} 页")
    build_xlsx(base).save(OUT / "评分表_T3合成池质量.xlsx")
    (OUT / "README.md").write_text(
        "# T3 合成池质量审计材料（2026-11-17）\n\n"
        "## 材料\n\n"
        "- `contact_128_page1-4.png`、`contact_256_page1-4.png`：每页 8 张，按生成 seed/样本序号排序。\n"
        "- `评分表_T3合成池质量.xlsx`：每个条件一行，128/256 分开评。\n\n"
        "## 评分方法\n\n"
        "对每个条件的两个尺寸分别评三项：\n\n"
        "- 视盘可见：0 不可见 / 1 部分或模糊 / 2 清晰\n"
        "- 血管过生成：0 无 / 1 轻度偏多 / 2 明显超出真实图可达程度\n"
        "- 亮度：0 偏暗 / 1 适中 / 2 偏亮\n\n"
        "看不清就留空，不强行填。评分者：作者本人。\n\n"
        "## 边界\n\n"
        "- 这是**描述性质量审计**，不改变 DL-EX-032 的预注册设计与样本池。\n"
        "- 不据此剔除图片；结果只用于解释 T3 与写作局限。\n"
        "- 32 个条件 = 4 个生成 seed × 8 个样本；128/256 同名文件是同一条件。\n",
        encoding="utf-8")
    print(f"OK → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
