"""转换任务及其选项的数据结构。"""

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from pdftodoc.models.enums import OcrEngineType


@dataclass(frozen=True)
class ConversionOptions:
    """转换可调参数。默认值适用于大多数中文文档。"""

    # OCR 引擎选择（核心配置）
    ocr_engine: OcrEngineType = OcrEngineType.PADDLE  # 使用 PaddleOCR（实测最快）

    # PaddleOCR 配置（仅在 ocr_engine=PADDLE 时生效）
    ocr_lang: str = "ch"               # PaddleOCR 语言
    ocr_version: str = "PP-OCRv5"      # PP-OCRv5：最新最强版本
    ocr_cpu_threads: int = 0           # OCR CPU 线程数；0 表示按本机 CPU 自动提速
    ocr_det_limit_side_len: int = 1920 # 文本检测最长边限制
    ocr_rec_batch_size: int = 6        # 文本识别批大小

    # 文本型 PDF 配置
    text_fast_layout: bool = True      # 文本型 PDF 走坐标版式快速转换，保持文字可编辑
    text_multi_processing: bool = True # 文本型 PDF 页数较多时启用 pdf2docx 多进程
    text_cpu_count: int = 0            # 文本型 PDF 转换进程数；0 表示按本机 CPU 自动选择
    text_multi_process_min_pages: int = 8  # 小文件不开多进程，避免启动成本反而变慢

    # PDF 类型检测配置
    detect_sample_threshold: int = 16  # 大于此页数时只抽样检测 PDF 类型
    detect_sample_per_zone: int = 3    # 大文档按前/中/后各抽取的页数
    scanned_text_threshold: int = 50   # 全文平均每页字符数阈值（低于则倾向扫描型）
    text_page_ratio_min: float = 0.6   # 判为文本型所需的「有文字页」占比
    min_page_chars: int = 20           # 单页≥此字符数才算「有文字页」

    # 渲染配置
    render_dpi: int = 200              # 扫描件渲染 DPI，提高至200以保证 OCR 输入质量
    wipe_light_watermark: bool = True  # OCR 前去除浅色文档水印，提升扫描件识别质量
    watermark_black_point: int = 108   # 浅色水印预处理黑场参数
    watermark_white_point: int = 164   # 浅色水印预处理白场参数
    preserve_scan_layout: bool = False # 扫描件默认 OCR 重建，保留可编辑文字
    layout_render_dpi: int = 200       # 版式优先模式的整页图片渲染 DPI

    # 其他配置
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
