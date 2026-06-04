"""测试夹具：用 PyMuPDF 动态生成文本型 / 扫描型样例 PDF（不入库二进制）。"""

from pathlib import Path

import fitz
import pytest


@pytest.fixture
def text_pdf(tmp_path: Path) -> Path:
    """文本型 PDF：含足量文字图层，应被判为 TEXT。"""
    path = tmp_path / "text_sample.pdf"
    doc = fitz.open()
    body = "Hello World. This is a text-based PDF sample used for detection tests. " * 3
    for _ in range(2):
        page = doc.new_page()
        page.insert_text((72, 72), body, fontsize=11)
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def scanned_pdf(tmp_path: Path) -> Path:
    """扫描型 PDF：仅含图片、无文字图层，应被判为 SCANNED。"""
    path = tmp_path / "scan_sample.pdf"
    doc = fitz.open()
    for _ in range(2):
        page = doc.new_page()
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 400, 400))
        pix.clear_with(220)  # 浅灰填充，无任何可提取文字
        page.insert_image(page.rect, pixmap=pix)
    doc.save(path)
    doc.close()
    return path
