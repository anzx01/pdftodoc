"""页面渲染：用 PyMuPDF 把 PDF 页渲染为 RGB numpy 图，供 OCR 使用。"""

import logging

import fitz
import numpy as np
from numpy.typing import NDArray

from pdftodoc.core.ocr import PageImage

logger = logging.getLogger(__name__)


def render_page(doc: "fitz.Document", page_index: int, dpi: int) -> NDArray[np.uint8]:
    """渲染指定页为 (H, W, 3) 的 RGB uint8 数组。

    dpi 越高识别越准但越慢；默认 200 适合大多数扫描件。
    """
    page = doc[page_index]
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    # alpha=False 时 n 应为 3；若为灰度(1)则堆叠为三通道
    if pix.n == 1:
        img = np.repeat(img, 3, axis=2)
    return np.ascontiguousarray(img[:, :, :3])


def render_page_image(doc: "fitz.Document", page_index: int, dpi: int) -> PageImage:
    """渲染指定页为 PNG 整页图片，保留扫描件原始视觉版式。"""
    page = doc[page_index]
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return PageImage(
        page_index=page_index,
        png=pix.tobytes("png"),
        width_pt=page.rect.width,
        height_pt=page.rect.height,
    )
