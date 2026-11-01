# Paper2App — F04-W02 Authoritative Record Contract & Deterministic Validation

**Status:** CLOSED / PASS

## Purpose

F04-W02 establishes the authoritative backend record-value boundary for registered Paper2App applications. Record payloads are accepted only against an immutable `RegisteredAppSpec` that has already passed the F04-W01 manifest/AppSpec gate.

Canonical runtime path at this stage:

`RegisteredAppSpec + entity_id + user payload -> deterministic record validation -> ValidatedRecordPayload`

Persistence, HTTP and UI remain outside W02.

## Production implementation

Created:

- `src/paper2app/runtime/record_validation.py`

Updated:

- `src/paper2app/runtime/registry.py` with `RECORD_VALIDATION_FAILED`.

Public W02 contracts include:

- `RecordValidationIssueCode`
- `RecordValidationIssue`
- `RecordValidationReport`
- `ValidatedRecordPayload`
- `RecordValidationError`
- `validate_record_payload(...)`
- `require_valid_record_payload(...)`

## Boundary decision

The record validator consumes `RegisteredAppSpec`, not a raw `AppSpec`.

This preserves the runtime trust boundary established in W01: a record cannot be validated or later persisted against a specification that has not already passed deterministic AppSpec validation and concrete runtime-manifest compatibility.

`ValidatedRecordPayload` retains:

- `registration_id`;
- `app_id`;
- `entity_id`;
- normalized ordered field values.

This gives F04-W03 the registered-spec provenance required for persistence without inventing a second identity layer.

## Deterministic field behavior

W02 supports the field vocabulary already declared by the Competition V1 runtime manifest.

Rules:

- undeclared payload keys are rejected;
- unknown entities are rejected;
- `integer` rejects booleans and non-integers;
- `decimal` accepts finite integers/floats and rejects booleans/non-finite floats;
- `boolean` is strict boolean;
- string-like values remain user-provided strings and are not silently trimmed or rewritten;
- `date`, `time`, and `datetime` require valid ISO strings and are canonicalized with the Python standard-library ISO representation;
- `enum` must be one declared option;
- `multi_enum` accepts JSON-style lists or tuples of strings, normalizes to a tuple, rejects duplicates, and rejects undeclared options.

Input mapping order never controls normalized output order. Successful values follow AppSpec entity-field order.

## Defaults and missing values

A default is applied only when `AppField.default_value is not None` and the field was omitted from the payload.

This is intentionally conservative because AppSpec V0.1 currently uses `None` both as the constructor default and as the logical null value; it does not encode a separate `default_is_set` bit. W02 therefore does not claim support for an explicit null default distinct from “no default”.

Optional fields that are absent and have no non-null default remain absent.

Optional fields may explicitly carry `None`; non-required validation rules skip null values.

## Validation rule execution

The backend record validator is authoritative for the bounded AppSpec validation vocabulary:

- `required`
- `min`
- `max`
- `min_length`
- `max_length`
- `allowed_values`
- `format`

`required` rejects missing, null, blank-string, and empty multi-choice values.

`allowed_values` may be narrower than the field's declared enum options and is enforced independently.

Bounded format semantics for Competition V1 are deterministic:

- `email`: non-whitespace local/domain parts with one `@` boundary and a dot in the domain side;
- `phone`: only digits plus common phone punctuation, with at least seven digits;
- `identifier`: ASCII alphanumeric first character followed by ASCII alphanumeric, `.`, `_`, `:`, or `-`.

These are competition-runtime contracts, not claims of universal international validation.

## Workflow-state boundary

W02 does not accept, derive or mutate workflow state. The payload contains only declared entity fields. Any undeclared workflow-state key is rejected like any other undeclared field.

Bounded workflow transition/state handling remains owned by F04-W07.

## Stable failure contract

Record rejection uses:

`RuntimeFailureCode.RECORD_VALIDATION_FAILED`

Structured issue codes include:

- `ENTITY_NOT_FOUND`
- `UNKNOWN_FIELD`
- `REQUIRED_FIELD_MISSING`
- `INVALID_FIELD_TYPE`
- `INVALID_CHOICE`
- `DUPLICATE_CHOICE`
- `VALIDATION_RULE_FAILED`

The strict `require_valid_record_payload(...)` API raises `RecordValidationError` and retains the structured report.

## Acceptance evidence

Fresh targeted acceptance:

- `tests.test_record_validation` -> **18/18 PASS**

Fresh regressions:

- `tests.test_runtime_manifest_registry` -> **14/14 PASS**
- `tests.test_app_spec_validation` -> **23/23 PASS**
- `tests.test_f03_w06_generalization_benchmark` -> **4/4 PASS**
- `python -m compileall src/paper2app/runtime` -> **PASS**
- `python -m compileall tests` -> **PASS**

The first W02 target run failed during fixture registration because the fixture contained `multi_enum` and `signature` fields without declaring the already-required `MULTI_CHOICE` and `SIGNATURE_CAPTURE` capabilities. The F03/W01 gate was correct; the fixture was corrected rather than weakening production validation.

## Generic-runtime contamination gate

A scoped runtime-source search found no `equipment` or `safety` demo markers.

W02 adds no:

- SQLite persistence;
- FastAPI/Pydantic surface;
- frontend code;
- demo-specific field labels or branches;
- workflow state engine.

## Verdict

**F04-W02 CLOSED / PASS.**

The runtime now has an authoritative deterministic record boundary suitable for F04-W03 persistence. Invalid data cannot reach persistence through the intended runtime path; validated record output carries immutable registered-spec provenance.
