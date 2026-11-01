# F03-W06 — Generalization Benchmark & F03 Closure

Status: **CLOSED / PASS**

## Purpose

Close F03 only after two materially different validated DocumentIR inputs produce materially different **validated AppSpecs** through the same production synthesis and validation contracts, with stable structural output and no per-demo production branch.

This gate validates the F03 specification layer. It does **not** claim that a real vision model has solved paper understanding and it does **not** claim that the F04 runtime is implemented.

## Canonical path under test

```text
validated DocumentIR
  -> synthesize_entity_fields
  -> synthesize_views_actions_persistence
  -> synthesize_validations_workflows
  -> assemble_app_spec_candidate
  -> validate_app_spec / runtime capability gate
  -> synthesize_validated_app_spec
  -> validated AppSpec
```

Both benchmark cases use `synthesize_validated_app_spec(...)` and the same `COMPETITION_V1_RUNTIME_PROFILE`.

## Benchmark fixtures

### Equipment Checkout

Uses the existing clean F02 Equipment Checkout golden DocumentIR unchanged.

### Safety / Inspection

The original F02 Safety golden intentionally remains unresolved around severity grouping and continues to fail closed at the authoritative AppSpec egress. F03-W06 therefore uses a separate benchmark fixture derived from that golden and adds only observable evidence needed to resolve the ambiguity:

- text option elements: `Low`, `Medium`, `High`;
- `OPTION_OF` relations from each option to the existing severity control;
- explicit directional `FOLLOWS` evidence: `Low -> Medium -> High`;
- the previously unresolved severity relation uncertainty is absent only in this resolved benchmark fixture.

No production synthesis rule or demo-specific branch is added to make the case pass.

## Fresh benchmark receipt

The bounded in-memory closure benchmark ran each case 20 times:

```text
F03_W06_CASE equipment_checkout: runs=20 valid=20 mean_ms=0.570 p95_ms=0.943 fingerprint=b74bccf0ee1ea76c
F03_W06_CASE safety_inspection: runs=20 valid=20 mean_ms=0.636 p95_ms=1.161 fingerprint=f54a44f97c892130
F03_W06_BENCHMARK cases=2 runs=40 valid=40 valid_appspec_rate=1.000
```

The latency values are diagnostic receipts for this run only; F03 has no frozen performance SLA.

Results:

- 2 materially different cases;
- 40 total synthesis runs;
- 40 validated AppSpecs;
- validated AppSpec rate: **1.000**;
- one structural fingerprint per case across all 20 repetitions;
- fingerprints differ between the two cases.

## Material-difference proof

The same production path produces different application semantics:

- Equipment Checkout does not contain a `severity` field and emits no workflow;
- Safety / Inspection contains `severity` as an evidence-backed enum with `Low`, `Medium`, `High`;
- Safety emits an `ALLOWED_VALUES` validation for severity;
- Safety emits a three-state ordered workflow with two transitions;
- `BASIC_WORKFLOW` is required by Safety but not Equipment.

The difference therefore comes from DocumentIR evidence, not from application-name branching.

## Fail-closed preservation

The original unresolved Safety golden is still tested through `synthesize_validated_app_spec(...)` and still raises `AppSpecValidationError` with `FAIL` status.

This proves W06 did not weaken W02-W05 uncertainty policy merely to obtain a second passing demo.

## No demo-specific production branch

The W06 acceptance suite scans `src/paper2app/**/*.py` and rejects production occurrences of the benchmark demo identifiers:

- `equipment_checkout` / `equipment checkout`;
- `safety_inspection` / `safety inspection` / `safety / inspection`.

The scan passed. W06 production source diff is empty; W06 adds only benchmark fixtures/tests plus closure documentation/status changes.

## Fresh regression evidence

```text
F03-W06 generalization benchmark    4/4 PASS
F03-W05 AppSpec validation         23/23 PASS
F03-W04 behavior synthesis         13/13 PASS
F03-W03 surface policy             12/12 PASS
F03-W02 entity/field synthesis     14/14 PASS
F03-W01 AppSpec contract           18/18 PASS
F02 DocumentIR validator           20/20 PASS
specification compile                   PASS
tests compile                           PASS
```

## F03 exit verdict

F03 exit requirement is satisfied:

> a validated AppSpec exists independently of rendering/runtime implementation.

Additionally, two materially different DocumentIR shapes now produce two materially different, stable, runtime-capability-compatible validated AppSpecs through one production synthesis stack.

**F03 — App Specification Synthesis: CLOSED / PASS.**

Next phase: **F04 — Generic Runtime**.
