"""数据模型层：重导出全部 dataclass 与 enum。"""

from pdftodoc.models.enums import ConversionStage, PdfType, TaskStatus
from pdftodoc.models.progress import ErrorInfo, ProgressEvent
from pdftodoc.models.result import ConversionResult, DetectionResult, PageResult
from pdftodoc.models.task import ConversionOptions, ConversionTask

__all__ = [
    "ConversionStage",
    "PdfType",
    "TaskStatus",
    "ErrorInfo",
    "ProgressEvent",
    "ConversionResult",
    "DetectionResult",
    "PageResult",
    "ConversionOptions",
    "ConversionTask",
]
