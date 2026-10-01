from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

import xray_mouth.workflow as workflow
from xray_mouth.cli import main
from xray_mouth.config import WorkflowConfig
from xray_mouth.domain import DEFAULT_PROTOCOL, Exam, Protocol, Radiograph
from xray_mouth.exceptions import ExportError, InputValidationError
from xray_mouth.reporting import write_report


def config(tmp_path: Path) -> WorkflowConfig:
    folder = tmp_path / "input"
    folder.mkdir()
    Image.new("L", (20, 40), 150).save(folder / "01_source.png")
    return WorkflowConfig(folder, tmp_path / "out", "Synthetic")


@pytest.mark.parametrize("stage", ["build_series_image", "_write_pdf", "write_report"])
def test_export_failure_cleans_only_its_own_directory(
    tmp_path: Path, monkeypatch, stage: str
) -> None:
    settings = config(tmp_path)
    settings.output_root.mkdir()
    existing = settings.output_root / "previous-export"
    existing.mkdir()
    (existing / "keep.txt").write_text("keep")
    original = (settings.input_directory / "01_source.png").read_bytes()

    def fail(*args, **kwargs):
        raise OSError("disk full /private/patient-name")

    monkeypatch.setattr(workflow, stage, fail)
    with pytest.raises(ExportError, match="permissions and disk space") as error:
        workflow.run_workflow(settings)
    assert "patient-name" not in str(error.value)
    assert list(settings.output_root.iterdir()) == [existing]
    assert (existing / "keep.txt").read_text() == "keep"
    assert (settings.input_directory / "01_source.png").read_bytes() == original


def test_output_root_file_returns_cli_error_without_traceback(tmp_path: Path, capsys) -> None:
    settings = config(tmp_path)
    settings.output_root.write_text("preserve")
    assert (
        main(
            [
                "--patient",
                "Synthetic",
                "--input",
                str(settings.input_directory),
                "--output-root",
                str(settings.output_root),
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
    assert "check permissions and disk space" in captured.err
    assert not captured.out
    assert settings.output_root.read_text() == "preserve"


def test_unsupported_protocol_fails_before_creating_demo(tmp_path: Path) -> None:
    with pytest.raises(InputValidationError, match="exactly slots"):
        workflow.run_workflow(
            WorkflowConfig(tmp_path / "input", tmp_path / "out", "Synthetic", demo=True),
            Protocol("empty", ()),
        )
    assert list(tmp_path.iterdir()) == []


def test_broken_symlink_counts_as_existing_result(tmp_path: Path) -> None:
    stamp = datetime(2026, 1, 1)
    candidate = workflow.timestamped_result_directory(tmp_path, "Synthetic", stamp)
    candidate.symlink_to(tmp_path / "missing")
    assert workflow.timestamped_result_directory(tmp_path, "Synthetic", stamp).name.endswith("-01")


def test_report_escapes_control_characters_in_source_names(tmp_path: Path) -> None:
    path = tmp_path / "report.txt"
    radiographs = {1: Radiograph(DEFAULT_PROTOCOL.slots[0], Path("01_scan\nCOMPLETE.png"))}
    write_report(
        path, Exam("Synthetic"), DEFAULT_PROTOCOL, radiographs, 1, ("a.png", "b.png", "c.pdf")
    )
    text = path.read_text()
    assert "01_scan\\u000aCOMPLETE.png" in text
    assert "\nCOMPLETE.png" not in text


def test_export_private_permissions_dpi_and_no_source_metadata(tmp_path: Path) -> None:
    settings = config(tmp_path)
    source = settings.input_directory / "01_source.png"
    exif = Image.Exif()
    exif[315] = "Private original author"
    Image.new("L", (20, 40), 150).save(source, exif=exif)
    original = source.read_bytes()
    result = workflow.run_workflow(settings)
    if os.name == "posix":
        assert result.directory.stat().st_mode & 0o777 == 0o700
    with Image.open(result.render_path) as rendered:
        assert rendered.info["dpi"] == pytest.approx((600, 600), abs=0.01)
        assert not rendered.getexif()
        # Small sources remain visible at the center of the new uniform 3:4 frame.
        x, y, width, height = default_geometry().slots[1].pixels(rendered.size)
        assert rendered.getpixel((x + width // 2, y + height // 2)) == (150, 150, 150)
    assert source.read_bytes() == original


def test_report_preserves_all_metadata_as_single_lines(tmp_path: Path) -> None:
    path = tmp_path / "report.txt"
    exam = Exam("Synthetic", metadata={"key\n": "value\r\n"})
    write_report(path, exam, DEFAULT_PROTOCOL, {}, 0, ("a.png", "b.png", "c.pdf"))
    assert "key\\u000a: value\\u000d\\u000a" in path.read_text()


def test_creation_collision_retries_without_overwriting_other_export(
    tmp_path: Path, monkeypatch
) -> None:
    settings = config(tmp_path)
    mkdir = Path.mkdir
    competitor = None

    def racing_mkdir(path, *args, **kwargs):
        nonlocal competitor
        if path.parent == settings.output_root and competitor is None:
            competitor = path
            mkdir(path)
            (path / "keep.txt").write_text("competing export")
        return mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", racing_mkdir)
    result = workflow.run_workflow(settings)
    assert result.directory != competitor
    assert competitor is not None
    assert (competitor / "keep.txt").read_text() == "competing export"
    assert result.pdf_path.exists()
