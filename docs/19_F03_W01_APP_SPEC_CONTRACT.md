# F03-W01 — AppSpec Contract & Bounded Vocabulary

**Status:** CLOSED / PASS
**Project:** Paper2App

## Goal

Implement the canonical AppSpec 0.1 contract as a technology-independent, immutable and bounded representation of application behavior. W01 defines representation only; graph/reference validation is intentionally deferred to F03-W05.

## Implemented contract

Production module:

`src/paper2app/specification/app_spec.py`

Public package:

`src/paper2app/specification/__init__.py`

Top-level identity:

- schema: `paper2app.app_spec`
- schema version: `0.1`

Implemented structures:

- `AppIdentity`
- `AppField`
- `AppEntity`
- `AppView`
- `AppAction`
- `AppValidation`
- `WorkflowCondition`
- `WorkflowState`
- `WorkflowTransition`
- `AppWorkflow`
- `PersistenceRequirement`
- `ProvenanceRecord`
- `AppSpecUncertainty`
- `AppSpec`

## Bounded vocabularies

Field types:

`string`, `multiline_string`, `integer`, `decimal`, `boolean`, `date`, `time`, `datetime`, `enum`, `multi_enum`, `signature`, `email`, `phone`, `identifier`.

View kinds:

`form`, `record_list`, `record_detail`.

Actions:

`create_record`, `update_record`, `view_record`, `list_records`, `search_records`, `filter_records`, `change_state`.

Validation rule kinds:

`required`, `min`, `max`, `min_length`, `max_length`, `allowed_values`, `format`.

Workflow condition operators:

`equals`, `not_equals`, `is_set`.

Capabilities:

`record_create`, `record_update`, `record_view`, `record_list`, `record_search`, `record_filter`, `persistence`, `multi_choice`, `basic_workflow`, `signature_capture`.

Provenance classes:

`DOCUMENT_DERIVED`, `PRODUCT_POLICY`, `USER_CONFIRMED`.

## Safety / determinism properties

- contract objects are frozen dataclasses;
- tuple-based collections keep the representation immutable;
- arbitrary dict/list/code payloads are rejected where bounded values are expected;
- enum/multi-enum options are explicit and unique;
- workflow representation is a bounded state-machine shape, not executable code;
- persistence expresses behavioral requirements only, not a database technology;
- uncertainty may be marked critical without embedding executable behavior;
- implementation-specific fields such as SQL, React, FastAPI, CSS, shell, script, code, paths, credentials and secrets are absent from the contract surface.

## Deliberate validator boundary

W01 does not resolve cross-object references such as:

- `primary_entity_id`;
- view entity/field references;
- action entity/workflow references;
- validation field references;
- workflow state/condition references;
- provenance target/source references;
- uncertainty targets;
- capability/runtime compatibility.

Those invariants belong to F03-W05. This keeps representation construction separate from deterministic executable-status authority.

## Acceptance evidence

`python -m unittest tests.test_app_spec_contract -v`

Result:

- 18 tests
- 18 PASS
- exit code 0

`python -m compileall src/paper2app/specification`

Result: PASS / exit code 0.

Fresh F02 regression:

- `tests.test_f02_generalization_benchmark` — 3/3 PASS
- `tests.test_document_ir_validation` — 20/20 PASS

No F02 production source was modified.

## Closure verdict

F03-W01 is **CLOSED / PASS**.

The repository now has one canonical, typed and technology-independent AppSpec representation suitable for deterministic synthesis work in F03-W02 onward.
