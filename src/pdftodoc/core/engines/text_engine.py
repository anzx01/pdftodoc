"""文本型引擎：用 pdf2docx 转换，保留版式。

pdf2docx 的 Converter.convert 不支持逐页中断与细粒度进度回调，
因此进度仅在「开始 / 完成」两点上报，取消仅在开始前检查（MVP 约束）。
"""

import logging
import os
import time

from pdf2docx import Converter

from pdftodoc.core.engines import CancelCheck, ProgressCallback
from pdftodoc.models.enums import ConversionStage, PdfType, TaskStatus
from pdftodoc.models.progress import ProgressEvent
from pdftodoc.models.result import ConversionResult
from pdftodoc.models.task import ConversionTask

logger = logging.getLogger(__name__)


def _resolve_worker_count(requested: int) -> int:
    """Resolve 0/negative worker settings to a fast default for pdf2docx."""
    if requested > 0:
        return requested
    cpu_count = os.cpu_count() or 4
    return max(2, min(8, cpu_count - 2 if cpu_count > 4 else cpu_count))


def _selected_page_count(start: int, end_exclusive: int | None, page_count: int) -> int:
    first = max(0, start)
    last_exclusive = page_count if end_exclusive is None else min(end_exclusive, page_count)
    return max(0, last_exclusive - first)


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
            selected_pages = _selected_page_count(opts.start_page, end, page_count)
            use_multi_processing = (
                opts.text_multi_processing
                and selected_pages >= opts.text_multi_process_min_pages
            )
            worker_count = _resolve_worker_count(opts.text_cpu_count)
            logger.info(
                "文本型转换参数: pages=%d multi_processing=%s cpu_count=%d",
                selected_pages, use_multi_processing, worker_count,
            )
            cv.convert(
                str(task.dst_docx),
                start=opts.start_page,
                end=end,
                multi_processing=use_multi_processing,
                cpu_count=worker_count,
            )
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
