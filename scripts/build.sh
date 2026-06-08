#!/usr/bin/env bash
# PyInstaller onefile build. The output is a single GUI executable:
#   dist/pdftodoc.exe
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

mkdir -p logs
LOG_FILE="logs/build_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "${LOG_FILE}") 2>&1

for model in PP-OCRv4_mobile_det PP-OCRv4_mobile_rec; do
    if [[ ! -d "assets/models/official_models/${model}" ]]; then
        echo "[build] Missing OCR model: assets/models/official_models/${model}"
        echo "[build] Run scripts/fetch_models.sh first."
        exit 1
    fi
done

echo "[build] Cleaning previous build outputs ..."
rm -rf build dist

echo "[build] Building onefile GUI executable ..."
if [[ -x ".venv/Scripts/python.exe" ]]; then
    PYTHON=".venv/Scripts/python.exe"
else
    PYTHON="python"
fi
"${PYTHON}" -m PyInstaller --noconfirm --clean pdftodoc.spec

echo "[build] Done: dist/pdftodoc.exe"
echo "[build] Log: ${LOG_FILE}"
