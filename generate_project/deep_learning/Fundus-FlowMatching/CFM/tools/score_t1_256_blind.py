#!/usr/bin/env python
"""T1-256 盲评揭盲与汇总（2026-11-14）

读 `make_t1_256_blind_sheet.py` 产出的 blind_key.json + 人工填好的评分 CSV，
按 key 把 A/B 还原成 t1_128 / t1_256，输出：

  * 逐维对比（均分 ± 标准差、Δ = T1-256 − T1@128、逐 seed 胜率）
  * 逐 seed 偏好与逐维 Δ（含**最差 seed**，协议要求不许只报均值）
  * 一致性检查：缺分/非法值/偏好缺填直接报错，不静默跳过

表结构（行级随机）：每个 seed 一行，A/B 各是一整行同一实验 → 可整体评。
支持 CSV（blind_score_template.csv）或 Excel（评分表_T1_256盲评.xlsx）。

评分表填法（CSV）
  prefer 列填 A / B / 平手（大小写不限）
  五维分 1–5 整数：A_vessel, A_disc, A_artifact, A_diversity, A_overall（B_ 同）

用法
  python tools/score_t1_256_blind.py --scores judgment/t1_256/评分表_T1_256盲评.xlsx
  python tools/score_t1_256_blind.py --scores 老师_1-2seed.csv --label 老师 --allow-missing-seeds
"""
import argparse
import csv
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
DIMS = ("vessel", "disc", "artifact", "diversity", "overall")
DIM_ZH = {"vessel": "血管细节", "disc": "视盘结构", "artifact": "伪影",
          "diversity": "多样性", "overall": "整体外观"}
ARMS = ("t1_128", "t1_256")
ARM_ZH = {"t1_128": "T1@128（放大）", "t1_256": "T1-256（原生）"}


def load_key(path: Path) -> dict:
    """行级随机 key：items = {"seed42": {"A": "t1_128", "B": "t1_256"}, ...}"""
    key = json.loads(path.read_text(encoding="utf-8"))
    flat = {}
    for seed_tag, ab in key["items"].items():
        if not (isinstance(ab, dict) and "A" in ab and "B" in ab):
            raise SystemExit("[FAIL] blind_key.json 不是行级随机格式（疑似旧的逐列版本），"
                             "请用 make_t1_256_blind_sheet.py 重出")
        flat[int(seed_tag.replace("seed", ""))] = ab
    return key, flat


# Excel 中文表头 → 内部字段名（make_score_xlsx.py 生成的表）
CH_HEADERS = {
    "seed": "seed",
    "对照图": "_fig",
    "偏好（A/B/平手）": "prefer",
    "备注": "_note",
}
for _side in ("A", "B"):
    for _d, _zh in (("overall", "整体外观"), ("vessel", "血管细节"), ("disc", "视盘结构"),
                    ("artifact", "伪影"), ("diversity", "多样性")):
        CH_HEADERS[f"{_side}·{_zh}"] = f"{_side}_{_d}"


def read_rows(path: Path):
    """读 CSV（blind_score_template.csv）或 Excel（评分表_*.xlsx），统一成 dict 列表。"""
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook

        wb = load_workbook(path, data_only=True)
        ws = wb[wb.sheetnames[0]]
        hdr = [None if c.value is None else str(c.value).strip() for c in ws[1]]
        out = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] is None:
                continue
            d = {}
            for h, v in zip(hdr, row):
                if h is None:
                    continue
                key = CH_HEADERS.get(h, h)
                if isinstance(v, float) and v.is_integer():
                    v = int(v)
                d[key] = "" if v is None else str(v).strip()
            out.append(d)
        return out
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_scores(path: Path, max_score: float = 5.0):
    rows = {}
    problems = []
    for r in read_rows(path):
        if r.get("seed") in ("", None):
            continue
        s = int(float(r["seed"]))
        pref = (r.get("prefer") or "").strip().upper()
        if pref in ("平手", "TIE", "T"):
            pref_arm = "tie"
        elif pref in ("A", "B"):
            pref_arm = pref
        elif pref == "":
            pref_arm = None
        else:
            problems.append(f"seed{s} prefer 非法: {pref!r}")
            pref_arm = None
        scores = {}
        for side in ("A", "B"):
            for d in DIMS:
                v = (r.get(f"{side}_{d}") or "").strip()
                if v == "":
                    problems.append(f"seed{s} {side}_{d} 缺分")
                    continue
                try:
                    fv = float(v)
                except ValueError:
                    problems.append(f"seed{s} {side}_{d} 非法: {v!r}")
                    continue
                if not (1 <= fv <= max_score):
                    problems.append(f"seed{s} {side}_{d} 越界(1–{max_score:g}): {fv}")
                scores[(side, d)] = fv
        rows[s] = {"prefer_raw": pref_arm, "scores": scores}
    return rows, problems


