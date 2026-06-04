"""文本识别器：把单张图片识别为按阅读顺序的文本行。

PaddleOCR 是重依赖且首次初始化很慢，故在此懒加载并集中隔离：
- ocr_engine 只依赖 TextRecognizer 协议，不直接 import paddle；
- 单元测试可注入 fake 识别器，无需真实 paddle 即可跑通整条链路。

PaddleOCR 版本约束：3.0.x（predict() 接口、结果以 rec_texts 暴露文本行）。
若官方 API 在小版本间变动，仅需修改本文件的 _ensure / recognize。
"""

import logging
import os
from typing import Protocol

import numpy as np

from pdftodoc.infra.paths import models_dir

logger = logging.getLogger(__name__)


class TextRecognizer(Protocol):
    """识别器协议：输入 RGB 图，输出按阅读顺序的非空文本行。"""

    def recognize(self, image: np.ndarray) -> tuple[str, ...]:
        ...


class PaddleRecognizer:
    """PaddleOCR 封装。paddle 在首次 recognize 时才加载，构造本身很轻。"""

    def __init__(self, lang: str = "ch") -> None:
        self._lang = lang
        self._ocr: object | None = None

    def _ensure(self) -> object:
        if self._ocr is not None:
            return self._ocr

        # 把 PaddleX 模型缓存固定到项目内 assets/models：fetch_models.sh 预下载
        # 与运行时定位走同一目录 —— 已下载则断网可用，未下载则首次联网拉取到此。
        cache = models_dir()
        cache.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(cache))

        from paddleocr import PaddleOCR

        # 仅做文本检测+识别，关闭方向/扭曲矫正等子模块以提速、降依赖
        logger.info("初始化 PaddleOCR(lang=%s)，模型缓存=%s ...", self._lang, cache)
        self._ocr = PaddleOCR(
            lang=self._lang,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        return self._ocr

    def recognize(self, image: np.ndarray) -> tuple[str, ...]:
        ocr = self._ensure()
        results = ocr.predict(image)  # type: ignore[attr-defined]
        lines: list[str] = []
        for res in results:
            # PaddleOCR 3.x 的结果对象为 dict 子类，文本行在 rec_texts 键下
            texts = res["rec_texts"] if "rec_texts" in res else []
            lines.extend(t for t in texts if t and t.strip())
        return tuple(lines)


__all__ = ["TextRecognizer", "PaddleRecognizer"]
