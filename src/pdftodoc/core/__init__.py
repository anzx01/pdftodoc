"""核心转换层：类型检测、引擎、OCR 与服务编排。

注意：本包 __init__ 刻意保持轻量，不在此导出 service/engine，
以避免 `import pdftodoc.core` 时即拉起 pdf2docx / paddle 等重型依赖，
也避免与 service.py 的 `from pdftodoc.core import detector` 形成循环导入。
调用方请直接 `from pdftodoc.core.service import ConversionService`。
"""
