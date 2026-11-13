#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 A 域审计相关配图（2026-11-11）
  1) fig_leakage_demo.png —— 目标域 severe 图与其 A 域换壳副本并排（注明 128RGB mse）
  2) fig_audit_flow.png  —— 330 → 299 → 258 的数量溯源与 41 张排除的构成
  3) fig_pair_check_20.png —— 20 对 RGB/骨架叠加抽查拼图（复制产物）
输出目录：research-report/figures/
"""
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

def _repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while not (p / "CLAUDE.md").exists():
        if p.parent == p:
            raise RuntimeError("未找到项目根（CLAUDE.md）")
        p = p.parent
    return p


REPO = _repo_root()
FIG = REPO / "research-report/figures"
FIG.mkdir(exist_ok=True)
A_DIR = REPO / "fundus/_all_images_ORIGINAL"
T_DIR = REPO / "fundus/hrsevere_61_sq128"
PAIR_DIR = REPO / "research-report/audit/a_domain_20261111/a_domain_pair_check_20261111"


def load_rgb(p, size=180):
    return np.asarray(Image.open(p).convert("RGB").resize((size, size), Image.LANCZOS))


def fig_leakage():
    """挑 4 组'目标域图 ↔ A 域换壳副本'，展示它们视觉上就是同一张照片。"""
    # 从闭合表复算得到的配对（mse 最小者）
    pairs = [("62e5366cb967fa9d728bd150fe39708c798a0530", "HRSRC_ATLAS_158_A", 2.9),
             ("f40442bb45d1bd431e4a51375ebe1f7253cd1648", "HRSRC_ATLAS_165_A", 3.5),
             ("80036", "HRSRC_CASE_181_A", 3.3),
             ("101a775efe69f6fd9d6766d5ffd592c8d6569891", "HRSRC_ATLAS_153_A", 2.2)]
    fig, axes = plt.subplots(2, len(pairs), figsize=(11.2, 6.2))
    for i, (t, a, mse) in enumerate(pairs):
        tp = T_DIR / f"{t}.png"
        ap = next(A_DIR.glob(f"{a}.*"))
        axes[0, i].imshow(load_rgb(tp)); axes[0, i].axis("off")
        axes[0, i].set_title(f"目标域 severe\n{t[:16]}…", fontsize=9)
        axes[1, i].imshow(load_rgb(ap)); axes[1, i].axis("off")
        axes[1, i].set_title(f"A 域副本 {a}\n128RGB mse={mse}", fontsize=9, color="#b30000")
    fig.text(0.5, 0.005, "上排：61 张目标域 HR severe 图；下排：A 域池中与之同一张照片的不同编码副本"
             "（mse 2–4，远低于同眼异帧的 56+）", ha="center", fontsize=9.5)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.90, bottom=0.09, wspace=0.05, hspace=0.32)
    fig.savefig(FIG / "fig_leakage_demo.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("[fig] fig_leakage_demo.png")


def fig_audit_flow():
    """330 → 299 → 258 的瀑布图 + 41 张排除构成。"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6), gridspec_kw={"width_ratios": [1.35, 1]})

    labels = ["旧 A 域\n实际用图", "作者淘汰\n31 张", "现存\n文件", "md5 重复\n20 张",
              "跨池换壳\n19 张", "池内换壳\n2 张", "A_clean\n冻结"]
    vals = [330, -31, 299, -20, -19, -2, 258]
    colors = ["#4472c4", "#c00000", "#4472c4", "#e07b39", "#e07b39", "#e07b39", "#2e7d32"]
    bottom, x = 0, np.arange(len(vals))
    running = 0
    for i, (lab, v, c) in enumerate(zip(labels, vals, colors)):
        if i in (0, 2, 6):                       # 绝对值柱
            ax1.bar(i, v, color=c, width=0.62)
            ax1.text(i, v + 8, str(v), ha="center", fontsize=11, fontweight="bold")
            running = v
        else:                                    # 减少柱
            ax1.bar(i, -v, bottom=running + v, color=c, width=0.62)
            ax1.text(i, running + v / 2, str(-v), ha="center", va="center",
                     fontsize=10, color="white", fontweight="bold")
            running = running + v
    ax1.set_xticks(x); ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel("图像数量"); ax1.set_ylim(0, 360)
    ax1.set_title("A 域训练池的数量溯源：330 → 299 → 258", fontsize=11)
    ax1.grid(axis="y", alpha=0.25)
    for i in (1, 3, 4, 5):
        ax1.axvline(i - 0.5, color="white", lw=0.8)

    # 右：41 张排除的构成（含重叠关系）
    ax2.barh([0], [20], color="#e07b39", label="md5 字节级重复（字典序靠后）")
    ax2.barh([1], [19], color="#c0504d", label="跨池换壳新增排除（主副本）")
    ax2.barh([2], [2], color="#9bbb59", label="池内换壳")
    ax2.barh([0], [10], left=10, color="#7f7f7f", hatch="//", edgecolor="white",
             label="←其中 10 个副本另有字节孪生，已算在 md5 一栏")
    ax2.set_yticks([0, 1, 2])
    ax2.set_yticklabels(["md5 重复", "跨池换壳", "池内换壳"], fontsize=9.5)
    ax2.set_xlabel("排除张数"); ax2.set_xlim(0, 26)
    ax2.set_title("共排除 41 张（20 + 19 + 2，不重复计数）", fontsize=11)
    ax2.legend(fontsize=8, loc="upper right", framealpha=0.95)
    ax2.set_ylim(-0.6, 2.6)
    ax2.grid(axis="x", alpha=0.25)
    for y, v in zip([0, 1, 2], [20, 19, 2]):
        ax2.text(v + 0.4, y, str(v), va="center", fontsize=10, fontweight="bold")

    fig.tight_layout()
    fig.savefig(FIG / "fig_audit_flow.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("[fig] fig_audit_flow.png")


def fig_pair_copy():
    src = PAIR_DIR / "montage_20.png"
    if src.exists():
        shutil.copy(src, FIG / "fig_pair_check_20.png")
        print("[fig] fig_pair_check_20.png <-", src)
    else:
        print("[WARN] montage_20.png 不存在")


if __name__ == "__main__":
    fig_leakage()
    fig_audit_flow()
    fig_pair_copy()
