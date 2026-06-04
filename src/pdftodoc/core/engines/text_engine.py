"""文本型引擎：用 pdf2docx 转换，保留版式。

pdf2docx 的 Converter.convert 不支持逐页中断与细粒度进度回调，
因此进度仅在「开始 / 完成」两点上报，取消仅在开始前检查（MVP 约束）。
"""

import logging
import time

from pdf2docx import Converter

from pdftodoc.core.engines import CancelCheck, ProgressCallback
from pdftodoc.models.enums import ConversionStage, PdfType, TaskStatus
from pdftodoc.models.progress import ProgressEvent
from pdftodoc.models.result import ConversionResult
from pdftodoc.models.task import ConversionTask

logger = logging.getLogger(__name__)


def _cancelled_result(task: ConversionTask, page_count: int) -> ConversionResult:
    return ConversionResult(
        task_id=task.task_id,
        status=TaskStatus.CANCELLED,
        pdf_type=PdfType.TEXT,
        output_path=None,
        page_count=page_count,
        message="已取消",
    )


class TextEngine:
    """封装 pdf2docx 的转换流程。"""

    def convert(
        self,
        task: ConversionTask,
        on_progress: ProgressCallback,
        is_cancelled: CancelCheck,
    ) -> ConversionResult:
        opts = task.options
        task.dst_docx.parent.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()

        cv = Converter(str(task.src_pdf))
        try:
            page_count = cv.fitz_doc.page_count
            if is_cancelled():
                return _cancelled_result(task, page_count)

            on_progress(ProgressEvent(
                task.task_id, ConversionStage.CONVERTING_TEXT, 0, page_count, "开始转换",
            ))
            end = opts.end_page + 1 if opts.end_page is not None else None
            cv.convert(str(task.dst_docx), start=opts.start_page, end=end)
        finally:
            cv.close()

        on_progress(ProgressEvent(
            task.task_id, ConversionStage.DONE, page_count, page_count, "转换完成",
        ))
        elapsed = time.monotonic() - started
        logger.info("文本型转换完成: %s -> %s (%.1fs)", task.src_pdf, task.dst_docx, elapsed)
        return ConversionResult(
            task_id=task.task_id,
            status=TaskStatus.SUCCESS,
            pdf_type=PdfType.TEXT,
            output_path=task.dst_docx,
            page_count=page_count,
            elapsed_sec=elapsed,
            message="转换完成",
        )
