"""Paper2App source-image input boundary."""

from .contracts import (
    AcceptedSource,
    CaptureKind,
    ImageNormalizationError,
    InputFailureCode,
    InputGateError,
    InputGatePolicy,
    NormalizationPolicy,
    NormalizedImage,
    RawImageInput,
    SupportedMediaType,
)
from .gate import gate_image_input
from .normalization import decode_and_normalize_image

__all__ = [
    "AcceptedSource",
    "CaptureKind",
    "ImageNormalizationError",
    "InputFailureCode",
    "InputGateError",
    "InputGatePolicy",
    "NormalizationPolicy",
    "NormalizedImage",
    "RawImageInput",
    "SupportedMediaType",
    "decode_and_normalize_image",
    "gate_image_input",
]
