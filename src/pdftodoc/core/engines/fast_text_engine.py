"""Fast layout-preserving engine for text-based PDFs.

This path uses the PDF's existing text layer and coordinates instead of running
pdf2docx's heavier layout analysis. It keeps text editable and restores page
size plus line positions through the shared DOCX builder.
"""

import logging
import time

import fitz

from pdftodoc.core.engines import CancelCheck, ProgressCallback
from pdftodoc.core.ocr import OcrLine, OcrPage
from pdftodoc.core.ocr.docx_builder import build_docx
from pdftodoc.models.enums import ConversionStage, PdfType, TaskStatus
from pdftodoc.models.progress import ProgressEvent
from pdftodoc.models.result import ConversionResult, PageResult
from pdftodoc.models.task import ConversionTask

logger = logging.getLogger(__name__)


class FastTextEngine:
    """Convert a text PDF quickly by placing editable lines at their PDF coordinates."""

    def convert(
        self,
        task: ConversionTask,
        on_progress: ProgressCallback,
        is_cancelled: CancelCheck,
    ) -> ConversionResult:
        started = time.monotonic()
        task.dst_docx.parent.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(task.src_pdf))
        pages: list[OcrPage] = []
        page_results: list[PageResult] = []
        try:
            page_count = doc.page_count
            indices = self._page_indices(task.options.start_page, task.options.end_page, page_count)
            total = len(indices)
            if is_cancelled():
                return self._cancelled(task, page_count)

            for step, page_index in enumerate(indices):
                if is_cancelled():
                    return self._cancelled(task, page_count)
                on_progress(ProgressEvent(
                    task.task_id,
                    ConversionStage.CONVERTING_TEXT,
                    step,
                    total,
                    f"第 {page_index + 1} 页",
                ))
                page = doc[page_index]
                text_lines = _extract_text_lines(page)
                lines = tuple(line.text for line in text_lines)
                pages.append(OcrPage(
                    page_index=page_index,
                    lines=lines,
                    text_lines=text_lines,
                    image_width_px=max(1, int(round(page.rect.width))),
                    image_height_px=max(1, int(round(page.rect.height))),
                    page_width_pt=page.rect.width,
                    page_height_pt=page.rect.height,
                ))
                page_results.append(PageResult(
                    page_index=page_index,
                    char_count=sum(len(line) for line in lines),
                    line_count=len(lines),
                ))
        finally:
            doc.close()

        on_progress(ProgressEvent(
            task.task_id,
            ConversionStage.BUILDING_DOCX,
            len(pages),
            len(pages),
            "生成 DOCX",
        ))
        build_docx(pages, task.dst_docx)
        on_progress(ProgressEvent(
            task.task_id,
            ConversionStage.DONE,
            len(pages),
            len(pages),
            "转换完成",
        ))

        elapsed = time.monotonic() - started
        logger.info(
            "快速文本版式转换完成 %s -> %s (%d 页, %.1fs)",
            task.src_pdf,
            task.dst_docx,
            len(pages),
            elapsed,
        )
        return ConversionResult(
            task_id=task.task_id,
            status=TaskStatus.SUCCESS,
            pdf_type=PdfType.TEXT,
            output_path=task.dst_docx,
            page_count=page_count,
            pages=tuple(page_results),
            elapsed_sec=elapsed,
            message="转换完成",
        )

    @staticmethod
    def _page_indices(start: int, end: int | None, page_count: int) -> list[int]:
        first = max(0, start)
        last = page_count - 1 if end is None else min(end, page_count - 1)
        return list(range(first, last + 1)) if first <= last else []

    @staticmethod
    def _cancelled(task: ConversionTask, page_count: int) -> ConversionResult:
        return ConversionResult(
            task_id=task.task_id,
            status=TaskStatus.CANCELLED,
            pdf_type=PdfType.TEXT,
            output_path=None,
            page_count=page_count,
            message="已取消",
        )


def _extract_text_lines(page: "fitz.Page") -> tuple[OcrLine, ...]:
    raw = page.get_text("dict", sort=True)
    lines: list[OcrLine] = []
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = "".join(str(span.get("text", "")) for span in spans).strip()
            if not text:
                continue
            bbox = _bbox(line.get("bbox"))
            lines.append(OcrLine(text=text, box=bbox))
    return tuple(sorted(lines, key=_line_sort_key))


def _bbox(raw: object) -> tuple[int, int, int, int] | None:
    if not isinstance(raw, list | tuple) or len(raw) < 4:
        return None
    try:
        x1, y1, x2, y2 = (int(round(float(value))) for value in raw[:4])
    except (TypeError, ValueError):
        return None
    return (x1, y1, x2, y2)


def _line_sort_key(line: OcrLine) -> tuple[int, int]:
    if line.box is None:
        return (0, 0)
    return (line.box[1], line.box[0])


__all__ = ["FastTextEngine"]
