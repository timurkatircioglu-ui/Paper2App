from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.understanding import (
    ControlState,
    ElementObservation,
    NormalizedBox,
    ObservedText,
    RegionKind,
    RegionObservation,
    StructuralInference,
    StructuralRoleHint,
    VisualKind,
    VisualObservationBatch,
)


class VisualObservationContractTests(unittest.TestCase):
    def test_normalized_box_accepts_valid_geometry(self) -> None:
        box = NormalizedBox(0.1, 0.2, 0.3, 0.4)
        self.assertEqual((box.x, box.y, box.w, box.h), (0.1, 0.2, 0.3, 0.4))

    def test_normalized_box_rejects_negative_origin(self) -> None:
        with self.assertRaises(ValueError):
            NormalizedBox(-0.1, 0.0, 0.2, 0.2)

    def test_normalized_box_rejects_out_of_bounds_extent(self) -> None:
        with self.assertRaises(ValueError):
            NormalizedBox(0.9, 0.2, 0.2, 0.2)

    def test_normalized_box_rejects_non_finite_values(self) -> None:
        with self.assertRaises(ValueError):
            NormalizedBox(0.0, 0.0, math.inf, 0.2)

    def test_confidence_must_be_within_unit_interval(self) -> None:
        with self.assertRaises(ValueError):
            RegionObservation(
                region_id="region-1",
                page_index=0,
                region_kind=RegionKind.SECTION,
                bbox=NormalizedBox(0.0, 0.0, 1.0, 0.5),
                confidence=1.1,
            )

    def test_observed_text_preserves_raw_and_normalized_separately(self) -> None:
        text = ObservedText(raw="DATE :", normalized="Date", confidence=0.96)
        self.assertEqual(text.raw, "DATE :")
        self.assertEqual(text.normalized, "Date")

    def test_text_payload_is_only_legal_for_text_visual_kind(self) -> None:
        with self.assertRaises(ValueError):
            ElementObservation(
                element_id="element-1",
                page_index=0,
                visual_kind=VisualKind.INPUT_BOX,
                bbox=NormalizedBox(0.1, 0.1, 0.2, 0.1),
                text=ObservedText(raw="Name"),
            )

    def test_control_state_is_only_legal_for_checkbox_or_radio(self) -> None:
        with self.assertRaises(ValueError):
            ElementObservation(
                element_id="element-1",
                page_index=0,
                visual_kind=VisualKind.INPUT_BOX,
                bbox=NormalizedBox(0.1, 0.1, 0.2, 0.1),
                control_state=ControlState.CHECKED,
            )

    def test_unknown_is_a_legal_observation_and_hint(self) -> None:
        element = ElementObservation(
            element_id="element-unknown",
            page_index=0,
            visual_kind=VisualKind.UNKNOWN,
            bbox=NormalizedBox(0.2, 0.2, 0.1, 0.1),
        )
        inference = StructuralInference(
            inference_id="inference-unknown",
            target_id="element-unknown",
            role_hint=StructuralRoleHint.UNKNOWN,
        )
        batch = VisualObservationBatch(page_count=1, elements=(element,), inferences=(inference,))
        self.assertIs(batch.elements[0].visual_kind, VisualKind.UNKNOWN)
        self.assertIs(batch.inferences[0].role_hint, StructuralRoleHint.UNKNOWN)

    def test_batch_rejects_page_reference_outside_page_count(self) -> None:
        region = RegionObservation(
            region_id="region-1",
            page_index=1,
            region_kind=RegionKind.SECTION,
            bbox=NormalizedBox(0.0, 0.0, 1.0, 1.0),
        )
        with self.assertRaises(ValueError):
            VisualObservationBatch(page_count=1, regions=(region,))

    def test_batch_rejects_duplicate_observation_ids_across_types(self) -> None:
        region = RegionObservation(
            region_id="same-id",
            page_index=0,
            region_kind=RegionKind.SECTION,
            bbox=NormalizedBox(0.0, 0.0, 1.0, 0.5),
        )
        element = ElementObservation(
            element_id="same-id",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.1, 0.1, 0.2, 0.1),
        )
        with self.assertRaises(ValueError):
            VisualObservationBatch(page_count=1, regions=(region,), elements=(element,))

    def test_batch_rejects_unresolved_inference_target(self) -> None:
        inference = StructuralInference(
            inference_id="inference-1",
            target_id="missing",
            role_hint=StructuralRoleHint.FIELD_LABEL,
        )
        with self.assertRaises(ValueError):
            VisualObservationBatch(page_count=1, inferences=(inference,))

    def test_batch_rejects_unresolved_inference_evidence(self) -> None:
        element = ElementObservation(
            element_id="element-1",
            page_index=0,
            visual_kind=VisualKind.TEXT,
            bbox=NormalizedBox(0.1, 0.1, 0.2, 0.05),
            text=ObservedText(raw="Returned"),
        )
        inference = StructuralInference(
            inference_id="inference-1",
            target_id="element-1",
            role_hint=StructuralRoleHint.FIELD_LABEL,
            evidence_ids=("missing",),
        )
        with self.assertRaises(ValueError):
            VisualObservationBatch(page_count=1, elements=(element,), inferences=(inference,))

    def test_observation_and_inference_remain_separate(self) -> None:
        label = ElementObservation(
            element_id="text-returned",
            page_index=0,
            visual_kind=VisualKind.TEXT,
            bbox=NormalizedBox(0.1, 0.2, 0.15, 0.05),
            confidence=0.99,
            text=ObservedText(raw="Returned", confidence=0.98),
        )
        checkbox = ElementObservation(
            element_id="checkbox-returned",
            page_index=0,
            visual_kind=VisualKind.CHECKBOX,
            bbox=NormalizedBox(0.3, 0.2, 0.03, 0.03),
            control_state=ControlState.UNKNOWN,
        )
        hint = StructuralInference(
            inference_id="hint-label",
            target_id="text-returned",
            role_hint=StructuralRoleHint.FIELD_LABEL,
            confidence=0.84,
            evidence_ids=("text-returned", "checkbox-returned"),
        )
        batch = VisualObservationBatch(page_count=1, elements=(label, checkbox), inferences=(hint,))

        self.assertIs(batch.elements[0].visual_kind, VisualKind.TEXT)
        self.assertIs(batch.inferences[0].role_hint, StructuralRoleHint.FIELD_LABEL)
        self.assertNotEqual(batch.elements[0].element_id, batch.inferences[0].inference_id)

    def test_checkbox_can_preserve_checked_state_without_semantic_commitment(self) -> None:
        checkbox = ElementObservation(
            element_id="checkbox-1",
            page_index=0,
            visual_kind=VisualKind.CHECKBOX,
            bbox=NormalizedBox(0.4, 0.4, 0.03, 0.03),
            control_state=ControlState.CHECKED,
        )
        batch = VisualObservationBatch(page_count=1, elements=(checkbox,))
        self.assertIs(batch.elements[0].control_state, ControlState.CHECKED)


if __name__ == "__main__":
    unittest.main()
