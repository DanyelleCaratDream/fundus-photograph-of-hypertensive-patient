# PROJECT_STATE — 当前工作交接

> 用法：会话结束说 `/handoff` 更新本文件；新会话第一句“读 PROJECT_STATE.md 和 CLAUDE.md”。
> 只记“现在在哪、下一步、已确认的规则”，**不记流水账**。
> 历史里程碑 → `docs/10-management/19-Progress-Log.md`（不参与启动加载）。
>
> **最后更新：2026-11-13 12:05**

## 1. 当前目标（一句话）
**A_clean(258) 780 轮 CFM 预训练收尾 → 跑 T1**（A_clean raw 初始化 vs T0 随机初始化，同配置同协议）；T1 脚本已就绪，训练完成即可一键执行。

## 2. 当前进度

- [ ] **A_clean 训练中**：`--preset a_domain_clean_cfm128`，780 轮 × 51 步 = 39,780 步。
  - 11-13 12:04 实测 **Epoch 693 / step 20,043**；每轮 210–230s，剩 87 轮 ≈ 5.5h，**预计 17:30 前后完成**（以 log 为准）。
  - 11-12 03:28 曾中断于 Epoch 341，已从 `checkpoint_epoch_000300.pth` 续训；每 50 轮存档。
  - 进度看 `CFM/results/a_domain_clean_cfm128/logs/training.log`；后台 UI 可能误标 stopped，**以日志为准**。
  - 变慢根因：SW Thermal Slowdown（驱动软件热降频）。
- [x] **T1 材料全部就绪**（11-13）：
  - `CFM/T1_PROTOCOL.md`（预注册设计 + 验收清单 + 五维评分表）
  - `CFM/tools/run_t1.sh`（训练 667 轮 → 验收 → 生成 32 张）
  - `CFM/tools/verify_training.py`（五项验收，A_clean/T1 通用）
  - `CFM/tools/pilot_metrics.py`、`CFM/tools/make_t1_sheet.py`
- [x] 代码/配置：`--init_weights_only` + 显式 `global_step`；预设 `a_domain_clean_cfm128`；冻结名单 `fundus/a_domain_clean_frozen.json`（258）。
- [x] 已登记：DL-EX-026（A_clean/T0-T1）、DL-EX-027（分类器 pilot）。
- [x] 分类器准备：A1/A2 已实现并过 6 项自检；数据口径 `fundus/HRSG_4_758_sq256`。
- [x] 教师汇报已发送（11-13，`汇报_进度_20261111.md` + `REPORT_DL_后续.docx`）。
- [x] 仓库清理（11-13）：A 重建 27.7MB 并换 Gitee 新库；B 公开库重建为单提交孤儿快照。
- [x] `docs/` 四分类 + 冷启动修复；文献按线整理；`.claude/` 整目录不入库。

**最近里程碑**：11-13 T1 脚本与验收清单（`a22d8ec`）｜11-13 A/B 仓库重建与历史清理（`a22d8ec`、`0ac51f9`）｜11-13 docs 四分类 + 冷启动修复（`a692dce`、`ae50b09`）。
更早历史见 `docs/10-management/19-Progress-Log.md`。

## 3. 已确认的事实（规则 / 教训，不要重复查证）

