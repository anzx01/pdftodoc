"""文本引擎端到端测试：用真实 pdf2docx 把文本型 PDF 转成 DOCX。"""

from pathlib import Path

from pdftodoc.core.service import ConversionService
from pdftodoc.models.enums import PdfType, TaskStatus
from pdftodoc.models.task import ConversionTask


def test_text_conversion_end_to_end(text_pdf: Path, tmp_path: Path) -> None:
    dst = tmp_path / "out.docx"
    result = ConversionService().convert(ConversionTask(text_pdf, dst))
    assert result.status is TaskStatus.SUCCESS
    assert result.pdf_type is PdfType.TEXT
    assert dst.exists() and dst.stat().st_size > 0
    assert result.page_count == 2
