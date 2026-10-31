# F02-W04 — Vision/OCR Provider Ports & Acceptance

**Status:** CLOSED / PASS
**Project:** Paper2App
**Phase:** F02 — Input Understanding / Paper Understanding Engine

## Goal

Define replaceable, versioned Vision/OCR provider boundaries that consume the canonical normalized image representation and emit bounded provider outputs without coupling Paper2App to a specific model, vendor, OCR engine or fallback chain.

## Scope

W04 owns:

- provider-neutral Vision and OCR port interfaces;
- canonical normalized provider-image input contract;
- versioned provider/model/prompt identity metadata;
- OCR exact-text observation contract;
- bounded provider-call retry semantics;
- controlled provider failure codes;
- unexpected-exception normalization;
- single-page Competition V1 response enforcement;
- deterministic fake-provider acceptance tests.

W04 does not own:

- selection of the production vision model/provider;
- selection of the production OCR engine/provider;
- provider benchmarking/calibration;
- multi-provider fallback/routing;
- observation fusion;
- semantic field inference;
- DocumentIR assembly.

Those remain later F02 work.

## Provider input contract

`ProviderImage` is the only image payload exposed to provider adapters in this package.

It carries:

- `source_id`;
- normalized-image SHA-256;
- canonical `image/png` media type;
- normalized width/height;
- canonical normalized bytes.

This keeps provider adapters downstream of F02-W02 normalization and prevents adapters from silently choosing their own source-image interpretation.

## Provider identity

Every adapter exposes a `ProviderIdentity` containing:

- provider kind (`vision` or `ocr`);
- provider name;
- adapter version;
- model identifier;
- optional prompt version.

The identity is returned in the successful provider result envelope so later evidence can record exactly which adapter/model/prompt binding produced observations.

## Vision port

`VisionProvider.analyze(image)` returns a W03 `VisualObservationBatch`.

The provider boundary therefore cannot return application source code, CRUD definitions, database structures or arbitrary unvalidated dictionaries as the canonical result.

Competition V1 enforces exactly one observed page for one normalized provider image.

## OCR port

`OCRProvider.extract(image)` returns an `OCRObservationBatch` containing bounded `OCRTextObservation` values.

OCR observations preserve:

- observation ID;
- page index;
- normalized geometry;
- raw extracted text;
- optional normalized text;
- raw provider confidence.

OCR remains exact-text evidence only. W04 does not allow OCR output to declare business semantics or application behavior.

## Failure contract

Controlled provider failures use:

- `VISION_FAILED`;
- `OCR_FAILED`.

`ProviderError` also carries a `retryable` flag.

Rules:

1. retry occurs only when `retryable=True`;
2. retry count is bounded by `ProviderCallPolicy`;
3. Competition V1 allows `1..3` attempts, default `2`;
4. non-retryable failure stops immediately;
5. unexpected provider exceptions are converted to the owning provider failure code;
6. unexpected raw provider exception messages are not copied into the normalized outward error;
7. a Vision provider cannot emit the OCR-owned failure code and vice versa;
8. no multi-provider fallback is implied or performed.

## Provider response validation

The wrapper fails closed when:

- provider identity is missing or belongs to the wrong provider kind;
- input is not a canonical `ProviderImage`;
- retry policy is invalid;
- Vision returns anything other than `VisualObservationBatch`;
- OCR returns anything other than `OCRObservationBatch`;
- a provider returns a multi-page result for a single Competition V1 image;
- OCR observation IDs collide or page references are invalid;
- provider confidence is outside `0.0..1.0`.

## Real provider binding decision

No production provider/model is selected in W04.

This is deliberate. Provider/model choice remains benchmark-driven. A real binding must earn its place through measured DocumentIR-level quality, latency, cost and failure behavior rather than popularity or convenience.

Multi-provider fallback is also deferred until measured failure modes justify the complexity.

## Acceptance evidence

`tests/test_provider_ports.py` verifies:

- provider identity/version/prompt metadata;
- canonical provider-image restrictions;
- OCR raw/normalized text preservation;
- OCR confidence bounds;
- OCR ID/page-reference validation;
- bounded call-policy validation;
- Vision success path;
- OCR success path;
- retryable Vision recovery;
- retryable OCR max-attempt stop;
- non-retryable immediate stop;
- unexpected provider exception normalization/sanitization;
- invalid Vision response fail-closed;
- invalid OCR response fail-closed;
- Competition V1 single-page enforcement;
- wrong-kind provider rejection;
- wrong-boundary failure-code normalization;
- invalid provider image rejected before provider invocation;
- invalid call policy rejected before provider invocation.

Acceptance result:

- W04 provider-port suite: **21/21 PASS** via `python -m unittest tests.test_provider_ports`;
- W03 visual-observation regression: **15/15 PASS** via `python -m unittest tests.test_visual_observation_contract`;
- provider/observation package compilation: **PASS** via `python -m compileall src/paper2app/understanding`.

## Closure decision

F02-W04 is `CLOSED / PASS`.

The next authorized package is **F02-W05 — Observation Fusion & DocumentIR Assembly**.
