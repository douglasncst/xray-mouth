from pathlib import Path

from PIL import Image

from gerar_relatorio import CANVAS_HEIGHT, CANVAS_WIDTH, SLOTS, find_images


def test_layout_has_16_unique_bounded_slots() -> None:
    assert set(SLOTS) == set(range(1, 17))
    assert len(set(SLOTS.values())) == 16
    for left, top, width, height in SLOTS.values():
        assert 0 <= left < CANVAS_WIDTH
        assert 0 <= top < CANVAS_HEIGHT
        assert left + width <= CANVAS_WIDTH
        assert top + height <= CANVAS_HEIGHT


def test_groups_use_identical_dimensions() -> None:
    side = {SLOTS[number][2:] for number in (1, 2, 6, 7, 8, 9, 13, 14)}
    center = {SLOTS[number][2:] for number in (3, 4, 5, 10, 11, 12, 15, 16)}
    assert side == {(280, 180)}
    assert center == {(185, 270)}


def test_find_images_maps_all_prefixes(tmp_path: Path) -> None:
    for number in range(1, 17):
        Image.new("L", (100, 120), number).save(tmp_path / f"{number:02d}_teste.jpg")
    assert set(find_images(tmp_path)) == set(range(1, 17))

