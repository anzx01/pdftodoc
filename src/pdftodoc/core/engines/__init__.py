"""引擎层：文本型引擎与 OCR 引擎共用的回调类型定义。"""

from collections.abc import Callable

from pdftodoc.models.progress import ProgressEvent

# 进度回调：引擎在各阶段调用，上报 ProgressEvent
ProgressCallback = Callable[[ProgressEvent], None]
# 取消检查：引擎在可中断处调用，返回 True 表示用户已请求取消
CancelCheck = Callable[[], bool]

__all__ = ["ProgressCallback", "CancelCheck"]
