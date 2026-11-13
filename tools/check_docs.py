#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文档健康检查：相对链接、入口预算、过期路径。

用法（任意目录）：
    python tools/check_docs.py

检查结果分三节；有任何问题 exit 1。
只用标准库，任何 Python 3 解释器都能跑。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# 入口文件行数上限（见 docs/10-management/18-Knowledge-Maintenance.md）
BUDGETS = {
    "PROJECT_STATE.md": 120,
    "PROJECT_MAP.md": 80,
    "CLAUDE.md": 60,
    "docs/00-Doc-Index.md": 100,
    "generate_project/deep_learning/Fundus-FlowMatching/CFM/results/README.md": 100,
}

# 已废弃路径 / 旧写法（出现即视为过期）
FORBIDDEN = [
    ("research-report/evaluation_report.md", "已归档到 _archive/reports/"),
    ("advisor_review_2026", "已合并到 research-report/audit/"),
    ("a_domain_clean_frozen_CANDIDATE", "已改名 a_domain_clean_frozen.json"),
    ("REPORT_DL_text §", "旧写法，应写 REPORT_DL_text.txt §"),
]

EXCLUDE_DIRS = {".git", "_archive", "node_modules", "__pycache__", "upstream", "torchcfm"}
# 历史/工具文件里允许出现旧路径（用于说明迁移来源）
SKIP_FORBIDDEN = {"tools", "research-report/audit"}
SCAN_SUFFIXES = {".md", ".py", ".txt"}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while not (p / "CLAUDE.md").exists():
        if p.parent == p:
            raise RuntimeError("未找到项目根（CLAUDE.md）")
        p = p.parent
    return p


def walk(root: Path):
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        yield p


def check_links(root: Path) -> list[tuple[str, str]]:
    broken = []
    for p in walk(root):
        if p.suffix.lower() != ".md":
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in LINK_RE.finditer(text):
            target = m.group(1).split("#")[0].strip()
            if not target or target.startswith(("http", "mailto:", "#")):
                continue
            if re.match(r"^[A-Za-z]:[\\/]", target):  # Windows 绝对路径
                continue
            if not (p.parent / target).resolve().exists():
                broken.append((str(p.relative_to(root)), m.group(1)))
    return broken


def check_budgets(root: Path) -> list[tuple[str, int, int]]:
    over = []
    for rel, limit in BUDGETS.items():
        p = root / rel
        if not p.exists():
            continue
        lines = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
        if lines > limit:
            over.append((rel, lines, limit))
    return over


def check_forbidden(root: Path) -> list[tuple[str, int, str, str]]:
    hits = []
    for p in walk(root):
        rel = p.relative_to(root).as_posix()
        if any(rel.startswith(d + "/") or rel == d for d in SKIP_FORBIDDEN):
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            for pattern, why in FORBIDDEN:
                if pattern in line:
                    hits.append((str(p.relative_to(root)), i, pattern, why))
    return hits


def main() -> int:
    root = repo_root()
    broken = check_links(root)
    over = check_budgets(root)
    stale = check_forbidden(root)

    print("== 1. Markdown 相对链接 ==")
    if broken:
        print(f"  {len(broken)} 处断链：")
        for f, t in broken:
            print(f"  - {f} -> {t}")
    else:
        print("  OK（0 broken）")

    print("\n== 2. 入口文件预算 ==")
    if over:
        for f, n, limit in over:
            print(f"  - {f}: {n} 行 > {limit}（需下沉/精简）")
    else:
        print("  OK（全部在预算内）")

    print("\n== 3. 过期路径 / 旧写法 ==")
    if stale:
        for f, i, pat, why in stale:
            print(f"  - {f}:{i} 含 `{pat}`（{why}）")
    else:
        print("  OK（无禁用路径）")

    problems = len(broken) + len(over) + len(stale)
    print(f"\n合计问题：{problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
