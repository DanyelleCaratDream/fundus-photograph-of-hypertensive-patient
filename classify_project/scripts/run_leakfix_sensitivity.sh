#!/usr/bin/env bash
# 任务4：官方 split 已识别重复组（涉及 test 的 5 组）排除后的敏感性分析
#   数据集：fundus/HRSG_4_758_sq256_dedup14（545/133/66，移除 14 张）
#   用法：bash classify_project/scripts/run_leakfix_sensitivity.sh         # 全部 9 次
#         bash classify_project/scripts/run_leakfix_sensitivity.sh A1      # 只跑某组
set -u
cd "$(dirname "$0")/../.."

export CUBLAS_WORKSPACE_CONFIG=:4096:8

DATA=fundus/HRSG_4_758_sq256_dedup14
OUT=classify_project/results/leakfix_sens_20261117
SEEDS="42 52 62"
MAX_GPU_TEMP="${MAX_GPU_TEMP:-75}"        # 温度护栏（可用环境变量覆盖；0=关闭）
mkdir -p "$OUT"

run() {
  local tag="$1"; shift
  echo "########## ${tag} ##########"
  python -X utf8 classify_project/scripts/train_classifier.py \
    --data "$DATA" --size 256 --seeds $SEEDS --epochs 30 \
    --batch-size 16 --lr 1e-4 --num-workers 0 --quiet \
    --deterministic --max-gpu-temp "$MAX_GPU_TEMP" \
    --dump-predictions "$OUT/predictions" \
    --arm-label "$tag" --out "$OUT/${tag}_20261117.json" "$@"
}

want="${1:-ALL}"
case "$want" in
  ALL|A0) run A0 ;;
esac
case "$want" in
  ALL|A1) run A1 --logit-adjust ;;
esac
case "$want" in
  ALL|A2) run A2 --drc ;;
esac

echo "########## 完成 ##########"
