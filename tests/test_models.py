"""模型层测试：ProgressEvent.percent 边界行为。"""

from pdftodoc.models.enums import ConversionStage
from pdftodoc.models.progress import ProgressEvent


def test_percent_normal() -> None:
    ev = ProgressEvent("t", ConversionStage.RENDERING, 3, 10)
    assert ev.percent == 30.0


def test_percent_zero_total() -> None:
    ev = ProgressEvent("t", ConversionStage.PENDING, 0, 0)
    assert ev.percent == 0.0


def test_percent_caps_at_100() -> None:
    ev = ProgressEvent("t", ConversionStage.DONE, 12, 10)
    assert ev.percent == 100.0
