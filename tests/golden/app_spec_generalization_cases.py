"""F03-W06 benchmark fixtures for validated AppSpec generalization."""

from __future__ import annotations

from dataclasses import replace

from paper2app.understanding import (
    DocumentElement,
    DocumentIR,
    DocumentRelation,
    NormalizedBox,
    RelationKind,
    TextEvidence,
    VisualKind,
)

from .document_ir_samples import equipment_checkout_golden, safety_inspection_golden


def equipment_checkout_appspec_ready_document_ir() -> DocumentIR:
    """Return the existing clean Equipment Checkout golden DocumentIR."""

    return equipment_checkout_golden().document_ir


def safety_inspection_appspec_ready_document_ir() -> DocumentIR:
    """Resolve Safety severity grouping with explicit observable option/order evidence.

    The F02 golden intentionally carries unresolved severity grouping so fail-closed
    behavior remains covered. F03-W06 uses a separate enriched benchmark fixture
    where Low/Medium/High are observable text options and FOLLOWS gives an explicit
    linear order. No production synthesis branch is added for this case.
    """

    document = safety_inspection_golden().document_ir
    severity = next(element for element in document.elements if element.element_id == "severity_control")

    option_specs = (
        ("severity_low", "Low", NormalizedBox(0.40, 0.38, 0.08, 0.04)),
        ("severity_medium", "Medium", NormalizedBox(0.52, 0.38, 0.12, 0.04)),
        ("severity_high", "High", NormalizedBox(0.68, 0.38, 0.08, 0.04)),
    )
    option_elements = tuple(
        DocumentElement(
            element_id=element_id,
            page_index=severity.page_index,
            visual_kind=VisualKind.TEXT,
            bbox=bbox,
            confidence=0.94,
            text_evidence=(
                TextEvidence(
                    evidence_id=f"vision_text:{element_id}",
                    provider_kind="vision",
                    provider_name="f03_w06_fixture",
                    provider_observation_id=element_id,
                    raw=label,
                    normalized=label,
                    bbox=bbox,
                    confidence=0.94,
                ),
            ),
        )
        for element_id, label, bbox in option_specs
    )

    option_relations = tuple(
        DocumentRelation(
            relation_id=f"option:{element_id}:severity",
            kind=RelationKind.OPTION_OF,
            source_id=element_id,
            target_id="severity_control",
            confidence=0.94,
            evidence_ids=(element_id, "severity_control"),
        )
        for element_id, _, _ in option_specs
    )
    order_relations = (
        DocumentRelation(
            relation_id="follows:severity_low:severity_medium",
            kind=RelationKind.FOLLOWS,
            source_id="severity_low",
            target_id="severity_medium",
            confidence=0.93,
            evidence_ids=("severity_low", "severity_medium"),
        ),
        DocumentRelation(
            relation_id="follows:severity_medium:severity_high",
            kind=RelationKind.FOLLOWS,
            source_id="severity_medium",
            target_id="severity_high",
            confidence=0.93,
            evidence_ids=("severity_medium", "severity_high"),
        ),
    )

    return replace(
        document,
        elements=document.elements + option_elements,
        relations=document.relations + option_relations + order_relations,
        uncertainties=(),
    )


def appspec_generalization_document_irs() -> tuple[tuple[str, DocumentIR], ...]:
    return (
        ("equipment_checkout", equipment_checkout_appspec_ready_document_ir()),
        ("safety_inspection", safety_inspection_appspec_ready_document_ir()),
    )
