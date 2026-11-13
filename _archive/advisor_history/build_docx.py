# -*- coding: utf-8 -*-
"""Convert the 2026-11-09 advisor report Markdown to a compact DOCX.

Run from this directory:  python build_docx.py
"""
import subprocess
import sys
from pathlib import Path

import docx
from docx.shared import Pt, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = Path(__file__).resolve().parent
SRC = HERE / "汇报_20261109.md"
DST = HERE / "汇报_20261109.docx"

subprocess.run(["pandoc", str(SRC), "-o", str(DST), "--from", "gfm"], check=True)

d = docx.Document(str(DST))

def set_font(style, name="等线", size=None, bold=None):
    style.font.name = name
    if size is not None:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), name)

set_font(d.styles["Normal"], size=10.5)
for sname in ("Heading 1", "Heading 2", "Heading 3", "Title"):
    if sname in d.styles:
        set_font(d.styles[sname], name="微软雅黑")

for section in d.sections:
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)

def add_table_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "999999")
        borders.append(el)
    tblPr.append(borders)

for table in d.tables:
    try:
        table.style = "Table Grid"
    except KeyError:
        add_table_borders(table)
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)

d.save(str(DST))
print(f"wrote {DST}")
