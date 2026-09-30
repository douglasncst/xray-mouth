from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ImageSource(ABC):
    """Provides locally accessible image paths to the validation pipeline.

    Future TWAIN or vendor SDK adapters can implement this interface once hardware
    has been physically validated. No device acquisition is currently shipped.
    """

    @abstractmethod
    def image_paths(self) -> list[Path]:
        """Return candidate source images without mutating them."""
