"""路径与资源定位。兼容开发态与 PyInstaller 打包态（sys._MEIPASS）。"""

import sys
from pathlib import Path


def _meipass() -> Path | None:
    """PyInstaller 打包运行时的资源解压目录；非打包态返回 None。"""
    base = getattr(sys, "_MEIPASS", None)
    return Path(base) if base else None


def is_frozen() -> bool:
    """是否运行于 PyInstaller 打包产物中。"""
    return _meipass() is not None


def project_root() -> Path:
    """项目根目录。开发态从源码上溯，打包态为资源解压目录。"""
    mei = _meipass()
    if mei is not None:
        return mei
    # paths.py -> infra -> pdftodoc -> src -> <root>
    return Path(__file__).resolve().parents[3]


def resource_dir() -> Path:
    """只读资源根目录（assets/）。"""
    return project_root() / "assets"


def models_dir() -> Path:
    """PaddleOCR 离线模型目录。"""
    return resource_dir() / "models"


def logs_dir() -> Path:
    """日志输出目录（可写）。打包态写到 exe 同级，避免写入临时只读目录。"""
    if is_frozen():
        base = Path(sys.executable).resolve().parent
    else:
        base = project_root()
    path = base / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path
