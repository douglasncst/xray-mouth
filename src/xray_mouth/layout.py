from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from xray_mouth.domain import Exam, Protocol, Radiograph
from xray_mouth.imaging import fit_with_padding, load_render_image


@dataclass(frozen=True, slots=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    def pixels(self, canvas: tuple[int, int]) -> tuple[int, int, int, int]:
        width, height = canvas
        return (
            int(self.x * width),
            int(self.y * height),
            int(self.width * width),
            int(self.height * height),
        )


@dataclass(frozen=True, slots=True)
class LayoutGeometry:
    slots: dict[int, Rect]
    center: Rect


def default_geometry() -> LayoutGeometry:
    top = {number: Rect(0.05 + (number - 1) * 0.19, 0.06, 0.17, 0.27) for number in range(1, 6)}
    lower = {
        number: Rect(0.05 + (number - 10) * 0.19, 0.72, 0.17, 0.22) for number in range(10, 15)
    }
    sides = {
        6: Rect(0.02, 0.40, 0.10, 0.13),
        7: Rect(0.02, 0.55, 0.10, 0.13),
        8: Rect(0.88, 0.40, 0.10, 0.13),
        9: Rect(0.88, 0.55, 0.10, 0.13),
    }
    return LayoutGeometry(slots=top | lower | sides, center=Rect(0.20, 0.41, 0.60, 0.22))


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default(size=size)


def build_series_image(
    radiographs: dict[int, Radiograph],
    exam: Exam,
    protocol: Protocol,
    size: tuple[int, int],
    contrast: float = 1.0,
) -> Image.Image:
    geometry = default_geometry()
    if set(geometry.slots) != {slot.number for slot in protocol.slots}:
        raise ValueError("Default layout geometry does not cover the selected protocol.")
    canvas = Image.new("RGB", size, "black")
    draw = ImageDraw.Draw(canvas)
    label_font = _font(max(13, size[0] // 110))
    detail_font = _font(max(14, size[0] // 85))
    for slot in protocol.slots:
        x, y, width, height = geometry.slots[slot.number].pixels(size)
        if radiograph := radiographs.get(slot.number):
            visual = fit_with_padding(load_render_image(radiograph.path, contrast), (width, height))
            canvas.paste(visual, (x, y))
        else:
            draw.rectangle(
                (x, y, x + width, y + height), outline=(110, 110, 110), width=max(1, size[0] // 900)
            )
            message = f"{slot.prefix}  MISSING"
            box = draw.textbbox((0, 0), message, font=label_font)
            draw.text(
                (x + (width - (box[2] - box[0])) / 2, y + height / 2),
                message,
                fill=(165, 165, 165),
                font=label_font,
            )
        draw.text(
            (x, max(0, y - label_font.size - 4)),
            f"{slot.prefix} {slot.label}",
            fill=(205, 205, 205),
            font=label_font,
        )
    cx, cy, cw, ch = geometry.center.pixels(size)
    draw.rectangle((cx, cy, cx + cw, cy + ch), outline=(95, 95, 95), width=max(1, size[0] // 1000))
    title = "SIMULATED / NON-DIAGNOSTIC" if exam.demo else "PERIAPICAL SERIES"
    lines = [title, exam.patient_name, f"Generated: {exam.created_at.strftime('%Y-%m-%d %H:%M')}"]
    if exam.metadata:
        lines.extend(f"{key}: {value}" for key, value in exam.metadata.items())
    line_height = detail_font.size + 7
    start_y = cy + (ch - line_height * len(lines)) // 2
    for index, line in enumerate(lines):
        box = draw.textbbox((0, 0), line, font=detail_font)
        draw.text(
            (cx + (cw - (box[2] - box[0])) / 2, start_y + index * line_height),
            line,
            fill="white",
            font=detail_font,
        )
    return canvas
