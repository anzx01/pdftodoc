"""应用装配：初始化日志 → 创建 QApplication → 显示主窗口 → 进入事件循环。"""

import logging

from pdftodoc.infra.logging_config import setup_logging


def run() -> int:
    """启动 GUI，返回进程退出码。"""
    setup_logging("app")
    logger = logging.getLogger(__name__)
    logger.info("启动 pdftodoc")

    # 延迟导入：避免在无显示环境/单测时拉起 Qt 与重型转换依赖。
    from PySide6.QtWidgets import QApplication

    from pdftodoc.gui.main_window import MainWindow

    app = QApplication([])
    app.setApplicationName("pdftodoc")
    window = MainWindow()
    window.show()
    return app.exec()
