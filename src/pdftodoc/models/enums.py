"""枚举定义：PDF 类型、转换阶段、任务状态。"""

from enum import Enum


class PdfType(Enum):
    """PDF 内容类型，决定走哪条转换链路。"""

    TEXT = "text"        # 文本型：含文字图层，走 pdf2docx 保留版式
    SCANNED = "scanned"  # 扫描型：纯图片，走 OCR
    MIXED = "mixed"      # 混合：部分页有文字，默认按 TEXT 处理并告警
    UNKNOWN = "unknown"  # 无法判定（如空文档）


class ConversionStage(Enum):
    """转换流程的细分阶段，用于进度上报。"""

    PENDING = "pending"
    DETECTING = "detecting"
    CONVERTING_TEXT = "converting_text"  # 文本型：pdf2docx 转换中
    RENDERING = "rendering"              # 扫描型：渲染页面为图片
    RECOGNIZING = "recognizing"          # 扫描型：OCR 识别
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
