"""转换服务编排器：检测 PDF 类型 → 分派引擎 → 汇报进度 → 支持取消。

这是 GUI 与底层引擎之间的唯一桥梁。GUI 不直接接触 pdf2docx / paddle。
"""

import dataclasses
import logging
import traceback
from collections.abc import Callable

from pdftodoc.core import detector
from pdftodoc.core.engines import CancelCheck, ProgressCallback
from pdftodoc.core.engines.text_engine import TextEngine
from pdftodoc.models.enums import ConversionStage, PdfType, TaskStatus
from pdftodoc.models.progress import ErrorInfo, ProgressEvent
from pdftodoc.models.result import ConversionResult, DetectionResult
from pdftodoc.models.task import ConversionTask

logger = logging.getLogger(__name__)

# 走文本引擎的类型（MIXED/UNKNOWN 默认按文本处理，保留版式更安全）
_TEXT_TYPES = {PdfType.TEXT, PdfType.MIXED, PdfType.UNKNOWN}

# 检测完成回调（可选，便于 UI 提早显示 PDF 类型）
DetectCallback = Callable[[DetectionResult], None]


def _noop_progress(_: ProgressEvent) -> None:
    pass


def _never_cancelled() -> bool:
    return False


class ConversionService:
    """转换编排器。OCR 引擎按需懒加载，避免无扫描件时引入 paddle 开销。"""

    def __init__(self) -> None:
        self._text_engine = TextEngine()
        self._ocr_engine: object | None = None

    def _get_ocr_engine(self) -> object:
        if self._ocr_engine is None:
            from pdftodoc.core.engines.ocr_engine import OcrEngine
            self._ocr_engine = OcrEngine()
        return self._ocr_engine

    def convert(
        self,
        task: ConversionTask,
        on_progress: ProgressCallback | None = None,
        on_detected: DetectCallback | None = None,
        is_cancelled: CancelCheck | None = None,
    ) -> ConversionResult:
        """执行一次转换。异常向上抛出，由调用方（worker）转为 ErrorInfo。"""
        progress = on_progress or _noop_progress
        cancelled = is_cancelled or _never_cancelled

        progress(ProgressEvent(task.task_id, ConversionStage.DETECTING, 0, 1, "检测 PDF 类型"))
        detection = detector.detect(str(task.src_pdf), task.options)
        if on_detected is not None:
            on_detected(detection)

        if cancelled():
            return self._cancelled(task, detection)

        use_text = (not task.options.force_ocr) and detection.pdf_type in _TEXT_TYPES
        if detection.pdf_type is PdfType.MIXED:
            logger.warning("检测为混合型，按文本型处理；部分页面可能是图片")

        if use_text:
            result = self._text_engine.convert(task, progress, cancelled)
        else:
            engine = self._get_ocr_engine()
            result = engine.convert(task, progress, cancelled)  # type: ignore[attr-defined]

        # 用真实检测类型覆盖引擎默认值（例如 MIXED 应如实反映）
        return dataclasses.replace(result, pdf_type=detection.pdf_type)

    @staticmethod
    def _cancelled(task: ConversionTask, detection: DetectionResult) -> ConversionResult:
        return ConversionResult(
            task_id=task.task_id,
            status=TaskStatus.CANCELLED,
            pdf_type=detection.pdf_type,
            output_path=None,
            page_count=detection.page_count,
            message="已取消",
        )

    @staticmethod
    def to_error_info(
        task: ConversionTask, exc: Exception, stage: ConversionStage = ConversionStage.FAILED
    ) -> ErrorInfo:
        """把异常转为结构化错误信息。"""
        logger.exception("转换失败: %s", exc)
        return ErrorInfo(
            task_id=task.task_id,
            stage=stage,
            exc_type=type(exc).__name__,
            message=str(exc),
            traceback_text="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        )
