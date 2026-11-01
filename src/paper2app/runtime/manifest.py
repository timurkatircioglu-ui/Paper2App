"""Concrete runtime capability manifest for Paper2App F04-W01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, TypeVar

from paper2app.specification.app_spec import (
    APP_SPEC_SCHEMA_VERSION,
    ActionKind,
    AppSpec,
    Capability,
    ConditionOperator,
    FieldType,
    ValidationRuleKind,
    ViewKind,
)

if TYPE_CHECKING:
    from paper2app.specification.validation import RuntimeCapabilityProfile


class RuntimeSurface(str, Enum):
    APP_SPEC_SCHEMA_VERSION = "app_spec_schema_version"
    FIELD_TYPE = "field_type"
    VIEW_KIND = "view_kind"
    ACTION_KIND = "action_kind"
    VALIDATION_RULE = "validation_rule"
    CONDITION_OPERATOR = "condition_operator"
    CAPABILITY = "capability"
    WORKFLOW = "workflow"


@dataclass(frozen=True, slots=True)
class RuntimeCompatibilityIssue:
    surface: RuntimeSurface
    value: str
    target_id: str | None = None


_EnumT = TypeVar("_EnumT", bound=Enum)


def _validate_enum_tuple(name: str, values: tuple[_EnumT, ...], enum_type: type[_EnumT]) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    if not values:
        raise ValueError(f"{name} must not be empty")
    if not all(isinstance(value, enum_type) for value in values):
        raise TypeError(f"{name} contains an invalid value")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must not contain duplicates")


@dataclass(frozen=True, slots=True)
class RuntimeManifest:
    manifest_id: str
    manifest_version: str
    supported_app_spec_versions: tuple[str, ...]
    supported_field_types: tuple[FieldType, ...]
    supported_view_kinds: tuple[ViewKind, ...]
    supported_action_kinds: tuple[ActionKind, ...]
    supported_validation_rules: tuple[ValidationRuleKind, ...]
    supported_condition_operators: tuple[ConditionOperator, ...]
    supported_capabilities: tuple[Capability, ...]
    workflows_enabled: bool
    max_workflows_per_entity: int

    def __post_init__(self) -> None:
        if not isinstance(self.manifest_id, str) or not self.manifest_id.strip():
            raise ValueError("manifest_id must be a non-empty string")
        if not isinstance(self.manifest_version, str) or not self.manifest_version.strip():
            raise ValueError("manifest_version must be a non-empty string")
        if not isinstance(self.supported_app_spec_versions, tuple) or not self.supported_app_spec_versions:
            raise ValueError("supported_app_spec_versions must be a non-empty tuple")
        if not all(isinstance(value, str) and value.strip() for value in self.supported_app_spec_versions):
            raise TypeError("supported_app_spec_versions contains an invalid value")
        if len(set(self.supported_app_spec_versions)) != len(self.supported_app_spec_versions):
            raise ValueError("supported_app_spec_versions must not contain duplicates")
        _validate_enum_tuple("supported_field_types", self.supported_field_types, FieldType)
        _validate_enum_tuple("supported_view_kinds", self.supported_view_kinds, ViewKind)
        _validate_enum_tuple("supported_action_kinds", self.supported_action_kinds, ActionKind)
        _validate_enum_tuple("supported_validation_rules", self.supported_validation_rules, ValidationRuleKind)
        _validate_enum_tuple("supported_condition_operators", self.supported_condition_operators, ConditionOperator)
        _validate_enum_tuple("supported_capabilities", self.supported_capabilities, Capability)
        if not isinstance(self.workflows_enabled, bool):
            raise TypeError("workflows_enabled must be a bool")
        if not isinstance(self.max_workflows_per_entity, int) or isinstance(self.max_workflows_per_entity, bool):
            raise TypeError("max_workflows_per_entity must be an int")
        if self.max_workflows_per_entity < 0:
            raise ValueError("max_workflows_per_entity must be >= 0")
        if self.workflows_enabled and self.max_workflows_per_entity < 1:
            raise ValueError("enabled workflows require max_workflows_per_entity >= 1")
        if not self.workflows_enabled and self.max_workflows_per_entity != 0:
            raise ValueError("disabled workflows require max_workflows_per_entity == 0")

    def capability_profile(self) -> "RuntimeCapabilityProfile":
        # Local import avoids making runtime package initialization depend on
        # specification.validation while that module derives its default profile.
        from paper2app.specification.validation import RuntimeCapabilityProfile

        return RuntimeCapabilityProfile(
            profile_id=self.manifest_id,
            supported_capabilities=self.supported_capabilities,
        )

    def compatibility_issues(self, app_spec: AppSpec) -> tuple[RuntimeCompatibilityIssue, ...]:
        if not isinstance(app_spec, AppSpec):
            raise TypeError("app_spec must be an AppSpec")

        issues: list[RuntimeCompatibilityIssue] = []
        if app_spec.schema_version not in self.supported_app_spec_versions:
            issues.append(
                RuntimeCompatibilityIssue(
                    RuntimeSurface.APP_SPEC_SCHEMA_VERSION,
                    app_spec.schema_version,
                )
            )

        for entity in app_spec.entities:
            for field in entity.fields:
                if field.field_type not in self.supported_field_types:
                    issues.append(RuntimeCompatibilityIssue(RuntimeSurface.FIELD_TYPE, field.field_type.value, field.field_id))

        for view in app_spec.views:
            if view.kind not in self.supported_view_kinds:
                issues.append(RuntimeCompatibilityIssue(RuntimeSurface.VIEW_KIND, view.kind.value, view.view_id))

        for action in app_spec.actions:
            if action.kind not in self.supported_action_kinds:
                issues.append(RuntimeCompatibilityIssue(RuntimeSurface.ACTION_KIND, action.kind.value, action.action_id))

        for validation in app_spec.validations:
            if validation.kind not in self.supported_validation_rules:
                issues.append(
                    RuntimeCompatibilityIssue(RuntimeSurface.VALIDATION_RULE, validation.kind.value, validation.validation_id)
                )

        workflow_counts: dict[str, int] = {}
        for workflow in app_spec.workflows:
            workflow_counts[workflow.entity_id] = workflow_counts.get(workflow.entity_id, 0) + 1
            if not self.workflows_enabled:
                issues.append(RuntimeCompatibilityIssue(RuntimeSurface.WORKFLOW, "disabled", workflow.workflow_id))
            for condition in workflow.conditions:
                if condition.operator not in self.supported_condition_operators:
                    issues.append(
                        RuntimeCompatibilityIssue(
                            RuntimeSurface.CONDITION_OPERATOR,
                            condition.operator.value,
                            condition.condition_id,
                        )
                    )
        if self.workflows_enabled:
            for entity_id, count in workflow_counts.items():
                if count > self.max_workflows_per_entity:
                    issues.append(
                        RuntimeCompatibilityIssue(
                            RuntimeSurface.WORKFLOW,
                            f"count:{count}",
                            entity_id,
                        )
                    )

        for capability in app_spec.capabilities:
            if capability not in self.supported_capabilities:
                issues.append(
                    RuntimeCompatibilityIssue(RuntimeSurface.CAPABILITY, capability.value, f"capability:{capability.value}")
                )

        return tuple(issues)


COMPETITION_V1_RUNTIME_MANIFEST = RuntimeManifest(
    manifest_id="competition_v1",
    manifest_version="0.1",
    supported_app_spec_versions=(APP_SPEC_SCHEMA_VERSION,),
    supported_field_types=tuple(FieldType),
    supported_view_kinds=tuple(ViewKind),
    supported_action_kinds=tuple(ActionKind),
    supported_validation_rules=tuple(ValidationRuleKind),
    supported_condition_operators=tuple(ConditionOperator),
    supported_capabilities=tuple(Capability),
    workflows_enabled=True,
    max_workflows_per_entity=1,
)
