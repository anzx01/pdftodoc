"""DOCX 生成：把每页 OCR 文本行写入 Word 文档（版式简化，逐页分页）。"""

import logging
from collections.abc import Sequence
from pathlib import Path

from docx import Document

from pdftodoc.core.ocr import OcrPage

logger = logging.getLogger(__name__)


def build_docx(pages: Sequence[OcrPage], dst: Path) -> None:
    """按页顺序写入文本行，页间插入分页符。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    for idx, page in enumerate(pages):
        for line in page.lines:
            document.add_paragraph(line)
        if not page.lines:
            document.add_paragraph("")  # 空页占位，保持页数对应
        if idx < len(pages) - 1:
            document.add_page_break()  # type: ignore[no-untyped-call]  # python-docx 缺类型标注
    document.save(str(dst))
    logger.info("已生成 DOCX：%s（%d 页）", dst, len(pages))
