# cfm128_text — 文本条件消融

- **问题**：在时间嵌入上加 severe 文本条件，能否提升真实感。
- **变量**：cfm128 + 零初始化 `text_proj`（加载后 maxdiff=0.0）。
- **结论**：128px 最佳分布方法。FID 148.2（六方法最低）、KID 0.113±0.007、C2ST 0.916（非检索类最低）；待迁 256 交付线。
- **登记**：`EXPERIMENTS.md` 执行记录 21。
- **指标**：`eval_data/cfm128_text_metrics.json`、`cfm128_text_fundus_metrics.json`。
