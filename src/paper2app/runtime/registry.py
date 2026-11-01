"""Validated in-memory AppSpec registry for Paper2App F04-W01."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from paper2app.specification.app_spec import AppSpec
from paper2app.specification.validation import (
    AppSpecValidationIssueCode,
    AppSpecValidationSeverity,
    AppSpecValidationStatus,
    validate_app_spec,
)

from .manifest import COMPETITION_V1_RUNTIME_MANIFEST, RuntimeManifest


class RuntimeFailureCode(str, Enum):
    APP_SPEC_INVALID = "APP_SPEC_INVALID"
    APP_SPEC_INCOMPATIBLE = "APP_SPEC_INCOMPATIBLE"
    SPEC_NOT_FOUND = "SPEC_NOT_FOUND"


class RuntimeRegistryError(ValueError):
    def __init__(self, code: RuntimeFailureCode, message: str, *, details: tuple[str, ...] = ()) -> None:
        self.code = code
        self.details = details
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class RegisteredAppSpec:
    registration_id: str
    app_id: str
    fingerprint: str
    app_spec_schema_version: str
    runtime_manifest_id: str
    runtime_manifest_version: str
    validation_status: AppSpecValidationStatus
    app_spec: AppSpec


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _canonical_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_canonical_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _canonical_value(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported canonical AppSpec value: {type(value).__name__}")


def app_spec_fingerprint(app_spec: AppSpec) -> str:
    if not isinstance(app_spec, AppSpec):
        raise TypeError("app_spec must be an AppSpec")
    canonical = json.dumps(
        _canonical_value(app_spec),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class AppSpecRegistry:
    """In-memory immutable-registration registry.

    Persistence belongs to F04-W03. W01 establishes registration identity,
    compatibility gating, history retention, and explicit activation semantics.
    """

    def __init__(self, manifest: RuntimeManifest = COMPETITION_V1_RUNTIME_MANIFEST) -> None:
        if not isinstance(manifest, RuntimeManifest):
            raise TypeError("manifest must be a RuntimeManifest")
        self._manifest = manifest
        self._registrations: dict[str, RegisteredAppSpec] = {}
        self._history_by_app: dict[str, list[str]] = {}
        self._active_by_app: dict[str, str] = {}

    @property
    def manifest(self) -> RuntimeManifest:
        return self._manifest

    def register(self, app_spec: AppSpec, *, activate: bool = False) -> RegisteredAppSpec:
        if not isinstance(app_spec, AppSpec):
            raise TypeError("app_spec must be an AppSpec")

        report = validate_app_spec(app_spec, self._manifest.capability_profile())
        if not report.valid:
            error_issues = tuple(
                issue for issue in report.issues if issue.severity is AppSpecValidationSeverity.ERROR
            )
            intrinsic_errors = tuple(
                issue
                for issue in error_issues
                if issue.code is not AppSpecValidationIssueCode.RUNTIME_CAPABILITY_UNSUPPORTED
            )
            if intrinsic_errors:
                raise RuntimeRegistryError(
                    RuntimeFailureCode.APP_SPEC_INVALID,
                    "AppSpec failed deterministic validation and cannot be registered",
                    details=tuple(issue.code.value for issue in intrinsic_errors),
                )
            raise RuntimeRegistryError(
                RuntimeFailureCode.APP_SPEC_INCOMPATIBLE,
                "AppSpec requires capabilities unsupported by the runtime manifest",
                details=tuple(issue.code.value for issue in error_issues),
            )

        compatibility_issues = self._manifest.compatibility_issues(app_spec)
        if compatibility_issues:
            raise RuntimeRegistryError(
                RuntimeFailureCode.APP_SPEC_INCOMPATIBLE,
                "AppSpec uses a surface unsupported by the runtime manifest",
                details=tuple(
                    f"{issue.surface.value}:{issue.value}"
                    for issue in compatibility_issues
                ),
            )

        fingerprint = app_spec_fingerprint(app_spec)
        registration_id = f"{app_spec.app.app_id}:{fingerprint}"
        existing = self._registrations.get(registration_id)
        if existing is not None:
            if activate:
                self._active_by_app[app_spec.app.app_id] = registration_id
            return existing

        registered = RegisteredAppSpec(
            registration_id=registration_id,
            app_id=app_spec.app.app_id,
            fingerprint=fingerprint,
            app_spec_schema_version=app_spec.schema_version,
            runtime_manifest_id=self._manifest.manifest_id,
            runtime_manifest_version=self._manifest.manifest_version,
            validation_status=report.status,
            app_spec=app_spec,
        )
        self._registrations[registration_id] = registered
        history = self._history_by_app.setdefault(app_spec.app.app_id, [])
        history.append(registration_id)

        if app_spec.app.app_id not in self._active_by_app or activate:
            self._active_by_app[app_spec.app.app_id] = registration_id

        return registered

    def activate(self, app_id: str, registration_id: str) -> RegisteredAppSpec:
        registered = self._registrations.get(registration_id)
        if registered is None or registered.app_id != app_id:
            raise RuntimeRegistryError(RuntimeFailureCode.SPEC_NOT_FOUND, "registered AppSpec was not found")
        self._active_by_app[app_id] = registration_id
        return registered

    def get_registration(self, registration_id: str) -> RegisteredAppSpec:
        registered = self._registrations.get(registration_id)
        if registered is None:
            raise RuntimeRegistryError(RuntimeFailureCode.SPEC_NOT_FOUND, "registered AppSpec was not found")
        return registered

    def get_active(self, app_id: str) -> RegisteredAppSpec:
        registration_id = self._active_by_app.get(app_id)
        if registration_id is None:
            raise RuntimeRegistryError(RuntimeFailureCode.SPEC_NOT_FOUND, "active AppSpec was not found")
        return self._registrations[registration_id]

    def list_registrations(self, app_id: str) -> tuple[RegisteredAppSpec, ...]:
        return tuple(
            self._registrations[registration_id]
            for registration_id in self._history_by_app.get(app_id, ())
        )
