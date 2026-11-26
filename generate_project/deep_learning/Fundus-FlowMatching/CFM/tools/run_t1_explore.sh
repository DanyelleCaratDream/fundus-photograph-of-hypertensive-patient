#!/usr/bin/env bash
# T1 推理侧探索（2026-11-13）：同权重下 raw/EMA × NFE 50/100
#
#   目的：先判断 T1 的遗留不足来自采样还是模型表征，不训练、不换权重。
#   raw×50 直接复用 judgment/t1/cfm128_hrsevere_t1_ac_raw_seed{S}（主结果），
#   本脚本只生成其余三格：EMA×50、raw×100、EMA×100。
#
# 用法
#   bash tools/run_t1_explore.sh --dry-run   # 只打印
#   bash tools/run_t1_explore.sh             # 生成 3 格 × 2 seed × 8 张 = 48 张
#
# 注意
#   * 不加 --use_raw 即用 EMA 权重（generate.py 默认行为）
#   * 探索性结果，不替换预注册主结果（raw / 50 NFE）
set -euo pipefail

CFM="D:/AI_Model_Project_for_Fundus_Color_Images/generate_project/deep_learning/Fundus-FlowMatching/CFM"
DL="D:/AI_Model_Project_for_Fundus_Color_Images/generate_project/deep_learning"
CKPT="$CFM/results/cfm128_hrsevere_t1_ac/models/final_model.pth"
CONDS="$CFM/data/conditions_hrsevere_61_128"
OUT="$CFM/judgment/t1_explore"
SEEDS=(42 1042)
PY="${PY:-python}"

DRY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    *) echo "未知参数: $arg"; exit 2 ;;
  esac
done

run() {
  echo "+ $*"
  [ "$DRY" = "1" ] || "$@"
}

[ -f "$CKPT" ] || { [ "$DRY" = "1" ] || { echo "[FAIL] 找不到 T1 权重: $CKPT"; exit 1; }; }
[ -d "$CONDS" ] || { echo "[FAIL] 找不到条件目录: $CONDS"; exit 1; }

gen() {
  local label="$1" seed="$2" steps="$3" raw="$4"
  local dest="$OUT/${label}_seed${seed}"
  if [ -e "$dest" ] && [ "$DRY" = "0" ]; then
    echo "[FAIL] 输出目录已存在: $dest（如要重跑先移走）"; exit 1
  fi
  local extra=()
  [ "$raw" = "1" ] && extra+=(--use_raw)
  run "$PY" "$DL/Fundus-Diffusion/ddpm/generate.py" \
    --checkpoint "$CKPT" \
    --num_images 8 \
    --seed "$seed" \
    --sampling_steps "$steps" \
    --img_size 128 \
    --base_dim 128 \
    --cond_path "$CONDS" \
    --output_dir "$dest" \
    --grid_size 0 \
    --sampler auto \
    "${extra[@]}"
}

for s in "${SEEDS[@]}"; do
  gen ema50 "$s" 50 0
  gen raw100 "$s" 100 1
  gen ema100 "$s" 100 0
done

echo
echo "完成。raw×50 复用 judgment/t1/cfm128_hrsevere_t1_ac_raw_seed{S}/singles。"
