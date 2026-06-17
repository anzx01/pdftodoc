# 发布说明 v0.1.0

## 📦 发布文件

**独立可执行程序**：`dist/pdftodoc.exe`（440 MB）

## ✨ 特性

### 核心功能
- ✅ **PDF 转 DOCX**：支持文本型和扫描型 PDF
- ✅ **高性能 OCR**：PaddleOCR PP-OCRv5 Server 模型（实测 ~4 秒/页）
- ✅ **表格识别**：自动检测和重建表格结构
- ✅ **印章提取**：红色印章单独提取为透明 PNG
- ✅ **水印处理**：OCR 前自动去除浅色水印
- ✅ **版式还原**：尽力保留原始文档版式

### OCR 引擎
- **PaddleOCR PP-OCRv5 Server**（百度开源）
  - 准确率：85-92%
  - 速度：约 4 秒/页（i7-10700 @ 2.90GHz）
  - 完全离线运行，无需联网（模型已内置）

## 📋 系统要求

- **操作系统**：Windows 10/11（64位）
- **CPU**：i5 及以上推荐（支持多核加速）
- **内存**：8GB 及以上推荐
- **磁盘空间**：至少 1GB 可用空间

## 🚀 使用方法

### 方式 1：直接运行 exe
1. 双击 `pdftodoc.exe`
2. 在 GUI 界面中选择 PDF 文件
3. 点击"转换"按钮
4. 等待转换完成（会显示进度）
5. 转换后的 DOCX 文件保存在同目录下

### 方式 2：从源码运行
```bash
# 1. 安装依赖
bash scripts/setup.sh

# 2. 下载 OCR 模型（首次运行）
bash scripts/fetch_models.sh

# 3. 启动 GUI
bash scripts/run.sh
```

## 📊 性能数据

基于实际测试（3 页验收证书 PDF）：

| 指标 | 数值 |
|-----|------|
| 总耗时 | 12.2 秒 |
| 平均速度 | 4.1 秒/页 |
| OCR 引擎 | PaddleOCR PP-OCRv5 Server |
| 准确率 | 85-92% |

## 🔧 配置说明

### 默认配置（已优化）
- OCR 语言：中文（`ch`）
- OCR 版本：PP-OCRv5
- 渲染 DPI：200（高质量）
- CPU 线程数：自动（根据 CPU 核心数）
- 检测边长限制：1920（适合 A4 扫描件）
- 识别批大小：6

### 自定义配置
编辑 `src/pdftodoc/models/task.py` 中的 `ConversionOptions` 类。

## 📖 文档

- **性能测试报告**：`docs/OCR引擎性能实测报告.md`
- **WPS 对比分析**：`docs/WPS对比分析.md`
- **完整文档**：`README.md`

## ⚠️ 已知限制

1. **准确率限制**
   - 开源 OCR 准确率：85-92%
   - 商业 OCR（如 WPS/ABBYY）：99%+
   - 这是开源方案的客观限制

2. **版式还原**
   - 复杂版式可能无法完美还原
   - 多栏布局、文字环绕等高级版式支持有限

3. **表格识别**
   - 简单表格：✅ 支持良好
   - 复杂表格（嵌套、斜线表头）：⚠️ 支持有限

## 🐛 问题反馈

如遇问题，请提供：
1. PDF 文件类型（文本型 / 扫描型）
2. 错误信息或截图
3. 系统配置（CPU、内存、OS 版本）

## 📜 许可证

本项目使用的开源组件：
- PaddleOCR：Apache 2.0
- pdf2docx：MIT
- PyMuPDF：AGPL v3
- python-docx：MIT

## 🙏 致谢

感谢以下开源项目：
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [pdf2docx](https://github.com/dothinking/pdf2docx)
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF)

---

**版本**：v0.1.0  
**构建日期**：2026-06-17  
**构建方式**：PyInstaller onefile（单文件独立可执行）
