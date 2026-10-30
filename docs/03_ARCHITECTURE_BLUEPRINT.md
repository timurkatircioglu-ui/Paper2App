# Paper2App — Architecture Blueprint V0.1

**Status:** Canonical competition baseline
**Origin:** Re-authored during the Kiroween 2026 Submission Period from pre-build design reasoning; no production implementation imported.

## 1. System goal

Transform a physical paper workflow into a usable, persistent application while keeping probabilistic AI reasoning separated from deterministic execution.

## 2. End-to-end architecture

`Paper/photo -> Input Preprocessor -> Document Understanding -> DocumentIR -> App Intent Synthesis -> AppSpec -> Deterministic Validator -> Schema-Driven Runtime -> Persistence -> Working App`

A parallel Evidence/Telemetry layer records timings, validation states and bounded diagnostics.

## 3. Architectural boundaries

### Input Preprocessor

**Input:** JPG/PNG single-page image.

**Responsibility:** file validation, orientation, crop, perspective correction, normalization handoff.

**Forbidden:** semantic field inference, application design, persistence.

### Document Understanding

**Input:** normalized/original document image.

**Responsibility:** detect regions, text, field-like visual elements, relationships, semantic hints and confidence; use OCR where exact transcription is useful.

**Output:** DocumentIR candidate.

**Forbidden:** direct UI generation, database design, executable behavior.

### DocumentIR Validator

**Responsibility:** deterministic schema/reference/geometry/confidence validation.

**Forbidden:** inventing missing document facts.

### App Intent Synthesis

**Input:** validated DocumentIR.

**Responsibility:** infer the technology-independent application model: entities, fields, logical types, views, validations, actions, workflow hints and persistence requirements.

**Output:** AppSpec proposal.

**Forbidden:** React/FastAPI/SQL implementation generation.

### AppSpec Validator

**Responsibility:** deterministic contract validation and runtime-capability compatibility.

**Rule:** unvalidated or incompatible AppSpec cannot enter runtime.

### Schema-Driven Runtime

**Input:** validated compatible AppSpec.

**Responsibility:** render known UI components, execute allowlisted actions/workflows, validate records, persist/retrieve records.

**Forbidden:** reinterpreting the paper, invoking arbitrary code from AppSpec, freeform semantic inference.

### Persistence

Competition V1 defaults to a generic SQLite store with application/spec identity plus validated JSON record payloads. Dynamic per-app SQL schema generation is out of scope unless measured evidence proves it necessary.

### Evidence / Telemetry

Record bounded stage timings, validation outcomes, confidence/uncertainty counts and runtime acceptance results. Do not log secrets or unnecessary sensitive document contents.

## 4. Trust boundary

### Probabilistic / untrusted side

- vision observations;
- OCR observations;
- semantic inference;
- DocumentIR proposal;
- AppSpec proposal.

### Deterministic gate

- DocumentIR validation;
- AppSpec validation;
- runtime capability check.

### Controlled execution side

- known field renderers;
- known views/actions;
- bounded workflow transitions;
- deterministic record validation;
- persistence operations.

## 5. Architecture laws

1. No direct AI-to-runtime execution.
2. DocumentIR and AppSpec are separate contracts.
3. Unknown/unsupported is legal; fabricated certainty is not.
4. One runtime serves multiple generated applications.
5. Primary and secondary demos use the same pipeline.
6. Runtime never interprets the source paper.
7. Vision never owns persistence.
8. Deterministic gates control executable behavior.
9. Evidence is first-class.
10. Complexity must earn its place.
11. Kiro is a development-engineering tool/evidence surface, not a mandatory runtime dependency unless a later deliberate product decision says otherwise.
12. Development tooling such as BORG is not a submission runtime dependency unless explicitly justified and rule-compliant.

## 6. Candidate technology stack

- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI + Pydantic
- Image processing: OpenCV where useful
- Vision: replaceable multimodal provider selected by benchmark
- OCR: replaceable OCR provider, used where justified
- Contracts: JSON / JSON Schema / typed models
- Frontend validation: Zod or equivalent
- Persistence: SQLite
- Backend tests: Pytest
- End-to-end tests: Playwright
- AI engineering: Kiro
- Version control: Git + public GitHub for final submission

Exact provider/model and dependency versions are intentionally not locked until implementation/benchmark evidence exists.

## 7. Initial supported scope

Competition V1 targets:

- single-page clean-ish phone photos/scans;
- printed forms and bounded workflow sheets;
- common text/date/boolean/choice/multiline concepts;
- explicit uncertainty;
- two materially different demo workflows;
- real persistence and reload.

Out of scope initially:

- general multi-page document understanding;
- arbitrary tables;
- perfect handwriting transcription;
- arbitrary executable formulas/scripts;
- enterprise BPM;
- per-generated-app source-code projects.

## 8. Demo architecture proof

### Demo A — Equipment Checkout

Expected concepts: Name, Item, Date, Returned, optional Signature/Approval.

### Demo B — Safety / Inspection Report

Expected concepts: Inspector, Location, Date, multi-choice categories, severity enum, notes, action-required boolean, approval.

Acceptance proof: both produce distinct AppSpecs and working apps using the same contracts and unchanged runtime source.

## 9. Open decisions

- exact vision provider/model;
- exact OCR provider and conditional-vs-always OCR policy;
- one-pass vs multi-pass vision prompting;
- confidence calibration thresholds;
- exact deployment target;
- exact UI component system;
- final workflow subset.

These are evidence-driven implementation decisions, not architectural ambiguities.
