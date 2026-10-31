"""Deterministic raw-image admission gate."""

from __future__ import annotations

import hashlib

from .contracts import (
    AcceptedSource,
    DEFAULT_INPUT_GATE_POLICY,
    InputFailureCode,
    InputGateError,
    InputGatePolicy,
    RawImageInput,
    SupportedMediaType,
)

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_JPEG_SOI_PREFIX = b"\xff\xd8\xff"
_JPEG_EOI = b"\xff\xd9"


def _safe_filename(filename: str | None) -> str | None:
    if filename is None:
        return None
    normalized = filename.replace("\\", "/")
    leaf = normalized.rsplit("/", 1)[-1].strip()
    if not leaf:
        return None
    return leaf[:255]


def _detect_media_type(content: bytes) -> SupportedMediaType:
    if content.startswith(_PNG_SIGNATURE):
        if len(content) < 24 or content[12:16] != b"IHDR":
            raise InputGateError(
                InputFailureCode.IMAGE_CORRUPT,
                "PNG signature exists but the required IHDR header is missing or truncated.",
            )
        width = int.from_bytes(content[16:20], "big")
        height = int.from_bytes(content[20:24], "big")
        if width <= 0 or height <= 0:
            raise InputGateError(
                InputFailureCode.IMAGE_CORRUPT,
                "PNG dimensions must be positive.",
            )
        return SupportedMediaType.PNG

    if content.startswith(_JPEG_SOI_PREFIX):
        if not content.endswith(_JPEG_EOI):
            raise InputGateError(
                InputFailureCode.IMAGE_CORRUPT,
                "JPEG start marker exists but the end marker is missing.",
            )
        return SupportedMediaType.JPEG

    raise InputGateError(
        InputFailureCode.INPUT_UNSUPPORTED,
        "Only PNG and JPEG source images are supported in competition V1.",
    )


def gate_image_input(
    raw: RawImageInput,
    policy: InputGatePolicy = DEFAULT_INPUT_GATE_POLICY,
) -> AcceptedSource:
    """Validate raw source bytes and return immutable source identity metadata.

    File extension and caller-provided MIME metadata are intentionally not trusted.
    Content signatures are authoritative at this boundary. Pixel decoding and
    resolution quality checks belong to F02-W02.
    """

    if not isinstance(raw.content, bytes):
        raise TypeError("raw.content must be bytes")

    byte_size = len(raw.content)
    if byte_size < policy.min_bytes:
        raise InputGateError(
            InputFailureCode.IMAGE_CORRUPT,
            f"Source image is too small to contain a supported image header ({byte_size} bytes).",
        )
    if byte_size > policy.max_bytes:
        raise InputGateError(
            InputFailureCode.INPUT_UNSUPPORTED,
            f"Source image exceeds the configured {policy.max_bytes}-byte input limit.",
        )

    media_type = _detect_media_type(raw.content)
    digest = hashlib.sha256(raw.content).hexdigest()

    return AcceptedSource(
        source_id=f"src_{digest[:24]}",
        media_type=media_type,
        sha256=digest,
        byte_size=byte_size,
        filename=_safe_filename(raw.filename),
        capture_kind=raw.capture_kind,
    )
