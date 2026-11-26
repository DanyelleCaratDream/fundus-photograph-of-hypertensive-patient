# 指标定义与 bootstrap CI 规范（任务 1、6 必须遵守）

> 目的：让两个人的复算结果可比、可核对。**不提供现成实现**，请按规范独立编写；
> 完成后在报告里写明实现细节与随机种子。

## 1. 指标

| 指标 | 定义 |
|---|---|
| acc | `mean(y_pred == y_true)` |
| balanced accuracy | `sklearn.metrics.balanced_accuracy_score`（各类召回的平均） |
| macro-F1 | `sklearn.metrics.f1_score(average='macro', zero_division=0)` |
| QWK | `sklearn.metrics.cohen_kappa_score(weights='quadratic')` |
| severe recall | `y_true==3` 中预测为 3 的比例 |
| 逐类 recall | 每个类的召回；分母为该类真实样本数 |

- 预测值一律用**决策 logits** 的 argmax（文件里已给出 `y_pred`，但必须自己从 `logits` 复算一遍核对）。
- A1 的 `logits` 是做过 logit adjustment 的决策 logits；A2 无 adjustment。
- test 只有 71 张、severe 只有 13 张：**1 张 ≈ 1.4 个百分点 acc / 7.7 个百分点 severe recall**，
  不得用"精确到 0.001"的口吻描述。

## 2. 配对 bootstrap（Δ 的 CI）

| 项 | 规定 |
|---|---|
| 重采样单位 | **test 图像**（不是患者；本数据无法确认患者级独立） |
| 分层方式 | 按 `y_true` 分层，层内按原样本量有放回抽样 |
| 重复次数 | **B = 1000**（可加做 10000 作为稳定性检查，报告主结果用 1000） |
| 随机种子 | 明确记录（建议 20261117），三个 arm 共用同一组重采样索引 |
| 配对 | 每次 bootstrap 迭代中，A0/A1/A2 使用**完全相同**的重采样索引；先算各自的指标，再算 Δ |
| 区间 | 百分位法，2.5% / 97.5% |
| 报告 | 点估计、CI 下/上界、B、seed、每类样本数 |

- 必须报告：`ΔA1−A0`、`ΔA2−A0`（逐 seed 与合并方式要说清）。
- 逐 seed 的 Δ 与跨 seed 汇总（均值/标准差）分开展示，不混用。
- CI 跨 0 时只能写"未观察到可复现的差异"，不能写"证明无差异"。

## 3. 禁止

- 不得对 test 做任何调参、阈值搜索、checkpoint 重选。
- 不得把 CI 解释为患者级置信区间或统计显著性检验。
- 不得只报告有利 seed；所有 seed、所有 arm 全报（失败也报）。
- 不得直接复制或调用 `bootstrap_ci.py`（那是待复核对象）；请独立实现。
