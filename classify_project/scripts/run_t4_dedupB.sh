#!/usr/bin/env bash
# DL-EX-034：任务4 口径 B——更严格去重敏感性（6 次训练）
#   A0 = 真实 527 自然遍历；A1 = 527 + 32 张 128px 合成（池 559，每轮无放回抽 527）
#   预算：30 轮 × 33 步 = 990（较 T3 的 1050 少 5.7%；导师 2026-11-25 批准方案 A）
#   权重：按 527 现算，A0/A1 共用
#   用法：bash classify_project/scripts/run_t4_dedupB.sh        # 全部 6 次
#         bash classify_project/scripts/run_t4_dedupB.sh A1     # 只跑 A1
set -u
cd "$(dirname "$0")/../.."

# 必须在启动 Python（CUDA 初始化）之前生效
export CUBLAS_WORKSPACE_CONFIG=:4096:8

DATA=fundus/HRSG_4_758_sq256_dedup45
OUT=classify_project/results/t4_dedupB_20261125
CW="1.107143,0.983209,1.021318,0.908621"
SEEDS="42 52 62"
DETERMINISTIC="--deterministic"
MAX_GPU_TEMP="${MAX_GPU_TEMP:-75}"
mkdir -p "$OUT"

run() {
  local tag="$1"; shift
  echo "########## ${tag} ##########"
  python -X utf8 classify_project/scripts/train_classifier.py \
    --data "$DATA" --size 256 --seeds $SEEDS --epochs 30 \
    --batch-size 16 --lr 1e-4 --num-workers 0 --quiet \
    --class-weights "$CW" --arm-label "$tag" $DETERMINISTIC \
    --max-gpu-temp "$MAX_GPU_TEMP" \
    --dump-predictions "$OUT/predictions" \
    --out "$OUT/${tag}_20261125.json" "$@"
}

want="${1:-ALL}"
case "$want" in
  ALL|A0) run A0 ;;
esac
case "$want" in
  ALL|A1) run A1 --extra-train-severe-dir fundus/t3_synth_128 --fixed-draws 527 ;;
esac

echo "########## 完成 ##########"
