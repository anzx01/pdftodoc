# pdftodoc — Windows PDF 转 DOCX 工具

桌面 GUI 工具，把 PDF 转换成可编辑的 DOCX。

## 支持的 PDF 类型

| PDF 类型 | 识别方式 | 转换策略 |
|---|---|---|
| 文本型（纯文字排版） | 字符层字符密度 | pdf2docx，保留版式 |
| 含嵌入图片的文本型（合格证、表单等） | 文字行中心落在图片块内 | OverlayEngine：白化烧入文字 + VML 可编辑文本框 |
| 扫描型 / 纯图片 | 字符密度极低 | 多引擎 OCR 重建文字和表格，公章裁剪补回 |
| 混合型 | 部分页有文字 | 按文本型处理 |

## OCR 引擎

本工具使用 **PaddleOCR PP-OCRv5**（百度开源）进行文字识别：

| 特性 | 说明 |
|-----|------|
| **速度** | 约 4 秒/页（实测，i7-10700 @ 2.90GHz） |
| **准确率** | 85-92% |
| **特点** | 完全免费离线，支持表格结构识别（PP-StructureV3） |
| **适用场景** | 验收证书、合同、发票等复杂文档 |

**为什么选择 PaddleOCR？**

经过实测对比（包括 RapidOCR、EasyOCR 等方案），PaddleOCR PP-OCRv5 在复杂文档场景下表现最佳：
- ✅ **速度最快**：实测 3 页验收证书仅需 12.2 秒
- ✅ **功能完整**：支持表格结构识别、印章提取
- ✅ **成熟稳定**：久经考验，生态完善

## 核心特性

- **高性能 OCR**：PaddleOCR PP-OCRv5，实测约 4 秒/页
- **完全免费离线**：无需联网（首次使用需下载模型），无使用次数限制，隐私安全
- **含嵌入图片的表单 / 合格证**：自动识别"烧入图片"的文字，用 OpenCV 白化图片内的文字区域，再以 VML 大文本框精确覆盖——背景图保留印章、表格线、LOGO，文字完全可在 Word / WPS 中编辑
- **扫描型 PDF**：OCR 前对浅色文档水印做预处理；表格重建为 Word 表格；红色公章提取为透明 PNG 浮动对象，可单独选中移动
- **性能自适应**：OCR 线程数按本机 CPU 自动调优，文本型大 PDF 自动启用 pdf2docx 多进程，小文件保持单进程以避免启动开销
- **可选整页图片模式**：`preserve_scan_layout=True` 保留扫描件像素级版式，但文字不可编辑

## 技术栈

Python 3.13 · PySide6 · pdf2docx · PyMuPDF · PaddleOCR (PP-OCRv5) · python-docx · OpenCV · uv

## 快速开始

> 所有操作通过 `scripts/` 下的 .sh 脚本执行（Git Bash），不要直接敲 uv/python。

```bash
bash scripts/setup.sh          # 建 .venv、安装依赖、校验 paddle
bash scripts/fetch_models.sh   # 预下载 OCR 模型到 assets/models/
bash scripts/run.sh            # 启动 GUI
bash scripts/test.sh           # 跑测试
bash scripts/build.sh          # PyInstaller 打包成 exe（onedir）
```

## 打包

打包前先确保 OCR 模型已下载到 `assets/models/`：

```bash
bash scripts/fetch_models.sh
bash scripts/build.sh
```

产物位于 `dist/pdftodoc/`，分发时需整个目录一起拷贝。

## OCR 导出说明

- 默认扫描件模式生成可编辑 DOCX，表格按检测线框重建为 Word 表格。
- 红色公章从原图中提取为透明 PNG，作为独立浮动对象插回对应位置。
- 若原文被公章遮挡，程序会用同一文档中更完整的字段做保守补全。
- `preserve_scan_layout=True` 可走整页图片兜底模式，版式最稳但文字不可编辑。

## 注意事项

- PaddlePaddle 的 Windows + Python 3.13 轮子仅在官方索引提供，已在 `pyproject.toml` 配置 `paddle-cpu` 索引。若 `setup.sh` 中 `paddle.utils.run_check()` 失败，可将 `.python-version` 改为 `3.12` 后重跑 `setup.sh`。
- 打包后的 exe 运行需目标机安装 VC++ Redistributable。

详见 `docs/` 目录。
