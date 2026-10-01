class XRayMouthError(Exception):
    """Base exception for expected application errors."""


class InputValidationError(XRayMouthError):
    """Raised when folder input cannot safely be processed."""


class DuplicateSlotError(InputValidationError):
    """Raised when more than one file claims a protocol slot."""


class ImageIntegrityError(InputValidationError):
    """Raised when a discovered source image is unreadable."""


class ExportError(XRayMouthError):
    """Raised when local filesystem operations prevent export."""
