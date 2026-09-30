from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError

from xray_mouth.domain import Protocol, Radiograph
from xray_mouth.exceptions import DuplicateSlotError, ImageIntegrityError, InputValidationError

PREFIX_PATTERN = re.compile(r"^(\d{2})(?:[_-]|$)")


def parse_slot_prefix(path: Path) -> int | None:
    """Return a two-digit filename prefix, or None when a file is unrelated."""
    match = PREFIX_PATTERN.match(path.stem)
    return int(match.group(1)) if match else None


def map_radiographs(paths: list[Path], protocol: Protocol) -> dict[int, Radiograph]:
    mapped: dict[int, Radiograph] = {}
    allowed = {slot.number for slot in protocol.slots}
    for path in paths:
        prefix = parse_slot_prefix(path)
        if prefix is None:
            continue
        if prefix not in allowed:
            raise InputValidationError(
                f"{path.name} uses slot {prefix:02d}, which is not part of the "
                f"{protocol.name} protocol."
            )
        if prefix in mapped:
            raise DuplicateSlotError(
                f"Duplicate slot {prefix:02d}: {mapped[prefix].path.name} and {path.name}"
            )
        verify_image(path)
        slot = protocol.slot_for(prefix)
        assert slot is not None
        mapped[prefix] = Radiograph(slot=slot, path=path)
    return mapped


def verify_image(path: Path) -> None:
    try:
        with Image.open(path) as image:
            image.verify()
    except (OSError, UnidentifiedImageError) as error:
        raise ImageIntegrityError(f"Cannot read image {path.name}: {error}") from error


def load_render_image(path: Path, contrast: float = 1.0) -> Image.Image:
    """Load a display copy; source files are never written or altered."""
    try:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("L")
            if contrast != 1.0:
                image = ImageEnhance.Contrast(image).enhance(contrast)
            return image.convert("RGB")
    except (OSError, UnidentifiedImageError) as error:
        raise ImageIntegrityError(f"Cannot render image {path.name}: {error}") from error


def fit_with_padding(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Fit an image inside size without stretching, using black letterboxing."""
    canvas = Image.new("RGB", size, "black")
    copy = image.copy()
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    offset = ((size[0] - copy.width) // 2, (size[1] - copy.height) // 2)
    canvas.paste(copy, offset)
    return canvas
