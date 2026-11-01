"""Deterministic entity/field synthesis from validated DocumentIR."""

from __future__ import annotations

from dataclasses import dataclass
import re

from paper2app.understanding.document_ir import (
    DocumentElement,
    DocumentIR,
    FieldCandidate,
    RelationKind,
    SemanticValueHint,
)
from paper2app.understanding.observations import VisualKind
from paper2app.understanding.validation import require_valid_document_ir

from .app_spec import (
    AppEntity,
    AppField,
    AppSpecUncertainty,
    FieldType,
    ProvenanceClass,
    ProvenanceRecord,
)


@dataclass(frozen=True, slots=True)
class FieldSynthesisDecision:
    candidate_id: str
    target_element_id: str
    field_id: str
    field_type: FieldType | None
    confidence: float | None
    source_refs: tuple[str, ...]
    emitted: bool
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class EntityFieldSynthesisResult:
    entities: tuple[AppEntity, ...]
    provenance: tuple[ProvenanceRecord, ...]
    uncertainties: tuple[AppSpecUncertainty, ...]
    decisions: tuple[FieldSynthesisDecision, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.entities, tuple) or not all(isinstance(item, AppEntity) for item in self.entities):
            raise TypeError("entities must be a tuple of AppEntity values")
        if not isinstance(self.provenance, tuple) or not all(
            isinstance(item, ProvenanceRecord) for item in self.provenance
        ):
            raise TypeError("provenance must be a tuple of ProvenanceRecord values")
        if not isinstance(self.uncertainties, tuple) or not all(
            isinstance(item, AppSpecUncertainty) for item in self.uncertainties
        ):
            raise TypeError("uncertainties must be a tuple of AppSpecUncertainty values")
        if not isinstance(self.decisions, tuple) or not all(
            isinstance(item, FieldSynthesisDecision) for item in self.decisions
        ):
            raise TypeError("decisions must be a tuple of FieldSynthesisDecision values")


