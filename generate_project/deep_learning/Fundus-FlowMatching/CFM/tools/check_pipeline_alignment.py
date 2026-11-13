#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""训练前管线检查：同步增强后，渗出权重图是否与图像渗出区域对齐（2026-11-07）

验证修复后的 FundusDataset(augment=True)：img/cond/weight 用同一 flip/angle。
对 61 张子集抽样 8 张，算 weight>0.3 区域与图像渗出阈值区域的重叠 IoU，
并输出叠加可视化（红=权重，绿=渗出阈值）。

用法
    python tools/check_pipeline_alignment.py
输出
    CFM/judgment/pipeline_alignment_check.png
    eval_data/_audit/pipeline_alignment_check.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image, ImageDraw

CFM = Path(__file__).resolve().parents[1]
DL = CFM.parents[1]
REPO = DL.parents[1]
sys.path.insert(0, str(DL / "Fundus-Diffusion" / "ddpm"))
from train import FundusDataset  # noqa: E402


def exudate_mask(rgb01):
    """与 make_lesion_weights.py 相同的渗出判据：亮黄（红高蓝低，排除视盘）。"""
    r, g, b = rgb01[..., 0], rgb01[..., 1], rgb01[..., 2]
    return (r > 0.55) & (g > 0.38) & (b < 0.45) & ((r - b) > 0.15)


def main():
    transform = transforms.Compose([
        transforms.Resize((128, 128)), transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])
    ds = FundusDataset(str(REPO / "fundus/hrsevere_61_sq128"), transform=transform,
                       cond_root=str(CFM / "data/conditions_hrsevere_61_128"),
                       img_size=128,
                       lesion_root=str(CFM / "data/lesion_weights_hrsevere_61_256"),
                       augment=True)
    n = len(ds)
    print(f"[data] {n} 张（augment=True）")
    rng = np.random.default_rng(0)
    idxs = rng.choice(n, 8, replace=False)

    ious = []
    panels = []
    for k, idx in enumerate(idxs):
        img, cond, w, _ = ds[int(idx)]          # 都经过同步增强
        rgb01 = (img.permute(1, 2, 0).numpy() + 1) / 2          # [-1,1] -> [0,1]
        wmap = w[0].numpy()                                     # [0,1]
        mask = exudate_mask(rgb01)
        sel_w = wmap > 0.3
        if sel_w.sum() == 0:
            ious.append(None)
            continue
        # precision = 权重图命中渗出候选的比例（权重图是膨胀软区，比硬 mask 大，故用 precision）
        prec = float((sel_w & mask).sum() / max(1, sel_w.sum()))
        ious.append(prec)
        # 可视化：RGB 图 + 红=权重 + 绿=渗出阈值
        ov = (rgb01 * 255).astype(np.uint8).copy()
        ov[sel_w] = (0.6 * ov[sel_w] + 0.4 * np.array([255, 0, 0])).astype(np.uint8)
        ov[mask] = (0.6 * ov[mask] + 0.4 * np.array([0, 255, 0])).astype(np.uint8)
        panels.append((Path(ds.image_paths[int(idx)]).stem, prec, Image.fromarray(ov)))

    S, CAP = 240, 40
    canvas = Image.new("RGB", (4 * (S + 8) + 8, 2 * (S + CAP) + 16), "white")
    d = ImageDraw.Draw(canvas)
    for i, (stem, iou, im) in enumerate(panels):
        r, c = divmod(i, 4)
        x, y = 8 + c * (S + 8), 8 + r * (S + CAP)
        canvas.paste(im.resize((S, S), Image.LANCZOS), (x, y))
        d.text((x, y + S + 2), f"{stem[:14]} IoU={iou:.2f}", fill="black")
    out_png = CFM / "judgment/pipeline_alignment_check.png"
    canvas.save(out_png)
    print(f"[png] {out_png}")

    valid = [x for x in ious if x is not None]
    report = {"n": n, "sampled": len(idxs), "precision_mean": round(float(np.mean(valid)), 3),
              "precision_min": round(float(np.min(valid)), 3),
              "precision_list": [round(x, 3) if x is not None else None for x in ious],
              "empty_weight_samples": sum(1 for x in ious if x is None),
              "verdict": "PASS" if (valid and np.mean(valid) > 0.3) else "CHECK"}
    out_json = REPO / "eval_data/_audit/pipeline_alignment_check.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[json] {out_json}")
    print(f"[verdict] precision mean={report['precision_mean']} ({report['verdict']})")


if __name__ == "__main__":
    main()
