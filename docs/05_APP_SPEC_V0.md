# Paper2App — AppSpec Contract V0.1

**Status:** Canonical competition baseline

## Purpose

AppSpec answers:

> What application behavior should represent the workflow described by a validated DocumentIR?

It does not prescribe React, FastAPI, SQL, CSS or other implementation details.

## Top-level shape

```json
{
  "schema": "paper2app.app_spec",
  "schema_version": "0.1",
  "app": {},
  "entities": [],
  "views": [],
  "actions": [],
  "workflows": [],
  "validations": [],
  "capabilities": [],
  "persistence": {},
  "provenance": {},
  "uncertainties": []
}
```

## Application identity

`app` may contain:

- stable application ID;
- display name;
- description;
- primary entity ID.

It must not contain package names, filesystem paths or implementation-specific module details.

## Entities and fields

Entities describe technology-independent application data concepts.

Initial logical field types may include:

- `string`
- `multiline_string`
- `integer`
- `decimal`
- `boolean`
- `date`
- `time`
- `datetime`
- `enum`
- `multi_enum`
- `signature`
- `email`
- `phone`
- `identifier`

A logical type is not a database-native type.

## Validations

AppSpec may express bounded deterministic rules such as:

- required;
- min/max;
- min/max length;
- allowed values;
- format rules such as email where supported.

Do not invent aggressive constraints that are not justified by document evidence, explicit product policy or user confirmation.

## Views

Initial semantic view kinds:

- `form`
- `record_list`
- `record_detail`

AppSpec may define field order and semantic grouping but must not prescribe CSS dimensions or frontend component implementations.

## Actions

Initial bounded action vocabulary:

- `create_record`
- `update_record`
- `view_record`
- `list_records`
- `search_records`
- `filter_records`
- `change_state`

Capabilities are explicit; entity existence does not automatically grant full CRUD.

## Workflows

Competition V1 may support a small deterministic state-machine subset:

- known states;
- initial state;
- known field-based conditions;
- bounded transitions.

A general BPM engine is explicitly out of scope.

## Capabilities

AppSpec declares required capabilities so compatibility can be checked before runtime execution.

Example requirements may include:

- record create/update/list;
- search/filter;
- persistence;
- multi-choice;
- basic workflow.

If runtime does not support a required capability, validation fails before application execution.

## Persistence requirement

AppSpec may state that persistence is required and records must survive reload. It does not specify SQLite/PostgreSQL/table names/SQL statements.

## Provenance

Important application decisions should remain traceable to their source where useful.

Candidate provenance classes:

- `DOCUMENT_DERIVED`
- `PRODUCT_POLICY`
- `USER_CONFIRMED`

This prevents product defaults from being misrepresented as facts observed in the paper.

## Uncertainty

Critical unresolved uncertainty blocks executable status. Non-critical uncertainty may yield `PASS_WITH_WARNINGS` if the final policy permits safe execution.

## Validation outcomes

Target validation result vocabulary:

- `PASS`
- `PASS_WITH_WARNINGS`
- `FAIL`

## Deterministic invariants

- known schema/version;
- unique IDs;
- all references resolve;
- field types belong to known vocabulary;
- enum/multi-enum options are valid;
- required/default values are type-compatible;
- views/actions/workflows reference known entities/fields/states;
- required capabilities are supported by runtime;
- critical unresolved uncertainty prevents execution;
- arbitrary executable payloads are absent.

## Forbidden content

AppSpec must never carry:

- JavaScript/Python source;
- SQL statements;
- HTML/CSS executable fragments;
- shell commands;
- database credentials;
- API secrets;
- arbitrary scripts;
- arbitrary executable formulas.

## Demo proof

The same AppSpec contract must represent both Equipment Checkout and Safety / Inspection applications while producing materially different schemas, views and behaviors through one runtime.

## Architecture laws

- S1 AppSpec describes behavior, not implementation.
- S2 Arbitrary executable code is forbidden.
- S3 Every reference resolves deterministically.
- S4 Every executable field has a known logical type.
- S5 CRUD/actions are explicit.
- S6 Unsupported capabilities fail before runtime.
- S7 Document facts and product-policy decisions remain distinguishable.
- S8 Critical uncertainty blocks execution.
- S9 One contract represents materially different applications.
- S10 Only validated AppSpec enters runtime.
