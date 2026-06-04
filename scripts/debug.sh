#!/usr/bin/env bash
# 调试启动 GUI（DEBUG 日志）。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

mkdir -p logs
export LOG_LEVEL=DEBUG
export HUB_DATASET_ENDPOINT="${HUB_DATASET_ENDPOINT:-https://modelscope.cn/api/v1/datasets}"

LOG_FILE="logs/debug_$(date +%Y%m%d_%H%M%S).log"
echo "[debug] 启动 GUI（DEBUG）..."
uv run python main.py 2>&1 | tee -a "${LOG_FILE}"
