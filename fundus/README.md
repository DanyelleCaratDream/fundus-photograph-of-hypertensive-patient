# fundus/ —— 数据池索引

> 本文件只回答“哪份数据是什么、能不能删”。口径与卫生结论以
> [docs/20-research/15-Data-Documentation.md](../docs/20-research/15-Data-Documentation.md) 为准；本目录图像整体不入 git（见 `.gitignore`）。

## 状态四档

- **规范**：训练/评估默认使用，不得随意改动
- **派生**：可由规范池 + 脚本重建，可删
- **墓园**：已移出但保留回滚（带 MANIFEST）
- **legacy**：不再用于新实验，仅历史引用

## 数据池总表

| 路径 | 数量 | 内容 | 状态 | 来源 / 备注 |
|---|---:|---|---|---|
| `_all_images_ORIGINAL/` | 299 | A 域网络眼底图（方形原图） | 规范 | 旧 A 域预训练实际 330，31 张作者事后淘汰；评估快照 `eval_data/real` 仍为 330 |
| `all_ORIGINAL_sq256/` | 163 | 手挑 A 域池（153 唯一）@256 | legacy | 早期 D 线候选池 |
| `combined_sq128/` | 193 | 合并训练池 @128（PNG） | 派生 | `combined_sq256` 的 128 版；仅 `eval/iqa_proxy_test.py` 仍引用 |
| `combined_sq256/` | 193 | 合并训练池 @256（JPG） | **规范** | D1/D2/D3/D4 与 CFM@128/256 训练池 |
| `a_domain_clean/` | 258 | 审计清洗后的 A 域（A_clean） | **规范** | 冻结名单见 `a_domain_clean_frozen.json`（2026-11-11 FROZEN） |
| `severe_train_sq128/` `severe_train_sq256/` | 76 | 老师 train severe 唯一底图（去 `_aug_1`） | 派生 | 由 `HRSG_4_758_v0.3.4` 派生 |
| `hrsevere_61_sq128/` `hrsevere_61_sq256/` | 61 | 冻结的纯 HR severe 62→61 名单 | **规范** | 名单 `hrsevere_61_frozen.json` + `hrsevere_61_FROZEN.md`（含 6 张连拍兄弟披露） |
| `HRSG_4_758_v0.3.4/` | 758 | 老师官方 4 级 DR 数据集（train 552 / val 135 / test 71） | **规范（只读）** | 只作源，不经训练脚本直接读（原图解码 67.8 ms/张） |
| `HRSG_4_758_square/` | 758 | 居中裁方 @原分辨率 | 派生 | `crop_to_square.py` 产物 |
| `HRSG_4_758_sq256/` | 758 | 预缩 @256，split 与原始一致 | **规范（分类器）** | 分类器训练/评估唯一口径（6.4 ms/张，10.6× 提速） |
| `_removed_dups_sq256/` | 36 图 + 36 mask + MANIFEST | 去重移出的副本 | 墓园 | 可回滚，勿删 MANIFEST |
| `reports/` | 3 | 跨 split 审计 CSV/JSON、train severe 跨 split 清单 | **规范（审计证据）** | 2026-11-06 / 11-07 |
| `a_domain_clean_frozen.json` / `_hashes.json` | — | A_clean 冻结名单（258）与逐图哈希 | **规范（冻结）** | 只允许改路径字段，内容不得改；见 audit README |
| `hrsevere_61_frozen.json` / `hrsevere_61_FROZEN.md` | — | 61 冻结名单与披露 | **规范（冻结）** | — |

## 脚本

| 脚本 | 作用 | 状态 |
|---|---|---|
| `crop_to_square.py` | 居中裁方（生成 `HRSG_4_758_square`） | 可重建 |
| `find_rotation_copies.py` | 旋转副本检索 | 一次审计 |
| `audit_cross_split_duplicates.py` | 跨 split 重复审计（生成 `reports/`） | 可复算 |

## 规范口径提醒

- 生成器训练/评估只用 **`combined_sq256`**；`combined_sq128` 是派生，不再新增使用。
- 分类器训练/评估只用 **`HRSG_4_758_sq256`**；`HRSG_4_758_v0.3.4` 只作源。
- 任何数据池增删，先更新本表，再更新 `docs/20-research/15-Data-Documentation.md`。
