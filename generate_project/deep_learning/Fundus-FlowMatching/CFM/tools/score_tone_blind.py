#!/usr/bin/env python
"""揭盲并汇总「色调校正 vs 原始 T1-256」小盲评（DL-EX-030 后续）

输入
  judgment/t1_256/tone_blind_score_template.csv
  judgment/t1_256/tone_blind_key.json

输出
  judgment/t1_256/tone_blind_summary.json
  控制台摘要

口径
  * 自动识别刻度：最高分 ≤ 5 → 1–5；否则按 0–100。
  * Δ = 校正 − 原始；胜率只统计有差异的对。
  * 偏好列与分数不一致时单独列出（不静默改分）。

用法
  python tools/score_tone_blind.py
  python tools/score_tone_blind.py --scores <另一份.csv> --label 老师
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
JUDGE = CFM / "judgment" / "t1_256"
DIMS = ("整体外观", "边界形状")


def load_rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_num(x: str):
    x = (x or "").strip()
    if not x:
        return None
    try:
        return float(x)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default=str(JUDGE / "tone_blind_score_template.csv"))
    ap.add_argument("--key", default=str(JUDGE / "tone_blind_key.json"))
    ap.add_argument("--label", default="作者")
    ap.add_argument("--out", default=str(JUDGE / "tone_blind_summary.json"))
    args = ap.parse_args()

    rows = load_rows(Path(args.scores))
    key = json.loads(Path(args.key).read_text(encoding="utf-8"))

    scores = []
    for r in rows:
        for dim in DIMS:
            for tag in ("A", "B"):
                v = parse_num(r.get(f"{tag}_{dim}", ""))
                if v is not None:
                    scores.append(v)
    scale = "1-5" if (scores and max(scores) <= 5) else "0-100"

    records, mismatches = [], []
    for r in rows:
        seed, col = str(int(r["seed"])), str(int(r["column"]) - 1)
        mapping = key[seed][col]
        rec = {"seed": int(seed), "column": int(col) + 1,
               "preference": (r.get("偏好(A/B/平)") or "").strip(),
               "note": (r.get("备注") or "").strip()}
        for dim in DIMS:
            va = parse_num(r.get(f"A_{dim}", ""))
            vb = parse_num(r.get(f"B_{dim}", ""))
            if va is None or vb is None:
                rec[dim] = None
                continue
            rec[dim] = {
                "orig": va if mapping["A"] == "orig" else vb,
                "tone": vb if mapping["A"] == "orig" else va,
                "delta": (vb - va) if mapping["A"] == "orig" else (va - vb),
            }
        # 偏好与分数一致性
        pref = rec["preference"]
        if pref in ("A", "B") and all(rec[d] for d in DIMS):
            dsum = sum(rec[d]["delta"] for d in DIMS)
            if (pref == "A" and dsum > 0) or (pref == "B" and dsum < 0):
                mismatches.append(rec)
        records.append(rec)

    summary = {"label": args.label, "scale": scale, "n_pairs": len(records),
               "dims": {}, "preference": {}, "mismatches": mismatches,
               "records": records}
    for dim in DIMS:
        ds = [r[dim]["delta"] for r in records if r[dim]]
        ds = np.array(ds, dtype=float)
        nz = ds[ds != 0]
        summary["dims"][dim] = {
            "n": int(ds.size),
            "mean_delta": float(ds.mean()) if ds.size else None,
            "tone_win": int((nz > 0).sum()),
            "orig_win": int((nz < 0).sum()),
            "tie": int((ds == 0).sum()),
        }

    tally = {}
    for r in records:
        p = r["preference"] or "未填"
        # 把偏好映射到 orig/tone
        seed, col = str(r["seed"]), str(r["column"] - 1)
        m = key[seed][col]
        if p == "平手":
            p = "平手"
        elif p in ("A", "B"):
            p = m[p]
        tally[p] = tally.get(p, 0) + 1
    summary["preference"] = tally

    print(f"[{args.label}] n={len(records)}  刻度={scale}")
    for dim in DIMS:
        s = summary["dims"][dim]
        print(f"  {dim}: Δ均值 {s['mean_delta']:+.3f}  "
              f"校正胜 {s['tone_win']} / 原始胜 {s['orig_win']} / 平 {s['tie']}")
    print(f"  偏好: {tally}")
    if mismatches:
        print(f"  [WARN] 偏好与分数方向不一致 {len(mismatches)} 对:")
        for m in mismatches:
            print(f"    seed{m['seed']} #{m['column']} 偏好={m['preference']}")
    print("\n备注（按 unblind 标注）:")
    for r in records:
        if r["note"]:
            m = key[str(r["seed"])][str(r["column"] - 1)]
            print(f"  seed{r['seed']} #{r['column']} [A={m['A']}, B={m['B']}] {r['note']}")

    Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print(f"\n写入: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
