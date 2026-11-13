# 进度日志（append-only）

> **本文件不参与会话启动加载**。只在需要追溯“什么时候做过什么”时打开。
> 规则：一条里程碑一行；不写 epoch/loss/临时路径等易变事实；细节指向 git commit、EXPERIMENTS、审计报告。
> 当前状态永远看 `PROJECT_STATE.md`。

| 日期 | 里程碑 | 结论 / 决策 | 证据 |
|---|---|---|---|
| 2026-11-11 | 30k 检查点扫描 | 20k→30k 震荡非单调；20,010 细节峰、28,500 几何峰 | EXPERIMENTS 记录 25 |
| 2026-11-11 | 导师裁决 T0/T1 方案 | 重训干净 A 域 CFM；T0 复用 667 轮权重；不手改权重 | DL-EX-026 预注册 |
| 2026-11-11 | T0/T1 开跑前核对 | A 域 330 张@128；发现旧权重增强错位、DDPM→CFM 跨目标两缺陷 | `audit/a_domain_20261111/td01_precheck_20261111.md` |
| 2026-11-11 | A 域数据审计与 A_clean 冻结 | 330→299→258；排除规则 20(md5)+19(跨池)+2(池内)=41；61 目标域 19 张有 A 域同图副本 | DL-EX-026；`audit/a_domain_20261111/a_domain_audit_20261111.md` |
| 2026-11-11 | T0 五项核对通过 | 随机初始化 / 61 名单匹配 / 667×30=20,010 / 配置与 T1 一致 / raw 为主 | `cfm128_hrsevere_pilot/logs/` |
| 2026-11-11 | train.py 升级 | 新增 `--init_weights_only` 与显式 `global_step` | 代码 + 冒烟记录 |
| 2026-11-11 | train_cfm 新增预设 | `a_domain_clean_cfm128`（258 张 / batch5 / 780 轮） | `train/train_cfm.py` |
| 2026-11-11 | 导师第二轮批准 + 阶段1冻结收尾 | 哈希入档；258 对重建复核 257/258=1.0000（306 例外已披露） | `fundus/a_domain_clean_frozen_hashes.json` |
| 2026-11-11 | DL-EX-026 登记 | 审计数字 + 预注册配置 + 验收清单入册 | EXPERIMENTS DL-EX-026 |
| 2026-11-11 | 深度清理两轮 | 磁盘 52G→~21G；敏感扫描零风险；gitignore 补 results 中间产物 | commit `c20dcc1`；`_archive/` |
| 2026-11-11 | REPORT_DL v1 增量更新 | 新增 §2.11、§5.13.5、第 7 章；3 处旧结论加更正标注 | `research-report/REPORT_DL.docx` |
| 2026-11-11 | REPORT_DL v2 三轮更新 | 论文向重写 + §1.4 审计 + 第 8 章后期实验 + 5 张竖版图 | `research-report/REPORT_DL_v2.docx` |
| 2026-11-11 | 教师汇报材料 | 消息稿 + `REPORT_DL_后续.docx`；核实无需补正文 | `research-report/汇报_进度_20261111.md` |
| 2026-11-11 | commit c20dcc1 双推 | A 仓库 GitHub/Gitee 同步 | git log |
| 2026-11-12 | 组员调研两批评估 | 旧 5 篇 MICCAI + 新 4 篇（BPaCo/AOR-DR/ECC-DM/CMPB）；数字不可照抄 | `memory/classifier-survey-2` |
| 2026-11-12 | 分类器 DL-EX-027 预注册 | HR 4 级 6 arms，主指标 QWK，MCID 0.02 | `classify_project/PILOT_PREREG_20261112.md` |
| 2026-11-12 | A1/A2 代码完成 | logit adjustment / DRC 实现，6 项自检通过 | `classify_project/scripts/test_pilot_arms.py` |
| 2026-11-12 | 分类器训练数据改 sq256 | 758 张预缩 256；v0.3.4 只作源 | `fundus/HRSG_4_758_sq256/` |
| 2026-11-12 | OCT 归档 + commit a5b4513 双推 | OCT 移 D:\tmp；分类器代码入库 | git log |
| 2026-11-12 | 目录重构 B 档 | 单一入口/地图、统一 experiment schema、audit 合并、休眠臂归档 | commit `45183ee`；`docs/10-management/17-Directory-Standard.md` |
| 2026-11-13 | 文献整理 | PDF 按线分目录；各项目 literature；4 份组员调研归位 | commit `1f20671` |
| 2026-11-13 | docs 架构重构 | docs/ 分 10-management/20-research/30-evaluation/40-writing | commit `a692dce` |
| 2026-11-13 | 冷启动修复 | README 刷新、18 处死链清理、过期横幅、MAP 冷启动速查 | commit `ae50b09` |
| 2026-11-13 | paper 文本恢复 | 从 v1 docx 重新提取 `REPORT_DL_text.txt`；引用改节号 | commit `c2fac75` |
| 2026-11-13 | 记忆维护机制 | 历史下沉到本文件；入口预算；`tools/check_docs.py` | 本文件 + docs/18 |

## 追加规则

- 只在 `/handoff` 触发下沉、或里程碑完成时追加；
- 一行写完“日期 / 里程碑 / 结论 / 证据”，不写子步骤；
- 证据优先用 commit hash、DL-EX 编号、报告文件名；
- 不写会快速过期的数字（epoch、loss、临时路径）。
