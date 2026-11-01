from __future__ import annotations

from dataclasses import replace
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.specification import FieldType, ProvenanceClass, synthesize_entity_fields
from paper2app.understanding import (
    DocumentDescriptor,
    DocumentElement,
    DocumentRelation,
    RelationKind,
    SemanticValueHint,
    TextEvidence,
    VisualKind,
)
from paper2app.understanding.validation import DocumentIRValidationError
from tests.golden.document_ir_samples import equipment_checkout_golden, safety_inspection_golden


class EntityFieldSynthesisTests(unittest.TestCase):
    def test_equipment_checkout_maps_to_one_primary_entity(self) -> None:
        result = synthesize_entity_fields(equipment_checkout_golden().document_ir)
        self.assertEqual(len(result.entities), 1)
        entity = result.entities[0]
        self.assertEqual(entity.entity_id, "equipment_checkout_record")
        self.assertEqual(entity.display_name, "Equipment Checkout Record")
        self.assertEqual(
            [(field.field_id, field.field_type) for field in entity.fields],
            [
                ("name", FieldType.STRING),
                ("item", FieldType.STRING),
                ("returned", FieldType.BOOLEAN),
                ("signature", FieldType.SIGNATURE),
            ],
        )

    def test_text_evidence_wins_for_display_label(self) -> None:
        result = synthesize_entity_fields(equipment_checkout_golden().document_ir)
        self.assertEqual(result.entities[0].fields[0].display_name, "Name")

    def test_candidate_id_is_used_as_generic_label_fallback(self) -> None:
        result = synthesize_entity_fields(equipment_checkout_golden().document_ir)
        fields = {field.field_id: field for field in result.entities[0].fields}
        self.assertEqual(fields["item"].display_name, "Item")
        self.assertEqual(fields["returned"].display_name, "Returned")

    def test_document_provenance_preserves_candidate_refs_and_confidence(self) -> None:
        result = synthesize_entity_fields(equipment_checkout_golden().document_ir)
        record = next(item for item in result.provenance if item.target_id == "name")
        self.assertIs(record.provenance_class, ProvenanceClass.DOCUMENT_DERIVED)
        self.assertIn("field:name", record.source_refs)
        self.assertIn("name_input", record.source_refs)
        self.assertIn("confidence=0.950", record.note or "")
        decision = next(item for item in result.decisions if item.field_id == "name")
        self.assertEqual(decision.confidence, 0.95)

    def test_choice_without_observed_options_is_not_silently_executable(self) -> None:
        result = synthesize_entity_fields(safety_inspection_golden().document_ir)
        entity = result.entities[0]
        self.assertNotIn("severity", {field.field_id for field in entity.fields})
        decision = next(item for item in result.decisions if item.field_id == "severity")
        self.assertFalse(decision.emitted)
        self.assertIsNone(decision.field_type)
        uncertainty = next(item for item in result.uncertainties if item.uncertainty_id == "synthesis:field:severity")
        self.assertTrue(uncertainty.critical)
        self.assertIn("no evidence-backed options", uncertainty.message)

    def test_choice_with_option_relations_becomes_enum(self) -> None:
        document = safety_inspection_golden().document_ir
        option_low = DocumentElement(
            element_id="severity_low",
            page_index=0,
            visual_kind=VisualKind.TEXT,
            bbox=document.elements[2].bbox,
            confidence=0.9,
            text_evidence=(
                TextEvidence(
                    evidence_id="vision_text:severity_low",
                    provider_kind="vision",
                    provider_name="fixture",
                    provider_observation_id="severity_low",
                    raw="Low",
                    normalized="Low",
                    bbox=document.elements[2].bbox,
                    confidence=0.9,
                ),
            ),
        )
        option_high = replace(
            option_low,
            element_id="severity_high",
            text_evidence=(replace(option_low.text_evidence[0], evidence_id="vision_text:severity_high", provider_observation_id="severity_high", raw="High", normalized="High"),),
        )
        relations = document.relations + (
            DocumentRelation(
                relation_id="option:low:severity",
                kind=RelationKind.OPTION_OF,
                source_id="severity_low",
                target_id="severity_control",
                confidence=0.9,
                evidence_ids=("severity_low", "severity_control"),
            ),
            DocumentRelation(
                relation_id="option:high:severity",
                kind=RelationKind.OPTION_OF,
                source_id="severity_high",
                target_id="severity_control",
                confidence=0.9,
                evidence_ids=("severity_high", "severity_control"),
            ),
        )
        enriched = replace(document, elements=document.elements + (option_low, option_high), relations=relations)
        result = synthesize_entity_fields(enriched)
        severity = next(field for field in result.entities[0].fields if field.field_id == "severity")
        self.assertIs(severity.field_type, FieldType.ENUM)
        self.assertEqual(severity.options, ("Low", "High"))

    def test_unknown_semantic_hint_uses_only_strong_visual_fallback(self) -> None:
        document = equipment_checkout_golden().document_ir
        candidates = tuple(
            replace(candidate, value_hint=SemanticValueHint.UNKNOWN)
            if candidate.candidate_id == "field:returned"
            else candidate
            for candidate in document.field_candidates
        )
        result = synthesize_entity_fields(replace(document, field_candidates=candidates))
        returned = next(field for field in result.entities[0].fields if field.field_id == "returned")
        self.assertIs(returned.field_type, FieldType.BOOLEAN)

    def test_unknown_input_box_type_becomes_uncertainty_not_string(self) -> None:
        document = equipment_checkout_golden().document_ir
        candidates = tuple(
            replace(candidate, value_hint=SemanticValueHint.UNKNOWN)
            if candidate.candidate_id == "field:item"
            else candidate
            for candidate in document.field_candidates
        )
        result = synthesize_entity_fields(replace(document, field_candidates=candidates))
        self.assertNotIn("item", {field.field_id for field in result.entities[0].fields})
        self.assertTrue(any(item.uncertainty_id == "synthesis:field:item" and item.critical for item in result.uncertainties))

    def test_unknown_document_type_uses_generic_entity_with_policy_provenance(self) -> None:
        document = equipment_checkout_golden().document_ir
        result = synthesize_entity_fields(replace(document, document=DocumentDescriptor()))
        self.assertEqual(result.entities[0].entity_id, "document_record")
        record = next(item for item in result.provenance if item.target_id == "document_record")
        self.assertIs(record.provenance_class, ProvenanceClass.PRODUCT_POLICY)
        self.assertTrue(any(item.uncertainty_id == "synthesis:document_type_unknown" for item in result.uncertainties))

    def test_slug_collisions_are_resolved_deterministically(self) -> None:
        document = equipment_checkout_golden().document_ir
        candidates = list(document.field_candidates)
        candidates[0] = replace(candidates[0], candidate_id="field:item")
        candidates[1] = replace(candidates[1], candidate_id="field:item!")
        mutated = replace(document, field_candidates=tuple(candidates))
        first = synthesize_entity_fields(mutated)
        second = synthesize_entity_fields(mutated)
        self.assertEqual(first, second)
        self.assertEqual([field.field_id for field in first.entities[0].fields[:2]], ["item", "item_2"])

    def test_pass_with_warnings_document_ir_is_valid_synthesis_input(self) -> None:
        result = synthesize_entity_fields(safety_inspection_golden().document_ir)
        self.assertEqual(result.entities[0].entity_id, "safety_inspection_report_record")
        self.assertGreaterEqual(len(result.decisions), 5)

    def test_invalid_document_ir_fails_closed_before_synthesis(self) -> None:
        document = equipment_checkout_golden().document_ir
        broken_relation = replace(document.relations[0], target_id="missing_element")
        invalid = replace(document, relations=(broken_relation,) + document.relations[1:])
        with self.assertRaises(DocumentIRValidationError):
            synthesize_entity_fields(invalid)

    def test_synthesis_result_does_not_create_views_actions_or_persistence(self) -> None:
        result = synthesize_entity_fields(equipment_checkout_golden().document_ir)
        self.assertFalse(hasattr(result, "views"))
        self.assertFalse(hasattr(result, "actions"))
        self.assertFalse(hasattr(result, "persistence"))

    def test_production_synthesis_has_no_demo_specific_branch_names(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "src" / "paper2app" / "specification" / "synthesis.py").read_text(encoding="utf-8").lower()
        for forbidden in ("equipment_checkout", "equipment checkout", "safety_inspection", "safety inspection"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
