"""检测器测试：文本型 / 扫描型 / 强制 OCR。"""

from pathlib import Path

from pdftodoc.core import detector
from pdftodoc.models.enums import PdfType
from pdftodoc.models.task import ConversionOptions


def test_detect_text(text_pdf: Path) -> None:
    result = detector.detect(str(text_pdf), ConversionOptions())
    assert result.pdf_type is PdfType.TEXT
    assert result.page_count == 2
    assert result.avg_chars_per_page >= 50
    assert result.text_page_ratio == 1.0


def test_detect_scanned(scanned_pdf: Path) -> None:
    result = detector.detect(str(scanned_pdf), ConversionOptions())
    assert result.pdf_type is PdfType.SCANNED
    assert result.avg_chars_per_page < 50


def test_force_ocr_overrides_text(text_pdf: Path) -> None:
    result = detector.detect(str(text_pdf), ConversionOptions(force_ocr=True))
    assert result.pdf_type is PdfType.SCANNED


def test_large_pdf_detection_samples_front_middle_and_back() -> None:
    options = ConversionOptions(detect_sample_threshold=16, detect_sample_per_zone=3)
    assert detector._select_sample(40, options) == (0, 1, 2, 19, 20, 21, 37, 38, 39)
