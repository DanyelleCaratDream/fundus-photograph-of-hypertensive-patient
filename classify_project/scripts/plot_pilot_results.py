"""分类器 pilot A0–A2 结果可视化（DL-EX-027）。

输入：classify_project/results/pilot_{A0,A1,A2}_20261115.json
输出：classify_project/results/pilot_20261115_plots/ 下三张图
  fig1_confusion.png   混淆矩阵（3 seed 合计，行归一化）
  fig2_metrics.png     五项指标对比（误差条=3 seed 标准差）
  fig3_qwk_seeds.png   QWK 逐 seed + 相对 A0 的差值与 MCID 判定带
用法：python -X utf8 classify_project/scripts/plot_pilot_results.py
"""
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(ROOT, "classify_project", "results")
OUT = os.path.join(RES, "pilot_20261115_plots")
os.makedirs(OUT, exist_ok=True)

DATE = "20261115"
CLASSES = ["正常", "轻度", "中度", "重度"]
ARMS = [
    ("A0", "基线 ResNet18", "#2a78d6"),
    ("A1", "+ logit adj", "#eb6834"),
    ("A2", "+ DRC", "#1baf7a"),
]
SURFACE = "#fcfcfb"
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8983"
GRID = "#e6e5e0"
MCID = 0.02

# 调色板（dataviz 技能默认实例，已跑 validate_palette.js）
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("blue_seq", BLUE_RAMP)

METRICS = [
    ("qwk", "QWK\n有序一致性"),
    ("acc", "ACC\n准确率"),
    ("balanced_acc", "BAcc\n平衡准确率"),
    ("macro_f1", "Macro-F1\n宏平均 F1"),
    ("severe_recall", "重度召回率"),
]


def load():
    data = {}
    for arm, _, _ in ARMS:
        p = os.path.join(RES, f"pilot_{arm}_{DATE}.json")
        with open(p, "r", encoding="utf-8") as f:
            data[arm] = json.load(f)
    return data


def style_axes(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)


