"""Small manually verified golden DocumentIR set for F02-W06/W07."""

from __future__ import annotations

from dataclasses import dataclass

from paper2app.understanding.document_ir import (
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
from paper2app.understanding.observations import (
    NormalizedBox,
    RegionKind,
    StructuralRoleHint,
    VisualKind,
)
from paper2app.understanding.validation import ValidationStatus


@dataclass(frozen=True, slots=True)
class GoldenDocumentIRSample:
    name: str
    expected_status: ValidationStatus
    document_ir: DocumentIR


def _source(seed: str) -> DocumentSource:
    return DocumentSource(
        source_id=f"source:{seed}",
        media_type="image/png",
        source_sha256=(seed * 64)[:64],
        normalized_sha256=((seed.upper()) * 64)[:64],
        capture_kind="scan",
        original_width=1200,
        original_height=1600,
        normalized_width=1200,
        normalized_height=1600,
        normalization_operations=("canonical_png",),
    )


def equipment_checkout_golden() -> GoldenDocumentIRSample:
    region = DocumentRegion(
        region_id="equipment_form",
        page_index=0,
        region_kind=RegionKind.FIELD_GROUP,
        bbox=NormalizedBox(0.05, 0.05, 0.90, 0.85),
        confidence=0.99,
        evidence_ids=(),
    )
    name_label = DocumentElement(
        element_id="name_label",
        page_index=0,
        visual_kind=VisualKind.TEXT,
        bbox=NormalizedBox(0.10, 0.16, 0.18, 0.04),
        confidence=0.99,
        text_evidence=(
            TextEvidence(
                evidence_id="vision_text:name_label",
                provider_kind="vision",
                provider_name="golden",
                provider_observation_id="name_label",
                raw="Name",
                normalized="Name",
                bbox=NormalizedBox(0.10, 0.16, 0.18, 0.04),
                confidence=0.99,
            ),
        ),
    )
    elements = (
        name_label,
        DocumentElement(
            element_id="name_input",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.32, 0.15, 0.45, 0.05),
            confidence=0.97,
        ),
        DocumentElement(
            element_id="item_input",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.32, 0.27, 0.45, 0.05),
            confidence=0.96,
        ),
        DocumentElement(
            element_id="returned_checkbox",
            page_index=0,
            visual_kind=VisualKind.CHECKBOX,
            bbox=NormalizedBox(0.32, 0.39, 0.04, 0.04),
            confidence=0.98,
        ),
        DocumentElement(
            element_id="signature_line",
            page_index=0,
            visual_kind=VisualKind.SIGNATURE_LINE,
            bbox=NormalizedBox(0.32, 0.53, 0.45, 0.04),
            confidence=0.94,
        ),
    )
    candidates = (
        FieldCandidate(
            candidate_id="field:name",
            target_element_id="name_input",
            role_hint=StructuralRoleHint.FIELD_VALUE_AREA,
            value_hint=SemanticValueHint.PERSON_NAME,
            confidence=0.95,
            evidence_ids=("name_label", "name_input"),
        ),
        FieldCandidate(
            candidate_id="field:item",
            target_element_id="item_input",
            role_hint=StructuralRoleHint.FIELD_VALUE_AREA,
            value_hint=SemanticValueHint.FREE_TEXT,
            confidence=0.94,
            evidence_ids=("item_input",),
        ),
        FieldCandidate(
            candidate_id="field:returned",
            target_element_id="returned_checkbox",
            role_hint=StructuralRoleHint.FIELD_VALUE_AREA,
            value_hint=SemanticValueHint.BOOLEAN,
            confidence=0.97,
            evidence_ids=("returned_checkbox",),
        ),
        FieldCandidate(
            candidate_id="field:signature",
            target_element_id="signature_line",
            role_hint=StructuralRoleHint.APPROVAL_AREA,
            value_hint=SemanticValueHint.SIGNATURE,
            confidence=0.92,
            evidence_ids=("signature_line",),
        ),
    )
    relations = tuple(
        DocumentRelation(
            relation_id=f"contains:equipment_form:{element.element_id}",
            kind=RelationKind.CONTAINS,
            source_id="equipment_form",
            target_id=element.element_id,
            confidence=None,
            evidence_ids=("equipment_form", element.element_id),
        )
        for element in elements
    )
    return GoldenDocumentIRSample(
        name="equipment_checkout",
        expected_status=ValidationStatus.PASS,
        document_ir=DocumentIR(
            source=_source("a"),
            document=DocumentDescriptor(document_type_hint="equipment_checkout", confidence=0.96),
            pages=(DocumentPage(page_index=0, width=1200, height=1600),),
            regions=(region,),
            elements=elements,
            field_candidates=candidates,
            relations=relations,
            uncertainties=(),
        ),
    )


