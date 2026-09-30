from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from xray_mouth.cli import main
from xray_mouth.config import SUPPORTED_EXTENSIONS, WorkflowConfig
from xray_mouth.domain import DEFAULT_PROTOCOL, Exam
from xray_mouth.exceptions import DuplicateSlotError, ImageIntegrityError, InputValidationError
from xray_mouth.imaging import fit_with_padding, map_radiographs, parse_slot_prefix
from xray_mouth.layout import build_series_image, default_geometry
from xray_mouth.workflow import run_workflow, timestamped_result_directory


def image(path: Path, size: tuple[int, int] = (120, 240)) -> None:
    Image.new("L", size, color=120).save(path)


def test_prefix_parsing() -> None:
    assert parse_slot_prefix(Path("01_upper.png")) == 1
    assert parse_slot_prefix(Path("14-lower.tiff")) == 14
    assert parse_slot_prefix(Path("1_bad.png")) is None
    assert parse_slot_prefix(Path("notes.png")) is None


def test_supported_extensions() -> None:
    assert {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"} == SUPPORTED_EXTENSIONS


def test_duplicate_slot_rejected(tmp_path: Path) -> None:
    first, second = tmp_path / "01_a.png", tmp_path / "01_b.png"
    image(first)
    image(second)
    with pytest.raises(DuplicateSlotError):
        map_radiographs([first, second], DEFAULT_PROTOCOL)


def test_corrupted_image_rejected(tmp_path: Path) -> None:
    corrupt = tmp_path / "01_broken.png"
    corrupt.write_bytes(b"not an image")
    with pytest.raises(ImageIntegrityError):
        map_radiographs([corrupt], DEFAULT_PROTOCOL)


def test_output_directory_naming(tmp_path: Path) -> None:
    timestamp = datetime(2026, 9, 30, 12, 30, 45)
    assert timestamped_result_directory(tmp_path, timestamp).name == "xray-mouth-20260930-123045"


def test_aspect_ratio_is_preserved() -> None:
    result = fit_with_padding(Image.new("RGB", (100, 200), "white"), (200, 200))
    assert result.getpixel((0, 0)) == (0, 0, 0)
    assert result.getpixel((100, 100)) == (255, 255, 255)


def test_layout_covers_all_configured_slots() -> None:
    assert set(default_geometry().slots) == {slot.number for slot in DEFAULT_PROTOCOL.slots}
    image = build_series_image({}, Exam("Patient"), DEFAULT_PROTOCOL, (800, 600))
    assert image.size == (800, 600)


def test_incomplete_workflow_and_source_immutability(tmp_path: Path) -> None:
    input_dir, output_root = tmp_path / "input", tmp_path / "reports"
    input_dir.mkdir()
    source = input_dir / "01_source.png"
    image(source)
    before = source.read_bytes()
    result = run_workflow(WorkflowConfig(input_dir, output_root, "Patient"))
    assert result.missing_slots == tuple(range(2, 15))
    assert source.read_bytes() == before
    assert result.preview_path.exists() and result.pdf_path.exists() and result.report_path.exists()


def test_strict_rejects_incomplete_series(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    image(input_dir / "01_source.png")
    with pytest.raises(InputValidationError, match="Strict mode"):
        run_workflow(WorkflowConfig(input_dir, tmp_path / "out", "Patient", strict=True))


def test_demo_mode_and_pdf_report(tmp_path: Path) -> None:
    result = run_workflow(WorkflowConfig(tmp_path / "demo", tmp_path / "out", "Demo", demo=True))
    assert len(result.mapped_slots) == 14
    assert result.missing_slots == ()
    assert result.pdf_path.read_bytes().startswith(b"%PDF")
    assert "synthetic and non-diagnostic" in result.report_path.read_text(encoding="utf-8")


def test_cli_happy_and_error_paths(tmp_path: Path) -> None:
    assert (
        main(
            [
                "--patient",
                "Demo",
                "--input",
                str(tmp_path / "demo"),
                "--output-root",
                str(tmp_path / "out"),
                "--demo",
            ]
        )
        == 0
    )
    assert main(["--patient", "Demo", "--input", str(tmp_path / "missing")]) == 1
