from __future__ import annotations

import os
from pathlib import Path

import pytest
from PIL import Image

from xray_mouth.cli import main
from xray_mouth.config import WorkflowConfig
from xray_mouth.devices.folder import FolderImageSource
from xray_mouth.domain import DEFAULT_PROTOCOL
from xray_mouth.exceptions import ImageIntegrityError, InputValidationError
from xray_mouth.imaging import fit_with_padding, map_radiographs, parse_slot_prefix, verify_image
from xray_mouth.workflow import create_demo_images, patient_directory_slug, run_workflow


@pytest.mark.parametrize("contrast", [0, -1, float("nan"), float("inf"), -float("inf")])
def test_invalid_contrast_rejected_by_api_and_cli(tmp_path: Path, contrast: float) -> None:
    with pytest.raises(InputValidationError, match="Contrast"):
        WorkflowConfig(tmp_path, tmp_path / "out", "Synthetic", contrast=contrast)
    assert (
        main(
            ["series", "--patient", "Synthetic", "--input", str(tmp_path), f"--contrast={contrast}"]
        )
        == 1
    )
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    "patient",
    ["", "   ", "Alice\nSeries status: COMPLETE", "A\x00B", "A" * 201, "A\u2028B", "A\x7fB"],
)
def test_patient_validation_before_side_effects(tmp_path: Path, patient: str) -> None:
    with pytest.raises(InputValidationError, match="Patient name"):
        run_workflow(WorkflowConfig(tmp_path / "demo", tmp_path / "out", patient, demo=True))
    assert list(tmp_path.iterdir()) == []


def test_unicode_prefixes_are_not_ascii_slots() -> None:
    assert parse_slot_prefix(Path("٠١_radiograph.png")) is None


def test_small_image_fills_slot_without_stretching() -> None:
    fitted = fit_with_padding(Image.new("RGB", (10, 20), "white"), (200, 200))
    assert fitted.getpixel((50, 0)) == (255, 255, 255)
    assert fitted.getpixel((149, 199)) == (255, 255, 255)
    assert fitted.getpixel((49, 100)) == (0, 0, 0)
    assert fitted.getpixel((150, 100)) == (0, 0, 0)


@pytest.mark.parametrize("filename", ["01_simulated.png", "01_patient.png", "notes.txt"])
def test_demo_rejects_nonempty_folder_without_modifying_files(
    tmp_path: Path, filename: str
) -> None:
    existing = tmp_path / filename
    existing.write_bytes(b"existing patient data")
    with pytest.raises(InputValidationError, match="empty input"):
        create_demo_images(tmp_path)
    assert existing.read_bytes() == b"existing patient data"
    assert list(tmp_path.iterdir()) == [existing]


def test_demo_uses_only_generated_images(tmp_path: Path) -> None:
    create_demo_images(tmp_path)
    assert len(map_radiographs(FolderImageSource(tmp_path).image_paths(), DEFAULT_PROTOCOL)) == 14


def test_truncated_bmp_rejected_by_full_decode(tmp_path: Path) -> None:
    path = tmp_path / "01_truncated.bmp"
    Image.new("RGB", (100, 100), "white").save(path)
    path.write_bytes(path.read_bytes()[:100])
    with pytest.raises(ImageIntegrityError, match="Cannot read image"):
        verify_image(path)


def test_multipage_tiff_is_not_silently_reduced_to_first_page(tmp_path: Path) -> None:
    path = tmp_path / "01_multi.tiff"
    Image.new("L", (10, 10)).save(path, save_all=True, append_images=[Image.new("L", (10, 10))])
    with pytest.raises(ImageIntegrityError, match="Multipage"):
        verify_image(path)


def test_high_bit_depth_is_not_silently_clipped(tmp_path: Path) -> None:
    path = tmp_path / "01_16bit.tiff"
    Image.new("I;16", (10, 10), 4096).save(path)
    with pytest.raises(ImageIntegrityError, match="High-bit-depth"):
        verify_image(path)


def test_decompression_bomb_warning_becomes_domain_error(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "01_large.png"
    Image.new("L", (11, 10)).save(path)
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 100)
    with pytest.raises(ImageIntegrityError, match="oversized"):
        verify_image(path)


def test_symlinked_image_is_rejected(tmp_path: Path) -> None:
    original = tmp_path / "original.png"
    Image.new("L", (10, 10)).save(original)
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / "01_link.png").symlink_to(original)
    with pytest.raises(InputValidationError, match="Symlinked"):
        FolderImageSource(folder).image_paths()


def test_folder_filters_extensions_and_subdirectories(tmp_path: Path) -> None:
    accepted = tmp_path / "01_UPPER.PNG"
    accepted.touch()
    (tmp_path / "02_ignore.txt").touch()
    (tmp_path / "03_folder.png").mkdir()
    assert FolderImageSource(tmp_path).image_paths() == [accepted]


def test_long_unicode_slug_is_bounded_and_safe() -> None:
    slug = patient_directory_slug("口" * 200)
    assert len(slug.encode("utf-8")) <= 120
    assert slug and not slug.endswith((" ", "."))


def test_identical_files_cannot_claim_different_slots(tmp_path: Path) -> None:
    first, second = tmp_path / "01_source.png", tmp_path / "02_copy.png"
    Image.new("L", (10, 10)).save(first)
    second.write_bytes(first.read_bytes())
    with pytest.raises(InputValidationError, match="Identical image files claim slots 01 and 02"):
        map_radiographs([first, second], DEFAULT_PROTOCOL)


@pytest.mark.parametrize(
    "extension,format_name",
    [
        ("png", "PNG"),
        ("jpg", "JPEG"),
        ("jpeg", "JPEG"),
        ("tif", "TIFF"),
        ("tiff", "TIFF"),
        ("bmp", "BMP"),
    ],
)
def test_all_documented_image_formats_decode(
    tmp_path: Path, extension: str, format_name: str
) -> None:
    path = tmp_path / f"01_image.{extension}"
    Image.new("RGB", (10, 20), "white").save(path, format=format_name)
    assert map_radiographs([path], DEFAULT_PROTOCOL)[1].path == path


def test_unsupported_content_cannot_hide_behind_png_extension(tmp_path: Path) -> None:
    path = tmp_path / "01_disguised.png"
    Image.new("RGB", (10, 20)).save(path, format="GIF")
    with pytest.raises(ImageIntegrityError, match="Unsupported image content"):
        verify_image(path)


def test_transparent_pixels_render_against_black_without_modifying_source(tmp_path: Path) -> None:
    from xray_mouth.imaging import load_render_image

    path = tmp_path / "01_alpha.png"
    Image.new("RGBA", (10, 20), (255, 255, 255, 0)).save(path)
    before = path.read_bytes()
    assert load_render_image(path).getpixel((0, 0)) == (0, 0, 0)
    assert path.read_bytes() == before


def test_duplicate_slot_message_escapes_filename_controls(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("Windows forbids control characters in filenames")
    first, second = tmp_path / "01_scan\nstatus.png", tmp_path / "01_copy.png"
    Image.new("L", (10, 10)).save(first)
    Image.new("L", (10, 10), 100).save(second)
    with pytest.raises(InputValidationError) as error:
        map_radiographs([first, second], DEFAULT_PROTOCOL)
    assert "\\nstatus" in str(error.value)
    assert "\n" not in str(error.value)
