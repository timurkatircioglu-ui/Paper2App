from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.runtime.manifest import (
    COMPETITION_V1_RUNTIME_MANIFEST,
    RuntimeManifest,
    RuntimeSurface,
)
from paper2app.runtime.registry import (
    AppSpecRegistry,
    RuntimeFailureCode,
    RuntimeRegistryError,
    app_spec_fingerprint,
)
from paper2app.specification import (
    COMPETITION_V1_RUNTIME_PROFILE,
    ActionKind,
    Capability,
    ConditionOperator,
    FieldType,
    ValidationRuleKind,
    ViewKind,
    assemble_app_spec_candidate,
    synthesize_validated_app_spec,
)
from tests.golden.app_spec_generalization_cases import (
    equipment_checkout_appspec_ready_document_ir,
    safety_inspection_appspec_ready_document_ir,
)
from tests.golden.document_ir_samples import safety_inspection_golden


class RuntimeManifestRegistryTests(unittest.TestCase):
    def _equipment_spec(self):
        return synthesize_validated_app_spec(equipment_checkout_appspec_ready_document_ir())

    def _safety_spec(self):
        return synthesize_validated_app_spec(safety_inspection_appspec_ready_document_ir())

    def test_competition_manifest_covers_bounded_appspec_vocabulary(self) -> None:
        manifest = COMPETITION_V1_RUNTIME_MANIFEST
        self.assertEqual(manifest.supported_field_types, tuple(FieldType))
        self.assertEqual(manifest.supported_view_kinds, tuple(ViewKind))
        self.assertEqual(manifest.supported_action_kinds, tuple(ActionKind))
        self.assertEqual(manifest.supported_validation_rules, tuple(ValidationRuleKind))
        self.assertEqual(manifest.supported_condition_operators, tuple(ConditionOperator))
        self.assertEqual(manifest.supported_capabilities, tuple(Capability))
        self.assertTrue(manifest.workflows_enabled)
        self.assertEqual(manifest.max_workflows_per_entity, 1)

    def test_f03_default_runtime_profile_is_derived_from_manifest(self) -> None:
        manifest = COMPETITION_V1_RUNTIME_MANIFEST
        self.assertEqual(COMPETITION_V1_RUNTIME_PROFILE.profile_id, manifest.manifest_id)
        self.assertEqual(COMPETITION_V1_RUNTIME_PROFILE.supported_capabilities, manifest.supported_capabilities)

    def test_manifest_rejects_inconsistent_workflow_policy(self) -> None:
        with self.assertRaises(ValueError):
            replace(COMPETITION_V1_RUNTIME_MANIFEST, workflows_enabled=False, max_workflows_per_entity=1)
        with self.assertRaises(ValueError):
            replace(COMPETITION_V1_RUNTIME_MANIFEST, workflows_enabled=True, max_workflows_per_entity=0)

    def test_supported_validated_appspec_registers_and_becomes_active(self) -> None:
        registry = AppSpecRegistry()
        spec = self._equipment_spec()
        registered = registry.register(spec)
        self.assertEqual(registered.app_id, spec.app.app_id)
        self.assertEqual(registered.runtime_manifest_id, COMPETITION_V1_RUNTIME_MANIFEST.manifest_id)
        self.assertEqual(registry.get_active(spec.app.app_id), registered)

    def test_identical_appspec_has_identical_fingerprint_and_idempotent_registration(self) -> None:
        registry = AppSpecRegistry()
        spec = self._equipment_spec()
        first = registry.register(spec)
        second = registry.register(spec)
        self.assertEqual(app_spec_fingerprint(spec), first.fingerprint)
        self.assertEqual(first.registration_id, second.registration_id)
        self.assertIs(first, second)
        self.assertEqual(len(registry.list_registrations(spec.app.app_id)), 1)

    def test_changed_appspec_gets_new_identity_without_silent_active_switch(self) -> None:
        registry = AppSpecRegistry()
        original = self._equipment_spec()
        first = registry.register(original)
        changed = replace(
            original,
            app=replace(original.app, display_name=f"{original.app.display_name} Revised"),
        )
        second = registry.register(changed)
        self.assertNotEqual(first.fingerprint, second.fingerprint)
        self.assertNotEqual(first.registration_id, second.registration_id)
        self.assertEqual(len(registry.list_registrations(original.app.app_id)), 2)
        self.assertEqual(registry.get_active(original.app.app_id), first)
        registry.activate(original.app.app_id, second.registration_id)
        self.assertEqual(registry.get_active(original.app.app_id), second)

    def test_register_activate_true_explicitly_switches_active_registration(self) -> None:
        registry = AppSpecRegistry()
        original = self._equipment_spec()
        first = registry.register(original)
        changed = replace(original, app=replace(original.app, description="Revised validated paper workflow."))
        second = registry.register(changed, activate=True)
        self.assertNotEqual(first.registration_id, second.registration_id)
        self.assertEqual(registry.get_active(original.app.app_id), second)
        self.assertEqual(len(registry.list_registrations(original.app.app_id)), 2)

    def test_critical_uncertainty_candidate_cannot_register(self) -> None:
        unresolved = assemble_app_spec_candidate(safety_inspection_golden().document_ir)
        registry = AppSpecRegistry()
        with self.assertRaises(RuntimeRegistryError) as caught:
            registry.register(unresolved)
        self.assertEqual(caught.exception.code, RuntimeFailureCode.APP_SPEC_INVALID)
        self.assertIn("CRITICAL_UNCERTAINTY", caught.exception.details)

    def test_manifest_unsupported_field_surface_cannot_register(self) -> None:
        restricted = replace(
            COMPETITION_V1_RUNTIME_MANIFEST,
            manifest_id="no_signature_fields",
            supported_field_types=tuple(field_type for field_type in FieldType if field_type is not FieldType.SIGNATURE),
        )
        registry = AppSpecRegistry(restricted)
        with self.assertRaises(RuntimeRegistryError) as caught:
            registry.register(self._equipment_spec())
        self.assertEqual(caught.exception.code, RuntimeFailureCode.APP_SPEC_INCOMPATIBLE)
        self.assertIn(f"{RuntimeSurface.FIELD_TYPE.value}:{FieldType.SIGNATURE.value}", caught.exception.details)

    def test_manifest_unsupported_capability_cannot_register(self) -> None:
        restricted = replace(
            COMPETITION_V1_RUNTIME_MANIFEST,
            manifest_id="no_signature_capture",
            supported_capabilities=tuple(
                capability for capability in Capability if capability is not Capability.SIGNATURE_CAPTURE
            ),
        )
        registry = AppSpecRegistry(restricted)
        with self.assertRaises(RuntimeRegistryError) as caught:
            registry.register(self._equipment_spec())
        self.assertEqual(caught.exception.code, RuntimeFailureCode.APP_SPEC_INCOMPATIBLE)
        self.assertIn("RUNTIME_CAPABILITY_UNSUPPORTED", caught.exception.details)

    def test_disabled_workflow_manifest_rejects_workflow_appspec(self) -> None:
        restricted = replace(
            COMPETITION_V1_RUNTIME_MANIFEST,
            manifest_id="workflow_disabled",
            workflows_enabled=False,
            max_workflows_per_entity=0,
        )
        registry = AppSpecRegistry(restricted)
        with self.assertRaises(RuntimeRegistryError) as caught:
            registry.register(self._safety_spec())
        self.assertEqual(caught.exception.code, RuntimeFailureCode.APP_SPEC_INCOMPATIBLE)
        self.assertTrue(any(detail.startswith(f"{RuntimeSurface.WORKFLOW.value}:") for detail in caught.exception.details))

    def test_missing_registration_and_active_spec_fail_with_spec_not_found(self) -> None:
        registry = AppSpecRegistry()
        with self.assertRaises(RuntimeRegistryError) as missing_registration:
            registry.get_registration("missing")
        self.assertEqual(missing_registration.exception.code, RuntimeFailureCode.SPEC_NOT_FOUND)
        with self.assertRaises(RuntimeRegistryError) as missing_active:
            registry.get_active("missing_app")
        self.assertEqual(missing_active.exception.code, RuntimeFailureCode.SPEC_NOT_FOUND)

    def test_activation_rejects_registration_from_another_app(self) -> None:
        registry = AppSpecRegistry()
        equipment = registry.register(self._equipment_spec())
        safety = registry.register(self._safety_spec())
        with self.assertRaises(RuntimeRegistryError) as caught:
            registry.activate(equipment.app_id, safety.registration_id)
        self.assertEqual(caught.exception.code, RuntimeFailureCode.SPEC_NOT_FOUND)

    def test_registry_is_runtime_contract_only_without_persistence_or_http_side_effects(self) -> None:
        registry = AppSpecRegistry()
        self.assertEqual(registry.list_registrations("unknown"), ())
        self.assertFalse(hasattr(registry, "save"))
        self.assertFalse(hasattr(registry, "connect"))
        self.assertFalse(hasattr(registry, "route"))


if __name__ == "__main__":
    unittest.main()
