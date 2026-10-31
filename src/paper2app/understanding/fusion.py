"""Deterministic fusion of vision/OCR observations into DocumentIR."""

from __future__ import annotations

from dataclasses import replace
import re
from typing import Protocol, runtime_checkable

from .document_ir import (
    DocumentDescriptor,
    DocumentElement,
    DocumentIR,
    DocumentPage,
    DocumentRegion,
    DocumentRelation,
    DocumentSource,
    DocumentUncertainty,
    FieldCandidate,
    RelationKind,
    SemanticValueHint,
    TextEvidence,
    UncertaintyCode,
)
from .observations import NormalizedBox, StructuralRoleHint, VisualKind
from .providers import OCRProviderResult, ProviderKind, VisionProviderResult


_TEXT_MATCH_THRESHOLD = 0.50


class _SourceView(Protocol):
    source_id: str
    media_type: object
    sha256: str
    capture_kind: object


class NormalizedImageView(Protocol):
    source: _SourceView
    original_width: int
    original_height: int
    normalized_width: int
    normalized_height: int
    normalized_sha256: str
    operations: tuple[str, ...]


def _validate_image_view(image: object) -> NormalizedImageView:
    required = (
        "source",
        "original_width",
        "original_height",
        "normalized_width",
        "normalized_height",
        "normalized_sha256",
        "operations",
    )
    if any(not hasattr(image, name) for name in required):
        raise TypeError("image must satisfy the normalized-image boundary contract")
    source = getattr(image, "source")
    if any(not hasattr(source, name) for name in ("source_id", "media_type", "sha256", "capture_kind")):
        raise TypeError("image.source must satisfy the accepted-source boundary contract")
    return image  # type: ignore[return-value]


def _enum_value(value: object, name: str) -> str:
    enum_value = getattr(value, "value", None)
    if not isinstance(enum_value, str) or not enum_value:
        raise TypeError(f"{name} must expose a non-empty string .value")
    return enum_value


def _intersection_area(left: NormalizedBox, right: NormalizedBox) -> float:
    x1 = max(left.x, right.x)
    y1 = max(left.y, right.y)
    x2 = min(left.x + left.w, right.x + right.w)
    y2 = min(left.y + left.h, right.y + right.h)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    return (x2 - x1) * (y2 - y1)


def _overlap_score(left: NormalizedBox, right: NormalizedBox) -> float:
    intersection = _intersection_area(left, right)
    if intersection <= 0.0:
        return 0.0
    smaller = min(left.w * left.h, right.w * right.h)
    return intersection / smaller if smaller > 0.0 else 0.0


def _contains(outer: NormalizedBox, inner: NormalizedBox) -> bool:
    epsilon = 1e-9
    return (
        inner.x + epsilon >= outer.x
        and inner.y + epsilon >= outer.y
        and inner.x + inner.w <= outer.x + outer.w + epsilon
        and inner.y + inner.h <= outer.y + outer.h + epsilon
    )


def _canonical_text(value: str) -> str:
    collapsed = " ".join(value.split()).casefold()
    collapsed = re.sub(r"\s+([:;,.!?])", r"\1", collapsed)
    return re.sub(r"[:;,.!?]", "", collapsed)


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _value_hint(visual_kind: VisualKind, role_hint: StructuralRoleHint) -> SemanticValueHint:
    if visual_kind is VisualKind.CHECKBOX:
        return SemanticValueHint.BOOLEAN
    if visual_kind is VisualKind.RADIO:
        return SemanticValueHint.CHOICE
    if visual_kind is VisualKind.SIGNATURE_LINE:
        return SemanticValueHint.SIGNATURE
    if role_hint is StructuralRoleHint.NOTES_AREA:
        return SemanticValueHint.MULTILINE_TEXT
    if visual_kind is VisualKind.HANDWRITING_AREA:
        return SemanticValueHint.FREE_TEXT
    if visual_kind in {VisualKind.INPUT_BOX, VisualKind.BLANK_LINE}:
        return SemanticValueHint.FREE_TEXT
    return SemanticValueHint.UNKNOWN


def _source_from_normalized(image: NormalizedImageView) -> DocumentSource:
    return DocumentSource(
        source_id=image.source.source_id,
        media_type=_enum_value(image.source.media_type, "source.media_type"),
        source_sha256=image.source.sha256,
        normalized_sha256=image.normalized_sha256,
        capture_kind=_enum_value(image.source.capture_kind, "source.capture_kind"),
        original_width=image.original_width,
        original_height=image.original_height,
        normalized_width=image.normalized_width,
        normalized_height=image.normalized_height,
        normalization_operations=image.operations,
    )


