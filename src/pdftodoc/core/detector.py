"""PDF 类型检测：判断是文本型（走 pdf2docx）还是扫描型（走 OCR）。

策略：用 PyMuPDF 逐页提取文本，统计去空白后的字符数。
- 单页字符数 >= min_page_chars 视为「有文字页」。
- 全文（抽样）平均字符数与有文字页占比共同决定类型。
大文件按配置抽样前/中/后各若干页，避免检测过慢。
"""

import logging
import re

import fitz  # PyMuPDF

from pdftodoc.models.enums import PdfType
from pdftodoc.models.result import DetectionResult
from pdftodoc.models.task import ConversionOptions

logger = logging.getLogger(__name__)

SCANNED_RATIO_MAX = 0.3  # 有文字页占比低于此值且平均字符少时判为扫描型

_WS = re.compile(r"\s+")


def _select_sample(page_count: int, options: ConversionOptions) -> tuple[int, ...]:
    """选择参与统计的页索引。小文件全选，大文件抽前/中/后若干页。"""
    threshold = max(1, options.detect_sample_threshold)
    if page_count <= threshold:
        return tuple(range(page_count))
    n = max(1, options.detect_sample_per_zone)
    mid = page_count // 2
    indices = set(range(n))
    indices.update(range(mid - n // 2, mid - n // 2 + n))
    indices.update(range(page_count - n, page_count))
    return tuple(sorted(i for i in indices if 0 <= i < page_count))


def _classify(avg: float, ratio: float, options: ConversionOptions) -> PdfType:
    """根据平均字符数与有文字页占比分类。"""
    threshold = options.scanned_text_threshold
    if avg >= threshold and ratio >= options.text_page_ratio_min:
        return PdfType.TEXT
    if avg < threshold and ratio < SCANNED_RATIO_MAX:
        return PdfType.SCANNED
    return PdfType.MIXED


def detect(pdf_path: str, options: ConversionOptions) -> DetectionResult:
    """检测 PDF 类型。force_ocr 时直接判为扫描型。"""
    doc = fitz.open(pdf_path)
    try:
        page_count = doc.page_count
        if page_count == 0:
            return DetectionResult(PdfType.UNKNOWN, 0, 0, 0.0, 0.0)

        sample = _select_sample(page_count, options)
        char_counts = [len(_WS.sub("", doc[i].get_text("text"))) for i in sample]
    finally:
        doc.close()

    total = sum(char_counts)
    avg = total / len(char_counts)
    text_pages = sum(1 for c in char_counts if c >= options.min_page_chars)
    ratio = text_pages / len(char_counts)

    pdf_type = PdfType.SCANNED if options.force_ocr else _classify(avg, ratio, options)
    logger.info(
        "检测结果: 类型=%s 总页=%d 抽样=%d 平均字符=%.1f 文字页占比=%.2f",
        pdf_type.value, page_count, len(sample), avg, ratio,
    )
    return DetectionResult(
        pdf_type=pdf_type,
        page_count=page_count,
        total_chars=total,
        avg_chars_per_page=avg,
        text_page_ratio=ratio,
        sampled_pages=sample,
    )
