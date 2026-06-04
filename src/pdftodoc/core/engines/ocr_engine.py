"""扫描型引擎：逐页渲染 → PaddleOCR 识别 → 生成 DOCX。

接口与 TextEngine 一致：convert(task, on_progress, is_cancelled) -> ConversionResult。
- 取消在每页边界检查，尽量即时响应；
- 进度按页上报 RENDERING / RECOGNIZING，收尾上报 BUILDING_DOCX / DONE；
- 识别器懒加载且可注入（见 recognizer.py），使本引擎可脱离 paddle 测试。
"""

import logging
import time

import fitz

from pdftodoc.core.engines import CancelCheck, ProgressCallback
from pdftodoc.core.ocr import OcrPage
from pdftodoc.core.ocr.docx_builder import build_docx
from pdftodoc.core.ocr.recognizer import PaddleRecognizer, TextRecognizer
from pdftodoc.core.ocr.renderer import render_page
from pdftodoc.models.enums import ConversionStage, PdfType, TaskStatus
from pdftodoc.models.progress import ProgressEvent
from pdftodoc.models.result import ConversionResult, PageResult
from pdftodoc.models.task import ConversionTask

logger = logging.getLogger(__name__)


class OcrEngine:
    """扫描型 PDF 的 OCR 转换引擎。"""

    def __init__(self, recognizer: TextRecognizer | None = None) -> None:
        # 注入优先（测试用 fake）；否则首次转换时按任务语言懒创建 PaddleRecognizer
        self._recognizer = recognizer

    def _get_recognizer(self, lang: str) -> TextRecognizer:
        if self._recognizer is None:
            self._recognizer = PaddleRecognizer(lang)
        return self._recognizer

    def convert(
        self,
        task: ConversionTask,
        on_progress: ProgressCallback,
        is_cancelled: CancelCheck,
    ) -> ConversionResult:
        opts = task.options
        started = time.monotonic()
        doc = fitz.open(str(task.src_pdf))
        try:
            page_count = doc.page_count
            indices = self._page_indices(opts.start_page, opts.end_page, page_count)
            total = len(indices)
            if is_cancelled():
                return self._cancelled(task, page_count)

            recognizer = self._get_recognizer(opts.ocr_lang)
            pages: list[OcrPage] = []
            page_results: list[PageResult] = []
            for step, page_index in enumerate(indices):
                if is_cancelled():
                    return self._cancelled(task, page_count)
                self._emit(on_progress, task, ConversionStage.RENDERING, step, total, page_index)
                image = render_page(doc, page_index, opts.render_dpi)

                if is_cancelled():
                    return self._cancelled(task, page_count)
                self._emit(
                    on_progress, task, ConversionStage.RECOGNIZING, step + 1, total, page_index
                )
                lines = recognizer.recognize(image)
                pages.append(OcrPage(page_index=page_index, lines=lines))
                page_results.append(PageResult(
                    page_index=page_index,
                    char_count=sum(len(line) for line in lines),
                    line_count=len(lines),
                ))
        finally:
            doc.close()

        on_progress(ProgressEvent(
            task.task_id, ConversionStage.BUILDING_DOCX, total, total, "生成 DOCX",
        ))
        build_docx(pages, task.dst_docx)

        on_progress(ProgressEvent(
            task.task_id, ConversionStage.DONE, total, total, "转换完成",
        ))
        elapsed = time.monotonic() - started
        logger.info(
            "扫描型转换完成: %s -> %s (%d 页, %.1fs)",
            task.src_pdf, task.dst_docx, total, elapsed,
        )
        return ConversionResult(
            task_id=task.task_id,
            status=TaskStatus.SUCCESS,
            pdf_type=PdfType.SCANNED,
            output_path=task.dst_docx,
            page_count=page_count,
            pages=tuple(page_results),
            elapsed_sec=elapsed,
            message="转换完成",
        )

    @staticmethod
    def _page_indices(start: int, end: int | None, page_count: int) -> list[int]:
        """把 0 基的 start/end（含）裁剪到有效页范围，返回待处理页索引。"""
        first = max(0, start)
        last = page_count - 1 if end is None else min(end, page_count - 1)
        return list(range(first, last + 1)) if first <= last else []

    @staticmethod
    def _emit(
        on_progress: ProgressCallback,
        task: ConversionTask,
        stage: ConversionStage,
        current: int,
        total: int,
        page_index: int,
    ) -> None:
        on_progress(ProgressEvent(task.task_id, stage, current, total, f"第 {page_index + 1} 页"))

    @staticmethod
    def _cancelled(task: ConversionTask, page_count: int) -> ConversionResult:
        return ConversionResult(
            task_id=task.task_id,
            status=TaskStatus.CANCELLED,
            pdf_type=PdfType.SCANNED,
            output_path=None,
            page_count=page_count,
            message="已取消",
        )
