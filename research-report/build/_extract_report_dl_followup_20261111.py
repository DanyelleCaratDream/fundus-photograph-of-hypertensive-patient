#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 REPORT_DL.docx 摘出「FiLM 之后」的内容，生成 REPORT_DL 后续（只读源，另存新文件）。

- 边界：5.12 在老师数据上微调（D 线）起，一路到参考文献。
- 方式：打开源 → 删除边界之前的 body 元素 → 顶部加标题+说明 → 另存。
- 不改动 REPORT_DL.docx。
"""
from pathlib import Path

from docx import Document
from docx.shared import Pt

def _repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while not (p / "CLAUDE.md").exists():
        if p.parent == p:
            raise RuntimeError("未找到项目根（CLAUDE.md）")
        p = p.parent
    return p


REPO = _repo_root()
SRC = REPO / "research-report" / "REPORT_DL.docx"
DST = REPO / "research-report" / "REPORT_DL_后续.docx"

ANCHOR_PREFIX = "5.12 在老师数据上微调"

doc = Document(str(SRC))

# 1. 定位锚点标题段
anchor_p = None
for p in doc.paragraphs:
    if p.text.strip().startswith(ANCHOR_PREFIX):
        anchor_p = p._p
        break
assert anchor_p is not None, f"未找到锚点标题：{ANCHOR_PREFIX}"

# 2. 删除 body 中位于锚点之前的所有元素（段落/表格）；锚点之后的 sectPr 自动保留
body = doc.element.body
removed = 0
for child in list(body):
    if child is anchor_p:
        break
    body.remove(child)
    removed += 1
print(f"删除锚点前元素 {removed} 个")

# 3. 顶部加标题 + 说明（addparagraph 先追加到文末，再 addprevious 移到锚点前）
title = doc.add_paragraph()
tr = title.add_run("REPORT_DL 后续：FiLM 之后的实验")
tr.bold = True
tr.font.size = Pt(18)
anchor_p.addprevious(title._p)

note = doc.add_paragraph()
nr = note.add_run(
    "本文档摘录自《REPORT_DL.docx》第 5.12 节起，内容原样未改，"
    "供老师快速查看 2026-10 之后的进展；全文见项目组文档 REPORT_DL.docx。"
)
nr.italic = True
nr.font.size = Pt(9)
anchor_p.addprevious(note._p)

doc.save(str(DST))
print(f"已保存：{DST}")
