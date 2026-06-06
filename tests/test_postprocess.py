"""OCR 后处理：过滤公章碎字并修正常见误识别。"""

from pdftodoc.core.ocr import OcrCell, OcrLine, OcrPage, OcrTable, SealImage
from pdftodoc.core.ocr.postprocess import clean_ocr_lines, repair_cross_page_fields


def test_clean_ocr_lines_filters_seal_fragments_and_fixes_typos() -> None:
    lines = (
        OcrLine("承诺单位（盖章)：西安安路信铁路拉术有", (100, 100, 300, 120)),
        OcrLine("公司", (100, 125, 140, 145)),
        OcrLine("安", (180, 180, 200, 200)),
        OcrLine("anlux@126. com", (100, 230, 220, 250)),
        OcrLine("特定规则一铁路轨道信号在线测量仪", (100, 260, 360, 280)),
    )
    seals = (SealImage(0, b"png", (150, 150, 230, 230)),)

    cleaned = clean_ocr_lines(lines, seals)

    assert [line.text for line in cleaned] == [
        "承诺单位（盖章)：西安安路信铁路技术有限公司",
        "anlux@126.com",
        "特定规则—铁路轨道信号在线测量仪",
    ]


def test_repair_cross_page_fields_completes_occluded_company_name() -> None:
    pages = (
        OcrPage(
            0,
            text_lines=(OcrLine("承诺单位（盖章)：西安安路信铁路技术有", (1, 1, 2, 2)),),
        ),
        OcrPage(
            1,
            text_lines=(OcrLine("西安安路信铁路技术有限公司", (1, 1, 2, 2)),),
            tables=(
                OcrTable(
                    bbox=(0, 0, 10, 10),
                    column_count=1,
                    rows=((OcrCell("西安安路信铁路技术有限公司"),),),
                ),
            ),
        ),
    )

    repaired = repair_cross_page_fields(pages)

    assert repaired[0].text_lines[0].text == "承诺单位（盖章)：西安安路信铁路技术有限公司"
    assert repaired[0].lines == ("承诺单位（盖章)：西安安路信铁路技术有限公司",)
