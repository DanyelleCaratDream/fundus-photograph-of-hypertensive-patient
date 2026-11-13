#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 5 张超宽对比图改成上下两段版（2026-11-11）

做法：自动检测纵向"背景缝"（整列为背景色的位置），在中点附近的缝处切成左右两半，
再上下拼接。适用于多面板拼图与多子图柱状图，不改变任何内容，只改版面长宽比。

输出：research-report/figures/vert_<原名>.png
"""
from pathlib import Path

import numpy as np
from PIL import Image

def _repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while not (p / "CLAUDE.md").exists():
        if p.parent == p:
            raise RuntimeError("未找到项目根（CLAUDE.md）")
        p = p.parent
    return p


REPO = _repo_root()
OUT = REPO / "research-report/figures"
FIG = REPO / "research-report/figures"
MEDIA = REPO / "research-report/_media_dl"
CFM = REPO / "generate_project/deep_learning/Fundus-FlowMatching/CFM"
J20 = REPO / "generate_project/deep_learning/Fundus-Diffusion/ddpm/judgment_20261020"

TARGETS = {
    "vert_fig_bdomain.png": MEDIA / "fig_bdomain.png",
    "vert_color_metrics.png": FIG / "color_metrics.png",
    "vert_weight_misalign.png": CFM / "judgment/weight_misalign_demo.png",
    "vert_b1a_vs_d3_native.png": J20 / "b1a_vs_d3_native.png",
    "vert_b1b500_vs_real.png": J20 / "b1b500_vs_real.png",
}


def bg_color(a):
    """取四条边里出现最多的颜色作为背景色。"""
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    colors, counts = np.unique(border.reshape(-1, border.shape[-1]), axis=0, return_counts=True)
    return colors[counts.argmax()]


def find_gaps(a, tol=10):
    """返回背景缝（列号区间）列表。"""
    bg = bg_color(a).astype(np.int16)
    diff = np.abs(a.astype(np.int16) - bg).max(axis=2)      # [H,W]
    col_bg = (diff <= tol).mean(axis=0)                     # 每列背景占比
    # 只认真面板缝：整列几乎全是背景（>=0.999），避免切在柱状图柱与柱之间
    is_gap = col_bg > 0.999
    gaps, start = [], None
    for x, v in enumerate(is_gap):
        if v and start is None:
            start = x
        elif not v and start is not None:
            gaps.append((start, x - 1)); start = None
    if start is not None:
        gaps.append((start, len(is_gap) - 1))
    return gaps


def main():
    for name, src in TARGETS.items():
        if not src.exists():
            print(f"[WARN] 缺文件 {src}"); continue
        im = Image.open(src).convert("RGB")
        a = np.array(im)
        h, w = a.shape[:2]
        gaps = find_gaps(a)
        # 候选缝中心，要求不是贴边的整列
        cands = [((s + e) // 2) for s, e in gaps if e - s >= 6 and 0.15 * w < (s + e) / 2 < 0.85 * w]
        split = min(cands, key=lambda c: abs(c - w / 2)) if cands else w // 2
        bg = tuple(int(v) for v in bg_color(a))
        left, right = a[:, :split], a[:, split:]
        body_h = max(left.shape[0], right.shape[0])
        pad = 10
        canvas = np.full((body_h * 2 + pad, max(left.shape[1], right.shape[1]), 3), bg, np.uint8)
        canvas[:left.shape[0], :left.shape[1]] = left
        y0 = left.shape[0] + pad
        canvas[y0:y0 + right.shape[0], :right.shape[1]] = right
        out = OUT / name
        Image.fromarray(canvas).save(out)
        print(f"[ok] {name}: {w}x{h} -> {split}+{w-split} 堆叠 -> "
              f"{canvas.shape[1]}x{canvas.shape[0]} (比例 {canvas.shape[1]/canvas.shape[0]:.2f})")


if __name__ == "__main__":
    main()
