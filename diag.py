"""诊断脚本：检查打包环境里的 importlib.metadata 是否能正确读到 paddlex dist-info。"""
import sys
import importlib.metadata
import os
from pathlib import Path

def run():
    lines = []
    lines.append(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
    lines.append(f"sys.path[:5]: {sys.path[:5]}")
    lines.append("")

    # 检查 paddlex metadata
    try:
        meta = importlib.metadata.metadata("paddlex")
        extras = meta.get_all("Provides-Extra", [])
        lines.append(f"paddlex Provides-Extra: {extras}")
        lines.append(f"'ocr' in extras: {'ocr' in extras}")
        lines.append(f"'ocr-core' in extras: {'ocr-core' in extras}")
    except Exception as e:
        lines.append(f"paddlex metadata ERROR: {e}")

    lines.append("")

    # 检查 ocr-core 依赖
    ocr_core_deps = ["imagesize", "opencv-contrib-python", "pyclipper",
                     "pypdfium2", "python-bidi", "shapely"]
    for dep in ocr_core_deps:
        try:
            v = importlib.metadata.version(dep)
            lines.append(f"OK   {dep}: {v}")
        except Exception:
            lines.append(f"MISS {dep}")

    lines.append("")

    # 尝试初始化 PaddleOCR
    try:
        if hasattr(sys, "_MEIPASS"):
            models = Path(sys.executable).parent / "assets" / "models"
        else:
            models = Path(__file__).parents[0] / "assets" / "models"
        os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(models))
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(
            lang="ch",
            ocr_version="PP-OCRv4",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            text_det_limit_side_len=960,
            text_det_limit_type="max",
            text_recognition_batch_size=4,
            device="cpu",
            cpu_threads=2,
            enable_hpi=False,
            enable_mkldnn=False,
        )
        lines.append("PaddleOCR init: OK")
    except Exception as e:
        import traceback
        lines.append(f"PaddleOCR init FAILED: {e}")
        lines.append(traceback.format_exc())

    # 写结果到文件（windowed 模式无控制台）
    out = Path(sys.executable).parent / "diag_result.txt" if hasattr(sys, "_MEIPASS") \
          else Path(__file__).parent / "diag_result.txt"
    out.write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    run()
