# F02-W02 — Deterministic Image Decode & Normalization

**Status:** CLOSED / PASS
**Project:** Paper2App
**Phase:** F02 — Input Understanding / Paper Understanding Engine

## Goal

Decode an admitted PNG/JPEG source into a bounded, canonical image representation while preserving original-source identity and keeping normalization deterministic and inspectable.

## Scope

W02 owns:

- real PNG/JPEG pixel decode;
- decoded width/height observation;
- pre-load pixel-count safety enforcement;
- minimum usable-resolution enforcement;
- EXIF orientation application;
- alpha flattening onto white for canonical form imagery;
- bounded aspect-ratio-preserving resize;
- canonical metadata-free PNG output;
- separate normalized SHA-256 identity;
- explicit normalization operation evidence.

W02 does not own:

- page-boundary detection/crop;
- perspective correction;
- OCR;
- semantic field inference;
- DocumentIR assembly;
- application intent.

Those remain later F02 work packages.

## Deterministic defaults

Competition V1 defaults:

- minimum short edge: `320 px`;
- maximum normalized long edge: `2048 px`;
- maximum decoded pixel budget before load: `24,000,000 pixels`;
- normalized output: `PNG`;
- resize filter: Pillow `LANCZOS`;
- transparency: flattened onto white;
- original and normalized identities remain separate.

These are product defaults, not universal truths. They may be changed later only by benchmark evidence.

## Contracts

`NormalizationPolicy` defines the bounded decode/normalization envelope.

`NormalizedImage` preserves:

- accepted source metadata;
- original dimensions;
- normalized dimensions;
- EXIF orientation observation;
- whether orientation was applied;
- whether resize occurred;
- normalized media type;
- normalized SHA-256;
- normalized bytes;
- ordered normalization operations.

Decode/normalization failures use `ImageNormalizationError`; W01 admission failures remain `InputGateError` so failure-layer ownership stays observable.

## Dependency decision

W02 uses Pillow through the declared project dependency:

`Pillow>=10.0`

Rationale:

- mature PNG/JPEG decode;
- EXIF orientation support;
- deterministic bounded resize;
- small implementation surface compared with introducing OpenCV before measured need.

OpenCV remains available as a later evidence-driven choice for page-boundary/perspective operations if W03/W04 benchmarks justify it.

## Safety invariant

Pixel-count policy is checked from decoded header dimensions before pixel buffer load. The system must not load an arbitrarily large decoded image and only then discover that it exceeded the configured safety envelope.

## Acceptance suite

`tests/test_image_normalization.py` covers:

1. valid PNG decode and canonical PNG output;
2. bounded long-edge resize with aspect ratio preserved;
3. short-edge rejection with `IMAGE_TOO_SMALL`;
4. EXIF orientation application;
5. transparent PNG flatten-to-white behavior;
6. pre-resize pixel-safety rejection;
7. signature-valid but undecodable PNG rejection;
8. deterministic normalized bytes/SHA for identical input.

W01 regression remains mandatory:

`tests/test_input_gate.py` — 9 tests.

## Closure evidence

- dependency bootstrap: `PASS` via `python -m pip install -e .`;
- resolved Pillow version in the active local Python environment: `12.2.0`;
- W02 normalization acceptance: `8/8 PASS` via `python -m unittest tests.test_image_normalization -v`;
- W01 input-gate regression: `9/9 PASS` via `python -m unittest tests.test_input_gate -v`;
- source and test compilation: `PASS` via `python -m compileall -q src tests`;
- canonical normalization behavior verified for EXIF orientation, bounded resize, pre-load pixel safety, transparent-PNG flattening, corrupt-image rejection, minimum-resolution rejection and deterministic normalized identity;
- BORG Shell19 Python remains dependency-isolated from the user's active PowerShell Python and therefore is not treated as authoritative runtime acceptance for this package; local acceptance used the environment where the declared editable package dependency resolves successfully.

## Closure gate

W02 may close only when all are true:

- Pillow dependency resolves from declared project metadata;
- W02 normalization tests PASS;
- W01 input-gate regression PASS;
- source compile PASS;
- Git diff contains only intended W02 changes;
- closure evidence is committed.

All closure gates are satisfied; F02-W02 is `CLOSED / PASS`.
