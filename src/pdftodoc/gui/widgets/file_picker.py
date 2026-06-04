"""PDF 文件选择控件。"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FilePicker(QWidget):
    """一行：标签 + 只读路径框 + 浏览按钮。选中文件时发出 file_selected。"""

    file_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("PDF 文件："))
        self._edit = QLineEdit()
        self._edit.setReadOnly(True)
        self._edit.setPlaceholderText("尚未选择文件")
        layout.addWidget(self._edit, 1)
        browse = QPushButton("浏览…")
        browse.clicked.connect(self._browse)
        layout.addWidget(browse)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择 PDF 文件", "", "PDF 文件 (*.pdf)")
        if path:
            self._edit.setText(path)
            self.file_selected.emit(path)

    def path(self) -> str:
        return self._edit.text()
