"""文本引擎端到端测试：用真实 pdf2docx 把文本型 PDF 转成 DOCX。"""

from pathlib import Path

import pytest
from docx import Document

from pdftodoc.core.engines import text_engine
from pdftodoc.core.engines.fast_text_engine import FastTextEngine
from pdftodoc.core.engines.text_engine import TextEngine
from pdftodoc.core.service import ConversionService
from pdftodoc.models.enums import PdfType, TaskStatus
from pdftodoc.models.task import ConversionOptions, ConversionTask


def test_text_conversion_end_to_end(text_pdf: Path, tmp_path: Path) -> None:
    dst = tmp_path / "out.docx"
    result = ConversionService().convert(ConversionTask(text_pdf, dst))
    assert result.status is TaskStatus.SUCCESS
    assert result.pdf_type is PdfType.TEXT
    assert dst.exists() and dst.stat().st_size > 0
    assert result.page_count == 2


def test_fast_text_engine_writes_editable_layout_text(text_pdf: Path, tmp_path: Path) -> None:
    dst = tmp_path / "fast.docx"
    result = FastTextEngine().convert(
        ConversionTask(text_pdf, dst),
        lambda _: None,
        lambda: False,
    )

    assert result.status is TaskStatus.SUCCESS
    assert dst.exists() and dst.stat().st_size > 0
    doc = Document(str(dst))
    text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    assert "Hello World" in text
    assert len(doc.inline_shapes) == 0
    assert doc.sections[0].page_width.pt > 0


def test_text_engine_enables_multiprocessing_for_larger_documents(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    class FakeDoc:
        page_count = 12

    class FakeConverter:
        def __init__(self, filename: str) -> None:
            captured["filename"] = filename
            self.fitz_doc = FakeDoc()

        def convert(
            self,
            docx_filename: str | None = None,
            start: int = 0,
            end: int | None = None,
            pages: list[int] | None = None,
            **kwargs: object,
        ) -> None:
            captured.update(kwargs)
            captured["start"] = start
            captured["end"] = end
            captured["pages"] = pages
            Path(str(docx_filename)).write_bytes(b"fake-docx")

        def close(self) -> None:
            captured["closed"] = True

    monkeypatch.setattr(text_engine, "Converter", FakeConverter)
    monkeypatch.setattr(text_engine.os, "cpu_count", lambda: 16)

    dst = tmp_path / "out.docx"
    result = TextEngine().convert(
        ConversionTask(tmp_path / "in.pdf", dst),
        lambda _: None,
        lambda: False,
    )

    assert result.status is TaskStatus.SUCCESS
    assert captured["multi_processing"] is True
    assert captured["cpu_count"] == 8
    assert captured["start"] == 0
    assert captured["end"] is None
    assert captured["closed"] is True


def test_text_engine_keeps_small_documents_single_process(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    class FakeDoc:
        page_count = 3

    class FakeConverter:
        def __init__(self, _filename: str) -> None:
            self.fitz_doc = FakeDoc()

        def convert(self, docx_filename: str | None = None, **kwargs: object) -> None:
            captured.update(kwargs)
            Path(str(docx_filename)).write_bytes(b"fake-docx")

        def close(self) -> None:
            pass

    monkeypatch.setattr(text_engine, "Converter", FakeConverter)

    result = TextEngine().convert(
        ConversionTask(
            tmp_path / "in.pdf",
            tmp_path / "out.docx",
            ConversionOptions(text_multi_process_min_pages=8),
        ),
        lambda _: None,
        lambda: False,
    )

    assert result.status is TaskStatus.SUCCESS
    assert captured["multi_processing"] is False
