# Paper2App

**Kiroween 2026 — Frankenstein**

Paper2App turns a photo of a paper workflow into a working, persistent application.

## Core transformation

`Paper / photo -> visual understanding -> DocumentIR -> AppSpec -> deterministic validation -> schema-driven runtime -> working app`

Paper2App is not an OCR demo and not a generic AI code generator. Vision/OCR produce a structured document representation; a separate synthesis stage proposes application semantics; deterministic contracts validate that proposal before a known runtime executes it.

## Competition status

- Competition: Kiroween 2026
- Category: Frankenstein
- Build period: October 30–December 4, 2026
- Repository created during the official Submission Period
- Fresh project: no pre-competition production code imported
- Kiro usage is tracked in the root `/.kiro` directory

See `docs/00_COMPETITION_CONTRACT.md` for the current rule lock and re-audit obligation.

## Product goal

A user photographs a real paper form or workflow. Paper2App understands its structure and intent, produces a validated application specification, and materializes a usable application that can accept, validate, save, list, search, filter, and reload records.

## Demonstration target

The same pipeline must generate at least two materially different working applications without runtime source changes, such as:

1. Equipment Checkout
2. Safety / Inspection Report

## Architecture principles

- AI proposes; deterministic code validates.
- Document truth (`DocumentIR`) is separate from application truth (`AppSpec`).
- Unknown and unsupported states are valid outcomes; invention is not.
- The runtime consumes only validated AppSpec.
- One generic runtime serves multiple generated applications.
- Persistence is real and must survive reload.
- Complexity must earn its place.

## Repository map

- `.kiro/` — Kiro steering/spec/hook evidence
- `docs/` — competition contract, architecture, contracts, roadmap, evidence plans
- application source folders will be added by competition work packages after bootstrap

## License

MIT License. See `LICENSE`.
