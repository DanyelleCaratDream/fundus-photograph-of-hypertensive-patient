# t1_256_contour_diag —— T1-256 轮廓退化诊断（DL-EX-030）

- **登记号**：DL-EX-030（`generate_project/deep_learning/EXPERIMENTS.md`）
- **问题**：DL-EX-029 判「部分成功（血管强、轮廓退）」；进 B 路线前先定位轮廓退化
  是采样端还是模型/数据侧。**不动权重、不重训**。
- **变量**：
  - 像素层：T1-256 原生 vs T1@128 Lanczos→256（N=32 配对，同 seed 同条件）；
    128 网格复核；真实 `fundus/hrsevere_61_sq256` 61 张参照。
  - 后处理：全局 RGB 统计归一（`tools/t1_256_color_correct.py`）。
  - 采样端：同权重 / 同 seed42，仅 `--sampling_steps` = 10 / 100（各 8 张）。
  - 边缘臂：同权重 / 同 seed42，`--img_size` 288 / 320，再中心裁回 256。
  - 色调臂：保色相 gamma 把前景平均亮度校到真实前景均值 0.3755（只提亮不压暗，零 GPU）。
- **结论**：
  - 轮廓退化的可测量主体 = **整体变暗（外圈更明显）** + **边界毛糙/锯齿**；
    不是「比真实图更不圆」（真实径向 CV 0.074 > T1-256 0.057）。
  - **全局 RGB 颜色校正排除**（抬亮黑背景，fov_area 0.744→0.962 为假改善）。
  - **NFE 10/100 排除**（border_lum 无单调趋势，面积/高频不动）。
  - **边缘零填充排除**：288/320 中心裁 256 去掉黑框但不恢复边界亮度（0.263→0.228/0.232）。
  - 全图平均亮度：真实 128/256 均 0.332，T1@128 0.286、T1-256 0.241（−16%）
    → 暗化来自 256 微调本身，不是数据缩放；径向衰减形状两代相同（0.60 vs 0.60）。
  - 色调 v1（全局、γ 无下限）：border_lum 0.269→0.331，但人工 16 对（1–5 刻度）**全平**、
    偏好原始 1 / 平 15，且 1 例边界外被放大成红色 → **v1 不接受**。
  - 色调 v2（mask-aware、γ∈[0.85,1]）：红色背景伪影消除，border_lum 0.269→0.292（效果更弱）；
    **未再评分，仅留档**。色调路线关闭，不作为 256 线修复方案。
- **指标位置**：
  - `CFM/judgment/t1_256/contour_diag.json`（组汇总 + per-image，含真实参照）
  - `CFM/judgment/t1_256/contour_diag_cc.json`（全局颜色校正臂）
  - `CFM/judgment/t1_256/contour_diag_nfe.json`（NFE 臂）
  - `CFM/judgment/t1_256/contour_diag_edge.json`（288/320 边缘臂 + 径向剖面）
  - `CFM/judgment/t1_256/contour_diag_tone.json`（色调校正臂）
- **本目录内容**：`cc_seed*/`、`nfe10_seed42/`、`nfe100_seed42/`、`gen288_seed42/`、
  `gen320_seed42/`、`tone_seed*/`。
- **脚本**：`t1_256_contour_diag.py`、`t1_256_color_correct.py`、`t1_256_edge_test.py`、
  `t1_256_tone_correct.py`（均在 `CFM/tools/`）。
- **状态/日期**：诊断 + 人工小盲评完成，2026-11-14/15。未改权重、未重训；色调路线关闭（v2 留档）。
- **未做**：边界/FOV 条件、低 lr + warm-up 重跑（约 11 h）。
