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
    aspect_ratio: float | None = None

    def pixels(self, canvas: tuple[int, int]) -> tuple[int, int, int, int]:
        width, height = canvas
        pixel_height = round(self.height * height)
        pixel_width = (
            round(pixel_height * self.aspect_ratio)
            if self.aspect_ratio is not None
            else round(self.width * width)
        )
        return (round(self.x * width), round(self.y * height), pixel_width, pixel_height)


@dataclass(frozen=True, slots=True)
class LayoutGeometry:
    slots: dict[int, Rect]
    center: Rect


def default_geometry() -> LayoutGeometry:
    """Return the Green-Smile-inspired 14-film mount.

    All 14 film frames use the same normalized dimensions. On the A4-landscape
    canvases shipped by the project this produces a physical frame ratio of
    approximately 3:4 (portrait) without stretching the source radiographs.
    """
    film_width = 0.0955
    film_height = 0.18

    side_y = (0.18, 0.37, 0.56, 0.75)
    left_x = 0.035
    right_x = 1.0 - left_x - film_width

    upper_center_y = 0.245
    lower_center_y = 0.585
    center_x = (0.312, 0.45225, 0.5925)

    slots = {
        # Patient right: upper posterior through lower posterior.
        1: Rect(left_x, side_y[0], film_width, film_height, 3 / 4),
        6: Rect(left_x, side_y[1], film_width, film_height, 3 / 4),
        7: Rect(left_x, side_y[2], film_width, film_height, 3 / 4),
        10: Rect(left_x, side_y[3], film_width, film_height, 3 / 4),
        # Maxillary anterior row.
        2: Rect(center_x[0], upper_center_y, film_width, film_height, 3 / 4),
        3: Rect(center_x[1], upper_center_y, film_width, film_height, 3 / 4),
        4: Rect(center_x[2], upper_center_y, film_width, film_height, 3 / 4),
        # Mandibular anterior row.
        11: Rect(center_x[0], lower_center_y, film_width, film_height, 3 / 4),
        12: Rect(center_x[1], lower_center_y, film_width, film_height, 3 / 4),
        13: Rect(center_x[2], lower_center_y, film_width, film_height, 3 / 4),
        # Patient left: upper posterior through lower posterior.
        5: Rect(right_x, side_y[0], film_width, film_height, 3 / 4),
        8: Rect(right_x, side_y[1], film_width, film_height, 3 / 4),
        9: Rect(right_x, side_y[2], film_width, film_height, 3 / 4),
        14: Rect(right_x, side_y[3], film_width, film_height, 3 / 4),
    }
    # Reserved visual breathing room between the central upper/lower rows.
    return LayoutGeometry(slots=slots, center=Rect(0.20, 0.455, 0.60, 0.10))


def _font(size: int, *, italic: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "DejaVuSans-Oblique.ttf" if italic else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size=size)
    except OSError:
        return ImageFont.load_default()


def _fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    width: int,
) -> str:
    """Keep display text inside its region; full information remains in the report."""
    try:
        draw.textbbox((0, 0), text, font=font)
    except UnicodeEncodeError:
        text = text.encode("latin-1", errors="replace").decode("latin-1")
    original = text
    while text:
        displayed = text if text == original else text + "..."
        box = draw.textbbox((0, 0), displayed, font=font)
        if box[2] - box[0] <= width:
            return displayed
        text = text[:-1]
    return ""


def _metadata(exam: Exam, key: str, fallback: str) -> str:
    value = exam.metadata.get(key)
    return value.strip() if value and value.strip() else fallback


