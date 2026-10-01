from __future__ import annotations

from pathlib import Path

from xray_mouth.domain import Exam, Protocol, Radiograph


def write_report(
    path: Path,
    exam: Exam,
    protocol: Protocol,
    radiographs: dict[int, Radiograph],
    candidate_image_count: int,
    output_names: tuple[str, str, str],
) -> None:
    missing = [slot for slot in protocol.slots if slot.number not in radiographs]
    lines = [
        "XRay Mouth export report",
        "=" * 24,
        f"Patient: {exam.patient_name}",
        f"Generated: {exam.created_at.isoformat(timespec='seconds')}",
        f"Protocol: {protocol.name}",
        f"Candidate image files found: {candidate_image_count}",
        f"Radiographs mapped: {len(radiographs)}",
        f"Expected positions: {len(protocol.slots)}",
        f"Missing positions: {len(missing)}",
        "Missing slots: " + (", ".join(slot.prefix for slot in missing) or "none"),
        f"Series status: {'COMPLETE' if not missing else 'INCOMPLETE'}",
        "",
        "Positions:",
    ]
    for slot in protocol.slots:
        filename = radiographs[slot.number].path.name if slot.number in radiographs else "MISSING"
        lines.append(f"{slot.prefix} {slot.label}: {filename}")
    lines.extend(
        [
            "",
            f"Preview: {output_names[0]}",
            f"High-resolution canvas: {output_names[1]}",
            f"PDF: {output_names[2]}",
            "Source files: NOT MODIFIED",
            "The high-resolution canvas is sized for A4 at 600 DPI; it does not add source "
            "resolution or clinical detail.",
            "This export organizes images only. It does not provide medical or dental diagnosis.",
        ]
    )
    if exam.demo:
        lines.append("Mode: DEMO / SYNTHETIC / NON-DIAGNOSTIC")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
