# F02-W06 — Deterministic DocumentIR Validation & Golden Set

**Status:** CLOSED / PASS
**Project:** Paper2App
**Phase:** F02 — Input Understanding / Paper Understanding Engine

## Goal

Establish the deterministic authority that decides whether an assembled DocumentIR is structurally valid, preserves explicit uncertainty without hiding it, and prevents invalid graphs from leaving the F02 understanding pipeline.

## Validation boundary

W05 assembly and W06 validation remain separate responsibilities:

- `assemble_document_ir(...)` constructs DocumentIR from provider-neutral evidence;
- `validate_document_ir(...)` evaluates cross-object graph invariants;
- `require_valid_document_ir(...)` fails closed on invalid graphs;
- `assemble_validated_document_ir(...)` is the authoritative F02 egress and performs assembly followed by deterministic validation before release.

No AI/provider output can bypass this deterministic egress contract.

## Validation statuses

The validator emits exactly three states:

- `PASS` — structurally valid and no explicit document uncertainty;
- `PASS_WITH_WARNINGS` — structurally valid while preserving explicit uncertainty;
- `FAIL` — one or more deterministic invariants are broken.

Explicit uncertainty is therefore not silently erased and is not automatically treated as structural invalidity.

## Deterministic invariants

W06 validates:

- known DocumentIR schema/version;
- SHA-256 source and normalized identities;
- non-empty, unique and contiguous page indices from zero;
- single-page normalized dimensions matching source provenance;
- global uniqueness across region, element, text-evidence, field-candidate, relation and uncertainty IDs;
- region/element page references resolve;
- field candidates target real elements;
- relation endpoints resolve to structural region/element observations;
- evidence references resolve only to observable region/element/text evidence;
- duplicate references inside one evidence list are rejected;
- uncertainty evidence must resolve even though the uncertainty itself remains a warning.

Constructor-level type checks remain useful but do not replace graph-level validation.

## Failure taxonomy

Deterministic validation issue codes:

- `DOCUMENT_TYPE_INVALID`
- `SCHEMA_INVALID`
- `SCHEMA_VERSION_INVALID`
- `SOURCE_HASH_INVALID`
- `PAGE_SET_INVALID`
- `SOURCE_PAGE_MISMATCH`
- `DUPLICATE_ID`
- `PAGE_REFERENCE_INVALID`
- `FIELD_TARGET_INVALID`
- `RELATION_ENDPOINT_INVALID`
- `EVIDENCE_REFERENCE_INVALID`
- `DUPLICATE_REFERENCE`
- `DOCUMENT_UNCERTAINTY` (warning)

Each issue includes severity, stable code, graph path and bounded message.

## Golden set

The manually verified golden set lives in:

`tests/golden/document_ir_samples.py`

### Golden A — Equipment Checkout

Materially represents the Equipment Checkout workflow with:

- form region;
- name text/entry evidence;
- item entry;
- returned checkbox;
- signature area;
- bounded field candidates;
- containment relations.

Expected validation status: `PASS`.

### Golden B — Safety / Inspection Report

Materially represents a different workflow with:

- inspector entry;
- location entry;
- severity choice control;
- notes/handwriting area;
- approval signature;
- bounded field candidates;
- containment relations;
- one explicit `FIELD_RELATION_AMBIGUOUS` uncertainty on severity grouping.

Expected validation status: `PASS_WITH_WARNINGS`.

This proves that two materially different document types share one DocumentIR contract and that explicit uncertainty remains legal and observable.

## Acceptance evidence

- W06 validator/golden suite: `20/20 PASS` via `python -m unittest tests.test_document_ir_validation`;
- W05 fusion regression: `13/13 PASS` via `python -m unittest tests.test_document_ir_fusion`;
- W04 provider-port regression: `21/21 PASS` via `python -m unittest tests.test_provider_ports`;
- W03 observation-contract regression: `15/15 PASS` via `python -m unittest tests.test_visual_observation_contract`;
- understanding source compile: `PASS` via `python -m compileall src/paper2app/understanding`.

The W06 suite covers valid golden samples, warning-preserving uncertainty, malformed source hashes, broken page sets, source/page mismatch, duplicate global IDs, unresolved page references, broken field targets, broken relation endpoints, unresolved evidence, duplicate references, invalid uncertainty evidence, unknown schema mutation, deterministic report stability and fail-closed authoritative egress.

## Architecture consequences

1. Assembly is not validation.
2. Explicit uncertainty is a first-class warning, not hidden state.
3. Evidence must point to observable support, not arbitrary inferred graph objects.
4. Invalid graph references cannot leave F02 through the authoritative egress.
5. Golden samples are reusable by F02-W07 generalization benchmarking.
6. No AppSpec/runtime/storage implementation concept is introduced by this package.

## Closure gate

All W06 closure gates are satisfied. F02-W06 is `CLOSED / PASS`.
