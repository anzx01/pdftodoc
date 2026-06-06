"""OCR 文本后处理：过滤公章碎字，修正常见误识别。"""

import re
from collections.abc import Sequence
from dataclasses import replace

from pdftodoc.core.ocr import BBox, OcrLine, OcrPage, SealImage

_REPLACEMENTS = {
    "拉术": "技术",
    "anlux@126. com": "anlux@126.com",
    "特定规则一铁路": "特定规则—铁路",
    "特定规则一轨道": "特定规则—轨道",
}


def clean_ocr_lines(lines: tuple[OcrLine, ...], seals: tuple[SealImage, ...]) -> tuple[OcrLine, ...]:
    """清洗 OCR 行，尽量避免印章内容和明显错字进入可编辑正文。"""
    cleaned: list[OcrLine] = []
    for line in lines:
        text = _clean_text(line.text)
        if not text or _is_seal_fragment(text, line.box, seals):
            continue
        cleaned.append(OcrLine(text=text, box=line.box))
    return tuple(_merge_split_company(cleaned))


def repair_cross_page_fields(pages: Sequence[OcrPage]) -> tuple[OcrPage, ...]:
    """Use complete fields found elsewhere in the same document to repair occluded text."""
    company = _find_company_name(pages)
    if not company:
        return tuple(pages)

    repaired: list[OcrPage] = []
    for page in pages:
        text_lines = tuple(_repair_company_line(line, company) for line in page.text_lines)
        repaired.append(replace(page, text_lines=text_lines, lines=tuple(line.text for line in text_lines)))
    return tuple(repaired)


def _clean_text(text: str) -> str:
    value = text.strip()
    for wrong, right in _REPLACEMENTS.items():
        value = value.replace(wrong, right)
    return value


def _find_company_name(pages: Sequence[OcrPage]) -> str:
    for text in _iter_texts(pages):
        match = re.search(r"[\u4e00-\u9fffA-Za-z0-9（）()·]{4,40}有限公司", text)
        if match:
            return match.group(0)
    return ""


def _iter_texts(pages: Sequence[OcrPage]) -> list[str]:
    texts: list[str] = []
    for page in pages:
        texts.extend(line.text for line in page.text_lines)
        for table in page.tables:
            for row in table.rows:
                texts.extend(cell.text for cell in row if cell.text)
    return texts


def _repair_company_line(line: OcrLine, company: str) -> OcrLine:
    if "盖章" not in line.text and "承诺单位" not in line.text:
        return line
    separator_at = max(line.text.rfind("："), line.text.rfind(":"))
    if separator_at < 0:
        return line
    prefix = line.text[separator_at + 1 :].strip()
    if len(prefix) < 4 or not company.startswith(prefix):
        return line
    return OcrLine(text=f"{line.text[: separator_at + 1]}{company}", box=line.box)


def _is_seal_fragment(text: str, box: BBox | None, seals: tuple[SealImage, ...]) -> bool:
    if box is None or len(text) > 2:
        return False
    cx, cy = _center(box)
    return any(_inside(cx, cy, seal.bbox) for seal in seals)


def _merge_split_company(lines: list[OcrLine]) -> list[OcrLine]:
    merged: list[OcrLine] = []
    skip_next = False
    for idx, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
        if idx + 1 < len(lines) and line.text.endswith("有") and lines[idx + 1].text == "公司":
            merged.append(OcrLine(text=f"{line.text}限公司", box=line.box))
            skip_next = True
        else:
            merged.append(line)
    return merged


def _center(box: BBox) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def _inside(x: int, y: int, box: BBox) -> bool:
    x1, y1, x2, y2 = box
    return x1 <= x <= x2 and y1 <= y <= y2
