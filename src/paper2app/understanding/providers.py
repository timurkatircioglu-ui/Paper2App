"""Provider ports and bounded execution contracts for Paper2App understanding."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import string
from typing import Protocol, runtime_checkable

from .observations import NormalizedBox, VisualObservationBatch


class ProviderKind(str, Enum):
    VISION = "vision"
    OCR = "ocr"


class ProviderFailureCode(str, Enum):
    VISION_FAILED = "VISION_FAILED"
    OCR_FAILED = "OCR_FAILED"


def _validate_nonempty(value: str, field_name: str, *, max_length: int = 128) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(value) > max_length:
        raise ValueError(f"{field_name} must be at most {max_length} characters")


def _validate_confidence(value: float | None) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError("provider_confidence must be numeric or None")
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ValueError("provider_confidence must be finite and within 0.0..1.0")


def _validate_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field_name} must be a 64-character SHA-256 hex string")
    if any(character not in string.hexdigits for character in value):
        raise ValueError(f"{field_name} must contain only hexadecimal characters")


@dataclass(frozen=True, slots=True)
class ProviderIdentity:
    """Versioned identity for one replaceable provider adapter/model binding."""

    kind: ProviderKind
    provider_name: str
    adapter_version: str
    model_id: str
    prompt_version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProviderKind):
            raise TypeError("kind must be a ProviderKind")
        _validate_nonempty(self.provider_name, "provider_name")
        _validate_nonempty(self.adapter_version, "adapter_version")
        _validate_nonempty(self.model_id, "model_id")
        if self.prompt_version is not None:
            _validate_nonempty(self.prompt_version, "prompt_version")


@dataclass(frozen=True, slots=True)
class ProviderImage:
    """Canonical normalized image payload exposed to vision/OCR adapters."""

    source_id: str
    normalized_sha256: str
    media_type: str
    width: int
    height: int
    content: bytes

    def __post_init__(self) -> None:
        _validate_nonempty(self.source_id, "source_id")
        _validate_sha256(self.normalized_sha256, "normalized_sha256")
        if self.media_type != "image/png":
            raise ValueError("provider image media_type must be canonical image/png")
        if not isinstance(self.width, int) or isinstance(self.width, bool) or self.width < 1:
            raise ValueError("width must be a positive integer")
        if not isinstance(self.height, int) or isinstance(self.height, bool) or self.height < 1:
            raise ValueError("height must be a positive integer")
        if not isinstance(self.content, bytes) or not self.content:
            raise ValueError("content must be non-empty bytes")


@dataclass(frozen=True, slots=True)
class OCRTextObservation:
    """Exact-text provider observation; no semantic/business interpretation is allowed."""

    observation_id: str
    page_index: int
    bbox: NormalizedBox
    raw_text: str
    normalized_text: str | None = None
    provider_confidence: float | None = None

    def __post_init__(self) -> None:
        _validate_nonempty(self.observation_id, "observation_id")
        if not isinstance(self.page_index, int) or isinstance(self.page_index, bool) or self.page_index < 0:
            raise ValueError("page_index must be a non-negative integer")
        if not isinstance(self.bbox, NormalizedBox):
            raise TypeError("bbox must be a NormalizedBox")
        if not isinstance(self.raw_text, str) or not self.raw_text:
            raise ValueError("raw_text must be a non-empty string")
        if self.normalized_text is not None and not isinstance(self.normalized_text, str):
            raise TypeError("normalized_text must be a string or None")
        _validate_confidence(self.provider_confidence)


@dataclass(frozen=True, slots=True)
class OCRObservationBatch:
    page_count: int
    observations: tuple[OCRTextObservation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.page_count, int) or isinstance(self.page_count, bool) or self.page_count < 1:
            raise ValueError("page_count must be a positive integer")
        if not isinstance(self.observations, tuple):
            raise TypeError("observations must be a tuple")

        seen: set[str] = set()
        for observation in self.observations:
            if not isinstance(observation, OCRTextObservation):
                raise TypeError("observations must contain OCRTextObservation values")
            if observation.page_index >= self.page_count:
                raise ValueError(
                    f"OCR observation {observation.observation_id!r} references page outside page_count"
                )
            if observation.observation_id in seen:
                raise ValueError(f"duplicate OCR observation id: {observation.observation_id}")
            seen.add(observation.observation_id)


@dataclass(frozen=True, slots=True)
class ProviderCallPolicy:
    """Bounded retry policy. No provider fallback is implied by this policy."""

    max_attempts: int = 2

    def __post_init__(self) -> None:
        if not isinstance(self.max_attempts, int) or isinstance(self.max_attempts, bool):
            raise TypeError("max_attempts must be an integer")
        if not 1 <= self.max_attempts <= 3:
            raise ValueError("max_attempts must be within 1..3")


DEFAULT_PROVIDER_CALL_POLICY = ProviderCallPolicy()


class ProviderError(RuntimeError):
    """Controlled provider failure crossing the provider boundary."""

    def __init__(self, code: ProviderFailureCode, message: str, *, retryable: bool = False) -> None:
        if not isinstance(code, ProviderFailureCode):
            raise TypeError("code must be a ProviderFailureCode")
        _validate_nonempty(message, "message", max_length=512)
        if not isinstance(retryable, bool):
            raise TypeError("retryable must be a bool")
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


@runtime_checkable
class VisionProvider(Protocol):
    @property
    def identity(self) -> ProviderIdentity: ...

    def analyze(self, image: ProviderImage) -> VisualObservationBatch: ...


@runtime_checkable
class OCRProvider(Protocol):
    @property
    def identity(self) -> ProviderIdentity: ...

    def extract(self, image: ProviderImage) -> OCRObservationBatch: ...


@dataclass(frozen=True, slots=True)
class VisionProviderResult:
    provider: ProviderIdentity
    observations: VisualObservationBatch
    attempts: int


@dataclass(frozen=True, slots=True)
class OCRProviderResult:
    provider: ProviderIdentity
    observations: OCRObservationBatch
    attempts: int


def _validated_identity(provider: object, expected_kind: ProviderKind) -> ProviderIdentity:
    identity = getattr(provider, "identity", None)
    if not isinstance(identity, ProviderIdentity):
        raise TypeError("provider.identity must be a ProviderIdentity")
    if identity.kind is not expected_kind:
        raise ValueError(
            f"provider identity kind {identity.kind.value!r} does not match expected {expected_kind.value!r}"
        )
    return identity


def run_vision_provider(
    provider: VisionProvider,
    image: ProviderImage,
    policy: ProviderCallPolicy = DEFAULT_PROVIDER_CALL_POLICY,
) -> VisionProviderResult:
    if not isinstance(image, ProviderImage):
        raise TypeError("image must be a ProviderImage")
    if not isinstance(policy, ProviderCallPolicy):
        raise TypeError("policy must be a ProviderCallPolicy")
    identity = _validated_identity(provider, ProviderKind.VISION)

    for attempt in range(1, policy.max_attempts + 1):
        try:
            observations = provider.analyze(image)
        except ProviderError as exc:
            if exc.code is not ProviderFailureCode.VISION_FAILED:
                raise ProviderError(
                    ProviderFailureCode.VISION_FAILED,
                    "Vision provider returned a failure code owned by another provider boundary.",
                ) from exc
            if exc.retryable and attempt < policy.max_attempts:
                continue
            raise
        except Exception as exc:
            raise ProviderError(
                ProviderFailureCode.VISION_FAILED,
                "Vision provider failed unexpectedly.",
            ) from exc

        if not isinstance(observations, VisualObservationBatch):
            raise ProviderError(
                ProviderFailureCode.VISION_FAILED,
                "Vision provider returned an invalid response type.",
            )
        if observations.page_count != 1:
            raise ProviderError(
                ProviderFailureCode.VISION_FAILED,
                "Competition V1 vision provider must return exactly one observed page for one provider image.",
            )
        return VisionProviderResult(provider=identity, observations=observations, attempts=attempt)

    raise AssertionError("unreachable bounded provider loop")


def run_ocr_provider(
    provider: OCRProvider,
    image: ProviderImage,
    policy: ProviderCallPolicy = DEFAULT_PROVIDER_CALL_POLICY,
) -> OCRProviderResult:
    if not isinstance(image, ProviderImage):
        raise TypeError("image must be a ProviderImage")
    if not isinstance(policy, ProviderCallPolicy):
        raise TypeError("policy must be a ProviderCallPolicy")
    identity = _validated_identity(provider, ProviderKind.OCR)

    for attempt in range(1, policy.max_attempts + 1):
        try:
            observations = provider.extract(image)
        except ProviderError as exc:
            if exc.code is not ProviderFailureCode.OCR_FAILED:
                raise ProviderError(
                    ProviderFailureCode.OCR_FAILED,
                    "OCR provider returned a failure code owned by another provider boundary.",
                ) from exc
            if exc.retryable and attempt < policy.max_attempts:
                continue
            raise
        except Exception as exc:
            raise ProviderError(
                ProviderFailureCode.OCR_FAILED,
                "OCR provider failed unexpectedly.",
            ) from exc

        if not isinstance(observations, OCRObservationBatch):
            raise ProviderError(
                ProviderFailureCode.OCR_FAILED,
                "OCR provider returned an invalid response type.",
            )
        if observations.page_count != 1:
            raise ProviderError(
                ProviderFailureCode.OCR_FAILED,
                "Competition V1 OCR provider must return exactly one observed page for one provider image.",
            )
        return OCRProviderResult(provider=identity, observations=observations, attempts=attempt)

    raise AssertionError("unreachable bounded provider loop")
