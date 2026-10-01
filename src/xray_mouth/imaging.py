from __future__ import annotations

import re
import warnings
from hashlib import file_digest
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError

from xray_mouth.domain import Protocol, Radiograph
from xray_mouth.exceptions import DuplicateSlotError, ImageIntegrityError, InputValidationError

PREFIX_PATTERN = re.compile(r"^([0-9]{2})(?:[_-]|$)")


def parse_slot_prefix(path: Path) -> int | None:
    """Return a two-digit filename prefix, or None when a file is unrelated."""
    match = PREFIX_PATTERN.match(path.stem)
    return int(match.group(1)) if match else None


def map_radiographs(paths: list[Path], protocol: Protocol) -> dict[int, Radiograph]:
    mapped: dict[int, Radiograph] = {}
    fingerprints: dict[bytes, int] = {}
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
        with path.open("rb") as stream:
            fingerprint = file_digest(stream, "sha256").digest()
        if fingerprint in fingerprints:
            raise DuplicateSlotError(
                f"Identical image files claim slots {fingerprints[fingerprint]:02d} "
                f"and {prefix:02d}."
            )
        fingerprints[fingerprint] = prefix
        slot = protocol.slot_for(prefix)
        assert slot is not None
        mapped[prefix] = Radiograph(slot=slot, path=path)
    return mapped


def verify_image(path: Path) -> None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                if image.format not in {"PNG", "JPEG", "TIFF", "BMP"}:
                    raise ImageIntegrityError(
                        "Unsupported image content; use PNG, JPEG, TIFF or BMP."
                    )
                if getattr(image, "n_frames", 1) != 1:
                    raise ImageIntegrityError("Multipage images are unsupported; export each page.")
                if image.mode.startswith("I") or image.mode == "F":
                    raise ImageIntegrityError(
                        "High-bit-depth images require an explicit 8-bit export before import."
                    )
                image.verify()
            # verify() checks structure; load() also catches truncated pixel data.
            with Image.open(path) as image:
                image.load()
    except (
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombWarning,
        Image.DecompressionBombError,
        ValueError,
    ) as error:
        raise ImageIntegrityError(
            "Cannot read image: invalid, truncated or oversized data."
        ) from error


def load_render_image(path: Path, contrast: float = 1.0) -> Image.Image:
    """Load a display copy; source files are never written or altered."""
    try:
        verify_image(path)
        with Image.open(path) as source:
            oriented = ImageOps.exif_transpose(source)
            if oriented.mode in {"RGBA", "LA"} or "transparency" in oriented.info:
                rgba = oriented.convert("RGBA")
                oriented = Image.alpha_composite(Image.new("RGBA", rgba.size, "black"), rgba)
            image = oriented.convert("L")
            if contrast != 1.0:
                image = ImageEnhance.Contrast(image).enhance(contrast)
            return image.convert("RGB")
    except (OSError, UnidentifiedImageError, ValueError) as error:
        raise ImageIntegrityError("Cannot render image: invalid image data.") from error


def fit_with_padding(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Fit an image inside size without stretching, using black letterboxing."""
    canvas = Image.new("RGB", size, "black")
    copy = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
    offset = ((size[0] - copy.width) // 2, (size[1] - copy.height) // 2)
    canvas.paste(copy, offset)
    return canvas
