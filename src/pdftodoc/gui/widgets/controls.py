"""输出路径与操作按钮（开始转换 / 取消）。"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Controls(QWidget):
    """输出 DOCX 路径行 + 转换/取消按钮行。"""

    convert_clicked = Signal()
    cancel_clicked = Signal()
    output_browse_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        row.addWidget(QLabel("输出 DOCX："))
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("默认与源文件同目录、同名 .docx")
        row.addWidget(self._output_edit, 1)
        self._out_btn = QPushButton("另存为…")
        self._out_btn.clicked.connect(self.output_browse_clicked)
        row.addWidget(self._out_btn)
        layout.addLayout(row)

        btns = QHBoxLayout()
        btns.addStretch(1)
        self._convert_btn = QPushButton("开始转换")
        self._convert_btn.clicked.connect(self.convert_clicked)
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self.cancel_clicked)
        btns.addWidget(self._convert_btn)
        btns.addWidget(self._cancel_btn)
        layout.addLayout(btns)

    def output_path(self) -> str:
        return self._output_edit.text()

    def set_output_path(self, path: str) -> None:
        self._output_edit.setText(path)

    def set_running(self, running: bool) -> None:
        """转换进行中：禁用输入与开始按钮，启用取消。"""
        self._convert_btn.setEnabled(not running)
        self._cancel_btn.setEnabled(running)
        self._out_btn.setEnabled(not running)
        self._output_edit.setEnabled(not running)
