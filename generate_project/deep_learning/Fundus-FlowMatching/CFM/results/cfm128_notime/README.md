# cfm128_notime — 去时间条件消融（负结果）

- **问题**：TTA-Flow 在 OCT 上"去时间条件更好"的结论能否迁移到眼底彩照。
- **变量**：cfm128 去掉时间条件输入。
- **结论**：**不迁移**。FID 183.7（比基线差）、KID 0.168（最差）；出血保留 0.522 反而最高（分布差但局部病理样信号强，矛盾如实记）。
- **登记**：`EXPERIMENTS.md` 执行记录 21。
- **指标**：`eval_data/cfm128_notime_metrics.json`、`cfm128_notime_fundus_metrics.json`。
