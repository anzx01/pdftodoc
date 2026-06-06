"""表格线检测：从扫描页图像和 OCR 坐标还原有线表格。"""

import cv2
import numpy as np
from numpy.typing import NDArray

from pdftodoc.core.ocr import OcrLine
from pdftodoc.core.ocr.table_detector import detect_tables


def test_detect_table_with_horizontal_merge() -> None:
    image = _table_image()
    lines = (
        OcrLine("合并表头", (45, 32, 125, 48)),
        OcrLine("右表头", (190, 32, 245, 48)),
        OcrLine("左", (38, 72, 58, 88)),
        OcrLine("中", (112, 72, 132, 88)),
        OcrLine("右", (210, 72, 230, 88)),
        OcrLine("二行左", (35, 112, 75, 128)),
    )

    tables = detect_tables(image, lines)

    assert len(tables) == 1
    table = tables[0]
    assert table.column_count == 3
    assert len(table.rows) == 3
    assert table.rows[0][0].text == "合并表头"
    assert table.rows[0][0].col_span == 2
    assert table.rows[0][1].text == "右表头"
    assert [cell.text for cell in table.rows[1]] == ["左", "中", "右"]
    assert table.rows[2][0].text == "二行左"


def _table_image() -> NDArray[np.uint8]:
    image = np.full((180, 300, 3), 255, dtype=np.uint8)
    for y in (20, 60, 100, 140):
        cv2.line(image, (20, y), (280, y), (0, 0, 0), 1)
    for x, y1 in ((20, 20), (160, 20), (280, 20), (80, 60)):
        cv2.line(image, (x, y1), (x, 140), (0, 0, 0), 1)
    return image
