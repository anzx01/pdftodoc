"""进度事件与错误信息的数据结构（跨线程传递）。"""

from dataclasses import dataclass

from pdftodoc.models.enums import ConversionStage


@dataclass(frozen=True)
class ProgressEvent:
    """进度上报事件。current/total 为当前阶段的步数（通常是页）。"""

    task_id: str
    stage: ConversionStage
    current: int
    total: int
    detail: str = ""

    @property
    def percent(self) -> float:
        """完成百分比（0~100）。total 为 0 时返回 0。"""
        if self.total <= 0:
            return 0.0
        return min(100.0, self.current / self.total * 100.0)


@dataclass(frozen=True)
class ErrorInfo:
    """转换失败的结构化错误信息。"""

    task_id: str
    stage: ConversionStage
    exc_type: str
    message: str
    traceback_text: str = ""
