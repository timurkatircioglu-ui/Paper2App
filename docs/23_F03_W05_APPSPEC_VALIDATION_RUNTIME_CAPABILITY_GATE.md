# F03-W05 — Deterministic AppSpec Validation & Runtime Capability Gate

**Status:** CLOSED / PASS

## Goal

Create the authoritative deterministic gate between synthesized AppSpec candidates and any runtime execution surface.

Canonical flow:

`validated DocumentIR -> W02 entity/field synthesis -> W03 surface policy -> W04 validation/workflow synthesis -> AppSpec candidate -> deterministic AppSpec validation -> runtime capability compatibility -> validated AppSpec`

Candidate assembly and executable admission are deliberately separate. An AppSpec may be representable while still being non-executable.

## Production implementation

`src/paper2app/specification/validation.py`

Public surface:

- `AppSpecValidationStatus`: `PASS`, `PASS_WITH_WARNINGS`, `FAIL`
- `AppSpecValidationSeverity`: `WARNING`, `ERROR`
- `AppSpecValidationIssueCode`
- `AppSpecValidationIssue`
- `AppSpecValidationReport`
- `AppSpecValidationError`
- `RuntimeCapabilityProfile`
- `COMPETITION_V1_RUNTIME_PROFILE`
- `validate_app_spec(...)`
- `require_valid_app_spec(...)`
- `assemble_app_spec_candidate(...)`
- `synthesize_validated_app_spec(...)`

## Deterministic invariants

The validator checks:

1. canonical AppSpec schema/version identity;
2. duplicate entity/field/view/action/workflow/validation/provenance/uncertainty IDs;
3. primary entity resolution;
4. field default-value compatibility with the logical field type and enum options;
5. view entity/field references and entity-local field scope;
6. action entity/workflow references;
7. `change_state` actions require a known workflow owned by the same entity;
8. validation entity/field references and validation-rule compatibility;
9. workflow state/condition/transition uniqueness and reference resolution;
10. workflow expected-value compatibility;
11. workflow reachability from the initial state;
12. capabilities required by explicit actions, persistence, field types and workflows;
13. declared required capabilities must be present in the AppSpec;
14. required capabilities must be supported by the selected runtime profile;
15. provenance targets must resolve to an AppSpec target surface;
16. critical uncertainty blocks executable status;
17. non-critical uncertainty remains visible as a warning.

## Validation compatibility policy

Bounded rule compatibility is deterministic:

- `required`: no executable payload;
- `min` / `max`: integer or decimal fields with numeric bounds;
- `min_length` / `max_length`: bounded textual field families with non-negative integer limits;
- `allowed_values`: enum/multi-enum only, with values already present in field options;
- `format`: currently bounded to `email`, `phone`, and `identifier` for the corresponding field types.

This gate validates proposed rules. It does not invent missing rules.

## Runtime capability gate

Capabilities are computed from the actual executable AppSpec surface:

- explicit record actions -> matching record capabilities;
- persistence requirement -> `persistence`;
- `multi_enum` -> `multi_choice`;
- signature fields -> `signature_capture`;
- workflows / change-state -> `basic_workflow`.

The AppSpec must declare every required capability. The selected runtime profile must support every required capability before execution is admitted.

`COMPETITION_V1_RUNTIME_PROFILE` is the bounded target capability contract for the planned Competition V1 runtime. W05 validates compatibility with that contract; it does not claim the later runtime implementation has already been built or acceptance-tested.

Unused declared capabilities are warnings rather than execution failures.

## Authoritative F03 egress

`assemble_app_spec_candidate(document_ir)` composes the W02-W04 production stages and creates the technology-independent top-level `AppIdentity`.

`synthesize_validated_app_spec(document_ir, runtime_profile)` then applies `require_valid_app_spec(...)` and returns only a non-FAIL AppSpec.

Therefore:

`candidate synthesis != executable admission`

and:

`critical uncertainty / invalid references / invalid workflow / missing capability / unsupported required capability -> fail closed`

## Golden behavior observed in W05

Equipment Checkout traverses the complete W02-W05 synthesis path and is admitted as a clean `PASS` AppSpec under the Competition V1 profile.

The current Safety/Inspection golden DocumentIR remains intentionally non-executable because the `severity` choice candidate has no evidence-backed options. W02 correctly preserves that as critical synthesis uncertainty, and W05 therefore rejects the candidate. W06 will use evidence-backed option relations for the second generalization proof; W05 does not weaken the gate merely to make the fixture pass.

## Acceptance evidence

Fresh acceptance run:

- `tests.test_app_spec_validation` — **23/23 PASS**
- `tests.test_validation_workflow_synthesis` — **13/13 PASS**
- `tests.test_view_action_persistence_policy` — **12/12 PASS**
- `tests.test_entity_field_synthesis` — **14/14 PASS**
- `tests.test_app_spec_contract` — **18/18 PASS**
- `tests.test_document_ir_validation` — **20/20 PASS**
- `python -m compileall src/paper2app/specification` — **PASS**

The W05 suite includes positive and adversarial cases for schema/version drift, duplicate IDs, broken references, invalid defaults/rules, unreachable workflow states, missing capabilities, unsupported runtime profiles, provenance drift, critical/non-critical uncertainty, deterministic capability receipts, and authoritative fail-closed egress.

## Closure decision

F03-W05 is **CLOSED / PASS**.

Next: **F03-W06 — Generalization Benchmark & F03 Closure**.
