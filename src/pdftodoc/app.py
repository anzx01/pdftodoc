"""应用装配：初始化日志 → 创建 QApplication → 显示主窗口 → 进入事件循环。"""

import logging

from pdftodoc.infra.logging_config import setup_logging


def run() -> int:
    """启动 GUI，返回进程退出码。"""
    setup_logging("app")
    logger = logging.getLogger(__name__)
    logger.info("启动 pdftodoc")

    # 延迟导入：避免在无显示环境/单测时拉起 Qt 与重型转换依赖。
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from pdftodoc.gui.main_window import MainWindow
    from pdftodoc.infra.paths import resource_dir

    app = QApplication([])
    app.setApplicationName("pdftodoc")
    icon_path = resource_dir() / "app.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return app.exec()
