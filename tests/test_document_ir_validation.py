from __future__ import annotations

from dataclasses import replace
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.understanding import (
    DocumentIRValidationError,
    DocumentPage,
    TextEvidence,
    ValidationIssueCode,
    ValidationStatus,
    assemble_validated_document_ir,
    require_valid_document_ir,
    validate_document_ir,
)
from tests.test_document_ir_fusion import _NormalizedImage, _ocr_result, _vision_result
from tests.golden.document_ir_samples import (
    equipment_checkout_golden,
    golden_document_ir_samples,
    safety_inspection_golden,
)


class DocumentIRValidationTests(unittest.TestCase):
    def test_golden_samples_match_expected_validation_status(self) -> None:
        samples = golden_document_ir_samples()
        self.assertEqual({sample.name for sample in samples}, {"equipment_checkout", "safety_inspection"})
        for sample in samples:
            with self.subTest(sample=sample.name):
                report = validate_document_ir(sample.document_ir)
                self.assertEqual(report.status, sample.expected_status)
                self.assertTrue(report.is_valid)

    def test_equipment_checkout_golden_is_clean_pass(self) -> None:
        report = validate_document_ir(equipment_checkout_golden().document_ir)
        self.assertEqual(report.status, ValidationStatus.PASS)
        self.assertEqual(report.issues, ())

    def test_safety_inspection_golden_preserves_uncertainty_as_warning(self) -> None:
        report = validate_document_ir(safety_inspection_golden().document_ir)
        self.assertEqual(report.status, ValidationStatus.PASS_WITH_WARNINGS)
        self.assertEqual(len(report.errors), 0)
        self.assertEqual(len(report.warnings), 1)
        self.assertEqual(report.warnings[0].code, ValidationIssueCode.DOCUMENT_UNCERTAINTY)

    def test_require_valid_accepts_pass_and_pass_with_warnings(self) -> None:
        for sample in golden_document_ir_samples():
            with self.subTest(sample=sample.name):
                self.assertIs(require_valid_document_ir(sample.document_ir), sample.document_ir)

    def test_authoritative_egress_assembles_and_validates_before_release(self) -> None:
        document = assemble_validated_document_ir(
            image=_NormalizedImage(),
            vision=_vision_result(),
            ocr=_ocr_result(),
        )
        self.assertTrue(validate_document_ir(document).is_valid)

    def test_non_document_ir_fails_closed(self) -> None:
        report = validate_document_ir(object())
        self.assertEqual(report.status, ValidationStatus.FAIL)
        self.assertEqual(report.errors[0].code, ValidationIssueCode.DOCUMENT_TYPE_INVALID)

    def test_invalid_source_hash_fails(self) -> None:
        document = equipment_checkout_golden().document_ir
        invalid = replace(document, source=replace(document.source, source_sha256="not-a-sha"))
        report = validate_document_ir(invalid)
        self.assertEqual(report.status, ValidationStatus.FAIL)
        self.assertIn(ValidationIssueCode.SOURCE_HASH_INVALID, {issue.code for issue in report.errors})

    def test_page_indices_must_be_contiguous_from_zero(self) -> None:
        document = equipment_checkout_golden().document_ir
        invalid = replace(document, pages=(DocumentPage(page_index=1, width=1200, height=1600),))
        report = validate_document_ir(invalid)
        self.assertIn(ValidationIssueCode.PAGE_SET_INVALID, {issue.code for issue in report.errors})

    def test_single_page_dimensions_must_match_normalized_source(self) -> None:
        document = equipment_checkout_golden().document_ir
        invalid = replace(document, pages=(DocumentPage(page_index=0, width=1000, height=1600),))
        report = validate_document_ir(invalid)
        self.assertIn(ValidationIssueCode.SOURCE_PAGE_MISMATCH, {issue.code for issue in report.errors})

    def test_duplicate_global_id_fails(self) -> None:
        document = equipment_checkout_golden().document_ir
        duplicate = replace(document.elements[0], element_id=document.regions[0].region_id)
        invalid = replace(document, elements=(duplicate,) + document.elements[1:])
        report = validate_document_ir(invalid)
        self.assertIn(ValidationIssueCode.DUPLICATE_ID, {issue.code for issue in report.errors})

    def test_element_page_reference_must_resolve(self) -> None:
        document = equipment_checkout_golden().document_ir
        invalid_element = replace(document.elements[0], page_index=1)
        invalid = replace(document, elements=(invalid_element,) + document.elements[1:])
        report = validate_document_ir(invalid)
        self.assertIn(ValidationIssueCode.PAGE_REFERENCE_INVALID, {issue.code for issue in report.errors})

    def test_field_candidate_target_must_resolve_to_element(self) -> None:
        document = equipment_checkout_golden().document_ir
        invalid_candidate = replace(document.field_candidates[0], target_element_id="missing-element")
        invalid = replace(document, field_candidates=(invalid_candidate,) + document.field_candidates[1:])
        report = validate_document_ir(invalid)
        self.assertIn(ValidationIssueCode.FIELD_TARGET_INVALID, {issue.code for issue in report.errors})

    def test_relation_endpoints_must_resolve_to_structural_observations(self) -> None:
        document = equipment_checkout_golden().document_ir
        invalid_relation = replace(document.relations[0], target_id=document.field_candidates[0].candidate_id)
        invalid = replace(document, relations=(invalid_relation,) + document.relations[1:])
        report = validate_document_ir(invalid)
        self.assertIn(ValidationIssueCode.RELATION_ENDPOINT_INVALID, {issue.code for issue in report.errors})

    def test_evidence_reference_must_resolve_to_observable_evidence(self) -> None:
        document = equipment_checkout_golden().document_ir
        invalid_candidate = replace(document.field_candidates[0], evidence_ids=("missing-evidence",))
        invalid = replace(document, field_candidates=(invalid_candidate,) + document.field_candidates[1:])
        report = validate_document_ir(invalid)
        self.assertIn(ValidationIssueCode.EVIDENCE_REFERENCE_INVALID, {issue.code for issue in report.errors})

    def test_duplicate_text_evidence_id_fails_global_uniqueness(self) -> None:
        document = equipment_checkout_golden().document_ir
        original_evidence = document.elements[0].text_evidence[0]
        duplicate_evidence = TextEvidence(
            evidence_id=original_evidence.evidence_id,
            provider_kind="ocr",
            provider_name="golden-ocr",
            provider_observation_id="duplicate",
            raw="Name",
            normalized="Name",
            bbox=original_evidence.bbox,
            confidence=0.90,
        )
        invalid_element = replace(
            document.elements[0],
            text_evidence=document.elements[0].text_evidence + (duplicate_evidence,),
        )
        invalid = replace(document, elements=(invalid_element,) + document.elements[1:])
        report = validate_document_ir(invalid)
        self.assertIn(ValidationIssueCode.DUPLICATE_ID, {issue.code for issue in report.errors})

    def test_duplicate_reference_inside_evidence_list_fails(self) -> None:
        document = equipment_checkout_golden().document_ir
        invalid_candidate = replace(document.field_candidates[0], evidence_ids=("name_input", "name_input"))
        invalid = replace(document, field_candidates=(invalid_candidate,) + document.field_candidates[1:])
        report = validate_document_ir(invalid)
        self.assertIn(ValidationIssueCode.DUPLICATE_REFERENCE, {issue.code for issue in report.errors})

    def test_uncertainty_with_missing_evidence_is_fail_not_warning_only(self) -> None:
        document = safety_inspection_golden().document_ir
        invalid_uncertainty = replace(document.uncertainties[0], evidence_ids=("missing-evidence",))
        invalid = replace(document, uncertainties=(invalid_uncertainty,))
        report = validate_document_ir(invalid)
        self.assertEqual(report.status, ValidationStatus.FAIL)
        self.assertIn(ValidationIssueCode.EVIDENCE_REFERENCE_INVALID, {issue.code for issue in report.errors})
        self.assertIn(ValidationIssueCode.DOCUMENT_UNCERTAINTY, {issue.code for issue in report.warnings})

    def test_unknown_schema_is_rejected_even_if_object_was_mutated_after_construction(self) -> None:
        document = equipment_checkout_golden().document_ir
        object.__setattr__(document, "schema", "paper2app.document_ir.future")
        report = validate_document_ir(document)
        self.assertIn(ValidationIssueCode.SCHEMA_INVALID, {issue.code for issue in report.errors})

    def test_require_valid_raises_structured_error_for_invalid_graph(self) -> None:
        document = equipment_checkout_golden().document_ir
        invalid = replace(document, pages=(DocumentPage(page_index=1, width=1200, height=1600),))
        with self.assertRaises(DocumentIRValidationError) as context:
            require_valid_document_ir(invalid)
        self.assertEqual(context.exception.report.status, ValidationStatus.FAIL)

    def test_validation_report_is_deterministic_for_same_graph(self) -> None:
        document = safety_inspection_golden().document_ir
        self.assertEqual(validate_document_ir(document), validate_document_ir(document))


if __name__ == "__main__":
    unittest.main()
