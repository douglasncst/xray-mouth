from __future__ import annotations

from PIL import ImageDraw, ImageFont

from xray_mouth.domain import DEFAULT_PROTOCOL, Exam
from xray_mouth.layout import build_series_image, default_geometry


def test_slot_labels_and_long_patient_text_stay_inside_regions(monkeypatch) -> None:
    original = ImageDraw.ImageDraw.text
    calls = []

    def record(self, xy, text, *args, **kwargs):
        calls.append((xy, self.textbbox(xy, text, font=kwargs["font"]), text))
        return original(self, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", record)
    size = (1754, 1240)
    build_series_image(
        {},
        Exam("Synthetic " * 20, metadata={str(i): "value" for i in range(20)}),
        DEFAULT_PROTOCOL,
        size,
    )
    geometry = default_geometry()
    for slot in DEFAULT_PROTOCOL.slots:
        x, _, width, _ = geometry.slots[slot.number].pixels(size)
        label = next(
            call
            for call in calls
            if call[2].startswith(f"{slot.prefix} ") and "MISSING" not in call[2]
        )
        assert x <= label[1][0] <= label[1][2] <= x + width
    cx, cy, cw, ch = geometry.center.pixels(size)
    central = [
        call
        for call in calls
        if call[2] and call[2][:2] not in {slot.prefix for slot in DEFAULT_PROTOCOL.slots}
    ]
    assert any("..." in call[2] for call in central)
    for _, box, _ in central:
        assert cx <= box[0] <= box[2] <= cx + cw
        assert cy <= box[1] <= box[3] <= cy + ch


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
