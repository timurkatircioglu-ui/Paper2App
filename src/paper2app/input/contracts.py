"""Deterministic input contracts for Paper2App source images."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SupportedMediaType(str, Enum):
    JPEG = "image/jpeg"
    PNG = "image/png"


class CaptureKind(str, Enum):
    CAMERA_PHOTO = "camera_photo"
    SCAN = "scan"
    UPLOAD = "upload"
    UNKNOWN = "unknown"


class InputFailureCode(str, Enum):
    INPUT_UNSUPPORTED = "INPUT_UNSUPPORTED"
    IMAGE_CORRUPT = "IMAGE_CORRUPT"


@dataclass(frozen=True, slots=True)
class InputGatePolicy:
    """Bounded deterministic policy for raw source acceptance."""

    max_bytes: int = 20 * 1024 * 1024
    min_bytes: int = 16

    def __post_init__(self) -> None:
        if self.min_bytes < 1:
            raise ValueError("min_bytes must be >= 1")
        if self.max_bytes < self.min_bytes:
            raise ValueError("max_bytes must be >= min_bytes")


DEFAULT_INPUT_GATE_POLICY = InputGatePolicy()


@dataclass(frozen=True, slots=True)
class RawImageInput:
    content: bytes
    filename: str | None = None
    capture_kind: CaptureKind = CaptureKind.UNKNOWN


@dataclass(frozen=True, slots=True)
class AcceptedSource:
    source_id: str
    media_type: SupportedMediaType
    sha256: str
    byte_size: int
    filename: str | None
    capture_kind: CaptureKind


class InputGateError(ValueError):
    """Structured deterministic rejection from the source input gate."""

    def __init__(self, code: InputFailureCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
