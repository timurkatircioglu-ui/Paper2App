"""Deterministic Competition V1 view/action/persistence policy synthesis."""

from __future__ import annotations

from dataclasses import dataclass

from .app_spec import (
    ActionKind,
    AppAction,
    AppEntity,
    AppSpecUncertainty,
    AppView,
    Capability,
    FieldType,
    PersistenceRequirement,
    ProvenanceClass,
    ProvenanceRecord,
    ViewKind,
)
from .synthesis import EntityFieldSynthesisResult


@dataclass(frozen=True, slots=True)
class ApplicationSurfaceSynthesisResult:
    """Cumulative F03 synthesis state after applying bounded product policy."""

    entities: tuple[AppEntity, ...]
    views: tuple[AppView, ...]
    actions: tuple[AppAction, ...]
    capabilities: tuple[Capability, ...]
    persistence: PersistenceRequirement
    provenance: tuple[ProvenanceRecord, ...]
    uncertainties: tuple[AppSpecUncertainty, ...]

    def __post_init__(self) -> None:
        typed_collections = (
            ("entities", self.entities, AppEntity),
            ("views", self.views, AppView),
            ("actions", self.actions, AppAction),
            ("capabilities", self.capabilities, Capability),
            ("provenance", self.provenance, ProvenanceRecord),
            ("uncertainties", self.uncertainties, AppSpecUncertainty),
        )
        for name, values, expected_type in typed_collections:
            if not isinstance(values, tuple):
                raise TypeError(f"{name} must be a tuple")
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{name} contains an invalid value")
        if not isinstance(self.persistence, PersistenceRequirement):
            raise TypeError("persistence must be a PersistenceRequirement")


_BASE_ACTIONS: tuple[tuple[ActionKind, Capability, str], ...] = (
    (ActionKind.CREATE_RECORD, Capability.RECORD_CREATE, "create"),
    (ActionKind.UPDATE_RECORD, Capability.RECORD_UPDATE, "update"),
    (ActionKind.VIEW_RECORD, Capability.RECORD_VIEW, "view"),
    (ActionKind.LIST_RECORDS, Capability.RECORD_LIST, "list"),
    (ActionKind.SEARCH_RECORDS, Capability.RECORD_SEARCH, "search"),
    (ActionKind.FILTER_RECORDS, Capability.RECORD_FILTER, "filter"),
)

_CAPABILITY_ORDER: tuple[Capability, ...] = (
    Capability.RECORD_CREATE,
    Capability.RECORD_UPDATE,
    Capability.RECORD_VIEW,
    Capability.RECORD_LIST,
    Capability.RECORD_SEARCH,
    Capability.RECORD_FILTER,
    Capability.PERSISTENCE,
    Capability.MULTI_CHOICE,
    Capability.SIGNATURE_CAPTURE,
    Capability.BASIC_WORKFLOW,
)


def _policy_provenance(target_id: str, note: str) -> ProvenanceRecord:
    safe_id = target_id.replace(":", "_")
    return ProvenanceRecord(
        provenance_id=f"policy:{safe_id}",
        target_id=target_id,
        provenance_class=ProvenanceClass.PRODUCT_POLICY,
        source_refs=(),
        note=note,
    )


def _ordered_capabilities(values: set[Capability]) -> tuple[Capability, ...]:
    return tuple(capability for capability in _CAPABILITY_ORDER if capability in values)


def synthesize_views_actions_persistence(
    entity_fields: EntityFieldSynthesisResult,
) -> ApplicationSurfaceSynthesisResult:
    """Apply bounded Competition V1 product policy to synthesized entities/fields.

    Views, actions and persistence are product decisions rather than facts observed on
    paper, so every newly introduced decision receives PRODUCT_POLICY provenance.
    Workflow/change-state semantics are deliberately excluded until F03-W04.
    """

    if not isinstance(entity_fields, EntityFieldSynthesisResult):
        raise TypeError("entity_fields must be an EntityFieldSynthesisResult")

    views: list[AppView] = []
    actions: list[AppAction] = []
    provenance = list(entity_fields.provenance)
    uncertainties = list(entity_fields.uncertainties)
    capabilities: set[Capability] = set()

    for entity in entity_fields.entities:
        field_ids = tuple(field.field_id for field in entity.fields)
        view_specs = (
            (ViewKind.FORM, "form", f"{entity.display_name} Form"),
            (ViewKind.RECORD_LIST, "list", f"{entity.display_name} Records"),
            (ViewKind.RECORD_DETAIL, "detail", f"{entity.display_name} Detail"),
        )
        for kind, suffix, title in view_specs:
            view_id = f"view:{entity.entity_id}:{suffix}"
            views.append(
                AppView(
                    view_id=view_id,
                    kind=kind,
                    entity_id=entity.entity_id,
                    field_ids=field_ids,
                    title=title,
                )
            )
            provenance.append(
                _policy_provenance(
                    view_id,
                    "Competition V1 exposes form/list/detail semantic views for executable entities.",
                )
            )

        for kind, capability, suffix in _BASE_ACTIONS:
            action_id = f"action:{entity.entity_id}:{suffix}"
            actions.append(AppAction(action_id=action_id, kind=kind, entity_id=entity.entity_id))
            capabilities.add(capability)
            provenance.append(
                _policy_provenance(
                    action_id,
                    "Competition V1 makes supported record operations explicit rather than implying CRUD from entity existence.",
                )
            )

        if any(field.field_type is FieldType.MULTI_ENUM for field in entity.fields):
            capabilities.add(Capability.MULTI_CHOICE)
        if any(field.field_type is FieldType.SIGNATURE for field in entity.fields):
            capabilities.add(Capability.SIGNATURE_CAPTURE)

    persistence = PersistenceRequirement(required=True, survive_reload=True)
    capabilities.add(Capability.PERSISTENCE)
    provenance.append(
        _policy_provenance(
            "persistence",
            "Competition V1 requires generated application records to persist and survive reload.",
        )
    )

    if not entity_fields.entities:
        uncertainties.append(
            AppSpecUncertainty(
                uncertainty_id="surface:no_entities",
                message="Views and actions cannot be synthesized because no executable entity exists.",
                critical=True,
            )
        )

    ordered_capabilities = _ordered_capabilities(capabilities)
    for capability in ordered_capabilities:
        provenance.append(
            _policy_provenance(
                f"capability:{capability.value}",
                "Required runtime capability is derived from the bounded Competition V1 application surface.",
            )
        )

    return ApplicationSurfaceSynthesisResult(
        entities=entity_fields.entities,
        views=tuple(views),
        actions=tuple(actions),
        capabilities=ordered_capabilities,
        persistence=persistence,
        provenance=tuple(provenance),
        uncertainties=tuple(uncertainties),
    )
