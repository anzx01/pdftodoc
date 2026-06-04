#!/usr/bin/env bash
# 运行测试套件（带覆盖率）。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

mkdir -p logs
LOG_FILE="logs/test_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[test] 运行 pytest ..."
uv run pytest tests/ --cov=src/pdftodoc -v

echo "[test] 完成。日志: ${LOG_FILE}"
