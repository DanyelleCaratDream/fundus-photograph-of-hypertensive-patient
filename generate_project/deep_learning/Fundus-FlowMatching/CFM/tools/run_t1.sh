#!/usr/bin/env bash
# T1 迁移实验：A_clean(258) 初始化 vs T0 随机初始化
#
#   T1 = cfm128_hrsevere_pilot 预设 + A_clean 最终 raw 权重 + init_weights_only
#        + 667 轮（与 T0 的 20,010 步对齐）
#
# 用法
#   bash tools/run_t1.sh              # 训练 + 生成 + 验收
#   bash tools/run_t1.sh --dry-run    # 只打印命令
#   bash tools/run_t1.sh --gen-only   # 跳过训练，只生成（训练已跑完时用）
#
# 关键约束（踩过的坑）
#   * --resume 必须绝对路径，否则会静默从 0 训练并覆盖存档
#   * 必须显式 --output_dir，否则 preset 会写进 T0 的 results/cfm128_hrsevere_pilot
#   * init_weights_only 只加载 model_state_dict（raw）；EMA 从加载后的权重重建
set -euo pipefail

CFM="D:/AI_Model_Project_for_Fundus_Color_Images/generate_project/deep_learning/Fundus-FlowMatching/CFM"
DL="D:/AI_Model_Project_for_Fundus_Color_Images/generate_project/deep_learning"
REPO="D:/AI_Model_Project_for_Fundus_Color_Images"

A_CKPT="$CFM/results/a_domain_clean_cfm128/models/final_model.pth"
OUT="$CFM/results/cfm128_hrsevere_t1_ac"
T1_CKPT="$OUT/models/final_model.pth"
CONDS="$CFM/data/conditions_hrsevere_61_128"
JUDGE="$CFM/judgment/t1"
SEEDS=(42 1042 2042 3042)
PY="${PY:-python}"

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

# ---------- 前置检查 ----------
if [ "$GEN_ONLY" = "0" ]; then
  if [ ! -f "$A_CKPT" ]; then
    if [ "$DRY" = "1" ]; then
      echo "[WARN] A_clean 最终权重尚不存在（训练未完成）: $A_CKPT"
    else
      echo "[FAIL] 找不到 A_clean 最终权重: $A_CKPT"; exit 1
    fi
  fi
  if [ -e "$OUT" ] && [ "$DRY" = "0" ]; then
    echo "[FAIL] 输出目录已存在: $OUT"
    echo "       如确认要重跑，先手动移走该目录（避免覆盖历史结果）"
    exit 1
  fi
fi

if [ "$GEN_ONLY" = "1" ] && [ ! -f "$T1_CKPT" ]; then
  echo "[FAIL] 找不到 T1 最终权重: $T1_CKPT"; exit 1
fi

# ---------- 1. 训练 ----------
if [ "$GEN_ONLY" = "0" ]; then
  echo "=== [1/3] T1 训练：667 轮 × 30 步 = 20,010 步 ==="
  run "$PY" "$CFM/train/train_cfm.py" \
    --preset cfm128_hrsevere_pilot \
    --resume "$A_CKPT" \
    --init_weights_only \
    --epochs 667 \
    --output_dir "$OUT"

  # ---------- 2. 验收 ----------
  echo "=== [2/3] 训练验收 ==="
  run "$PY" "$CFM/tools/verify_training.py" \
    --run-dir "$OUT" --expect-epochs 667 --steps-per-epoch 30
fi

# ---------- 3. 生成（与 T0 的 e3 口径完全一致）----------
echo "=== [3/3] 生成 8 条件 × 4 seed = 32 张（raw / Euler 50 NFE）==="
for s in "${SEEDS[@]}"; do
  run "$PY" "$DL/Fundus-Diffusion/ddpm/generate.py" \
    --checkpoint "$T1_CKPT" \
    --num_images 8 \
    --seed "$s" \
    --sampling_steps 50 \
    --img_size 128 \
    --base_dim 128 \
    --cond_path "$CONDS" \
    --output_dir "$JUDGE/cfm128_hrsevere_t1_ac_raw_seed$s" \
    --grid_size 0 \
    --sampler auto \
    --use_raw
done

echo
echo "完成。下一步："
echo "  python tools/pilot_metrics.py --t0 e3 --t1 t1 --out judgment/t1/metrics_t1.json"
echo "  python tools/make_t1_sheet.py --t0 e3 --t1 t1 --out judgment/t1"
