# pdftodoc — Windows PDF 转 DOCX 工具

桌面 GUI 工具，把 PDF 转换成 DOCX。

- **文本型 PDF**：用 [pdf2docx](https://pypi.org/project/pdf2docx/) 转换，保留版式。
- **扫描型 / 纯图片 PDF**：默认 OCR 重建可编辑文字和表格，并从原图裁剪公章补回。
- OCR 默认使用中文 `PP-OCRv4_mobile` 轻量模型，避免 `PP-OCRv5_server`
  在 CPU 机器上长时间卡顿；整页图片保真模式保留为可选兜底。
- 扫描件导出的文字是普通 Word 段落/表格，公章是独立透明图片对象，可在 Word/WPS
  中单独选中、移动或删除。

## 技术栈

Python 3.13 · PySide6 · pdf2docx · PyMuPDF · PaddleOCR · python-docx · uv

## 快速开始

> 所有操作通过 `scripts/` 下的 .sh 脚本执行（Git Bash 运行），不要直接敲 uv/python。

```bash
bash scripts/setup.sh          # 建 .venv、安装依赖、校验 paddle
bash scripts/fetch_models.sh   # 预下载 OCR 模型到 assets/models/
bash scripts/run.sh            # 启动 GUI
bash scripts/test.sh           # 跑测试
bash scripts/build.sh          # PyInstaller 打包成 exe（onedir）
```

## 打包可执行文件

打包前先确保 OCR 模型已经下载到 `assets/models/`：

```bash
bash scripts/fetch_models.sh
bash scripts/build.sh
```

打包产物位于：

```text
dist/pdftodoc/pdftodoc.exe
```

`dist/pdftodoc/` 是 onedir 目录，分发时需要整个目录一起拷贝，不只拷贝 exe。

## OCR 导出说明

- 默认扫描件模式会生成可编辑 DOCX，不再把整页 PDF 当作背景图铺进 Word。
- 表格会按检测到的线框重建为 Word 表格，并尽量保留列宽、行高和单元格合并。
- 红色公章会从原图中提取为透明 PNG，再作为独立浮动对象插回对应位置。
- 如果原文被公章遮挡，程序会用同一文档中更完整的字段做保守补全。
- `preserve_scan_layout=True` 时可走整页图片兜底模式，版式最稳，但文字不可编辑。

## 注意事项

- PaddlePaddle 的 Windows + Python 3.13 轮子仅在官方索引提供，已在 `pyproject.toml`
  配置 `paddle-cpu` 索引。若 `setup.sh` 中 `paddle.utils.run_check()` 失败，
  可将 `.python-version` 改为 `3.12` 后重跑 `setup.sh`。
- 打包后的 exe 运行需目标机安装 VC++ Redistributable。

详见 `docs/` 目录。
