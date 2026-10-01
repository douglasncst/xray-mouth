from __future__ import annotations

from pathlib import Path

from xray_mouth.config import SUPPORTED_EXTENSIONS
from xray_mouth.devices.base import ImageSource
from xray_mouth.exceptions import InputValidationError


class FolderImageSource(ImageSource):
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def image_paths(self) -> list[Path]:
        if not self.directory.exists() or not self.directory.is_dir():
            raise InputValidationError("Input directory does not exist or is not a directory.")
        if any(
            path.is_symlink() and path.suffix.lower() in SUPPORTED_EXTENSIONS
            for path in self.directory.iterdir()
        ):
            raise InputValidationError(
                "Symlinked images are unsupported; provide local image files."
            )
        return sorted(
            path
            for path in self.directory.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )
