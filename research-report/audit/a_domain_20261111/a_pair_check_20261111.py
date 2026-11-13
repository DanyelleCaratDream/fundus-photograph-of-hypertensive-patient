#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A 域 RGB ↔ 血管骨架 配对抽查（2026-11-11，导师要求的 20 对叠加检查）

方法（比纯目视更硬）：条件图由 `prep_conditions.py::extract_vessel_mask` 从配对 RGB 生成。
对随机抽取的 20 对，用**同一算法**从 `fundus/a_domain_clean/<stem>.jpg` 重新推导 mask，
与存档 `CFM/data/conditions_a_domain_clean/<stem>.png` 做像素级比对：

  - identity 一致率（预期 ~1.0：配对正确 + 方向位置一致时可逐像素复现）
  - 对照组：flipH / flipV / rot180 / transpose / 平移(±3px) / 错配其他图的推导结果
  - 同时输出叠加图（RGB + 条件结构红色高亮）供人工复核

输出目录：research-report/audit/a_domain_20261111/a_domain_pair_check_20261111/
  overlay_<stem>.png ×20、montage_20.png、pair_check_result.json
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
def _repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while not (p / "CLAUDE.md").exists():
        if p.parent == p:
            raise RuntimeError("未找到项目根（CLAUDE.md）")
        p = p.parent
    return p


REPO = _repo_root()
sys.path.insert(0, str(REPO / "generate_project/deep_learning/Fundus-Diffusion/ddpm"))
from prep_conditions import extract_vessel_mask  # noqa: E402

IMG_DIR = REPO / "fundus/a_domain_clean"
COND_DIR = REPO / "generate_project/deep_learning/Fundus-FlowMatching/CFM/data/conditions_a_domain_clean"
OUT_DIR = HERE / "a_domain_pair_check_20261111"
N_SAMPLE = 20
SEED = 20261111
TMP = OUT_DIR / "_tmp_rederive.png"


def find_img(stem):
    for ext in (".jpg", ".png", ".jpeg"):
        p = IMG_DIR / (stem + ext)
        if p.exists():
            return p
    raise FileNotFoundError(stem)


def shifts(a):
    """8 方向 ±3px 平移"""
    out = {}
    for dx in (-3, 0, 3):
        for dy in (-3, 0, 3):
            if dx == 0 and dy == 0:
                continue
            out[f"shift({dx},{dy})"] = np.roll(a, (dy, dx), axis=(0, 1))
    return out


def main():
    OUT_DIR.mkdir(exist_ok=True)
    stems = sorted(p.stem for p in COND_DIR.iterdir() if p.suffix == ".png")
    assert len(stems) == 258, f"cond count {len(stems)} != 258"
    rng = np.random.default_rng(SEED)
    sample = [stems[i] for i in rng.choice(len(stems), N_SAMPLE, replace=False)]
    print(f"[sample] seed={SEED} n={N_SAMPLE}")

    rederived = {}
    conds = {}
    for s in sample:
        extract_vessel_mask(str(find_img(s)), str(TMP), 128)
        rederived[s] = cv2.imread(str(TMP), 0)
        conds[s] = cv2.imread(str(COND_DIR / (s + ".png")), 0)
        assert rederived[s] is not None and conds[s] is not None, s
    TMP.unlink(missing_ok=True)

    results = []
    for k, s in enumerate(sample):
        c, m = conds[s], rederived[s]
        ag = lambda x: float((c == x).mean())
        alts = {"flipH": np.flip(m, 1), "flipV": np.flip(m, 0),
                "rot180": np.rot90(m, 2), "transpose": m.T}
        alts.update(shifts(m))
        alt_scores = {kk: ag(vv) for kk, vv in alts.items()}
        # 错配对照：用其他 19 张图的推导结果比对
        wrong = {o: float((c == rederived[o]).mean()) for o in sample if o != s}
        wrong_best = max(wrong, key=wrong.get)
        ident = ag(m)
        best_alt = max(alt_scores, key=alt_scores.get)
        r = {
            "stem": s,
            "agree_identity": round(ident, 4),
            "best_alternative": best_alt,
            "agree_best_alt": round(alt_scores[best_alt], 4),
            "agree_flipH": round(alt_scores["flipH"], 4),
            "agree_flipV": round(alt_scores["flipV"], 4),
            "agree_rot180": round(alt_scores["rot180"], 4),
            "agree_transpose": round(alt_scores["transpose"], 4),
            "agree_shift_best": round(max(v for kk, v in alt_scores.items() if kk.startswith("shift")), 4),
            "wrong_partner_best": wrong_best,
            "agree_wrong_partner_best": round(wrong[wrong_best], 4),
        }
        r["verdict"] = "PASS" if (ident >= 0.99 and ident - alt_scores[best_alt] >= 0.05
                                  and ident - wrong[wrong_best] >= 0.05) else "CHECK"
        results.append(r)

        # 叠加图：RGB(×4 放大) + 条件图暗类(=算法输出的血管结构类)红色高亮
        img = cv2.imread(str(find_img(s)))
        img = cv2.resize(img, (128, 128))
        img = cv2.resize(img, (512, 512), interpolation=cv2.INTER_NEAREST)
        c4 = cv2.resize(c, (512, 512), interpolation=cv2.INTER_NEAREST)
        sel = c4 == 0
        img[sel] = (0.55 * img[sel] + 0.45 * np.array([0, 0, 255])).astype(np.uint8)
        cv2.imwrite(str(OUT_DIR / f"overlay_{s}.png"), img)

    # 拼图 5×4
    S, CAP = 240, 34
    canvas = np.full((4 * (S + CAP) + 8, 5 * (S + 6) + 6, 3), 255, np.uint8)
    for i, r in enumerate(results):
        row, col = divmod(i, 5)
        y, x = 4 + row * (S + CAP), 4 + col * (S + 6)
        ov = cv2.imread(str(OUT_DIR / f"overlay_{r['stem']}.png"))
        canvas[y:y + S, x:x + S] = cv2.resize(ov, (S, S))
        cv2.putText(canvas, f"{r['stem'][:22]} id={r['agree_identity']:.3f}",
                    (x + 2, y + S + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.imwrite(str(OUT_DIR / "montage_20.png"), canvas)

    n_pass = sum(1 for r in results if r["verdict"] == "PASS")
    idents = [r["agree_identity"] for r in results]
    summary = {
        "date": "2026-11-11", "n": N_SAMPLE, "seed": SEED, "pool": "a_domain_clean(258)",
        "method": "prep_conditions.extract_vessel_mask 重推导 + 像素一致率对照（identity vs flip/shift/错配）",
        "identity_min": round(min(idents), 4), "identity_mean": round(float(np.mean(idents)), 4),
        "alt_max_overall": round(max(r["agree_best_alt"] for r in results), 4),
        "wrong_partner_max_overall": round(max(r["agree_wrong_partner_best"] for r in results), 4),
        "n_pass": n_pass,
        "verdict": "PASS" if n_pass == N_SAMPLE else "CHECK",
        "results": results,
    }
    (OUT_DIR / "pair_check_result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[identity] min={min(idents):.4f} mean={np.mean(idents):.4f}")
    print(f"[alt] best-alternative max={summary['alt_max_overall']}")
    print(f"[wrong] wrong-partner max={summary['wrong_partner_max_overall']}")
    print(f"[verdict] {n_pass}/{N_SAMPLE} PASS -> {summary['verdict']}")
    print(f"[out] {OUT_DIR}")


if __name__ == "__main__":
    main()
