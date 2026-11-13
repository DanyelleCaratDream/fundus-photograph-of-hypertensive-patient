# cfm128_featA — RETFound 特征检索条件消融

- **问题**：换成 RETFound-CFP 1024 维基础模型特征做检索条件，是否比手工特征更好。
- **变量**：cfm128 + RETFound 检索条件（featA）。
- **结论**：方向同 featC 但幅度更弱（FID 162.8、出血存在 0.383 最高）；**可解释手工特征在病理保真上反超黑盒特征**。
- **登记**：`EXPERIMENTS.md` 执行记录 21。
- **指标**：`eval_data/cfm128_featA_metrics.json`、`cfm128_featA_fundus_metrics.json`、`cfm128_featA_diversity.json`。
