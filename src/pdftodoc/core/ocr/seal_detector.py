"""从扫描页图像中检测并抠出红色公章。"""

import cv2
import numpy as np
from numpy.typing import NDArray
from typing import cast

from pdftodoc.core.ocr import BBox, SealImage


def detect_seals(image: NDArray[np.uint8], page_index: int) -> tuple[SealImage, ...]:
    """检测红色印章，返回透明 PNG。"""
    mask = _red_mask(image)
    merged = cv2.morphologyEx(
        mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)), iterations=1
    )
    merged = cv2.dilate(merged, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1)
    contours, _ = cv2.findContours(merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    height, width = image.shape[:2]
    candidates: list[tuple[float, BBox, BBox]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        if not _looks_like_seal(x, y, w, h, area, width, height):
            continue
        bbox = _expanded_bbox(x, y, w, h, width, height)
        candidates.append((area, bbox, (x, y, x + w, y + h)))

    seals: list[SealImage] = []
    for _, bbox, core_bbox in sorted(candidates, reverse=True)[:2]:
        if any(_iou(bbox, seal.bbox) > 0.3 for seal in seals):
            continue
        png = _transparent_crop(image, mask, bbox, core_bbox)
        if png:
            seals.append(SealImage(page_index=page_index, png=png, bbox=bbox))
    return tuple(seals)


def _red_mask(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]
    hsv_red = ((h <= 12) | (h >= 165)) & (s >= 60) & (v >= 70)
    return cast(
        NDArray[np.uint8],
        hsv_red.astype(np.uint8) * 255,
    )


def _looks_like_seal(
    x: int, y: int, w: int, h: int, area: float, image_width: int, image_height: int
) -> bool:
    box_area = w * h
    if box_area < image_width * image_height * 0.006:
        return False
    if box_area > image_width * image_height * 0.15:
        return False
    ratio = w / max(1, h)
    if not 0.65 <= ratio <= 1.55:
        return False
    if y < image_height * 0.35:
        return False
    return area > box_area * 0.08


def _expanded_bbox(x: int, y: int, w: int, h: int, image_width: int, image_height: int) -> BBox:
    pad = max(16, int(max(w, h) * 0.12))
    return (
        max(0, x - pad),
        max(0, y - pad),
        min(image_width, x + w + pad),
        min(image_height, y + h + pad),
    )


def _transparent_crop(
    image: NDArray[np.uint8], mask: NDArray[np.uint8], bbox: BBox, core_bbox: BBox
) -> bytes:
    x1, y1, x2, y2 = bbox
    crop = image[y1:y2, x1:x2]
    alpha = mask[y1:y2, x1:x2]
    if crop.size == 0 or int(np.count_nonzero(alpha)) == 0:
        return b""
    bgra = np.zeros((crop.shape[0], crop.shape[1], 4), dtype=np.uint8)
    bgra[:, :, 0] = 55
    bgra[:, :, 1] = 75
    bgra[:, :, 2] = 230
    alpha_mask = cast(
        NDArray[np.uint8],
        cv2.dilate(alpha, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1),
    )
    height, width = alpha_mask.shape
    alpha_mask = cast(
        NDArray[np.uint8],
        cv2.bitwise_and(alpha_mask, _ellipse_mask((height, width), bbox, core_bbox)),
    )
    bgra[:, :, 3] = cv2.GaussianBlur(alpha_mask, (3, 3), 0)
    ok, encoded = cv2.imencode(".png", bgra)
    return bytes(encoded) if ok else b""


def _ellipse_mask(shape: tuple[int, int], bbox: BBox, core_bbox: BBox) -> NDArray[np.uint8]:
    x1, y1, _, _ = bbox
    cx1, cy1, cx2, cy2 = core_bbox
    center = ((cx1 + cx2) // 2 - x1, (cy1 + cy2) // 2 - y1)
    axes = (max(1, (cx2 - cx1) // 2 + 4), max(1, (cy2 - cy1) // 2 + 4))
    result = np.zeros(shape, dtype=np.uint8)
    cv2.ellipse(result, center, axes, 0.0, 0.0, 360.0, (255,), -1)
    return result


def _iou(a: BBox, b: BBox) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if intersection == 0:
        return 0.0
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return intersection / (area_a + area_b - intersection)
