# cfm128_featC — 手工特征检索条件消融

- **问题**：15 维手工特征 + Dirichlet 重心检索条件，能否提升病理保真。
- **变量**：cfm128 + 检索条件（featC）。
- **结论**：走"病理保真 + 多样性"路线。FID 164.9（未改善），但出血保留 0.567（最高）、C2ST 0.836（全方法最难判别）、多样性 +7.8%。
- **登记**：`EXPERIMENTS.md` 执行记录 21。
- **指标**：`eval_data/cfm128_featC_metrics.json`、`cfm128_featC_fundus_metrics.json`、`cfm128_featC_diversity.json`。
