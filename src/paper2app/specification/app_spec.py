"""Technology-independent AppSpec runtime contracts for Paper2App."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


APP_SPEC_SCHEMA = "paper2app.app_spec"
APP_SPEC_SCHEMA_VERSION = "0.1"


class FieldType(str, Enum):
    STRING = "string"
    MULTILINE_STRING = "multiline_string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    ENUM = "enum"
    MULTI_ENUM = "multi_enum"
    SIGNATURE = "signature"
    EMAIL = "email"
    PHONE = "phone"
    IDENTIFIER = "identifier"


class ViewKind(str, Enum):
    FORM = "form"
    RECORD_LIST = "record_list"
    RECORD_DETAIL = "record_detail"


class ActionKind(str, Enum):
    CREATE_RECORD = "create_record"
    UPDATE_RECORD = "update_record"
    VIEW_RECORD = "view_record"
    LIST_RECORDS = "list_records"
    SEARCH_RECORDS = "search_records"
    FILTER_RECORDS = "filter_records"
    CHANGE_STATE = "change_state"


class ValidationRuleKind(str, Enum):
    REQUIRED = "required"
    MIN = "min"
    MAX = "max"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    ALLOWED_VALUES = "allowed_values"
    FORMAT = "format"


class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IS_SET = "is_set"


class Capability(str, Enum):
    RECORD_CREATE = "record_create"
    RECORD_UPDATE = "record_update"
    RECORD_VIEW = "record_view"
    RECORD_LIST = "record_list"
    RECORD_SEARCH = "record_search"
    RECORD_FILTER = "record_filter"
    PERSISTENCE = "persistence"
    MULTI_CHOICE = "multi_choice"
    BASIC_WORKFLOW = "basic_workflow"
    SIGNATURE_CAPTURE = "signature_capture"


class ProvenanceClass(str, Enum):
    DOCUMENT_DERIVED = "DOCUMENT_DERIVED"
    PRODUCT_POLICY = "PRODUCT_POLICY"
    USER_CONFIRMED = "USER_CONFIRMED"


ScalarValue = str | int | float | bool | None
AppValue = ScalarValue | tuple[str, ...]


def _require_nonempty(value: str, name: str, *, maximum: int = 256) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if len(value) > maximum:
        raise ValueError(f"{name} must be at most {maximum} characters")


def _validate_optional_text(value: str | None, name: str, *, maximum: int = 512) -> None:
    if value is None:
        return
    _require_nonempty(value, name, maximum=maximum)


def _validate_string_tuple(value: tuple[str, ...], name: str, *, allow_empty: bool = True) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{name} must not be empty")
    for item in value:
        _require_nonempty(item, f"{name} item")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")


def _validate_app_value(value: AppValue, name: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{name} float must be finite")
        return
    if isinstance(value, tuple):
        _validate_string_tuple(value, name)
        return
    raise TypeError(f"{name} must be a bounded scalar or tuple of strings")


@dataclass(frozen=True, slots=True)
class AppIdentity:
    app_id: str
    display_name: str
    description: str
    primary_entity_id: str

    def __post_init__(self) -> None:
        _require_nonempty(self.app_id, "app_id")
        _require_nonempty(self.display_name, "display_name")
        _require_nonempty(self.description, "description", maximum=512)
        _require_nonempty(self.primary_entity_id, "primary_entity_id")


@dataclass(frozen=True, slots=True)
class AppField:
    field_id: str
    display_name: str
    field_type: FieldType
    options: tuple[str, ...] = ()
    default_value: AppValue = None

    def __post_init__(self) -> None:
        _require_nonempty(self.field_id, "field_id")
        _require_nonempty(self.display_name, "display_name")
        if not isinstance(self.field_type, FieldType):
            raise TypeError("field_type must be a FieldType")
        _validate_string_tuple(self.options, "options")
        if self.field_type in {FieldType.ENUM, FieldType.MULTI_ENUM}:
            if not self.options:
                raise ValueError("enum and multi_enum fields require at least one option")
        elif self.options:
            raise ValueError("only enum and multi_enum fields may define options")
        _validate_app_value(self.default_value, "default_value")


@dataclass(frozen=True, slots=True)
class AppEntity:
    entity_id: str
    display_name: str
    fields: tuple[AppField, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.entity_id, "entity_id")
        _require_nonempty(self.display_name, "display_name")
        if not isinstance(self.fields, tuple) or not self.fields:
            raise ValueError("fields must be a non-empty tuple")
        if not all(isinstance(field, AppField) for field in self.fields):
            raise TypeError("fields must contain AppField values")


@dataclass(frozen=True, slots=True)
class AppView:
    view_id: str
    kind: ViewKind
    entity_id: str
    field_ids: tuple[str, ...]
    title: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.view_id, "view_id")
        if not isinstance(self.kind, ViewKind):
            raise TypeError("kind must be a ViewKind")
        _require_nonempty(self.entity_id, "entity_id")
        _validate_string_tuple(self.field_ids, "field_ids")
        _validate_optional_text(self.title, "title")


@dataclass(frozen=True, slots=True)
class AppAction:
    action_id: str
    kind: ActionKind
    entity_id: str
    workflow_id: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.action_id, "action_id")
        if not isinstance(self.kind, ActionKind):
            raise TypeError("kind must be an ActionKind")
        _require_nonempty(self.entity_id, "entity_id")
        if self.workflow_id is not None:
            _require_nonempty(self.workflow_id, "workflow_id")


@dataclass(frozen=True, slots=True)
class AppValidation:
    validation_id: str
    entity_id: str
    field_id: str
    kind: ValidationRuleKind
    value: AppValue = None

    def __post_init__(self) -> None:
        _require_nonempty(self.validation_id, "validation_id")
        _require_nonempty(self.entity_id, "entity_id")
        _require_nonempty(self.field_id, "field_id")
        if not isinstance(self.kind, ValidationRuleKind):
            raise TypeError("kind must be a ValidationRuleKind")
        _validate_app_value(self.value, "validation value")


@dataclass(frozen=True, slots=True)
class WorkflowCondition:
    condition_id: str
    field_id: str
    operator: ConditionOperator
    expected_value: ScalarValue = None

    def __post_init__(self) -> None:
        _require_nonempty(self.condition_id, "condition_id")
        _require_nonempty(self.field_id, "field_id")
        if not isinstance(self.operator, ConditionOperator):
            raise TypeError("operator must be a ConditionOperator")
        _validate_app_value(self.expected_value, "expected_value")
        if isinstance(self.expected_value, tuple):
            raise TypeError("workflow expected_value must be scalar")


@dataclass(frozen=True, slots=True)
class WorkflowState:
    state_id: str
    display_name: str

    def __post_init__(self) -> None:
        _require_nonempty(self.state_id, "state_id")
        _require_nonempty(self.display_name, "display_name")


@dataclass(frozen=True, slots=True)
class WorkflowTransition:
    transition_id: str
    from_state_id: str
    to_state_id: str
    condition_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_nonempty(self.transition_id, "transition_id")
        _require_nonempty(self.from_state_id, "from_state_id")
        _require_nonempty(self.to_state_id, "to_state_id")
        if self.from_state_id == self.to_state_id:
            raise ValueError("workflow transition states must differ")
        _validate_string_tuple(self.condition_ids, "condition_ids")


@dataclass(frozen=True, slots=True)
class AppWorkflow:
    workflow_id: str
    entity_id: str
    states: tuple[WorkflowState, ...]
    initial_state_id: str
    conditions: tuple[WorkflowCondition, ...] = ()
    transitions: tuple[WorkflowTransition, ...] = ()

    def __post_init__(self) -> None:
        _require_nonempty(self.workflow_id, "workflow_id")
        _require_nonempty(self.entity_id, "entity_id")
        if not isinstance(self.states, tuple) or not self.states:
            raise ValueError("states must be a non-empty tuple")
        if not all(isinstance(state, WorkflowState) for state in self.states):
            raise TypeError("states must contain WorkflowState values")
        _require_nonempty(self.initial_state_id, "initial_state_id")
        if not isinstance(self.conditions, tuple) or not all(
            isinstance(condition, WorkflowCondition) for condition in self.conditions
        ):
            raise TypeError("conditions must be a tuple of WorkflowCondition values")
        if not isinstance(self.transitions, tuple) or not all(
            isinstance(transition, WorkflowTransition) for transition in self.transitions
        ):
            raise TypeError("transitions must be a tuple of WorkflowTransition values")


@dataclass(frozen=True, slots=True)
class PersistenceRequirement:
    required: bool = True
    survive_reload: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.required, bool):
            raise TypeError("required must be a bool")
        if not isinstance(self.survive_reload, bool):
            raise TypeError("survive_reload must be a bool")


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    provenance_id: str
    target_id: str
    provenance_class: ProvenanceClass
    source_refs: tuple[str, ...] = ()
    note: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.provenance_id, "provenance_id")
        _require_nonempty(self.target_id, "target_id")
        if not isinstance(self.provenance_class, ProvenanceClass):
            raise TypeError("provenance_class must be a ProvenanceClass")
        _validate_string_tuple(self.source_refs, "source_refs")
        _validate_optional_text(self.note, "note", maximum=256)


@dataclass(frozen=True, slots=True)
class AppSpecUncertainty:
    uncertainty_id: str
    message: str
    critical: bool
    target_ids: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_nonempty(self.uncertainty_id, "uncertainty_id")
        _require_nonempty(self.message, "message", maximum=512)
        if not isinstance(self.critical, bool):
            raise TypeError("critical must be a bool")
        _validate_string_tuple(self.target_ids, "target_ids")
        _validate_string_tuple(self.source_refs, "source_refs")


@dataclass(frozen=True, slots=True)
class AppSpec:
    app: AppIdentity
    entities: tuple[AppEntity, ...]
    views: tuple[AppView, ...]
    actions: tuple[AppAction, ...]
    workflows: tuple[AppWorkflow, ...]
    validations: tuple[AppValidation, ...]
    capabilities: tuple[Capability, ...]
    persistence: PersistenceRequirement
    provenance: tuple[ProvenanceRecord, ...]
    uncertainties: tuple[AppSpecUncertainty, ...]
    schema: str = APP_SPEC_SCHEMA
    schema_version: str = APP_SPEC_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != APP_SPEC_SCHEMA:
            raise ValueError("unknown AppSpec schema")
        if self.schema_version != APP_SPEC_SCHEMA_VERSION:
            raise ValueError("unknown AppSpec schema_version")
        if not isinstance(self.app, AppIdentity):
            raise TypeError("app must be an AppIdentity")
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