def assemble_document_ir(
    image: NormalizedImageView,
    vision: VisionProviderResult,
    ocr: OCRProviderResult | None = None,
) -> DocumentIR:
    """Fuse provider observations without silently overwriting disagreement."""

    image = _validate_image_view(image)
    if not isinstance(vision, VisionProviderResult):
        raise TypeError("vision must be a VisionProviderResult")
    if ocr is not None and not isinstance(ocr, OCRProviderResult):
        raise TypeError("ocr must be an OCRProviderResult or None")
    if vision.provider.kind is not ProviderKind.VISION:
        raise ValueError("vision result must carry a vision provider identity")
    if vision.observations.page_count != 1:
        raise ValueError("competition V1 DocumentIR assembly requires one vision page")
    if ocr is not None:
        if ocr.provider.kind is not ProviderKind.OCR:
            raise ValueError("ocr result must carry an OCR provider identity")
        if ocr.observations.page_count != vision.observations.page_count:
            raise ValueError("vision and OCR page_count must agree")

    regions = tuple(
        DocumentRegion(
            region_id=region.region_id,
            page_index=region.page_index,
            region_kind=region.region_kind,
            bbox=region.bbox,
            confidence=region.confidence,
            evidence_ids=(),
        )
        for region in vision.observations.regions
    )

    elements: list[DocumentElement] = []
    for element in vision.observations.elements:
        text_evidence: tuple[TextEvidence, ...] = ()
        if element.text is not None:
            text_evidence = (
                TextEvidence(
                    evidence_id=f"vision_text:{element.element_id}",
                    provider_kind="vision",
                    provider_name=vision.provider.provider_name,
                    provider_observation_id=element.element_id,
                    raw=element.text.raw,
                    normalized=element.text.normalized,
                    bbox=element.bbox,
                    confidence=element.text.confidence,
                ),
            )
        elements.append(
            DocumentElement(
                element_id=element.element_id,
                page_index=element.page_index,
                visual_kind=element.visual_kind,
                bbox=element.bbox,
                confidence=element.confidence,
                text_evidence=text_evidence,
                evidence_ids=(),
            )
        )

    if ocr is not None:
        for ordinal, observation in enumerate(ocr.observations.observations):
            evidence = TextEvidence(
                evidence_id=f"ocr_text:{observation.observation_id}",
                provider_kind="ocr",
                provider_name=ocr.provider.provider_name,
                provider_observation_id=observation.observation_id,
                raw=observation.raw_text,
                normalized=observation.normalized_text,
                bbox=observation.bbox,
                confidence=observation.provider_confidence,
            )

            best_index: int | None = None
            best_score = 0.0
            for index, element in enumerate(elements):
                if element.page_index != observation.page_index or element.visual_kind is not VisualKind.TEXT:
                    continue
                score = _overlap_score(element.bbox, observation.bbox)
                if score > best_score:
                    best_score = score
                    best_index = index

            if best_index is not None and best_score >= _TEXT_MATCH_THRESHOLD:
                target = elements[best_index]
                elements[best_index] = replace(target, text_evidence=target.text_evidence + (evidence,))
            else:
                elements.append(
                    DocumentElement(
                        element_id=f"ocr_element_{ordinal:04d}",
                        page_index=observation.page_index,
                        visual_kind=VisualKind.TEXT,
                        bbox=observation.bbox,
                        confidence=observation.provider_confidence,
                        text_evidence=(evidence,),
                        evidence_ids=(),
                    )
                )

    uncertainties: list[DocumentUncertainty] = []
    for element in elements:
        if len(element.text_evidence) < 2:
            continue
        variants = {
            _canonical_text(evidence.normalized if evidence.normalized is not None else evidence.raw)
            for evidence in element.text_evidence
        }
        if len(variants) > 1:
            uncertainties.append(
                DocumentUncertainty(
                    uncertainty_id=f"text_conflict:{element.element_id}",
                    code=UncertaintyCode.TEXT_CONFLICT,
                    message="Matched text providers disagree on the observed text for this element.",
                    evidence_ids=tuple(evidence.evidence_id for evidence in element.text_evidence),
                )
            )

    element_by_id = {element.element_id: element for element in elements}
    field_candidates: list[FieldCandidate] = []
    for inference in vision.observations.inferences:
        target = element_by_id.get(inference.target_id)
        if target is None:
            continue
        if inference.role_hint not in {
            StructuralRoleHint.FIELD_VALUE_AREA,
            StructuralRoleHint.NOTES_AREA,
            StructuralRoleHint.APPROVAL_AREA,
        }:
            continue
        field_candidates.append(
            FieldCandidate(
                candidate_id=f"field:{inference.inference_id}",
                target_element_id=target.element_id,
                role_hint=inference.role_hint,
                value_hint=_value_hint(target.visual_kind, inference.role_hint),
                confidence=inference.confidence,
                evidence_ids=_unique((target.element_id,) + inference.evidence_ids),
            )
        )

    relations: list[DocumentRelation] = []
    for region in regions:
        for element in elements:
            if region.page_index == element.page_index and _contains(region.bbox, element.bbox):
                relations.append(
                    DocumentRelation(
                        relation_id=f"contains:{region.region_id}:{element.element_id}",
                        kind=RelationKind.CONTAINS,
                        source_id=region.region_id,
                        target_id=element.element_id,
                        confidence=None,
                        evidence_ids=(region.region_id, element.element_id),
                    )
                )

    return DocumentIR(
        source=_source_from_normalized(image),
        document=DocumentDescriptor(),
        pages=(DocumentPage(page_index=0, width=image.normalized_width, height=image.normalized_height),),
        regions=regions,
        elements=tuple(elements),
        field_candidates=tuple(field_candidates),
        relations=tuple(relations),
        uncertainties=tuple(uncertainties),
    )
