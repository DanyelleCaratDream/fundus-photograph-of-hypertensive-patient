# ddpm/ —— 自研扩散训练器与产物地图

> 这个目录里**只有 9 个代码文件**，其余都是训练产物/派生数据。
> Flow Matching（CFM）也复用这里的 `train.py`，入口封装在
> `../../Fundus-FlowMatching/CFM/{train,infer,tools}/`。

## 代码文件（真正的代码）

| 文件 | 作用 | 关键入口 |
|:--|:--|:--|
| **`train.py`** | **主训练器**：FiLM 条件 UNet、ResBlock、TimeEmbedding、GaussianDiffusion、FundusDataset、EMA、LPIPS/颜色正则、温度守护；同时支持 `--objective ddpm` 与 `cfm` | `--dataset_path` `--cond_path` `--objective` |
| **`generate.py`** | 采样/推理：DDPM、DDIM、CFM Euler；条件图加载、颜色校正；`--sampler auto` 按 checkpoint 自动选 | `--checkpoint` `--num_images` |
| `sdedit.py` | DDPM 版 SDEdit 自精修（加噪到 t0 再 DDIM 去噪） | `--checkpoint --t0` |
| `prep_conditions.py` | 从眼底图提取血管骨架（条件输入） | `--dataset_path --output_dir --img_size` |
| `check_progress.py` / `.sh` | 查看训练进度/日志 | — |
| `f1_sr_deliver.py` | Real-ESRGAN x4 超分交付（128→512→256） | `--src` 等 |
| `f2_cfm_sdedit.py` | CFM@128 自精修 | `--checkpoint --t_start` |
| `f3_cfm256_sdedit.py` | CFM@256 自精修 | `--checkpoint --t_start` |
| `deliver_cfm256_s08.py` | CFM@256 交付批次（SDEdit 0.8，分批+续跑） | `--base_dir --out` |

**CFM 的家族入口**（薄封装，调用上面的训练器）：
`Fundus-FlowMatching/CFM/train/train_cfm.py`、`CFM/infer/{sample,sdedit,deliver}_cfm.py`。

## 产物/派生数据（不是代码）

| 目录/文件 | 内容 | 能否重建 |
|:--|:--|:--|
| `results_film_l1lpips/` | A 域最佳 DDPM（CFM 的初始化权重）+ logs | 需重训（保留 final） |
| `results_D3_.../`、`results_D4_.../` | B 域微调/从零扩散实验（final 权重） | 需重训（保留 final） |
| `results_*/logs`、`images` | 训练日志与预览图 | 训练时生成 |
| `conditions/`、`conditions_combined_128/256/` | 派生的血管 mask | `prep_conditions.py` |
| `lesion_weights_256/` | 派生的病灶权重图 | `CFM/tools/make_lesion_weights.py` |
| `judgment_20261018/19/20/` | 判定/对比图 | 采样脚本 + 对比脚本 |
| `sdedit_D3_ema/` | D3 的 SDEdit 输出 | `sdedit.py` |
| `lesion_train.log` | 当前训练的日志（可删） | — |
| `__pycache__/` | Python 缓存 | 可删 |

## 一句话

- **要改训练逻辑** → `train.py`
- **要出图** → `generate.py`（或 CFM 的 `infer/` 封装）
- **要看结果** → `results_*/`、`judgment_*/`
- **`Fundus-FlowMatching/code/` 里只有上游库**（flow_matching / torchcfm），不是我们的代码


## 目录命名（legacy）

本目录沿用 2026 年早期命名：结果目录 `results_<描述>/`、判图目录 `judgment_<日期>/`。
**新实验一律按 `docs/10-management/17-Directory-Standard.md`**（`results/<exp>/` + 每实验 README + `judgment/`），
不再新增 `results_*` / `judgment_*` 平级目录。老目录只加 `README.md` 说明，不改名。


## 判图目录索引（`judgment_<日期>/`，不入 git）

| 目录 | 内容 |
|---|---|
| `judgment_20261018/` | D3/D4 四组裁决期的并排对照 |
| `judgment_20261019/` | D 线后处理、SDEdit 与交付候选 |
| `judgment_20261020/` | F2/F3、b1 线对照、与真实图对比（报告第 7/8 章用图来源） |

判图含真实患者图，已在 `.gitignore` 中排除。
