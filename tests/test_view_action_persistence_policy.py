from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.specification import (
    ActionKind,
    AppEntity,
    AppField,
    Capability,
    EntityFieldSynthesisResult,
    FieldType,
    ProvenanceClass,
    ViewKind,
    synthesize_entity_fields,
    synthesize_views_actions_persistence,
)
from tests.golden.document_ir_samples import equipment_checkout_golden, safety_inspection_golden


class ViewActionPersistencePolicyTests(unittest.TestCase):
    def _equipment(self):
        return synthesize_views_actions_persistence(
            synthesize_entity_fields(equipment_checkout_golden().document_ir)
        )

    def test_equipment_generates_form_list_detail_views(self) -> None:
        result = self._equipment()
        self.assertEqual(
            tuple(view.kind for view in result.views),
            (ViewKind.FORM, ViewKind.RECORD_LIST, ViewKind.RECORD_DETAIL),
        )
        field_ids = tuple(field.field_id for field in result.entities[0].fields)
        self.assertTrue(all(view.field_ids == field_ids for view in result.views))

    def test_equipment_actions_are_explicit_bounded_record_operations(self) -> None:
        result = self._equipment()
        self.assertEqual(
            tuple(action.kind for action in result.actions),
            (
                ActionKind.CREATE_RECORD,
                ActionKind.UPDATE_RECORD,
                ActionKind.VIEW_RECORD,
                ActionKind.LIST_RECORDS,
                ActionKind.SEARCH_RECORDS,
                ActionKind.FILTER_RECORDS,
            ),
        )
        self.assertNotIn(ActionKind.CHANGE_STATE, tuple(action.kind for action in result.actions))

    def test_required_capabilities_follow_actions_and_field_needs(self) -> None:
        result = self._equipment()
        self.assertEqual(
            result.capabilities,
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
        self.assertNotIn(Capability.BASIC_WORKFLOW, result.capabilities)

    def test_persistence_policy_requires_reload_survival(self) -> None:
        persistence = self._equipment().persistence
        self.assertTrue(persistence.required)
        self.assertTrue(persistence.survive_reload)

    def test_surface_policy_provenance_is_product_policy_and_field_provenance_is_preserved(self) -> None:
        result = self._equipment()
        document_records = [
            record for record in result.provenance if record.provenance_class is ProvenanceClass.DOCUMENT_DERIVED
        ]
        policy_records = [
            record for record in result.provenance if record.provenance_class is ProvenanceClass.PRODUCT_POLICY
        ]
        self.assertGreaterEqual(len(document_records), 1)
        self.assertGreaterEqual(len(policy_records), 1)
        self.assertTrue(any(record.target_id == "persistence" for record in policy_records))
        self.assertTrue(any(record.target_id.startswith("view:") for record in policy_records))
        self.assertTrue(any(record.target_id.startswith("action:") for record in policy_records))

    def test_safety_preserves_upstream_critical_uncertainty_without_blocking_safe_surface_proposal(self) -> None:
        upstream = synthesize_entity_fields(safety_inspection_golden().document_ir)
        result = synthesize_views_actions_persistence(upstream)
        self.assertTrue(any(item.critical for item in upstream.uncertainties))
        self.assertEqual(result.uncertainties, upstream.uncertainties)
        self.assertEqual(len(result.views), 3)
        self.assertEqual(len(result.actions), 6)

    def test_multi_enum_field_adds_multi_choice_capability(self) -> None:
        entity_fields = EntityFieldSynthesisResult(
            entities=(
                AppEntity(
                    entity_id="survey_record",
                    display_name="Survey Record",
                    fields=(
                        AppField(
                            field_id="categories",
                            display_name="Categories",
                            field_type=FieldType.MULTI_ENUM,
                            options=("A", "B"),
                        ),
                    ),
                ),
            ),
            provenance=(),
            uncertainties=(),
            decisions=(),
        )
        result = synthesize_views_actions_persistence(entity_fields)
        self.assertIn(Capability.MULTI_CHOICE, result.capabilities)
        self.assertNotIn(Capability.SIGNATURE_CAPTURE, result.capabilities)

    def test_multiple_entities_receive_same_generic_surface_policy(self) -> None:
        entity_fields = EntityFieldSynthesisResult(
            entities=(
                AppEntity(
                    entity_id="alpha",
                    display_name="Alpha",
                    fields=(AppField("name", "Name", FieldType.STRING),),
                ),
                AppEntity(
                    entity_id="beta",
                    display_name="Beta",
                    fields=(AppField("active", "Active", FieldType.BOOLEAN),),
                ),
            ),
            provenance=(),
            uncertainties=(),
            decisions=(),
        )
        result = synthesize_views_actions_persistence(entity_fields)
        self.assertEqual(len(result.views), 6)
        self.assertEqual(len(result.actions), 12)
        self.assertEqual(len(set(result.capabilities)), len(result.capabilities))

    def test_no_entities_fails_closed_with_critical_surface_uncertainty(self) -> None:
        entity_fields = EntityFieldSynthesisResult(
            entities=(), provenance=(), uncertainties=(), decisions=()
        )
        result = synthesize_views_actions_persistence(entity_fields)
        self.assertEqual(result.views, ())
        self.assertEqual(result.actions, ())
        self.assertEqual(result.capabilities, (Capability.PERSISTENCE,))
        self.assertTrue(any(item.uncertainty_id == "surface:no_entities" and item.critical for item in result.uncertainties))

    def test_wrong_input_type_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            synthesize_views_actions_persistence(object())  # type: ignore[arg-type]

    def test_surface_synthesis_is_deterministic(self) -> None:
        upstream = synthesize_entity_fields(equipment_checkout_golden().document_ir)
        self.assertEqual(
            synthesize_views_actions_persistence(upstream),
            synthesize_views_actions_persistence(upstream),
        )

    def test_production_surface_policy_has_no_demo_specific_names(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "paper2app"
            / "specification"
            / "surface_policy.py"
        ).read_text(encoding="utf-8").lower()
        for forbidden in ("equipment_checkout", "equipment checkout", "safety_inspection", "safety inspection"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
