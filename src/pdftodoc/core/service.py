"""转换服务编排器：检测 PDF 类型 → 分派引擎 → 汇报进度 → 支持取消。

这是 GUI 与底层引擎之间的唯一桥梁。GUI 不直接接触 pdf2docx / paddle。
"""

import dataclasses
import logging
import threading
import traceback
from collections.abc import Callable
from typing import Protocol

from pdftodoc.core.engines import CancelCheck, ProgressCallback
from pdftodoc.models.enums import ConversionStage, PdfType, TaskStatus
from pdftodoc.models.progress import ErrorInfo, ProgressEvent
from pdftodoc.models.result import ConversionResult, DetectionResult
from pdftodoc.models.task import ConversionOptions, ConversionTask

logger = logging.getLogger(__name__)

# 走文本引擎的类型（MIXED/UNKNOWN 默认按文本处理，保留版式更安全）
_TEXT_TYPES = {PdfType.TEXT, PdfType.MIXED, PdfType.UNKNOWN}

# 检测完成回调（可选，便于 UI 提早显示 PDF 类型）
DetectCallback = Callable[[DetectionResult], None]


class _ConversionEngine(Protocol):
    def convert(
        self,
        task: ConversionTask,
        on_progress: ProgressCallback,
        is_cancelled: CancelCheck,
    ) -> ConversionResult:
        ...


def _noop_progress(_: ProgressEvent) -> None:
    pass


def _never_cancelled() -> bool:
    return False


class ConversionService:
    """转换编排器。OCR 引擎按需懒加载，避免无扫描件时引入 paddle 开销。"""

    def __init__(self) -> None:
        self._text_engine: _ConversionEngine | None = None
        self._fast_text_engine: _ConversionEngine | None = None
        self._precise_text_engine: _ConversionEngine | None = None
        self._ocr_engine: _ConversionEngine | None = None
        self._overlay_engine: _ConversionEngine | None = None
        self._text_lock = threading.Lock()
        self._ocr_lock = threading.RLock()

    def _get_overlay_engine(self) -> _ConversionEngine:
        with self._text_lock:
            if self._overlay_engine is None:
                from pdftodoc.core.engines.overlay_engine import OverlayEngine

                self._overlay_engine = OverlayEngine()
            return self._overlay_engine

    def _get_text_engine(self, *, fast: bool) -> _ConversionEngine:
        with self._text_lock:
            if self._text_engine is not None:
                return self._text_engine
            if fast:
                if self._fast_text_engine is None:
                    from pdftodoc.core.engines.fast_text_engine import FastTextEngine

                    self._fast_text_engine = FastTextEngine()
                return self._fast_text_engine
            if self._precise_text_engine is None:
                from pdftodoc.core.engines.text_engine import TextEngine

                self._precise_text_engine = TextEngine()
            return self._precise_text_engine

    def _get_ocr_engine(self) -> _ConversionEngine:
        with self._ocr_lock:
            if self._ocr_engine is None:
                from pdftodoc.core.engines.ocr_engine import OcrEngine

                self._ocr_engine = OcrEngine()
            return self._ocr_engine

    def prewarm_ocr(self, options: ConversionOptions | None = None) -> None:
        """Load and run OCR once in the background so first editable scan conversion is faster."""
        with self._ocr_lock:
            engine = self._get_ocr_engine()
            warm_up = getattr(engine, "warm_up", None)
            if callable(warm_up):
                warm_up(options or ConversionOptions())

    @staticmethod
    def _detect(task: ConversionTask) -> DetectionResult:
        from pdftodoc.core import detector

        return detector.detect(str(task.src_pdf), task.options)

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
        detection = self._detect(task)
        if on_detected is not None:
            on_detected(detection)

        if cancelled():
            return self._cancelled(task, detection)

        use_text = (not task.options.force_ocr) and detection.pdf_type in _TEXT_TYPES
        if detection.pdf_type is PdfType.MIXED:
            logger.warning("检测为混合型，按文本型处理；部分页面可能是图片")

        if use_text:
            if detection.has_embedded_images:
                # 含嵌入图片时用 Overlay 引擎：图片精确锚定，文字用浮动文本框对齐原坐标
                logger.info("检测到嵌入图片，使用 Overlay 引擎精确还原图文布局")
                result = self._get_overlay_engine().convert(task, progress, cancelled)
            else:
                fast_text = task.options.text_fast_layout and detection.pdf_type is PdfType.TEXT
                result = self._get_text_engine(fast=fast_text).convert(task, progress, cancelled)
        else:
            with self._ocr_lock:
                result = self._get_ocr_engine().convert(task, progress, cancelled)

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
