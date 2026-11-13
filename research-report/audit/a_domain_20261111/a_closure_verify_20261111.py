#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A 域审计数字闭合复算（2026-11-11，回应导师复核问题）

问题：换壳副本 31 组（跨池 29 + 池内 2），为何 A_clean 只排除 19 张跨池副本？
本脚本从原始文件**全量重算**（不信任既有 dupmap），验证：
  1) md5 字节级簇 → 排除字典序靠后者（20 张）
  2) A(299)×61(目标域) 128RGB mse<20 → 跨池同图对（应为 29 对）
  3) A 池内 mse<20 非 md5 对 → 池内换壳（应为 2 对）
  4) 三规则并集 = 41，299-41=258，与冻结名单 JSON 一致
  5) 保留 258 × 61 全量 mse 最小值 ≥ 20（无漏排的目标域同图副本）
输出：a_closure_table_20261111.md（对应表）+ 控制台摘要
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

def _repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while not (p / "CLAUDE.md").exists():
        if p.parent == p:
            raise RuntimeError("未找到项目根（CLAUDE.md）")
        p = p.parent
    return p


REPO = _repo_root()
A_DIR = REPO / "fundus/_all_images_ORIGINAL"          # 299
T_DIR = REPO / "fundus/hrsevere_61_sq128"             # 61 目标域
COND_DIR = REPO / "generate_project/deep_learning/Fundus-FlowMatching/CFM/data/conditions_a_domain_clean"
CLEAN_DIR = REPO / "fundus/a_domain_clean"
JSON_PATH = REPO / "fundus/a_domain_clean_frozen.json"
OUT_MD = Path(__file__).resolve().parent / "a_closure_table_20261111.md"

MSE_TH_SAMEPHOTO = 20.0   # 同图判定阈值（dupmap：同图 2-11，同眼异帧 56-630）
SIZE = 128
stem = lambda f: f.rsplit(".", 1)[0]


def load128(p):
    im = Image.open(p).convert("RGB").resize((SIZE, SIZE), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32)            # 0-255 尺度


