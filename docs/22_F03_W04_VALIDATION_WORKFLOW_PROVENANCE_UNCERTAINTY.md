# F03-W04 — Validation, Workflow, Provenance & Uncertainty Synthesis

**Status:** CLOSED / PASS

## Goal

Extend the cumulative F03 synthesis state with only evidence-supported deterministic validations and bounded workflow semantics while preserving provenance and uncertainty explicitly.

Canonical boundary:

`validated DocumentIR + W03 application surface -> validations/workflows/provenance/uncertainty -> cumulative AppSpec synthesis state`

W04 does not perform final AppSpec graph validation or runtime capability compatibility. Those remain F03-W05 responsibilities.

## Production implementation

Added:

- `src/paper2app/specification/behavior_synthesis.py`
- public exports from `src/paper2app/specification/__init__.py`

Primary API:

- `ValidationWorkflowSynthesisResult`
- `synthesize_validations_workflows(document_ir, surface)`

Authoritative synthesis input still requires a deterministically valid DocumentIR.

## Validation synthesis policy

W04 deliberately does not infer constraints merely because they are common application defaults.

Not synthesized without explicit evidence:

- `required`
- `min`
- `max`
- `min_length`
- `max_length`

Current bounded validation synthesis:

1. Evidence-backed `enum` / `multi_enum` options produce `ALLOWED_VALUES`.
2. An evidence-backed logical `email` field produces `FORMAT = email`.

Validation provenance is `DOCUMENT_DERIVED` and retains the supporting field/option evidence references.

## Workflow synthesis policy

Workflow is not inferred from the presence of a checkbox, boolean field, status-like label, or demo knowledge.

A workflow is synthesized only when all of the following are true:

1. the synthesized field is an evidence-backed `enum`;
2. its options resolve to DocumentIR option elements through `OPTION_OF` evidence;
3. explicit `FOLLOWS` relations exist between those option elements;
4. the observed graph is one deterministic linear chain covering all options.

If `FOLLOWS` evidence exists but is cyclic, branching, disconnected, or otherwise non-linear, W04 emits a critical uncertainty and no executable workflow.

Competition V1 permits at most one evidence-backed workflow per entity. Multiple valid workflow candidates become a critical uncertainty instead of an arbitrary choice.

When a workflow is emitted:

- the `AppWorkflow` is `DOCUMENT_DERIVED`;
- an explicit `change_state` action is added;
- `BASIC_WORKFLOW` capability is required;
- the action/capability exposure is `PRODUCT_POLICY` provenance.

## FOLLOWS directional clarification

During W04 implementation a contract gap was found: DocumentIR defined the `follows` relation vocabulary but did not define edge direction.

Canonical clarification was added to `docs/04_DOCUMENT_IR_V0.md`:

- for ordered workflow evidence, `source_id` is the predecessor;
- `target_id` is the successor.

This is a documentation-level semantic clarification; no F02 runtime representation or schema changed.

## Uncertainty translation

W04 preserves all upstream AppSpec synthesis uncertainties and additionally translates DocumentIR uncertainties into AppSpec uncertainties.

Policy:

- if a DocumentIR uncertainty evidence set intersects an emitted field's document-derived source references, the translated uncertainty is critical and targets that field;
- `UNKNOWN` DocumentIR uncertainty is fail-safe critical even when a specific field target cannot be resolved;
- otherwise the source uncertainty remains visible as a non-critical AppSpec warning;
- unresolved field synthesis uncertainty from W02 remains unchanged and can already be critical.

This keeps source ambiguity observable without silently converting it into executable certainty.

## Provenance law

W04 preserves the distinction between:

- `DOCUMENT_DERIVED`: validation values, workflow states/order, translated document evidence;
- `PRODUCT_POLICY`: exposing an evidence-backed workflow as `change_state` and requiring the matching runtime capability;
- `USER_CONFIRMED`: reserved for later explicit user confirmation flows and never fabricated by W04.

No source code, SQL, shell commands, arbitrary scripts, or executable formulas are emitted.

## Acceptance evidence

Fresh bounded acceptance:

- F03-W04 validation/workflow synthesis: **13/13 PASS**
- F03-W03 surface-policy regression: **12/12 PASS**
- F03-W02 entity/field synthesis regression: **14/14 PASS**
- F03-W01 AppSpec contract regression: **18/18 PASS**
- F02 DocumentIR validator regression: **20/20 PASS**
- `python -m compileall src/paper2app/specification`: **PASS**

Acceptance covers:

- no invented validation/workflow on the Equipment Checkout golden fixture;
- cumulative W03 surface preservation;
- Safety/Inspection unresolved severity remains explicit;
- invalid DocumentIR fails closed;
- evidence-backed enum allowed-values validation;
- evidence-backed email format validation;
- explicit `FOLLOWS` chain -> deterministic linear workflow;
- workflow -> explicit `change_state` action + `BASIC_WORKFLOW` capability;
- ambiguous workflow graph blocks workflow execution;
- field-affecting document uncertainty becomes critical;
- unclassified document uncertainty is fail-safe critical;
- repeated synthesis is structurally deterministic;
- production behavior synthesis contains no demo-specific branch markers.

## Closure verdict

F03-W04 is **CLOSED / PASS**.

Next authorized package:

**F03-W05 — Deterministic AppSpec Validation & Runtime Capability Gate**
