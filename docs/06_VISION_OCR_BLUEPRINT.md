# Paper2App — Vision/OCR Blueprint V0.1

**Status:** Canonical competition baseline

## Goal

Convert a supported document image into a validated DocumentIR without making application-implementation decisions.

## Pipeline

`Source image -> Input gate -> Image normalization -> Visual structure pass -> Vision/OCR observations -> Fusion -> Semantic candidates -> DocumentIR assembly -> Deterministic validation`

## Input gate

Competition V1 initially targets:

- JPG/PNG;
- single-page camera photo or scan;
- printed forms/workflow sheets;
- bounded handwriting tolerance.

Reject or warn explicitly for corrupt images, unusable resolution, unsupported multi-page inputs or document complexity outside the declared capability envelope.

## Image normalization

Candidate deterministic operations:

- EXIF orientation;
- rotation;
- page boundary/crop;
- perspective correction;
- bounded resize;
- mild contrast/denoise where evidence shows benefit.

Avoid destructive over-processing. Preserve original and normalized representations separately.

## Vision responsibility

Vision may identify:

- document/section structure;
- text/label regions;
- blank lines and input boxes;
- checkboxes/radio-like controls;
- signature/notes areas;
- spatial relationships;
- bounded semantic-role candidates.

Vision must not generate application source code, database structures or executable runtime instructions.

## OCR responsibility

OCR is an exact-text extraction aid. It may provide text, location and provider confidence. OCR is not the semantic or workflow authority.

OCR policy (always-on vs conditional) remains benchmark-driven.

## Provider abstraction

Keep logical interfaces such as:

- `VisionProvider.analyze(image)` -> observations
- `OCRProvider.extract(image)` -> text observations

Provider selection must remain replaceable behind stable internal contracts.

## Fusion

Fusion combines:

- vision observations;
- OCR observations;
- normalized geometry;
- deterministic proximity/alignment features;
- bounded semantic inference.

Provider disagreement must remain observable rather than being silently overwritten.

## Observation vs inference

Example:

Observation:
- text `Returned` exists;
- adjacent square control exists;
- horizontal alignment is strong.

Inference:
- text likely labels the checkbox;
- expected value may be boolean.

These layers remain distinguishable in DocumentIR/evidence.

## Spatial reasoning

Geometry is necessary for forms because text alone cannot reliably associate labels with inputs. Useful evidence includes:

- left/right proximity;
- above/below relationship;
- horizontal/vertical alignment;
- containment;
- same-region membership;
- bounded reading order.

## Checkboxes and choices

Visual detection may classify controls and state hints (`checked`, `unchecked`, `unknown`). Application-field commitment occurs later in AppSpec synthesis.

## Handwriting policy

Paper2App may understand the layout of forms containing handwriting without claiming perfect handwriting transcription. Heavy handwriting OCR is not a competition V1 success requirement unless later benchmark evidence supports it.

## Tables

Complex general table understanding is initially out of scope. A `table_like` hint may be emitted and unsupported complexity may fail explicitly.

## Confidence

Preserve provider confidence separately from any Paper2App-derived/calibrated confidence. Do not assume confidence values from different providers are directly comparable.

Calibration thresholds must be benchmark-driven.

## Failure taxonomy

Candidate failures/warnings:

- `INPUT_UNSUPPORTED`
- `IMAGE_CORRUPT`
- `IMAGE_TOO_SMALL`
- `PAGE_NOT_DETECTED`
- `PERSPECTIVE_FAILED`
- `VISION_FAILED`
- `OCR_FAILED`
- `TEXT_CONFLICT`
- `LAYOUT_AMBIGUOUS`
- `FIELD_RELATION_AMBIGUOUS`
- `DOCUMENT_UNSUPPORTED`
- `DOCUMENT_IR_INVALID`

OCR failure does not automatically imply total pipeline failure if vision evidence remains sufficient for a valid DocumentIR.

## Retry/fallback policy

Retries and fallbacks are bounded. Do not introduce multi-provider fallback complexity until measured failure modes justify it.

## Privacy / logging

- minimize raw image retention;
- avoid logging full sensitive document text by default;
- never log secrets;
- prefer synthetic/redacted competition benchmark examples where possible.

## Observability

Per-run evidence may include:

- preprocess/vision/OCR/fusion timing;
- elements detected;
- field candidates;
- low-confidence count;
- validation result;
- provider/prompt version identifiers.

## Benchmark strategy

Provider/prompt choices are evaluated against DocumentIR-level quality, not popularity.

Core metrics:

- text accuracy;
- element detection;
- field detection;
- label-input association;
- field semantic-hint accuracy;
- section/layout accuracy;
- valid DocumentIR rate;
- latency;
- cost per document;
- failure rate.

Primary AI-side North Star: **VALID DOCUMENT IR RATE**.

Later product North Star: **END-TO-END PAPER -> WORKING APP SUCCESS**.

## Golden samples

Create a small manually verified golden set early in implementation. Keep demo samples distinct from the broader benchmark set to reduce demo overfitting.

## Architecture laws

- V1 Vision observes documents; it does not design applications.
- V2 OCR extracts text; it does not infer business logic.
- V3 Original and normalized images remain distinguishable.
- V4 Raw observations are not silently overwritten.
- V5 Geometry is first-class evidence.
- V6 Vision/OCR disagreement remains observable.
- V7 UNKNOWN is preferable to invented certainty.
- V8 Providers remain replaceable.
- V9 Only validated DocumentIR leaves the pipeline.
- V10 Quality is measured at DocumentIR/end-to-end level, not OCR alone.
- V11 Retries/fallbacks are bounded.
- V12 Sensitive content is not unnecessarily retained/logged.
