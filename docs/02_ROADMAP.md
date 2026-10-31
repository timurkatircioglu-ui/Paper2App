# Paper2App — Competition Roadmap

**Status:** Active
**Competition:** Kiroween 2026
**Category:** Frankenstein

## Macro phases

### M0 — Competition & Product Lock

#### F00 — Competition Contract & Fresh Repo
- [x] F00-W01 Competition Rule Lock & Fresh Repo Bootstrap — CLOSED / PASS
- [ ] F00-W02 Official Rules Re-audit when published — EVENT-DRIVEN / PENDING PUBLICATION
- [x] F00-W03 Git/GitHub/public-license/.kiro compliance gate — CLOSED / PASS
- [x] F00-W04 Competition baseline closure — CLOSED / PASS

Exit: PASS — current competition eligibility and repository baseline are evidenced. F00-W02 remains a standing mandatory re-audit obligation when the full Official Rules are published.

#### F01 — Product Contract
- [x] F01-W01 Problem & Audience Lock — CLOSED / PASS
- [x] F01-W02 Product Promise & Demo Lock — CLOSED / PASS
- [x] F01-W03 Minimum Lovable Product & Non-Goals Lock — CLOSED / PASS
- [x] F01-W04 Success Metrics & Product Contract Closure — CLOSED / PASS

Exit: PASS — a judge can understand Paper2App in one sentence and the team knows exactly what to build. Canonical contract: `docs/10_F01_PRODUCT_CONTRACT.md`.

### M1 — Paper Understanding Engine

#### F02 — Input Understanding
- [x] F02-W01 Input Gate & Source Contract — CLOSED / PASS
- [x] F02-W02 Deterministic Image Decode & Normalization — CLOSED / PASS
- [x] F02-W03 Visual Structure Observation Contract — CLOSED / PASS
- [x] F02-W04 Vision/OCR Provider Ports & Acceptance — CLOSED / PASS
- [x] F02-W05 Observation Fusion & DocumentIR Assembly — CLOSED / PASS
- [x] F02-W06 Deterministic DocumentIR Validation & Golden Set — CLOSED / PASS
- [ ] F02-W07 Generalization Benchmark & F02 Closure — READY TO START

Exit: at least two selected document types convert into stable validated DocumentIR structures. Canonical phase plan: `docs/11_F02_INPUT_UNDERSTANDING_PLAN.md`.

### M2 — Cognitive Transformation

#### F03 — App Specification Synthesis
- schema/entity inference
- field-type inference
- validation inference
- workflow/action inference
- AppSpec implementation
- deterministic AppSpec validation
- provenance mapping

Exit: validated AppSpec exists independently of rendering/runtime implementation.

### M3 — App Factory

#### F04 — Generic Runtime
- capability manifest
- AppSpec registry
- field renderer registry
- dynamic forms
- list/detail views
- generic backend API
- generic SQLite JSON record store
- authoritative record validation
- search/filter
- bounded workflow transitions

Exit: supported validated AppSpecs execute without per-app source changes.

#### F05 — Closed-Loop Paper2App
- upload/capture
- normalize
- understand
- DocumentIR
- AppSpec
- validate
- materialize runtime
- enter real data
- save
- reload/retrieve

Exit: primary demo works end-to-end without manual code edits between stages.

### M4 — Frankenstein Proof

#### F06 — Generalization Proof
- second materially different paper workflow
- same vision/IR/spec/runtime pipeline
- different fields/schema/UI/behavior
- unsupported-input handling
- zero runtime-source-change proof

Exit: two materially different papers become two functioning apps through one system.

#### F07 — Kiro Integration & Evidence
- steering strategy
- spec-driven work packages
- Kiro hooks where useful
- MCP/powers/Crew experiments where they earn their place
- Kiro contribution/evidence log
- reproducible development narrative

Exit: judges can see exactly how and why Kiro materially improved development.

### M5 — Prize Package

#### F08 — UX & Frankenstein Identity
- capture/import experience
- transformation visualization
- source paper vs generated app
- confidence/error states
- polished responsive UI
- memorable but restrained Frankenstein identity

Exit: first-time viewers understand the transformation immediately.

#### F09 — Verification, Reliability & Benchmark
- contract tests
- deterministic acceptance suite
- golden samples
- unseen-form benchmark
- malformed/unsupported input tests
- persistence/reload tests
- second-demo regression
- clean build/run

Exit: supported deterministic runtime paths pass consistently and AI-side quality is measured rather than assumed.

#### F10 — Deployment & Submission Package
- public deployment
- GitHub hygiene
- README/setup
- architecture diagram
- evidence index
- Devpost description
- Kiro write-up
- category justification
- demo script/video
- submission form draft

Exit: judges can understand, run and evaluate the project without hidden knowledge.

#### F11 — Final Competition Gate
- Official Rules final re-audit
- public repo/license/.kiro check
- live app check
- end-to-end demo check
- two-workflow generalization check
- Kiro evidence check
- video under 3 minutes
- submission before deadline

Exit: `SUBMIT` or `DO NOT SUBMIT` decision.

## Locked technical principles

1. Vision/OCR never directly drives executable runtime behavior.
2. DocumentIR and AppSpec remain separate contracts.
3. Only validated AppSpec enters the runtime.
4. Runtime is generic and schema-driven.
5. Competition V1 persistence uses a generic SQLite record store with validated JSON payloads unless measured evidence justifies a change.
6. Unsupported/unknown is an explicit legal outcome.
7. Two demo applications must use the same pipeline.
8. Kiro usage must be substantive and evidenced.
9. Complexity must earn its place.

## Immediate sequence

1. Close F00-W01 bootstrap.
2. Initialize Git and create first canonical commit.
3. Create/publish GitHub repository and verify license + `.kiro` visibility.
4. Re-audit Official Rules page when published.
5. Begin F01 Product Contract and convert pre-competition architecture reasoning into competition-created engineering artifacts.
