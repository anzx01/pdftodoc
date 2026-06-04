"""日志配置：root logger 同时输出到控制台与 logs/ 下的轮转文件。"""

import logging
import os
from logging.handlers import RotatingFileHandler

from pdftodoc.infra.paths import logs_dir

_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_configured = False


def setup_logging(log_name: str = "app") -> logging.Logger:
    """初始化全局日志。重复调用安全（只配置一次）。

    日志级别由环境变量 LOG_LEVEL 控制（默认 INFO）。
    文件输出到 logs/<log_name>.log，单文件 5MB、保留 5 份。
    """
    global _configured
    root = logging.getLogger()
    if _configured:
        return root

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root.setLevel(level)

    formatter = logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    log_file = logs_dir() / f"{log_name}.log"
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    _configured = True
    root.info("日志初始化完成，级别=%s，文件=%s", level_name, log_file)
    return root
