"""Slot neighbourhood of a bed (REQ-053 GP-FR-130, SR-021, GP-NFR-016).

* :meth:`AdjacencyService.recompute` re-derives the ``adjacent_to`` edges of one bed from its slots'
  geometry (:mod:`app.domain.engines.adjacency_engine`) and reconciles them with the stored edges:
  derived edges follow the geometry, ``source = manual`` edges stay. It is idempotent, so the Celery task
  that runs it may be delivered twice or overlap another run of the same bed.
* :meth:`AdjacencyService.set_manual_edge` / :meth:`~AdjacencyService.remove_manual_edge` are the only way
  a user sets or removes a neighbourhood. Both ends must belong to the caller's tenant **and** to the same
  site (SR-021): a payload naming a slot of another site is refused before anything is written.

Every method takes ``*, tenant_key`` without a default and resolves ownership through the anchor
(:mod:`app.domain.services.location_ownership`); a slot has no tenant of its own (#2107). The task that
triggers a recompute is handed only a ``location_key`` and resolves site and tenant itself
(:func:`app.tasks.adjacency.adjacency_recompute`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import structlog

from app.common.enums import GrowthHabit, TenantRole
from app.common.exceptions import ForbiddenError, PlanError
from app.common.types import LocationKey, SlotKey
from app.domain.engines.adjacency_engine import (
    WOODY_HABITS,
    AdjacencyNode,
    derive_adjacency,
    lower_bound_cm,
)
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.graph_repository import (
    ADJACENCY_SOURCE_MANUAL,
    AdjacencySync,
    IGraphRepository,
)
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.garden_plan import SlotSpeciesHint
from app.domain.models.site import DEFAULT_ADJACENCY_FACTOR, Slot
from app.domain.services.location_ownership import resolve_owned_location, resolve_owned_slot

logger = structlog.get_logger()

#: Starts a recompute of the bed with this key out of band (the Celery task); injected, so the domain
#: stays free of the task queue and a unit test sees the dispatch without a broker.
AdjacencyDispatch = Callable[[str], None]

WOODY_VALUES = frozenset(habit.value for habit in WOODY_HABITS)


def request_adjacency_recompute(dispatch: AdjacencyDispatch | None, location_key: str) -> None:
    """Ask for the recompute of a bed after a committed slot change (GP-NFR-016); never raises.

    Out of band and after the write: a broker that is down must not turn a stored slot into an error, and
    the derivation is idempotent, so the next slot change repairs a dispatch that was lost.
    """
    if dispatch is None or not location_key:
        return
    try:
        dispatch(location_key)
    except Exception as exc:  # noqa: BLE001 — a lost dispatch must not fail the committed write
        logger.warning("adjacency.dispatch_failed", location_key=location_key, error_type=type(exc).__name__)


ERROR_SELF_EDGE = "adjacency.same_slot"
ERROR_OTHER_SITE = "adjacency.different_site"
#: Largest ``distance_cm`` a manual edge may carry (a bed is at most 1000 m across; the spec's coordinates).
MAX_MANUAL_DISTANCE_CM = 100_000.0


@dataclass(frozen=True)
class AdjacencyResult:
    """What a recompute did: the neighbour pairs derived and the directed edges changed."""

    location_key: str
    pairs: int
    sync: AdjacencySync


@dataclass(frozen=True)
class _SpeciesFields:
    spacing_cm: float | None
    row_spacing_cm: float | None
    mature_width_cm: float | None
    growth_habit: GrowthHabit | None


def _merge_hints(hints: list[SlotSpeciesHint]) -> _SpeciesFields:
    """Merge the species of one slot: the widest spacing and width, woody as soon as one species is."""
    spacings = [v for v in (lower_bound_cm(h.spacing_cm) for h in hints) if v is not None]
    rows = [v for v in (lower_bound_cm(h.row_spacing_cm) for h in hints) if v is not None]
    widths = [lower_bound_cm(h.mature_width_cm) for h in hints]
    woody = next((GrowthHabit(h.growth_habit) for h in hints if h.growth_habit in WOODY_VALUES), None)
    return _SpeciesFields(
        spacing_cm=max(spacings) if spacings else None,
        row_spacing_cm=max(rows) if rows else None,
        # An interaction radius needs the width of every species in the slot; one unknown voids it.
        mature_width_cm=max(w for w in widths if w is not None) if widths and None not in widths else None,
        growth_habit=woody,
    )


class AdjacencyService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        plan_repo: IGardenPlanRepository,
        graph_repo: IGraphRepository,
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._graph = graph_repo

    # ── Derived edges (GP-FR-130) ─────────────────────────────────────────────

    def recompute(self, location_key: LocationKey, *, tenant_key: str) -> AdjacencyResult:
        """Re-derive the ``adjacent_to`` edges among the slots of one bed; manual edges stay."""
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        site = self._sites.get_site_by_key(location.site_key)
        factor = site.plan.adjacency_factor if site is not None and site.plan is not None else DEFAULT_ADJACENCY_FACTOR
        slots = self._plan.load_active_slots(
            location.site_key, [location_key], tenant_key=tenant_key, include_archived=True
        )
        hints_by_slot: dict[str, list[SlotSpeciesHint]] = {}
        for hint in self._plan.load_slot_species_hints(location_key, tenant_key=tenant_key):
            hints_by_slot.setdefault(hint.slot_key, []).append(hint)

        nodes = [
            self._node_of(slot, hints_by_slot.get(slot.key or "", []))
            for slot in slots
            if slot.key and slot.geometry is not None and slot.archived_at is None
        ]
        pairs = derive_adjacency(nodes, factor)
        sync = self._graph.sync_derived_adjacency(
            [slot.key for slot in slots if slot.key],
            [(pair.slot_a_key, pair.slot_b_key, pair.distance_cm) for pair in pairs],
        )
        logger.info(
            "adjacency.recomputed",
            location_key=location_key,
            slots=len(nodes),
            pairs=len(pairs),
            created=sync.created,
            updated=sync.updated,
            removed=sync.removed,
        )
        return AdjacencyResult(location_key=location_key, pairs=len(pairs), sync=sync)

    @staticmethod
    def _node_of(slot: Slot, hints: list[SlotSpeciesHint]) -> AdjacencyNode:
        merged = _merge_hints(hints)
        assert slot.key is not None and slot.geometry is not None  # noqa: S101 — filtered by the caller
        return AdjacencyNode(
            key=slot.key,
            role=slot.slot_role,
            geometry=slot.geometry,
            spacing_cm=slot.planned_spacing_cm if slot.planned_spacing_cm is not None else merged.spacing_cm,
            row_spacing_cm=merged.row_spacing_cm,
            mature_width_cm=merged.mature_width_cm,
            growth_habit=merged.growth_habit,
        )

    # ── Manual edges (SR-021) ─────────────────────────────────────────────────

    @staticmethod
    def _require_editor(role: TenantRole) -> None:
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")

    def _both_ends(self, slot_a_key: SlotKey, slot_b_key: SlotKey, *, tenant_key: str) -> tuple[Slot, Slot]:
        """Both slots, each resolved under the tenant, and on one site (SR-021).

        A slot of another tenant answers 404 exactly like an unknown one; a slot of another site of the
        *same* tenant is a 422 of the caller's own making.
        """
        if slot_a_key == slot_b_key:
            raise PlanError(
                ERROR_SELF_EDGE, "A slot cannot be adjacent to itself.", status_code=422, field="other_slot_key"
            )
        first, first_location = resolve_owned_slot(self._sites, slot_a_key, tenant_key)
        second, second_location = resolve_owned_slot(self._sites, slot_b_key, tenant_key)
        if first_location.site_key != second_location.site_key:
            raise PlanError(
                ERROR_OTHER_SITE,
                "Both slots of an adjacency must belong to the same site.",
                status_code=422,
                field="other_slot_key",
            )
        for slot in (first, second):
            if slot.archived_at is not None:
                raise PlanError(
                    "adjacency.slot_archived",
                    "An archived slot is history; it cannot be given a neighbour.",
                    status_code=422,
                    field="other_slot_key",
                )
        return first, second

    def set_manual_edge(
        self,
        slot_a_key: SlotKey,
        slot_b_key: SlotKey,
        *,
        tenant_key: str,
        role: TenantRole,
        distance_cm: float | None,
    ) -> None:
        """Record that two slots of one site are neighbours, whatever their geometry says (``source = manual``)."""
        self._require_editor(role)
        first, second = self._both_ends(slot_a_key, slot_b_key, tenant_key=tenant_key)
        if distance_cm is not None and not 0 <= distance_cm <= MAX_MANUAL_DISTANCE_CM:
            raise PlanError(
                "adjacency.distance_out_of_range",
                f"distance_cm must lie within 0..{MAX_MANUAL_DISTANCE_CM:g}.",
                status_code=422,
                field="distance_cm",
            )
        self._graph.set_adjacent_slots(
            first.key or slot_a_key, second.key or slot_b_key, distance_cm=distance_cm, source=ADJACENCY_SOURCE_MANUAL
        )
        logger.info("adjacency.manual_set", slot_a_key=slot_a_key, slot_b_key=slot_b_key)

    def remove_manual_edge(
        self, slot_a_key: SlotKey, slot_b_key: SlotKey, *, tenant_key: str, role: TenantRole
    ) -> bool:
        """Remove the manual neighbourhood of two slots; ``False`` when there was none (derived edges stay)."""
        self._require_editor(role)
        first, second = self._both_ends(slot_a_key, slot_b_key, tenant_key=tenant_key)
        removed = self._graph.remove_manual_adjacency(first.key or slot_a_key, second.key or slot_b_key)
        logger.info("adjacency.manual_removed", slot_a_key=slot_a_key, slot_b_key=slot_b_key, removed=removed)
        return removed > 0
