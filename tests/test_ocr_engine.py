"""OCR 链路测试：注入 fake 识别器，对扫描型 PDF 跑端到端，不依赖真实 paddle。

覆盖 renderer（真实 PyMuPDF 渲染）、docx_builder（真实 python-docx）、
ocr_engine（分页/取消/结果聚合）以及 service → OCR 引擎的分派整链路。
"""

from pathlib import Path

import fitz
import numpy as np
from docx import Document

from pdftodoc.core.engines.ocr_engine import OcrEngine
from pdftodoc.core.ocr import OcrPage
from pdftodoc.core.ocr.docx_builder import build_docx
from pdftodoc.core.ocr.renderer import render_page
from pdftodoc.core.service import ConversionService
from pdftodoc.models.enums import PdfType, TaskStatus
from pdftodoc.models.task import ConversionTask


class FakeRecognizer:
    """计数用假识别器：每页返回一行固定文本，不触碰 paddle。"""

    def __init__(self) -> None:
        self.calls = 0

    def recognize(self, image: np.ndarray) -> tuple[str, ...]:
        self.calls += 1
        return (f"第{self.calls}页识别文本",)


def test_render_page_shape(scanned_pdf: Path) -> None:
    doc = fitz.open(scanned_pdf)
    try:
        img = render_page(doc, 0, dpi=100)
    finally:
        doc.close()
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.dtype == np.uint8


def test_build_docx_writes_lines(tmp_path: Path) -> None:
    dst = tmp_path / "b.docx"
    build_docx((OcrPage(0, ("行一", "行二")), OcrPage(1, ())), dst)
    assert dst.exists()
    texts = [p.text for p in Document(str(dst)).paragraphs]
    assert "行一" in texts and "行二" in texts


def test_ocr_engine_end_to_end(scanned_pdf: Path, tmp_path: Path) -> None:
    dst = tmp_path / "out.docx"
    fake = FakeRecognizer()
    result = OcrEngine(recognizer=fake).convert(
        ConversionTask(scanned_pdf, dst), lambda _: None, lambda: False
    )
    assert result.status is TaskStatus.SUCCESS
    assert result.pdf_type is PdfType.SCANNED
    assert dst.exists() and dst.stat().st_size > 0
    assert result.page_count == 2
    assert fake.calls == 2
    assert len(result.pages) == 2
    assert result.pages[0].line_count == 1


def test_ocr_engine_cancel(scanned_pdf: Path, tmp_path: Path) -> None:
    dst = tmp_path / "out.docx"
    fake = FakeRecognizer()
    result = OcrEngine(recognizer=fake).convert(
        ConversionTask(scanned_pdf, dst), lambda _: None, lambda: True
    )
    assert result.status is TaskStatus.CANCELLED
    assert result.output_path is None
    assert fake.calls == 0
    assert not dst.exists()


def test_service_dispatches_scanned_end_to_end(scanned_pdf: Path, tmp_path: Path) -> None:
    """detector 真把扫描件判为 SCANNED，且 service → OcrEngine → DOCX 全链路打通。"""
    dst = tmp_path / "s.docx"
    svc = ConversionService()
    svc._ocr_engine = OcrEngine(recognizer=FakeRecognizer())  # 跳过懒加载，避免拉起 paddle
    result = svc.convert(ConversionTask(scanned_pdf, dst))
    assert result.status is TaskStatus.SUCCESS
    assert result.pdf_type is PdfType.SCANNED
    assert dst.exists() and dst.stat().st_size > 0
