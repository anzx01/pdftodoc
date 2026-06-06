"""OCR 子层：页面渲染、PaddleOCR 封装、DOCX 生成。

跨模块传递的中性结构 OcrPage 在此定义，使 docx_builder 不依赖 paddle。
"""

from dataclasses import dataclass, field

type BBox = tuple[int, int, int, int]


@dataclass(frozen=True)
class PageImage:
    """渲染后的整页图片，用于版式优先的扫描件 DOCX。"""

    page_index: int
    png: bytes
    width_pt: float
    height_pt: float


@dataclass(frozen=True)
class SealImage:
    """从扫描页抠出的公章图片。"""

    page_index: int
    png: bytes
    bbox: BBox


@dataclass(frozen=True)
class OcrLine:
    """单条 OCR 文本及其在渲染图片中的边界框。"""

    text: str
    box: BBox | None = None


@dataclass(frozen=True)
class OcrCell:
    """OCR 还原出的表格单元格。"""

    text: str = ""
    col_span: int = 1


@dataclass(frozen=True)
class OcrTable:
    """OCR 还原出的表格，支持横向合并单元格。"""

    bbox: BBox
    column_count: int
    rows: tuple[tuple[OcrCell, ...], ...] = field(default_factory=tuple)
    column_widths: tuple[int, ...] = field(default_factory=tuple)
    row_heights: tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OcrPage:
    """单页 OCR 结果。lines 保留纯文本摘要，text_lines/tables 用于版式还原。"""

    page_index: int
    lines: tuple[str, ...] = field(default_factory=tuple)
    text_lines: tuple[OcrLine, ...] = field(default_factory=tuple)
    tables: tuple[OcrTable, ...] = field(default_factory=tuple)
    seals: tuple[SealImage, ...] = field(default_factory=tuple)
    image_width_px: int = 0
    image_height_px: int = 0
    page_width_pt: float = 0.0
    page_height_pt: float = 0.0


__all__ = ["BBox", "OcrCell", "OcrLine", "OcrPage", "OcrTable", "PageImage", "SealImage"]