def _draw_header(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    exam: Exam,
    protocol: Protocol,
) -> None:
    width, height = canvas.size
    header_height = max(72, int(height * 0.145))
    dark_green = (3, 40, 31)
    darker_green = (1, 24, 20)
    orange = (239, 111, 35)
    white = (245, 245, 245)
    muted = (205, 211, 208)

    draw.rectangle((0, 0, width, header_height), fill=darker_green)
    draw.rectangle((0, 0, int(width * 0.32), header_height), fill=dark_green)
    line_width = max(2, width // 900)
    draw.line(
        (0, header_height - line_width, width, header_height - line_width),
        fill=orange,
        width=line_width,
    )

    # Subtle dotted accent, derived from the approved Green Smile visual language.
    dot_radius = max(2, width // 700)
    dot_gap = max(dot_radius * 4, width // 180)
    start_x = int(width * 0.90)
    start_y = max(dot_radius * 3, int(header_height * 0.18))
    for row in range(3):
        for column in range(7):
            x = start_x + column * dot_gap + row * dot_radius
            y = start_y + row * dot_gap
            draw.ellipse(
                (x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius),
                fill=orange,
            )

    clinic_name = _metadata(exam, "clinic_name", "XRay Mouth")
    clinic_subtitle = _metadata(exam, "clinic_subtitle", "CLINICAL RADIOGRAPH SERIES")
    exam_label = _metadata(exam, "exam_label", protocol.name)
    exam_date = _metadata(exam, "exam_date", exam.created_at.strftime("%d/%m/%Y"))

    clinic_font = _font(max(24, width // 38))
    clinic_accent_font = _font(max(24, width // 38), italic=True)
    subtitle_font = _font(max(11, width // 95))
    detail_font = _font(max(12, width // 78))

    clinic_x = int(width * 0.045)
    clinic_y = int(header_height * 0.17)
    clinic_max_width = int(width * 0.30)

    parts = clinic_name.rsplit(" ", 1)
    if len(parts) == 2:
        prefix = _fit_text(draw, parts[0] + " ", clinic_font, clinic_max_width)
        draw.text((clinic_x, clinic_y), prefix, fill=white, font=clinic_font)
        prefix_box = draw.textbbox((clinic_x, clinic_y), prefix, font=clinic_font)
        remaining = clinic_max_width - (prefix_box[2] - prefix_box[0])
        accent = _fit_text(draw, parts[1], clinic_accent_font, max(0, remaining))
        draw.text((prefix_box[2], clinic_y), accent, fill=orange, font=clinic_accent_font)
    else:
        name = _fit_text(draw, clinic_name, clinic_font, clinic_max_width)
        draw.text((clinic_x, clinic_y), name, fill=white, font=clinic_font)

    subtitle_y = clinic_y + max(30, width // 33)
    subtitle = _fit_text(draw, clinic_subtitle.upper(), subtitle_font, clinic_max_width)
    draw.text((clinic_x, subtitle_y), subtitle, fill=muted, font=subtitle_font)

    divider_x = int(width * 0.365)
    divider_pad = int(header_height * 0.18)
    draw.line(
        (divider_x, divider_pad, divider_x, header_height - divider_pad),
        fill=orange,
        width=line_width,
    )

    info_x = int(width * 0.39)
    info_width = int(width * 0.47)
    line_height = max(20, width // 57)
    info_y = int(header_height * 0.13)
    rows = (
        f"Paciente: {exam.patient_name}",
        f"Exame: {exam_label}",
        f"Data: {exam_date}",
    )
    for index, row in enumerate(rows):
        fitted = _fit_text(draw, row, detail_font, info_width)
        draw.text(
            (info_x, info_y + index * line_height),
            fitted,
            fill=white,
            font=detail_font,
        )


def _paste_rounded_film(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    visual: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    x, y, width, height = box
    radius = max(5, min(width, height) // 13)
    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=255)
    canvas.paste(visual, (x, y), mask)
    border_width = max(1, canvas.width // 1300)
    draw.rounded_rectangle(
        (x, y, x + width - 1, y + height - 1),
        radius=radius,
        outline=(220, 220, 220),
        width=border_width,
    )


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
    _draw_header(canvas, draw, exam, protocol)

    label_font = _font(max(12, size[0] // 105))
    for slot in protocol.slots:
        box = geometry.slots[slot.number].pixels(size)
        x, y, width, height = box
        if radiograph := radiographs.get(slot.number):
            visual = fit_with_padding(load_render_image(radiograph.path, contrast), (width, height))
            _paste_rounded_film(canvas, draw, visual, box)
        else:
            radius = max(5, min(width, height) // 13)
            draw.rounded_rectangle(
                (x, y, x + width - 1, y + height - 1),
                radius=radius,
                outline=(105, 105, 105),
                width=max(1, size[0] // 1200),
            )
            message = _fit_text(draw, f"{slot.prefix} MISSING", label_font, width - 10)
            text_box = draw.textbbox((0, 0), message, font=label_font)
            text_width = text_box[2] - text_box[0]
            text_height = text_box[3] - text_box[1]
            draw.text(
                (x + (width - text_width) / 2, y + (height - text_height) / 2),
                message,
                fill=(155, 155, 155),
                font=label_font,
            )
    return canvas
