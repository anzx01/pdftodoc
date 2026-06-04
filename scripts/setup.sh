#!/usr/bin/env bash
# 环境搭建：创建 .venv、安装依赖、校验 paddle 是否可加载（go/no-go 关口）。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

mkdir -p logs
LOG_FILE="logs/setup_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[setup] 项目根: ${ROOT_DIR}"
echo "[setup] 创建/确认虚拟环境 .venv ..."
uv venv .venv --allow-existing

echo "[setup] 安装依赖（含 dev 组）..."
uv sync --all-groups

echo "[setup] 校验 PaddlePaddle 是否可在当前 Python 加载..."
if ! uv run python -c "import paddle; paddle.utils.run_check()"; then
    echo "[setup] !! paddle 校验失败。若为 Python 3.13 兼容问题，"
    echo "[setup]    请将 .python-version 改为 3.12 后重跑本脚本。"
    exit 1
fi

echo "[setup] 完成。日志: ${LOG_FILE}"
