# research-report/audit —— 导师评审与数据审计证据

> 2026-11-12 由 `advisor_review_20261106/`、`advisor_review_20261109/` 合并而来。
> 本目录只放**仍在被引用**的证据；已取代的规划材料在 `_archive/advisor_history/`。

## 一、材料索引

| 材料 | 对应 | 报告位置 | 状态 |
|---|---|---|---|
| `advisor_20261106/README.md` | 2026-11-06 对导师意见的答复包（渗出加权真实实现、3× 归一化、增强错位、KID 重算、Q&A） | REPORT_DL §7.8（两处训练缺陷） | ✅ 仍有效 |
| `advisor_20261106/01–04*.png` | 真实/CFM@256/加权/低清对比、渗出强度排序、TTA-HM 负结果、Tiger 零样本负结果 | §7 / 第 6 章 | ✅ 证据图 |
| `advisor_20261106/code/` | 加权损失修复前后代码、数据集 `__getitem__` 摘录、诊断脚本、配置快照 | §7.8 | ✅ 代码证据（CFM README 指向此） |
| `a_domain_20261111/a_domain_audit_20261111.md` | A 域审计主文：330→299→258、三层重复、T0 五项核对、预算 | REPORT_DL_v2 §1.4；EXPERIMENTS DL-EX-026 | ✅ 主文档 |
| `a_domain_20261111/a_closure_table_20261111.md` | 闭合表：20(md5)+19(跨池新增)+2(池内)=41，299−41=258 | DL-EX-026 | ✅ |
| `a_domain_20261111/a_domain_dupmap_20261111.txt` | 重复簇明细（同图 / 同眼异帧） | DL-EX-026 | ✅ |
| `a_domain_20261111/a_domain_audit_lists_20261111.txt` | 原始中间清单（cond-orphan、near-dup） | 审计原始数据 | ✅ |
| `a_domain_20261111/td01_precheck_20261111.md` | T0/T1 开跑前核对；发现缺陷 A（增强错位）、B（DDPM→CFM 跨目标） | DL-EX-026 | ✅ |
| `a_domain_20261111/a_domain_pair_check_20261111/` | 20 对 RGB↔骨架叠加图 + `pair_check_result.json`（20/20 identity=1.0） | §1.4；`figures/fig_pair_check_20.png` 的输入 | ✅ |
| `a_domain_20261111/a_pair_check_full_20261111.json` | 258 对全量复核（257/258=1.0000，唯一例外 HRSRC_DATASET_306=0.9432 已披露） | DL-EX-026 | ✅ |
| `a_domain_20261111/*.py` | 三个可复算脚本（closure / pair check / freeze+hash） | 审计附录 | ✅ 可复算 |

## 二、冻结名单路径变更说明（2026-11-12）

`fundus/a_domain_clean_frozen.json` 中的 `closure_table` 与 `pair_check` 两个**路径字段**
已改为本目录新位置。`files` / `excluded` / `count` 与 `a_domain_clean_frozen_hashes.json`
**完全未改动**（`status` 仍为 FROZEN-2026-11-11）。

## 三、已移出的材料

以下已被 2026-11-11 汇报与报告正文取代、且全仓库零引用，移到 `_archive/advisor_history/`：

- `汇报_20261109.md/.docx` + `build_docx.py`（11-09 进展汇报旧快照）
- `crosssplit_verification_20261107.md`（72 vs 61 跨 split 核查）
- `data_provenance_and_training_plan_20261107.md`（193 混合池溯源 + C1/C2 方案）
- `pilot_failure_and_options_20261108.md`（61 张 320 轮试点失败与三条路线）

## 四、复算方法

脚本用“向上找 `CLAUDE.md`”定位仓库根，可在任意位置运行：

```bash
python research-report/audit/a_domain_20261111/a_closure_verify_20261111.py
python research-report/audit/a_domain_20261111/a_pair_check_20261111.py
python research-report/audit/a_domain_20261111/a_freeze_finalize_20261111.py
```

判图/叠加图含真实患者图像，本目录的 audit 证据图**仅在本地与私有仓库保留**；公开仓库按 B 仓库规则处理。
