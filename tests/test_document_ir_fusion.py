from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.understanding import (
    ElementObservation,
    NormalizedBox,
    ObservedText,
    OCRObservationBatch,
    OCRProviderResult,
    OCRTextObservation,
    ProviderIdentity,
    ProviderKind,
    RegionKind,
    RegionObservation,
    StructuralInference,
    StructuralRoleHint,
    VisualKind,
    VisualObservationBatch,
    VisionProviderResult,
)
from paper2app.understanding.document_ir import (
    DOCUMENT_IR_SCHEMA,
    DOCUMENT_IR_SCHEMA_VERSION,
    RelationKind,
    SemanticValueHint,
    UncertaintyCode,
)
from paper2app.understanding.fusion import assemble_document_ir


class _Value(str, Enum):
    PNG = "image/png"
    UPLOAD = "upload"


@dataclass(frozen=True)
class _Source:
    source_id: str = "src_demo"
    media_type: _Value = _Value.PNG
    sha256: str = "a" * 64
    capture_kind: _Value = _Value.UPLOAD


@dataclass(frozen=True)
class _NormalizedImage:
    source: _Source = _Source()
    original_width: int = 1600
    original_height: int = 1000
    normalized_width: int = 1600
    normalized_height: int = 1000
    normalized_sha256: str = "b" * 64
    operations: tuple[str, ...] = ("canonical_png",)


VISION_ID = ProviderIdentity(
    kind=ProviderKind.VISION,
    provider_name="vision-fixture",
    adapter_version="1",
    model_id="fixture-model",
    prompt_version="p1",
)
OCR_ID = ProviderIdentity(
    kind=ProviderKind.OCR,
    provider_name="ocr-fixture",
    adapter_version="1",
    model_id="fixture-ocr",
)


def _vision_result(*, text: str = "DATE :", checkbox: bool = True) -> VisionProviderResult:
    region = RegionObservation(
        region_id="region_main",
        page_index=0,
        region_kind=RegionKind.FIELD_GROUP,
        bbox=NormalizedBox(0.05, 0.10, 0.90, 0.60),
        confidence=0.93,
    )
    elements = [
        ElementObservation(
            element_id="label_date",
            page_index=0,
            visual_kind=VisualKind.TEXT,
            bbox=NormalizedBox(0.10, 0.20, 0.20, 0.05),
            confidence=0.91,
            text=ObservedText(raw=text, normalized="Date", confidence=0.90),
        ),
        ElementObservation(
            element_id="date_input",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.35, 0.19, 0.30, 0.07),
            confidence=0.88,
        ),
        ElementObservation(
            element_id="notes_box",
            page_index=0,
            visual_kind=VisualKind.HANDWRITING_AREA,
            bbox=NormalizedBox(0.10, 0.40, 0.70, 0.20),
            confidence=0.82,
        ),
    ]
    inferences = [
        StructuralInference(
            inference_id="inf_date_value",
            target_id="date_input",
            role_hint=StructuralRoleHint.FIELD_VALUE_AREA,
            confidence=0.84,
            evidence_ids=("label_date", "date_input"),
        ),
        StructuralInference(
            inference_id="inf_notes",
            target_id="notes_box",
            role_hint=StructuralRoleHint.NOTES_AREA,
            confidence=0.80,
            evidence_ids=("notes_box",),
        ),
    ]
    if checkbox:
        elements.append(
            ElementObservation(
                element_id="returned_check",
                page_index=0,
                visual_kind=VisualKind.CHECKBOX,
                bbox=NormalizedBox(0.70, 0.20, 0.04, 0.04),
                confidence=0.95,
            )
        )
        inferences.append(
            StructuralInference(
                inference_id="inf_returned",
                target_id="returned_check",
                role_hint=StructuralRoleHint.FIELD_VALUE_AREA,
                confidence=0.89,
                evidence_ids=("returned_check",),
            )
        )
    return VisionProviderResult(
        provider=VISION_ID,
        observations=VisualObservationBatch(
            page_count=1,
            regions=(region,),
            elements=tuple(elements),
            inferences=tuple(inferences),
        ),
        attempts=1,
    )


def _ocr_result(*, text: str = "DATE:", bbox: NormalizedBox | None = None) -> OCRProviderResult:
    return OCRProviderResult(
        provider=OCR_ID,
        observations=OCRObservationBatch(
            page_count=1,
            observations=(
                OCRTextObservation(
                    observation_id="ocr_date",
                    page_index=0,
                    bbox=bbox or NormalizedBox(0.105, 0.202, 0.19, 0.045),
                    raw_text=text,
                    normalized_text=text,
                    provider_confidence=0.97,
                ),
            ),
        ),
        attempts=1,
    )


