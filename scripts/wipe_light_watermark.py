"""Batch wipe pale document watermarks from PDF pages or images."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import fitz
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pdftodoc.core.ocr.watermark import wipe_light_watermark  # noqa: E402


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="PDF, image, or image directory")
    parser.add_argument("output", type=Path, help="Output directory or image path")
    parser.add_argument("--dpi", type=int, default=250, help="PDF render DPI")
    parser.add_argument("--black", type=int, default=108, help="Black point")
    parser.add_argument("--white", type=int, default=164, help="White point")
    args = parser.parse_args()

    source = args.input.resolve()
    target = args.output.resolve()
    if source.is_dir():
        wipe_dir(source, target, args.black, args.white)
    elif source.suffix.lower() == ".pdf":
        wipe_pdf(source, target, args.dpi, args.black, args.white)
    elif source.suffix.lower() in IMAGE_EXTS:
        wipe_image(source, target, args.black, args.white)
    else:
        raise SystemExit(f"Unsupported input: {source}")
    return 0


def wipe_pdf(source: Path, output_dir: Path, dpi: int, black: int, white: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(source))
    try:
        for index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False)
            image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 1:
                image = np.repeat(image, 3, axis=2)
            wiped = wipe_light_watermark(np.ascontiguousarray(image[:, :, :3]), black, white)
            out = output_dir / f"page_{index:02d}.png"
            cv2.imwrite(str(out), cv2.cvtColor(wiped, cv2.COLOR_RGB2BGR))
            print(out)
    finally:
        doc.close()


def wipe_dir(source_dir: Path, output_dir: Path, black: int, white: int) -> None:
    for source in source_dir.rglob("*"):
        if source.is_file() and source.suffix.lower() in IMAGE_EXTS:
            target = output_dir / source.relative_to(source_dir)
            wipe_image(source, target, black, white)


def wipe_image(source: Path, target: Path, black: int, white: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    image = cv2.imread(str(source), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise SystemExit(f"Cannot read image: {source}")
    wiped = _wipe_cv_image(image, black, white)
    cv2.imwrite(str(target), wiped)
    print(target)


def _wipe_cv_image(image: np.ndarray, black: int, white: int) -> np.ndarray:
    if image.ndim == 2:
        return wipe_light_watermark(image, black, white)
    if image.shape[2] == 4:
        output = image.copy()
        output[:, :, :3] = wipe_light_watermark(output[:, :, :3], black, white)
        return output
    return wipe_light_watermark(image[:, :, :3], black, white)


if __name__ == "__main__":
    raise SystemExit(main())
