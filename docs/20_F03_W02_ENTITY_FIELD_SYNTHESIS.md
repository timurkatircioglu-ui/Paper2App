# F03-W02 — Deterministic Entity & Field Synthesis

**Status:** CLOSED / PASS
**Phase:** F03 — App Specification Synthesis

## Goal

Convert validated DocumentIR field candidates into bounded technology-independent AppEntity/AppField structures without inventing unsupported semantics or implementation details.

## Implemented surface

Production implementation:

- `src/paper2app/specification/synthesis.py`
- public exports from `src/paper2app/specification/__init__.py`

Primary API:

- `synthesize_entity_fields(document_ir)`
- `EntityFieldSynthesisResult`
- `FieldSynthesisDecision`

The result carries:

- synthesized entities/fields;
- document-derived provenance;
- synthesis uncertainties;
- per-candidate decision receipts including confidence and source references.

Views, actions, persistence, validations and workflows are intentionally not synthesized in W02.

## Authoritative input gate

`synthesize_entity_fields()` begins with `require_valid_document_ir()`.

Therefore invalid DocumentIR cannot enter authoritative F03 entity/field synthesis. `PASS_WITH_WARNINGS` DocumentIR remains legal input because the graph is valid while uncertainties remain explicit.

## Bounded logical type mapping

Document semantic hints map conservatively:

- `free_text` -> `string`
- `person_name` -> `string`
- `number` -> `decimal`
- `date` -> `date`
- `time` -> `time`
- `boolean` -> `boolean`
- `multiline_text` -> `multiline_string`
- `signature` -> `signature`
- `email` -> `email`
- `phone` -> `phone`
- `identifier` -> `identifier`

Strong visual fallback is limited to visually distinctive controls:

- checkbox -> boolean
- signature line -> signature
- handwriting area -> multiline string

A generic input box with an unknown semantic hint is not silently coerced to string.

## Choice / enum rule

`choice` becomes an executable `enum` only when DocumentIR contains evidence-backed option elements connected through `OPTION_OF` relations and those option elements carry observed text.

If options are not present, the field candidate is not emitted as AppField. Instead W02 emits a critical synthesis uncertainty.

This prevents fixture/product knowledge such as expected severity labels from being injected as if observed in the paper.

## Labels and stable identifiers

Display labels are selected in bounded priority order:

1. `LABELS` relation text evidence;
2. text evidence referenced by the field candidate;
3. generic candidate identifier fallback;
4. generic target-element identifier fallback.

Field IDs are deterministic normalized slugs. Collisions are resolved deterministically with `_2`, `_3`, ... suffixes.

## Entity policy

Competition V1 currently synthesizes one primary record entity per paper workflow.

When `document_type_hint` is known, entity identity is document-derived. When it is `unknown`, W02 uses a generic `document_record` identity as an explicit product-policy fallback and records a non-critical uncertainty.

This is deliberately not a multi-entity inference engine; complexity must earn its place in a later evidence-backed package.

## Provenance and confidence

Each emitted field receives `DOCUMENT_DERIVED` provenance with:

- source field-candidate ID;
- target element ID;
- evidence references;
- source confidence in the bounded provenance note.

`FieldSynthesisDecision` also preserves confidence directly for every emitted or blocked candidate.

## Golden behavior

### Equipment Checkout

The W06 golden DocumentIR produces one `equipment_checkout_record` entity with:

- `name` -> string
- `item` -> string
- `returned` -> boolean
- `signature` -> signature

### Safety / Inspection

The W06 golden DocumentIR produces the resolvable fields from the same synthesis code path.

`severity` is intentionally not executable in the W06 golden fixture because the DocumentIR has a `choice` semantic hint but no evidence-backed `OPTION_OF` options. W02 emits a critical uncertainty instead of inventing `Low / Medium / High`.

A dedicated acceptance case enriches the same candidate with observed `Low` and `High` option elements and `OPTION_OF` relations; synthesis then emits a valid enum with exactly those observed options.

## Acceptance evidence

Fresh W02 suite:

- `tests.test_entity_field_synthesis` -> 14/14 PASS

Regression:

- `tests.test_app_spec_contract` -> 18/18 PASS
- `tests.test_document_ir_validation` -> 20/20 PASS

Static gate:

- `python -m compileall src/paper2app/specification` -> PASS

Additional acceptance coverage includes:

- invalid DocumentIR fail-closed;
- evidence-backed label selection;
- bounded semantic type mapping;
- enum option evidence requirement;
- strong visual fallback only;
- unknown input-box type remains uncertain;
- unknown document type product-policy fallback;
- deterministic slug collision resolution;
- PASS_WITH_WARNINGS DocumentIR accepted as structurally valid input;
- no view/action/persistence synthesis in W02;
- no Equipment/Safety demo-specific branch names in production synthesis source.

## Closure verdict

F03-W02 is **CLOSED / PASS**.

The next package is **F03-W03 — Views, Actions & Persistence Policy**.
