"""Regression checks for the approved geometry, artwork and exported report."""

import hashlib
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

from xray_mouth.cli import main
from xray_mouth.report import SLOTS, find_images

ROOT = Path(__file__).resolve().parents[1]
APPROVED_SLOTS = {
    1: (174, 145, 240, 176),
    2: (174, 337, 240, 178),
    3: (498, 262, 186, 241),
    4: (735, 262, 186, 241),
    5: (975, 262, 185, 241),
    6: (1192, 145, 242, 176),
    7: (1192, 337, 242, 178),
    8: (174, 532, 240, 178),
    9: (174, 725, 240, 175),
    10: (498, 591, 186, 241),
    11: (735, 591, 186, 241),
    12: (975, 591, 185, 241),
    13: (1192, 532, 242, 178),
    14: (1192, 725, 242, 175),
}


def test_approved_layout_and_artwork_are_unchanged() -> None:
    assert SLOTS == APPROVED_SLOTS
    artwork = ROOT / "assets" / "green_smile_reference_header.png"
    assert hashlib.sha256(artwork.read_bytes()).hexdigest() == (
        "705d94f0699eb90e9098de753cda7a9a27516f954e43b79a6063518d5e8aeb99"
    )


def test_report_cli_renders_approved_png_and_single_page_pdf(tmp_path: Path) -> None:
    patient = tmp_path / "xray" / "Paciente sintetico"
    patient.mkdir(parents=True)
    original_hashes = {}
    for number in range(1, 15):
        path = patient / f"{number:02d}_synthetic.png"
        Image.new("L", (300, 300), number * 16).save(path)
        original_hashes[path] = hashlib.sha256(path.read_bytes()).digest()

    assert main(["report", str(tmp_path), "--no-open"]) == 0
    output, = (tmp_path / "relatorio").iterdir()
    with Image.open(output / "periapical_series_preview.png") as image:
        assert image.size == (1672, 941)
        image = image.convert("RGB")
        for number, (x, y, width, height) in APPROVED_SLOTS.items():
            assert image.getpixel((x + width // 2, y + height // 2)) == (number * 16,) * 3
            assert image.getpixel((x, y)) == (0, 0, 0)
        assert image.getpixel((800, 550)) == (0, 0, 0)
    pdf = PdfReader(output / "periapical_series.pdf")
    assert len(pdf.pages) == 1
    assert float(pdf.pages[0].mediabox.width) == pytest.approx(1254, abs=1)
    assert float(pdf.pages[0].mediabox.height) == pytest.approx(705.75, abs=1)
    document = (output / "montagem.html").read_text(encoding="utf-8")
    assert "Paciente sintetico" in document
    assert "font-size:24px" in document
    assert "border-radius:42px" in document
    assert "color:#ff6200" in document
    assert "object-fit:cover" in document
    for path, digest in original_hashes.items():
        assert hashlib.sha256(path.read_bytes()).digest() == digest


def test_duplicate_and_missing_inputs_fail_before_rendering(tmp_path: Path) -> None:
    Image.new("L", (10, 10)).save(tmp_path / "01_first.png")
    with pytest.raises(ValueError, match="faltam imagens"):
        find_images(tmp_path)
    Image.new("L", (10, 10)).save(tmp_path / "01_duplicate.png")
    with pytest.raises(ValueError, match="mais de uma imagem"):
        find_images(tmp_path)


def test_report_cli_reports_missing_input(tmp_path: Path) -> None:
    assert main(["report", str(tmp_path), "--no-open"]) == 1
