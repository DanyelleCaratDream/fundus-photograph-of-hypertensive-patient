# cfm128_hrsevere_pilot — 61 张纯 HR severe 从零试点

- **问题**：仅 61 张冻结 severe、从零，能否训出可用生成器；检查点质量如何随步数变化。
- **变量**：61 张 / 128px / bd128 / batch2 / L1+LPIPS / 同步增强 / lr 1e-4 / seed42。
- **结论**：320 轮试点失败（纹理噪点、结构崩）；续训到 **20,010 步出现结构性突破**（细节峰），28,500 几何峰，30,000 回退 → 20k–30k 是震荡区间。**T0 = `models/checkpoint_epoch_000667.pth`（20,010 步）**。
- **登记**：`EXPERIMENTS.md` 执行记录 22；`PROJECT_STATE.md` §3。
- **指标**：`eval_data/cfm128_hrsevere_pilot_*`（E2/E3/E4 与扫描图在 `CFM/judgment/e2,e3,e4,scan30k`）。
