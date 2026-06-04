# pdftodoc — Windows PDF 转 DOCX 工具

桌面 GUI 工具，把 PDF 转换成可编辑的 DOCX。

- **文本型 PDF**：用 [pdf2docx](https://pypi.org/project/pdf2docx/) 转换，保留版式。
- **扫描型 / 纯图片 PDF**：逐页渲染 → [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 识别 → 生成 DOCX。

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

## 注意事项

- PaddlePaddle 的 Windows + Python 3.13 轮子仅在官方索引提供，已在 `pyproject.toml`
  配置 `paddle-cpu` 索引。若 `setup.sh` 中 `paddle.utils.run_check()` 失败，
  可将 `.python-version` 改为 `3.12` 后重跑 `setup.sh`。
- 打包后的 exe 运行需目标机安装 VC++ Redistributable。

详见 `docs/` 目录。
