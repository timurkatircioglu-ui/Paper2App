from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.specification import (
    APP_SPEC_SCHEMA,
    APP_SPEC_SCHEMA_VERSION,
    ActionKind,
    AppAction,
    AppEntity,
    AppField,
    AppIdentity,
    AppSpec,
    AppSpecUncertainty,
    AppValidation,
    AppView,
    AppWorkflow,
    Capability,
    ConditionOperator,
    FieldType,
    PersistenceRequirement,
    ProvenanceClass,
    ProvenanceRecord,
    ValidationRuleKind,
    ViewKind,
    WorkflowCondition,
    WorkflowState,
    WorkflowTransition,
)


def _minimal_spec() -> AppSpec:
    entity = AppEntity(
        entity_id="record",
        display_name="Record",
        fields=(AppField("name", "Name", FieldType.STRING),),
    )
    return AppSpec(
        app=AppIdentity("demo", "Demo", "Demo application", "record"),
        entities=(entity,),
        views=(AppView("form", ViewKind.FORM, "record", ("name",)),),
        actions=(AppAction("create", ActionKind.CREATE_RECORD, "record"),),
        workflows=(),
        validations=(AppValidation("required_name", "record", "name", ValidationRuleKind.REQUIRED),),
        capabilities=(Capability.RECORD_CREATE, Capability.PERSISTENCE),
        persistence=PersistenceRequirement(),
        provenance=(
            ProvenanceRecord(
                "prov_name",
                "name",
                ProvenanceClass.DOCUMENT_DERIVED,
                source_refs=("field:name",),
            ),
        ),
        uncertainties=(),
    )


