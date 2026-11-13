# 分类器底盘 Pilot 预注册（2026-11-12）

> 状态：**DRAFT — 划分口径已定（不重划分）；待其余三项确认后冻结**
> 负责人：分类器侧
> 关联：[HANDOFF_TSTR_20261106.md](HANDOFF_TSTR_20261106.md) · [README.md](README.md) · `generate_project/deep_learning/EXPERIMENTS.md`
> 本文件只写"开跑前定死的东西"；结果出来后另起结果文件，并登记 EXPERIMENTS.md。

## 0. 一句话目的

在**完全不使用任何生成图**的前提下，确定 HR 4 级分类器在真实数据上的"上界"和底盘，为后续 TSTR 提供唯一基线。

## 1. 要回答的问题

现有 TSTR 基线是 ResNet18@256 + 加权 CE（历史 QWK≈0.747；官方 split 含已知跨 split 重复，按老师决定不重划分，数字需带此标注）。
文献提示还有三条可能更优的路线：

- 不平衡处理：logit adjustment / DRC 两阶段
- 有序建模：序数回归（CORAL）
- 小样本特征：RETFound 冻结 backbone

**问题：在 HRSG 758（severe 唯一图仅 76）上，哪条路线真的提升 QWK？提升多少？**

## 2. 预先写死的假设

| 编号 | 假设 | 判定 |
|:--:|:--|:--|
| H1 | 序数头 / DRC 比 A0 提升 QWK ≥ 0.02 | 支持/不支持 |
| H2 | RETFound frozen + 线性/序数头比 A0 ≥ 0.03 | 支持/不支持 |
| H0 | 全部路线提升 < 0.02 | 则"分类器底盘不是瓶颈"，TSTR 维持 ResNet18 |

这三条是预期，不是结论；结果出来后照实写支持或不支持。

## 3. 数据与隔离（硬约束）

- 数据：训练读 `fundus/HRSG_4_758_sq256/`（居中裁方 + 预缩 256，758 张，split 与原始完全一致）；`fundus/HRSG_4_758_v0.3.4/` 只作源，**不要直接训练**（原始图 2304–3456px，每张解码约 68ms，比 sq256 慢 10 倍）。4 类 normal / mild / moderate / severe。
- 计数（唯一底图）：train 120 / 140 / 140 / **76**；val 34 / 40 / 40 / 21；test 18 / 20 / 20 / **13**。
- ⚠️ train/severe 另有 76 张 `_aug_1` 垂直翻转副本，数据集自带。**按文件原样读（552 个文件），不剔除副本。**
- **本 pilot 一张生成图都不用**；val/test 永远保持真实。
- 划分口径（**老师 2026-11-12 裁定：不重划分**）：
  - 正式口径 = 老师官方 split（与老师、组员、历史数字对齐）。
  - 已审计出的 32 对跨 split 重复（`fundus/reports/cross_split_audit_2026-11-06.csv`）**不做重划分**，只在论文/报告中如实披露。
  - 所有数字标注"含已知跨 split 重复，按老师决定未重划分"，不隐瞒、不夸大。

## 4. 模型 arms（同数据、同评估、同 seeds）

| Arm | 模型 | 说明 |
|:--:|:--|:--|
| A0 | ResNet18@256 + ImageNet + 加权 CE | 现有基线，必须先复现 |
| A1 | A0 + post-hoc logit adjustment | τ 只在 val 上调 |
| A2 | A0 + DRC 两阶段 | 阶段1 原始分布学表示；阶段2 类平衡重训分类头 |
| A3 | RETFound ViT-L/16 **frozen** @224 + 线性头 | 眼底预训练的价值 |
| A4 | RETFound frozen + CORAL 序数头 | 预训练 + 有序建模 |
| A5 | ViT-B/16 ImageNet frozen + 线性头（对照） | 区分"眼底预训练"与"ViT 架构"的贡献 |

A5 不能省：否则 RETFound 赢了也说不清是预训练还是架构的功劳。

## 5. 训练协议（沿用现有脚本，不引入新变量）

- 优化器 AdamW，lr 1e-4，batch 16，30 epochs，cosine 退火；seeds **42 / 52 / 62**。
- 加权 CE，类别权重 = 逆频率。
- 按 **val QWK** 选最佳 epoch；test 只在最后评一次。
- 预处理：Resize + ImageNet normalize；**不加数据增强**（与现有协议一致）。
- A1 的 τ、A3/A4/A5 的头学习率，只在 val 上网格搜索，test 不参与。
- RETFound / ViT 先一次性提取 frozen 特征并缓存，再训头，避免重复前向。
- 代码状态：**A1/A2 已实现**（`train_classifier.py --logit-adjust` / `--drc`），
  纯函数与冻结逻辑自检 `test_pilot_arms.py` 6 项通过（2026-11-12）；A3–A5 待写。

## 6. 指标

- **主指标：QWK**（3 seeds 的均值 ± 标准差）。
- 次指标：balanced accuracy、macro-F1、severe recall、各类 recall、混淆矩阵。
- 不确定性：test severe 仅 13 张，**1 张图 ≈ 7.7pp**；主指标给 bootstrap 1000 次的 95% CI。
- 不单独报 overall accuracy（会被 normal 类抬高）。

## 7. 裁决规则（提前定死，防止事后挑结果）

1. 按 QWK 均值排序。
2. 若第一名与 A0 的差值 **< 0.02**（预设最小有意义差异 MCID），判"无实质提升"，保留 A0。
3. 若 A3/A4 胜出，必须同时看 A5：A5 与 A3 差距 < 0.01 → 结论写成"ViT 架构的功劳"，不能写成"眼底预训练的功劳"。
4. 所有 arm 全部报告，不因结果差删除。
5. test 上不调任何超参、不早停、不换指标。

## 8. 成功 / 失败判据

- **成功**：找到 ≥ 0.02 QWK 提升、且 severe recall 下降不超过 5pp 的 arm。
- **失败**：全部 < 0.02 → 写"分类器底盘不是瓶颈"，TSTR 继续用 ResNet18，精力回生成侧。
- 部分成功：QWK 升但 severe recall 掉 >5pp → 判"不可用"，因为我们的核心就是 severe。

## 9. 产出与登记

- 结果 JSON：`classify_project/results/pilot_<arm>_<date>.json`（复用现有格式）。
- 汇总：一页表（arm × QWK/bAcc/macroF1/severe recall）+ 混淆矩阵。
- `EXPERIMENTS.md` 预注册时占号 **DL-EX-027**，结果出来补录。

## 10. 计算预算

- A0/A1/A2：3 seeds × 30 epochs，每 arm 半小时内。
- A3/A4/A5：特征提取一次 + 头训练，每 arm 十分钟级。
- 总计 < 2 小时单卡。

## 11. 待老师确认（冻结前必须问清）

1. ~~官方 split 是否作为正式口径；是否允许按去重分组重划分。~~ ✅ 2026-11-12 老师裁定：官方 split 为正式口径，不重划分。
2. 4 级（normal/mild/moderate/severe）与 KW 分级的对应关系。
3. val 能否用于选 epoch / 调超参（现有协议是这么做的）。
4. test severe 只有 13 张，是否接受"结论必须带 CI、单张图影响 7.7pp"的写法。

## 12. 与 TSTR 的关系

本 pilot 只定"真实数据上的分类器上界和底盘"，**不评价任何生成器**。
TSTR 阶段沿用本 pilot 选出的底盘和同一套协议，只改变"train 里是否注入生成 severe 图"，比较相对变化。
