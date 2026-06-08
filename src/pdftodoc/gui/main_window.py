"""主窗口：组装控件，管理 QThread 生命周期，连接 worker 信号到 UI。"""

import logging
import threading
from pathlib import Path

from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from pdftodoc.core.service import ConversionService
from pdftodoc.gui.widgets import Controls, FilePicker, ProgressPanel
from pdftodoc.gui.worker import ConversionWorker
from pdftodoc.models.enums import TaskStatus
from pdftodoc.models.progress import ErrorInfo, ProgressEvent
from pdftodoc.models.result import ConversionResult, DetectionResult
from pdftodoc.models.task import ConversionOptions, ConversionTask

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """单文件 PDF→DOCX 转换主界面。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("pdftodoc — PDF 转 DOCX")
        self.resize(640, 480)
        self._service = ConversionService()
        self._thread: QThread | None = None
        self._worker: ConversionWorker | None = None
        self._prewarm_started = False

        central = QWidget()
        layout = QVBoxLayout(central)
        self._picker = FilePicker()
        self._controls = Controls()
        self._progress = ProgressPanel()
        layout.addWidget(self._picker)
        layout.addWidget(self._controls)
        layout.addWidget(self._progress, 1)
        self.setCentralWidget(central)

        self._picker.file_selected.connect(self._on_file_selected)
        self._controls.convert_clicked.connect(self._start)
        self._controls.cancel_clicked.connect(self._request_cancel)
        self._controls.output_browse_clicked.connect(self._choose_output)
        QTimer.singleShot(3000, self._start_ocr_prewarm)

    # ---- 输入处理 ----
    def _on_file_selected(self, path: str) -> None:
        self._controls.set_output_path(str(Path(path).with_suffix(".docx")))

    def _choose_output(self) -> None:
        start = self._controls.output_path() or self._picker.path()
        path, _ = QFileDialog.getSaveFileName(self, "保存 DOCX", start, "Word 文档 (*.docx)")
        if path:
            if not path.lower().endswith(".docx"):
                path += ".docx"
            self._controls.set_output_path(path)

    # ---- 启动 / 取消 ----
    def _start(self) -> None:
        src = self._picker.path()
        if not src:
            QMessageBox.warning(self, "提示", "请先选择一个 PDF 文件")
            return
        dst = self._controls.output_path() or str(Path(src).with_suffix(".docx"))
        options = ConversionOptions(
            text_fast_layout=not self._controls.precise_text_layout(),
        )
        task = ConversionTask(Path(src), Path(dst), options)
        self._controls.set_running(True)
        self._progress.reset()
        self._progress.append_log(f"开始转换：{src}")
        self._launch(task)

    def _launch(self, task: ConversionTask) -> None:
        thread = QThread(self)
        worker = ConversionWorker(task, self._service)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._on_progress)
        worker.detected.connect(self._on_detected)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)
        self._thread, self._worker = thread, worker
        thread.start()

    def _start_ocr_prewarm(self) -> None:
        if self._prewarm_started:
            return
        if self._thread is not None:
            QTimer.singleShot(3000, self._start_ocr_prewarm)
            return
        self._prewarm_started = True
        thread = threading.Thread(
            target=self._prewarm_ocr,
            name="pdftodoc-ocr-prewarm",
            daemon=True,
        )
        thread.start()

    def _prewarm_ocr(self) -> None:
        try:
            self._service.prewarm_ocr()
            logger.info("OCR 预热完成")
        except Exception:
            logger.exception("OCR 预热失败")

    def _request_cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            self._progress.append_log("正在取消…")

    # ---- worker 信号槽（均在 UI 线程执行）----
    def _on_progress(self, ev: ProgressEvent) -> None:
        self._progress.update_progress(ev)

    def _on_detected(self, d: DetectionResult) -> None:
        self._progress.append_log(
            f"检测：{d.pdf_type.value}（{d.page_count} 页，平均 {d.avg_chars_per_page:.0f} 字符/页）"
        )

    def _on_finished(self, result: ConversionResult) -> None:
        if result.status is TaskStatus.SUCCESS:
            self._progress.append_log(
                f"完成：{result.output_path}（耗时 {result.elapsed_sec:.1f}s）"
            )
            QMessageBox.information(self, "完成", f"已生成：\n{result.output_path}")
        elif result.status is TaskStatus.CANCELLED:
            self._progress.append_log("已取消")
        else:
            self._progress.append_log(f"结束：{result.message}")

    def _on_failed(self, err: ErrorInfo) -> None:
        self._progress.append_log(f"失败：{err.exc_type}: {err.message}")
        QMessageBox.critical(self, "转换失败", f"{err.exc_type}: {err.message}")

    def _on_thread_finished(self) -> None:
        self._controls.set_running(False)
        self._thread = None
        self._worker = None
