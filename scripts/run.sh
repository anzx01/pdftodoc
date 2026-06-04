#!/usr/bin/env bash
# 正常启动 GUI（INFO 日志）。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

mkdir -p logs
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
# 规避 PaddleOCR 在 Python 3.13 下 modelscope 的导入 bug
export HUB_DATASET_ENDPOINT="${HUB_DATASET_ENDPOINT:-https://modelscope.cn/api/v1/datasets}"

LOG_FILE="logs/run_$(date +%Y%m%d_%H%M%S).log"
echo "[run] 启动 GUI（日志级别 ${LOG_LEVEL}）..."
uv run python main.py 2>&1 | tee -a "${LOG_FILE}"
