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
# paddle 系列需 --collect-all 收齐数据/动态库
SITE_PACKAGES="$(uv run python -c 'import sysconfig; k="purelib"; print(sysconfig.get_paths()[k])')"
uv run pyinstaller \
    --name pdftodoc \
    --noconfirm \
    --windowed \
    --collect-all paddleocr \
    --collect-all paddlex \
    --collect-all paddle \
    main.py

# 修复1：paddle/libs DLL 路径
echo "[build] 修复 paddle/libs DLL 路径 ..."
PADDLE_INTERNAL="dist/pdftodoc/_internal/paddle"
mkdir -p "${PADDLE_INTERNAL}/libs"
for dll in "${PADDLE_INTERNAL}"/*.dll; do
    [[ -f "$dll" ]] && cp -f "$dll" "${PADDLE_INTERNAL}/libs/"
done

# 修复2：批量复制所有 dist-info 到 _internal/
echo "[build] 复制 dist-info 元数据到 _internal/ ..."
INTERNAL="dist/pdftodoc/_internal"
for d in "${SITE_PACKAGES}"/*.dist-info; do
    [[ -d "$d" ]] && cp -rf "$d" "${INTERNAL}/"
done

# 修复3：复制 assets（含 OCR 模型）
echo "[build] 复制 assets（含 OCR 模型）到产物目录 ..."
cp -rf assets dist/pdftodoc/

echo "[build] 完成。产物：dist/pdftodoc/pdftodoc.exe（日志: ${LOG_FILE}）"
echo "[build] 提示：目标机需安装 VC++ Redistributable 方可运行。"
