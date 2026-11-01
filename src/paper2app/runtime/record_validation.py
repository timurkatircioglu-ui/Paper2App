"""Authoritative deterministic record validation for Paper2App F04-W02."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import Enum
import math
import re
from collections.abc import Mapping

from paper2app.specification.app_spec import (
    AppEntity,
    AppField,
    AppValidation,
    FieldType,
    ValidationRuleKind,
)

from .registry import RegisteredAppSpec, RuntimeFailureCode, RuntimeRegistryError


RecordScalar = str | int | float | bool | None
RecordValue = RecordScalar | tuple[str, ...]


class RecordValidationIssueCode(str, Enum):
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    REQUIRED_FIELD_MISSING = "REQUIRED_FIELD_MISSING"
    INVALID_FIELD_TYPE = "INVALID_FIELD_TYPE"
    INVALID_CHOICE = "INVALID_CHOICE"
    DUPLICATE_CHOICE = "DUPLICATE_CHOICE"
    VALIDATION_RULE_FAILED = "VALIDATION_RULE_FAILED"


@dataclass(frozen=True, slots=True)
class RecordValidationIssue:
    code: RecordValidationIssueCode
    message: str
    field_id: str | None = None
    validation_id: str | None = None


@dataclass(frozen=True, slots=True)
class ValidatedRecordPayload:
    registration_id: str
    app_id: str
    entity_id: str
    values: tuple[tuple[str, RecordValue], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            field_id: list(value) if isinstance(value, tuple) else value
            for field_id, value in self.values
        }


@dataclass(frozen=True, slots=True)
class RecordValidationReport:
    valid: bool
    issues: tuple[RecordValidationIssue, ...]
    normalized: ValidatedRecordPayload | None


class RecordValidationError(RuntimeRegistryError):
    def __init__(self, report: RecordValidationReport) -> None:
        self.report = report
        details = tuple(
            f"{issue.code.value}:{issue.field_id or issue.validation_id or '-'}"
            for issue in report.issues
        )
        super().__init__(
            RuntimeFailureCode.RECORD_VALIDATION_FAILED,
            "record validation failed",
            details=details,
        )


_MISSING = object()
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_ALLOWED_RE = re.compile(r"^[+0-9() .-]+$")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


def _entity_for(registered: RegisteredAppSpec, entity_id: str) -> AppEntity | None:
    return next((entity for entity in registered.app_spec.entities if entity.entity_id == entity_id), None)


def _normalize_iso(field_type: FieldType, value: str) -> str | None:
    try:
        if field_type is FieldType.DATE:
            return date.fromisoformat(value).isoformat()
        if field_type is FieldType.TIME:
            return time.fromisoformat(value).isoformat()
        if field_type is FieldType.DATETIME:
            if "T" not in value and " " not in value:
                return None
            return datetime.fromisoformat(value).isoformat()
    except ValueError:
        return None
    return value


def _normalize_value(field: AppField, value: object) -> tuple[RecordValue | object, RecordValidationIssue | None]:
    if value is None:
        return None, None

    field_type = field.field_type
    text_types = {
        FieldType.STRING,
        FieldType.MULTILINE_STRING,
        FieldType.SIGNATURE,
        FieldType.EMAIL,
        FieldType.PHONE,
        FieldType.IDENTIFIER,
    }
    if field_type in text_types:
        if isinstance(value, str):
            return value, None
        return _MISSING, RecordValidationIssue(
            RecordValidationIssueCode.INVALID_FIELD_TYPE,
            f"{field.field_id} must be a string",
            field.field_id,
        )

    if field_type in {FieldType.DATE, FieldType.TIME, FieldType.DATETIME}:
        if not isinstance(value, str):
            return _MISSING, RecordValidationIssue(
                RecordValidationIssueCode.INVALID_FIELD_TYPE,
                f"{field.field_id} must be an ISO string",
                field.field_id,
            )
        normalized = _normalize_iso(field_type, value)
        if normalized is None:
            return _MISSING, RecordValidationIssue(
                RecordValidationIssueCode.INVALID_FIELD_TYPE,
                f"{field.field_id} is not a valid {field_type.value}",
                field.field_id,
            )
        return normalized, None

    if field_type is FieldType.INTEGER:
        if isinstance(value, int) and not isinstance(value, bool):
            return value, None
        return _MISSING, RecordValidationIssue(
            RecordValidationIssueCode.INVALID_FIELD_TYPE,
            f"{field.field_id} must be an integer",
            field.field_id,
        )

    if field_type is FieldType.DECIMAL:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if isinstance(value, float) and not math.isfinite(value):
                return _MISSING, RecordValidationIssue(
                    RecordValidationIssueCode.INVALID_FIELD_TYPE,
                    f"{field.field_id} must be a finite decimal",
                    field.field_id,
                )
            return value, None
        return _MISSING, RecordValidationIssue(
            RecordValidationIssueCode.INVALID_FIELD_TYPE,
            f"{field.field_id} must be numeric",
            field.field_id,
        )

    if field_type is FieldType.BOOLEAN:
        if isinstance(value, bool):
            return value, None
        return _MISSING, RecordValidationIssue(
            RecordValidationIssueCode.INVALID_FIELD_TYPE,
            f"{field.field_id} must be a boolean",
            field.field_id,
        )

    if field_type is FieldType.ENUM:
        if not isinstance(value, str):
            return _MISSING, RecordValidationIssue(
                RecordValidationIssueCode.INVALID_FIELD_TYPE,
                f"{field.field_id} must be a string choice",
                field.field_id,
            )
        if value not in field.options:
            return _MISSING, RecordValidationIssue(
                RecordValidationIssueCode.INVALID_CHOICE,
                f"{field.field_id} contains an unsupported choice",
                field.field_id,
            )
        return value, None

    if field_type is FieldType.MULTI_ENUM:
        if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
            return _MISSING, RecordValidationIssue(
                RecordValidationIssueCode.INVALID_FIELD_TYPE,
                f"{field.field_id} must be a list or tuple of string choices",
                field.field_id,
            )
        choices = tuple(value)
        if len(set(choices)) != len(choices):
            return _MISSING, RecordValidationIssue(
                RecordValidationIssueCode.DUPLICATE_CHOICE,
                f"{field.field_id} must not repeat choices",
                field.field_id,
            )
        if any(item not in field.options for item in choices):
            return _MISSING, RecordValidationIssue(
                RecordValidationIssueCode.INVALID_CHOICE,
                f"{field.field_id} contains an unsupported choice",
                field.field_id,
            )
        return choices, None

    return _MISSING, RecordValidationIssue(
        RecordValidationIssueCode.INVALID_FIELD_TYPE,
        f"{field.field_id} uses an unsupported runtime field type",
        field.field_id,
    )


def _required_satisfied(value: object) -> bool:
    if value is _MISSING or value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, tuple):
        return bool(value)
    return True


def _format_valid(expected: object, value: object) -> bool:
    if value is None:
        return True
    if not isinstance(expected, str) or not isinstance(value, str):
        return False
    if expected == "email":
        return bool(_EMAIL_RE.fullmatch(value))
    if expected == "phone":
        digits = sum(character.isdigit() for character in value)
        return bool(_PHONE_ALLOWED_RE.fullmatch(value)) and digits >= 7
    if expected == "identifier":
        return bool(_IDENTIFIER_RE.fullmatch(value))
    return False


def _rule_satisfied(validation: AppValidation, value: object) -> bool:
    kind = validation.kind
    expected = validation.value

    if kind is ValidationRuleKind.REQUIRED:
        return _required_satisfied(value)
    if value is _MISSING or value is None:
        return True
    if kind is ValidationRuleKind.MIN:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= expected
    if kind is ValidationRuleKind.MAX:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value <= expected
    if kind is ValidationRuleKind.MIN_LENGTH:
        return isinstance(value, str) and len(value) >= expected
    if kind is ValidationRuleKind.MAX_LENGTH:
        return isinstance(value, str) and len(value) <= expected
    if kind is ValidationRuleKind.ALLOWED_VALUES:
        if not isinstance(expected, tuple):
            return False
        if isinstance(value, tuple):
            return all(item in expected for item in value)
        return value in expected
    if kind is ValidationRuleKind.FORMAT:
        return _format_valid(expected, value)
    return False


def validate_record_payload(
    registered: RegisteredAppSpec,
    entity_id: str,
    payload: Mapping[str, object],
) -> RecordValidationReport:
    if not isinstance(registered, RegisteredAppSpec):
        raise TypeError("registered must be a RegisteredAppSpec")
    if not isinstance(entity_id, str) or not entity_id.strip():
        raise ValueError("entity_id must be a non-empty string")
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")
    if not all(isinstance(key, str) for key in payload):
        raise TypeError("payload keys must be strings")

    entity = _entity_for(registered, entity_id)
    if entity is None:
        issue = RecordValidationIssue(
            RecordValidationIssueCode.ENTITY_NOT_FOUND,
            f"entity not found: {entity_id}",
        )
        return RecordValidationReport(False, (issue,), None)

    issues: list[RecordValidationIssue] = []
    field_by_id = {field.field_id: field for field in entity.fields}
    for field_id in sorted(set(payload) - set(field_by_id)):
        issues.append(
            RecordValidationIssue(
                RecordValidationIssueCode.UNKNOWN_FIELD,
                f"undeclared field: {field_id}",
                field_id,
            )
        )

    normalized_by_id: dict[str, RecordValue] = {}
    for field in entity.fields:
        raw_value = payload.get(field.field_id, _MISSING)
        if raw_value is _MISSING and field.default_value is not None:
            raw_value = field.default_value
        if raw_value is _MISSING:
            continue
        normalized, issue = _normalize_value(field, raw_value)
        if issue is not None:
            issues.append(issue)
            continue
        normalized_by_id[field.field_id] = normalized  # type: ignore[assignment]

    validations = tuple(
        validation
        for validation in registered.app_spec.validations
        if validation.entity_id == entity_id
    )
    for validation in validations:
        value = normalized_by_id.get(validation.field_id, _MISSING)
        if not _rule_satisfied(validation, value):
            code = (
                RecordValidationIssueCode.REQUIRED_FIELD_MISSING
                if validation.kind is ValidationRuleKind.REQUIRED
                else RecordValidationIssueCode.VALIDATION_RULE_FAILED
            )
            issues.append(
                RecordValidationIssue(
                    code,
                    f"validation failed: {validation.kind.value}",
                    validation.field_id,
                    validation.validation_id,
                )
            )

    if issues:
        return RecordValidationReport(False, tuple(issues), None)

    ordered_values = tuple(
        (field.field_id, normalized_by_id[field.field_id])
        for field in entity.fields
        if field.field_id in normalized_by_id
    )
    normalized = ValidatedRecordPayload(
        registration_id=registered.registration_id,
        app_id=registered.app_id,
        entity_id=entity_id,
        values=ordered_values,
    )
    return RecordValidationReport(True, (), normalized)


def require_valid_record_payload(
    registered: RegisteredAppSpec,
    entity_id: str,
    payload: Mapping[str, object],
) -> ValidatedRecordPayload:
    report = validate_record_payload(registered, entity_id, payload)
    if not report.valid or report.normalized is None:
        raise RecordValidationError(report)
    return report.normalized
