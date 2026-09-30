from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from xray_mouth.cli import main
from xray_mouth.config import SUPPORTED_EXTENSIONS, WorkflowConfig
from xray_mouth.domain import DEFAULT_PROTOCOL, Exam
from xray_mouth.exceptions import DuplicateSlotError, ImageIntegrityError, InputValidationError
from xray_mouth.imaging import (
    fit_with_padding,
    load_render_image,
    map_radiographs,
    parse_slot_prefix,
)
from xray_mouth.layout import build_series_image, default_geometry
from xray_mouth.workflow import patient_directory_slug, run_workflow, timestamped_result_directory


def image(path: Path, size: tuple[int, int] = (120, 240), color: int = 120) -> None:
    Image.new("L", size, color=color).save(path)


def test_protocol_has_exactly_fourteen_slots() -> None:
    assert len(DEFAULT_PROTOCOL.slots) == 14
    assert [slot.number for slot in DEFAULT_PROTOCOL.slots] == list(range(1, 15))


def test_prefix_parsing_and_unprefixed_files() -> None:
    assert parse_slot_prefix(Path("01_upper.png")) == 1
    assert parse_slot_prefix(Path("14-lower.tiff")) == 14
    assert parse_slot_prefix(Path("1_bad.png")) is None
    assert parse_slot_prefix(Path("notes.png")) is None


def test_supported_extensions() -> None:
    assert {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"} == SUPPORTED_EXTENSIONS


def test_invalid_and_duplicate_slots_are_rejected(tmp_path: Path) -> None:
    invalid = tmp_path / "15_not_in_protocol.png"
    first, second = tmp_path / "01_a.png", tmp_path / "01_b.png"
    image(invalid)
    with pytest.raises(InputValidationError, match="slot 15"):
        map_radiographs([invalid], DEFAULT_PROTOCOL)
    image(first)
    image(second)
    with pytest.raises(DuplicateSlotError, match="Duplicate slot 01"):
        map_radiographs([first, second], DEFAULT_PROTOCOL)


def test_corrupted_image_rejected(tmp_path: Path) -> None:
    corrupt = tmp_path / "01_broken.png"
    corrupt.write_bytes(b"not an image")
    with pytest.raises(ImageIntegrityError, match="Cannot read image"):
        map_radiographs([corrupt], DEFAULT_PROTOCOL)


def test_patient_slug_and_collision_handling(tmp_path: Path) -> None:
    assert patient_directory_slug("João da Silva") == "João_da_Silva"
    assert patient_directory_slug(' <>:"/\\|?* ') == "patient"
    timestamp = datetime(2026, 9, 30, 12, 30, 45)
    first = timestamped_result_directory(tmp_path, "João da Silva", timestamp)
    assert first.name == "João_da_Silva_2026-09-30_12-30-45"
    first.mkdir()
    assert timestamped_result_directory(tmp_path, "João da Silva", timestamp).name.endswith("-01")


def test_aspect_ratio_exif_and_contrast_are_render_only(tmp_path: Path) -> None:
    source = tmp_path / "01_oriented.jpg"
    original = Image.new("L", (10, 20))
    for x in range(original.width):
        for y in range(original.height):
            original.putpixel((x, y), 30 + x * 15)
    exif = Image.Exif()
    exif[274] = 6
    original.save(source, exif=exif)
    before = source.read_bytes()
    oriented = load_render_image(source)
    contrast = load_render_image(source, contrast=1.5)
    assert oriented.size == (20, 10)
    assert source.read_bytes() == before
    assert oriented.getpixel((10, 5)) != contrast.getpixel((10, 5))
    padded = fit_with_padding(Image.new("RGB", (100, 200), "white"), (200, 200))
    assert padded.getpixel((0, 0)) == (0, 0, 0)
    assert padded.getpixel((100, 100)) == (255, 255, 255)


def test_geometry_is_within_canvas_without_slot_overlap() -> None:
    geometry = default_geometry()
    assert set(geometry.slots) == {slot.number for slot in DEFAULT_PROTOCOL.slots}
    rects = list(geometry.slots.values())
    for rect in rects:
        assert 0 <= rect.x < 1 and 0 <= rect.y < 1
        assert 0 < rect.width and 0 < rect.height
        assert rect.x + rect.width <= 1 and rect.y + rect.height <= 1
        assert rect.height / rect.width >= 1.0
    for index, first in enumerate(rects):
        for second in rects[index + 1 :]:
            overlap = not (
                first.x + first.width <= second.x
                or second.x + second.width <= first.x
                or first.y + first.height <= second.y
                or second.y + second.height <= first.y
            )
            assert not overlap
    assert build_series_image({}, Exam("Patient"), DEFAULT_PROTOCOL, (800, 600)).size == (800, 600)


def test_incomplete_workflow_source_immutability_and_report(tmp_path: Path) -> None:
    input_dir, output_root = tmp_path / "input", tmp_path / "reports"
    input_dir.mkdir()
    source = input_dir / "01_source.png"
    image(source)
    (input_dir / "unrelated.png").write_bytes(b"not inspected")
    before = source.read_bytes()
    result = run_workflow(WorkflowConfig(input_dir, output_root, "João da Silva"))
    report = result.report_path.read_text(encoding="utf-8")
    assert result.missing_slots == tuple(range(2, 15))
    assert source.read_bytes() == before
    assert "Series status: INCOMPLETE" in report
    assert "01 Superior posterior right: 01_source.png" in report
    assert "02 Superior anterior right: MISSING" in report
    assert "Images received: 2" in report
    assert "Source files: NOT MODIFIED" in report
    assert "periapical_series_600dpi.png" in report
    assert result.preview_path.exists() and result.pdf_path.exists() and result.render_path.exists()


def test_strict_rejects_incomplete_series(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    image(input_dir / "01_source.png")
    with pytest.raises(InputValidationError, match="Strict mode"):
        run_workflow(WorkflowConfig(input_dir, tmp_path / "out", "Patient", strict=True))


def test_demo_mode_full_series_pdf_and_detailed_report(tmp_path: Path) -> None:
    result = run_workflow(WorkflowConfig(tmp_path / "demo", tmp_path / "out", "Demo", demo=True))
    report = result.report_path.read_text(encoding="utf-8")
    assert len(result.mapped_slots) == 14 and result.missing_slots == ()
    assert result.pdf_path.read_bytes().startswith(b"%PDF")
    assert Image.open(result.preview_path).size == (1754, 1240)
    assert Image.open(result.render_path).size == (7016, 4960)
    assert "Series status: COMPLETE" in report
    assert "Images received: 14" in report
    assert "14 Lower posterior left: 14_simulated.png" in report
    assert "Mode: DEMO / SYNTHETIC / NON-DIAGNOSTIC" in report
    assert "Patient: Demo" in report


def test_cli_happy_error_and_strict_paths(tmp_path: Path) -> None:
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
    assert main(["--patient", "Demo", "--input", str(tmp_path / "missing"), "--contrast", "0"]) == 2
