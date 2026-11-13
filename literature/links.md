# 外部链接收集

> 老师给的、或自己找到但还没下载 PDF 的链接，记在这里。
> 格式建议：`- [主题] 链接 —— 一句话说明为什么有用`

## 老师给的链接

<!-- 在这里往下加 -->
- [Evo-RAD MICCAI 2026 深度解析（CVMed新视界）] https://mp.weixin.qq.com/s/PUEPFEJ5eboFaKe2ybw9XA —— 罕见视网膜病「自进化智能体检索」诊断；全文已存 `EvoRAD-2026-MICCAI-CVMed-analysis.md`
- [Evo-RAD 2026 实现教程（最新医学影像技术）] https://mp.weixin.qq.com/s/J6cp8m58pW-EgtxPF1x0sw —— 同上主题的实现/流程版，含数据下载链接；全文已存 `EvoRAD-2026-implementation-tutorial.md`
微信里的推文：https://mp.weixin.qq.com/s/MKqQUMxFKUebIr7gdbHPag
Code availability
The code and models are available on both GitHub (https://github.
com/fangdai-dear/Tiger-Model.git) and Hugging Face (https://
huggingface.co/FangDai/Tiger-Model). Installation instructions are
provided in both repositories. We have provided the permanent
reference for the version of the code used in this study70. The code is
open-source and released under the Apache License 2.0, which allows
free use, modi cation, and redistribution under its terms. The imple-
mentation is based on multiple publicly available open-source pro-
jects. We have retained all original license information and copyright
notices in the corresponding source les. Speci cally, we acknowledge
the following contributions: Diffusers by HuggingFace (Apache 2.0):
https://github.com/huggingface/diffusersStable Stable Diffusion by
Rombach et al. (Apache 2.0): https://github.com/CompVis/stable-
diffusion. ControlNet (MIT): https://huggingface.co/papers/2302.
05543. Fusion Module by Yimian Dai (MIT): https://github.com/
YimianDai/open-aff.

## 自己找到的

<!-- 在这里往下加 -->
- [分类器-长尾] BPaCo, MICCAI 2024 — https://papers.miccai.org/miccai-2024/paper/2020_paper.pdf ｜ 代码 https://github.com/Davidczy/BPaCo —— PDF 已存 `pdf/classifier/Cai2024-BPaCo.pdf`；只借鉴 logit compensation，完整方法不适合 76 张 severe
- [分类器-序数] AOR-DR, MICCAI 2025 — https://papers.miccai.org/miccai-2025/paper/0874_paper.pdf ｜ 代码 https://github.com/Qinkaiyu/AOR-DR —— PDF 已存 `pdf/classifier/Yu2025-AORDR.pdf`；价值在冻结 RETFound + 序数头，注意论文自报 42% 与表格不符
- [生成增广] ECC-DM, MICCAI 2025 — https://papers.miccai.org/miccai-2025/paper/4449_paper.pdf ｜ 代码 https://github.com/AlanZhang1995/ECC_DM_for_DR —— PDF 已存 `pdf/classifier/Zhang2025-ECCDM.pdf`；语义分筛选的直接先行工作
- [HR 分级] Suman et al., CMPB 2025, 261:108585 — https://doi.org/10.1016/j.cmpb.2025.108585 ｜ PubMed 39862474 —— 付费全文；其 HRSG 是 354 张，不是我们的 HRSG_4_758

### 生成线文献（PDF 原件）

> 笔记在 `generate_project/literature/`；这里只登记原件。

- [生成-小样本 FM] Few-Shot Flow Matching with Stochastic Barycentric Sampling for Image Synthesis — Kulbaka et al. (Imperial College London) — PDF 已存 `pdf/generation/Few-Shot Flow Matching with Stochastic Barycentric Sampling for Image Synthesis.pdf` —— **与本项目最贴**：DR 眼底 few-shot 合成 + 下游 5 级 DR 分级 QWK（N=20/50 提升 0.10→0.20 / 0.29→0.37）；代码 anonymous.4open.science
- [生成-FM-统一框架] Symmetrical Flow Matching: Unified Image Generation, Segmentation, and Classification — Caetano et al., AAAI-26 — 代码 https://github.com/caetas/SymmetricFlow ｜ PDF 已存 `pdf/generation/Symmetrical Flow Matching_ Unified Image Generation, Segmentation, and Classification with Score-Based Generative Models.pdf`
- [生成-TTA] Test-Time Adaptation in Optical Coherence Tomography Using Trajectory-Aligned Time-Independent Flow — arXiv:2606.18876 — PDF 已存 `pdf/generation/Test-Time Adaptation in Optical Coherence Tomography Using Trajectory-Aligned Time-Independent Flow.pdf` —— TTA-Flow；其"去时间条件"在眼底不成立（cfm128_notime）
- [生成-医学扩散增广] Improving AI models for rare thyroid cancer subtype by text guided diffusion models — Nature Communications 2025, DOI 10.1038/s41467-025-59478-8— PDF 已存 `pdf/generation/s41467-025-59478-8.pdf` —— 罕见亚型 text-guided diffusion 增广，叙事与我们 severe 稀有类同构
- [其他-综述] Self-evolving artificial intelligence virtual cells: A closed-loop system from multi-scale modeling to biomedical applications — Hu et al. 2026 — PDF 已存 `pdf/other/hu-et-al-2026-self-evolving-artificial-intelligence-virtual-cells-a-closed-loop-system-from-multi-scale-modeling-to.pdf` —— 虚拟细胞综述，与本项目无直接关系，仅背景

