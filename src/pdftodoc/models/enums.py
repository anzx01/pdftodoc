"""枚举定义：PDF 类型、转换阶段、任务状态、OCR 引擎类型。"""

from enum import Enum


class PdfType(Enum):
    """PDF 内容类型，决定走哪条转换链路。"""

    TEXT = "text"        # 文本型：含文字图层，走 pdf2docx 保留版式
    SCANNED = "scanned"  # 扫描型：纯图片，默认整页图片保留版式，可选 OCR
    MIXED = "mixed"      # 混合：部分页有文字，默认按 TEXT 处理并告警
    UNKNOWN = "unknown"  # 无法判定（如空文档）


class OcrEngineType(Enum):
    """OCR 识别引擎类型。

    PADDLE: PaddleOCR PP-OCRv5（百度）
            - 速度：约 4 秒/页（实测）
            - 准确率：85-92%
            - 完全本地单进程运行
            - 支持表格结构识别（PP-StructureV3）
            - 成熟稳定，久经考验
    """

    PADDLE = "paddle"    # PaddleOCR PP-OCRv5（唯一可用引擎）


class ConversionStage(Enum):
    """转换流程的细分阶段，用于进度上报。"""

    PENDING = "pending"
    DETECTING = "detecting"
    CONVERTING_TEXT = "converting_text"  # 文本型：pdf2docx 转换中
    RENDERING = "rendering"              # 扫描型：渲染页面为图片
    RECOGNIZING = "recognizing"          # 扫描型可选：OCR 识别
    BUILDING_DOCX = "building_docx"       # 扫描型：生成 DOCX
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """任务的最终状态。"""

    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"
