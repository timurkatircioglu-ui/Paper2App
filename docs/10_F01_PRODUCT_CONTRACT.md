# F01 — Product Contract

**Status:** CLOSED / PASS
**Project:** Paper2App
**Competition:** Kiroween 2026
**Category:** Frankenstein
**Lock date:** 2026-10-31 (Türkiye)

## Purpose

Lock what Paper2App is, who it is for, what Competition V1 must deliver, what it must not become, and how product success will be judged before implementation expands.

F01 is a product-scope contract. It does not lock evidence-driven implementation details such as the exact vision model, OCR provider, deployment provider, UI component library, or confidence thresholds.

## F01 work packages

- [x] F01-W01 — Problem & Audience Lock — CLOSED / PASS
- [x] F01-W02 — Product Promise & Demo Lock — CLOSED / PASS
- [x] F01-W03 — Minimum Lovable Product & Non-Goals Lock — CLOSED / PASS
- [x] F01-W04 — Success Metrics & Product Contract Closure — CLOSED / PASS

## F01-W01 — Problem & Audience Lock

### Product problem

Many operational workflows still begin and end on paper: checkout forms, inspection sheets, visitor forms, checklists, request forms, and similar bounded workflow documents.

Turning each paper workflow into software normally requires multiple engineering steps: requirements analysis, data/schema design, form/UI implementation, validation behavior, persistence, and workflow logic.

Paper2App compresses that transformation into one understandable product flow while keeping probabilistic AI understanding separated from deterministic execution.

### Primary Competition V1 audience

Paper2App Competition V1 is primarily for:

> **small operational teams and process owners who repeatedly use paper forms or workflow sheets and want a lightweight working digital application without commissioning a custom software project.**

Representative users include:

- equipment / inventory coordinators;
- inspection or safety teams;
- office / facility operations;
- small organizations with recurring paper workflows;
- internal process owners validating whether a paper process should become software.

### Secondary audience

Secondary users include makers, developers, and internal-tool builders who want a fast paper-to-application bootstrap that remains inspectable and contract-driven.

### Explicit non-audience for Competition V1

Competition V1 is not optimized for:

- enterprise BPM administrators;
- organizations requiring complex IAM/RBAC, audit-compliance suites, or deep integrations;
- teams seeking arbitrary application/code generation;
- heavy handwritten-document transcription;
- general document-management or OCR-only workloads.

### Job to be done

When a user has a recurring paper workflow, they should be able to provide a clear image of it and get a usable, persistent application that reflects the document's intended data-entry and bounded workflow behavior.

## F01-W02 — Product Promise & Demo Lock

### One-line hook

> **Take a picture of a paper workflow and turn it into a working application.**

This is the canonical competition-facing hook.

### Product promise

The product promise is not merely:

`paper -> OCR text`

and not:

`paper -> pretty generated form`

It is:

`paper/photo -> understand structure and intent -> DocumentIR -> AppSpec -> deterministic validation -> generic runtime -> persistent working application`

The desired user/judge reaction is:

> I took a photo of a form and now I have an app that actually works.

### Primary demo lock

**Demo A — Equipment Checkout**

Expected concepts:

- Name
- Item
- Date
- Returned
- optional Signature / Approval where supported

Expected generated behavior:

- data-entry form;
- validation;
- save;
- persistent records;
- list/detail;
- search/filter;
- update / return-state handling;
- data survives reload.

### Generalization demo lock

**Demo B — Safety / Inspection Report**

Expected concepts:

- Inspector
- Location
- Date
- categories such as Electrical / Fire / Structural
- Severity: Low / Medium / High
- Notes
- Action Required
- Approval

### Generalization law

Both demos must pass through the same DocumentIR contract, AppSpec contract, validators, and generic runtime.

The second demo must require **zero per-demo runtime source modifications**.

A hard-coded Equipment Checkout screen plus a hard-coded Inspection screen does not satisfy the product contract.

## F01-W03 — Minimum Lovable Product & Non-Goals Lock

### Minimum Lovable Product (MLP)

Competition V1 must provide one coherent end-to-end experience:

1. user provides a supported single-page JPG/PNG photo or scan;
2. input is validated and normalized;
3. document structure/text/field relationships are understood;
4. a valid DocumentIR is produced or the system fails explicitly;
5. application semantics are proposed as AppSpec;
6. AppSpec passes deterministic validation and runtime capability checks;
7. one generic runtime materializes the application;
8. the user can enter real data;
9. records can be saved;
10. records can be listed and viewed;
11. supported records can be updated;
12. search/filter works where defined by the AppSpec/runtime subset;
13. persisted data remains after reload;
14. unsupported or critically uncertain cases do not silently become executable behavior.

### Supported Competition V1 boundary

Prioritize:

