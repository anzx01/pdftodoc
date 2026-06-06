#!/usr/bin/env bash
# 预下载 PaddleOCR 模型到项目内 assets/models（PaddleX 缓存目录），
# 之后运行时（recognizer 设同一 PADDLE_PDX_CACHE_HOME）即可断网使用。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

mkdir -p logs assets/models
LOG_FILE="logs/fetch_models_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "${LOG_FILE}") 2>&1

# 模型缓存固定到项目内，与 recognizer.PaddleRecognizer._ensure 保持一致
export PADDLE_PDX_CACHE_HOME="${ROOT_DIR}/assets/models"
# 规避 PaddleOCR 在新版 Python 下 modelscope 的导入 bug
export HUB_DATASET_ENDPOINT="${HUB_DATASET_ENDPOINT:-https://modelscope.cn/api/v1/datasets}"
OCR_LANG="${OCR_LANG:-ch}"
OCR_VERSION="${OCR_VERSION:-PP-OCRv4}"

echo "[fetch_models] 缓存目录: ${PADDLE_PDX_CACHE_HOME}"
echo "[fetch_models] 触发一次初始化以下载 lang=${OCR_LANG}, version=${OCR_VERSION} 的检测/识别模型 ..."

# 初始化即触发 PaddleX 按需下载模型；用一张小白图跑一次 predict 确保全部权重就位
uv run python - "${OCR_LANG}" "${OCR_VERSION}" <<'PY'
import sys
import numpy as np
from paddleocr import PaddleOCR

lang = sys.argv[1]
version = sys.argv[2]
ocr = PaddleOCR(
    lang=lang,
    ocr_version=version,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    text_det_limit_side_len=960,
    text_det_limit_type="max",
    text_recognition_batch_size=4,
    device="cpu",
    cpu_threads=2,
    enable_hpi=False,
    enable_mkldnn=False,
)
ocr.predict(np.full((64, 256, 3), 255, dtype=np.uint8))
print(f"[fetch_models] lang={lang}, version={version} 模型已就绪")
PY

echo "[fetch_models] 完成。模型位于 ${PADDLE_PDX_CACHE_HOME}，日志: ${LOG_FILE}"
