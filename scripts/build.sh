#!/usr/bin/env bash
# PyInstaller 打包为 Windows 可执行（onedir 模式，便于排查依赖与加载离线模型）。
# 产物在 dist/pdftodoc/，连同 assets/（含已下载的 OCR 模型）一并分发。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

mkdir -p logs
LOG_FILE="logs/build_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "${LOG_FILE}") 2>&1

if [[ ! -d "assets/models" || -z "$(ls -A assets/models 2>/dev/null)" ]]; then
    echo "[build] !! assets/models 为空。请先运行 scripts/fetch_models.sh 预下载 OCR 模型，"
    echo "[build]    否则打包产物在断网机器上无法识别扫描件。"
    exit 1
fi

echo "[build] 清理上次产物 ..."
rm -rf build dist

echo "[build] 运行 PyInstaller（onedir，GUI 无控制台）..."
# Windows --add-data 用 ';' 分隔 源;目标；paddle 系列需 --collect-all 收齐数据/动态库
uv run pyinstaller \
    --name pdftodoc \
    --noconfirm \
    --windowed \
    --add-data "assets;assets" \
    --collect-all paddleocr \
    --collect-all paddlex \
    --collect-all paddle \
    main.py

echo "[build] 完成。产物：dist/pdftodoc/pdftodoc.exe（日志: ${LOG_FILE}）"
echo "[build] 提示：目标机需安装 VC++ Redistributable 方可运行。"
