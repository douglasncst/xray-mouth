from __future__ import annotations

from pathlib import Path

from xray_mouth.domain import Exam, Protocol


def write_report(path: Path, exam: Exam, protocol: Protocol, mapped_slots: set[int]) -> None:
    missing = [slot for slot in protocol.slots if slot.number not in mapped_slots]
    lines = [
        "XRay Mouth export report",
        "=" * 24,
        f"Patient: {exam.patient_name}",
        f"Generated: {exam.created_at.isoformat(timespec='seconds')}",
        f"Protocol: {protocol.name} ({len(protocol.slots)} slots)",
        f"Mapped slots: {', '.join(f'{slot:02d}' for slot in sorted(mapped_slots)) or 'none'}",
        f"Missing slots: {', '.join(slot.prefix for slot in missing) or 'none'}",
        "",
        "This export organizes images only. It does not provide medical or dental diagnosis.",
    ]
    if exam.demo:
        lines.append("All images in this run are synthetic and non-diagnostic.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