### 数据泄露与重复图像检索（组员第三批调研，2026-11-12）

> 来源文档：`classify_project/literature/surveys/医学影像数据泄露与重复图像检索.docx`（4 篇，全部免费可下）

- [数据泄露-眼科 OCT] Inflation of test accuracy due to data leakage in deep learning-based classification of OCT images — Scientific Data 2022 — https://www.nature.com/articles/s41597-022-01618-6 ｜ PDF 已存 `pdf/methodology/Nature2022-OCT-DataLeakage.pdf` —— 按图像切分使 MCC 高 0.07–0.43、准确率高 5–30pp；Kermany v2 测试集 92% 与训练患者编号重叠
- [数据泄露-MRI] More slices, less truth: effects of different test-set design strategies for MRI classification — **Croatian Medical Journal 2022;63(4):370-378**（调研 docx 误写为 European Radiology Experimental；Crossref 核实）— DOI 10.3325/cmj.2022.63.370 ｜ https://hrcak.srce.hr/306690 ｜ PDF 已存 `pdf/methodology/CMJ2022-MRI-TestSetDesign.pdf` —— 患者级切分错误率约为图像级的 10 倍；**四分类 46.80% vs 2.06%**（最贴合我们的 4 级任务）
- [数据泄露-皮肤 ISIC] Analysis of the ISIC image datasets: Usage, benchmarks and recommendations — Medical Image Analysis 2022 — https://pubmed.ncbi.nlm.nih.gov/34852988/ —— md5/SHA 查完全重复 + 文件名查缩小版；清 14,310 个重复；比较哈希 vs ImageHash/MSE/SSIM/余弦并报告误报
- [数据泄露-皮肤 Derma] Investigating the Quality of DermaMNIST and Fitzpatrick17k Dermatological Image Datasets — Scientific Data 2025 — https://doi.org/10.1038/s41597-025-04382-5 ｜ PDF 已存 `pdf/methodology/SciData2025-DermaMNIST-Quality.pdf` —— fastdup 相似检索 + 人工确认；DermaMNIST 训练-测试 886 图（641 病灶）重叠

### HR 分级（组员第三批，2026-11-12）

> 来源文档：`classify_project/literature/surveys/论文调研.docx`（5 篇）；只有 CMPB'25 是真 KWB 四级，数字均不可比。

- [HR-多骨干] Triple-Stream Deep Feature Selection with Metaheuristic Optimization and ML for Multi-Stage HR Diagnosis — arXiv:2503.01603, 2025 — https://arxiv.org/abs/2503.01603 ｜ PDF 已存 `pdf/classifier/arXiv2025-TripleStream-HR.pdf` —— 14 骨干筛选 + 三路特征 + SVM/RF/XGB + HHO；唯一可借鉴“冻结多骨干 + 传统分类器”，HHO 不适用我们
- [HR-轻量] Mobile-HR: An Ophthalmologic-Based Classification System for Diagnosis of HR Using Optimized MobileNet — **Diagnostics 2023;13(8):1439**（调研 docx 误写 1414）+ DOI 10.3390/diagnostics13081439 ｜ PDF 已存 `pdf/classifier/Diagnostics2023-MobileHR.pdf` —— 任务是 HR 病变诊断、非四级分级，不适用
> 未下载：CMPB'25（付费，DRC=A2，HRSG 354≠我们 758）、JEMT AVR 管线、CMPB MA-DNet（付费）；如需全文找学校图书馆。

> 与本项目的关系：4 篇查的都是**真实数据集内部/跨 split** 重复；我们另做了**生成器训练池 ↔ 下游目标类**的交叉泄漏（A 域 19 张换壳副本），文献空白，可作数据审计部分的差异化点。
