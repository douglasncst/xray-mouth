"""Synthetic demo data for documentation and safe evaluation."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from .analysis import dataset_report


def _gradient_image(width: int = 512, height: int = 256) -> Image.Image:
    image = Image.new("L", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            radial = ((x - width / 2) ** 2 + (y - height / 2) ** 2) ** 0.5
            base = 210 - min(radial / 1.8, 170)
            pixels[x, y] = max(0, min(255, round(base)))
    draw = ImageDraw.Draw(image)
    for center_x in (140, 205, 270, 335, 400):
        draw.rounded_rectangle(
            (center_x - 22, 52, center_x + 22, 205),
            radius=18,
            outline=235,
            width=5,
        )
        draw.line((center_x, 115, center_x - 10, 197), fill=225, width=3)
        draw.line((center_x, 115, center_x + 10, 197), fill=225, width=3)
    return image


def create_demo(directory: Path) -> dict[str, object]:
    """Create synthetic images and a report without using clinical data."""

    directory.mkdir(parents=True, exist_ok=True)
    _gradient_image().save(directory / "synthetic_dental_xray.png")
    Image.new("L", (256, 128), color=2).save(directory / "synthetic_underexposed.png")
    Image.new("L", (256, 128), color=253).save(directory / "synthetic_overexposed.png")
    report = dataset_report(directory)
    report_path = directory / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
