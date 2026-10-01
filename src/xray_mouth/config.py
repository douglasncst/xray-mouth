from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from xray_mouth.exceptions import InputValidationError

SUPPORTED_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"})


@dataclass(frozen=True, slots=True)
class RenderConfig:
    preview_size: tuple[int, int] = (1754, 1240)
    detail_size: tuple[int, int] = (7016, 4960)
    contrast: float = 1.0


@dataclass(frozen=True, slots=True)
class WorkflowConfig:
    input_directory: Path
    output_root: Path
    patient_name: str
    strict: bool = False
    demo: bool = False
    contrast: float = 1.0
    clinic_name: str = "XRay Mouth"
    clinic_subtitle: str = "Clinical Radiograph Series"
    exam_label: str = "Série periapical"

    def __post_init__(self) -> None:
        if not isfinite(self.contrast) or self.contrast <= 0:
            raise InputValidationError("Contrast must be finite and greater than zero.")
        if not self.patient_name.strip():
            raise InputValidationError("Patient name must not be empty.")
        if len(self.patient_name) > 200 or not self.patient_name.isprintable():
            raise InputValidationError(
                "Patient name must be at most 200 characters without controls."
            )
        for label, value, maximum in (
            ("Clinic name", self.clinic_name, 120),
            ("Clinic subtitle", self.clinic_subtitle, 160),
            ("Exam label", self.exam_label, 120),
        ):
            if not value.strip():
                raise InputValidationError(f"{label} must not be empty.")
            if len(value) > maximum or not value.isprintable():
                raise InputValidationError(
                    f"{label} must be at most {maximum} characters without controls."
                )
