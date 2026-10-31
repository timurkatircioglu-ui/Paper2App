# F02 — Input Understanding / Paper Understanding Engine

**Status:** ACTIVE
**Project:** Paper2App
**Phase:** F02
**North Star:** VALID DOCUMENT IR RATE

## Goal

Convert a supported paper/form image into a stable, validated DocumentIR while keeping probabilistic document understanding separate from deterministic execution.

Canonical flow:

`source image -> input gate -> deterministic decode/normalization -> visual/text observations -> fusion -> semantic candidates -> DocumentIR assembly -> deterministic validation`

## Work packages

### F02-W01 — Input Gate & Source Contract

**Status:** CLOSED / PASS

Scope:

- establish the Python source/test package baseline;
- accept only competition-V1 source image media (`image/png`, `image/jpeg`);
- detect media from content bytes rather than trusting filename or caller MIME metadata;
- preserve deterministic SHA-256 source identity;
- preserve bounded capture-kind metadata;
- reduce supplied filenames to a safe basename;
- reject unsupported, obviously corrupt, undersized, or over-policy inputs explicitly;
- keep pixel decoding, resolution quality and normalization out of W01.

Implementation:

- `pyproject.toml`
- `src/paper2app/input/contracts.py`
- `src/paper2app/input/gate.py`
- `src/paper2app/input/__init__.py`
- `tests/test_input_gate.py`

Acceptance evidence:

- `python_unittest_pattern` selector `tests.test_input_gate`: **9 tests PASS**;
- `python_compileall src`: **PASS**;
- PNG/JPEG content-sniffing: PASS;
- filename-extension disagreement does not override bytes: PASS;
- deterministic source SHA/source_id: PASS;
- unsupported signature rejection: PASS;
- corrupt PNG/JPEG rejection: PASS;
- configured input byte bound: PASS;
- safe basename handling: PASS.

Deferred beyond W01:

- actual pixel decode;
- exact image dimensions from decoded image;
- minimum usable resolution;
- EXIF orientation;
- crop/page-boundary handling;
- perspective correction;
- resize/normalization output.

### F02-W02 — Deterministic Image Decode & Normalization

**Status:** CLOSED / PASS

Target:

- decode accepted PNG/JPEG bytes;
- establish decoded width/height/channels;
- reject undecodable or unusable-resolution images;
- preserve original and normalized representations distinctly;
- apply bounded orientation/resize normalization;
- add crop/perspective correction only where deterministic evidence justifies it;
- emit normalization metadata required by DocumentIR source provenance.

Closure evidence: `docs/12_F02_W02_IMAGE_NORMALIZATION.md`.

### F02-W03 — Visual Structure Observation Contract

**Status:** CLOSED / PASS

Target:

- bounded visual region/element observation models;
- normalized geometry;
- observation vs inference separation;
- text/label, input-box, checkbox/radio, signature/notes and section candidates;
- `unknown` as a legal observation.

Closure evidence: `docs/13_F02_W03_VISUAL_STRUCTURE_OBSERVATION_CONTRACT.md`.

### F02-W04 — Vision/OCR Provider Ports & Acceptance

**Status:** CLOSED / PASS

Target:

- replaceable `VisionProvider` and `OCRProvider` contracts;
- versioned provider observations;
- bounded failure/retry semantics;
- OCR remains exact-text aid, not semantic authority;
- provider/prompt selection benchmarked rather than hard-coded by popularity.

Closure evidence: `docs/14_F02_W04_VISION_OCR_PROVIDER_PORTS.md`.

### F02-W05 — Observation Fusion & DocumentIR Assembly

**Status:** CLOSED / PASS

Target:

- preserve provider disagreement;
- combine geometry, text and visual observations;
- derive bounded semantic candidates;
- construct DocumentIR without application/runtime decisions;
- preserve evidence/provenance for important inferences.

Closure evidence: `docs/15_F02_W05_OBSERVATION_FUSION_DOCUMENT_IR_ASSEMBLY.md`.

### F02-W06 — Deterministic DocumentIR Validation & Golden Set

**Status:** CLOSED / PASS

Target:

- deterministic schema/reference/geometry validation;
- explicit uncertainty handling;
- small manually verified golden sample set;
- failure taxonomy and benchmark receipts;
- only valid DocumentIR leaves the F02 pipeline.

Closure evidence: `docs/16_F02_W06_DOCUMENT_IR_VALIDATION_GOLDEN_SET.md`.

### F02-W07 — Generalization Benchmark & F02 Closure

**Status:** READY TO START

Target:

- Equipment Checkout and Safety/Inspection Report both pass through the same input-understanding contracts;
- stable validated DocumentIR for both materially different workflows;
- no per-demo hard-coded pipeline branch;
- record valid DocumentIR rate, latency and failure evidence;
- close F02 only when roadmap exit is evidenced.

## F02 invariants

1. Vision observes documents; it does not design applications.
2. OCR extracts text; it does not infer business logic.
3. Original and normalized representations remain distinguishable.
4. Raw observations are not silently overwritten.
5. Geometry is first-class evidence.
6. Provider disagreement remains observable.
7. `unknown` is preferable to invented certainty.
8. Providers remain replaceable.
9. Only validated DocumentIR leaves F02.
10. Sensitive source content is not unnecessarily retained or logged.

## Current phase state

F02 implementation is active and W01–W06 are closed with evidence.

**Completed:** F02-W01 through F02-W06.

**Next:** F02-W07 — Generalization Benchmark & F02 Closure.
