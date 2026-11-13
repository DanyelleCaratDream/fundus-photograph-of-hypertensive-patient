#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 REPORT_DL.docx（v1）提取纯文本，供 paper/ 写作检索。

输出：research-report/REPORT_DL_text.txt
- 段落按文档顺序输出
- 表格转成 `| a | b |` 行，前面加 `[TABLE]` 标记
- 顶部写生成时间与“行号不稳定，引用请用节号”的提示

用法：
    python research-report/build/_extract_report_dl_text.py
"""
from datetime import date
from pathlib import Path

from docx import Document
from docx.document import Document as _Doc
from docx.table import Table
from docx.text.paragraph import Paragraph


def _repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while not (p / "CLAUDE.md").exists():
        p = p.parent
    return p


REPO = _repo_root()
SRC = REPO / "research-report" / "REPORT_DL.docx"
DST = REPO / "research-report" / "REPORT_DL_text.txt"


def iter_blocks(doc: _Doc):
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, doc)
        elif child.tag.endswith("}tbl"):
            yield Table(child, doc)


def main() -> None:
    doc = Document(str(SRC))
    out = [
        "# REPORT_DL.docx 纯文本提取",
        f"# 生成日期：{date.today().isoformat()}（来源：research-report/REPORT_DL.docx，v1）",
        "# 用途：paper/ 写作检索。行号随文档变化不稳定，引用请用节号（如 §5.10.2）。",
        "# 数字仍以 EXPERIMENTS.md / eval_data/*.json 为准，本文件不承担数字权威。",
        "",
    ]
    for block in iter_blocks(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                out.append(text)
        else:
            out.append("[TABLE]")
            for row in block.rows:
                cells = [c.text.strip().replace("\n", " / ") for c in row.cells]
                out.append("| " + " | ".join(cells) + " |")
            out.append("[/TABLE]")
    DST.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已写入 {DST}（{len(out)} 行）")


if __name__ == "__main__":
    main()