class AppSpecContractTests(unittest.TestCase):
    def test_schema_identity_is_frozen(self) -> None:
        spec = _minimal_spec()
        self.assertEqual(APP_SPEC_SCHEMA, "paper2app.app_spec")
        self.assertEqual(APP_SPEC_SCHEMA_VERSION, "0.1")
        self.assertEqual(spec.schema, APP_SPEC_SCHEMA)
        self.assertEqual(spec.schema_version, APP_SPEC_SCHEMA_VERSION)

    def test_field_type_vocabulary_is_exact(self) -> None:
        self.assertEqual(
            {item.value for item in FieldType},
            {
                "string", "multiline_string", "integer", "decimal", "boolean", "date", "time",
                "datetime", "enum", "multi_enum", "signature", "email", "phone", "identifier",
            },
        )

    def test_action_vocabulary_is_exact(self) -> None:
        self.assertEqual(
            {item.value for item in ActionKind},
            {
                "create_record", "update_record", "view_record", "list_records",
                "search_records", "filter_records", "change_state",
            },
        )

    def test_view_vocabulary_is_exact(self) -> None:
        self.assertEqual({item.value for item in ViewKind}, {"form", "record_list", "record_detail"})

    def test_provenance_classes_are_exact(self) -> None:
        self.assertEqual(
            {item.value for item in ProvenanceClass},
            {"DOCUMENT_DERIVED", "PRODUCT_POLICY", "USER_CONFIRMED"},
        )

    def test_enum_requires_unique_options(self) -> None:
        with self.assertRaises(ValueError):
            AppField("severity", "Severity", FieldType.ENUM)
        with self.assertRaises(ValueError):
            AppField("severity", "Severity", FieldType.ENUM, options=("Low", "Low"))
        field = AppField("severity", "Severity", FieldType.ENUM, options=("Low", "Medium", "High"))
        self.assertEqual(field.options, ("Low", "Medium", "High"))

    def test_non_enum_rejects_options(self) -> None:
        with self.assertRaises(ValueError):
            AppField("name", "Name", FieldType.STRING, options=("A", "B"))

    def test_arbitrary_default_payload_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            AppField("name", "Name", FieldType.STRING, default_value={"script": "run"})  # type: ignore[arg-type]

    def test_validation_payload_is_bounded(self) -> None:
        rule = AppValidation("allowed", "record", "severity", ValidationRuleKind.ALLOWED_VALUES, ("Low", "High"))
        self.assertEqual(rule.value, ("Low", "High"))
        with self.assertRaises(TypeError):
            AppValidation("bad", "record", "name", ValidationRuleKind.FORMAT, ["python"])  # type: ignore[arg-type]

    def test_workflow_contract_is_bounded_state_machine(self) -> None:
        workflow = AppWorkflow(
            workflow_id="return_flow",
            entity_id="record",
            states=(WorkflowState("out", "Checked out"), WorkflowState("returned", "Returned")),
            initial_state_id="out",
            conditions=(WorkflowCondition("is_returned", "returned", ConditionOperator.EQUALS, True),),
            transitions=(WorkflowTransition("mark_returned", "out", "returned", ("is_returned",)),),
        )
        self.assertEqual(workflow.initial_state_id, "out")
        self.assertEqual(workflow.transitions[0].to_state_id, "returned")

    def test_workflow_self_transition_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            WorkflowTransition("noop", "open", "open")

    def test_capability_vocabulary_is_bounded(self) -> None:
        self.assertEqual(
            {item.value for item in Capability},
            {
                "record_create", "record_update", "record_view", "record_list", "record_search",
                "record_filter", "persistence", "multi_choice", "basic_workflow", "signature_capture",
            },
        )

    def test_persistence_contract_is_technology_independent(self) -> None:
        persistence = PersistenceRequirement(required=True, survive_reload=True)
        self.assertTrue(persistence.required)
        self.assertTrue(persistence.survive_reload)
        self.assertFalse(any(name in {"sqlite", "postgres", "table", "sql"} for name in {f.name for f in fields(persistence)}))

    def test_uncertainty_can_be_critical_without_executable_payload(self) -> None:
        uncertainty = AppSpecUncertainty(
            "uncertain_state",
            "Returned-state semantics require confirmation.",
            critical=True,
            target_ids=("return_flow",),
            source_refs=("field:returned",),
        )
        self.assertTrue(uncertainty.critical)

    def test_appspec_collections_are_tuples(self) -> None:
        spec = _minimal_spec()
        self.assertIsInstance(spec.entities, tuple)
        with self.assertRaises(TypeError):
            AppSpec(
                app=spec.app,
                entities=list(spec.entities),  # type: ignore[arg-type]
                views=spec.views,
                actions=spec.actions,
                workflows=spec.workflows,
                validations=spec.validations,
                capabilities=spec.capabilities,
                persistence=spec.persistence,
                provenance=spec.provenance,
                uncertainties=spec.uncertainties,
            )

    def test_contract_objects_are_immutable(self) -> None:
        spec = _minimal_spec()
        with self.assertRaises(FrozenInstanceError):
            spec.app.display_name = "Changed"  # type: ignore[misc]

    def test_contract_surface_contains_no_implementation_fields(self) -> None:
        forbidden = {"sql", "sqlite", "postgres", "react", "fastapi", "css", "html", "shell", "script", "code", "path", "credential", "secret"}
        contract_types = (
            AppIdentity, AppField, AppEntity, AppView, AppAction, AppValidation,
            WorkflowCondition, WorkflowState, WorkflowTransition, AppWorkflow,
            PersistenceRequirement, ProvenanceRecord, AppSpecUncertainty, AppSpec,
        )
        names = {field.name.casefold() for contract_type in contract_types for field in fields(contract_type)}
        self.assertFalse(names & forbidden)

    def test_cross_reference_resolution_is_deliberately_deferred_to_validator(self) -> None:
        spec = _minimal_spec()
        unresolved = AppView("detail", ViewKind.RECORD_DETAIL, "missing_entity", ("missing_field",))
        candidate = AppSpec(
            app=spec.app,
            entities=spec.entities,
            views=(unresolved,),
            actions=spec.actions,
            workflows=spec.workflows,
            validations=spec.validations,
            capabilities=spec.capabilities,
            persistence=spec.persistence,
            provenance=spec.provenance,
            uncertainties=spec.uncertainties,
        )
        self.assertEqual(candidate.views[0].entity_id, "missing_entity")


if __name__ == "__main__":
    unittest.main()
