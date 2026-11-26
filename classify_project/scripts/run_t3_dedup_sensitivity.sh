#!/usr/bin/env bash
# DL-EX-032 专属去重敏感性：冻结去重 split（545/133/66）上重跑 A0 与 A1(128)，各 3 seed
#   用法：bash classify_project/scripts/run_t3_dedup_sensitivity.sh          # 6 次
#         bash classify_project/scripts/run_t3_dedup_sensitivity.sh A1       # 只跑 A1
set -u
cd "$(dirname "$0")/../.."

export CUBLAS_WORKSPACE_CONFIG=:4096:8

DATA=fundus/HRSG_4_758_sq256_dedup14
OUT=classify_project/results/t3_dedup_sens_20261118
# 由去重 train（120/138/137/150，N=545）现算并冻结，A0/A1 共用
CW="1.13541667,0.98731884,0.99452555,0.90833333"
SEEDS="42 52 62"
MAX_GPU_TEMP="${MAX_GPU_TEMP:-75}"
mkdir -p "$OUT"

run() {
  local tag="$1"; shift
  echo "########## ${tag} ##########"
  python -X utf8 classify_project/scripts/train_classifier.py \
    --data "$DATA" --size 256 --seeds $SEEDS --epochs 30 \
    --batch-size 16 --lr 1e-4 --num-workers 0 --quiet \
    --class-weights "$CW" --arm-label "$tag" \
    --deterministic --max-gpu-temp "$MAX_GPU_TEMP" \
    --dump-predictions "$OUT/predictions" \
    --out "$OUT/${tag}_20261118.json" "$@"
}

want="${1:-ALL}"
case "$want" in
  ALL|A0) run A0 ;;
esac
case "$want" in
  ALL|A1) run A1 --extra-train-severe-dir fundus/t3_synth_128 --fixed-draws 552 ;;
esac

echo "########## 完成 ##########"
