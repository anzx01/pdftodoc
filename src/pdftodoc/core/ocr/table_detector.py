"""从扫描页图像和 OCR 坐标中还原简单有线表格。"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from statistics import median
from typing import cast

import cv2
import numpy as np
from numpy.typing import NDArray

from pdftodoc.core.ocr import BBox, OcrCell, OcrLine, OcrTable


@dataclass(frozen=True)
class _Segment:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def cx(self) -> int:
        return (self.x1 + self.x2) // 2

    @property
    def cy(self) -> int:
        return (self.y1 + self.y2) // 2


def detect_tables(image: NDArray[np.uint8], lines: Sequence[OcrLine]) -> tuple[OcrTable, ...]:
    """检测页面中的有线表格，并把 OCR 文本落入单元格。"""
    if not lines:
        return ()

    horizontal, vertical = _detect_line_segments(image)
    groups = _group_horizontal_lines(horizontal)
    tables: list[OcrTable] = []
    for group in groups:
        table = _build_table(group, vertical, lines)
        if table is not None:
            tables.append(table)
    return tuple(tables)


def _detect_line_segments(image: NDArray[np.uint8]) -> tuple[list[_Segment], list[_Segment]]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    binary = cv2.adaptiveThreshold(
        ~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 25, -2
    )
    height, width = gray.shape

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(30, width // 30), 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(10, height // 110)))
    h_mask = cast(
        NDArray[np.uint8],
        cv2.dilate(cv2.erode(binary, h_kernel, iterations=1), h_kernel, iterations=1),
    )
    v_mask = cast(
        NDArray[np.uint8],
        cv2.dilate(cv2.erode(binary, v_kernel, iterations=1), v_kernel, iterations=1),
    )

    h_min_width = max(90, width // 8)
    v_min_height = max(20, height // 70)
    horizontal = [
        segment
        for segment in _segments_from_mask(h_mask)
        if segment.width >= h_min_width and segment.height <= 6
    ]
    vertical = [
        segment
        for segment in _segments_from_mask(v_mask)
        if segment.height >= v_min_height and segment.width <= 10
    ]
    return horizontal, vertical


def _segments_from_mask(mask: NDArray[np.uint8]) -> list[_Segment]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    segments: list[_Segment] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        segments.append(_Segment(x, y, x + w, y + h))
    return segments


def _group_horizontal_lines(segments: Sequence[_Segment]) -> list[list[_Segment]]:
    groups: list[list[_Segment]] = []
    for segment in sorted(segments, key=lambda item: item.cy):
        for group in groups:
            x1 = int(median(item.x1 for item in group))
            x2 = int(median(item.x2 for item in group))
            if abs(segment.x1 - x1) <= 12 and abs(segment.x2 - x2) <= 12:
                group.append(segment)
                break
        else:
            groups.append([segment])

    table_groups: list[list[_Segment]] = []
    for group in groups:
        merged = _merge_horizontal_positions(group)
        if len(merged) >= 3 and _group_height(merged) >= 50:
            table_groups.append(merged)
    return table_groups


def _merge_horizontal_positions(segments: Sequence[_Segment]) -> list[_Segment]:
    if not segments:
        return []
    grouped: list[list[_Segment]] = []
    for segment in sorted(segments, key=lambda item: item.cy):
        if grouped and abs(segment.cy - int(median(item.cy for item in grouped[-1]))) <= 3:
            grouped[-1].append(segment)
        else:
            grouped.append([segment])

    merged: list[_Segment] = []
    for group in grouped:
        y = int(round(median(item.cy for item in group)))
        merged.append(_Segment(min(item.x1 for item in group), y, max(item.x2 for item in group), y))
    return merged


def _group_height(group: Sequence[_Segment]) -> int:
    return max(item.cy for item in group) - min(item.cy for item in group)


def _build_table(
    horizontal: Sequence[_Segment], vertical: Sequence[_Segment], lines: Sequence[OcrLine]
) -> OcrTable | None:
    y_coords = sorted(item.cy for item in horizontal)
    if len(y_coords) < 3:
        return None

    left = int(round(median(item.x1 for item in horizontal)))
    right = int(round(median(item.x2 for item in horizontal)))
    top, bottom = y_coords[0], y_coords[-1]
    if right - left < 100 or bottom - top < 50:
        return None

    relevant_vertical = [
        segment
        for segment in vertical
        if left - 12 <= segment.cx <= right + 12 and _overlap(segment.y1, segment.y2, top, bottom) > 15
    ]
    x_coords = _merge_positions([left, right, *(segment.cx for segment in relevant_vertical)])
    if len(x_coords) < 3:
        return None

    rows: list[tuple[OcrCell, ...]] = []
    row_heights: list[int] = []
    for y1, y2 in zip(y_coords, y_coords[1:], strict=False):
        row = _build_row((left, y1, right, y2), x_coords, relevant_vertical, lines)
        rows.append(tuple(row))
        row_heights.append(y2 - y1)

    if not any(cell.text for row in rows for cell in row):
        return None
    return OcrTable(
        bbox=(left, top, right, bottom),
        column_count=len(x_coords) - 1,
        rows=tuple(rows),
        column_widths=tuple(x2 - x1 for x1, x2 in zip(x_coords, x_coords[1:], strict=False)),
        row_heights=tuple(row_heights),
    )


def _build_row(
    row_box: BBox,
    x_coords: Sequence[int],
    vertical: Sequence[_Segment],
    lines: Sequence[OcrLine],
) -> list[OcrCell]:
    left, y1, right, y2 = row_box
    active = [
        index
        for index, x in enumerate(x_coords)
        if x in (left, right) or _has_vertical_boundary(x, y1, y2, vertical)
    ]
    if active[0] != 0:
        active.insert(0, 0)
    if active[-1] != len(x_coords) - 1:
        active.append(len(x_coords) - 1)

    cells: list[OcrCell] = []
    for start, end in zip(active, active[1:], strict=False):
        cell_box = (x_coords[start], y1, x_coords[end], y2)
        cells.append(OcrCell(text=_cell_text(cell_box, lines), col_span=end - start))
    return cells


def _has_vertical_boundary(x: int, y1: int, y2: int, vertical: Sequence[_Segment]) -> bool:
    row_height = max(1, y2 - y1)
    needed = max(10, int(row_height * 0.45))
    return any(abs(segment.cx - x) <= 4 and _overlap(segment.y1, segment.y2, y1, y2) >= needed for segment in vertical)


def _cell_text(cell_box: BBox, lines: Sequence[OcrLine]) -> str:
    x1, y1, x2, y2 = cell_box
    inside = [
        line
        for line in lines
        if line.box is not None and _inside(_center(line.box), (x1, y1, x2, y2), margin=2)
    ]
    return "\n".join(line.text for line in sorted(inside, key=_line_sort_key))


def _line_sort_key(line: OcrLine) -> tuple[int, int]:
    if line.box is None:
        return (0, 0)
    return (line.box[1], line.box[0])


def _center(box: BBox) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def _inside(point: tuple[int, int], box: BBox, margin: int = 0) -> bool:
    x, y = point
    x1, y1, x2, y2 = box
    return x1 - margin <= x <= x2 + margin and y1 - margin <= y <= y2 + margin


def _merge_positions(values: Iterable[int], tolerance: int = 5) -> list[int]:
    positions = sorted(values)
    if not positions:
        return []

    groups: list[list[int]] = [[positions[0]]]
    for value in positions[1:]:
        if abs(value - int(round(median(groups[-1])))) <= tolerance:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [int(round(median(group))) for group in groups]


def _overlap(a1: int, a2: int, b1: int, b2: int) -> int:
    return max(0, min(a2, b2) - max(a1, b1))
