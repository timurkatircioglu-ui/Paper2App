# F03 — App Specification Synthesis Plan

**Status:** ACTIVE
**Phase goal:** Transform validated DocumentIR into a technology-independent AppSpec proposal, then deterministically validate it before any runtime execution.

## Architectural boundary

F03 starts only from validated DocumentIR. It may infer application semantics, but it must not generate React/FastAPI/SQL/CSS/source-code implementation details.

Canonical flow:

`validated DocumentIR -> bounded synthesis -> AppSpec proposal -> deterministic AppSpec validation -> runtime capability compatibility -> validated AppSpec`

The probabilistic/untrusted side may propose. Deterministic gates decide whether the proposal is executable.

## Work packages

### F03-W01 — AppSpec Contract & Bounded Vocabulary

**Status:** CLOSED / PASS

Target:

- implement the canonical AppSpec 0.1 runtime contract;
- freeze bounded field/view/action/validation/workflow/capability vocabularies;
- represent persistence, provenance and uncertainty without implementation details;
- reject arbitrary executable payload shapes at the contract boundary;
- keep graph/reference validation separate for the later deterministic validator.

Closure evidence: `docs/19_F03_W01_APP_SPEC_CONTRACT.md`.

### F03-W02 — Deterministic Entity & Field Synthesis

**Status:** CLOSED / PASS

Target:

- accept only validated DocumentIR as synthesis input;
- map bounded DocumentIR field candidates to one or more application entities/fields;
- infer logical field types conservatively from document-semantic hints;
- preserve source references and confidence/uncertainty;
- use `unknown`/explicit uncertainty instead of invented certainty;
- avoid demo-specific synthesis branches.

Closure evidence: `docs/20_F03_W02_ENTITY_FIELD_SYNTHESIS.md`.

### F03-W03 — Views, Actions & Persistence Policy

**Status:** CLOSED / PASS

Target:

- synthesize form/list/detail semantic views;
- make create/update/view/list/search/filter actions explicit;
- derive capability requirements from the AppSpec surface;
- apply bounded Competition V1 persistence product policy;
- distinguish product-policy defaults from document-derived facts.

Closure evidence: `docs/21_F03_W03_VIEWS_ACTIONS_PERSISTENCE_POLICY.md`.

### F03-W04 — Validation, Workflow, Provenance & Uncertainty Synthesis

**Status:** CLOSED / PASS

Target:

- synthesize only evidence-supported deterministic validation rules;
- synthesize a small state-machine subset where document evidence justifies it;
- attach `DOCUMENT_DERIVED`, `PRODUCT_POLICY`, or `USER_CONFIRMED` provenance;
- propagate/translate critical and non-critical uncertainty explicitly;
- never emit arbitrary executable formulas or scripts.

Closure evidence: `docs/22_F03_W04_VALIDATION_WORKFLOW_PROVENANCE_UNCERTAINTY.md`.

### F03-W05 — Deterministic AppSpec Validation & Runtime Capability Gate

**Status:** CLOSED / PASS

Target:

- deterministic schema/version/reference/type validation;
- validate enum/default/validation-rule compatibility;
- validate views/actions/workflows against known entities/fields/states;
- reject unsupported required runtime capabilities before execution;
- critical unresolved uncertainty must block executable status;
- expose `PASS`, `PASS_WITH_WARNINGS`, `FAIL`.

Closure evidence: `docs/23_F03_W05_APPSPEC_VALIDATION_RUNTIME_CAPABILITY_GATE.md`.

### F03-W06 — Generalization Benchmark & F03 Closure

**Status:** CLOSED / PASS

Target:

- Equipment Checkout and Safety/Inspection produce materially different AppSpecs through the same synthesis contracts;
- both AppSpecs validate through the same deterministic gate;
- no per-demo production synthesis/runtime branch;
- structural output is stable under deterministic fixtures;
- close F03 only when the roadmap exit is evidenced.

Closure evidence: `docs/24_F03_W06_GENERALIZATION_BENCHMARK_AND_CLOSURE.md`.

## F03 invariants

1. AppSpec describes application behavior, not implementation technology.
2. Only validated DocumentIR may enter authoritative synthesis.
3. Document-derived facts and product-policy decisions remain distinguishable.
4. Actions/capabilities are explicit; entity existence does not imply full CRUD.
5. Unknown/critical uncertainty is legal and never silently converted into executable certainty.
6. Arbitrary source code, SQL, shell, HTML/CSS, scripts, secrets and executable formulas are forbidden.
7. One AppSpec contract must represent materially different applications.
8. Runtime capability incompatibility fails before runtime execution.
9. Only deterministically validated AppSpec may enter the runtime.
10. Complexity must earn its place.

## Current phase state

F03 is CLOSED / PASS.

**Completed:** F03-W01 through F03-W06.

**Next:** F04-W01 — Runtime Manifest & Validated AppSpec Registry.
