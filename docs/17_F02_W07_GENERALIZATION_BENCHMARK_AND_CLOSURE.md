# F02-W07 — Generalization Benchmark & F02 Closure

**Status:** CLOSED / PASS

## Purpose

Close F02 only if two materially different workflows pass through the same Paper2App understanding contracts and produce stable validated DocumentIR without demo-specific production branches.

## Benchmark scope

The W07 benchmark starts at the normalized-image/provider boundary and exercises the production contracts below:

`ProviderImage -> run_vision_provider + run_ocr_provider -> assemble_validated_document_ir -> validate_document_ir`

The benchmark corpus is fixture-backed and contains two materially different workflow shapes:

1. Equipment Checkout — free-text inputs, checkbox and signature structure.
2. Safety / Inspection — free-text inputs, radio choices, handwriting/notes area, checkbox and approval signature structure.

Both cases use the same provider ports, fusion implementation, DocumentIR representation and deterministic validator.

## Non-claim

This benchmark does **not** claim real-world vision-model accuracy on photographed paper. The provider observations are deterministic fixtures used to prove contract-level generalization, stability and branch independence.

Real provider/model/prompt quality must be benchmarked separately with representative real document images before demo/production acceptance. W07 does not silently convert fixture success into a claim of visual-understanding accuracy.

W02 real image decode/normalization acceptance remains covered by `docs/12_F02_W02_IMAGE_NORMALIZATION.md`.

## Canonical benchmark run

Command surface: Shell19 bounded `python_unittest_pattern`.

Benchmark test:

`tests.test_f02_generalization_benchmark`

Observed receipt:

```text
F02_W07_BENCHMARK cases=2 runs=40 valid=40 valid_ir_rate=1.000 mean_ms=0.223 p95_ms=0.401
F02_W07_CASE equipment_checkout: runs=20 valid=20 mean_ms=0.301 p95_ms=0.454 fingerprint=0b77fc88e1223977
F02_W07_CASE safety_inspection: runs=20 valid=20 mean_ms=0.144 p95_ms=0.363 fingerprint=f7b0e61d72a7d65c
```

Test result:

```text
Ran 3 tests in 0.082s
OK
```

Latency is recorded as an observational receipt for this bounded in-memory run. No product SLA or competition success threshold is inferred from these numbers.

## Generalization evidence

- 40/40 benchmark runs produced validator-accepted DocumentIR.
- Valid DocumentIR rate for this fixture benchmark: 1.000.
- Each workflow produced one stable structural fingerprint across all 20 repeated runs.
- The two workflows are materially different in visual/control structure.
- Production source scan found no `equipment_checkout`, `equipment checkout`, `safety_inspection`, `safety inspection`, or `safety / inspection` markers under `src/paper2app`.
- Demo-specific fixture knowledge exists only under tests/golden; it is not part of production branching logic.

## Regression gate

Fresh W07 closure run:

```text
F02-W06 validator/golden regression      20/20 PASS
F02-W05 fusion regression                13/13 PASS
F02-W04 provider-port regression         21/21 PASS
F02-W03 observation-contract regression  15/15 PASS
understanding compile                    PASS
```

Earlier W01/W02 closure evidence remains authoritative for input gating and real PNG/JPEG decode/normalization.

## F02 exit decision

Roadmap exit requirement:

> at least two selected document types convert into stable validated DocumentIR structures.

Evidence satisfies the contract-level exit:

- Equipment Checkout -> stable validated DocumentIR: PASS.
- Safety / Inspection -> stable validated DocumentIR: PASS.
- Same production provider/fusion/validation path: PASS.
- Stable repeated fingerprints: PASS.
- No per-demo production branch: PASS.
- Explicit benchmark and failure/validation evidence: PASS.

Therefore:

**F02 — Input Understanding: CLOSED / PASS**

This closure establishes the deterministic input-understanding contract/runtime foundation. It is not a substitute for later real-image provider-quality acceptance.

## Next phase

`F03 — App Specification Synthesis`

The next phase consumes only validated DocumentIR and must preserve the existing architecture law:

`AI proposes -> contracts represent -> deterministic code validates -> runtime executes.`
