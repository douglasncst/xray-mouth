from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
