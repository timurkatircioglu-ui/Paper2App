"""Deterministic validation/workflow/provenance/uncertainty synthesis for F03-W04."""

from __future__ import annotations

from dataclasses import dataclass
import re

from paper2app.understanding.document_ir import DocumentIR, DocumentRelation, RelationKind, UncertaintyCode
from paper2app.understanding.validation import require_valid_document_ir

from .app_spec import (
    ActionKind,
    AppAction,
    AppEntity,
    AppSpecUncertainty,
    AppValidation,
    AppView,
    AppWorkflow,
    Capability,
    FieldType,
    PersistenceRequirement,
    ProvenanceClass,
    ProvenanceRecord,
    ValidationRuleKind,
    WorkflowState,
    WorkflowTransition,
)
from .surface_policy import ApplicationSurfaceSynthesisResult


@dataclass(frozen=True, slots=True)
class ValidationWorkflowSynthesisResult:
    """Cumulative F03 state after evidence-backed validations/workflows are added."""

    entities: tuple[AppEntity, ...]
    views: tuple[AppView, ...]
    actions: tuple[AppAction, ...]
    workflows: tuple[AppWorkflow, ...]
    validations: tuple[AppValidation, ...]
    capabilities: tuple[Capability, ...]
    persistence: PersistenceRequirement
    provenance: tuple[ProvenanceRecord, ...]
    uncertainties: tuple[AppSpecUncertainty, ...]

    def __post_init__(self) -> None:
        typed_collections = (
            ("entities", self.entities, AppEntity),
            ("views", self.views, AppView),
            ("actions", self.actions, AppAction),
            ("workflows", self.workflows, AppWorkflow),
            ("validations", self.validations, AppValidation),
            ("capabilities", self.capabilities, Capability),
            ("provenance", self.provenance, ProvenanceRecord),
            ("uncertainties", self.uncertainties, AppSpecUncertainty),
        )
        for name, values, expected_type in typed_collections:
            if not isinstance(values, tuple):
                raise TypeError(f"{name} must be a tuple")
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{name} contains an invalid value")
        if not isinstance(self.persistence, PersistenceRequirement):
            raise TypeError("persistence must be a PersistenceRequirement")


@dataclass(frozen=True, slots=True)
class _WorkflowProposal:
    entity_id: str
    field_id: str
    workflow: AppWorkflow
    source_refs: tuple[str, ...]


