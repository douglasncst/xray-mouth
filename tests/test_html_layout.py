from pathlib import Path

from PIL import Image

from gerar_relatorio import CANVAS_HEIGHT, CANVAS_WIDTH, SLOTS, find_images


def test_layout_has_14_unique_bounded_slots() -> None:
    assert CANVAS_WIDTH == 1600
    assert CANVAS_HEIGHT == 1278
    assert set(SLOTS) == set(range(1, 15))
    assert len(set(SLOTS.values())) == 14
    for left, top, width, height in SLOTS.values():
        assert 0 <= left < CANVAS_WIDTH
        assert 0 <= top < CANVAS_HEIGHT
        assert left + width <= CANVAS_WIDTH
        assert top + height <= CANVAS_HEIGHT


def test_reference_groups_use_expected_dimensions() -> None:
    side = {SLOTS[number][2:] for number in (1, 5, 6, 7, 8, 9, 10, 14)}
    center = {SLOTS[number][2:] for number in (2, 3, 4, 11, 12, 13)}
    assert side == {(252, 190)}
    assert center == {(190, 253)}


def test_reference_group_positions() -> None:
    assert [SLOTS[number][:2] for number in (1, 6, 7, 10)] == [
        (63, 126),
        (63, 346),
        (63, 567),
        (63, 787),
    ]
    assert [SLOTS[number][:2] for number in (2, 3, 4)] == [
        (441, 251),
        (705, 251),
        (964, 251),
    ]
    assert [SLOTS[number][:2] for number in (11, 12, 13)] == [
        (441, 629),
        (705, 629),
        (964, 629),
    ]
    assert [SLOTS[number][:2] for number in (5, 8, 9, 14)] == [
        (1279, 126),
        (1279, 346),
        (1279, 567),
        (1279, 787),
    ]


def test_find_images_maps_all_prefixes(tmp_path: Path) -> None:
    for number in range(1, 15):
        Image.new("L", (100, 120), number).save(tmp_path / f"{number:02d}_teste.jpg")
    assert set(find_images(tmp_path)) == set(range(1, 15))
