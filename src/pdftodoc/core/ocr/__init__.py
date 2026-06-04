"""OCR 子层：页面渲染、PaddleOCR 封装、DOCX 生成。

跨模块传递的中性结构 OcrPage 在此定义，使 docx_builder 不依赖 paddle。
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OcrPage:
    """单页 OCR 文本结果（按阅读顺序的文本行）。"""

    page_index: int
    lines: tuple[str, ...] = field(default_factory=tuple)


__all__ = ["OcrPage"]
