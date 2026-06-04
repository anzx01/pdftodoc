"""后台转换 worker（QObject + moveToThread 模式）。

进度/结果/错误通过信号跨线程回报到 UI（Qt 自动 QueuedConnection）。
取消通过线程安全的 threading.Event：UI 线程直接调用 cancel() 即可即时生效，
不依赖 worker 线程的事件循环（run() 执行期间该事件循环并不处理排队槽）。
"""

import logging
import threading

from PySide6.QtCore import QObject, Signal, Slot

from pdftodoc.core.service import ConversionService
from pdftodoc.models.task import ConversionTask

logger = logging.getLogger(__name__)


class ConversionWorker(QObject):
    """在独立线程中执行一次转换任务。"""

    progress = Signal(object)   # ProgressEvent
    finished = Signal(object)   # ConversionResult
    failed = Signal(object)     # ErrorInfo
    detected = Signal(object)   # DetectionResult

    def __init__(self, task: ConversionTask, service: ConversionService) -> None:
        super().__init__()
        self._task = task
        self._service = service
        self._cancel = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            result = self._service.convert(
                self._task,
                on_progress=self.progress.emit,
                on_detected=self.detected.emit,
                is_cancelled=self._cancel.is_set,
            )
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001 — 统一转为结构化错误回报 UI
            self.failed.emit(self._service.to_error_info(self._task, exc))

    def cancel(self) -> None:
        """请求取消（线程安全，UI 线程直接调用）。"""
        logger.info("用户请求取消任务 %s", self._task.task_id)
        self._cancel.set()
