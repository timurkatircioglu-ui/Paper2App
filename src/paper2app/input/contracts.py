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
    IMAGE_TOO_SMALL = "IMAGE_TOO_SMALL"


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


@dataclass(frozen=True, slots=True)
class NormalizationPolicy:
    """Deterministic bounds for image decode and canonical normalization."""

    min_short_edge: int = 320
    max_long_edge: int = 2048
    max_pixels: int = 24_000_000

    def __post_init__(self) -> None:
        if self.min_short_edge < 1:
            raise ValueError("min_short_edge must be >= 1")
        if self.max_long_edge < self.min_short_edge:
            raise ValueError("max_long_edge must be >= min_short_edge")
        if self.max_pixels < self.min_short_edge * self.min_short_edge:
            raise ValueError("max_pixels is too small for the configured minimum edge")


DEFAULT_NORMALIZATION_POLICY = NormalizationPolicy()


@dataclass(frozen=True, slots=True)
class NormalizedImage:
    source: AcceptedSource
    original_width: int
    original_height: int
    normalized_width: int
    normalized_height: int
    exif_orientation: int | None
    orientation_applied: bool
    resized: bool
    normalized_media_type: SupportedMediaType
    normalized_sha256: str
    normalized_content: bytes
    operations: tuple[str, ...]


class ImageNormalizationError(ValueError):
    """Structured deterministic failure from decode/normalization."""

    def __init__(self, code: InputFailureCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class InputGateError(ValueError):
    """Structured deterministic rejection from the source input gate."""

    def __init__(self, code: InputFailureCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
