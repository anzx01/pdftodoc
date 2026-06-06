"""文本识别器：把单张图片识别为按阅读顺序的文本行。

PaddleOCR 是重依赖且首次初始化很慢，故在此懒加载并集中隔离。
"""

import logging
import os
from pathlib import Path
from collections.abc import Iterable
from typing import Any, Protocol, cast

import numpy as np
from numpy.typing import NDArray

from pdftodoc.core.ocr import BBox, OcrLine
from pdftodoc.infra.paths import models_dir

logger = logging.getLogger(__name__)

_MODEL_DIR = "official_models"
_KNOWN_MODELS = {
    ("ch", "PP-OCRv4"): ("PP-OCRv4_mobile_det", "PP-OCRv4_mobile_rec"),
}


class TextRecognizer(Protocol):
    """识别器协议：输入 RGB 图，输出按阅读顺序的非空文本行。"""

    def recognize(self, image: NDArray[np.uint8]) -> tuple[str, ...]:
        ...


class PaddleRecognizer:
    """PaddleOCR 封装。paddle 在首次 recognize 时才加载，构造本身很轻。"""

    def __init__(
        self,
        lang: str = "ch",
        ocr_version: str = "PP-OCRv4",
        cpu_threads: int = 2,
        det_limit_side_len: int = 960,
        rec_batch_size: int = 4,
    ) -> None:
        self._lang = lang
        self._ocr_version = ocr_version
        self._cpu_threads = cpu_threads
        self._det_limit_side_len = det_limit_side_len
        self._rec_batch_size = rec_batch_size
        self._ocr: object | None = None

    def _ensure(self) -> object:
        if self._ocr is not None:
            return self._ocr

        cache = models_dir()
        cache.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(cache))
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

        from paddleocr import PaddleOCR

        kwargs: dict[str, object] = {
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
            "text_det_limit_side_len": self._det_limit_side_len,
            "text_det_limit_type": "max",
            "text_recognition_batch_size": self._rec_batch_size,
            "device": "cpu",
            "cpu_threads": self._cpu_threads,
            "enable_hpi": False,
            "enable_mkldnn": False,  # 禁用 mkldnn 避开 PIR+oneDNN bug
        }
        kwargs.update(self._model_kwargs(cache))

        logger.info(
            "初始化 PaddleOCR(lang=%s, version=%s, cpu_threads=%d, cache=%s)",
            self._lang, self._ocr_version, self._cpu_threads, cache,
        )
        self._ocr = PaddleOCR(**kwargs)
        return self._ocr

    def _model_kwargs(self, cache: Path) -> dict[str, object]:
        names = _KNOWN_MODELS.get((self._lang, self._ocr_version))
        if names is None:
            return {"lang": self._lang, "ocr_version": self._ocr_version}

        det_name, rec_name = names
        kwargs: dict[str, object] = {
            "text_detection_model_name": det_name,
            "text_recognition_model_name": rec_name,
        }
        det_dir = _existing_model_dir(cache, det_name)
        rec_dir = _existing_model_dir(cache, rec_name)
        if det_dir is not None:
            kwargs["text_detection_model_dir"] = str(det_dir)
        if rec_dir is not None:
            kwargs["text_recognition_model_dir"] = str(rec_dir)
        return kwargs

    def recognize(self, image: NDArray[np.uint8]) -> tuple[str, ...]:
        return tuple(line.text for line in self.recognize_layout(image))

    def recognize_layout(self, image: NDArray[np.uint8]) -> tuple[OcrLine, ...]:
        ocr = self._ensure()
        results = cast(Iterable[Any], ocr.predict(image))  # type: ignore[attr-defined]
        lines: list[OcrLine] = []
        for res in results:
            texts = res["rec_texts"] if "rec_texts" in res else []
            boxes = res["rec_boxes"] if "rec_boxes" in res else []
            for index, raw_text in enumerate(texts):
                text = str(raw_text).strip()
                if text:
                    lines.append(OcrLine(text=text, box=_box_at(boxes, index)))
        return tuple(lines)


def _existing_model_dir(cache: Path, model_name: str) -> Path | None:
    path = cache / _MODEL_DIR / model_name
    return path if path.is_dir() else None


def _box_at(boxes: object, index: int) -> BBox | None:
    try:
        raw = boxes[index]  # type: ignore[index]
    except (IndexError, TypeError):
        return None
    if hasattr(raw, "tolist"):
        raw = raw.tolist()
    if not isinstance(raw, list | tuple) or len(raw) < 4:
        return None
    try:
        x1, y1, x2, y2 = (int(round(float(value))) for value in raw[:4])
    except (TypeError, ValueError):
        return None
    return (x1, y1, x2, y2)


__all__ = ["TextRecognizer", "PaddleRecognizer"]