def safety_inspection_golden() -> GoldenDocumentIRSample:
    region = DocumentRegion(
        region_id="inspection_form",
        page_index=0,
        region_kind=RegionKind.FIELD_GROUP,
        bbox=NormalizedBox(0.05, 0.05, 0.90, 0.88),
        confidence=0.98,
        evidence_ids=(),
    )
    elements = (
        DocumentElement(
            element_id="inspector_input",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.30, 0.14, 0.50, 0.05),
            confidence=0.95,
        ),
        DocumentElement(
            element_id="location_input",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.30, 0.24, 0.50, 0.05),
            confidence=0.95,
        ),
        DocumentElement(
            element_id="severity_control",
            page_index=0,
            visual_kind=VisualKind.RADIO,
            bbox=NormalizedBox(0.30, 0.38, 0.05, 0.05),
            confidence=0.89,
        ),
        DocumentElement(
            element_id="notes_area",
            page_index=0,
            visual_kind=VisualKind.HANDWRITING_AREA,
            bbox=NormalizedBox(0.16, 0.52, 0.68, 0.16),
            confidence=0.91,
        ),
        DocumentElement(
            element_id="approval_signature",
            page_index=0,
            visual_kind=VisualKind.SIGNATURE_LINE,
            bbox=NormalizedBox(0.30, 0.78, 0.50, 0.04),
            confidence=0.90,
        ),
    )
    candidates = (
        FieldCandidate(
            candidate_id="field:inspector",
            target_element_id="inspector_input",
            role_hint=StructuralRoleHint.FIELD_VALUE_AREA,
            value_hint=SemanticValueHint.PERSON_NAME,
            confidence=0.93,
            evidence_ids=("inspector_input",),
        ),
        FieldCandidate(
            candidate_id="field:location",
            target_element_id="location_input",
            role_hint=StructuralRoleHint.FIELD_VALUE_AREA,
            value_hint=SemanticValueHint.FREE_TEXT,
            confidence=0.92,
            evidence_ids=("location_input",),
        ),
        FieldCandidate(
            candidate_id="field:severity",
            target_element_id="severity_control",
            role_hint=StructuralRoleHint.FIELD_VALUE_AREA,
            value_hint=SemanticValueHint.CHOICE,
            confidence=0.82,
            evidence_ids=("severity_control",),
        ),
        FieldCandidate(
            candidate_id="field:notes",
            target_element_id="notes_area",
            role_hint=StructuralRoleHint.NOTES_AREA,
            value_hint=SemanticValueHint.MULTILINE_TEXT,
            confidence=0.90,
            evidence_ids=("notes_area",),
        ),
        FieldCandidate(
            candidate_id="field:approval",
            target_element_id="approval_signature",
            role_hint=StructuralRoleHint.APPROVAL_AREA,
            value_hint=SemanticValueHint.SIGNATURE,
            confidence=0.89,
            evidence_ids=("approval_signature",),
        ),
    )
    relations = tuple(
        DocumentRelation(
            relation_id=f"contains:inspection_form:{element.element_id}",
            kind=RelationKind.CONTAINS,
            source_id="inspection_form",
            target_id=element.element_id,
            confidence=None,
            evidence_ids=("inspection_form", element.element_id),
        )
        for element in elements
    )
    uncertainty = DocumentUncertainty(
        uncertainty_id="uncertainty:severity_relation",
        code=UncertaintyCode.FIELD_RELATION_AMBIGUOUS,
        message="Severity choice grouping needs review before stronger semantic commitment.",
        evidence_ids=("severity_control",),
    )
    return GoldenDocumentIRSample(
        name="safety_inspection",
        expected_status=ValidationStatus.PASS_WITH_WARNINGS,
        document_ir=DocumentIR(
            source=_source("b"),
            document=DocumentDescriptor(document_type_hint="safety_inspection_report", confidence=0.94),
            pages=(DocumentPage(page_index=0, width=1200, height=1600),),
            regions=(region,),
            elements=elements,
            field_candidates=candidates,
            relations=relations,
            uncertainties=(uncertainty,),
        ),
    )


def golden_document_ir_samples() -> tuple[GoldenDocumentIRSample, ...]:
    return (equipment_checkout_golden(), safety_inspection_golden())
