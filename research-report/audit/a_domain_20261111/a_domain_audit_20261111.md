# A 域数据审计 + T0 核对报告（2026-11-11）

> 对应导师"A域预训练开跑前检查表"三项 + T0 checkpoint 五项核对 + 预算建议。
> 所有数字可在仓库复核，明细文件路径均已给出。

## 一、检查表 1：A 域数据量审计 —— 330 → 299 → **258**

### 层层溯源
| 层 | 数量 | 说明 |
|---|---|---|
| 旧 A 域预训练实际用图 | **330** | config → `_all_images_ORIGINAL`；配套骨架 330；eval_data/real=330；31 张为作者事后手动淘汰（docs/20-research/15） |
| 现存 | 299 | 293 jpg + 6 png |
| 审计后唯一图（候选冻结） | **258** | 见下 |

### 审计发现的三层重复（32×32 灰度粗筛 + 128×128 RGB 精判）
| 层 | 对数 | 性质 | 处理 |
|---|---|---|---|
| ① md5 字节级重复 | 20 | 同一文件存两份（如 `HRSRC_ATLAS_328_A`=`HRSRC_ATLAS_281_A`） | 排除字典序靠后副本 |
| ② 换壳副本（128RGB mse 2–11） | 31（跨池 29 + 池内 2） | **同一张照片**不同编码/尺寸 | 跨池：A 域副本全排除；池内：字典序靠后排除 |
| ③ 同眼异帧（128RGB mse 56–630，含灰区） | 38 | 同一采集序列不同帧 | 保留 + 披露（与 61 名单同口径） |

### ⚠️ 最重要发现：数据泄漏
**61 张目标域 HR severe 图中，19 张在 A 域池存在换壳副本**（如 `62e5366c…` ↔ `HRSRC_DATASET_222`，128RGB mse≈2.8 = 同一张照片）。
若不清洗，A 域预训练 = 变相见过 31% 的目标域数据，T0/T1 对比被污染——"迁移"优势会混入"多看一遍目标域"的效应。
另有 2 对 61 侧图的**同眼异帧**兄弟帧在 A 域（`62e5366c…`↔`HRSRC_CASE_027`、`80040`↔`HRSRC_CASE_198_A`）——患者级重叠，建议保留+披露（对应导师第五点口径）。

### 候选冻结名单（待批准）
- **A_clean = 299 − 41 = 258 张**（排除 = 20 md5 副本 + 19 换壳跨池副本 + 2 换壳池内副本，去重后计 41）
- 条件骨架 258/258 全齐（0 缺失）
- 名单：`fundus/a_domain_clean_frozen_CANDIDATE.json`（含排除清单与规则）
- 已物化：`fundus/a_domain_clean/`（258 原图）+ `CFM/data/conditions_a_domain_clean/`（258 骨架）
- 逐对明细：`research-report/audit/a_domain_20261111/a_domain_dupmap_20261111.txt`

## 二、检查表 2：旧 A 域代码输入方式 —— RGB + 配对血管 mask，增强错位坐实

2026-07-28 版 `train.py`（`git show 037d071` 存档 /tmp/train_20260728.py）：
- `FundusDataset(root, transform, cond_root=args.cond_path)` → **确认是条件生成**（RGB + 1 通道血管骨架，`cond_path=./conditions`）
- `cond_transform` 未传入 → 回落 `transform`；图像与 mask 各自独立采样 `Flip(0.5)+Rot(15°)` → **约 50% 错位**（即预检报告的问题 A）
- → 新 A 域训练直接复用修复后管线（当前 ddpm/train.py，2026-11-06 起图像/条件同步增强），无需新写数据代码

## 三、检查表 3：T0 checkpoint 五项核对 —— 全部通过

| # | 项 | 证据 |
|---|---|---|
| 1 | 随机初始化 | 首段 log `Training started 2026-11-07 22:02:36`，Args **resume=null**（注：config.json 里的 resume=…000667 是最后一次续训覆盖保存，勿误读） |
| 2 | 冻结 61 张 | dataset=hrsevere_61_sq128，目录 61 张 ↔ `hrsevere_61_frozen.json` 61/61 匹配 |
| 3 | 实际 20,010 步 | 61 张 batch2 drop_last → 30 步/轮 × 667 轮；log Epoch 1–1000 连续；ckpt 内 epoch=666（0 起始）↔ 文件名 667（1 起始）自洽 |
| 4 | 配置与 T1 一致 | 128 / bd128 / batch2 / lr 1e-4 / L1+LPIPS 0.1+color 0.01 / EMA 0.9999 / seed 42 / objective=cfm |
| 5 | raw 为主 | E2/E3/E4 全部 raw 协议 |

