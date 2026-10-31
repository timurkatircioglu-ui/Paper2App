# F02-W05 — Observation Fusion & DocumentIR Assembly

**Status:** CLOSED / PASS
**Project:** Paper2App
**Phase:** F02 — Input Understanding / Paper Understanding Engine

## Goal

Fuse provider-neutral vision and OCR observations into one DocumentIR representation without silently overwriting provider disagreement or introducing application/runtime implementation decisions.

## Implemented surface

- `src/paper2app/understanding/document_ir.py`
- `src/paper2app/understanding/fusion.py`
- public exports through `src/paper2app/understanding/__init__.py`
- acceptance tests in `tests/test_document_ir_fusion.py`

## Canonical assembly boundary

`normalized image + VisionProviderResult + optional OCRProviderResult -> DocumentIR`

W05 assembly is deterministic. It is not the final validation authority; exhaustive reference/evidence/schema validation remains F02-W06 responsibility.

## DocumentIR representation

The runtime contract now represents:

- source identity and normalization provenance;
- document descriptor with `unknown` as a legal default;
- page metadata;
- regions and visual elements;
- provider-specific text evidence;
- bounded field candidates;
- deterministic spatial relations;
- explicit uncertainties;
- canonical schema/version identifiers.

The representation contains document evidence and bounded document semantics only. SQL, React, CRUD, API route, storage-engine, CSS, workflow-code and generated-source decisions remain forbidden.

## Fusion laws

1. Vision observations remain the structural baseline.
2. OCR is optional and remains an exact-text aid.
3. Matching OCR and vision text are retained as separate evidence records.
4. Provider text disagreement is never silently overwritten.
5. Case/whitespace/punctuation-only text variation does not create a conflict warning; raw evidence is still preserved.
6. Material matched-text disagreement produces `TEXT_CONFLICT` uncertainty.
7. Unmatched OCR text becomes a standalone text element instead of being discarded.
8. Region containment produces deterministic `contains` relations.
9. Field candidates are created only from bounded structural value-area/notes/approval inferences.
10. Visual kind constrains semantic value hints; it does not create AppSpec/database types.
11. `FIELD_LABEL` inference alone never becomes a value field.
12. Competition V1 assembly fails closed when Vision/OCR page counts disagree.

## Bounded semantic mapping

Current deterministic candidate hints include:

- checkbox -> `boolean`;
- radio -> `choice`;
- signature line -> `signature`;
- notes area -> `multiline_text`;
- input box / blank line / handwriting area -> `free_text` where structurally appropriate;
- unresolved cases -> `unknown`.

These are document-semantic hints, not runtime field implementations.

## Dependency boundary

Fusion does not import Pillow or the W02 decoder implementation at runtime. It consumes a structural normalized-image boundary compatible with W02 `NormalizedImage`. This keeps W05 provider/document reasoning testable independently from decoder dependencies while preserving production compatibility.

## Acceptance evidence

- W05 fusion/DocumentIR suite: **13/13 PASS** via `python -m unittest tests.test_document_ir_fusion`;
- W04 provider-port regression: **21/21 PASS** via `python -m unittest tests.test_provider_ports`;
- W03 visual-observation regression: **15/15 PASS** via `python -m unittest tests.test_visual_observation_contract`;
- understanding source compilation: **PASS** via `python -m compileall src/paper2app/understanding`;
- initial acceptance exposed a punctuation-only false `TEXT_CONFLICT`; minimal patch made conflict comparison punctuation-insensitive while preserving raw provider evidence and true semantic disagreement detection.

## Deferred to F02-W06

W06 owns the final deterministic DocumentIR validator and golden-set gate, including exhaustive checks for:

- global ID uniqueness;
- page/reference resolution;
- relation endpoint resolution;
- evidence-reference resolution;
- confidence and geometry invariants across the assembled graph;
- known schema/version enforcement at the release boundary;
- explicit invalid-document verdicts;
- golden-sample receipts.

## Closure decision

F02-W05 is `CLOSED / PASS`.

The next authorized package is **F02-W06 — Deterministic DocumentIR Validation & Golden Set**.
