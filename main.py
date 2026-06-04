"""应用入口。保持简洁：仅委托给 pdftodoc.app.run()。"""

from pdftodoc.app import run

if __name__ == "__main__":
    raise SystemExit(run())