def _slug(value: str, *, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or fallback


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _field_provenance(
    surface: ApplicationSurfaceSynthesisResult,
    field_id: str,
) -> ProvenanceRecord | None:
    for record in surface.provenance:
        if record.target_id == field_id and record.provenance_class is ProvenanceClass.DOCUMENT_DERIVED:
            return record
    return None


def _candidate_for_field(document_ir: DocumentIR, provenance: ProvenanceRecord | None):
    if provenance is None:
        return None
    source_refs = set(provenance.source_refs)
    for candidate in document_ir.field_candidates:
        if candidate.candidate_id in source_refs:
            return candidate
    return None


def _text_for_element(document_ir: DocumentIR, element_id: str) -> str | None:
    for element in document_ir.elements:
        if element.element_id != element_id:
            continue
        for evidence in element.text_evidence:
            text = evidence.normalized if evidence.normalized else evidence.raw
            if isinstance(text, str) and text.strip():
                return text.strip()
        return None
    return None


def _option_evidence(
    document_ir: DocumentIR,
    target_element_id: str,
) -> tuple[tuple[str, str, str], ...]:
    """Return ordered (option_text, option_element_id, relation_id) evidence."""

    options: list[tuple[str, str, str]] = []
    seen_text: set[str] = set()
    for relation in document_ir.relations:
        if relation.kind is not RelationKind.OPTION_OF:
            continue
        option_id: str | None = None
        if relation.target_id == target_element_id:
            option_id = relation.source_id
        elif relation.source_id == target_element_id:
            option_id = relation.target_id
        if option_id is None:
            continue
        text = _text_for_element(document_ir, option_id)
        if text and text not in seen_text:
            seen_text.add(text)
            options.append((text, option_id, relation.relation_id))
    return tuple(options)


def _document_validation_provenance(
    validation: AppValidation,
    source_refs: tuple[str, ...],
    note: str,
) -> ProvenanceRecord:
    return ProvenanceRecord(
        provenance_id=f"document:validation:{validation.validation_id.replace(':', '_')}",
        target_id=validation.validation_id,
        provenance_class=ProvenanceClass.DOCUMENT_DERIVED,
        source_refs=_unique(source_refs),
        note=note,
    )


def _policy_provenance(target_id: str, note: str) -> ProvenanceRecord:
    return ProvenanceRecord(
        provenance_id=f"policy:w04:{target_id.replace(':', '_')}",
        target_id=target_id,
        provenance_class=ProvenanceClass.PRODUCT_POLICY,
        source_refs=(),
        note=note,
    )


def _linear_workflow_proposal(
    document_ir: DocumentIR,
    entity: AppEntity,
    field,
    field_provenance: ProvenanceRecord | None,
) -> tuple[_WorkflowProposal | None, AppSpecUncertainty | None]:
    if field.field_type is not FieldType.ENUM or len(field.options) < 2:
        return None, None

    candidate = _candidate_for_field(document_ir, field_provenance)
    if candidate is None:
        return None, None

    option_evidence = _option_evidence(document_ir, candidate.target_element_id)
    option_id_by_text = {text: element_id for text, element_id, _ in option_evidence}
    if any(option not in option_id_by_text for option in field.options):
        return None, None

    option_ids = {option_id_by_text[option] for option in field.options}
    follows = tuple(
        relation
        for relation in document_ir.relations
        if relation.kind is RelationKind.FOLLOWS
        and relation.source_id in option_ids
        and relation.target_id in option_ids
    )
    if not follows:
        return None, None

    edge_by_pair: dict[tuple[str, str], DocumentRelation] = {}
    for relation in follows:
        edge_by_pair.setdefault((relation.source_id, relation.target_id), relation)
    edges = tuple(edge_by_pair.values())

    incoming: dict[str, int] = {node: 0 for node in option_ids}
    outgoing: dict[str, list[str]] = {node: [] for node in option_ids}
    for relation in edges:
        outgoing[relation.source_id].append(relation.target_id)
        incoming[relation.target_id] += 1

    roots = [node for node in option_ids if incoming[node] == 0]
    structurally_linear = (
        len(edges) == len(option_ids) - 1
        and len(roots) == 1
        and all(count <= 1 for count in incoming.values())
        and all(len(targets) <= 1 for targets in outgoing.values())
    )

    ordered_ids: list[str] = []
    if structurally_linear:
        current = roots[0]
        while current not in ordered_ids:
            ordered_ids.append(current)
            targets = outgoing[current]
            if not targets:
                break
            current = targets[0]
        structurally_linear = len(ordered_ids) == len(option_ids)

    workflow_source_refs = _unique(
        tuple(ref for _, element_id, relation_id in option_evidence for ref in (element_id, relation_id))
        + tuple(relation.relation_id for relation in edges)
        + (candidate.candidate_id, candidate.target_element_id)
    )

    if not structurally_linear:
        return None, AppSpecUncertainty(
            uncertainty_id=f"workflow:{entity.entity_id}:{field.field_id}:ambiguous",
            message="Observed workflow ordering is not a single deterministic linear state chain.",
            critical=True,
            target_ids=(field.field_id,),
            source_refs=workflow_source_refs,
        )

    text_by_id = {element_id: text for text, element_id, _ in option_evidence}
    used_state_ids: set[str] = set()
    state_id_by_option_id: dict[str, str] = {}
    states: list[WorkflowState] = []
    for option_id in ordered_ids:
        label = text_by_id[option_id]
        base = f"state:{field.field_id}:{_slug(label, fallback='state')}"
        state_id = base
        ordinal = 2
        while state_id in used_state_ids:
            state_id = f"{base}_{ordinal}"
            ordinal += 1
        used_state_ids.add(state_id)
        state_id_by_option_id[option_id] = state_id
        states.append(WorkflowState(state_id=state_id, display_name=label))

    transitions = tuple(
        WorkflowTransition(
            transition_id=f"transition:{field.field_id}:{index + 1}",
            from_state_id=state_id_by_option_id[ordered_ids[index]],
            to_state_id=state_id_by_option_id[ordered_ids[index + 1]],
        )
        for index in range(len(ordered_ids) - 1)
    )
    workflow = AppWorkflow(
        workflow_id=f"workflow:{entity.entity_id}:{field.field_id}",
        entity_id=entity.entity_id,
        states=tuple(states),
        initial_state_id=states[0].state_id,
        transitions=transitions,
    )
    return _WorkflowProposal(
        entity_id=entity.entity_id,
        field_id=field.field_id,
        workflow=workflow,
        source_refs=workflow_source_refs,
    ), None


def synthesize_validations_workflows(
    document_ir: DocumentIR,
    surface: ApplicationSurfaceSynthesisResult,
) -> ValidationWorkflowSynthesisResult:
    """Add only evidence-backed validations/workflows to the cumulative F03 surface."""

    document_ir = require_valid_document_ir(document_ir)
    if not isinstance(surface, ApplicationSurfaceSynthesisResult):
        raise TypeError("surface must be an ApplicationSurfaceSynthesisResult")

    validations: list[AppValidation] = []
    workflows: list[AppWorkflow] = []
    actions = list(surface.actions)
    capabilities = list(surface.capabilities)
    provenance = list(surface.provenance)
    uncertainties = list(surface.uncertainties)
    workflow_proposals_by_entity: dict[str, list[_WorkflowProposal]] = {}

    field_document_refs: dict[str, set[str]] = {}

    for entity in surface.entities:
        for field in entity.fields:
            field_provenance = _field_provenance(surface, field.field_id)
            source_refs = field_provenance.source_refs if field_provenance is not None else ()
            field_document_refs[field.field_id] = set(source_refs)

            if field.field_type in {FieldType.ENUM, FieldType.MULTI_ENUM} and field.options:
                candidate = _candidate_for_field(document_ir, field_provenance)
                option_refs: tuple[str, ...] = ()
                if candidate is not None:
                    option_refs = tuple(
                        ref
                        for _, element_id, relation_id in _option_evidence(document_ir, candidate.target_element_id)
                        for ref in (element_id, relation_id)
                    )
                validation = AppValidation(
                    validation_id=f"validation:{entity.entity_id}:{field.field_id}:allowed_values",
                    entity_id=entity.entity_id,
                    field_id=field.field_id,
                    kind=ValidationRuleKind.ALLOWED_VALUES,
                    value=field.options,
                )
                validations.append(validation)
                provenance.append(
                    _document_validation_provenance(
                        validation,
                        source_refs + option_refs,
                        "Allowed values come from evidence-backed enum options already present in the synthesized field.",
                    )
                )

            if field.field_type is FieldType.EMAIL:
                validation = AppValidation(
                    validation_id=f"validation:{entity.entity_id}:{field.field_id}:format",
                    entity_id=entity.entity_id,
                    field_id=field.field_id,
                    kind=ValidationRuleKind.FORMAT,
                    value="email",
                )
                validations.append(validation)
                provenance.append(
                    _document_validation_provenance(
                        validation,
                        source_refs,
                        "Email format validation follows the evidence-backed logical email field type.",
                    )
                )

            proposal, workflow_uncertainty = _linear_workflow_proposal(
                document_ir,
                entity,
                field,
                field_provenance,
            )
            if workflow_uncertainty is not None:
                uncertainties.append(workflow_uncertainty)
            if proposal is not None:
                workflow_proposals_by_entity.setdefault(entity.entity_id, []).append(proposal)

    for entity_id, proposals in workflow_proposals_by_entity.items():
        if len(proposals) > 1:
            uncertainties.append(
                AppSpecUncertainty(
                    uncertainty_id=f"workflow:{entity_id}:multiple",
                    message="Competition V1 supports at most one evidence-backed workflow per entity.",
                    critical=True,
                    target_ids=tuple(proposal.field_id for proposal in proposals),
                    source_refs=_unique(tuple(ref for proposal in proposals for ref in proposal.source_refs)),
                )
            )
            continue

        proposal = proposals[0]
        workflows.append(proposal.workflow)
        provenance.append(
            ProvenanceRecord(
                provenance_id=f"document:workflow:{proposal.workflow.workflow_id.replace(':', '_')}",
                target_id=proposal.workflow.workflow_id,
                provenance_class=ProvenanceClass.DOCUMENT_DERIVED,
                source_refs=proposal.source_refs,
                note="Workflow states and order come from explicit option and FOLLOWS document evidence.",
            )
        )

        action_id = f"action:{entity_id}:change_state"
        actions.append(
            AppAction(
                action_id=action_id,
                kind=ActionKind.CHANGE_STATE,
                entity_id=entity_id,
                workflow_id=proposal.workflow.workflow_id,
            )
        )
        provenance.append(
            _policy_provenance(
                action_id,
                "Competition V1 exposes an evidence-backed workflow through an explicit change_state action.",
            )
        )
        if Capability.BASIC_WORKFLOW not in capabilities:
            capabilities.append(Capability.BASIC_WORKFLOW)
            provenance.append(
                _policy_provenance(
                    f"capability:{Capability.BASIC_WORKFLOW.value}",
                    "Basic workflow capability is required only when an evidence-backed workflow is emitted.",
                )
            )

    for uncertainty in document_ir.uncertainties:
        evidence = set(uncertainty.evidence_ids)
        affected_fields = tuple(
            field_id
            for field_id, refs in field_document_refs.items()
            if evidence.intersection(refs)
        )
        critical = bool(affected_fields) or uncertainty.code is UncertaintyCode.UNKNOWN
        uncertainties.append(
            AppSpecUncertainty(
                uncertainty_id=f"document:{uncertainty.uncertainty_id}",
                message=f"DocumentIR {uncertainty.code.value}: {uncertainty.message}",
                critical=critical,
                target_ids=affected_fields,
                source_refs=uncertainty.evidence_ids,
            )
        )

    return ValidationWorkflowSynthesisResult(
        entities=surface.entities,
        views=surface.views,
        actions=tuple(actions),
        workflows=tuple(workflows),
        validations=tuple(validations),
        capabilities=tuple(capabilities),
        persistence=surface.persistence,
        provenance=tuple(provenance),
        uncertainties=tuple(uncertainties),
    )
