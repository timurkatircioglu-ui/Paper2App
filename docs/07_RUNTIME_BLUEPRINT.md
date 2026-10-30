# Paper2App — Runtime Blueprint V0.1

**Status:** Canonical competition baseline

## Purpose

The runtime consumes only a validated, runtime-compatible AppSpec and materializes a working application without generating a new source-code project per document.

## Core decision

Competition V1 uses a **schema-driven generic runtime**, not AI-generated React/backend source per paper.

`Validated AppSpec -> known generic runtime -> working persistent application`

## Runtime components

- AppSpec Registry
- Runtime Capability Manifest
- Dynamic UI / Field Renderer Registry
- View Renderer
- Action Engine
- Deterministic Record Validation
- Bounded Workflow Engine
- Persistence API
- Generic SQLite Store
- Evidence/Telemetry

## Runtime boundary

The runtime does not:

- inspect the original paper;
- call vision/OCR to reinterpret source evidence;
- infer new application semantics;
- execute arbitrary scripts from AppSpec.

## Frontend candidate

React + TypeScript + Vite.

Candidate generic components:

- AppShell
- DynamicForm
- FieldRenderer
- RecordList
- RecordDetail
- Search/Filter controls
- ValidationSummary
- explicit RuntimeError state

There must be no demo-specific `EquipmentCheckoutForm` or equivalent hard-coded component in the generic path.

## Field renderer registry

Logical AppSpec types map to known renderers, for example:

- `string` -> text input
- `multiline_string` -> textarea
- `boolean` -> checkbox/toggle
- `date` -> date input
- `enum` -> single choice/select
- `multi_enum` -> multi-choice control
- supported numeric/identifier formats -> bounded known renderers

Unsupported types fail before execution.

## Runtime capability manifest

The runtime publishes the exact field types, views, actions and workflow features it supports. AppSpec validation checks required capabilities against this manifest before application launch.

## Backend candidate

Python + FastAPI + Pydantic.

The backend remains generic. Example conceptual APIs:

- fetch registered AppSpec;
- create record;
- list records;
- fetch record;
- update record;
- search/filter records.

AppSpec does not know concrete HTTP routes.

## Persistence decision

Competition V1 defaults to **generic SQLite record storage with validated JSON payloads** rather than dynamically generating SQL tables/migrations for every AppSpec.

Conceptual stored metadata:

- record ID;
- app ID;
- entity ID;
- AppSpec version;
- bounded workflow state where needed;
- validated payload JSON;
- created/updated timestamps.

Advantages:

- no per-app migration engine;
- minimal dynamic SQL;
- easier generalization;
- simpler regression;
- lower demo failure surface.

## AppSpec Registry

Only validated AppSpecs may be registered. Registry responsibilities include:

- application identity;
- AppSpec version;
- validation status;
- runtime compatibility;
- active specification lookup.

Prefer immutable version history rather than silently overwriting old AppSpecs.

## Validation

Record validation occurs twice where practical:

1. client-side for UX;
2. authoritative backend validation before persistence.

Supported validation rules remain bounded and deterministic.

## Views

Competition V1 targets semantic views such as:

- form/create;
- record list;
- record detail.

Semantic field ordering/grouping may come from AppSpec. CSS/layout implementation remains a runtime concern.

## Actions

Only allowlisted actions execute, such as:

- create;
- update;
- view;
- list;
- search;
- filter;
- bounded state transition.

No arbitrary shell/SQL/script action exists.

## Workflow engine

Competition V1 supports only a small deterministic state-machine subset if required by demo evidence. A general BPM engine is out of scope.

## Search/filter

Use simple deterministic search/filter appropriate for competition-scale records. Elasticsearch/vector search or other infrastructure requires measured justification.

## Application isolation

Records are isolated by `app_id`. Data from one generated application must never appear inside another application context.

## Persistence proof

Canonical acceptance:

1. open generated app;
2. enter valid data;
3. save;
4. reload/restart the UI;
5. retrieve and display the same record.

## Generalization proof

Run AppSpec A and AppSpec B through the same runtime.

Acceptance condition:

**runtime source changes between the two generated applications = zero**.

## Runtime failure taxonomy

Candidate deterministic failures:

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

## Deployment

Final competition submission requires a working application URL. Localhost may be used during development, but F10 must provide a judge-accessible deployment consistent with the eventual Official Rules.

## Minimum competition runtime

Required target capabilities:

- dynamic form rendering;
- string/multiline/boolean/date/enum/multi-enum support;
- required/type/choice validation;
- create/update/list/detail;
- search/filter;
- persistence;
- reload proof;
- explicit errors.

Initially out of scope:

- user accounts/roles;
- multi-user collaboration;
- cloud sync;
- complex BPM;
- custom user scripts;
- arbitrary formulas;
- plugin marketplace;
- per-app generated source projects.

## Runtime North Star

For any AppSpec that validation declares supported and executable:

**VALID APPSPEC -> WORKING APP RATE = 100%**.

Failures on supported deterministic paths are runtime bugs, not acceptable probabilistic misses.

## Architecture laws

- R1 Runtime consumes only validated AppSpec.
- R2 Runtime never interprets source documents.
- R3 One runtime executes all supported applications.
- R4 Application behavior is data-driven, not demo-hard-coded.
- R5 AppSpec cannot execute arbitrary code.
- R6 Backend performs authoritative record validation.
- R7 Unsupported capability fails before execution.
- R8 Persistence is application-isolated.
- R9 Records retain AppSpec/version provenance.
- R10 Supported AppSpecs execute deterministically.
- R11 Reload preserves persisted records.
- R12 Second demo requires zero runtime source modification.