**诚实披露三项**：
1. log 有一次**中止的续训**（重复 epoch 321–326，两段 "Resumed at epoch 320"）；被覆盖后从 320 重跑，最终轨迹连续，20,010 步成立
2. 旧 checkpoint **无 global_step 字段**，20,010 由轮数×每轮步数推算；train.py 现已补显式 global_step
3. 61 名单含 6 张 1ffa95aX 疑似序列关联（commit 990fb8a 已披露）

## 四、A 域预训练预算建议（对应"先核对旧日志与损失曲线"）

旧 A 域（DDPM，330 张 batch5 = 66 步/轮，780 轮）loss 轨迹：
`ep1 0.551 → ep50 0.073 → ep100 0.058 → ep200 0.059 → ep300 0.058 → ep500 0.052 → ep780 0.052`
→ **约 ep100–200 进入平台**，780 轮远超平台。

但本项目自己的反例：61 张试点 loss 约 ep100 后趋平，而 15k→20,010 步仍出现真实质量突破（圆形轮廓、梯度能量 0.0120→0.0139）——**loss 平台 ≠ 质量平台**。

**建议**：预注册 **780 轮**（258 张 batch5 = 51 步/轮 → **39,780 步**），每 50 轮存档供诊断扫描（不用于选点）。
估时约 8–13h（旧 52s/轮 × 780 ≈ 11h；含 cool_sleep 待确认）。待导师拍板。

## 五、代码改动（已完成，向后兼容）

1. **`ddpm/train.py` 新增 `--init_weights_only`**（迁移初始化模式）：
   - 只加载 `--resume` 的 `model_state_dict`，**strict=True**（缺失/多余参数直接报错，不静默跳过）
   - epoch 归零、**优化器全新**（不继承 Adam 动量）、**EMA 从加载后权重重建**（不继承旧 EMA）
   - 日志开新文件，Args 含 `init_weights_only: true` 可追溯；不修改任何原始权重文件
2. **显式 `global_step`**：每 `optimizer.step()` +1；写入定期/中断/最终三种 checkpoint；epoch 日志行追加 `step=`
3. **冒烟测试（0-epoch，无训练发生）**：
   - T0 checkpoint strict 加载 ✅ 成功（无缺失/多余参数）；final_model.pth 含 `global_step: 0` ✅
   - 预设 dry-run 命令正确 ✅；py_compile 通过 ✅
   - **负结果验证**：旧 A 域 DDPM 权重 strict 也能干净加载 → 7 月 FiLM 架构与当前代码**逐键一致**；strict 拦截的是"架构不匹配"，旧权重弃用的真实理由是三重缺陷（增强错位 / DDPM 目标 / 泄漏副本），不是架构
4. **`train_cfm.py` 新增预设 `a_domain_clean_cfm128`**（258 张 / batch5 / 780 轮 / 输出 results/a_domain_clean_cfm128）

## 六、待导师批准后执行

```bash
# 1) A_clean 预训练（批准名单+预算后）
python train/train_cfm.py --preset a_domain_clean_cfm128

# 2) A_clean 完成后 T1（唯一差异=初始化来源）
python train/train_cfm.py --preset cfm128_hrsevere_pilot \
  --resume <A_clean>/models/final_model.pth --init_weights_only --epochs 667

# 3) T0 冻结不动（checkpoint_epoch_000667.pth）；对比出图 8 条件×4 seed=64 张，五维分开评
```

**待批清单**：① 258 张冻结名单 ② 780 轮预算 ③ docs/20-research/15 更正口径（"旧 A 域预训练实际用 330，现存 299，审计后唯一 258"）

---

## 七、导师复核回应（2026-11-11 第二轮）：跨池 29→19 的闭合 + 20 对配对抽查

### 7.1 数字问题：为什么 29 组跨池只计入 19 张排除？

**29 组是"对"数，不是"待排除文件"数。** 全量重算（A 域 299 × 目标域 61，128×128 RGB mse，不依赖原 dupmap）确认：

- 19 张目标域图在 A 域共有 **29 个副本**：其中 **10 张目标图各有 2 个 A 域副本**（9 张 ATLAS/CASE 主副本 + 各自一个**字节级相同的 DATASET 孪生**），9 张目标图各有 1 个副本；
- 这 10 个 DATASET 孪生本身就是 md5 重复簇里"字典序靠后"的一方，**已计入 20 张 md5 排除**（与规则①重叠，不重复计数）；
- 因此跨池规则只需**新增排除 19 张主副本**（13 ATLAS + 6 CASE）。

**闭合：20（md5）+ 19（跨池新增）+ 2（池内换壳）= 41；299 − 41 = 258。** 逐组对应表（含每个副本的排除规则与字节孪生关系）：
`research-report/audit/a_domain_20261111/a_closure_table_20261111.md`（脚本 `a_closure_verify_20261111.py` 可复算，10 项一致性核对全部 ✅）。

