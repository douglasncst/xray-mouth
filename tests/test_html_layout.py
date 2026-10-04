from pathlib import Path

from PIL import Image

from xray_mouth import report as gerar_relatorio

CANVAS_HEIGHT = gerar_relatorio.CANVAS_HEIGHT
CANVAS_WIDTH = gerar_relatorio.CANVAS_WIDTH
SLOTS = gerar_relatorio.SLOTS
build_html = gerar_relatorio.build_html
find_images = gerar_relatorio.find_images
patient_directories = gerar_relatorio.patient_directories
safe_output_name = gerar_relatorio.safe_output_name


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


def test_reference_groups_use_expected_dimensions() -> None:
    for number in (1, 2, 6, 7, 8, 9, 13, 14):
        width, height = SLOTS[number][2:]
        assert width in (240, 242)
        assert height in (175, 176, 178)
    for number in (3, 4, 5, 10, 11, 12):
        width, height = SLOTS[number][2:]
        assert width in (185, 186)
        assert height == 241


def test_reference_group_positions() -> None:
    assert [SLOTS[number][:2] for number in (1, 2, 8, 9)] == [
        (174, 145),
        (174, 337),
        (174, 532),
        (174, 725),
    ]
    assert [SLOTS[number][:2] for number in (3, 4, 5)] == [
        (498, 262),
        (735, 262),
        (975, 262),
    ]
    assert [SLOTS[number][:2] for number in (10, 11, 12)] == [
        (498, 591),
        (735, 591),
        (975, 591),
    ]
    assert [SLOTS[number][:2] for number in (6, 7, 13, 14)] == [
        (1192, 145),
        (1192, 337),
        (1192, 532),
        (1192, 725),
    ]


def test_find_images_maps_all_prefixes(tmp_path: Path) -> None:
    for number in range(1, 15):
        Image.new("L", (100, 120), number).save(tmp_path / f"{number:02d}_teste.jpg")
    assert set(find_images(tmp_path)) == set(range(1, 15))


def test_patient_directories_uses_immediate_folder_names(tmp_path: Path) -> None:
    (tmp_path / "Maria Silva").mkdir()
    (tmp_path / "Francisco Bispo De Souza").mkdir()
    (tmp_path / "README.md").write_text("ignored", encoding="utf-8")

    assert [path.name for path in patient_directories(tmp_path)] == [
        "Francisco Bispo De Souza",
        "Maria Silva",
    ]


def test_patient_name_and_date_are_rendered_safely(tmp_path: Path) -> None:
    logo = tmp_path / "logo.png"
    Image.new("RGB", (1, 1)).save(logo)
    images: dict[int, Path] = {}
    for number in range(1, 15):
        path = tmp_path / f"{number:02d}.jpg"
        Image.new("L", (1, 1)).save(path)
        images[number] = path

    document = build_html(images, logo, "Ana & <Silva>", "03/10/2026")

    assert "Ana &amp; &lt;Silva&gt;" in document
    assert "03/10/2026" in document
    assert "Douglas do Nascimento Castilho" not in document


def test_safe_output_name_replaces_windows_reserved_characters() -> None:
    assert safe_output_name('Paciente: Nome/Com\\Caracteres?') == (
        "Paciente_ Nome_Com_Caracteres_"
    )
