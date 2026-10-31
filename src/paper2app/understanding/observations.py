"""Provider-independent visual structure observation contracts for Paper2App."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class RegionKind(str, Enum):
    TITLE_AREA = "title_area"
    SECTION = "section"
    FIELD_GROUP = "field_group"
    TABLE_LIKE = "table_like"
    INSTRUCTIONS = "instructions"
    FOOTER = "footer"
    UNKNOWN = "unknown"


class VisualKind(str, Enum):
    TEXT = "text"
    BLANK_LINE = "blank_line"
    INPUT_BOX = "input_box"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SIGNATURE_LINE = "signature_line"
    HANDWRITING_AREA = "handwriting_area"
    SEPARATOR = "separator"
    ARROW = "arrow"
    UNKNOWN = "unknown"


class ControlState(str, Enum):
    CHECKED = "checked"
    UNCHECKED = "unchecked"
    UNKNOWN = "unknown"


class StructuralRoleHint(str, Enum):
    FIELD_LABEL = "field_label"
    FIELD_VALUE_AREA = "field_value_area"
    SECTION_HEADING = "section_heading"
    NOTES_AREA = "notes_area"
    APPROVAL_AREA = "approval_area"
    INSTRUCTIONS = "instructions"
    UNKNOWN = "unknown"


def _validate_id(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")


def _validate_confidence(value: float | None, field_name: str = "confidence") -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be a number or None")
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ValueError(f"{field_name} must be finite and within 0.0..1.0")


@dataclass(frozen=True, slots=True)
class NormalizedBox:
    """Normalized rectangle in page/image coordinates."""

    x: float
    y: float
    w: float
    h: float

    def __post_init__(self) -> None:
        values = {"x": self.x, "y": self.y, "w": self.w, "h": self.h}
        for name, value in values.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"bbox.{name} must be numeric")
            if not math.isfinite(float(value)):
                raise ValueError(f"bbox.{name} must be finite")

        if self.x < 0.0 or self.y < 0.0:
            raise ValueError("bbox origin must be within 0.0..1.0")
        if self.w <= 0.0 or self.h <= 0.0:
            raise ValueError("bbox width and height must be > 0")
        if self.x > 1.0 or self.y > 1.0 or self.w > 1.0 or self.h > 1.0:
            raise ValueError("bbox values must remain within 0.0..1.0")
        if self.x + self.w > 1.0 + 1e-9 or self.y + self.h > 1.0 + 1e-9:
            raise ValueError("bbox must fit entirely inside normalized page bounds")


@dataclass(frozen=True, slots=True)
class ObservedText:
    """Text observation preserving raw extraction separately from normalization."""

    raw: str
    normalized: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.raw, str) or not self.raw:
            raise ValueError("observed text raw value must be a non-empty string")
        if self.normalized is not None and not isinstance(self.normalized, str):
            raise TypeError("observed text normalized value must be a string or None")
        _validate_confidence(self.confidence, "text confidence")


@dataclass(frozen=True, slots=True)
class RegionObservation:
    region_id: str
    page_index: int
    region_kind: RegionKind
    bbox: NormalizedBox
    confidence: float | None = None

    def __post_init__(self) -> None:
        _validate_id(self.region_id, "region_id")
        if not isinstance(self.page_index, int) or isinstance(self.page_index, bool) or self.page_index < 0:
            raise ValueError("page_index must be a non-negative integer")
        if not isinstance(self.region_kind, RegionKind):
            raise TypeError("region_kind must be a RegionKind")
        if not isinstance(self.bbox, NormalizedBox):
            raise TypeError("bbox must be a NormalizedBox")
        _validate_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class ElementObservation:
    element_id: str
    page_index: int
    visual_kind: VisualKind
    bbox: NormalizedBox
    confidence: float | None = None
    text: ObservedText | None = None
    control_state: ControlState = ControlState.UNKNOWN

    def __post_init__(self) -> None:
        _validate_id(self.element_id, "element_id")
        if not isinstance(self.page_index, int) or isinstance(self.page_index, bool) or self.page_index < 0:
            raise ValueError("page_index must be a non-negative integer")
        if not isinstance(self.visual_kind, VisualKind):
            raise TypeError("visual_kind must be a VisualKind")
        if not isinstance(self.bbox, NormalizedBox):
            raise TypeError("bbox must be a NormalizedBox")
        _validate_confidence(self.confidence)
        if self.text is not None:
            if not isinstance(self.text, ObservedText):
                raise TypeError("text must be ObservedText or None")
            if self.visual_kind is not VisualKind.TEXT:
                raise ValueError("text payload is only legal for visual_kind=text")
        if not isinstance(self.control_state, ControlState):
            raise TypeError("control_state must be a ControlState")
        if self.visual_kind not in {VisualKind.CHECKBOX, VisualKind.RADIO} and self.control_state is not ControlState.UNKNOWN:
            raise ValueError("checked/unchecked control_state is only legal for checkbox or radio observations")


@dataclass(frozen=True, slots=True)
class StructuralInference:
    """A bounded structural interpretation kept separate from raw observations."""

    inference_id: str
    target_id: str
    role_hint: StructuralRoleHint
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_id(self.inference_id, "inference_id")
        _validate_id(self.target_id, "target_id")
        if not isinstance(self.role_hint, StructuralRoleHint):
            raise TypeError("role_hint must be a StructuralRoleHint")
        _validate_confidence(self.confidence)
        if not isinstance(self.evidence_ids, tuple):
            raise TypeError("evidence_ids must be a tuple")
        seen: set[str] = set()
        for evidence_id in self.evidence_ids:
            _validate_id(evidence_id, "evidence_id")
            if evidence_id in seen:
                raise ValueError("evidence_ids must not contain duplicates")
            seen.add(evidence_id)


@dataclass(frozen=True, slots=True)
class VisualObservationBatch:
    """Deterministically validated provider-neutral observations for one document."""

    page_count: int
    regions: tuple[RegionObservation, ...] = ()
    elements: tuple[ElementObservation, ...] = ()
    inferences: tuple[StructuralInference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.page_count, int) or isinstance(self.page_count, bool) or self.page_count < 1:
            raise ValueError("page_count must be a positive integer")
        if not isinstance(self.regions, tuple) or not isinstance(self.elements, tuple) or not isinstance(self.inferences, tuple):
            raise TypeError("regions, elements and inferences must be tuples")

        observation_ids: set[str] = set()
        all_ids: set[str] = set()

        for region in self.regions:
            if not isinstance(region, RegionObservation):
                raise TypeError("regions must contain RegionObservation values")
            if region.page_index >= self.page_count:
                raise ValueError(f"region {region.region_id!r} references page outside page_count")
            if region.region_id in all_ids:
                raise ValueError(f"duplicate observation id: {region.region_id}")
            observation_ids.add(region.region_id)
            all_ids.add(region.region_id)

        for element in self.elements:
            if not isinstance(element, ElementObservation):
                raise TypeError("elements must contain ElementObservation values")
            if element.page_index >= self.page_count:
                raise ValueError(f"element {element.element_id!r} references page outside page_count")
            if element.element_id in all_ids:
                raise ValueError(f"duplicate observation id: {element.element_id}")
            observation_ids.add(element.element_id)
            all_ids.add(element.element_id)

        for inference in self.inferences:
            if not isinstance(inference, StructuralInference):
                raise TypeError("inferences must contain StructuralInference values")
            if inference.inference_id in all_ids:
                raise ValueError(f"duplicate id: {inference.inference_id}")
            all_ids.add(inference.inference_id)
            if inference.target_id not in observation_ids:
                raise ValueError(f"inference target does not resolve: {inference.target_id}")
            for evidence_id in inference.evidence_ids:
                if evidence_id not in observation_ids:
                    raise ValueError(f"inference evidence does not resolve: {evidence_id}")
