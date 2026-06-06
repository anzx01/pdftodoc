import numpy as np

from pdftodoc.core.ocr.watermark import wipe_light_watermark


def test_wipe_light_watermark_preserves_dark_and_whitens_light_pixels() -> None:
    image = np.array([[[0], [108], [164], [220], [255]]], dtype=np.uint8)

    wiped = wipe_light_watermark(image, black_point=108, white_point=164)

    assert wiped.dtype == np.uint8
    assert wiped.tolist() == [[[0], [0], [255], [255], [254]]]


def test_wipe_light_watermark_keeps_shape_for_rgb_images() -> None:
    image = np.full((3, 4, 3), 220, dtype=np.uint8)

    wiped = wipe_light_watermark(image)

    assert wiped.shape == image.shape
    assert wiped.flags.c_contiguous