def _slug(value: str, *, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or fallback


def _display(value: str, *, fallback: str) -> str:
    cleaned = re.sub(r"[_:\-]+", " ", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return fallback
    return " ".join(part[:1].upper() + part[1:] for part in cleaned.split(" "))


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _element_text(element: DocumentElement | None) -> str | None:
    if element is None:
        return None
    for evidence in element.text_evidence:
        text = evidence.normalized if evidence.normalized else evidence.raw
        if isinstance(text, str) and text.strip():
            return text.strip()
    return None


def _label_for_candidate(
    document_ir: DocumentIR,
    candidate: FieldCandidate,
    element_by_id: dict[str, DocumentElement],
) -> str:
    for relation in document_ir.relations:
        if relation.kind is RelationKind.LABELS and relation.target_id == candidate.target_element_id:
            text = _element_text(element_by_id.get(relation.source_id))
            if text:
                return text

    for evidence_id in candidate.evidence_ids:
        if evidence_id == candidate.target_element_id:
            continue
        text = _element_text(element_by_id.get(evidence_id))
        if text:
            return text

    candidate_tail = candidate.candidate_id.split(":", 1)[-1]
    if candidate_tail and candidate_tail != candidate.candidate_id:
        return _display(candidate_tail, fallback="Field")

    target_name = re.sub(r"(?:_input|_field|_control|_box|_area|_line)$", "", candidate.target_element_id)
    return _display(target_name, fallback="Field")


def _choice_options(
    document_ir: DocumentIR,
    candidate: FieldCandidate,
    element_by_id: dict[str, DocumentElement],
) -> tuple[str, ...]:
    options: list[str] = []
    for relation in document_ir.relations:
        if relation.kind is not RelationKind.OPTION_OF:
            continue
        option_id: str | None = None
        if relation.target_id == candidate.target_element_id:
            option_id = relation.source_id
        elif relation.source_id == candidate.target_element_id:
            option_id = relation.target_id
        if option_id is None:
            continue
        text = _element_text(element_by_id.get(option_id))
        if text and text not in options:
            options.append(text)
    return tuple(options)


def _field_type(
    candidate: FieldCandidate,
    target: DocumentElement,
    choice_options: tuple[str, ...],
) -> tuple[FieldType | None, str | None]:
    mapping = {
        SemanticValueHint.FREE_TEXT: FieldType.STRING,
        SemanticValueHint.PERSON_NAME: FieldType.STRING,
        SemanticValueHint.NUMBER: FieldType.DECIMAL,
        SemanticValueHint.DATE: FieldType.DATE,
        SemanticValueHint.TIME: FieldType.TIME,
        SemanticValueHint.BOOLEAN: FieldType.BOOLEAN,
        SemanticValueHint.MULTILINE_TEXT: FieldType.MULTILINE_STRING,
        SemanticValueHint.SIGNATURE: FieldType.SIGNATURE,
        SemanticValueHint.EMAIL: FieldType.EMAIL,
        SemanticValueHint.PHONE: FieldType.PHONE,
        SemanticValueHint.IDENTIFIER: FieldType.IDENTIFIER,
    }
    if candidate.value_hint in mapping:
        return mapping[candidate.value_hint], None
    if candidate.value_hint is SemanticValueHint.CHOICE:
        if choice_options:
            return FieldType.ENUM, None
        return None, "choice candidate has no evidence-backed options"

    if target.visual_kind is VisualKind.CHECKBOX:
        return FieldType.BOOLEAN, None
    if target.visual_kind is VisualKind.SIGNATURE_LINE:
        return FieldType.SIGNATURE, None
    if target.visual_kind is VisualKind.HANDWRITING_AREA:
        return FieldType.MULTILINE_STRING, None
    return None, "field type remains unknown from bounded document evidence"


def _field_base_id(candidate: FieldCandidate) -> str:
    value = candidate.candidate_id.split(":", 1)[-1]
    return _slug(value, fallback=_slug(candidate.target_element_id, fallback="field"))


def _stable_unique_id(base: str, used: set[str]) -> str:
    if base not in used:
        used.add(base)
        return base
    ordinal = 2
    while f"{base}_{ordinal}" in used:
        ordinal += 1
    result = f"{base}_{ordinal}"
    used.add(result)
    return result


def synthesize_entity_fields(document_ir: DocumentIR) -> EntityFieldSynthesisResult:
    """Synthesize bounded entity/field semantics from a validated DocumentIR.

    This function is intentionally narrower than full AppSpec synthesis. It creates
    data concepts only; views, actions, persistence, validations and workflows are
    owned by later F03 packages.
    """

    document_ir = require_valid_document_ir(document_ir)
    element_by_id = {element.element_id: element for element in document_ir.elements}

    fields: list[AppField] = []
    provenance: list[ProvenanceRecord] = []
    uncertainties: list[AppSpecUncertainty] = []
    decisions: list[FieldSynthesisDecision] = []
    used_field_ids: set[str] = set()

    for candidate in document_ir.field_candidates:
        target = element_by_id[candidate.target_element_id]
        options = _choice_options(document_ir, candidate, element_by_id)
        proposed_type, reason = _field_type(candidate, target, options)
        field_id = _stable_unique_id(_field_base_id(candidate), used_field_ids)
        source_refs = _unique((candidate.candidate_id, candidate.target_element_id) + candidate.evidence_ids)

        if proposed_type is None:
            uncertainties.append(
                AppSpecUncertainty(
                    uncertainty_id=f"synthesis:{candidate.candidate_id}",
                    message=reason or "field synthesis could not resolve a safe logical type",
                    critical=True,
                    source_refs=source_refs,
                )
            )
            decisions.append(
                FieldSynthesisDecision(
                    candidate_id=candidate.candidate_id,
                    target_element_id=candidate.target_element_id,
                    field_id=field_id,
                    field_type=None,
                    confidence=candidate.confidence,
                    source_refs=source_refs,
                    emitted=False,
                    reason=reason,
                )
            )
            continue

        display_name = _label_for_candidate(document_ir, candidate, element_by_id)
        app_field = AppField(
            field_id=field_id,
            display_name=display_name,
            field_type=proposed_type,
            options=options if proposed_type is FieldType.ENUM else (),
        )
        fields.append(app_field)
        confidence_note = "unknown" if candidate.confidence is None else f"{candidate.confidence:.3f}"
        provenance.append(
            ProvenanceRecord(
                provenance_id=f"document:{field_id}",
                target_id=field_id,
                provenance_class=ProvenanceClass.DOCUMENT_DERIVED,
                source_refs=source_refs,
                note=f"Synthesized from DocumentIR field candidate; confidence={confidence_note}",
            )
        )
        decisions.append(
            FieldSynthesisDecision(
                candidate_id=candidate.candidate_id,
                target_element_id=candidate.target_element_id,
                field_id=field_id,
                field_type=proposed_type,
                confidence=candidate.confidence,
                source_refs=source_refs,
                emitted=True,
            )
        )

    document_hint = document_ir.document.document_type_hint
    hint_is_known = document_hint.strip().lower() != "unknown"
    entity_base = _slug(document_hint, fallback="document") if hint_is_known else "document"
    entity_id = f"{entity_base}_record"
    entity_display = f"{_display(document_hint, fallback='Document')} Record" if hint_is_known else "Document Record"

    entities: tuple[AppEntity, ...] = ()
    if fields:
        entities = (AppEntity(entity_id=entity_id, display_name=entity_display, fields=tuple(fields)),)
        provenance.append(
            ProvenanceRecord(
                provenance_id=f"entity:{entity_id}",
                target_id=entity_id,
                provenance_class=(ProvenanceClass.DOCUMENT_DERIVED if hint_is_known else ProvenanceClass.PRODUCT_POLICY),
                source_refs=(document_ir.source.source_id,) if hint_is_known else (),
                note=("Entity identity follows document_type_hint." if hint_is_known else "Generic primary entity used because document type is unknown."),
            )
        )
        if not hint_is_known:
            uncertainties.append(
                AppSpecUncertainty(
                    uncertainty_id="synthesis:document_type_unknown",
                    message="Document type is unknown; a generic primary entity identity was used.",
                    critical=False,
                    target_ids=(entity_id,),
                    source_refs=(document_ir.source.source_id,),
                )
            )
    elif document_ir.field_candidates:
        uncertainties.append(
            AppSpecUncertainty(
                uncertainty_id="synthesis:no_executable_fields",
                message="No field candidate could be safely converted into an executable AppField.",
                critical=True,
                source_refs=tuple(candidate.candidate_id for candidate in document_ir.field_candidates),
            )
        )

    return EntityFieldSynthesisResult(
        entities=entities,
        provenance=tuple(provenance),
        uncertainties=tuple(uncertainties),
        decisions=tuple(decisions),
    )
