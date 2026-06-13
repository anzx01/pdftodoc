"""检测结果与转换结果的数据结构。"""

from dataclasses import dataclass, field
from pathlib import Path

from pdftodoc.models.enums import PdfType, TaskStatus


@dataclass(frozen=True)
class DetectionResult:
    """PDF 类型检测结果。"""

    pdf_type: PdfType
    page_count: int
    total_chars: int
    avg_chars_per_page: float
    text_page_ratio: float                 # 有可观文字的页面占比
    sampled_pages: tuple[int, ...] = ()     # 实际参与统计的页索引（大文件抽样）
    has_embedded_images: bool = False       # 是否含嵌入图片块（需要 pdf2docx 处理）


@dataclass(frozen=True)
class PageResult:
    """单页处理结果。"""

    page_index: int
    char_count: int
    line_count: int = 0
    ok: bool = True
    message: str = ""


@dataclass(frozen=True)
class ConversionResult:
    """一次转换的最终结果。"""

    task_id: str
    status: TaskStatus
    pdf_type: PdfType
    output_path: Path | None
    page_count: int
    pages: tuple[PageResult, ...] = field(default_factory=tuple)
    elapsed_sec: float = 0.0
    message: str = ""
