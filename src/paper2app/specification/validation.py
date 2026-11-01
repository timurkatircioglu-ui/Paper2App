"""Deterministic AppSpec validation and runtime capability gating for F03-W05."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from paper2app.understanding.document_ir import DocumentIR

from .app_spec import (
    APP_SPEC_SCHEMA,
    APP_SPEC_SCHEMA_VERSION,
    ActionKind,
    AppField,
    AppSpec,
    Capability,
    ConditionOperator,
    FieldType,
    ValidationRuleKind,
)
from .behavior_synthesis import synthesize_validations_workflows
from .surface_policy import synthesize_views_actions_persistence
from .synthesis import synthesize_entity_fields


class AppSpecValidationStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"


class AppSpecValidationSeverity(str, Enum):
    WARNING = "WARNING"
    ERROR = "ERROR"


class AppSpecValidationIssueCode(str, Enum):
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    VERSION_MISMATCH = "VERSION_MISMATCH"
    DUPLICATE_ID = "DUPLICATE_ID"
    PRIMARY_ENTITY_MISSING = "PRIMARY_ENTITY_MISSING"
    REFERENCE_MISSING = "REFERENCE_MISSING"
    REFERENCE_SCOPE_MISMATCH = "REFERENCE_SCOPE_MISMATCH"
    DEFAULT_VALUE_INCOMPATIBLE = "DEFAULT_VALUE_INCOMPATIBLE"
    VALIDATION_RULE_INCOMPATIBLE = "VALIDATION_RULE_INCOMPATIBLE"
    WORKFLOW_GRAPH_INVALID = "WORKFLOW_GRAPH_INVALID"
    REQUIRED_CAPABILITY_MISSING = "REQUIRED_CAPABILITY_MISSING"
    RUNTIME_CAPABILITY_UNSUPPORTED = "RUNTIME_CAPABILITY_UNSUPPORTED"
    UNUSED_CAPABILITY = "UNUSED_CAPABILITY"
    CRITICAL_UNCERTAINTY = "CRITICAL_UNCERTAINTY"
    NONCRITICAL_UNCERTAINTY = "NONCRITICAL_UNCERTAINTY"
    PROVENANCE_TARGET_MISSING = "PROVENANCE_TARGET_MISSING"


@dataclass(frozen=True, slots=True)
class AppSpecValidationIssue:
    code: AppSpecValidationIssueCode
    severity: AppSpecValidationSeverity
    message: str
    target_id: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeCapabilityProfile:
    profile_id: str
    supported_capabilities: tuple[Capability, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not self.profile_id.strip():
            raise ValueError("profile_id must be a non-empty string")
        if not isinstance(self.supported_capabilities, tuple):
            raise TypeError("supported_capabilities must be a tuple")
        if not all(isinstance(item, Capability) for item in self.supported_capabilities):
            raise TypeError("supported_capabilities contains an invalid value")
        if len(set(self.supported_capabilities)) != len(self.supported_capabilities):
            raise ValueError("supported_capabilities must not contain duplicates")


COMPETITION_V1_RUNTIME_PROFILE = RuntimeCapabilityProfile(
    profile_id="competition_v1",
    supported_capabilities=tuple(Capability),
)


@dataclass(frozen=True, slots=True)
class AppSpecValidationReport:
    status: AppSpecValidationStatus
    issues: tuple[AppSpecValidationIssue, ...]
    required_capabilities: tuple[Capability, ...]
    runtime_profile_id: str

    @property
    def valid(self) -> bool:
        return self.status is not AppSpecValidationStatus.FAIL


class AppSpecValidationError(ValueError):
    def __init__(self, report: AppSpecValidationReport) -> None:
        self.report = report
        codes = ", ".join(issue.code.value for issue in report.issues if issue.severity is AppSpecValidationSeverity.ERROR)
        super().__init__(f"AppSpec validation failed: {codes or 'unknown error'}")


def _issue(
    issues: list[AppSpecValidationIssue],
    code: AppSpecValidationIssueCode,
    severity: AppSpecValidationSeverity,
    message: str,
    target_id: str | None = None,
) -> None:
    issues.append(AppSpecValidationIssue(code=code, severity=severity, message=message, target_id=target_id))


def _value_compatible(field: AppField, value: object) -> bool:
    if value is None:
        return True
    field_type = field.field_type
    if field_type in {
        FieldType.STRING,
        FieldType.MULTILINE_STRING,
        FieldType.DATE,
        FieldType.TIME,
        FieldType.DATETIME,
        FieldType.SIGNATURE,
        FieldType.EMAIL,
        FieldType.PHONE,
        FieldType.IDENTIFIER,
    }:
        return isinstance(value, str)
    if field_type is FieldType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    if field_type is FieldType.DECIMAL:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if field_type is FieldType.BOOLEAN:
        return isinstance(value, bool)
    if field_type is FieldType.ENUM:
        return isinstance(value, str) and value in field.options
    if field_type is FieldType.MULTI_ENUM:
        return isinstance(value, tuple) and all(isinstance(item, str) and item in field.options for item in value)
    return False


def _validation_compatible(field: AppField, kind: ValidationRuleKind, value: object) -> bool:
    if kind is ValidationRuleKind.REQUIRED:
        return value is None
    if kind in {ValidationRuleKind.MIN, ValidationRuleKind.MAX}:
        return field.field_type in {FieldType.INTEGER, FieldType.DECIMAL} and isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind in {ValidationRuleKind.MIN_LENGTH, ValidationRuleKind.MAX_LENGTH}:
        return (
            field.field_type
            in {
                FieldType.STRING,
                FieldType.MULTILINE_STRING,
                FieldType.EMAIL,
                FieldType.PHONE,
                FieldType.IDENTIFIER,
            }
            and isinstance(value, int)
            and not isinstance(value, bool)
            and value >= 0
        )
    if kind is ValidationRuleKind.ALLOWED_VALUES:
        return (
            field.field_type in {FieldType.ENUM, FieldType.MULTI_ENUM}
            and isinstance(value, tuple)
            and bool(value)
            and all(isinstance(item, str) and item in field.options for item in value)
        )
    if kind is ValidationRuleKind.FORMAT:
        expected = {
            FieldType.EMAIL: "email",
            FieldType.PHONE: "phone",
            FieldType.IDENTIFIER: "identifier",
        }.get(field.field_type)
        return isinstance(value, str) and expected == value
    return False


def _required_capabilities(app_spec: AppSpec) -> tuple[Capability, ...]:
    required: set[Capability] = set()
    action_map = {
        ActionKind.CREATE_RECORD: Capability.RECORD_CREATE,
        ActionKind.UPDATE_RECORD: Capability.RECORD_UPDATE,
        ActionKind.VIEW_RECORD: Capability.RECORD_VIEW,
        ActionKind.LIST_RECORDS: Capability.RECORD_LIST,
        ActionKind.SEARCH_RECORDS: Capability.RECORD_SEARCH,
        ActionKind.FILTER_RECORDS: Capability.RECORD_FILTER,
        ActionKind.CHANGE_STATE: Capability.BASIC_WORKFLOW,
    }
    for action in app_spec.actions:
        required.add(action_map[action.kind])
    if app_spec.persistence.required or app_spec.persistence.survive_reload:
        required.add(Capability.PERSISTENCE)
    for entity in app_spec.entities:
        for field in entity.fields:
            if field.field_type is FieldType.MULTI_ENUM:
                required.add(Capability.MULTI_CHOICE)
            if field.field_type is FieldType.SIGNATURE:
                required.add(Capability.SIGNATURE_CAPTURE)
    if app_spec.workflows:
        required.add(Capability.BASIC_WORKFLOW)
    return tuple(capability for capability in Capability if capability in required)


def _target_ids(app_spec: AppSpec) -> set[str]:
    values = {app_spec.app.app_id, "persistence"}
    values.update(entity.entity_id for entity in app_spec.entities)
    for entity in app_spec.entities:
        values.update(field.field_id for field in entity.fields)
    values.update(view.view_id for view in app_spec.views)
    values.update(action.action_id for action in app_spec.actions)
    values.update(workflow.workflow_id for workflow in app_spec.workflows)
    values.update(validation.validation_id for validation in app_spec.validations)
    values.update(f"capability:{capability.value}" for capability in app_spec.capabilities)
    return values


def _check_duplicate_ids(app_spec: AppSpec, issues: list[AppSpecValidationIssue]) -> None:
    collections: tuple[tuple[str, Iterable[str]], ...] = (
        ("entity", (item.entity_id for item in app_spec.entities)),
        ("field", (field.field_id for entity in app_spec.entities for field in entity.fields)),
        ("view", (item.view_id for item in app_spec.views)),
        ("action", (item.action_id for item in app_spec.actions)),
        ("workflow", (item.workflow_id for item in app_spec.workflows)),
        ("validation", (item.validation_id for item in app_spec.validations)),
        ("provenance", (item.provenance_id for item in app_spec.provenance)),
        ("uncertainty", (item.uncertainty_id for item in app_spec.uncertainties)),
    )
    for label, ids in collections:
        seen: set[str] = set()
        for value in ids:
            if value in seen:
                _issue(
                    issues,
                    AppSpecValidationIssueCode.DUPLICATE_ID,
                    AppSpecValidationSeverity.ERROR,
                    f"duplicate {label} id: {value}",
                    value,
                )
            seen.add(value)


def validate_app_spec(
    app_spec: AppSpec,
    runtime_profile: RuntimeCapabilityProfile = COMPETITION_V1_RUNTIME_PROFILE,
) -> AppSpecValidationReport:
    if not isinstance(app_spec, AppSpec):
        raise TypeError("app_spec must be an AppSpec")
    if not isinstance(runtime_profile, RuntimeCapabilityProfile):
        raise TypeError("runtime_profile must be a RuntimeCapabilityProfile")

    issues: list[AppSpecValidationIssue] = []

    if app_spec.schema != APP_SPEC_SCHEMA:
        _issue(issues, AppSpecValidationIssueCode.SCHEMA_MISMATCH, AppSpecValidationSeverity.ERROR, "unknown AppSpec schema")
    if app_spec.schema_version != APP_SPEC_SCHEMA_VERSION:
        _issue(issues, AppSpecValidationIssueCode.VERSION_MISMATCH, AppSpecValidationSeverity.ERROR, "unknown AppSpec schema version")

    _check_duplicate_ids(app_spec, issues)

    entity_by_id = {entity.entity_id: entity for entity in app_spec.entities}
    field_by_id = {field.field_id: field for entity in app_spec.entities for field in entity.fields}
    field_owner = {field.field_id: entity.entity_id for entity in app_spec.entities for field in entity.fields}
    workflow_by_id = {workflow.workflow_id: workflow for workflow in app_spec.workflows}

    if app_spec.app.primary_entity_id not in entity_by_id:
        _issue(
            issues,
            AppSpecValidationIssueCode.PRIMARY_ENTITY_MISSING,
            AppSpecValidationSeverity.ERROR,
            "app primary_entity_id does not resolve",
            app_spec.app.primary_entity_id,
        )

    for field in field_by_id.values():
        if not _value_compatible(field, field.default_value):
            _issue(
                issues,
                AppSpecValidationIssueCode.DEFAULT_VALUE_INCOMPATIBLE,
                AppSpecValidationSeverity.ERROR,
                "field default_value is incompatible with field_type/options",
                field.field_id,
            )

    for view in app_spec.views:
        entity = entity_by_id.get(view.entity_id)
        if entity is None:
            _issue(issues, AppSpecValidationIssueCode.REFERENCE_MISSING, AppSpecValidationSeverity.ERROR, "view entity does not resolve", view.view_id)
            continue
        allowed_fields = {field.field_id for field in entity.fields}
        for field_id in view.field_ids:
            if field_id not in field_by_id:
                _issue(issues, AppSpecValidationIssueCode.REFERENCE_MISSING, AppSpecValidationSeverity.ERROR, "view field does not resolve", view.view_id)
            elif field_id not in allowed_fields:
                _issue(issues, AppSpecValidationIssueCode.REFERENCE_SCOPE_MISMATCH, AppSpecValidationSeverity.ERROR, "view field belongs to a different entity", view.view_id)

    for action in app_spec.actions:
        if action.entity_id not in entity_by_id:
            _issue(issues, AppSpecValidationIssueCode.REFERENCE_MISSING, AppSpecValidationSeverity.ERROR, "action entity does not resolve", action.action_id)
        if action.kind is ActionKind.CHANGE_STATE:
            if action.workflow_id is None or action.workflow_id not in workflow_by_id:
                _issue(issues, AppSpecValidationIssueCode.REFERENCE_MISSING, AppSpecValidationSeverity.ERROR, "change_state action requires a known workflow", action.action_id)
            elif workflow_by_id[action.workflow_id].entity_id != action.entity_id:
                _issue(issues, AppSpecValidationIssueCode.REFERENCE_SCOPE_MISMATCH, AppSpecValidationSeverity.ERROR, "action workflow belongs to a different entity", action.action_id)
        elif action.workflow_id is not None:
            _issue(issues, AppSpecValidationIssueCode.REFERENCE_SCOPE_MISMATCH, AppSpecValidationSeverity.ERROR, "only change_state actions may reference a workflow", action.action_id)

    for validation in app_spec.validations:
        field = field_by_id.get(validation.field_id)
        if validation.entity_id not in entity_by_id or field is None:
            _issue(issues, AppSpecValidationIssueCode.REFERENCE_MISSING, AppSpecValidationSeverity.ERROR, "validation entity/field reference does not resolve", validation.validation_id)
            continue
        if field_owner[validation.field_id] != validation.entity_id:
            _issue(issues, AppSpecValidationIssueCode.REFERENCE_SCOPE_MISMATCH, AppSpecValidationSeverity.ERROR, "validation field belongs to a different entity", validation.validation_id)
            continue
        if not _validation_compatible(field, validation.kind, validation.value):
            _issue(issues, AppSpecValidationIssueCode.VALIDATION_RULE_INCOMPATIBLE, AppSpecValidationSeverity.ERROR, "validation rule is incompatible with field type/options", validation.validation_id)

    for workflow in app_spec.workflows:
        entity = entity_by_id.get(workflow.entity_id)
        if entity is None:
            _issue(issues, AppSpecValidationIssueCode.REFERENCE_MISSING, AppSpecValidationSeverity.ERROR, "workflow entity does not resolve", workflow.workflow_id)
            continue
        state_ids = [state.state_id for state in workflow.states]
        if len(set(state_ids)) != len(state_ids) or workflow.initial_state_id not in set(state_ids):
            _issue(issues, AppSpecValidationIssueCode.WORKFLOW_GRAPH_INVALID, AppSpecValidationSeverity.ERROR, "workflow states are duplicated or initial state does not resolve", workflow.workflow_id)
        condition_ids = [condition.condition_id for condition in workflow.conditions]
        if len(set(condition_ids)) != len(condition_ids):
            _issue(issues, AppSpecValidationIssueCode.WORKFLOW_GRAPH_INVALID, AppSpecValidationSeverity.ERROR, "workflow condition ids must be unique", workflow.workflow_id)
        transition_ids = [transition.transition_id for transition in workflow.transitions]
        if len(set(transition_ids)) != len(transition_ids):
            _issue(issues, AppSpecValidationIssueCode.WORKFLOW_GRAPH_INVALID, AppSpecValidationSeverity.ERROR, "workflow transition ids must be unique", workflow.workflow_id)

        entity_fields = {field.field_id: field for field in entity.fields}
        known_conditions = set(condition_ids)
        known_states = set(state_ids)
        for condition in workflow.conditions:
            field = entity_fields.get(condition.field_id)
            if field is None:
                _issue(issues, AppSpecValidationIssueCode.REFERENCE_MISSING, AppSpecValidationSeverity.ERROR, "workflow condition field does not resolve in workflow entity", condition.condition_id)
                continue
            if condition.operator is ConditionOperator.IS_SET:
                if condition.expected_value is not None:
                    _issue(issues, AppSpecValidationIssueCode.WORKFLOW_GRAPH_INVALID, AppSpecValidationSeverity.ERROR, "is_set condition must not carry expected_value", condition.condition_id)
            elif not _value_compatible(field, condition.expected_value):
                _issue(issues, AppSpecValidationIssueCode.WORKFLOW_GRAPH_INVALID, AppSpecValidationSeverity.ERROR, "workflow expected_value is incompatible with field", condition.condition_id)
        adjacency: dict[str, set[str]] = {state_id: set() for state_id in known_states}
        for transition in workflow.transitions:
            if transition.from_state_id not in known_states or transition.to_state_id not in known_states:
                _issue(issues, AppSpecValidationIssueCode.WORKFLOW_GRAPH_INVALID, AppSpecValidationSeverity.ERROR, "workflow transition state does not resolve", transition.transition_id)
                continue
            if any(condition_id not in known_conditions for condition_id in transition.condition_ids):
                _issue(issues, AppSpecValidationIssueCode.REFERENCE_MISSING, AppSpecValidationSeverity.ERROR, "workflow transition condition does not resolve", transition.transition_id)
            adjacency[transition.from_state_id].add(transition.to_state_id)

        if workflow.initial_state_id in known_states:
            reachable = {workflow.initial_state_id}
            frontier = [workflow.initial_state_id]
            while frontier:
                current = frontier.pop()
                for target in adjacency.get(current, set()):
                    if target not in reachable:
                        reachable.add(target)
                        frontier.append(target)
            if reachable != known_states:
                _issue(issues, AppSpecValidationIssueCode.WORKFLOW_GRAPH_INVALID, AppSpecValidationSeverity.ERROR, "workflow contains states unreachable from initial state", workflow.workflow_id)

    required_capabilities = _required_capabilities(app_spec)
    declared = set(app_spec.capabilities)
    supported = set(runtime_profile.supported_capabilities)
    for capability in required_capabilities:
        if capability not in declared:
            _issue(issues, AppSpecValidationIssueCode.REQUIRED_CAPABILITY_MISSING, AppSpecValidationSeverity.ERROR, "required capability is not declared", f"capability:{capability.value}")
        if capability not in supported:
            _issue(issues, AppSpecValidationIssueCode.RUNTIME_CAPABILITY_UNSUPPORTED, AppSpecValidationSeverity.ERROR, f"runtime profile {runtime_profile.profile_id} does not support required capability", f"capability:{capability.value}")
    for capability in app_spec.capabilities:
        if capability not in required_capabilities:
            _issue(issues, AppSpecValidationIssueCode.UNUSED_CAPABILITY, AppSpecValidationSeverity.WARNING, "declared capability is not required by the current AppSpec surface", f"capability:{capability.value}")

    targets = _target_ids(app_spec)
    for provenance in app_spec.provenance:
        if provenance.target_id not in targets:
            _issue(issues, AppSpecValidationIssueCode.PROVENANCE_TARGET_MISSING, AppSpecValidationSeverity.ERROR, "provenance target_id does not resolve", provenance.provenance_id)

    for uncertainty in app_spec.uncertainties:
        if uncertainty.critical:
            _issue(issues, AppSpecValidationIssueCode.CRITICAL_UNCERTAINTY, AppSpecValidationSeverity.ERROR, uncertainty.message, uncertainty.uncertainty_id)
        else:
            _issue(issues, AppSpecValidationIssueCode.NONCRITICAL_UNCERTAINTY, AppSpecValidationSeverity.WARNING, uncertainty.message, uncertainty.uncertainty_id)

    has_error = any(issue.severity is AppSpecValidationSeverity.ERROR for issue in issues)
    has_warning = any(issue.severity is AppSpecValidationSeverity.WARNING for issue in issues)
    status = (
        AppSpecValidationStatus.FAIL
        if has_error
        else AppSpecValidationStatus.PASS_WITH_WARNINGS
        if has_warning
        else AppSpecValidationStatus.PASS
    )
    return AppSpecValidationReport(
        status=status,
        issues=tuple(issues),
        required_capabilities=required_capabilities,
        runtime_profile_id=runtime_profile.profile_id,
    )


def require_valid_app_spec(
    app_spec: AppSpec,
    runtime_profile: RuntimeCapabilityProfile = COMPETITION_V1_RUNTIME_PROFILE,
) -> AppSpec:
    report = validate_app_spec(app_spec, runtime_profile)
    if not report.valid:
        raise AppSpecValidationError(report)
    return app_spec


def _app_identity_for(document_ir: DocumentIR, entities) -> tuple[str, str, str, str]:
    if entities:
        primary = entities[0]
        base = primary.entity_id.removesuffix("_record") or "generated"
        display = primary.display_name.removesuffix(" Record") or primary.display_name
        return f"{base}_app", f"{display} App", "Generated from a validated paper workflow.", primary.entity_id
    return "paper2app_generated_app", "Generated App", "Generated from a validated paper workflow.", "unresolved_primary_entity"


def assemble_app_spec_candidate(document_ir: DocumentIR) -> AppSpec:
    entity_fields = synthesize_entity_fields(document_ir)
    surface = synthesize_views_actions_persistence(entity_fields)
    behavior = synthesize_validations_workflows(document_ir, surface)
    app_id, display_name, description, primary_entity_id = _app_identity_for(document_ir, behavior.entities)
    from .app_spec import AppIdentity, ProvenanceClass, ProvenanceRecord

    app_provenance = ProvenanceRecord(
        provenance_id=f"policy:{app_id}",
        target_id=app_id,
        provenance_class=ProvenanceClass.PRODUCT_POLICY,
        source_refs=(),
        note="Top-level application identity is derived from the synthesized primary entity under Competition V1 policy.",
    )
    return AppSpec(
        app=AppIdentity(app_id, display_name, description, primary_entity_id),
        entities=behavior.entities,
        views=behavior.views,
        actions=behavior.actions,
        workflows=behavior.workflows,
        validations=behavior.validations,
        capabilities=behavior.capabilities,
        persistence=behavior.persistence,
        provenance=behavior.provenance + (app_provenance,),
        uncertainties=behavior.uncertainties,
    )


def synthesize_validated_app_spec(
    document_ir: DocumentIR,
    runtime_profile: RuntimeCapabilityProfile = COMPETITION_V1_RUNTIME_PROFILE,
) -> AppSpec:
    return require_valid_app_spec(assemble_app_spec_candidate(document_ir), runtime_profile)
