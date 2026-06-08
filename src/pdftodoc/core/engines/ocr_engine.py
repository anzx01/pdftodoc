"""扫描型引擎：逐页渲染 → PaddleOCR 识别 → 生成 DOCX。

接口与 TextEngine 一致：convert(task, on_progress, is_cancelled) -> ConversionResult。
- 取消在每页边界检查，尽量即时响应；
- 进度按页上报 RENDERING / RECOGNIZING，收尾上报 BUILDING_DOCX / DONE；
- 识别器懒加载且可注入（见 recognizer.py），使本引擎可脱离 paddle 测试。
"""

import logging
import time
from collections.abc import Callable
from typing import cast

import fitz
import numpy as np
from numpy.typing import NDArray

from pdftodoc.core.engines import CancelCheck, ProgressCallback
from pdftodoc.core.ocr import OcrLine, OcrPage, PageImage
from pdftodoc.core.ocr.docx_builder import build_docx, build_image_docx
from pdftodoc.core.ocr.postprocess import clean_ocr_lines, repair_cross_page_fields
from pdftodoc.core.ocr.recognizer import PaddleRecognizer, TextRecognizer
from pdftodoc.core.ocr.renderer import (
    render_page,
    render_page_image,
)
from pdftodoc.core.ocr.seal_detector import detect_seals
from pdftodoc.core.ocr.table_detector import detect_tables
from pdftodoc.core.ocr.watermark import wipe_light_watermark
from pdftodoc.models.enums import ConversionStage, PdfType, TaskStatus
from pdftodoc.models.progress import ProgressEvent
from pdftodoc.models.result import ConversionResult, PageResult
from pdftodoc.models.task import ConversionOptions, ConversionTask

logger = logging.getLogger(__name__)


class OcrEngine:
    """扫描型 PDF 的 OCR 转换引擎。"""

    def __init__(self, recognizer: TextRecognizer | None = None) -> None:
        # 注入优先（测试用 fake）；否则首次转换时按任务语言懒创建 PaddleRecognizer
        self._recognizer = recognizer

    def _get_recognizer(self, opts: ConversionOptions) -> TextRecognizer:
        if self._recognizer is None:
            self._recognizer = PaddleRecognizer(
                lang=opts.ocr_lang,
                ocr_version=opts.ocr_version,
                cpu_threads=opts.ocr_cpu_threads,
                det_limit_side_len=opts.ocr_det_limit_side_len,
                rec_batch_size=opts.ocr_rec_batch_size,
            )
        return self._recognizer

    def warm_up(self, opts: ConversionOptions) -> None:
        """Initialize PaddleOCR before the first real editable conversion."""
        recognizer = self._get_recognizer(opts)
        image = np.full((64, 256, 3), 255, dtype=np.uint8)
        self._recognize_page(recognizer, image)

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

            if opts.preserve_scan_layout:
                return self._convert_as_page_images(
                    task, doc, indices, page_count, on_progress, is_cancelled, started
                )

            recognizer = self._get_recognizer(opts)
            pages: list[OcrPage] = []
            page_results: list[PageResult] = []
            for step, page_index in enumerate(indices):
                if is_cancelled():
                    return self._cancelled(task, page_count)
                self._emit(on_progress, task, ConversionStage.RENDERING, step, total, page_index)
                image = render_page(doc, page_index, opts.render_dpi)
                ocr_image = (
                    wipe_light_watermark(
                        image,
                        opts.watermark_black_point,
                        opts.watermark_white_point,
                    )
                    if opts.wipe_light_watermark
                    else image
                )

                if is_cancelled():
                    return self._cancelled(task, page_count)
                self._emit(
                    on_progress, task, ConversionStage.RECOGNIZING, step + 1, total, page_index
                )
                raw_lines = self._recognize_page(recognizer, ocr_image)
                seals = detect_seals(image, page_index)
                text_lines = clean_ocr_lines(raw_lines, seals)
                lines = tuple(line.text for line in text_lines)
                tables = detect_tables(ocr_image, text_lines)
                page = doc[page_index]
                pages.append(
                    OcrPage(
                        page_index=page_index,
                        lines=lines,
                        text_lines=text_lines,
                        tables=tables,
                        seals=seals,
                        image_width_px=image.shape[1],
                        image_height_px=image.shape[0],
                        page_width_pt=page.rect.width,
                        page_height_pt=page.rect.height,
                    )
                )
                page_results.append(PageResult(
                    page_index=page_index,
                    char_count=sum(len(line) for line in lines),
                    line_count=len(lines),
                ))
        finally:
            doc.close()

        pages = list(repair_cross_page_fields(pages))
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

    def _convert_as_page_images(
        self,
        task: ConversionTask,
        doc: "fitz.Document",
        indices: list[int],
        page_count: int,
        on_progress: ProgressCallback,
        is_cancelled: CancelCheck,
        started: float,
    ) -> ConversionResult:
        total = len(indices)
        images: list[PageImage] = []
        page_results: list[PageResult] = []
        for step, page_index in enumerate(indices):
            if is_cancelled():
                return self._cancelled(task, page_count)
            self._emit(on_progress, task, ConversionStage.RENDERING, step, total, page_index)
            images.append(render_page_image(doc, page_index, task.options.layout_render_dpi))
            page_results.append(PageResult(page_index=page_index, char_count=0, line_count=0))

        on_progress(ProgressEvent(
            task.task_id, ConversionStage.BUILDING_DOCX, total, total, "生成版式 DOCX",
        ))
        build_image_docx(images, task.dst_docx)

        on_progress(ProgressEvent(
            task.task_id, ConversionStage.DONE, total, total, "转换完成",
        ))
        elapsed = time.monotonic() - started
        logger.info(
            "扫描型版式转换完成: %s -> %s (%d 页, %.1fs)",
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
    def _recognize_page(
        recognizer: TextRecognizer, image: NDArray[np.uint8]
    ) -> tuple[OcrLine, ...]:
        layout_method = getattr(recognizer, "recognize_layout", None)
        if callable(layout_method):
            recognize_layout = cast(Callable[[NDArray[np.uint8]], tuple[OcrLine, ...]], layout_method)
            return recognize_layout(image)
        return tuple(OcrLine(text=text) for text in recognizer.recognize(image))

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
