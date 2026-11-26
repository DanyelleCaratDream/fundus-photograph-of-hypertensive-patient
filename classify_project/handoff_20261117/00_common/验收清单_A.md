# 验收清单：组员 A

## A1 统计复核

- [ ] 输入 9 个预测文件 sha256 与清单一致
- [ ] 从 `logits` 复算的 `y_pred` 与文件内 `y_pred` 完全一致
- [ ] QWK / bAcc / macro-F1 / severe recall / 逐类 recall 全部给出（逐 seed + 跨 seed）
- [ ] 说明 sklearn 版本与参数（`weights='quadratic'`、`zero_division=0`）
- [ ] ΔA1−A0、ΔA2−A0 均给出点估计与 95% CI
- [ ] bootstrap：B、seed、分层方式、配对方式写明（B=1000，三 arm 共用重采样索引）
- [ ] 与 `baseline_numbers.md` 逐项差异表；差异有原因
- [ ] 明确写出"11-12 主结果无逐图预测，不可复算"
- [ ] 未使用 `bootstrap_ci.py`；脚本可独立运行
- [ ] 无"患者级 CI / 统计显著 / 证明无差异"表述

## A2 T3 复算

- [ ] 9 个 run 全部重算，逐 seed 指标齐全
- [ ] 同 seed ΔA1−A0、ΔA2−A0 + CI
- [ ] `optimizer_steps=1050` 全部核对
- [ ] 冻结类别权重逐一核对
- [ ] `fixed_draws`（A0 null / A1、A2 552）核对
- [ ] `epoch_stats` 30 条、`batches=35`、`last_batch=8` 核对
- [ ] 逐图 exposure 均值核对（A0 30；A1/A2 真实≈28.36）
- [ ] A1/A2 同 seed 抽样索引一致性核对
- [ ] 合成图与条件图配对关系核对
- [ ] 判定边界：0.02 非显著性、seed 层配对、不得合并 128/256 当独立样本

## 通用

- [ ] 输入只读，交付在独立目录
- [ ] 环境与命令齐全
- [ ] **结论卡五要素齐全**（结论/证据文件/计算方法/可复现脚本/局限性）
- [ ] 报告中的每条结论都能在结论卡找到对应行
- [ ] 每条结论可追溯
