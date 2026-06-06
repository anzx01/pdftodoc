"""PaddleOCR 封装测试：不加载真实 paddle，只校验初始化参数与结果清洗。"""

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from pdftodoc.core.ocr import recognizer


def test_paddle_recognizer_uses_local_mobile_models(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_root = tmp_path / "official_models"
    det_dir = model_root / "PP-OCRv4_mobile_det"
    rec_dir = model_root / "PP-OCRv4_mobile_rec"
    det_dir.mkdir(parents=True)
    rec_dir.mkdir(parents=True)

    created: dict[str, object] = {}

    class FakePaddleOCR:
        def __init__(self, **kwargs: object) -> None:
            created.update(kwargs)

        def predict(self, _image: np.ndarray) -> list[dict[str, list[str]]]:
            return [{"rec_texts": ["  第一行  ", "", "第二行"]}]

    monkeypatch.setattr(recognizer, "models_dir", lambda: tmp_path)
    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=FakePaddleOCR))

    lines = recognizer.PaddleRecognizer().recognize(np.zeros((8, 8, 3), dtype=np.uint8))

    assert lines == ("第一行", "第二行")
    assert created["text_detection_model_name"] == "PP-OCRv4_mobile_det"
    assert created["text_recognition_model_name"] == "PP-OCRv4_mobile_rec"
    assert created["text_detection_model_dir"] == str(det_dir)
    assert created["text_recognition_model_dir"] == str(rec_dir)
    assert created["text_det_limit_side_len"] == 960
    assert created["text_det_limit_type"] == "max"
    assert created["cpu_threads"] == 2
    assert created["enable_mkldnn"] is False
    assert "lang" not in created
    assert "ocr_version" not in created
