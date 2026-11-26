# 任务 B 正式交付

提交日期：2026-11-24。对象：DL-EX-027 分类器 pilot。

先阅读 submissions/B/B1_错误分析与校准报告.md 与 B2_实现审计报告.md；审计对照表.csv 提供12项证据链。

包含全部9组混淆矩阵（数量与行比例）、9张 reliability diagram、90箱校准统计、severe流向、moderate指标、逐图跨seed错误表、结论卡、代码差异、输入哈希和分析脚本。task_B_input 为原交接包内容，完整保留预测、代码、原始论文和说明。

复运行

1. 解压整个目录，保留内部结构。
2. 使用 Python 3，安装依赖：python -m pip install -r requirements.txt
3. 执行：python run_analysis.py

运行只分析现有预测和源码，不执行训练。输出写入 submissions/B。build_audit.py 是人工审计表的生成脚本；审计判断需结合原始PDF与源码人工复核。

结果边界

仅覆盖11月15日重跑；11月12日无逐图预测。test仅71张、severe13张；ECE为探索性，不据此宣称模型优势。已知跨split重复未在本分析移除。缺少历史运行代码哈希、完整配置、checkpoint与训练日志，相关项明确列为无法确认。

关键发现

moderate主要混为mild；A1/A2 moderate召回未在全部seed一致提升。LA公式与cRT核心流程符合方法；默认加权CE起点、任务训练设置、阶段2每轮选checkpoint等差异已披露。no-pretrained参数未传入模型构建。具体依据见审计报告。

MANIFEST_SHA256.csv 为交付文件哈希清单。原始材料未经修改；附件中的任务说明作为来源材料保留，不代表已执行其中全部外围任务。