def main():
    a_files = sorted([p.name for p in A_DIR.iterdir()])
    t_files = sorted([p.name for p in T_DIR.iterdir()])
    print(f"[data] A={len(a_files)} target={len(t_files)}")

    # ---------- 1) md5 字节级簇 ----------
    by_md5 = {}
    for f in a_files:
        by_md5.setdefault(hashlib.md5((A_DIR / f).read_bytes()).hexdigest(), []).append(f)
    md5_clusters = sorted([sorted(v) for v in by_md5.values() if len(v) > 1])
    md5_excl = set()                                   # 全名
    for cl in md5_clusters:
        md5_excl.update(cl[1:])                        # 排除字典序靠后
    print(f"[md5] clusters={len(md5_clusters)} sizes={sorted(set(len(c) for c in md5_clusters))} excluded={len(md5_excl)}")

    # ---------- 2) 128RGB mse 全量矩阵 ----------
    A = np.stack([load128(A_DIR / f) for f in a_files])            # [nA,128,128,3]
    T = np.stack([load128(T_DIR / f) for f in t_files])            # [nT,128,128,3]
    Af = A.reshape(len(A), -1); Tf = T.reshape(len(T), -1)
    aa = (Af * Af).sum(1); tt = (Tf * Tf).sum(1)
    cross = (aa[:, None] + tt[None, :] - 2 * Af @ Tf.T) / Af.shape[1]   # [nA,nT]
    sameA = (aa[:, None] + aa[None, :] - 2 * Af @ Af.T) / Af.shape[1]   # [nA,nA]

    # 跨池同图对
    crosspool = []                                     # (target, afile, mse)
    for i, tf in enumerate(t_files):
        for j, af in enumerate(a_files):
            m = float(cross[j, i])
            if m < MSE_TH_SAMEPHOTO:
                crosspool.append((tf, af, m))
    cp_a_files = sorted(set(x[1] for x in crosspool))
    cp_targets = sorted(set(x[0] for x in crosspool))
    print(f"[cross] pairs={len(crosspool)} unique_A_files={len(cp_a_files)} unique_targets={len(cp_targets)}")
    print(f"[cross] mse range: {min(x[2] for x in crosspool):.1f}-{max(x[2] for x in crosspool):.1f}")

    # 池内换壳（非 md5 同簇）
    md5_pair = set()
    for cl in md5_clusters:
        for x in cl:
            for y in cl:
                md5_pair.add((x, y))
    within = []
    for j in range(len(a_files)):
        for k in range(j + 1, len(a_files)):
            x, y = a_files[j], a_files[k]
            if (x, y) in md5_pair:
                continue
            m = float(sameA[j, k])
            if m < MSE_TH_SAMEPHOTO:
                within.append((x, y, m))
    within_excl = set()
    for x, y, m in within:
        within_excl.add(y)                             # 排除字典序靠后
    print(f"[within] shell pairs={len(within)} excluded={len(within_excl)}")

    # ---------- 3) 三规则并集闭合 ----------
    cp_new = [f for f in cp_a_files if f not in md5_excl]     # 跨池规则新增排除
    cp_overlap = [f for f in cp_a_files if f in md5_excl]     # 已被 md5 规则覆盖
    union = md5_excl | set(cp_a_files) | within_excl
    print(f"[decomp] md5={len(md5_excl)} + cross_new={len(cp_new)} + within={len(within_excl)} "
          f"=> union={len(union)} (overlap cross∩md5={len(cp_overlap)})")

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    js_excl, js_files = set(data["excluded"]), set(data["files"])
    kept_stems = {stem(f) for f in a_files} - {stem(f) for f in union}
    checks = {
        "union==41": len(union) == 41,
        "union==JSON_excluded": {stem(f) for f in union} == js_excl,
        "kept==258": len(kept_stems) == 258,
        "kept==JSON_files": kept_stems == js_files,
        "crosspool_pairs==29": len(crosspool) == 29,
        "crosspool_unique_targets==19": len(cp_targets) == 19,
        "within_pairs==2": len(within) == 2,
        "md5_excl==20": len(md5_excl) == 20,
    }

    # ---------- 4) 无漏排：保留 258 × 61 最小 mse ----------
    kept_idx = [j for j, f in enumerate(a_files) if stem(f) in kept_stems]
    sub = cross[np.ix_(kept_idx, range(len(t_files)))]
    jj, ii = np.unravel_index(np.argmin(sub), sub.shape)
    min_pair = (a_files[kept_idx[jj]], t_files[ii], float(sub[jj, ii]))
    col_min = sub.min(0)                               # 每张目标图在保留池中的最小 mse
    checks["no_missed_copy(min>=20)"] = bool(col_min.min() >= MSE_TH_SAMEPHOTO)
    print(f"[missed-copy-check] kept{len(kept_idx)} x {len(t_files)} min mse = {min_pair[2]:.1f} "
          f"({stem(min_pair[0])} <-> {stem(min_pair[1])}); per-target min: "
          f"median={np.median(col_min):.0f} max={col_min.max():.0f}")

    # 物化目录核对（stem 级）
    mat_img = {p.stem for p in CLEAN_DIR.iterdir()}
    mat_cond = {p.stem for p in COND_DIR.iterdir()}
    checks["materialized_imgs==kept"] = mat_img == kept_stems
    checks["materialized_conds==kept"] = mat_cond == kept_stems
    print(f"[materialize] imgs={len(mat_img)} conds={len(mat_cond)} (kept={len(kept_stems)})")

    # ---------- 5) 对应表输出 ----------
    twin_of = {}
    cluster_of = {}
    for cl in md5_clusters:
        for x in cl[1:]:
            twin_of[x] = cl[0]
        for x in cl:
            cluster_of[x] = cl
    by_target = {}
    for tf, af, m in crosspool:
        by_target.setdefault(tf, []).append((af, m))
    n_new = sum(1 for tf in cp_targets for af, m in by_target[tf] if af not in md5_excl)
    lines = [
        "# 跨池 29 组去重关系 ↔ 实际排除文件对应表（2026-11-11 复算）",
        "",
        f"> 全量重算自原始文件：A 域 {len(a_files)} × 目标域 {len(t_files)}，128×128 RGB mse，"
        f"同图阈值 <{MSE_TH_SAMEPHOTO:.0f}（实测同图 {min(x[2] for x in crosspool):.1f}–"
        f"{max(x[2] for x in crosspool):.1f}；保留池最小值 {min_pair[2]:.1f} = 同眼异帧）。",
        "",
        f"**{len(cp_targets)} 张目标图在 A 域共有 {len(cp_a_files)} 个副本 → {len(crosspool)} 对**。"
        f"其中 {len(cp_overlap)} 个副本本身是 md5 字节级重复簇里被排除的一方（与保留的主副本字节相同），"
        f"已计入 20 张 md5 排除；跨池规则**只需新增排除 {n_new} 张**（主副本）。",
        f"闭合：20（md5）+ {n_new}（跨池新增）+ 2（池内换壳）= {len(union)}；"
        f"{len(a_files)} − {len(union)} = {len(kept_stems)}。",
        "",
        "| # | 目标域图(61池) | A域同图副本 | mse | 该副本排除规则 | 字节级孪生(=同一文件) |",
        "|---|---|---|---|---|---|",
    ]
    for n, tf in enumerate(cp_targets, 1):
        for af, m in sorted(by_target[tf]):
            if af in md5_excl:
                rule = "①md5（重叠，计入 20）"
                twin = f"{stem(twin_of[af])}（保留→又被②排除）" if af in twin_of else "—"
            else:
                rule = "②跨池换壳（新增排除）"
                sib = [stem(x) for x in cluster_of.get(af, [af]) if x != af]
                twin = f"{sib[0]}（①已排除）" if sib else "—"
            lines.append(f"| {n} | {stem(tf)} | {stem(af)} | {m:.1f} | {rule} | {twin} |")
    lines += [
        "",
        "## 池内换壳 2 组（不涉目标域）",
        "",
        "| 保留 | 排除（字典序靠后） | mse |",
        "|---|---|---|",
    ]
    for x, y, m in within:
        lines.append(f"| {stem(x)} | {stem(y)} | {m:.1f} |")
    lines += [
        "",
        "## 无漏排验证（穷举）",
        "",
        f"- 保留 {len(kept_stems)} 张 × 61 张目标域全量 mse：最小值 **{min_pair[2]:.1f}**"
        f"（{stem(min_pair[0])} ↔ {stem(min_pair[1])}，即已披露的同眼异帧兄弟帧）≥ 阈值 {MSE_TH_SAMEPHOTO:.0f} → "
        + ("**无漏排**" if col_min.min() >= MSE_TH_SAMEPHOTO else "**存在漏排，需处理！**"),
        f"- 逐目标图最小 mse：median={np.median(col_min):.0f}，max={col_min.max():.0f}，"
        f"61/61 张 >{MSE_TH_SAMEPHOTO:.0f}：{bool((col_min >= MSE_TH_SAMEPHOTO).all())}",
        "",
        "## 一致性核对",
        "",
    ]
    for k, v in checks.items():
        lines.append(f"- {'✅' if v else '❌'} {k}")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"[out] {OUT_MD}")
    print(f"[verdict] {'ALL PASS' if all(checks.values()) else 'FAIL: ' + str([k for k, v in checks.items() if not v])}")


if __name__ == "__main__":
    main()
