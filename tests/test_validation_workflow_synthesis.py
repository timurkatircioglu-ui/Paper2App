from __future__ import annotations

from dataclasses import replace
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.specification import (
    ActionKind,
    Capability,
    ProvenanceClass,
    ValidationRuleKind,
    synthesize_entity_fields,
    synthesize_validations_workflows,
    synthesize_views_actions_persistence,
)
from paper2app.understanding import (
    DocumentElement,
    DocumentRelation,
    DocumentUncertainty,
    RelationKind,
    SemanticValueHint,
    TextEvidence,
    UncertaintyCode,
    VisualKind,
)
from paper2app.understanding.validation import DocumentIRValidationError
from tests.golden.document_ir_samples import equipment_checkout_golden, safety_inspection_golden


def _surface(document_ir):
    return synthesize_views_actions_persistence(synthesize_entity_fields(document_ir))


def _text_option(document, element_id: str, text: str) -> DocumentElement:
    anchor = document.elements[2]
    return DocumentElement(
        element_id=element_id,
        page_index=0,
        visual_kind=VisualKind.TEXT,
        bbox=anchor.bbox,
        confidence=0.95,
        text_evidence=(
            TextEvidence(
                evidence_id=f"vision_text:{element_id}",
                provider_kind="vision",
                provider_name="fixture",
                provider_observation_id=element_id,
                raw=text,
                normalized=text,
                bbox=anchor.bbox,
                confidence=0.95,
            ),
        ),
    )


def _enum_document(*, with_follows: bool = False, ambiguous: bool = False):
    document = safety_inspection_golden().document_ir
    low = _text_option(document, "severity_low", "Low")
    high = _text_option(document, "severity_high", "High")
    relations = document.relations + (
        DocumentRelation(
            relation_id="option:low:severity",
            kind=RelationKind.OPTION_OF,
            source_id=low.element_id,
            target_id="severity_control",
            confidence=0.95,
            evidence_ids=(low.element_id, "severity_control"),
        ),
        DocumentRelation(
            relation_id="option:high:severity",
            kind=RelationKind.OPTION_OF,
            source_id=high.element_id,
            target_id="severity_control",
            confidence=0.95,
            evidence_ids=(high.element_id, "severity_control"),
        ),
    )
    if with_follows:
        relations += (
            DocumentRelation(
                relation_id="follows:low:high",
                kind=RelationKind.FOLLOWS,
                source_id=low.element_id,
                target_id=high.element_id,
                confidence=0.95,
                evidence_ids=(low.element_id, high.element_id),
            ),
        )
    if ambiguous:
        relations += (
            DocumentRelation(
                relation_id="follows:high:low",
                kind=RelationKind.FOLLOWS,
                source_id=high.element_id,
                target_id=low.element_id,
                confidence=0.95,
                evidence_ids=(high.element_id, low.element_id),
            ),
        )
    return replace(
        document,
        elements=document.elements + (low, high),
        relations=relations,
        uncertainties=(),
    )


