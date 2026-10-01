from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RadiographSlot:
    number: int
    label: str

    @property
    def prefix(self) -> str:
        return f"{self.number:02d}"


@dataclass(frozen=True, slots=True)
class Protocol:
    name: str
    slots: tuple[RadiographSlot, ...]

    def slot_for(self, number: int) -> RadiographSlot | None:
        return next((slot for slot in self.slots if slot.number == number), None)


DEFAULT_PROTOCOL = Protocol(
    name="14-position periapical series",
    slots=(
        RadiographSlot(1, "Superior posterior right"),
        RadiographSlot(2, "Superior anterior right"),
        RadiographSlot(3, "Superior incisors"),
        RadiographSlot(4, "Superior anterior left"),
        RadiographSlot(5, "Superior posterior left"),
        RadiographSlot(6, "Lateral upper right"),
        RadiographSlot(7, "Lateral lower right"),
        RadiographSlot(8, "Lateral upper left"),
        RadiographSlot(9, "Lateral lower left"),
        RadiographSlot(10, "Lower posterior right"),
        RadiographSlot(11, "Lower anterior right"),
        RadiographSlot(12, "Lower incisors"),
        RadiographSlot(13, "Lower anterior left"),
        RadiographSlot(14, "Lower posterior left"),
    ),
)


@dataclass(frozen=True, slots=True)
class Radiograph:
    slot: RadiographSlot
    path: Path


@dataclass(frozen=True, slots=True)
class Exam:
    patient_name: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, str] = field(default_factory=dict)
    demo: bool = False


@dataclass(frozen=True, slots=True)
class ExportResult:
    directory: Path
    preview_path: Path
    render_path: Path
    pdf_path: Path
    report_path: Path
    mapped_slots: tuple[int, ...]
    missing_slots: tuple[int, ...]
