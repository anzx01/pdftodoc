"""进度面板：阶段文本 + 进度条 + 日志区。"""

from PySide6.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from pdftodoc.models.enums import ConversionStage
from pdftodoc.models.progress import ProgressEvent

_STAGE_TEXT = {
    ConversionStage.PENDING: "等待中",
    ConversionStage.DETECTING: "检测 PDF 类型",
    ConversionStage.CONVERTING_TEXT: "转换中（文本型）",
    ConversionStage.RENDERING: "渲染页面",
    ConversionStage.RECOGNIZING: "OCR 识别",
    ConversionStage.BUILDING_DOCX: "生成 DOCX",
    ConversionStage.DONE: "完成",
    ConversionStage.FAILED: "失败",
    ConversionStage.CANCELLED: "已取消",
}
# pdf2docx 无逐页进度，转换期间用不确定进度条
_BUSY_STAGES = {ConversionStage.DETECTING, ConversionStage.CONVERTING_TEXT}
# 含 current/total 的逐页阶段，附带页码显示
_PAGED_STAGES = {
    ConversionStage.RENDERING,
    ConversionStage.RECOGNIZING,
    ConversionStage.BUILDING_DOCX,
}


class ProgressPanel(QWidget):
    """展示转换进度与日志。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._stage_label = QLabel("就绪")
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        layout.addWidget(self._stage_label)
        layout.addWidget(self._bar)
        layout.addWidget(self._log, 1)

    def reset(self) -> None:
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._stage_label.setText("就绪")
        self._log.clear()

    def update_progress(self, ev: ProgressEvent) -> None:
        text = _STAGE_TEXT.get(ev.stage, ev.stage.value)
        if ev.stage in _BUSY_STAGES:
            self._bar.setRange(0, 0)  # 不确定进度
        else:
            self._bar.setRange(0, 100)
            self._bar.setValue(int(ev.percent))
        if ev.stage in _PAGED_STAGES and ev.total > 0:
            text += f"  {ev.current}/{ev.total}"
        self._stage_label.setText(text)
        if ev.detail:
            self.append_log(f"{text}：{ev.detail}")

    def append_log(self, message: str) -> None:
        self._log.appendPlainText(message)
