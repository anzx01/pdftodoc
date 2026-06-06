"""公章检测：从扫描页中抠出红色圆章。"""

import cv2
import numpy as np
from numpy.typing import NDArray

from pdftodoc.core.ocr.seal_detector import detect_seals


def test_detect_seal_returns_transparent_png() -> None:
    image = _seal_image()

    seals = detect_seals(image, page_index=0)

    assert len(seals) == 1
    assert seals[0].png.startswith(b"\x89PNG")
    x1, y1, x2, y2 = seals[0].bbox
    assert 90 <= x1 <= 150
    assert 90 <= y1 <= 160
    assert x2 - x1 >= 80
    assert y2 - y1 >= 80


def _seal_image() -> NDArray[np.uint8]:
    image = np.full((360, 360, 3), 255, dtype=np.uint8)
    cv2.circle(image, (180, 220), 55, (0, 0, 180), 3)
    cv2.line(image, (150, 220), (210, 220), (0, 0, 180), 4)
    cv2.line(image, (180, 190), (180, 250), (0, 0, 180), 4)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
