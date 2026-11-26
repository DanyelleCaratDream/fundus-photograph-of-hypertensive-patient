# 任务 A：分类器统计复核与 T3 独立复算

> 负责人：组员 A（统计与结果复核线）
> 优先级：最高｜不占 GPU｜预计 2–3 小时
> 原则：**独立复算**，不是复述或整理现有报告；所有输入只读。

## 0. 目标

判断 DL-EX-027（分类器 pilot）与 DL-EX-032（T3）报告中的指标，能否由逐图预测和训练记录重新计算得到。

## A1. DL-EX-027 统计复核（现在即可开始）

**输入**

- `00_common/predictions/A{0,1,2}_seed{42,52,62}.json`（9 个）
- `01_A_pilot/baseline_numbers.md`（现有数字，供核对）
- `00_common/指标与CI规范.md`

**要做**

1. 从 `logits` 重新 argmax 得到预测，与文件里的 `y_pred` 核对。
2. 独立计算每个 seed 的 QWK、balanced accuracy、macro-F1、severe recall、逐类 recall。
3. 给出跨 seed 的均值与标准差。
4. 按规范做配对、分层 bootstrap：逐 seed 的 Δ 与合并后的 Δ，B=1000，记录 seed。
5. 与 `baseline_numbers.md` 逐项核对；不一致必须定位原因（实现差异？数字错误？）。
6. **明确写出**：11-12 主结果没有逐图预测，无法复算，只能核对汇总与重跑差值。

**禁止**

- 不重新选择 checkpoint；不按 test 调参。
- 不把 CI 说成跨患者置信区间；不把 13 张 severe 支持细粒度亚组结论。
- 不使用 `bootstrap_ci.py`（它是被复核对象）。

## A2. DL-EX-032 独立复算（等 9 次产物冻结后）

**输入**

- `02_A_t3/t3_runs/*.json`、`02_A_t3/predictions/*.json`
- `02_A_t3/T3_输入说明.md`

**要做**

1. 从逐图预测重算每个 seed 的 QWK 与预定指标。
2. 计算同 seed 的 ΔA1−A0、ΔA2−A0，以及配对分层 bootstrap CI。
3. 核对每次 run：`optimizer_steps=1050`、冻结类别权重、`fixed_draws`、`epoch_stats`、
   逐图 exposure、A1/A2 同 seed 抽样是否一致。
4. 核对 A1/A2 对应 seed 与条件图的配对关系。
5. 输出"原汇总 vs 独立复算"逐项差异表。

**禁止**

- 不修改训练产物或预测；不覆盖原报告。
- 不把确定性模式解释为"消除全部随机性"；不把 0.02 当显著性线。
- 不把 9 次运行当 9 个独立样本做组间显著性检验。

## 交付物

| 文件 | 内容 |
|---|---|
| `submissions/A/A1_统计复核报告.md` | 方法、逐 seed 表、Δ 与 CI、与现有数字的差异及原因、限制 |
| `submissions/A/A2_T3复算报告.md` | 同上 + 训练记录核对表 |
| `submissions/A/结论卡.csv` | **每条结论一行，五要素齐全**（见 `00_common/结论卡模板.md`） |
| `submissions/A/recompute.py` | 可独立运行；带 `--self-check` 或明确入口 |
| `submissions/A/差异表.csv` | 原数字 / 复算数字 / 差值 / 原因 |
| `submissions/A/环境.txt` | Python/sklearn/numpy 版本与运行命令 |

> **共同提交标准（导师 2026-11-17 定）**：每条结论必须同时给出
> 结论 / 证据文件 / 计算方法 / 可复现脚本 / 局限性。缺一项视为未提交。

## 红线

1. 输入只读；交付写独立目录。
2. 不碰 `EXPERIMENTS.md`、`PROJECT_STATE.md`、报告正文。
3. 不根据结果改实验设计或口径。
4. 每条结论都要能指回输入文件与代码位置。

## 验收

见 `00_common/验收清单_A.md`。通过标准：复算可重复、差异有解释、
训练记录核对项齐全、报告无越界表述。
