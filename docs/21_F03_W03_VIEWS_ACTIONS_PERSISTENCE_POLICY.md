# F03-W03 — Views, Actions & Persistence Policy

**Status:** CLOSED / PASS

## Scope

F03-W03 applies bounded Competition V1 product policy on top of F03-W02 entity/field synthesis. It does not render UI, execute actions, implement persistence, or synthesize workflow state transitions.

Canonical flow:

`EntityFieldSynthesisResult -> bounded surface policy -> views + actions + capabilities + persistence + cumulative provenance/uncertainty`

## Implementation

Production source:

- `src/paper2app/specification/surface_policy.py`

Public API:

- `ApplicationSurfaceSynthesisResult`
- `synthesize_views_actions_persistence(...)`

## Policy decisions

For every executable entity, Competition V1 emits semantic:

- `form`
- `record_list`
- `record_detail`

Explicit record actions are:

- `create_record`
- `update_record`
- `view_record`
- `list_records`
- `search_records`
- `filter_records`

Entity existence does not imply CRUD. Actions are explicit and required runtime capabilities are derived from those actions.

Persistence policy is:

- persistence required;
- records survive reload.

Additional capabilities are derived only when field types require them:

- `multi_choice` for `multi_enum`;
- `signature_capture` for `signature`.

`change_state` actions and `basic_workflow` capability remain outside W03 and are reserved for F03-W04 evidence-supported workflow synthesis.

## Provenance law

Form/list/detail, record actions, persistence and required runtime capabilities are Paper2App product decisions. They receive `PRODUCT_POLICY` provenance and are not misrepresented as facts observed in the source paper.

F03-W02 `DOCUMENT_DERIVED` field/entity provenance and upstream uncertainties are preserved unchanged.

## Fail-closed behavior

If no executable entity exists:

- no views are emitted;
- no record actions are emitted;
- a critical `surface:no_entities` uncertainty is added.

W03 does not invent an entity to satisfy the UI policy.

## Acceptance evidence

Target suite:

- `tests.test_view_action_persistence_policy` — 12/12 PASS

Regression:

- `tests.test_entity_field_synthesis` — 14/14 PASS
- `tests.test_app_spec_contract` — 18/18 PASS
- `tests.test_document_ir_validation` — 20/20 PASS
- `python -m compileall src/paper2app/specification` — PASS

The first W03 shell invocation used a filename-style unittest selector and failed import discovery; rerunning with the canonical module selector passed 12/12. This was a test-harness invocation error, not a product-code failure.

## Generalization evidence

`surface_policy.py` contains no Equipment Checkout or Safety/Inspection-specific production branch. The same policy operates over generic `AppEntity`/`AppField` contracts and also accepts multiple entities.

## Closure verdict

F03-W03 is CLOSED / PASS.

Next: `F03-W04 — Validation, Workflow, Provenance & Uncertainty Synthesis`.
