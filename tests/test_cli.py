import json
from pathlib import Path

from PIL import Image

from xray_mouth.cli import main


def test_inspect_command_writes_json_report(tmp_path: Path) -> None:
    Image.new("L", (2, 2), color=64).save(tmp_path / "sample.png")
    output = tmp_path / "report.json"

    status = main(["inspect", str(tmp_path), "--output", str(output)])

    assert status == 0
    assert json.loads(output.read_text(encoding="utf-8"))["file_count"] == 1


def test_inspect_command_prints_report(tmp_path: Path, capsys: object) -> None:
    Image.new("L", (2, 2), color=64).save(tmp_path / "sample.png")

    status = main(["inspect", str(tmp_path)])

    assert status == 0
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert '"schema_version": "1.0"' in captured.out
