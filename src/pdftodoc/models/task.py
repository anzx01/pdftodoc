"""转换任务及其选项的数据结构。"""

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class ConversionOptions:
    """转换可调参数。默认值适用于大多数中文文档。"""

    ocr_lang: str = "ch"               # PaddleOCR 语言
    scanned_text_threshold: int = 50   # 全文平均每页字符数阈值（低于则倾向扫描型）
    text_page_ratio_min: float = 0.6   # 判为文本型所需的「有文字页」占比
    min_page_chars: int = 20           # 单页≥此字符数才算「有文字页」
    render_dpi: int = 200              # 扫描件渲染 DPI
    force_ocr: bool = False            # 强制走 OCR（忽略检测结果）
    start_page: int = 0                # 起始页（0 基）
    end_page: int | None = None        # 结束页（含），None 表示到末页


@dataclass(frozen=True)
class ConversionTask:
    """一次转换任务：源 PDF、目标 DOCX、选项。"""

    src_pdf: Path
    dst_docx: Path
    options: ConversionOptions = field(default_factory=ConversionOptions)
    task_id: str = field(default_factory=lambda: uuid4().hex)
