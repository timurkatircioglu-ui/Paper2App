# F02-W03 — Visual Structure Observation Contract

**Status:** CLOSED / PASS
**Project:** Paper2App
**Phase:** F02 — Input Understanding / Paper Understanding Engine

## Goal

Define the provider-independent structural observation language that sits between normalized document imagery and later Vision/OCR provider adapters, fusion, and DocumentIR assembly.

W03 answers:

> What can Paper2App safely represent as a visual observation before committing to document semantics or application behavior?

## Boundary

W03 owns contracts and deterministic invariants only.

It does not own:

- computer-vision detection algorithms;
- OCR engines;
- provider SDKs or prompts;
- provider retries/fallbacks;
- field semantic-type inference;
- relation synthesis;
- DocumentIR assembly;
- AppSpec/application behavior.

Provider ports begin in F02-W04. Fusion and DocumentIR assembly begin in F02-W05.

## Core law

**Observation is not inference.**

Examples:

- `visual_kind=checkbox` is an observable structural classification;
- `control_state=checked` is an observable state hint;
- `raw="Returned"` is preserved source text;
- `role_hint=field_label` is a separate bounded structural inference;
- no observation object may silently become an application field or workflow rule.

## Contract types

Implementation:

- `src/paper2app/understanding/observations.py`
- `src/paper2app/understanding/__init__.py`

Public contract types:

- `NormalizedBox`
- `ObservedText`
- `RegionObservation`
- `ElementObservation`
- `StructuralInference`
- `VisualObservationBatch`

Bounded vocabularies:

- `RegionKind`
- `VisualKind`
- `ControlState`
- `StructuralRoleHint`

## Geometry

All observation geometry uses normalized coordinates against the relevant page/image coordinate space.

`NormalizedBox` fields:

- `x`
- `y`
- `w`
- `h`

Deterministic rules:

- values must be numeric and finite;
- origin must be inside `0.0..1.0`;
- width/height must be positive;
- the entire rectangle must remain inside normalized page bounds.

Geometry is evidence, not UI layout.

## Region vocabulary

`RegionKind` mirrors the bounded DocumentIR baseline:

- `title_area`
- `section`
- `field_group`
- `table_like`
- `instructions`
- `footer`
- `unknown`

`unknown` is legal and preferable to invented certainty.

## Visual element vocabulary

`VisualKind` mirrors the bounded DocumentIR visual vocabulary:

- `text`
- `blank_line`
- `input_box`
- `checkbox`
- `radio`
- `signature_line`
- `handwriting_area`
- `separator`
- `arrow`
- `unknown`

The contract deliberately does not contain React widgets, database types, CRUD actions, or AppSpec concepts.

## Text preservation

`ObservedText` keeps:

- `raw` — mandatory source extraction;
- `normalized` — optional normalized representation;
- `confidence` — optional bounded confidence.

Raw text is never replaced by normalized text.

A text payload is legal only on `visual_kind=text`; other visual elements cannot smuggle semantic text into their observation payload.

## Control state

`ControlState` is bounded to:

- `checked`
- `unchecked`
- `unknown`

A non-unknown control state is legal only for checkbox/radio observations.

This records visible state without committing business meaning.

## Structural inference

`StructuralInference` is intentionally separate from `ElementObservation` and `RegionObservation`.

Bounded role hints:

- `field_label`
- `field_value_area`
- `section_heading`
- `notes_area`
- `approval_area`
- `instructions`
- `unknown`

Each inference may contain:

- independent `inference_id`;
- `target_id` referencing an observed region/element;
- optional confidence;
- zero or more observable `evidence_ids`.

Inference evidence may reference observations only. It may not cite another inference as if it were source evidence.

## Batch invariants

`VisualObservationBatch` validates the observation set deterministically:

- `page_count >= 1`;
- regions/elements/inferences are immutable tuples;
- all region and element IDs are globally unique;
- inference IDs cannot collide with observation IDs;
- every region/element page index resolves inside `page_count`;
- every inference target resolves to an observation;
- every inference evidence reference resolves to an observation;
- confidence, when present, is finite and inside `0.0..1.0`.

These invariants are a pre-DocumentIR safety seam. Later phases may add richer relations but cannot weaken these guarantees silently.

## Provider neutrality

W03 contains no provider/model identifiers or SDK-specific payloads.

F02-W04 must adapt provider-specific output into these contracts rather than leaking provider response structures deeper into Paper2App.

This preserves replaceability and makes benchmark comparisons possible on a common representation.

## Acceptance suite

`tests/test_visual_observation_contract.py` covers 15 contract cases:

1. valid normalized geometry;
2. negative-origin rejection;
3. out-of-bounds rectangle rejection;
4. non-finite geometry rejection;
5. confidence bounds;
6. raw/normalized text preservation;
7. text payload restricted to text observations;
8. control state restricted to checkbox/radio observations;
9. legal `unknown` observation/inference;
10. page-reference bounds;
11. duplicate observation-ID rejection across region/element types;
12. unresolved inference-target rejection;
13. unresolved evidence-reference rejection;
14. observation/inference separation;
15. checked-state preservation without semantic commitment.

## Closure evidence

- `python_unittest_pattern` selector `tests.test_visual_observation_contract`: **15/15 PASS**;
- `python_compileall src/paper2app/understanding`: **PASS**;
- no new external dependency required;
- W01/W02 input/normalization implementation files are unchanged by W03;
- provider choice remains deferred to F02-W04;
- observation vocabulary remains aligned with `docs/04_DOCUMENT_IR_V0.md`;
- UNKNOWN remains legal;
- raw text and inference remain separately represented.

## Gate decision

**F02-W03 = CLOSED / PASS**

Next authorized package:

**F02-W04 — Vision/OCR Provider Ports & Acceptance**
