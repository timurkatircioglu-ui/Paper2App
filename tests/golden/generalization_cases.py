"""Provider-level generalization cases for the F02 closure benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from paper2app.understanding import (
    ElementObservation,
    NormalizedBox,
    ObservedText,
    OCRObservationBatch,
    OCRTextObservation,
    ProviderIdentity,
    ProviderImage,
    ProviderKind,
    RegionKind,
    RegionObservation,
    StructuralInference,
    StructuralRoleHint,
    VisualKind,
    VisualObservationBatch,
)


class _Value(str, Enum):
    PNG = "image/png"
    SCAN = "scan"


@dataclass(frozen=True, slots=True)
class _Source:
    source_id: str
    media_type: _Value
    sha256: str
    capture_kind: _Value = _Value.SCAN


@dataclass(frozen=True, slots=True)
class SyntheticNormalizedImage:
    source: _Source
    original_width: int = 1200
    original_height: int = 1600
    normalized_width: int = 1200
    normalized_height: int = 1600
    normalized_sha256: str = "f" * 64
    operations: tuple[str, ...] = ("canonical_png",)


@dataclass(frozen=True, slots=True)
class StaticVisionProvider:
    identity: ProviderIdentity
    observations: VisualObservationBatch

    def analyze(self, image: ProviderImage) -> VisualObservationBatch:
        return self.observations


@dataclass(frozen=True, slots=True)
class StaticOCRProvider:
    identity: ProviderIdentity
    observations: OCRObservationBatch

    def extract(self, image: ProviderImage) -> OCRObservationBatch:
        return self.observations


@dataclass(frozen=True, slots=True)
class GeneralizationCase:
    name: str
    normalized_image: SyntheticNormalizedImage
    provider_image: ProviderImage
    vision_provider: StaticVisionProvider
    ocr_provider: StaticOCRProvider


def _ids(case_name: str) -> tuple[ProviderIdentity, ProviderIdentity]:
    vision = ProviderIdentity(
        kind=ProviderKind.VISION,
        provider_name="generalization-fixture-vision",
        adapter_version="1",
        model_id="fixture-vision-v1",
        prompt_version="f02-w07-v1",
    )
    ocr = ProviderIdentity(
        kind=ProviderKind.OCR,
        provider_name="generalization-fixture-ocr",
        adapter_version="1",
        model_id="fixture-ocr-v1",
    )
    return vision, ocr


def _case_images(name: str, hex_digit: str) -> tuple[SyntheticNormalizedImage, ProviderImage]:
    source_sha = hex_digit * 64
    normalized_sha = ("f" if hex_digit != "f" else "e") * 64
    source = _Source(source_id=f"source:{name}", media_type=_Value.PNG, sha256=source_sha)
    normalized = SyntheticNormalizedImage(source=source, normalized_sha256=normalized_sha)
    provider = ProviderImage(
        source_id=source.source_id,
        normalized_sha256=normalized_sha,
        media_type="image/png",
        width=normalized.normalized_width,
        height=normalized.normalized_height,
        content=f"synthetic:{name}".encode("utf-8"),
    )
    return normalized, provider


def equipment_checkout_case() -> GeneralizationCase:
    name = "equipment_checkout"
    image, provider_image = _case_images(name, "1")
    vision_id, ocr_id = _ids(name)

    region = RegionObservation(
        region_id="equipment_form",
        page_index=0,
        region_kind=RegionKind.FIELD_GROUP,
        bbox=NormalizedBox(0.05, 0.05, 0.90, 0.85),
        confidence=0.98,
    )
    elements = (
        ElementObservation(
            element_id="name_label",
            page_index=0,
            visual_kind=VisualKind.TEXT,
            bbox=NormalizedBox(0.10, 0.14, 0.18, 0.04),
            confidence=0.97,
            text=ObservedText(raw="Name", normalized="Name", confidence=0.97),
        ),
        ElementObservation(
            element_id="name_input",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.32, 0.13, 0.45, 0.06),
            confidence=0.95,
        ),
        ElementObservation(
            element_id="item_label",
            page_index=0,
            visual_kind=VisualKind.TEXT,
            bbox=NormalizedBox(0.10, 0.25, 0.18, 0.04),
            confidence=0.96,
            text=ObservedText(raw="Item", normalized="Item", confidence=0.96),
        ),
        ElementObservation(
            element_id="item_input",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.32, 0.24, 0.45, 0.06),
            confidence=0.95,
        ),
        ElementObservation(
            element_id="date_input",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.32, 0.35, 0.30, 0.06),
            confidence=0.93,
        ),
        ElementObservation(
            element_id="returned_checkbox",
            page_index=0,
            visual_kind=VisualKind.CHECKBOX,
            bbox=NormalizedBox(0.32, 0.47, 0.04, 0.04),
            confidence=0.96,
        ),
        ElementObservation(
            element_id="signature_line",
            page_index=0,
            visual_kind=VisualKind.SIGNATURE_LINE,
            bbox=NormalizedBox(0.32, 0.59, 0.45, 0.04),
            confidence=0.92,
        ),
    )
    inferences = (
        StructuralInference("inf_name", "name_input", StructuralRoleHint.FIELD_VALUE_AREA, 0.90, ("name_label", "name_input")),
        StructuralInference("inf_item", "item_input", StructuralRoleHint.FIELD_VALUE_AREA, 0.89, ("item_label", "item_input")),
        StructuralInference("inf_date", "date_input", StructuralRoleHint.FIELD_VALUE_AREA, 0.86, ("date_input",)),
        StructuralInference("inf_returned", "returned_checkbox", StructuralRoleHint.FIELD_VALUE_AREA, 0.92, ("returned_checkbox",)),
        StructuralInference("inf_signature", "signature_line", StructuralRoleHint.APPROVAL_AREA, 0.88, ("signature_line",)),
    )
    vision = StaticVisionProvider(
        identity=vision_id,
        observations=VisualObservationBatch(page_count=1, regions=(region,), elements=elements, inferences=inferences),
    )
    ocr = StaticOCRProvider(
        identity=ocr_id,
        observations=OCRObservationBatch(
            page_count=1,
            observations=(
                OCRTextObservation("ocr_name", 0, NormalizedBox(0.10, 0.14, 0.18, 0.04), "NAME", "Name", 0.99),
                OCRTextObservation("ocr_item", 0, NormalizedBox(0.10, 0.25, 0.18, 0.04), "ITEM", "Item", 0.99),
            ),
        ),
    )
    return GeneralizationCase(name, image, provider_image, vision, ocr)


def safety_inspection_case() -> GeneralizationCase:
    name = "safety_inspection"
    image, provider_image = _case_images(name, "2")
    vision_id, ocr_id = _ids(name)

    region = RegionObservation(
        region_id="inspection_form",
        page_index=0,
        region_kind=RegionKind.SECTION,
        bbox=NormalizedBox(0.04, 0.04, 0.92, 0.90),
        confidence=0.97,
    )
    elements = (
        ElementObservation(
            element_id="inspector_label",
            page_index=0,
            visual_kind=VisualKind.TEXT,
            bbox=NormalizedBox(0.08, 0.12, 0.22, 0.04),
            confidence=0.96,
            text=ObservedText(raw="Inspector", normalized="Inspector", confidence=0.96),
        ),
        ElementObservation(
            element_id="inspector_input",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.34, 0.11, 0.48, 0.06),
            confidence=0.94,
        ),
        ElementObservation(
            element_id="location_input",
            page_index=0,
            visual_kind=VisualKind.INPUT_BOX,
            bbox=NormalizedBox(0.34, 0.22, 0.48, 0.06),
            confidence=0.94,
        ),
        ElementObservation(
            element_id="severity_low",
            page_index=0,
            visual_kind=VisualKind.RADIO,
            bbox=NormalizedBox(0.34, 0.34, 0.035, 0.035),
            confidence=0.91,
        ),
        ElementObservation(
            element_id="severity_high",
            page_index=0,
            visual_kind=VisualKind.RADIO,
            bbox=NormalizedBox(0.50, 0.34, 0.035, 0.035),
            confidence=0.90,
        ),
        ElementObservation(
            element_id="notes_area",
            page_index=0,
            visual_kind=VisualKind.HANDWRITING_AREA,
            bbox=NormalizedBox(0.10, 0.46, 0.72, 0.18),
            confidence=0.88,
        ),
        ElementObservation(
            element_id="action_checkbox",
            page_index=0,
            visual_kind=VisualKind.CHECKBOX,
            bbox=NormalizedBox(0.34, 0.70, 0.04, 0.04),
            confidence=0.93,
        ),
        ElementObservation(
            element_id="approval_signature",
            page_index=0,
            visual_kind=VisualKind.SIGNATURE_LINE,
            bbox=NormalizedBox(0.34, 0.80, 0.48, 0.04),
            confidence=0.90,
        ),
    )
    inferences = (
        StructuralInference("inf_inspector", "inspector_input", StructuralRoleHint.FIELD_VALUE_AREA, 0.88, ("inspector_label", "inspector_input")),
        StructuralInference("inf_location", "location_input", StructuralRoleHint.FIELD_VALUE_AREA, 0.87, ("location_input",)),
        StructuralInference("inf_severity_low", "severity_low", StructuralRoleHint.FIELD_VALUE_AREA, 0.86, ("severity_low",)),
        StructuralInference("inf_severity_high", "severity_high", StructuralRoleHint.FIELD_VALUE_AREA, 0.86, ("severity_high",)),
        StructuralInference("inf_notes", "notes_area", StructuralRoleHint.NOTES_AREA, 0.90, ("notes_area",)),
        StructuralInference("inf_action", "action_checkbox", StructuralRoleHint.FIELD_VALUE_AREA, 0.89, ("action_checkbox",)),
        StructuralInference("inf_approval", "approval_signature", StructuralRoleHint.APPROVAL_AREA, 0.87, ("approval_signature",)),
    )
    vision = StaticVisionProvider(
        identity=vision_id,
        observations=VisualObservationBatch(page_count=1, regions=(region,), elements=elements, inferences=inferences),
    )
    ocr = StaticOCRProvider(
        identity=ocr_id,
        observations=OCRObservationBatch(
            page_count=1,
            observations=(
                OCRTextObservation("ocr_inspector", 0, NormalizedBox(0.08, 0.12, 0.22, 0.04), "INSPECTOR", "Inspector", 0.99),
            ),
        ),
    )
    return GeneralizationCase(name, image, provider_image, vision, ocr)


def generalization_cases() -> tuple[GeneralizationCase, ...]:
    return (equipment_checkout_case(), safety_inspection_case())
