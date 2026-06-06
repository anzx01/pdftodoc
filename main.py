"""应用入口。保持简洁：仅委托给 pdftodoc.app.run()。"""

import multiprocessing

from pdftodoc.app import run

if __name__ == "__main__":
    # PyInstaller + Windows multiprocessing spawn 模式必须调用，否则打包后子进程挂起
    multiprocessing.freeze_support()
    raise SystemExit(run())
