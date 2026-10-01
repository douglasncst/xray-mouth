from pathlib import Path

from PIL import Image

from xray_mouth.analysis import (
    dataset_report,
    filename_may_contain_identifier,
    find_duplicate_groups,
    inspect_image,
)


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
    assert report["duplicate_groups"] == []


def test_find_duplicate_groups_detects_duplicates_and_sorts_deterministically(
    tmp_path: Path,
) -> None:
    # Group 1: 3 identical files
    img1 = Image.new("L", (2, 2), color=10)
    path_1a = tmp_path / "img_z.png"
    path_1b = tmp_path / "img_a.png"
    path_1c = tmp_path / "img_m.png"
    for p in (path_1a, path_1b, path_1c):
        img1.save(p)

    # Group 2: 2 identical files
    img2 = Image.new("L", (2, 2), color=20)
    path_2a = tmp_path / "beta_2.png"
    path_2b = tmp_path / "beta_1.png"
    for p in (path_2a, path_2b):
        img2.save(p)

    # Unique file: 1 file (must NOT be in duplicate_groups)
    Image.new("L", (2, 2), color=30).save(tmp_path / "unique.png")

    report = dataset_report(tmp_path)

    assert report["file_count"] == 6
    duplicate_groups = report["duplicate_groups"]
    assert isinstance(duplicate_groups, list)
    assert len(duplicate_groups) == 2

    # Group 2 has earliest path "beta_1.png", so it comes first in sorted groups
    group_beta = duplicate_groups[0]
    assert group_beta["paths"] == [str(path_2b), str(path_2a)]
    assert len(group_beta["paths"]) == 2

    # Group 1 has paths sorted: "img_a.png", "img_m.png", "img_z.png"
    group_alpha = duplicate_groups[1]
    assert group_alpha["paths"] == [str(path_1b), str(path_1c), str(path_1a)]
    assert len(group_alpha["paths"]) == 3


def test_find_duplicate_groups_edge_cases() -> None:
    # Empty items
    assert find_duplicate_groups([]) == []

    # Only single files (no duplicates)
    items = [
        {"path": "/path/one.png", "sha256": "hash1"},
        {"path": "/path/two.png", "sha256": "hash2"},
    ]
    assert find_duplicate_groups(items) == []

    # Incomplete or non-string entries safely ignored
    items_malformed = [
        {"path": "/path/one.png", "sha256": None},
        {"path": 123, "sha256": "hash1"},
    ]
    assert find_duplicate_groups(items_malformed) == []

