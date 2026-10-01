from pathlib import Path

from PIL import Image

from xray_mouth.analysis import dataset_report, filename_may_contain_identifier, inspect_image


def test_inspect_image_reports_reproducible_metrics(tmp_path: Path) -> None:
    path = tmp_path / "sample.png"
    Image.new("L", (4, 4), color=128).save(path)

    report = inspect_image(path)

    assert report.width == 4
    assert report.height == 4
    assert report.mean_intensity == 128.0
    assert report.sha256
    assert "very low contrast" in report.warnings


def test_filename_privacy_warning() -> None:
    assert filename_may_contain_identifier(Path("patient_12345678.png"))
    assert not filename_may_contain_identifier(Path("study_a.png"))


def test_dataset_report_is_json_ready(tmp_path: Path) -> None:
    Image.new("L", (3, 3), color=10).save(tmp_path / "image.png")

    report = dataset_report(tmp_path)

    assert report["file_count"] == 1
    assert report["errors"] == []
