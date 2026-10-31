"""DocumentIR runtime contracts assembled from provider-neutral document evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from .observations import NormalizedBox, RegionKind, StructuralRoleHint, VisualKind


DOCUMENT_IR_SCHEMA = "paper2app.document_ir"
DOCUMENT_IR_SCHEMA_VERSION = "0.1"


class SemanticValueHint(str, Enum):
    FREE_TEXT = "free_text"
    PERSON_NAME = "person_name"
    NUMBER = "number"
    DATE = "date"
    TIME = "time"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    MULTILINE_TEXT = "multiline_text"
    SIGNATURE = "signature"
    IDENTIFIER = "identifier"
    EMAIL = "email"
    PHONE = "phone"
    UNKNOWN = "unknown"


class RelationKind(str, Enum):
    LABELS = "labels"
    CONTAINS = "contains"
    BELONGS_TO = "belongs_to"
    OPTION_OF = "option_of"
    FOLLOWS = "follows"
    ALIGNED_WITH = "aligned_with"
    ASSOCIATED_WITH = "associated_with"


class UncertaintyCode(str, Enum):
    TEXT_CONFLICT = "TEXT_CONFLICT"
    LAYOUT_AMBIGUOUS = "LAYOUT_AMBIGUOUS"
    FIELD_RELATION_AMBIGUOUS = "FIELD_RELATION_AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


def _require_nonempty(value: str, name: str, *, maximum: int = 256) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if len(value) > maximum:
        raise ValueError(f"{name} must be at most {maximum} characters")


def _validate_confidence(value: float | None, name: str = "confidence") -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric or None")
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ValueError(f"{name} must be finite and within 0.0..1.0")


@dataclass(frozen=True, slots=True)
class DocumentSource:
    source_id: str
    media_type: str
    source_sha256: str
    normalized_sha256: str
    capture_kind: str
    original_width: int
    original_height: int
    normalized_width: int
    normalized_height: int
    normalization_operations: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.source_id, "source_id")
        _require_nonempty(self.media_type, "media_type")
        _require_nonempty(self.source_sha256, "source_sha256")
        _require_nonempty(self.normalized_sha256, "normalized_sha256")
        _require_nonempty(self.capture_kind, "capture_kind")
        for name, value in (
            ("original_width", self.original_width),
            ("original_height", self.original_height),
            ("normalized_width", self.normalized_width),
            ("normalized_height", self.normalized_height),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if not isinstance(self.normalization_operations, tuple):
            raise TypeError("normalization_operations must be a tuple")
        for operation in self.normalization_operations:
            _require_nonempty(operation, "normalization operation")


@dataclass(frozen=True, slots=True)
class DocumentDescriptor:
    document_type_hint: str = "unknown"
    confidence: float | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.document_type_hint, "document_type_hint")
        _validate_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class DocumentPage:
    page_index: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if not isinstance(self.page_index, int) or isinstance(self.page_index, bool) or self.page_index < 0:
            raise ValueError("page_index must be a non-negative integer")
        if not isinstance(self.width, int) or isinstance(self.width, bool) or self.width < 1:
            raise ValueError("width must be a positive integer")
        if not isinstance(self.height, int) or isinstance(self.height, bool) or self.height < 1:
            raise ValueError("height must be a positive integer")


@dataclass(frozen=True, slots=True)
class TextEvidence:
    evidence_id: str
    provider_kind: str
    provider_name: str
    provider_observation_id: str
    raw: str
    normalized: str | None
    bbox: NormalizedBox
    confidence: float | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.evidence_id, "evidence_id")
        if self.provider_kind not in {"vision", "ocr"}:
            raise ValueError("provider_kind must be 'vision' or 'ocr'")
        _require_nonempty(self.provider_name, "provider_name")
        _require_nonempty(self.provider_observation_id, "provider_observation_id")
        if not isinstance(self.raw, str) or not self.raw:
            raise ValueError("raw text must be non-empty")
        if self.normalized is not None and not isinstance(self.normalized, str):
            raise TypeError("normalized text must be a string or None")
        if not isinstance(self.bbox, NormalizedBox):
            raise TypeError("bbox must be a NormalizedBox")
        _validate_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class DocumentRegion:
    region_id: str
    page_index: int
    region_kind: RegionKind
    bbox: NormalizedBox
    confidence: float | None
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.region_id, "region_id")
        if not isinstance(self.page_index, int) or isinstance(self.page_index, bool) or self.page_index < 0:
            raise ValueError("page_index must be a non-negative integer")
        if not isinstance(self.region_kind, RegionKind):
            raise TypeError("region_kind must be a RegionKind")
        if not isinstance(self.bbox, NormalizedBox):
            raise TypeError("bbox must be a NormalizedBox")
        _validate_confidence(self.confidence)
        if not isinstance(self.evidence_ids, tuple):
            raise TypeError("evidence_ids must be a tuple")


@dataclass(frozen=True, slots=True)
class DocumentElement:
    element_id: str
    page_index: int
    visual_kind: VisualKind
    bbox: NormalizedBox
    confidence: float | None
    text_evidence: tuple[TextEvidence, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_nonempty(self.element_id, "element_id")
        if not isinstance(self.page_index, int) or isinstance(self.page_index, bool) or self.page_index < 0:
            raise ValueError("page_index must be a non-negative integer")
        if not isinstance(self.visual_kind, VisualKind):
            raise TypeError("visual_kind must be a VisualKind")
        if not isinstance(self.bbox, NormalizedBox):
            raise TypeError("bbox must be a NormalizedBox")
        _validate_confidence(self.confidence)
        if not isinstance(self.text_evidence, tuple) or not all(isinstance(item, TextEvidence) for item in self.text_evidence):
            raise TypeError("text_evidence must be a tuple of TextEvidence")
        if not isinstance(self.evidence_ids, tuple):
            raise TypeError("evidence_ids must be a tuple")


@dataclass(frozen=True, slots=True)
class FieldCandidate:
    candidate_id: str
    target_element_id: str
    role_hint: StructuralRoleHint
    value_hint: SemanticValueHint
    confidence: float | None
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.candidate_id, "candidate_id")
        _require_nonempty(self.target_element_id, "target_element_id")
        if not isinstance(self.role_hint, StructuralRoleHint):
            raise TypeError("role_hint must be a StructuralRoleHint")
        if not isinstance(self.value_hint, SemanticValueHint):
            raise TypeError("value_hint must be a SemanticValueHint")
        _validate_confidence(self.confidence)
        if not isinstance(self.evidence_ids, tuple) or not self.evidence_ids:
            raise ValueError("field candidate evidence_ids must be a non-empty tuple")


@dataclass(frozen=True, slots=True)
class DocumentRelation:
    relation_id: str
    kind: RelationKind
    source_id: str
    target_id: str
    confidence: float | None
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.relation_id, "relation_id")
        if not isinstance(self.kind, RelationKind):
            raise TypeError("kind must be a RelationKind")
        _require_nonempty(self.source_id, "source_id")
        _require_nonempty(self.target_id, "target_id")
        if self.source_id == self.target_id:
            raise ValueError("relation endpoints must be distinct")
        _validate_confidence(self.confidence)
        if not isinstance(self.evidence_ids, tuple):
            raise TypeError("evidence_ids must be a tuple")


@dataclass(frozen=True, slots=True)
class DocumentUncertainty:
    uncertainty_id: str
    code: UncertaintyCode
    message: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.uncertainty_id, "uncertainty_id")
        if not isinstance(self.code, UncertaintyCode):
            raise TypeError("code must be an UncertaintyCode")
        _require_nonempty(self.message, "message", maximum=512)
        if not isinstance(self.evidence_ids, tuple) or not self.evidence_ids:
            raise ValueError("uncertainty evidence_ids must be a non-empty tuple")


@dataclass(frozen=True, slots=True)
class DocumentIR:
    source: DocumentSource
    document: DocumentDescriptor
    pages: tuple[DocumentPage, ...]
    regions: tuple[DocumentRegion, ...]
    elements: tuple[DocumentElement, ...]
    field_candidates: tuple[FieldCandidate, ...]
    relations: tuple[DocumentRelation, ...]
    uncertainties: tuple[DocumentUncertainty, ...]
    schema: str = DOCUMENT_IR_SCHEMA
    schema_version: str = DOCUMENT_IR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != DOCUMENT_IR_SCHEMA:
            raise ValueError("unknown DocumentIR schema")
        if self.schema_version != DOCUMENT_IR_SCHEMA_VERSION:
            raise ValueError("unknown DocumentIR schema_version")
        if not isinstance(self.source, DocumentSource):
            raise TypeError("source must be a DocumentSource")
        if not isinstance(self.document, DocumentDescriptor):
            raise TypeError("document must be a DocumentDescriptor")
        for name in ("pages", "regions", "elements", "field_candidates", "relations", "uncertainties"):
            if not isinstance(getattr(self, name), tuple):
                raise TypeError(f"{name} must be a tuple")
