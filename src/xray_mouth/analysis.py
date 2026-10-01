"""Image inspection and dataset reporting."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageStat, UnidentifiedImageError

SUPPORTED_EXTENSIONS = {".bmp", ".dcm", ".dicom", ".jpeg", ".jpg", ".png", ".tif", ".tiff"}
SENSITIVE_FILENAME_PATTERNS = (
    re.compile(r"\b(patient|paciente|name|nome|dob|birth|nascimento)\b", re.IGNORECASE),
    re.compile(r"\b\d{8,}\b"),
    re.compile(r"\b\d{4}[-_]\d{2}[-_]\d{2}\b"),
)


@dataclass(frozen=True)
class ImageReport:
    """Serializable inspection result for one image."""

    path: str
    sha256: str
    format: str
    width: int
    height: int
    mode: str
    mean_intensity: float
    intensity_stddev: float
    dark_fraction: float
    bright_fraction: float
    edge_energy: float
    filename_privacy_warning: bool
    warnings: list[str]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def filename_may_contain_identifier(path: Path) -> bool:
    normalized = re.sub(r"[^A-Za-z0-9-]", " ", path.stem)
    return any(pattern.search(normalized) for pattern in SENSITIVE_FILENAME_PATTERNS)


def _edge_energy(pixels: list[int], width: int, height: int) -> float:
    if width < 2 or height < 2:
        return 0.0
    total = 0
    comparisons = 0
    for y in range(height):
        row = y * width
        for x in range(width - 1):
            total += abs(pixels[row + x + 1] - pixels[row + x])
            comparisons += 1
    for y in range(height - 1):
        row = y * width
        next_row = (y + 1) * width
        for x in range(width):
            total += abs(pixels[next_row + x] - pixels[row + x])
            comparisons += 1
    return round(total / comparisons, 3) if comparisons else 0.0


def inspect_image(path: Path) -> ImageReport:
    """Inspect a raster image without modifying it."""

    privacy_warning = filename_may_contain_identifier(path)
    warnings: list[str] = []
    if privacy_warning:
        warnings.append("filename may contain a patient identifier")

    try:
        with Image.open(path) as source:
            image_format = source.format or path.suffix.removeprefix(".").upper()
            grayscale = source.convert("L")
            width, height = grayscale.size
            pixels = list(grayscale.get_flattened_data())
            stats = ImageStat.Stat(grayscale)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"unsupported or unreadable image: {path}") from exc

    pixel_count = max(len(pixels), 1)
    dark_fraction = sum(value <= 5 for value in pixels) / pixel_count
    bright_fraction = sum(value >= 250 for value in pixels) / pixel_count
    stddev = float(stats.stddev[0])
    if stddev < 8:
        warnings.append("very low contrast")
    if dark_fraction > 0.8:
        warnings.append("mostly dark image")
    if bright_fraction > 0.8:
        warnings.append("mostly bright image")

    return ImageReport(
        path=str(path),
        sha256=sha256_file(path),
        format=image_format,
        width=width,
        height=height,
        mode=source.mode,
        mean_intensity=round(float(stats.mean[0]), 3),
        intensity_stddev=round(stddev, 3),
        dark_fraction=round(dark_fraction, 6),
        bright_fraction=round(bright_fraction, 6),
        edge_energy=_edge_energy(pixels, width, height),
        filename_privacy_warning=privacy_warning,
        warnings=warnings,
    )


def iter_images(root: Path, recursive: bool = False) -> list[Path]:
    if root.is_file():
        return [root]
    pattern = "**/*" if recursive else "*"
    return sorted(
        path
        for path in root.glob(pattern)
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def dataset_report(root: Path, recursive: bool = False) -> dict[str, object]:
    """Build a JSON-ready report. DICOM files are inventoried for anonymization."""

    items: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    dicom_files = 0
    for path in iter_images(root, recursive=recursive):
        if path.suffix.lower() in {".dcm", ".dicom"}:
            dicom_files += 1
            items.append(
                {
                    "path": str(path),
                    "sha256": sha256_file(path),
                    "format": "DICOM",
                    "filename_privacy_warning": filename_may_contain_identifier(path),
                    "warnings": ["run the anonymize command before sharing"],
                }
            )
            continue
        try:
            items.append(asdict(inspect_image(path)))
        except ValueError as exc:
            errors.append({"path": str(path), "error": str(exc)})

    numeric_stddevs = [
        float(item["intensity_stddev"]) for item in items if "intensity_stddev" in item
    ]
    return {
        "schema_version": "1.0",
        "root": str(root),
        "file_count": len(items),
        "dicom_file_count": dicom_files,
        "privacy_warning_count": sum(bool(item["filename_privacy_warning"]) for item in items),
        "mean_intensity_stddev": round(math.fsum(numeric_stddevs) / len(numeric_stddevs), 3)
        if numeric_stddevs
        else None,
        "items": items,
        "errors": errors,
    }
