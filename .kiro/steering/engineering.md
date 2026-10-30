# Paper2App Engineering Steering

## Core architecture rule

**AI understands and proposes. Contracts represent. Deterministic code validates. The runtime executes.**

## Trust boundaries

1. Vision/OCR output is probabilistic and untrusted.
2. DocumentIR represents document truth, not application implementation.
3. AppSpec represents application behavior, not source code.
4. AppSpec must pass deterministic validation and runtime-capability checks before execution.
5. Runtime executes only allowlisted field types, actions, views and workflow transitions.
6. Arbitrary executable code, shell commands, SQL statements and embedded scripts are forbidden in AppSpec.

## DocumentIR laws

- Preserve source identity and raw observations.
- Keep observation and inference distinguishable.
- Important inferences may carry confidence and observable evidence.
- `unknown` is valid.
- IDs and references must validate deterministically.
- Geometry is first-class evidence.
- DocumentIR must not contain React, SQL, CRUD implementation, API route or storage-engine decisions.

## AppSpec laws

- Technology-independent behavior contract.
- Logical field types, not DB-native types.
- CRUD/actions are explicit, not assumed.
- Unsupported runtime capabilities fail before execution.
- Document-derived, product-policy and user-confirmed decisions remain distinguishable where relevant.
- Critical unresolved uncertainty blocks execution.
- Only validated AppSpec may enter runtime.

## Runtime laws

- One generic runtime for all supported generated applications.
- No per-demo hard-coded components.
- Backend performs authoritative record validation.
- Competition V1 persistence defaults to generic SQLite storage with validated JSON payloads.
- Records are isolated by app identity and retain spec/version provenance.
- Persisted data must survive reload.
- A second materially different AppSpec must execute with zero runtime source modifications.

## Vision/OCR strategy

- Vision-first document/layout understanding.
- OCR is an exact-text aid, not the semantic authority.
- Original and normalized images remain distinguishable.
- Provider disagreements remain observable.
- Providers sit behind replaceable interfaces.
- Retry/fallback behavior is bounded.
- Optimize for valid DocumentIR rate and end-to-end success, not OCR score alone.

## Engineering discipline

Use evidence-driven work packages:

1. state the contract;
2. implement the smallest change that satisfies it;
3. add focused tests;
4. run regression;
5. record evidence;
6. close only on verified PASS.

Prefer root-cause fixes over broad rewrites. Do not expand scope merely because a feature is technically interesting.

## Competition discipline

- Keep `/.kiro` tracked and visible.
- Record meaningful Kiro specs, steering, hooks and experiments.
- Preserve evidence needed to explain how Kiro improved the build.
- Re-audit competition rules when the dedicated Official Rules page is published.
