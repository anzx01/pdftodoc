"""基础设施层：日志与路径。"""

from pdftodoc.infra.logging_config import setup_logging
from pdftodoc.infra.paths import logs_dir, models_dir, project_root, resource_dir

__all__ = [
    "setup_logging",
    "logs_dir",
    "models_dir",
    "project_root",
    "resource_dir",
]