**无漏排验证（穷举）**：保留 258 张 × 61 张目标域全量 mse，最小值 **55.6**（`HRSRC_CASE_198_A` ↔ `80040`，即第五节已披露的同眼异帧兄弟帧，非同图），61/61 张目标图逐张最小 mse 均 >20（median=654）→ **A_clean 中不存在任何遗漏的目标域同图副本**。

### 7.2 随机抽查 20 对 RGB ↔ 血管骨架：20/20 通过

方法（比纯目视更严）：条件图由 `prep_conditions.py::extract_vessel_mask` 从配对 RGB 生成（按 stem 配对，`splitext(fname)[0]+".png"`）。对随机抽取 20 对（seed=20261111），**用同一算法从 `fundus/a_domain_clean/` 的 RGB 重新推导 mask**，与存档 `conditions_a_domain_clean/` 逐像素比对：

| 指标 | 结果 | 判读 |
|---|---|---|
| identity 一致率 | **20/20 = 1.0000**（逐像素精确复现） | 配对正确、方向与位置一致 |
| 翻转/旋转/转置对照 | 最高 0.917（最弱例 CASE_016，大片均匀 mask 区） | 方向错必然掉到 ≤0.92 |
| ±3px 平移对照 | 最高 0.917 | 位置错必然暴露 |
| 错配其他图对照 | 最高 0.819 | 配对错必然暴露 |

- **结论：20 对全部通过**，无一例翻转/错位/错配。
- 产物（供人工复核）：`research-report/audit/a_domain_20261111/a_domain_pair_check_20261111/`（20 张叠加图 `overlay_*.png`（红色=条件结构）、拼图 `montage_20.png`、明细 `pair_check_result.json`；脚本 `a_pair_check_20261111.py` 可复算）。
- 附注：存档条件图为该算法的 mask 模式输出，与 61 池条件同源同口径（旧 330 条件的逐字节拷贝，已验证）。

### 7.3 据此执行的动作

1. **冻结名单**：`fundus/a_domain_clean_frozen_CANDIDATE.json` → **`fundus/a_domain_clean_frozen.json`**（status=FROZEN-2026-11-11，count=258；文件内容不变，仅状态与依据字段更新）
2. `train_cfm.py` 预设 `a_domain_clean_cfm128` 注释同步更名与闭合算式；预设本身未改动
3. **T0 未做任何修改**（`checkpoint_epoch_000667.pth` 原样）
4. 预注册 780 轮预算维持建议，待作者确认开训时间

---

## 八、导师第二轮批准（2026-11-11）+ 阶段 1 执行记录

导师复核结论：数字闭合通过、20 对配对抽查通过，**批准进入 A 域预训练**（预注册配置同第七节）。
导师附加的两点口径，均已采纳：

1. **无漏排验证的适用范围**：穷举 mse 只证明"指定相似度方法下无低于阈值的近重复"，**不证明无患者级关联**——
   38 对同眼异帧（含 61 侧 2 对）保留 + 最终论文披露。
2. **配对正确 ≠ 骨架医学正确**：抽查证明的是图像↔骨架无错配/几何错位；自动提取骨架是否符合真实血管解剖
   是另一回事，论文中不混谈。

### 阶段 1（冻结数据集）执行情况（2026-11-11）

- [x] **文件哈希入档**：`fundus/a_domain_clean_frozen_hashes.json`（258 图 + 258 骨架 md5，各 258 唯一，无碰撞）
- [x] **全量 258 对确定性重建复核**（导师建议的低成本完整性检查，脚本 `a_freeze_finalize_20261111.py`）：
  - 257/258 identity = 1.0000（逐像素精确复现）
  - 唯一例外 `HRSRC_DATASET_306` = **0.9432**：差异为全图分散的阈值边缘像素（~5.7%），该图自身几何对照
    （flip/rot/transpose ≤0.635、错配 0.523）远低于 identity → **配对/方向/位置正确，非几何错位**。
    交叉验证：原始文件与 a_domain_clean 拷贝 md5 相同、新 258 条件与旧 330 条件逐字节一致、原始文件重推导
    同为 0.9432 → 差异源于当年生成条件图的环境（cv2 版本微差，该图为 18KB 高压缩小图对解码敏感），
    数据链路未被动过。**判定 PASS（含披露）**，明细 `a_pair_check_full_20261111.json`
- [x] 19 张跨池副本与 38 对同眼异帧审计结果：第一、六、七节 + `a_domain_dupmap_20261111.txt` 已载
- [x] **drop_last 行为核实并登记**（导师特别提醒）：258 张 batch5 `shuffle=True, drop_last=True` →
  每轮 51 步实际用 255 张，尾部 3 张丢弃且**逐轮随机轮换**（非固定 3 张）→ 已写入 EXPERIMENTS.md DL-EX-026

### 开训

- 预注册配置已登记 EXPERIMENTS.md（DL-EX-026）；完成后验收清单：epoch=780、global_step=39,780、
  raw strict 加载、log 完整、无 NaN。
- T0 未做任何修改。