- single-page clean-ish phone photos/scans;
- printed forms and bounded workflow sheets;
- common text, multiline, date, boolean, enum/choice concepts;
- explicit uncertainty;
- two materially different paper workflows;
- one generic runtime;
- real persistence and reload;
- evidence that claims are measurable.

### Non-goals

Paper2App Competition V1 is not:

- a universal no-code platform;
- an enterprise BPM suite;
- a general-purpose IDE;
- a perfect OCR engine;
- a handwriting-recognition research project;
- a giant multi-agent platform;
- an arbitrary database migration generator;
- a general source-code generator;
- a multi-user SaaS platform;
- a system for arbitrary executable formulas/scripts;
- a general multi-page document-understanding engine;
- a solution for arbitrary complex tables;
- a replacement for every document workflow.

### Scope law

**Complexity must earn its place.**

If a smaller deterministic mechanism satisfies the product contract more reliably than a broader clever mechanism, Competition V1 chooses the smaller mechanism.

## F01-W04 — Success Metrics & Closure

### Product North Star

**END-TO-END PAPER -> WORKING APP SUCCESS**

AI-side supporting metric:

**VALID DOCUMENTIR RATE**

Runtime supporting metric:

**VALID SUPPORTED APPSPEC -> WORKING APP SUCCESS**

### Hard acceptance metrics

F01 defines the following product-level hard gates for later implementation phases:

1. **Two-demo generalization:** both locked demo workflows produce functioning applications through the same contracts and runtime.
2. **Zero demo-specific runtime patching:** Demo B executes without modifying runtime source to accommodate that demo.
3. **Runtime determinism:** every supported validated AppSpec used in canonical acceptance must materialize successfully; unsupported capability must fail before execution.
4. **Persistence proof:** canonical demo records survive save -> reload -> read.
5. **Validation separation:** AI output never enters runtime without deterministic contract validation.
6. **Explicit uncertainty:** critical unresolved uncertainty blocks execution instead of being guessed away.
7. **Real usability:** the generated application accepts and retrieves real user-entered records; screenshots alone are insufficient.
8. **Competition legibility:** the product can be explained accurately with the canonical one-line hook.
9. **Kiro evidence:** Kiro usage remains substantive and reproducible in repository evidence.
10. **Submission usability:** by final submission a working public application URL and public demo video must exist.

### Metrics intentionally not numerically frozen in F01

The following must be measured during implementation/benchmark phases before numeric thresholds are locked:

- end-to-end generation latency;
- vision/OCR accuracy thresholds;
- confidence calibration thresholds;
- provider cost;
- retry/fallback thresholds;
- final benchmark-set size beyond the locked two demo workflows.

Premature numeric targets would be invented rather than evidence-based.

### Product kill / fail conditions

The product contract is violated if any of the following becomes the canonical implementation:

- AI output directly executes without deterministic validation;
- the product is effectively only OCR;
- the generated application cannot persist real data;
- the second demo requires demo-specific runtime implementation;
- unsupported input is silently converted into invented application behavior;
- the architecture expands into a general no-code/BPM/agent platform before the core paper-to-app loop is proven;
- Kiro is present only decoratively rather than as substantive build evidence.

## Deferred implementation decisions

The following remain evidence-driven and are intentionally not locked by F01:

- exact vision provider/model;
- exact OCR provider;
- OCR always-on vs conditional policy;
- one-pass vs multi-pass vision prompting;
- confidence calibration thresholds;
- exact deployment target;
- exact UI component system;
- final bounded workflow subset;
- latency/cost target after benchmark evidence.

These are implementation decisions, not unresolved product identity.

## F01 evidence sources

This contract consolidates and narrows the already-created competition baseline:

- `docs/01_PROJECT_CHARTER.md`
- `docs/03_ARCHITECTURE_BLUEPRINT.md`
- `docs/04_DOCUMENT_IR_V0.md`
- `docs/05_APP_SPEC_V0.md`
- `docs/06_VISION_OCR_BLUEPRINT.md`
- `docs/07_RUNTIME_BLUEPRINT.md`
- `.kiro/steering/product.md`

## F01 exit gate

Roadmap exit requirement:

> a judge can understand Paper2App in one sentence and the team knows exactly what to build.

### Gate decision

- problem: LOCKED;
- primary audience: LOCKED;
- one-line hook: LOCKED;
- primary demo: LOCKED;
- generalization demo: LOCKED;
- Minimum Lovable Product: LOCKED;
- non-goals: LOCKED;
- product success metrics: LOCKED;
- evidence-driven implementation decisions: correctly DEFERRED;
- F01 exit: PASS.

**F01 — Product Contract = CLOSED / PASS**

**Next:** F02 — Input Understanding / Paper Understanding Engine.
