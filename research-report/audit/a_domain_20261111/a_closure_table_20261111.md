# 跨池 29 组去重关系 ↔ 实际排除文件对应表（2026-11-11 复算）

> 全量重算自原始文件：A 域 299 × 目标域 61，128×128 RGB mse，同图阈值 <20（实测同图 1.8–3.7；保留池最小值 55.6 = 同眼异帧）。

**19 张目标图在 A 域共有 29 个副本 → 29 对**。其中 10 个副本本身是 md5 字节级重复簇里被排除的一方（与保留的主副本字节相同），已计入 20 张 md5 排除；跨池规则**只需新增排除 19 张**（主副本）。
闭合：20（md5）+ 19（跨池新增）+ 2（池内换壳）= 41；299 − 41 = 258。

| # | 目标域图(61池) | A域同图副本 | mse | 该副本排除规则 | 字节级孪生(=同一文件) |
|---|---|---|---|---|---|
| 1 | 0bf8a9db042015e556be924ec11f3bba06f10cf2 | HRSRC_ATLAS_151_A | 3.1 | ②跨池换壳（新增排除） | HRSRC_DATASET_216（①已排除） |
| 1 | 0bf8a9db042015e556be924ec11f3bba06f10cf2 | HRSRC_DATASET_216 | 3.1 | ①md5（重叠，计入 20） | HRSRC_ATLAS_151_A（保留→又被②排除） |
| 2 | 101a775efe69f6fd9d6766d5ffd592c8d6569891 | HRSRC_ATLAS_153_A | 2.2 | ②跨池换壳（新增排除） | HRSRC_DATASET_223（①已排除） |
| 2 | 101a775efe69f6fd9d6766d5ffd592c8d6569891 | HRSRC_DATASET_223 | 2.2 | ①md5（重叠，计入 20） | HRSRC_ATLAS_153_A（保留→又被②排除） |
| 3 | 21e273fb1c3c8d166a735c3ce787b64c8ada67c2 | HRSRC_ATLAS_154_A | 3.2 | ②跨池换壳（新增排除） | HRSRC_DATASET_221（①已排除） |
| 3 | 21e273fb1c3c8d166a735c3ce787b64c8ada67c2 | HRSRC_DATASET_221 | 3.2 | ①md5（重叠，计入 20） | HRSRC_ATLAS_154_A（保留→又被②排除） |
| 4 | 28_left | HRSRC_CASE_002 | 1.8 | ②跨池换壳（新增排除） | — |
| 5 | 32_right | HRSRC_CASE_004 | 2.6 | ②跨池换壳（新增排除） | HRSRC_DATASET_210（①已排除） |
| 5 | 32_right | HRSRC_DATASET_210 | 2.6 | ①md5（重叠，计入 20） | HRSRC_CASE_004（保留→又被②排除） |
| 6 | 3de36b817ba577bb8a16dd8bf6c95fe05f66755c | HRSRC_ATLAS_156_A | 3.5 | ②跨池换壳（新增排除） | HRSRC_DATASET_217（①已排除） |
| 6 | 3de36b817ba577bb8a16dd8bf6c95fe05f66755c | HRSRC_DATASET_217 | 3.5 | ①md5（重叠，计入 20） | HRSRC_ATLAS_156_A（保留→又被②排除） |
| 7 | 3eed6f7d0e928c4f695757d2d154a82bf2e3b3d3 | HRSRC_ATLAS_157_A | 2.5 | ②跨池换壳（新增排除） | HRSRC_DATASET_218（①已排除） |
| 7 | 3eed6f7d0e928c4f695757d2d154a82bf2e3b3d3 | HRSRC_DATASET_218 | 2.5 | ①md5（重叠，计入 20） | HRSRC_ATLAS_157_A（保留→又被②排除） |
| 8 | 62e5366cb967fa9d728bd150fe39708c798a0530 | HRSRC_ATLAS_158_A | 2.9 | ②跨池换壳（新增排除） | HRSRC_DATASET_222（①已排除） |
| 8 | 62e5366cb967fa9d728bd150fe39708c798a0530 | HRSRC_DATASET_222 | 2.9 | ①md5（重叠，计入 20） | HRSRC_ATLAS_158_A（保留→又被②排除） |
| 9 | 6a5ac0d63bb17f4154922af743a98646d89455c2 | HRSRC_ATLAS_159_A | 2.8 | ②跨池换壳（新增排除） | HRSRC_DATASET_219（①已排除） |
| 9 | 6a5ac0d63bb17f4154922af743a98646d89455c2 | HRSRC_DATASET_219 | 2.8 | ①md5（重叠，计入 20） | HRSRC_ATLAS_159_A（保留→又被②排除） |
| 10 | 80036 | HRSRC_CASE_181_A | 3.3 | ②跨池换壳（新增排除） | — |
| 11 | 80045 | HRSRC_CASE_194_A | 2.5 | ②跨池换壳（新增排除） | — |
| 12 | 861_left | HRSRC_CASE_038 | 3.5 | ②跨池换壳（新增排除） | — |
| 13 | 8e06c22851c4492532a1b583383e96be579b00ad | HRSRC_ATLAS_160_A | 3.5 | ②跨池换壳（新增排除） | HRSRC_DATASET_220（①已排除） |
| 13 | 8e06c22851c4492532a1b583383e96be579b00ad | HRSRC_DATASET_220 | 3.5 | ①md5（重叠，计入 20） | HRSRC_ATLAS_160_A（保留→又被②排除） |
| 14 | 983_right | HRSRC_CASE_040 | 2.5 | ②跨池换壳（新增排除） | — |
| 15 | ceee348eb63613f6096d278ec0f16c11968d0a4d | HRSRC_ATLAS_161_A | 3.5 | ②跨池换壳（新增排除） | — |
| 16 | e3a5c4421746b2624928ca7921f79de55aadcf54 | HRSRC_ATLAS_162_A | 3.3 | ②跨池换壳（新增排除） | — |
| 17 | eb83e7b2d06cebb82e926c0ef14bd5dd6fc747d2 | HRSRC_ATLAS_163_A | 3.7 | ②跨池换壳（新增排除） | — |
| 18 | f3ef1dd4076e5badebfc9db6bbe30c2d19fc408e | HRSRC_ATLAS_164_A | 3.1 | ②跨池换壳（新增排除） | — |
| 19 | f40442bb45d1bd431e4a51375ebe1f7253cd1648 | HRSRC_ATLAS_165_A | 3.5 | ②跨池换壳（新增排除） | HRSRC_DATASET_230（①已排除） |
| 19 | f40442bb45d1bd431e4a51375ebe1f7253cd1648 | HRSRC_DATASET_230 | 3.5 | ①md5（重叠，计入 20） | HRSRC_ATLAS_165_A（保留→又被②排除） |

## 池内换壳 2 组（不涉目标域）

| 保留 | 排除（字典序靠后） | mse |
|---|---|---|
| HRSRC_ATLAS_254_A | HRSRC_ATLAS_270_A | 10.7 |
| HRSRC_ATLAS_271_A | HRSRC_ATLAS_322_A | 6.0 |

## 无漏排验证（穷举）

- 保留 258 张 × 61 张目标域全量 mse：最小值 **55.6**（HRSRC_CASE_198_A ↔ 80040，即已披露的同眼异帧兄弟帧）≥ 阈值 20 → **无漏排**
- 逐目标图最小 mse：median=654，max=1803，61/61 张 >20：True

## 一致性核对

- ✅ union==41
- ✅ union==JSON_excluded
- ✅ kept==258
- ✅ kept==JSON_files
- ✅ crosspool_pairs==29
- ✅ crosspool_unique_targets==19
- ✅ within_pairs==2
- ✅ md5_excl==20
- ✅ no_missed_copy(min>=20)
- ✅ materialized_imgs==kept
- ✅ materialized_conds==kept