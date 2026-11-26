# a_domain_clean_cfm128 — A_clean(258) 从零预训练（T1 起点）

- **问题**：清洗后的 A 域能否作为 T1 迁移实验的起点权重（替代有泄漏的旧 A 域权重）。
- **变量**：数据 = `fundus/a_domain_clean`（258 张，冻结定单）；128px / bd128 / batch5 / 780 轮（39,780 步）/ seed42 / L1+LPIPS+color。
- **状态**：🔵 训练中（2026-11-13 预计完成）；完成后按 DL-EX-026 验收清单核对，再跑 T1。
- **登记**：`EXPERIMENTS.md` DL-EX-026。
- **指标**：暂无。完成后落 `eval_data/a_domain_clean_cfm128_*.json`。
