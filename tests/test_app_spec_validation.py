from __future__ import annotations

from dataclasses import replace
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.specification import (
    ActionKind,
    AppAction,
    AppSpecUncertainty,
    AppSpecValidationError,
    AppSpecValidationIssueCode,
    AppSpecValidationStatus,
    AppValidation,
    AppWorkflow,
    Capability,
    ProvenanceClass,
    ProvenanceRecord,
    RuntimeCapabilityProfile,
    ValidationRuleKind,
    WorkflowState,
    WorkflowTransition,
    assemble_app_spec_candidate,
    require_valid_app_spec,
    synthesize_validated_app_spec,
    validate_app_spec,
)
from tests.golden.document_ir_samples import equipment_checkout_golden, safety_inspection_golden


class AppSpecValidationTests(unittest.TestCase):
    def _equipment_spec(self):
        return assemble_app_spec_candidate(equipment_checkout_golden().document_ir)

    def test_equipment_candidate_is_clean_pass(self) -> None:
        report = validate_app_spec(self._equipment_spec())
        self.assertIs(report.status, AppSpecValidationStatus.PASS)
        self.assertEqual(report.issues, ())

    def test_authoritative_egress_returns_valid_equipment_spec(self) -> None:
        spec = synthesize_validated_app_spec(equipment_checkout_golden().document_ir)
        self.assertEqual(spec.app.primary_entity_id, "equipment_checkout_record")
        self.assertIs(validate_app_spec(spec).status, AppSpecValidationStatus.PASS)

    def test_safety_candidate_fails_closed_on_unresolved_critical_field(self) -> None:
        candidate = assemble_app_spec_candidate(safety_inspection_golden().document_ir)
        report = validate_app_spec(candidate)
        self.assertIs(report.status, AppSpecValidationStatus.FAIL)
        self.assertIn(AppSpecValidationIssueCode.CRITICAL_UNCERTAINTY, {issue.code for issue in report.issues})
        with self.assertRaises(AppSpecValidationError):
            synthesize_validated_app_spec(safety_inspection_golden().document_ir)

    def test_schema_mismatch_is_reported(self) -> None:
        spec = self._equipment_spec()
        object.__setattr__(spec, "schema", "paper2app.bad")
        report = validate_app_spec(spec)
        self.assertIn(AppSpecValidationIssueCode.SCHEMA_MISMATCH, {issue.code for issue in report.issues})

    def test_version_mismatch_is_reported(self) -> None:
        spec = self._equipment_spec()
        object.__setattr__(spec, "schema_version", "9.9")
        report = validate_app_spec(spec)
        self.assertIn(AppSpecValidationIssueCode.VERSION_MISMATCH, {issue.code for issue in report.issues})

    def test_duplicate_view_id_fails(self) -> None:
        spec = self._equipment_spec()
        duplicate = replace(spec.views[1], view_id=spec.views[0].view_id)
        report = validate_app_spec(replace(spec, views=(spec.views[0], duplicate)))
        self.assertIn(AppSpecValidationIssueCode.DUPLICATE_ID, {issue.code for issue in report.issues})

    def test_primary_entity_must_resolve(self) -> None:
        spec = self._equipment_spec()
        report = validate_app_spec(replace(spec, app=replace(spec.app, primary_entity_id="missing")))
        self.assertIn(AppSpecValidationIssueCode.PRIMARY_ENTITY_MISSING, {issue.code for issue in report.issues})

    def test_view_entity_must_resolve(self) -> None:
        spec = self._equipment_spec()
        bad_view = replace(spec.views[0], entity_id="missing")
        report = validate_app_spec(replace(spec, views=(bad_view,) + spec.views[1:]))
        self.assertIn(AppSpecValidationIssueCode.REFERENCE_MISSING, {issue.code for issue in report.issues})

    def test_view_field_must_resolve(self) -> None:
        spec = self._equipment_spec()
        bad_view = replace(spec.views[0], field_ids=spec.views[0].field_ids + ("missing",))
        report = validate_app_spec(replace(spec, views=(bad_view,) + spec.views[1:]))
        self.assertIn(AppSpecValidationIssueCode.REFERENCE_MISSING, {issue.code for issue in report.issues})

    def test_default_value_must_match_field_type(self) -> None:
        spec = self._equipment_spec()
        entity = spec.entities[0]
        bad_field = replace(entity.fields[0], default_value=True)
        bad_entity = replace(entity, fields=(bad_field,) + entity.fields[1:])
        report = validate_app_spec(replace(spec, entities=(bad_entity,)))
        self.assertIn(AppSpecValidationIssueCode.DEFAULT_VALUE_INCOMPATIBLE, {issue.code for issue in report.issues})

    def test_validation_rule_must_match_field_type(self) -> None:
        spec = self._equipment_spec()
        invalid = AppValidation(
            validation_id="validation:name:allowed",
            entity_id=spec.entities[0].entity_id,
            field_id="name",
            kind=ValidationRuleKind.ALLOWED_VALUES,
            value=("A", "B"),
        )
        report = validate_app_spec(replace(spec, validations=(invalid,)))
        self.assertIn(AppSpecValidationIssueCode.VALIDATION_RULE_INCOMPATIBLE, {issue.code for issue in report.issues})

    def test_validation_field_scope_is_checked(self) -> None:
        spec = self._equipment_spec()
        first_field = spec.entities[0].fields[0]
        second = replace(
            spec.entities[0],
            entity_id="other_record",
            fields=(replace(first_field, field_id="other_name"),),
        )
        invalid = AppValidation("v", second.entity_id, "name", ValidationRuleKind.REQUIRED)
        report = validate_app_spec(replace(spec, entities=spec.entities + (second,), validations=(invalid,)))
        self.assertIn(AppSpecValidationIssueCode.REFERENCE_SCOPE_MISMATCH, {issue.code for issue in report.issues})

    def test_unreachable_workflow_state_fails(self) -> None:
        spec = self._equipment_spec()
        workflow = AppWorkflow(
            workflow_id="workflow:test",
            entity_id=spec.entities[0].entity_id,
            states=(WorkflowState("open", "Open"), WorkflowState("closed", "Closed"), WorkflowState("orphan", "Orphan")),
            initial_state_id="open",
            transitions=(WorkflowTransition("transition:close", "open", "closed"),),
        )
        capabilities = spec.capabilities + (Capability.BASIC_WORKFLOW,)
        report = validate_app_spec(replace(spec, workflows=(workflow,), capabilities=capabilities))
        self.assertIn(AppSpecValidationIssueCode.WORKFLOW_GRAPH_INVALID, {issue.code for issue in report.issues})

    def test_change_state_action_requires_known_workflow(self) -> None:
        spec = self._equipment_spec()
        action = AppAction("action:change", ActionKind.CHANGE_STATE, spec.entities[0].entity_id, workflow_id="missing")
        capabilities = spec.capabilities + (Capability.BASIC_WORKFLOW,)
        report = validate_app_spec(replace(spec, actions=spec.actions + (action,), capabilities=capabilities))
        self.assertIn(AppSpecValidationIssueCode.REFERENCE_MISSING, {issue.code for issue in report.issues})

    def test_missing_declared_required_capability_fails(self) -> None:
        spec = self._equipment_spec()
        capabilities = tuple(item for item in spec.capabilities if item is not Capability.PERSISTENCE)
        report = validate_app_spec(replace(spec, capabilities=capabilities))
        self.assertIn(AppSpecValidationIssueCode.REQUIRED_CAPABILITY_MISSING, {issue.code for issue in report.issues})

    def test_runtime_profile_rejects_unsupported_required_capability(self) -> None:
        spec = self._equipment_spec()
        profile = RuntimeCapabilityProfile(
            profile_id="no_signature",
            supported_capabilities=tuple(item for item in Capability if item is not Capability.SIGNATURE_CAPTURE),
        )
        report = validate_app_spec(spec, profile)
        self.assertIn(AppSpecValidationIssueCode.RUNTIME_CAPABILITY_UNSUPPORTED, {issue.code for issue in report.issues})

    def test_unused_capability_is_warning_not_failure(self) -> None:
        spec = self._equipment_spec()
        report = validate_app_spec(replace(spec, capabilities=spec.capabilities + (Capability.BASIC_WORKFLOW,)))
        self.assertIs(report.status, AppSpecValidationStatus.PASS_WITH_WARNINGS)
        self.assertIn(AppSpecValidationIssueCode.UNUSED_CAPABILITY, {issue.code for issue in report.issues})

    def test_noncritical_uncertainty_is_warning(self) -> None:
        spec = self._equipment_spec()
        uncertainty = AppSpecUncertainty("u:note", "Review wording.", critical=False)
        candidate = replace(spec, uncertainties=(uncertainty,))
        report = validate_app_spec(candidate)
        self.assertIs(report.status, AppSpecValidationStatus.PASS_WITH_WARNINGS)
        self.assertIn(AppSpecValidationIssueCode.NONCRITICAL_UNCERTAINTY, {issue.code for issue in report.issues})
        self.assertIs(require_valid_app_spec(candidate), candidate)

    def test_critical_uncertainty_blocks_execution(self) -> None:
        spec = self._equipment_spec()
        uncertainty = AppSpecUncertainty("u:block", "Critical review required.", critical=True)
        candidate = replace(spec, uncertainties=(uncertainty,))
        report = validate_app_spec(candidate)
        self.assertIs(report.status, AppSpecValidationStatus.FAIL)
        with self.assertRaises(AppSpecValidationError):
            require_valid_app_spec(candidate)

    def test_provenance_target_must_resolve(self) -> None:
        spec = self._equipment_spec()
        bad = ProvenanceRecord("prov:missing", "missing", ProvenanceClass.PRODUCT_POLICY)
        report = validate_app_spec(replace(spec, provenance=spec.provenance + (bad,)))
        self.assertIn(AppSpecValidationIssueCode.PROVENANCE_TARGET_MISSING, {issue.code for issue in report.issues})

    def test_required_capability_receipt_is_deterministic(self) -> None:
        spec = self._equipment_spec()
        first = validate_app_spec(spec)
        second = validate_app_spec(spec)
        self.assertEqual(first, second)
        self.assertEqual(
            first.required_capabilities,
            (
                Capability.RECORD_CREATE,
                Capability.RECORD_UPDATE,
                Capability.RECORD_VIEW,
                Capability.RECORD_LIST,
                Capability.RECORD_SEARCH,
                Capability.RECORD_FILTER,
                Capability.PERSISTENCE,
                Capability.SIGNATURE_CAPTURE,
            ),
        )

    def test_runtime_profile_contract_rejects_duplicate_capabilities(self) -> None:
        with self.assertRaises(ValueError):
            RuntimeCapabilityProfile("bad", (Capability.PERSISTENCE, Capability.PERSISTENCE))

    def test_validator_requires_typed_inputs(self) -> None:
        with self.assertRaises(TypeError):
            validate_app_spec(object())  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            validate_app_spec(self._equipment_spec(), object())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
