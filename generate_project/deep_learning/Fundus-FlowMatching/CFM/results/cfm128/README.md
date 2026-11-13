# cfm128 — CFM@128 基线（F2）

- **问题**：把 DDPM 权重迁到条件流匹配后，128px 下是否还能保持生成质量。
- **变量**：初始化 = `ddpm/results_film_l1lpips/final_model.pth`；193 张 `combined_sq128`；1100 轮。
- **结论**：可用基线。FID 178.87 / KID 0.158±0.007 / BRISQUE 38.0；病灶保留弱于 D3（出血保留 0.320 vs 0.754）。
- **登记**：`EXPERIMENTS.md` 第 6 章 / 执行记录 16–20。
- **指标**：`eval_data/cfm128_metrics.json`、`cfm128_fundus_metrics.json`。
