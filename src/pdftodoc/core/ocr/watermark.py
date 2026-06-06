"""Light watermark preprocessing for scanned document pages.

The core level-adjustment idea is adapted from SmileZXLee's
DocumentLightMarkWipeTool (MIT License, copyright 2019 Li Zhaoxiang):
https://github.com/SmileZXLee/DocumentLightMarkWipeTool
"""

import numpy as np
from numpy.typing import NDArray


def wipe_light_watermark(
    image: NDArray[np.uint8],
    black_point: int = 108,
    white_point: int = 164,
) -> NDArray[np.uint8]:
    """Push pale watermark pixels toward white while preserving dark text.

    The original tool intentionally relies on uint8 wraparound after a small
    negative level adjustment. This implementation makes that wrap explicit so
    behavior stays stable across NumPy versions.
    """
    black, white = _normalize_points(black_point, white_point)
    image_array = _as_uint8(image)
    rate = -((white - black) / 255.0) * 0.05
    diff = np.maximum(image_array.astype(np.int16) - black, 0)
    shifted = np.rint(diff * rate).astype(np.int16)
    wiped = np.mod(shifted, 256).astype(np.uint8)
    return np.ascontiguousarray(wiped)


def _normalize_points(black_point: int, white_point: int) -> tuple[int, int]:
    white = max(2, min(255, int(white_point)))
    black = max(0, min(255, int(black_point)))
    if black >= white:
        black = white - 2
    return black, white


def _as_uint8(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    if image.dtype == np.uint8:
        return image
    return np.clip(image, 0, 255).astype(np.uint8)


__all__ = ["wipe_light_watermark"]
