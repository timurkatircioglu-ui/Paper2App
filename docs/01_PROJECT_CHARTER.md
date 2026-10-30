# Paper2App — Project Charter

**Competition:** Kiroween 2026
**Category:** Frankenstein
**Status:** Product contract locked — F01 CLOSED / PASS

## One-line hook

**Take a picture of a paper workflow and turn it into a working application.**

## Product problem

Many real workflows still live on paper: checkout forms, inspection sheets, visitor forms, checklists, request forms and other operational documents. Turning each of these into software normally requires requirements analysis, schema design, UI work, validation logic and persistence engineering.

Paper2App compresses that transformation into one visible flow while preserving explicit contracts and deterministic gates.

## Primary audience

Competition V1 is primarily for small operational teams and process owners who repeatedly use paper forms or workflow sheets and want a lightweight working digital application without commissioning a custom software project.

Representative users include equipment/inventory coordinators, inspection or safety teams, office/facility operations, small organizations with recurring paper workflows, and internal process owners validating whether a paper process should become software.

Secondary users include makers, developers, and internal-tool builders who want a fast paper-to-application bootstrap that remains inspectable and contract-driven.

## Core transformation

`Physical paper/image -> visual and structural understanding -> DocumentIR -> application intent synthesis -> AppSpec -> deterministic validation -> schema-driven runtime -> persistent working application`

## Product principle

The desired reaction is:

> I took a photo of a form and now I have an app that actually works.

Paper2App must therefore be usable, not merely visually impressive.

## Primary demo

**Equipment Checkout**

Candidate source fields:

- Name
- Item
- Date
- Returned checkbox
- Signature / approval area where supported

Generated application target:

- data entry form;
- deterministic validation;
- save;
- persistent records;
- list/detail;
- search/filter;
- update/return-state handling;
- data remains after reload.

## Generalization demo

**Safety / Inspection Report**

Candidate source concepts:

- Inspector
- Location
- Date
- categories such as Electrical / Fire / Structural
- Severity: Low / Medium / High
- Notes
- Action Required
- Approval

This second workflow must pass through the same contracts and runtime without special-case source-code changes.

## Success criteria

Paper2App succeeds when:

1. the project is demonstrably new within the competition period;
2. the Frankenstein fit is immediately understandable;
3. a viewer can understand the product in one sentence;
4. paper/photo to working app completes end-to-end;
5. at least two materially different paper workflows produce functioning applications;
6. generated apps persist and reload real data;
7. deterministic checks separate AI inference from executable behavior;
8. unsupported or uncertain inputs fail explicitly rather than hallucinating;
9. Kiro usage is substantive, reproducible and evidenced;
10. the product can be demonstrated clearly inside the competition video limit;
11. a working deployed application URL is available for judging.

## Non-goals

Paper2App V1 is not:

- a universal no-code platform;
- an enterprise BPM suite;
- a general-purpose IDE;
- a perfect OCR engine;
- a handwriting-recognition research project;
- a giant multi-agent platform;
- a database migration generator;
- a source-code generator for arbitrary applications;
- a replacement for every document workflow.

## Scope guardrails

Competition V1 should prioritize:

- single-page forms/images;
- clean phone photos or scans;
- a bounded vocabulary of field types;
- two strong demo workflows;
- explicit uncertainty;
- one generic application runtime;
- reliable persistence;
- measurable end-to-end evidence.

## Product risks

- overbuilding infrastructure before the core loop works;
- appearing to be only OCR or a generic form builder;
- fragile model/provider dependence;
- pretty generated UI without real persistence;
- hard-coded demo forms masquerading as generalization;
- Kiro usage that is decorative rather than meaningful;
- rule or submission compliance drift;
- uncontrolled scope expansion.

## Operating principle

**AI understands and proposes. Contracts represent. Deterministic code validates. The runtime executes.**

Complexity must earn its place.
