#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A_clean 冻结收尾（2026-11-11，导师批准后的阶段1动作）

1. 文件哈希入档：258 张 RGB + 258 张骨架的 md5 → fundus/a_domain_clean_frozen_hashes.json
   （主名单 JSON 增加 hash_file 引用字段）
2. 全量 258 对确定性重建复核（导师建议，成本低的完整性检查）：
   用 prep_conditions.extract_vessel_mask 从每张 RGB 重新推导，与存档骨架逐像素比对，
   对照组 = flipH/flipV/rot180/transpose + 环移错配（cond_i vs rederive_{i+1}）。

输出：research-report/audit/a_domain_20261111/a_pair_check_full_20261111.json + 控制台摘要
"""
import hashlib
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
FROZEN = REPO / "fundus/a_domain_clean_frozen.json"
HASH_OUT = REPO / "fundus/a_domain_clean_frozen_hashes.json"
RESULT_OUT = HERE / "a_pair_check_full_20261111.json"
TMP = HERE / "_tmp_rederive.png"


def find_img(stem):
    for ext in (".jpg", ".png", ".jpeg"):
        p = IMG_DIR / (stem + ext)
        if p.exists():
            return p
    raise FileNotFoundError(stem)


def md5f(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def main():
    d = json.loads(FROZEN.read_text(encoding="utf-8"))
    stems = d["files"]
    assert len(stems) == 258 and d["count"] == 258

    # ---- 1) 哈希入档 ----
    hashes = {"frozen_at": "2026-11-11", "n": 258,
              "images_md5": {}, "conditions_md5": {}}
    for s in stems:
        hashes["images_md5"][s] = md5f(find_img(s))
        hashes["conditions_md5"][s] = md5f(COND_DIR / (s + ".png"))
    HASH_OUT.write_text(json.dumps(hashes, ensure_ascii=False, indent=1), encoding="utf-8")
    if "hash_file" not in d:
        d["hash_file"] = "fundus/a_domain_clean_frozen_hashes.json"
        FROZEN.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    n_img_uniq = len(set(hashes["images_md5"].values()))
    n_cond_uniq = len(set(hashes["conditions_md5"].values()))
    print(f"[hash] images 258 -> {n_img_uniq} unique md5; conds 258 -> {n_cond_uniq} unique md5")
    print(f"[hash] {HASH_OUT}")

    # ---- 2) 全量重推导比对 ----
    rederived, conds = {}, {}
    for i, s in enumerate(stems):
        extract_vessel_mask(str(find_img(s)), str(TMP), 128)
        rederived[s] = cv2.imread(str(TMP), 0)
        conds[s] = cv2.imread(str(COND_DIR / (s + ".png")), 0)
        if rederived[s] is None or conds[s] is None:
            raise RuntimeError(f"read fail: {s}")
        if i % 50 == 0:
            print(f"  rederive {i}/258", flush=True)
    TMP.unlink(missing_ok=True)

    rows = []
    for i, s in enumerate(stems):
        c, m = conds[s], rederived[s]
        ag = lambda x: float((c == x).mean())
        nxt = stems[(i + 1) % len(stems)]                # 环移错配对照
        rows.append({
            "stem": s,
            "identity": round(ag(m), 4),
            "flipH": round(ag(np.flip(m, 1)), 4),
            "flipV": round(ag(np.flip(m, 0)), 4),
            "rot180": round(ag(np.rot90(m, 2)), 4),
            "transpose": round(ag(m.T), 4),
            "wrong_partner": round(ag(rederived[nxt]), 4),
        })
    idents = [r["identity"] for r in rows]
    alt_max = max(max(r["flipH"], r["flipV"], r["rot180"], r["transpose"]) for r in rows)
    wrong_max = max(r["wrong_partner"] for r in rows)
    n_exact = sum(1 for x in idents if x == 1.0)
    summary = {
        "date": "2026-11-11", "n": 258, "method": "full deterministic re-derivation (same as 20-pair check)",
        "identity_min": round(min(idents), 4), "identity_mean": round(float(np.mean(idents)), 4),
        "identity_exact_1.0": n_exact,
        "transform_alt_max": round(alt_max, 4),
        "wrong_partner_max(cyclic)": round(wrong_max, 4),
        "fail_list": [r["stem"] for r in rows if r["identity"] < 0.99],
        "verdict": "PASS" if min(idents) >= 0.99 else "CHECK",
        "results": rows,
    }
    RESULT_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[full-check] identity: min={min(idents):.4f} mean={np.mean(idents):.4f} exact={n_exact}/258")
    print(f"[full-check] transform-alt max={alt_max:.4f}  wrong-partner max={wrong_max:.4f}")
    print(f"[full-check] fail_list={summary['fail_list']}")
    print(f"[full-check] verdict={summary['verdict']} -> {RESULT_OUT}")


if __name__ == "__main__":
    main()