class ValidationWorkflowSynthesisTests(unittest.TestCase):
    def test_equipment_golden_does_not_invent_validation_or_workflow(self) -> None:
        document = equipment_checkout_golden().document_ir
        surface = _surface(document)
        result = synthesize_validations_workflows(document, surface)
        self.assertEqual(result.validations, ())
        self.assertEqual(result.workflows, ())
        self.assertNotIn(ActionKind.CHANGE_STATE, {action.kind for action in result.actions})
        self.assertNotIn(Capability.BASIC_WORKFLOW, result.capabilities)

    def test_surface_views_actions_persistence_are_preserved(self) -> None:
        document = equipment_checkout_golden().document_ir
        surface = _surface(document)
        result = synthesize_validations_workflows(document, surface)
        self.assertEqual(result.entities, surface.entities)
        self.assertEqual(result.views, surface.views)
        self.assertEqual(result.persistence, surface.persistence)
        self.assertEqual(result.actions, surface.actions)

    def test_safety_uncertainty_is_preserved_and_document_uncertainty_is_translated(self) -> None:
        document = safety_inspection_golden().document_ir
        surface = _surface(document)
        result = synthesize_validations_workflows(document, surface)
        synthesis_uncertainty = next(item for item in result.uncertainties if item.uncertainty_id == "synthesis:field:severity")
        translated = next(item for item in result.uncertainties if item.uncertainty_id == "document:uncertainty:severity_relation")
        self.assertTrue(synthesis_uncertainty.critical)
        self.assertFalse(translated.critical)
        self.assertEqual(translated.source_refs, ("severity_control",))

    def test_invalid_document_ir_fails_closed(self) -> None:
        valid = equipment_checkout_golden().document_ir
        surface = _surface(valid)
        invalid = replace(valid, source=replace(valid.source, source_sha256="not-a-sha"))
        with self.assertRaises(DocumentIRValidationError):
            synthesize_validations_workflows(invalid, surface)

    def test_enum_options_emit_allowed_values_validation_without_inventing_workflow(self) -> None:
        document = _enum_document()
        result = synthesize_validations_workflows(document, _surface(document))
        validation = next(item for item in result.validations if item.field_id == "severity")
        self.assertIs(validation.kind, ValidationRuleKind.ALLOWED_VALUES)
        self.assertEqual(validation.value, ("Low", "High"))
        self.assertEqual(result.workflows, ())
        provenance = next(item for item in result.provenance if item.target_id == validation.validation_id)
        self.assertIs(provenance.provenance_class, ProvenanceClass.DOCUMENT_DERIVED)
        self.assertIn("option:low:severity", provenance.source_refs)
        self.assertIn("option:high:severity", provenance.source_refs)

    def test_email_type_emits_only_email_format_validation(self) -> None:
        document = equipment_checkout_golden().document_ir
        candidates = list(document.field_candidates)
        candidates[0] = replace(candidates[0], value_hint=SemanticValueHint.EMAIL)
        document = replace(document, field_candidates=tuple(candidates))
        result = synthesize_validations_workflows(document, _surface(document))
        email_validation = next(item for item in result.validations if item.field_id == "name")
        self.assertIs(email_validation.kind, ValidationRuleKind.FORMAT)
        self.assertEqual(email_validation.value, "email")
        self.assertNotIn(ValidationRuleKind.REQUIRED, {item.kind for item in result.validations})
        self.assertNotIn(ValidationRuleKind.MIN, {item.kind for item in result.validations})
        self.assertNotIn(ValidationRuleKind.MAX, {item.kind for item in result.validations})

    def test_explicit_follows_chain_emits_linear_workflow(self) -> None:
        document = _enum_document(with_follows=True)
        result = synthesize_validations_workflows(document, _surface(document))
        self.assertEqual(len(result.workflows), 1)
        workflow = result.workflows[0]
        self.assertEqual([state.display_name for state in workflow.states], ["Low", "High"])
        self.assertEqual(workflow.initial_state_id, workflow.states[0].state_id)
        self.assertEqual(len(workflow.transitions), 1)
        self.assertEqual(workflow.transitions[0].from_state_id, workflow.states[0].state_id)
        self.assertEqual(workflow.transitions[0].to_state_id, workflow.states[1].state_id)

    def test_workflow_adds_explicit_change_state_action_and_capability(self) -> None:
        document = _enum_document(with_follows=True)
        result = synthesize_validations_workflows(document, _surface(document))
        action = next(item for item in result.actions if item.kind is ActionKind.CHANGE_STATE)
        self.assertEqual(action.workflow_id, result.workflows[0].workflow_id)
        self.assertIn(Capability.BASIC_WORKFLOW, result.capabilities)
        action_provenance = next(item for item in result.provenance if item.target_id == action.action_id)
        workflow_provenance = next(item for item in result.provenance if item.target_id == result.workflows[0].workflow_id)
        self.assertIs(action_provenance.provenance_class, ProvenanceClass.PRODUCT_POLICY)
        self.assertIs(workflow_provenance.provenance_class, ProvenanceClass.DOCUMENT_DERIVED)
        self.assertIn("follows:low:high", workflow_provenance.source_refs)

    def test_ambiguous_follows_graph_blocks_workflow(self) -> None:
        document = _enum_document(with_follows=True, ambiguous=True)
        result = synthesize_validations_workflows(document, _surface(document))
        self.assertEqual(result.workflows, ())
        self.assertNotIn(ActionKind.CHANGE_STATE, {action.kind for action in result.actions})
        self.assertNotIn(Capability.BASIC_WORKFLOW, result.capabilities)
        uncertainty = next(item for item in result.uncertainties if item.uncertainty_id.endswith(":ambiguous"))
        self.assertTrue(uncertainty.critical)

    def test_document_uncertainty_touching_emitted_field_becomes_critical(self) -> None:
        document = equipment_checkout_golden().document_ir
        uncertainty = DocumentUncertainty(
            uncertainty_id="uncertainty:name_text",
            code=UncertaintyCode.TEXT_CONFLICT,
            message="Name text differs between providers.",
            evidence_ids=("name_input",),
        )
        document = replace(document, uncertainties=(uncertainty,))
        result = synthesize_validations_workflows(document, _surface(document))
        translated = next(item for item in result.uncertainties if item.uncertainty_id == "document:uncertainty:name_text")
        self.assertTrue(translated.critical)
        self.assertEqual(translated.target_ids, ("name",))

    def test_unknown_document_uncertainty_is_fail_safe_critical(self) -> None:
        document = equipment_checkout_golden().document_ir
        uncertainty = DocumentUncertainty(
            uncertainty_id="uncertainty:unknown",
            code=UncertaintyCode.UNKNOWN,
            message="Unclassified ambiguity remains.",
            evidence_ids=("equipment_form",),
        )
        document = replace(document, uncertainties=(uncertainty,))
        result = synthesize_validations_workflows(document, _surface(document))
        translated = next(item for item in result.uncertainties if item.uncertainty_id == "document:uncertainty:unknown")
        self.assertTrue(translated.critical)

    def test_repeated_synthesis_is_structurally_deterministic(self) -> None:
        document = _enum_document(with_follows=True)
        surface = _surface(document)
        self.assertEqual(
            synthesize_validations_workflows(document, surface),
            synthesize_validations_workflows(document, surface),
        )

    def test_production_behavior_synthesis_has_no_demo_specific_branch_markers(self) -> None:
        source_path = Path(__file__).resolve().parents[1] / "src" / "paper2app" / "specification" / "behavior_synthesis.py"
        source = source_path.read_text(encoding="utf-8").lower()
        for marker in ("equipment_checkout", "equipment checkout", "safety_inspection", "safety inspection"):
            self.assertNotIn(marker, source)


if __name__ == "__main__":
    unittest.main()