def fig_confusion(data):
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.4), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    for ax, (arm, desc, _) in zip(axes, ARMS):
        runs = data[arm]["runs"]
        conf = np.sum([r["confusion"] for r in runs], axis=0).astype(float)
        rowsum = conf.sum(axis=1, keepdims=True)
        pct = np.divide(conf, rowsum, out=np.zeros_like(conf), where=rowsum > 0)
        ax.imshow(pct, cmap=CMAP, vmin=0, vmax=1)
        for i in range(4):
            for j in range(4):
                v = pct[i, j]
                txt = f"{v * 100:.0f}%\n({int(conf[i, j])})"
                ax.text(j, i, txt, ha="center", va="center", fontsize=8.5,
                        color="#ffffff" if v > 0.55 else INK)
        ax.set_xticks(range(4))
        ax.set_yticks(range(4))
        ax.set_xticklabels(CLASSES, fontsize=9)
        ax.set_yticklabels([f"{c}\n(n={int(n)})" for c, n in zip(CLASSES, rowsum[:, 0])],
                           fontsize=8.5)
        ax.set_xlabel("预测类别 →", fontsize=9.5, color=INK2)
        q = data[arm]["summary"]["qwk"]
        ax.set_title(f"{arm}（{desc}）\nQWK {q['mean']:.3f} ± {q['std']:.3f}",
                     fontsize=10.5, color=INK, pad=10)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
    axes[0].set_ylabel("真实类别 ↓", fontsize=9.5, color=INK2)
    fig.suptitle("混淆矩阵：3 个 seed 合计，行归一化（对角=\n答对的比例，格内括号=样本数）".replace("\n", ""),
                 fontsize=12.5, color=INK, y=1.02)
    fig.text(0.99, -0.09, "测试集 n=71（每 seed 相同划分）；行%=该真实类中被判为该预测类的比例",
             ha="right", fontsize=8, color=INK3)
    fig.tight_layout()
    p = os.path.join(OUT, "fig1_confusion.png")
    fig.savefig(p, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return p


def fig_metrics(data):
    fig, axes = plt.subplots(1, 5, figsize=(15.5, 4.0), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    x = np.arange(3)
    for ax, (key, label) in zip(axes, METRICS):
        style_axes(ax)
        means = [data[a]["summary"][key]["mean"] for a, _, _ in ARMS]
        stds = [data[a]["summary"][key]["std"] for a, _, _ in ARMS]
        colors = [c for _, _, c in ARMS]
        bars = ax.bar(x, means, width=0.62, color=colors, yerr=stds,
                      error_kw=dict(ecolor=INK3, lw=1.2, capsize=3, capthick=1.0),
                      zorder=3)
        for xi, m, s in zip(x, means, stds):
            ax.text(xi, m + s + 0.02, f"{m:.3f}", ha="center", va="bottom",
                    fontsize=8, color=INK)
        ax.set_xticks(x)
        ax.set_xticklabels([a for a, _, _ in ARMS], fontsize=9)
        ax.set_ylim(0, 1.08)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
        ax.set_axisbelow(True)
        ax.set_title(label, fontsize=10, color=INK, pad=8)
    axes[0].set_ylabel("0–1，越大越好", fontsize=9, color=INK2)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in ARMS]
    fig.legend(handles, [f"{a}  {d}" for a, d, _ in ARMS], loc="upper center",
               ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 1.04))
    fig.suptitle("五项指标对比（柱=3 seed 均值，须=标准差；纵轴从 0 起，避免夸大差异）",
                 fontsize=12.5, color=INK, y=1.10)
    fig.text(0.99, -0.04, "每 arm 3 seeds（42/52/62）× 30 epochs；测试集 n=71",
             ha="right", fontsize=8, color=INK3)
    fig.tight_layout()
    p = os.path.join(OUT, "fig2_metrics.png")
    fig.savefig(p, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return p


def fig_qwk(data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.6), dpi=200,
                                   gridspec_kw={"width_ratios": [1.05, 1]})
    fig.patch.set_facecolor(SURFACE)
    seeds = data["A0"]["seeds"]
    base = np.array([r["qwk"] for r in data["A0"]["runs"]])

    # 左：逐 seed QWK
    style_axes(ax1)
    ax1.grid(axis="y", color=GRID, lw=0.8, zorder=0)
    ax1.set_axisbelow(True)
    for (arm, desc, color), off in zip(ARMS, (-0.08, 0.0, 0.08)):
        ys = np.array([r["qwk"] for r in data[arm]["runs"]])
        ax1.plot(np.arange(3) + off, ys, "-o", color=color, lw=2, ms=8,
                 label=f"{arm} {desc}", zorder=3)
        ax1.text(2.14 + off, ys[-1], f"{arm}\n{ys[-1]:.3f}", color=color,
                 fontsize=8.5, va="center", ha="left")
    ax1.set_xticks(range(3))
    ax1.set_xticklabels([f"seed {s}" for s in seeds], fontsize=9)
    ax1.set_ylim(0.70, 0.82)
    ax1.set_ylabel("QWK", fontsize=9.5, color=INK2)
    ax1.set_title("每个 seed 单独看：三条线几乎缠在一起", fontsize=11, color=INK, pad=8)
    ax1.set_xlim(-0.35, 2.75)
    ax1.legend(loc="lower left", frameon=False, fontsize=8.5, ncol=1)

    # 右：Δ vs A0 + MCID 带
    style_axes(ax2)
    ax2.grid(axis="y", color=GRID, lw=0.8, zorder=0)
    ax2.set_axisbelow(True)
    ax2.axhspan(-MCID, MCID, color="#e6e5e0", alpha=0.9, zorder=1)
    ax2.axhline(0, color=INK3, lw=1, zorder=2)
    ax2.text(2.46, 0.0, "MCID ±0.02\n（小于此值=没实质提升）", fontsize=7.8,
             color=INK3, va="center", ha="left")
    width = 0.26
    for k, (arm, desc, color) in enumerate(ARMS[1:], start=1):
        ys = np.array([r["qwk"] for r in data[arm]["runs"]])
        d = ys - base
        ax2.bar(np.arange(3) + (k - 1.5) * width, d, width=width * 0.92,
                color=color, zorder=3, label=f"{arm} − A0")
        for xi, dv in zip(np.arange(3) + (k - 1.5) * width, d):
            ax2.text(xi, dv + 0.0015, f"{dv:+.3f}", ha="center", va="bottom",
                     fontsize=7.5, color=INK)
    ax2.set_xticks(range(3))
    ax2.set_xticklabels([f"seed {s}" for s in seeds], fontsize=9)
    ax2.set_ylim(-0.03, 0.045)
    ax2.set_ylabel("ΔQWK（相对 A0）", fontsize=9.5, color=INK2)
    ax2.set_title("差值全部落在 MCID 灰带内 → 判“无实质提升”", fontsize=11,
                  color=INK, pad=8)
    ax2.legend(loc="upper left", frameon=False, fontsize=8.5)

    fig.suptitle("A1 / A2 比 A0 好在哪？——3 个 seed 的配对差值", fontsize=12.5,
                 color=INK, y=1.02)
    fig.tight_layout()
    p = os.path.join(OUT, "fig3_qwk_seeds.png")
    fig.savefig(p, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return p


def main():
    data = load()
    paths = [fig_confusion(data), fig_metrics(data), fig_qwk(data)]
    print("\n".join(paths))
    # 控制台摘要（便于核对）
    for arm, _, _ in ARMS:
        s = data[arm]["summary"]
        print(f"{arm}: QWK {s['qwk']['mean']:.4f}±{s['qwk']['std']:.4f}  "
              f"ACC {s['acc']['mean']:.4f}  BAcc {s['balanced_acc']['mean']:.4f}  "
              f"F1 {s['macro_f1']['mean']:.4f}  SR {s['severe_recall']['mean']:.4f}")
    for arm in ("A1", "A2"):
        d = [r["qwk"] - b["qwk"] for r, b in zip(data[arm]["runs"], data["A0"]["runs"])]
        print(f"{arm}-A0 ΔQWK per seed: {[round(x, 4) for x in d]}  mean {np.mean(d):+.4f}")


if __name__ == "__main__":
    main()
