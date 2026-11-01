# Paper2App — F04-W01 Runtime Manifest & Validated AppSpec Registry

**Status:** CLOSED / PASS

## Purpose

F04-W01 establishes the first concrete runtime boundary after F03: one immutable runtime manifest declares the bounded AppSpec surface Competition V1 intends to execute, and an in-memory registry accepts only deterministically valid, manifest-compatible AppSpecs.

This package deliberately does **not** implement persistence, HTTP, FastAPI, SQLite, record validation, frontend rendering or workflow execution. Those remain owned by later F04 work packages.

## Production surface

Created:

- `src/paper2app/runtime/__init__.py`
- `src/paper2app/runtime/manifest.py`
- `src/paper2app/runtime/registry.py`

Adjusted:

- `src/paper2app/specification/validation.py`
- `src/paper2app/specification/__init__.py`

Acceptance:

- `tests/test_runtime_manifest_registry.py`

## Runtime Manifest

`COMPETITION_V1_RUNTIME_MANIFEST` is now the single concrete runtime support authority for:

- AppSpec schema versions;
- `FieldType`;
- `ViewKind`;
- `ActionKind`;
- `ValidationRuleKind`;
- `ConditionOperator`;
- `Capability`;
- whether bounded workflow is enabled;
- the maximum workflow count per entity.

The manifest is immutable and rejects duplicate/ill-typed support declarations and inconsistent workflow policy.

### Manifest-derived AppSpec capability profile

F03 previously held a separately constructed `COMPETITION_V1_RUNTIME_PROFILE`. W01 removes that independently maintained capability list from the authoritative path.

`validate_app_spec(...)`, `require_valid_app_spec(...)` and `synthesize_validated_app_spec(...)` now resolve their default capability profile lazily from `COMPETITION_V1_RUNTIME_MANIFEST`.

The public compatibility name `COMPETITION_V1_RUNTIME_PROFILE` remains available through lazy module/package access, so existing callers do not need to change, but its value is derived from the runtime manifest.

Lazy resolution is intentional: eager `runtime.manifest <-> specification.validation` imports create a package-initialization cycle. The final design preserves dependency direction without relying on import order.

## Manifest compatibility gate

The runtime manifest checks the actual AppSpec surface, not only declared capabilities.

A spec is incompatible when it uses a runtime surface that the selected manifest does not support, including:

- field type;
- view kind;
- action kind;
- validation rule;
- condition operator;
- workflow policy;
- declared capability;
- AppSpec schema version.

A restricted custom manifest therefore rejects an otherwise structurally valid AppSpec with `APP_SPEC_INCOMPATIBLE`.

## Registered AppSpec identity

`app_spec_fingerprint(...)` canonicalizes the immutable AppSpec graph and computes SHA-256 over deterministic UTF-8 JSON.

Properties proven by acceptance:

- identical AppSpec -> identical fingerprint;
- identical AppSpec -> identical registration ID;
- re-registering the same spec is idempotent and does not duplicate history;
- changing AppSpec content -> different fingerprint and registration ID;
- registration identity is independent from mutable timestamps because W01 stores no registration timestamp.

`RegisteredAppSpec` retains:

- registration ID;
- app ID;
- SHA-256 fingerprint;
- AppSpec schema version;
- runtime manifest ID/version;
- validation status;
- immutable AppSpec object.

## Registry activation semantics

`AppSpecRegistry` is in-memory in W01. Persistence is intentionally deferred to F04-W03.

Rules:

1. first valid registration for an `app_id` becomes active;
2. a later different registration for the same app is retained in immutable history but does **not** silently replace the active registration;
3. cutover requires `activate=True` on registration or explicit `activate(app_id, registration_id)`;
4. an identical re-registration returns the existing registered object;
5. active and historical lookup never mutates registered specs.

This preserves old specification history while making active-spec change explicit.

## Runtime failure contract

W01 establishes the bounded registry failure codes required by the runtime blueprint:

- `APP_SPEC_INVALID`
- `APP_SPEC_INCOMPATIBLE`
- `SPEC_NOT_FOUND`

Classification:

- graph/reference/type/critical-uncertainty validation failures -> `APP_SPEC_INVALID`;
- manifest/runtime support mismatch -> `APP_SPEC_INCOMPATIBLE`;
- unknown active/registered identity -> `SPEC_NOT_FOUND`.

No raw persistence/HTTP exception surface exists in W01.

## Acceptance evidence

Fresh canonical runs:

- `python -m unittest tests.test_runtime_manifest_registry` -> **14/14 PASS**
- `python -m unittest tests.test_app_spec_validation` -> **23/23 PASS**
- `python -m unittest tests.test_f03_w06_generalization_benchmark` -> **4/4 PASS**
- `python -m unittest tests.test_app_spec_contract` -> **18/18 PASS**
- `python -m compileall -q src/paper2app/runtime` -> **PASS**
- `python -m compileall -q src/paper2app/specification` -> **PASS**

The F03 generalization benchmark still passes after the default capability profile moved behind the manifest-derived lazy path.

## Red-to-green notes

Two early red runs were not accepted as closure evidence:

1. The first targeted `unittest` call could not import `paper2app` because Shell19 direct unittest execution does not inject `src/` into `sys.path`. The new test adopted the same explicit `src` bootstrap used by existing repository tests.
2. The next run exposed a real package import cycle caused by eagerly materializing the manifest-derived profile while `runtime.manifest` itself was importing `specification.app_spec`. The profile resolution was made lazy at both `validation` and public `specification` package boundaries. The final targeted and regression runs are green.

## Scope boundary

W01 contains no:

- SQLite/database adapter;
- record payload persistence;
- FastAPI/Pydantic service;
- HTTP route;
- React/TypeScript code;
- field renderer;
- record create/update/search implementation;
- workflow execution engine.

Those remain owned by F04-W02 through F04-W07.

## Verdict

**F04-W01 = CLOSED / PASS**

The runtime now has one concrete support manifest, a manifest-derived AppSpec compatibility profile, deterministic immutable registered-spec identity, explicit active/history semantics, and fail-closed registration errors. F04-W02 may now define authoritative runtime record contracts and deterministic record validation against registered AppSpecs.
