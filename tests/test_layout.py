from __future__ import annotations

import pytest
from PIL import ImageDraw, ImageFont

from xray_mouth.domain import DEFAULT_PROTOCOL, Exam
from xray_mouth.layout import build_series_image, default_geometry


def test_header_long_text_is_clipped_inside_header(monkeypatch) -> None:
    original = ImageDraw.ImageDraw.text
    calls = []

    def record(self, xy, text, *args, **kwargs):
        calls.append((xy, self.textbbox(xy, text, font=kwargs["font"]), text))
        return original(self, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", record)
    size = (1754, 1240)
    build_series_image(
        {},
        Exam(
            "Synthetic " * 30,
            metadata={
                "clinic_name": "Green Smile Dental Radiographic Center " * 5,
                "clinic_subtitle": "Clinical radiograph series " * 10,
                "exam_label": "Periapical full-mouth series " * 10,
            },
        ),
        DEFAULT_PROTOCOL,
        size,
    )

    patient = next(call for call in calls if call[2].startswith("Paciente:"))
    exam = next(call for call in calls if call[2].startswith("Exame:"))
    assert patient[2].endswith("...")
    assert exam[2].endswith("...")

    info_x = int(size[0] * 0.39)
    info_right = info_x + int(size[0] * 0.47)
    for _, box, text in calls:
        if text.startswith(("Paciente:", "Exame:", "Data:")):
            assert info_x <= box[0] <= box[2] <= info_right


def test_all_film_frames_are_uniform_portrait_three_by_four() -> None:
    geometry = default_geometry()
    for canvas in ((800, 600), (1600, 900), (1754, 1240), (7016, 4960)):
        rectangles = [geometry.slots[number].pixels(canvas) for number in range(1, 15)]
        widths = {rectangle[2] for rectangle in rectangles}
        heights = {rectangle[3] for rectangle in rectangles}
        assert len(widths) == 1
        assert len(heights) == 1
        width = widths.pop()
        height = heights.pop()
        assert width / height == pytest.approx(3 / 4, abs=0.004)


def test_missing_truetype_font_uses_compatible_fallback(monkeypatch) -> None:
    def missing(*args, **kwargs):
        raise OSError("font unavailable")

    # The default font on Pillow >=10.1 is itself loaded by truetype(), so
    # force the longstanding bitmap fallback to exercise Pillow 10.0 behavior.
    default = (
        ImageFont.load_default_imagefont()
        if hasattr(ImageFont, "load_default_imagefont")
        else ImageFont.load_default()
    )
    monkeypatch.setattr(ImageFont, "truetype", missing)
    monkeypatch.setattr(ImageFont, "load_default", lambda: default)
    assert build_series_image({}, Exam("口" * 20), DEFAULT_PROTOCOL, (800, 600)).size == (800, 600)
