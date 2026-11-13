# cfm128_align — 时间轴对齐消融

- **问题**：DDPM→CFM 的时间语义反转（index 0=干净 vs t=0=噪声）是否是一处隐性损失源。
- **变量**：与 cfm128 完全相同，唯一差异 = `--cfm_time_align`（`idx=(1−t)·T`）。
- **结论**：有效。FID 178.9→151.8（−15%）、KID 0.158→0.121，收敛更稳；后被 text 条件超过。
- **登记**：`EXPERIMENTS.md` 执行记录 20–21。
- **指标**：`eval_data/cfm128_align_metrics.json`、`cfm128_align_fundus_metrics.json`。
