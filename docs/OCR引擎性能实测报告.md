# OCR 引擎性能实测报告

## 测试环境

- **硬件**: i7-10700 @ 2.90GHz, 16GB RAM
- **系统**: Windows 10 Pro
- **测试文档**: 验收证书（3 页，含表格、印章、多行文字）

## 测试结果

### 完整对比

| 引擎 | 总耗时 | 平均速度 | 加速比 | 实际表现 |
|-----|--------|---------|--------|---------|
| **PaddleOCR PP-OCRv5** | **12.2 秒** | **4.1 秒/页** | 基准 | ✅ **最快** |
| RapidOCR | 20.2 秒 | 6.7 秒/页 | -40% | ❌ 反而更慢 |

## 结论

**PaddleOCR PP-OCRv5 是最佳选择**

### 选择理由

1. ✅ **速度最快**: 实测比 RapidOCR 快 40%（12.2 秒 vs 20.2 秒）
2. ✅ **功能完整**: 支持表格结构识别（PP-StructureV3）
3. ✅ **成熟稳定**: 百度开源，久经考验
4. ✅ **适合复杂场景**: PP-OCRv5 server 模型专为复杂文档优化

### 为什么 RapidOCR 反而更慢？

官方宣传 RapidOCR 比 PaddleOCR 快 2 倍（0.5-1 秒 vs 1-1.5 秒/页），但实测中反而慢 40%。可能原因：

1. **测试场景差异**
   - 官方可能测试简单文档（单行文本）
   - 我们的验收证书包含表格、印章、复杂版式
   
2. **模型配置不同**
   - PaddleOCR PP-OCRv5 **server 模型**专为复杂场景优化
   - RapidOCR 可能使用的是 mobile 模型转换的 ONNX

3. **CPU vs GPU**
   - 官方测试可能使用 GPU
   - 我们的测试是纯 CPU 推理
   - ONNX Runtime 的 CPU 优化不如 PaddlePaddle

4. **首次加载开销**
   - ONNX 模型加载可能更耗时
   - PaddleOCR 的模型已经过多次优化

## 其他测试过的方案

### GLM-OCR（智谱 AI）
- ❌ **不可用**: 需要独立 vLLM/SGLang 服务器进程
- ❌ **复杂度高**: 无法单进程运行
- ✅ **准确率高**: 94.62%（OmniDocBench 排名第一）

### OpenOCR（复旦大学）
- ❌ **不可用**: Python API 不完整
- ❌ **文档缺失**: 无法找到正确的使用方法

### EasyOCR
- ⚠️ **未测试**: 支持 80+ 语言
- ⚠️ **待验证**: 速度和准确率未知

### Docling（IBM）
- ⚠️ **未测试**: 适合多格式文档转换
- ⚠️ **中文支持待验证**

### dots.OCR（小红书）
- ❌ **不适合**: 需要 GPU（3B 模型）
- ❌ **复杂度高**: PyTorch + Transformers
- ✅ **准确率高**: 超越 GLM-OCR

## 推荐配置

**最终方案**: 使用 **PaddleOCR PP-OCRv5**

```python
from pdftodoc.models.task import ConversionOptions

options = ConversionOptions(
    ocr_version="PP-OCRv5",      # 使用 server 模型
    ocr_lang="ch",               # 中文
    render_dpi=200,              # 高质量渲染
    ocr_det_limit_side_len=1920, # 大尺寸检测
    ocr_rec_batch_size=6,        # 批量识别
)
```

## 性能优化建议

1. **CPU 线程数**: 默认 0（自动按 CPU 核心数优化）
2. **渲染 DPI**: 200（平衡质量与速度）
3. **检测边长限制**: 1920（适合 A4 扫描件）
4. **识别批大小**: 6（平衡内存与速度）

## 测试日期

2026-06-17
