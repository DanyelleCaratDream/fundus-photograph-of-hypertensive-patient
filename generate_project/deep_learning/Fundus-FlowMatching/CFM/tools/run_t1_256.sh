#!/usr/bin/env bash
# T1-256 微调（2026-11-14 老师冻结 B*）
#
#   T1@128 raw 权重 → 256px 继续训：667 轮 × 30 次更新 = 20,010 更新
#   micro-batch 1 + 梯度累积 2（有效 batch 2）；每轮 61 张中 60 张参与、1 张轮换丢弃
#   曝光 40,020 张，与 T1 完全对齐
#
# 用法
#   bash tools/run_t1_256.sh --dry-run   # 只打印
#   bash tools/run_t1_256.sh             # 训练 → 验收 → 生成 32 张
#
# 约束
#   * --resume 必须绝对路径；必须显式 --output_dir
#   * 主结果 raw；每 50 轮存档；不允许中途挑 checkpoint
set -euo pipefail

CFM="D:/AI_Model_Project_for_Fundus_Color_Images/generate_project/deep_learning/Fundus-FlowMatching/CFM"
DL="D:/AI_Model_Project_for_Fundus_Color_Images/generate_project/deep_learning"
SRC_CKPT="$CFM/results/cfm128_hrsevere_t1_ac/models/final_model.pth"
OUT="$CFM/results/cfm256_hrsevere_t1_ac"
T1_CKPT="$OUT/models/final_model.pth"
CONDS="$CFM/data/conditions_hrsevere_61_256"
JUDGE="$CFM/judgment/t1_256"
SEEDS=(42 1042 2042 3042)
PY="${PY:-python}"
# 预览间隔可覆盖：默认 25；显存紧张时用 IMG_INTERVAL=667（只在末轮出图）
IMG_INTERVAL="${IMG_INTERVAL:-25}"

DRY=0
GEN_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --gen-only) GEN_ONLY=1 ;;
    *) echo "未知参数: $arg"; exit 2 ;;
  esac
done

run() {
  echo "+ $*"
  [ "$DRY" = "1" ] || "$@"
}

if [ "$GEN_ONLY" = "0" ]; then
  if [ ! -f "$SRC_CKPT" ]; then
    [ "$DRY" = "1" ] && echo "[WARN] T1 权重不存在: $SRC_CKPT" || { echo "[FAIL] 找不到 T1 权重: $SRC_CKPT"; exit 1; }
  fi
  if [ -e "$OUT" ] && [ "$DRY" = "0" ]; then
    echo "[FAIL] 输出目录已存在: $OUT（重跑请先移走）"; exit 1
  fi
fi
if [ "$GEN_ONLY" = "1" ] && [ ! -f "$T1_CKPT" ]; then
  echo "[FAIL] 找不到 T1-256 权重: $T1_CKPT"; exit 1
fi

# ---------- 1. 训练 ----------
if [ "$GEN_ONLY" = "0" ]; then
  echo "=== [1/3] T1-256 训练：667 轮 × 30 更新 = 20,010 ==="
  run "$PY" "$CFM/train/train_cfm.py" \
    --preset cfm256_t1_ac \
    --resume "$SRC_CKPT" \
    --init_weights_only \
    --epochs 667 \
    --output_dir "$OUT" \
    --image_save_interval "$IMG_INTERVAL"

  # ---------- 2. 验收 ----------
  echo "=== [2/3] 训练验收 ==="
  run "$PY" "$CFM/tools/verify_training.py" \
    --run-dir "$OUT" --expect-epochs 667 --steps-per-epoch 30
fi

# ---------- 3. 生成（4 seed × 8 条件；raw / Euler 50 NFE）----------
echo "=== [3/3] 生成 4 seed × 8 条件 = 32 张 ==="
for s in "${SEEDS[@]}"; do
  run "$PY" "$DL/Fundus-Diffusion/ddpm/generate.py" \
    --checkpoint "$T1_CKPT" \
    --num_images 8 \
    --seed "$s" \
    --sampling_steps 50 \
    --img_size 256 \
    --base_dim 128 \
    --cond_path "$CONDS" \
    --output_dir "$JUDGE/cfm256_hrsevere_t1_ac_raw_seed$s" \
    --grid_size 0 \
    --sampler auto \
    --use_raw
done

echo
echo "完成。下一步：盲评拼图（A/B 随机，key 单独存）与两层指标。"
