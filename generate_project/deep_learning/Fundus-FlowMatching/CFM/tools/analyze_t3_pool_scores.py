# -*- coding: utf-8 -*-
"""统计 T3 合成池质量评分（32 行：4 生成 seed × 8 样本 × 128/256 两列）。

量表：视盘 0 不可见 / 1 部分 / 2 清晰；过生成 0 无 / 1 轻度 / 2 明显；
亮度 0 偏暗 / 1 适中 / 2 偏亮；留空 = 不确定。

用法（仓库根目录）：
    python -X utf8 generate_project/deep_learning/Fundus-FlowMatching/CFM/tools/analyze_t3_pool_scores.py
输出：同目录 judgment/t3_pool_audit_20261117/评分统计_20261125.{json,md}
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
AUD = HERE.parent / "judgment/t3_pool_audit_20261117"
XLSX = AUD / "评分表_T3合成池质量.xlsx"


def dist(vals: list) -> dict:
    c = Counter("blank" if v is None else str(v) for v in vals)
    return {k: c.get(k, 0) for k in ("0", "1", "2", "blank")}


def main() -> int:
    ws = load_workbook(XLSX, read_only=True, data_only=True)["评分"]
    rows = list(ws.iter_rows(values_only=True))
    hdr, data = rows[0], [dict(zip(rows[0], r)) for r in rows[1:] if r[0]]
    assert len(data) == 32, len(data)

    def col(name: str) -> list:
        return [r[name] for r in data]

    res = {
        "n_rows": len(data),
        "n_conditions": len({(r["生成seed"], r["样本序号"]) for r in data}),
        "dist": {
            "disc_128": dist(col("视盘_128")), "disc_256": dist(col("视盘_256")),
            "over_128": dist(col("过生成_128")), "over_256": dist(col("过生成_256")),
            "bright_128": dist(col("亮度_128")), "bright_256": dist(col("亮度_256")),
        },
    }

    # 配对比较（同一条件内 128 vs 256）
    def paired(a: str, b: str, better):
        c = Counter()
        for r in data:
            x, y = r[a], r[b]
            if x is None or y is None:
                c["blank"] += 1
            elif x == y:
                c["equal"] += 1
            elif better(x, y):
                c["win_256"] += 1
            else:
                c["win_128"] += 1
        return dict(c)

    res["paired"] = {
        "disc": paired("视盘_128", "视盘_256", lambda x, y: y > x),
        "over": paired("过生成_128", "过生成_256", lambda x, y: y < x),
        "bright": {
            "256_dimmer": sum(1 for r in data if r["亮度_256"] is not None
                              and r["亮度_128"] is not None and r["亮度_256"] < r["亮度_128"]),
            "equal": sum(1 for r in data if r["亮度_256"] == r["亮度_128"]),
            "256_brighter": sum(1 for r in data if r["亮度_256"] is not None
                                and r["亮度_128"] is not None and r["亮度_256"] > r["亮度_128"]),
        },
    }
    # 偏暗计数（亮度=0）
    res["dark"] = {
        "n_128": sum(1 for r in data if r["亮度_128"] == 0),
        "n_256": sum(1 for r in data if r["亮度_256"] == 0),
    }
    notes = [{"id": r["条件ID"], "note": r["备注"]} for r in data if r["备注"]]
    res["notes"] = notes
    res["note_mentions_brightness_lower"] = sum("低" in n["note"] for n in notes)

    (AUD / "评分统计_20261125.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# T3 合成池质量评分统计（2026-11-25）", "",
             f"共 {res['n_rows']} 行（{res['n_conditions']} 个条件 × 128/256）。"
             "量表：视盘 0/1/2；过生成 0/1/2；亮度 0 偏暗 / 1 适中 / 2 偏亮。", "",
             "## 分布", "",
             "| 项目 | 0 | 1 | 2 | 留空 |", "|:--|--:|--:|--:|--:|"]
    name = {"disc_128": "视盘 128", "disc_256": "视盘 256",
            "over_128": "过生成 128", "over_256": "过生成 256",
            "bright_128": "亮度 128", "bright_256": "亮度 256"}
    for k, label in name.items():
        d = res["dist"][k]
        lines.append(f"| {label} | {d['0']} | {d['1']} | {d['2']} | {d['blank']} |")
    lines += ["", "## 同条件配对（128 vs 256）", "",
              f"- 视盘：256 更好 {res['paired']['disc'].get('win_256',0)} 对，"
              f"128 更好 {res['paired']['disc'].get('win_128',0)} 对，"
              f"相同 {res['paired']['disc'].get('equal',0)} 对。",
              f"- 过生成（越少越好）：256 更少 {res['paired']['over'].get('win_256',0)} 对，"
              f"256 更多 {res['paired']['over'].get('win_128',0)} 对，"
              f"相同 {res['paired']['over'].get('equal',0)} 对。",
              f"- 亮度：256 更暗 {res['paired']['bright']['256_dimmer']} 对，相同 "
              f"{res['paired']['bright']['equal']} 对，更亮 {res['paired']['bright']['256_brighter']} 对；"
              f"偏暗（=0）计数 128 {res['dark']['n_128']} / 256 {res['dark']['n_256']}。",
              "", f"## 备注（{len(notes)} 条）", ""]
    for n in notes:
        lines.append(f"- {n['id']}：{n['note']}")
    lines.append("")
    (AUD / "评分统计_20261125.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(res["dist"], ensure_ascii=False))
    print("paired:", json.dumps(res["paired"], ensure_ascii=False))
    print("dark:", res["dark"], "notes:", len(notes))
    print(f"已写 {AUD / '评分统计_20261125.json'} / .md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
