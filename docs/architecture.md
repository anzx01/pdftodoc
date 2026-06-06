# pdftodoc 架构说明

桌面 GUI 工具，把 PDF 转换为 DOCX。按 PDF 内容自动选路：

- **文本型**（含文字图层）→ `pdf2docx`，保留版式。
- **扫描型**（纯图片）→ 默认 OCR 重建可编辑文字/表格，并从原图裁剪公章补回。
  整页图片保真模式保留为可选兜底。

## 分层结构

```
src/pdftodoc/
├─ app.py            应用装配：日志 → QApplication → 主窗口
├─ models/           纯数据结构（强类型 dataclass，frozen）
│  ├─ enums.py       PdfType / ConversionStage / TaskStatus
│  ├─ task.py        ConversionTask / ConversionOptions
│  ├─ result.py      DetectionResult / PageResult / ConversionResult
│  └─ progress.py    ProgressEvent / ErrorInfo（跨线程传递）
├─ core/             业务核心（不依赖 Qt）
│  ├─ detector.py    PDF 类型检测（PyMuPDF 抽样统计文字量）
│  ├─ service.py     编排器：检测 → 分派引擎 → 进度/取消
│  ├─ engines/       text_engine（pdf2docx） / ocr_engine（扫描型）
│  └─ ocr/           renderer（渲染）/ recognizer（PaddleOCR 封装）/ docx_builder
├─ gui/              PySide6 界面（main_window / widgets / worker）
└─ infra/            logging_config / paths（兼容 PyInstaller）
```

依赖方向单向向内：`gui → core → models`，`infra` 为横切。GUI 永远不直接接触
`pdf2docx`/`paddle`，只通过 `ConversionService` 这一唯一桥梁。

## 转换链路

```
ConversionService.convert(task)
  │  DETECTING      detector.detect() → DetectionResult
  ├─ 文本型/混合/未知 ─→ TextEngine          (CONVERTING_TEXT → DONE)
  └─ 扫描型/强制OCR ──→ OcrEngine
                         可编辑OCR: RENDERING → RECOGNIZING → BUILDING_DOCX → DONE
                         整页图片:  RENDERING → BUILDING_DOCX → DONE
```

- **类型判定**：抽样各页去空白字符数，按「平均字符数 + 有文字页占比」分类；
  大文件默认抽前/中/后各 3 页，避免检测过慢。混合型按文本型处理并告警。
- **文本型提速**：文本型 PDF 页数达到阈值时自动启用 `pdf2docx` 多进程；
  小文件保持单进程，避免进程启动成本超过收益。
- **OCR 重建**：默认使用 `renderer.render_page` →
  `recognizer.recognize_layout`（PaddleOCR 文本+坐标）→ `table_detector.detect_tables` →
  `seal_detector.detect_seals`（裁剪公章）→ `postprocess.clean_ocr_lines`（过滤公章碎字、
  修正常见误识别）→ `docx_builder.build_docx`。
- **整页图片兜底**：开启 `preserve_scan_layout` 时使用 `renderer.render_page_image` →
  `docx_builder.build_image_docx`，视觉保真但文本不可编辑。
- **取消**：在每页边界检查 `is_cancelled`，尽量即时响应。文本型受 pdf2docx 限制
  仅能在开始前取消（MVP 约束）。

## 线程模型

GUI 用 `QObject + moveToThread` 把转换放到后台线程：

- 进度/结果/错误经 Qt 信号回 UI（自动 QueuedConnection）。
- 取消用 `threading.Event`，UI 线程直接 `set()` 即时生效，不依赖 worker 事件循环。

## OCR 离线模型

`PaddleRecognizer` 在首次识别时把 `PADDLE_PDX_CACHE_HOME` 固定到 `assets/models/`，
与 `scripts/fetch_models.sh` 预下载目录一致——预下载后即可断网运行。
PaddleOCR 与 paddle 为重依赖，故识别器**懒加载**：文本型 PDF 与整页图片兜底模式不会加载 paddle。
`ocr_cpu_threads=0` 表示按本机 CPU 自动选择线程数，当前默认最多使用 8 个推理线程；
识别批量默认为 8，以提高多行文本识别吞吐。

## 设计约束

- 数据结构全部强类型（frozen dataclass），跨模块用中性结构 `OcrPage` 解耦 paddle。
- paddle 调用集中隔离在 `recognizer.py` 一处，便于测试注入 fake、便于适配版本变动。
- 单文件 < 300 行；每层目录文件数受控。

## 测试策略

`tests/` 用 PyMuPDF 动态生成文本型/扫描型样例 PDF（不入库二进制）。OCR 链路注入
`FakeRecognizer`，配合真实 renderer/docx_builder 跑端到端，无需真实 paddle 即可验证
分派、分页、取消与产物。运行：`bash scripts/test.sh`。
