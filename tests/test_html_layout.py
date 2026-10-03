import importlib.util
from pathlib import Path

from PIL import Image

MODULE_PATH = Path(__file__).resolve().parents[1] / "gerar_relatorio.py"
SPEC = importlib.util.spec_from_file_location("gerar_relatorio", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
gerar_relatorio = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gerar_relatorio)

CANVAS_HEIGHT = gerar_relatorio.CANVAS_HEIGHT
CANVAS_WIDTH = gerar_relatorio.CANVAS_WIDTH
SLOTS = gerar_relatorio.SLOTS
find_images = gerar_relatorio.find_images
locate_exam = gerar_relatorio.locate_exam


def test_layout_has_14_unique_bounded_slots() -> None:
    assert CANVAS_WIDTH == 1672
    assert CANVAS_HEIGHT == 941
    assert set(SLOTS) == set(range(1, 15))
    assert len(set(SLOTS.values())) == 14
    for left, top, width, height in SLOTS.values():
        assert 0 <= left < CANVAS_WIDTH
        assert 0 <= top < CANVAS_HEIGHT
        assert left + width <= CANVAS_WIDTH
        assert top + height <= CANVAS_HEIGHT


def test_approved_reference_positions() -> None:
    assert [SLOTS[number] for number in (1, 6, 7, 10)] == [
        (174, 145, 240, 177),
        (174, 336, 240, 180),
        (174, 531, 240, 179),
        (174, 724, 240, 176),
    ]
    assert [SLOTS[number] for number in (2, 3, 4)] == [
        (497, 261, 188, 240),
        (734, 261, 188, 242),
        (974, 261, 187, 242),
    ]
    assert [SLOTS[number] for number in (11, 12, 13)] == [
        (496, 591, 189, 242),
        (734, 591, 188, 242),
        (974, 591, 186, 242),
    ]
    assert [SLOTS[number] for number in (5, 8, 9, 14)] == [
        (1191, 145, 243, 177),
        (1192, 336, 242, 180),
        (1193, 531, 241, 179),
        (1192, 724, 242, 177),
    ]


def test_find_images_maps_all_prefixes(tmp_path: Path) -> None:
    for number in range(1, 15):
        Image.new("L", (100, 120), number).save(tmp_path / f"{number:02d}_teste.jpg")
    assert set(find_images(tmp_path)) == set(range(1, 15))


def test_locate_exam_uses_patient_folder_name(tmp_path: Path) -> None:
    xray = tmp_path / "xray"
    patient = xray / "Francisco Bispo De Souza"
    patient.mkdir(parents=True)
    Image.new("L", (20, 20), 128).save(patient / "01_teste.jpg")
    exam_dir, patient_name = locate_exam(xray)
    assert exam_dir == patient
    assert patient_name == "Francisco Bispo De Souza"
