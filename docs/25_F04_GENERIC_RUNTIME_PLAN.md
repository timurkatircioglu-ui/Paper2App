# Paper2App — F04 Generic Runtime Plan

**Status:** ACTIVE — preflight complete, F04-W01 READY TO START

## Purpose

F04 turns a deterministically validated, runtime-compatible AppSpec into a working persistent application through one schema-driven runtime. It does not generate a new React/backend project per AppSpec.

Canonical flow:

`Validated AppSpec -> Runtime Manifest/Registry -> Record Validation -> Generic Store/API -> Schema-Driven UI -> Allowlisted Actions/Workflow -> Persistent Working App`

## Preflight findings

1. F03 already provides the authoritative AppSpec gate through `synthesize_validated_app_spec(...)`, `validate_app_spec(...)` and runtime capability profiles.
2. The repository currently contains no runtime package, FastAPI service, frontend application, SQLite store or Node package surface. F04 therefore starts from a clean runtime boundary.
3. `docs/07_RUNTIME_BLUEPRINT.md` already locks the core runtime laws: one generic runtime, no paper reinterpretation, no arbitrary code execution, generic JSON record persistence, app isolation and zero per-demo runtime-source changes.
4. `COMPETITION_V1_RUNTIME_PROFILE` proves capability compatibility at the AppSpec layer, but F04 needs a concrete runtime manifest that is the single source of truth for supported field types, views, actions, validation rules, workflow subset and capabilities.
5. Runtime implementation must preserve the distinction between AppSpec schema version and immutable registered AppSpec instance identity. F04 will use deterministic registered-spec identity/fingerprint rather than mutating AppSpec semantics.
6. Runtime North Star remains: for every AppSpec that the runtime declares supported and executable, `VALID APPSPEC -> WORKING APP RATE = 100%`.

## Stack decision

Competition V1 runtime stack is frozen to the existing blueprint direction:

- backend/runtime core: Python;
- HTTP service: FastAPI + Pydantic;
- persistence: Python `sqlite3` with validated JSON payloads;
- frontend: React + TypeScript + Vite;
- frontend/backend communication: bounded JSON contracts;
- no ORM, per-app SQL schema generator, microservice split, vector database, queue or plugin framework unless measured evidence later justifies one.

Exact dependency versions are intentionally deferred to the work package that introduces each dependency.

## Work-package decomposition

### F04-W01 — Runtime Manifest & Validated AppSpec Registry

**Status:** CLOSED / PASS

Target:

- create the `paper2app.runtime` package;
- define one concrete Runtime Manifest covering supported `FieldType`, `ViewKind`, `ActionKind`, `ValidationRuleKind`, condition/workflow subset and `Capability` values;
- derive the AppSpec `RuntimeCapabilityProfile` from that manifest rather than maintaining a second independent capability list;
- define deterministic immutable registered-AppSpec identity/fingerprint;
- allow registration only after the AppSpec passes the manifest-derived deterministic compatibility gate;
- provide active-spec lookup without silently overwriting prior registered versions;
- establish deterministic runtime failure contracts for invalid/incompatible/spec-not-found paths.

Acceptance:

- validated supported AppSpec registers;
- invalid/critical-uncertainty AppSpec cannot register;
- unsupported manifest surface cannot register;
- identical AppSpec yields identical registered identity;
- changed AppSpec yields a different identity;
- same app may retain immutable historical registrations while one registration is active;
- no persistence/HTTP/UI implementation is pulled into W01.

Closure evidence: `docs/26_F04_W01_RUNTIME_MANIFEST_APPSPEC_REGISTRY.md`.

### F04-W02 — Authoritative Record Contract & Deterministic Validation

**Status:** CLOSED / PASS

Target:

- define the runtime record payload/value boundary;
- validate field presence, unknown fields, logical types, enum/multi-enum choices and bounded AppSpec validation rules;
- apply bounded defaults only where AppSpec explicitly defines them;
- keep workflow state outside arbitrary payload data;
- return structured deterministic validation failures;
- make backend validation authoritative; frontend validation later mirrors it only for UX.

Acceptance:

- valid payload normalizes deterministically;
- invalid type/choice/rule fails before persistence;
- undeclared fields are rejected;
- validation remains generic and contains no demo labels or branches.

Closure evidence: `docs/27_F04_W02_AUTHORITATIVE_RECORD_VALIDATION.md`.

### F04-W03 — Generic SQLite Runtime Store & Application Isolation

**Status:** READY TO START

Target:

- implement a small SQLite adapter using generic tables, not per-app schema generation;
- persist immutable registered AppSpecs and validated record JSON;
- retain `record_id`, `app_id`, `entity_id`, registered-spec identity, workflow state and timestamps;
- enforce app/entity/spec isolation on reads and updates;
- prove process reopen/reload preserves data.

Acceptance:

- create/read/update/list survives store reopen;
- app A cannot read/update app B records;
- record provenance retains registered AppSpec identity;
- no dynamic SQL table/migration generation per AppSpec.

### F04-W04 — Generic Runtime Service API Foundation

**Status:** PLANNED

Target:

- introduce FastAPI/Pydantic only here;
- expose generic application/spec discovery and record create/list/detail/update/search/filter operations;
- route all writes through the authoritative record validator and SQLite store;
- map runtime failures to stable bounded API errors;
- keep AppSpec free of concrete HTTP route knowledge.

Acceptance:

- API works against at least one registered validated AppSpec;
- invalid record write is rejected before persistence;
- missing app/spec/record produce explicit deterministic errors;
- app isolation holds through HTTP surface.

### F04-W05 — Frontend Runtime Foundation & Field Renderer Registry

**Status:** PLANNED

Target:

- introduce React + TypeScript + Vite only here;
- create one generic AppShell and field-renderer registry;
- support the bounded F03 logical field vocabulary required by Competition V1, including signature and multi-choice capabilities where declared;
- consume runtime/AppSpec JSON rather than generated per-app source;
- provide explicit unsupported-field/runtime-error state.

Acceptance:

- field rendering is selected by AppSpec type only;
- no `EquipmentCheckoutForm`, `SafetyInspectionForm` or equivalent demo-specific component exists;
- frontend build/typecheck passes;
- unsupported renderer path fails visibly, never silently substitutes a different field type.

### F04-W06 — Schema-Driven Views, CRUD UX, Search & Filter

**Status:** PLANNED

Target:

- render AppSpec `form`, `record_list` and `record_detail` views generically;
- bind create/update/view/list/search/filter actions to the generic API;
- provide client-side validation feedback that mirrors, but never replaces, backend validation;
- support reload/navigation without losing persisted records;
- preserve application context and app isolation in the UI.

Acceptance:

- user can enter, save, list, inspect and update real data;
- search/filter operate deterministically at competition scale;
- reload retrieves the same persisted record;
- UI behavior is AppSpec-driven rather than demo-branch-driven.

### F04-W07 — Allowlisted Action Engine & Bounded Workflow Runtime

**Status:** PLANNED

Target:

- execute only AppSpec-declared allowlisted actions;
- implement the bounded state-machine subset from F03;
- validate state-transition legality and conditions before mutation;
- persist workflow state with the record;
- expose transition capability through generic API/UI controls;
- keep arbitrary formulas/scripts/BPM features out of scope.

Acceptance:

- legal transition succeeds and persists;
- illegal/unreachable transition fails deterministically;
- records without workflow remain unaffected;
- no arbitrary action execution surface exists.

### F04-W08 — Persistence, Two-AppSpec Generalization Benchmark & F04 Closure

**Status:** PLANNED

Target:

- register and execute the Equipment Checkout and resolved Safety/Inspection AppSpecs through the same runtime;
- create/update/list/detail/search/filter records for both;
- exercise Safety workflow where applicable;
- restart/reopen runtime storage and retrieve the same records;
- prove application isolation;
- prove runtime source changes between AppSpec A and AppSpec B are zero;
- close F04 only when the roadmap exit is evidenced.

Acceptance:

- both supported validated AppSpecs become functioning persistent apps;
- fresh runtime acceptance is 100% on the bounded benchmark;
- record/app/spec provenance is preserved;
- zero per-demo production runtime source modification;
- backend tests, frontend build/typecheck and integration acceptance all pass.

## Runtime failure surface

F04 keeps the blueprint taxonomy bounded and explicit:

- `APP_SPEC_INVALID`
- `APP_SPEC_INCOMPATIBLE`
- `UNSUPPORTED_FIELD_TYPE`
- `UNSUPPORTED_ACTION`
- `UNSUPPORTED_WORKFLOW`
- `RECORD_VALIDATION_FAILED`
- `PERSISTENCE_WRITE_FAILED`
- `PERSISTENCE_READ_FAILED`
- `SPEC_NOT_FOUND`
- `RECORD_NOT_FOUND`

Additional codes may be introduced only when a concrete deterministic failure cannot be represented by this set without ambiguity.

## F04 invariants

1. Runtime consumes only deterministically validated, manifest-compatible AppSpec.
2. Runtime never reinterprets the source paper or calls Vision/OCR.
3. One runtime executes every supported application.
4. Runtime behavior is AppSpec-driven; demo identity never controls production logic.
5. AppSpec cannot execute arbitrary code, SQL, shell commands, formulas or scripts.
6. Backend record validation is authoritative.
7. Runtime support claims come from one concrete manifest.
8. Persistence is isolated by application and retains registered-spec provenance.
9. Registered AppSpec instances are immutable; replacement creates a new identity/version.
10. Reload/restart must preserve persisted records.
11. Second application requires zero runtime source modification.
12. Complexity must earn its place.

## Explicit non-goals for F04

- paper/image ingestion;
- Vision/OCR or DocumentIR inference;
- new AppSpec semantic inference;
- user accounts/RBAC;
- multi-user collaboration;
- cloud synchronization;
- arbitrary plugins/scripts/formulas;
- generalized BPM;
- per-app generated source repositories;
- production hosting/deployment polish beyond what is required to prove the runtime locally.

## Current phase state

F04 is ACTIVE.

**Completed:** preflight, bounded work-package decomposition, F04-W01, and F04-W02.

**Next:** F04-W03 — Generic SQLite Runtime Store & Application Isolation.
