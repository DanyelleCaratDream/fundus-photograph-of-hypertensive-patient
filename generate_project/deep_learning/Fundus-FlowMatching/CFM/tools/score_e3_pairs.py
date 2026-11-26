# -*- coding: utf-8 -*-
"""E3 逐对盲评汇总：读评分表 xlsx + 左右 key，揭盲后统计三问的胜负与逐 seed 分布。

用法：
  python tools/score_e3_pairs.py \
      --scores judgment/e3_display_scale/author_32对/评分表_E3_32对.xlsx \
      --key    judgment/e3_display_scale/author_32对/key_作者_勿删.json \
      --out    judgment/e3_display_scale/author_32对/score_summary_作者.json

约定：单元格填 左 / 右 / 平（伪影列可填 左/右/平/无，不计入主判定）。
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import load_workbook

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QUESTIONS = {
    "血管细节（左/右/平）": "vessel",
    "轮廓质量（左/右/平）": "contour",
    "整体视觉观感（左/右/平）": "overall",
}
ARTIFACT = "伪影（附加：左/右/平/无）"
NORM = {"左": "left", "右": "right", "平": "tie", "平手": "tie", "": None, None: None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    key = json.loads(Path(a.key).read_text(encoding="utf-8"))
    wb = load_workbook(a.scores)
    ws = wb.worksheets[0]
    head = [c.value for c in ws[1]]
    idx = {h: i for i, h in enumerate(head) if h}
    missing_cols = [q for q in list(QUESTIONS) + [ARTIFACT] if q not in idx]
    if "编号" not in idx or missing_cols:
        raise SystemExit(f"[FAIL] 表头不匹配，缺：{missing_cols or ['编号']}")

    records, missing, mismatch = [], [], []
    for row in ws.iter_rows(min_row=2, values_only=True):
        pid = row[idx["编号"]]
        if not pid:
            continue
        if pid not in key["items"]:
            mismatch.append(pid)
            continue
        item = key["items"][pid]
        rec = {"id": pid, "seed": item["seed"], "cond_index": item["cond_index"],
               "left": item["left"], "right": item["right"]}

        def decode(cell):
            v = NORM.get(str(cell).strip() if cell is not None else "")
            if v is None:
                return None
            if v == "tie":
                return "tie"
            return item[v]          # left/right → 128/256

        for q, name in QUESTIONS.items():
            rec[name] = decode(row[idx[q]])
        rec["artifact"] = decode(row[idx[ARTIFACT]]) if ARTIFACT in idx else None
        rec["note"] = row[idx["备注"]] if "备注" in idx else None
        if all(rec[n] is None for n in QUESTIONS.values()):
            missing.append(pid)
        records.append(rec)

    def agg(rs, name):
        c = Counter(r[name] for r in rs if r[name])
        n = sum(c.values())
        return {"n": n, "win_128": c.get("128", 0), "win_256": c.get("256", 0),
                "tie": c.get("tie", 0),
                "diff": c.get("256", 0) - c.get("128", 0)}

    summary = {"n_rows": len(records), "missing_rows": missing, "unknown_ids": mismatch,
               "per_question": {}, "per_seed": {}}
    for name in QUESTIONS.values():
        summary["per_question"][name] = agg(records, name)
    by_seed = defaultdict(list)
    for r in records:
        by_seed[r["seed"]].append(r)
    for s, rs in sorted(by_seed.items()):
        summary["per_seed"][str(s)] = {name: agg(rs, name) for name in QUESTIONS.values()}

    # ---- 预注册判定规则（导师 2026-11-16 定稿，见 EXPERIMENTS DL-EX-031）----
    def seed_support(q, arm):
        """支持某一边（胜场多于另一边）的 seed 数。"""
        return sum(1 for sd in summary["per_seed"].values() if sd[q][f"win_{arm}"] > sd[q][f"win_{'128' if arm == '256' else '256'}"])

    rules = {}
    if summary["n_rows"] == 32:
        v, c, o = summary["per_question"]["vessel"], summary["per_question"]["contour"], summary["per_question"]["overall"]
        sup256_v, sup128_c, sup128_o = seed_support("vessel", "256"), seed_support("contour", "128"), seed_support("overall", "128")
        rules = {
            "A_256_vessel": {"win_256": v["win_256"], "need_ge": 20,
                             "seeds_supporting_256": sup256_v, "need_seeds_ge": 3,
                             "met": v["win_256"] >= 20 and sup256_v >= 3},
            "B_128_contour": {"win_128": c["win_128"], "need_ge": 20,
                              "seeds_supporting_128": sup128_c, "need_seeds_ge": 3,
                              "met": c["win_128"] >= 20 and sup128_c >= 3},
            "C_256_overall_no_disadvantage": {
                "win_128": o["win_128"], "need_le": 16,
                "net_win_128_minus_256": o["win_128"] - o["win_256"], "need_net_le": 4,
                "seeds_supporting_128": sup128_o, "need_seeds_le": 2,
                "met": o["win_128"] <= 16 and (o["win_128"] - o["win_256"]) <= 4 and sup128_o <= 2},
        }
        summary["rules"] = rules

    Path(a.out).write_text(json.dumps({"summary": summary, "records": records},
                                      ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"行数 {len(records)}｜未填 {len(missing)}｜未知编号 {len(mismatch)}")
    for name, s in summary["per_question"].items():
        print(f"  {name:12s} n={s['n']:2d}  128胜 {s['win_128']:2d}  256胜 {s['win_256']:2d}  平 {s['tie']:2d}")
    if rules:
        print("\n预注册判定（仅对 32 对主评分适用）:")
        a_ = rules["A_256_vessel"]
        print(f"  A 256血管优势   {a_['win_256']}/32≥20 且 支持seed {a_['seeds_supporting_256']}/4≥3 → {'达成' if a_['met'] else '未达成'}")
        b_ = rules["B_128_contour"]
        print(f"  B 128轮廓优势   {b_['win_128']}/32≥20 且 支持seed {b_['seeds_supporting_128']}/4≥3 → {'达成' if b_['met'] else '未达成'}")
        c_ = rules["C_256_overall_no_disadvantage"]
        print(f"  C 256整体无劣势 128胜 {c_['win_128']}/32≤16、净胜 {c_['net_win_128_minus_256']}≤4、支持seed {c_['seeds_supporting_128']}/4≤2 → {'达成' if c_['met'] else '未达成'}")
        print("  ⚠️ 未达阈值 ≠ 证明不存在差异；这些是决策阈值，不是显著性界限。")
    elif records:
        print("\n[提示] 本表不是 32 对主评分（第二评分者 8 对仅作交叉核对），不套用 A/B/C 阈值。")
    print(f"→ {a.out}")


if __name__ == "__main__":
    main()
