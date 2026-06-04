"""服务编排测试：用 fake 引擎验证分派逻辑与取消，不触碰真实 pdf2docx/paddle。"""

from pathlib import Path

import pytest

from pdftodoc.core import detector
from pdftodoc.core.engines import CancelCheck, ProgressCallback
from pdftodoc.core.service import ConversionService
from pdftodoc.models.enums import PdfType, TaskStatus
from pdftodoc.models.result import ConversionResult, DetectionResult
from pdftodoc.models.task import ConversionTask


class FakeEngine:
    """记录是否被调用的假引擎。"""

    def __init__(self, name: str) -> None:
        self.name = name
        self.called = False

    def convert(
        self, task: ConversionTask, on_progress: ProgressCallback, is_cancelled: CancelCheck
    ) -> ConversionResult:
        self.called = True
        return ConversionResult(
            task_id=task.task_id,
            status=TaskStatus.SUCCESS,
            pdf_type=PdfType.TEXT,
            output_path=task.dst_docx,
            page_count=1,
            message=self.name,
        )


def _patch_detect(monkeypatch: pytest.MonkeyPatch, pdf_type: PdfType) -> None:
    def fake_detect(path: str, options: object) -> DetectionResult:
        return DetectionResult(pdf_type, 1, 100, 100.0, 1.0)

    monkeypatch.setattr(detector, "detect", fake_detect)


def _make_service() -> tuple[ConversionService, FakeEngine, FakeEngine]:
    svc = ConversionService()
    text_fake, ocr_fake = FakeEngine("text"), FakeEngine("ocr")
    svc._text_engine = text_fake  # type: ignore[assignment]
    svc._ocr_engine = ocr_fake    # 预置以跳过懒加载
    return svc, text_fake, ocr_fake


def _task(tmp_path: Path) -> ConversionTask:
    return ConversionTask(tmp_path / "a.pdf", tmp_path / "a.docx")


def test_dispatch_text(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_detect(monkeypatch, PdfType.TEXT)
    svc, text_fake, ocr_fake = _make_service()
    result = svc.convert(_task(tmp_path))
    assert text_fake.called and not ocr_fake.called
    assert result.pdf_type is PdfType.TEXT


def test_dispatch_scanned(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_detect(monkeypatch, PdfType.SCANNED)
    svc, text_fake, ocr_fake = _make_service()
    result = svc.convert(_task(tmp_path))
    assert ocr_fake.called and not text_fake.called
    assert result.pdf_type is PdfType.SCANNED


def test_mixed_uses_text_engine(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_detect(monkeypatch, PdfType.MIXED)
    svc, text_fake, ocr_fake = _make_service()
    result = svc.convert(_task(tmp_path))
    assert text_fake.called and not ocr_fake.called
    assert result.pdf_type is PdfType.MIXED  # 如实反映检测类型


def test_cancel_before_convert(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_detect(monkeypatch, PdfType.TEXT)
    svc, text_fake, _ = _make_service()
    result = svc.convert(_task(tmp_path), is_cancelled=lambda: True)
    assert result.status is TaskStatus.CANCELLED
    assert not text_fake.called
