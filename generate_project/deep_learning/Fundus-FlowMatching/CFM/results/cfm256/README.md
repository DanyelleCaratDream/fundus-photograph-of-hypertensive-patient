# cfm256 — CFM@256 原生（F3）

- **问题**：原生 256 能否补上 CFM@128 的锐度/细节短板。
- **变量**：从 cfm128 续训 1101→1420 轮；193 张 `combined_sq256`；bd128 / batch1 / L1+LPIPS+color。
- **结论**：分布/感知全面领先：FID 121.84、KID 0.084、BRISQUE 13.21（真实 11.02）、色彩距离 0.0345；作者目检 97/100。**代价是病灶弱于 D3**（出血保留 0.204 vs 0.754）。
- **登记**：`EXPERIMENTS.md` 执行记录 17–19。
- **指标**：`eval_data/cfm256_metrics.json`、`cfm256_fundus_metrics.json`。