class DocumentIRFusionTests(unittest.TestCase):
    def test_assembles_canonical_schema_source_and_unknown_document_type(self) -> None:
        result = assemble_document_ir(_NormalizedImage(), _vision_result())
        self.assertEqual(result.schema, DOCUMENT_IR_SCHEMA)
        self.assertEqual(result.schema_version, DOCUMENT_IR_SCHEMA_VERSION)
        self.assertEqual(result.source.source_id, "src_demo")
        self.assertEqual(result.source.normalized_sha256, "b" * 64)
        self.assertEqual(result.document.document_type_hint, "unknown")
        self.assertIsNone(result.document.confidence)
        self.assertEqual(result.pages[0].width, 1600)
        self.assertEqual(result.pages[0].height, 1000)

    def test_vision_and_matching_ocr_text_are_preserved_as_separate_evidence(self) -> None:
        result = assemble_document_ir(_NormalizedImage(), _vision_result(), _ocr_result())
        label = next(element for element in result.elements if element.element_id == "label_date")
        self.assertEqual(len(label.text_evidence), 2)
        self.assertEqual({item.provider_kind for item in label.text_evidence}, {"vision", "ocr"})
        self.assertEqual({item.raw for item in label.text_evidence}, {"DATE :", "DATE:"})

    def test_equivalent_spacing_and_punctuation_does_not_create_text_conflict(self) -> None:
        result = assemble_document_ir(_NormalizedImage(), _vision_result(), _ocr_result())
        self.assertFalse(any(item.code is UncertaintyCode.TEXT_CONFLICT for item in result.uncertainties))

    def test_real_provider_text_disagreement_creates_explicit_uncertainty(self) -> None:
        result = assemble_document_ir(_NormalizedImage(), _vision_result(), _ocr_result(text="NAME"))
        conflict = next(item for item in result.uncertainties if item.code is UncertaintyCode.TEXT_CONFLICT)
        self.assertEqual(conflict.evidence_ids, ("vision_text:label_date", "ocr_text:ocr_date"))

    def test_unmatched_ocr_text_becomes_standalone_text_element(self) -> None:
        result = assemble_document_ir(
            _NormalizedImage(),
            _vision_result(),
            _ocr_result(bbox=NormalizedBox(0.82, 0.82, 0.12, 0.04)),
        )
        element = next(item for item in result.elements if item.element_id == "ocr_element_0000")
        self.assertEqual(element.visual_kind, VisualKind.TEXT)
        self.assertEqual(element.text_evidence[0].provider_observation_id, "ocr_date")

    def test_field_candidates_are_bounded_document_semantics(self) -> None:
        result = assemble_document_ir(_NormalizedImage(), _vision_result())
        by_target = {item.target_element_id: item for item in result.field_candidates}
        self.assertEqual(by_target["date_input"].value_hint, SemanticValueHint.FREE_TEXT)
        self.assertEqual(by_target["notes_box"].value_hint, SemanticValueHint.MULTILINE_TEXT)
        self.assertEqual(by_target["returned_check"].value_hint, SemanticValueHint.BOOLEAN)

    def test_field_candidate_preserves_observable_evidence_references(self) -> None:
        result = assemble_document_ir(_NormalizedImage(), _vision_result())
        candidate = next(item for item in result.field_candidates if item.target_element_id == "date_input")
        self.assertEqual(candidate.evidence_ids, ("date_input", "label_date"))

    def test_region_containment_becomes_deterministic_contains_relations(self) -> None:
        result = assemble_document_ir(_NormalizedImage(), _vision_result())
        relations = {(item.source_id, item.target_id, item.kind) for item in result.relations}
        self.assertIn(("region_main", "label_date", RelationKind.CONTAINS), relations)
        self.assertIn(("region_main", "notes_box", RelationKind.CONTAINS), relations)

    def test_ocr_is_optional(self) -> None:
        result = assemble_document_ir(_NormalizedImage(), _vision_result(), None)
        label = next(element for element in result.elements if element.element_id == "label_date")
        self.assertEqual(len(label.text_evidence), 1)
        self.assertEqual(label.text_evidence[0].provider_kind, "vision")

    def test_page_count_disagreement_fails_closed(self) -> None:
        bad_ocr = OCRProviderResult(
            provider=OCR_ID,
            observations=OCRObservationBatch(page_count=2, observations=()),
            attempts=1,
        )
        with self.assertRaisesRegex(ValueError, "page_count"):
            assemble_document_ir(_NormalizedImage(), _vision_result(), bad_ocr)

    def test_non_normalized_image_shape_is_rejected(self) -> None:
        with self.assertRaisesRegex(TypeError, "normalized-image"):
            assemble_document_ir(object(), _vision_result())  # type: ignore[arg-type]

    def test_visual_label_inference_does_not_become_a_value_field(self) -> None:
        vision = _vision_result(checkbox=False)
        label_inference = StructuralInference(
            inference_id="inf_label",
            target_id="label_date",
            role_hint=StructuralRoleHint.FIELD_LABEL,
            confidence=0.9,
            evidence_ids=("label_date",),
        )
        augmented = VisionProviderResult(
            provider=vision.provider,
            observations=VisualObservationBatch(
                page_count=1,
                regions=vision.observations.regions,
                elements=vision.observations.elements,
                inferences=vision.observations.inferences + (label_inference,),
            ),
            attempts=1,
        )
        result = assemble_document_ir(_NormalizedImage(), augmented)
        self.assertFalse(any(item.target_element_id == "label_date" for item in result.field_candidates))

    def test_document_ir_has_no_application_implementation_surface(self) -> None:
        result = assemble_document_ir(_NormalizedImage(), _vision_result())
        forbidden = {"sql", "react", "crud", "api_routes", "storage_engine", "css", "workflow_code"}
        self.assertTrue(forbidden.isdisjoint(result.__dataclass_fields__.keys()))


if __name__ == "__main__":
    unittest.main()
