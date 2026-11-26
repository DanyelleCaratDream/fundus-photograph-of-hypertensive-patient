# 引用便签（refs-notes）

> `.bib` 建库前的暂存区。每条记录：键、完整出处、在我们论文中的角色、引用纪律。
> 建库时按 `literature/README.md` 约定归位（PDF 下载进 `literature/pdf/<generation|classifier|methodology|other>/`，命名 `作者年份-简短标题.pdf`）。

## R1. Deo et al. 2025 ——「通用指标盲区」共识锚点（必引）

- Deo, Y. et al. *Metrics that Matter: Evaluating Generative Models for Medical Images*. arXiv:2505.07175 (2025). 代码: https://github.com/YashDeo-York/GenMed
- **角色**：6.2 的核心引用——证明「FID/KID/MMD 对局部临床相关形态改变不敏感、上游指标排名与下游任务不一致」是**已发表共识**；我们的「FID 相近但出血保留率差 4.5×」是它结论的**新实例**（眼底域 + 受控消融），不是新发现。
- **纪律**：不得写成"我们首次发现"。

## R2. Asokan & Manju 2026 —— LFS（竞争者，划界引用）

- Asokan & Manju. *Lesion-Fidelity-Aware Synthetic Data Augmentation for Diabetic Retinopathy Grading Using Conditional GANs*. IEEE Access (2026). DOI: 10.1109/ACCESS.2026.3690867（GOLD OA）
- **角色**：6.2 划界——他们是 judge–artist–student 架构、以**条件 mask** 为参照、Dice 像素重叠、逐样本筛选分数；我们是**真实病灶**参照、Wasserstein+面积保留比、每模型聚合标尺。
- **纪律（docs/40-writing/12 原文核实）**：① 不说"和 LFS 一样"，不说"首创病灶级指标"；② **他们全文从未提 FID**（只批评 "global realism metrics" 泛称），引用时不可写成"他们批评 FID"；③ 可对话点：Low-LFS paradox（低保真样本反而提升少数类召回）。

## R3. 血管条件生成源头（防"首创"表述）

- Guibas, J.T. et al. *Synthetic Medical Images from Dual Generative Adversarial Networks*. arXiv (2017)——两阶段思想源头，DRIVE 仅 40 对。
- Costa, P. et al. *End-to-End Adversarial Retinal Image Synthesis*. IEEE TMI (2018)——血管树→彩图，614 对。
- **角色**：2. Related Work + 3.1——"血管骨架条件生成眼底图"2017 年就有，我们不做新颖性声称。

## R4. Tiger-Model（老师给的权威范文）

- Dai, F. et al. *Improving AI models for rare thyroid cancer subtype by text guided diffusion models*. Nature Communications (2025). DOI: 10.1038/s41467-025-59478-8. PDF 已在 `literature/pdf/generation/s41467-025-59478-8.pdf`；开源: GitHub `fangdai-dear/Tiger-Model` + HuggingFace `FangDai/Tiger-Model`（Apache 2.0）。
- **角色**：Introduction/Discussion 对照——小样本罕见病类 + 扩散生成 + 全开源发布的发表路线。

## R5. RF-GANs（下游 QWK 增广范式）

- Chen, Y., Long, J. & Guo, J. *RF-GANs: A Method to Synthesize Retinal Fundus Images Based on Generative Adversarial Network*. Computational Intelligence and Neuroscience (2021). DOI: 10.1155/2021/3812865
- **角色**：相关工作 + 4.4——合成图做增广 → 下游 accuracy/QWK 提升的眼底域先例；贡献列表写法（编号①②③）参考。

## R6. Esteban et al. 2017 —— TSTR 原始论文（必引）

- Esteban, C. et al. *Real-valued (Medical) Time Series Generation with Recurrent Conditional GANs*. arXiv:1706.02633 (2017).
- **角色**：4.4/6.3——TSTR/TRTS 协议出处；报告"相对 TRTR 上界基线的下降幅度"为其标准做法。

## R7. Xia et al. 2026 —— 检索增强诊断（罕见类稀缺的另一条路线）

- Xia, W., Du, Y., Lin, J., Wang, M., Shi, D. & Wang, S. *Evo-RAD: Navigating Rare Retinal Disease Diagnosis via Self-Evolving Agentic Retrieval*. **MICCAI 2026**. arXiv:2606.22955. 代码: https://github.com/SDH-Lab/Evo-RAD
- **角色**：2.5 检索增强诊断；6.x 讨论"检索 vs 生成"的干预点差异。**不把检索基线作为本文对照。**
- **方法要点（摘要级）**：冻结 RetiZero；把检索写成马尔可夫决策过程；图策略执行 DELETE / INSERT / TERMINATE；GRPO 训练，奖励强调证据同质性；最终对保留病例多数投票。摘要明确针对 hubness（常见病图像反复成为近邻，检索到"视觉相似但语义错误"的证据）。
- **数字（来自摘要/二次拆解，引用前须核原文）**：论文称优于视网膜基础模型 +21.04%、优于静态检索与参数高效微调 +3.56%；二次拆解给出 Rare-20 46.28% vs 42.72%、Retina-31 65.33% vs 60.41%。摘要未说明百分数是绝对还是相对，正文不直接引用这些数字。
- **纪律**：① 任务（20/31 类罕见病）、数据（Retina Image Bank）、骨干（RetiZero）、指标（Accuracy/F1）均与本文不同，**禁止横向比数字**；② 它改推理时证据集，本文改训练时数据组成，写成互补而非替代；③ 引论文，不引公众号；④ 未读全文前只写摘要级事实，细节标"待核"。

## P0 待读全文（从正文移出的写作待办）

- Deo 2025、Pandey 2025：获取链接已核实（docs/40-writing/12 §六）；下载进 `literature/pdf/generation/` 后更新本文件。正文 2.1/2.3 的相关表述目前只到摘要/二手拆解级。
- 2.2 的 DR-GAN（2022）、StyleGAN 路线（2022）、扩散路线（2024）、RetinaGAN（2023）尚未补作者姓名与完整出处；建 `.bib` 前必须补齐，不得在正文写"待核"。