- **T0 = `CFM/results/cfm128_hrsevere_pilot/models/checkpoint_epoch_000667.pth`**（667×30=20,010 步）；`final_model.pth`=30,000（诊断点），`checkpoint_epoch_000950.pth`=28,500（探索候选）。
- **T0 生成图已有，直接复用**：`CFM/judgment/e3/cfm128_hrsevere_20000_raw_seed{42,1042,2042,3042}/singles/`（各 8 张，raw / Euler 50 NFE）。
- **`--init_weights_only` 只加载 `model_state_dict`（raw）**，EMA 从加载后权重重建；T1 用 raw 初始化是作者 11-13 确认的口径。
- **T1 必须显式 `--output_dir`**，否则 preset 会写进 T0 的 `results/cfm128_hrsevere_pilot`；`--resume` 必须绝对路径。
- **续训硬坑**：`global_step` 不随 resume 恢复，最终 ckpt 约 (780−300)×51=24,480，总步数按 `epoch×51` 核算。
- **A 域旧权重（results_film_l1lpips）三重缺陷**：增强错位、DDPM 目标非 CFM、池内含 19 张目标域同图副本 → 废弃。
- **20k→30k 震荡**：20,010 细节峰、28,500 几何峰；loss 平台 ≠ 质量平台（EXPERIMENTS 记录 25）。
- **评价五维分开**：整体外观 / 血管细节 / 视盘结构 / 伪影 / 多样性，不用单一综合分。
- **指标脚本已重写**：`D:\tmp\run_e3_20k.sh` 与 `D:\tmp\pilot_metrics.py` **已不存在**；新 `tools/pilot_metrics.py` 绝对值与 E2/E3 旧记录**不同源，只能 T0/T1 内部对比**。
- **分类器数据口径**：只用 `HRSG_4_758_sq256`（758，split 与原始一致）；`v0.3.4` 只作源；32 对跨 split 重复只披露。
- **分类器 pilot 代码状态**：A1/A2 已实现；A3–A5 未写，卡在 RETFound/ViT 权重下载。
- **热降频**：SW Thermal Slowdown，物理降温优先，必要时加大 `cool_sleep`。
- **git 规矩**：每次提交推 A 的 GitHub + Gitee（私有自查）；B 为公开清理版。
  - A 的 Gitee 已换新库 `yandicaizhaoxiangmu2zicha`（旧库已删，配额回收）；GitHub A 名称不变。
  - **公开口径**：真实+生成的合并图可公开，**单幅真实患者图不上传**；29 张图已逐张核过，无单幅真图。
  - **B = 单提交孤儿快照 `0ac51f9`**（27.7MB / 390 文件），历史里无 `.claude`、无 docx、无预览图；A 私有库历史仍含 `handoff.md`（无害，未重写）。
  - `.claude/` 整目录不入库（11-13 作者定）；settings/记忆/命令全在本地。
  - 旧历史备份：`D:/tmp/cleanup_A_20261113/fundus_A_backup_20261113.bundle`（659MB）。
- **数字/审计细节不复制**：审计 → `research-report/audit/README.md` + DL-EX-026；报告结构 → `research-report/README.md`；分类器调研 → `classify_project/literature/README.md`；实验数字 → `EXPERIMENTS.md`。

## 4. 下一步（按顺序）

1. 监控 A_clean 训练到 780 轮；完成即跑验收：
   `python tools/verify_training.py --run-dir results/a_domain_clean_cfm128 --expect-epochs 780 --steps-per-epoch 51`
2. 验收通过后跑 T1：`bash tools/run_t1.sh`（训练 667 轮 + 验收 + 生成 32 张）；
   再 `python tools/pilot_metrics.py` + `python tools/make_t1_sheet.py`，五维分开评；结果补记 DL-EX-026。
3. 分类器 pilot：GPU 空闲后跑 A0–A2（`--data fundus/HRSG_4_758_sq256`，参考 `PILOT_PREREG_20261112.md`）；A3–A5 待权重。
4. `docs/20-research/15` 口径更正（330 / 299 / 258）待导师最后确认。

## 5. 会话关键路径

- 东西在哪：`PROJECT_MAP.md`（冷启动 7 问速查）；规则：`docs/10-management/17` / `18`。
- 审计证据：`research-report/audit/README.md`（A 域主文档 + 导师答复包）。
- 冻结名单：`fundus/a_domain_clean_frozen.json`（258）；`fundus/hrsevere_61_frozen.json`（61）。
- T1 全套：`CFM/T1_PROTOCOL.md` + `CFM/tools/{run_t1.sh,verify_training.py,pilot_metrics.py,make_t1_sheet.py}`。
- T0/T1 权重：`CFM/results/cfm128_hrsevere_pilot/`、`CFM/results/a_domain_clean_cfm128/`。
- 分类器：`classify_project/PILOT_PREREG_20261112.md`；自检 `classify_project/scripts/test_pilot_arms.py`。
- ⚠️ `D:\tmp\torch_ckpt_backup\` 为 LPIPS 权重备份；`D:\tmp\archive_OCT_20261112\OCT` 为 TTA-Flow OCT 复现归档（28MB，作者自行处理）。

## 6. 待确认 / 我的疑问

- `docs/20-research/15` 更正口径待导师确认。
- 分类器 4 级与 KW 分级的对应关系待老师。
- val 用途（现有协议用 val 选 epoch）与 test severe 13 张的 CI 写法待老师确认。
- RETFound 权重下载通道（直连 000；hf-mirror 403）需换 ModelScope 或确认仓库名。
- 最终验收的 `global_step` 口径（ckpt 内约 24,480）是否可接受。