def mean_std(xs):
    n = len(xs)
    if n == 0:
        return float("nan"), float("nan")
    m = sum(xs) / n
    if n < 2:
        return m, 0.0
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m, var ** 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=str(CFM / "judgment/t1_256/blind_key.json"))
    ap.add_argument("--scores", default=str(CFM / "judgment/t1_256/blind_score_template.csv"))
    ap.add_argument("--label", default="作者", help="评分者标签")
    ap.add_argument("--allow-missing-seeds", action="store_true",
                    help="允许只评部分 seed（第二评分者情形）")
    ap.add_argument("--out", default=None, help="汇总 JSON 输出路径")
    ap.add_argument("--max-score", type=float, default=5.0,
                    help="分值上限（协议 1–5；作者若用百分制填 100，汇总按原始分值报告）")
    a = ap.parse_args()

    key, flat = load_key(Path(a.key))
    rows, problems = load_scores(Path(a.scores), a.max_score)

    if problems:
        print(f"[FAIL] 评分表有 {len(problems)} 处问题，未汇总：")
        for p in problems[:15]:
            print("   ", p)
        return 1

    seeds_scored = sorted(rows)
    seeds_all = sorted(flat)
    missing_seeds = [s for s in seeds_all if s not in seeds_scored]
    if missing_seeds and not a.allow_missing_seeds:
        print(f"[FAIL] 缺 seed: {missing_seeds}（协议要求 4 seed 全展示；"
              f"若为第二评分者请加 --allow-missing-seeds）")
        return 1

    # ---------- 还原臂（行级：每 seed 一行，A/B 各是一个实验）----------
    per_arm = {arm: {d: [] for d in DIMS} for arm in ARMS}
    per_seed = {}
    pref_tally_all = {"t1_128": 0, "t1_256": 0, "tie": 0}
    for s, sc in sorted(rows.items()):
        ab = flat.get(s)
        if ab is None:
            print(f"[FAIL] key 里找不到 seed{s}")
            return 1
        arm_of = {"A": ab["A"], "B": ab["B"]}
        ps = {"pref": {"t1_128": 0, "t1_256": 0, "tie": 0},
              "dims": {d: {"t1_128": [], "t1_256": []} for d in DIMS}}
        for side in ("A", "B"):
            arm = arm_of[side]
            for d in DIMS:
                v = sc["scores"][(side, d)]
                per_arm[arm][d].append(v)
                ps["dims"][d][arm].append(v)
        if sc["prefer_raw"] == "tie":
            ps["pref"]["tie"] += 1
            pref_tally_all["tie"] += 1
        else:
            arm = arm_of[sc["prefer_raw"]]
            ps["pref"][arm] += 1
            pref_tally_all[arm] += 1
        per_seed[s] = ps

    # ---------- 逐维对比 ----------
    print(f"\n## 盲评汇总（评分者：{a.label}；{len(rows)} seed，每 seed 一次整体判断）\n")
    print("| 维度 | T1@128（放大） | T1-256（原生） | Δ | T1-256 逐 seed 占优 |")
    print("|---|---:|---:|---:|---:|")
    dim_summary = {}
    for d in DIMS:
        m1, s1 = mean_std(per_arm["t1_128"][d])
        m2, s2 = mean_std(per_arm["t1_256"][d])
        n = min(len(per_arm["t1_128"][d]), len(per_arm["t1_256"][d]))
        wins = sum(1 for k in range(n) if per_arm["t1_256"][d][k] > per_arm["t1_128"][d][k])
        ties = sum(1 for k in range(n) if per_arm["t1_256"][d][k] == per_arm["t1_128"][d][k])
        print(f"| {DIM_ZH[d]} | {m1:.2f} ± {s1:.2f} | {m2:.2f} ± {s2:.2f} "
              f"| {m2 - m1:+.2f} | {wins}/{n}（平 {ties}） |")
        dim_summary[d] = {"t1_128": {"mean": m1, "std": s1}, "t1_256": {"mean": m2, "std": s2},
                          "delta": m2 - m1, "win": wins, "tie": ties, "n": n}

    total = sum(pref_tally_all.values())
    print(f"\n**偏好总票**：T1-256 {pref_tally_all['t1_256']}/{total}，"
          f"T1@128 {pref_tally_all['t1_128']}/{total}，平手 {pref_tally_all['tie']}/{total}")

    # ---------- 逐 seed（含最差 seed）----------
    print("\n| seed | 整体偏好 | Δ血管 | Δ视盘 | Δ伪影 | Δ多样性 | Δ整体 | 五维Δ均值 |")
    print("|---|---|---:|---:|---:|---:|---:|---:|")
    seed_summary, worst, worst_val = {}, None, None
    for s in seeds_scored:
        ps = per_seed[s]
        deltas = {}
        for d in DIMS:
            m1, _ = mean_std(ps["dims"][d]["t1_128"])
            m2, _ = mean_std(ps["dims"][d]["t1_256"])
            deltas[d] = m2 - m1
        avg = sum(deltas.values()) / len(DIMS)
        if worst_val is None or avg < worst_val:
            worst, worst_val = s, avg
        pref_txt = ("T1-256" if ps["pref"]["t1_256"] else
                    "T1@128" if ps["pref"]["t1_128"] else "平手")
        print(f"| {s} | {pref_txt} "
              f"| {deltas['vessel']:+.2f} | {deltas['disc']:+.2f} | {deltas['artifact']:+.2f} "
              f"| {deltas['diversity']:+.2f} | {deltas['overall']:+.2f} | {avg:+.2f} |")
        seed_summary[str(s)] = {"pref": ps["pref"], "delta": deltas, "delta_mean": avg}
    print(f"\n**最差 seed**：{worst}（五维 Δ 均值 {worst_val:+.2f}）")

    out = Path(a.out) if a.out else Path(a.scores).with_name(f"blind_summary_{a.label}.json")
    payload = {
        "label": a.label,
        "rows": len(rows),
        "key_rng_seed": key.get("rng_seed"),
        "dims": dim_summary,
        "pref_tally": pref_tally_all,
        "per_seed": seed_summary,
        "worst_seed": worst,
        "worst_seed_delta_mean": worst_val,
        "seeds_missing": missing_seeds,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
