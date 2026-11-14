"""Slot reservation, planting states and bed clearing (REQ-053 WP 3.2, GP-FR-055/064–066, GP-API-019/021/022/024).

* :meth:`prepare_layout` turns the layout fields of a run's entries into the slots a bed gets (GP-FR-064) —
  pure compute on the bed's geometry, run **before** the run is stored so a refusal leaves nothing behind.
* :meth:`plan_slots` / :meth:`release_slot` set and drop the reservation of a run (GP-API-021/022). V-08 is
  checked here for the answer and again **inside** the write transaction (a reservation placed in between
  must not slip through).
* :meth:`pick_batch_slots` chooses the free slots of a succession plan's batches (GP-FR-074); they are then written
  through :meth:`reserve_slots`, the same path as ``plan-slots``, and dropped through :meth:`release_run_reservations`.
* :meth:`list_plantings` answers ``GET /locations/{key}/plantings`` (§11.3).
* :meth:`clear_bed` ends every live run and plant of a bed, archives its slots and logs ``clearing``
  (GP-FR-055). The care event is built by :class:`CareEventService` — its validation and stored shape —
  and written in the clearing's own transaction.

**Ownership is resolved here, never in the router** (T-01…T-04, #2107): every public method takes
``*, tenant_key: str`` without a default and resolves the bed or the run through
:mod:`app.domain.services.location_ownership` / ``verify_tenant_ownership`` before anything is read or
written. A foreign and an absent resource answer identically (404); a slot key of a body answers 422
``reference.not_found`` (GP-NFR-058).

**Logs carry no user text** (GP-NFR-060): keys, counts, codes.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from decimal import InvalidOperation
from typing import Any

import structlog
from pydantic import ValidationError as PydanticValidationError

from app.common.datetimes import today_utc
from app.common.enums import (
    GeometrySource,
    LayoutStrategy,
    PlantingRunStatus,
    RowDirection,
    SlotRole,
    TenantRole,
    TerminationType,
)
from app.common.exceptions import (
    ForbiddenError,
    InvalidRunStateError,
    NotFoundError,
    PlanError,
    PlanValidationError,
)
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.calculators.planting_layout_calculator import (
    EntryLayout,
    LayoutResult,
    LayoutSlot,
    LayoutWarning,
    compute_layout,
)
from app.domain.engines.garden_plan_engine import (
    ERROR_REFERENCE_NOT_FOUND,
    ERROR_SLOT_OUTSIDE_BED,
    ERROR_SLOT_OVERLAP,
    overlapping_zones,
    slots_outside_bed,
)
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.slot_reservation_engine import (
    PLANTING_STATES,
    ActivePlant,
    CandidateSlot,
    Reservation,
    SlotConflict,
    allocate_slot_ids,
    find_conflicts,
    pick_free_slots,
    slot_id_prefix,
)
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.planting_reservation_repository import IPlantingReservationRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.care_event import CareEvent, CareEventInput, CareEventOrigin
from app.domain.models.garden_plan import MAX_SLOTS_PER_BATCH, MAX_SLOTS_PER_SITE
from app.domain.models.geometry import PointGeometry, PolygonGeometry
from app.domain.models.planting_reservation import (
    ClearBedOutcome,
    ClearBedWrite,
    MixedRunsOutcome,
    MixedRunsWrite,
    NewReservedSlot,
    PlantingRow,
    ReservationReads,
    ReservationWrite,
    RunSlotsWrite,
)
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.site import Location, Slot
from app.domain.services.adjacency_service import AdjacencyDispatch, request_adjacency_recompute
from app.domain.services.care_event_service import CareEventService
from app.domain.services.location_ownership import resolve_owned_location, resolve_owned_slot
from app.domain.services.slot_occupancy import ERROR_SLOT_ALREADY_PLANNED

logger = structlog.get_logger()

ERROR_ALREADY_PLANNED = ERROR_SLOT_ALREADY_PLANNED
ERROR_SPACING_REQUIRED = "layout.spacing_required"
ERROR_QUOTA = "plan.quota_exceeded"
ERROR_NOT_ENOUGH_SLOTS = "succession.not_enough_slots"
#: Run key of a batch chosen in :meth:`PlantingReservationService.pick_batch_slots` but not stored yet.
_PENDING_BATCH = "pending-batch:"

#: Reservations that fill a run's entry are at most the positions one bed holds (GP-NFR-017).
MAX_RESERVED_SLOTS = MAX_SLOTS_PER_BATCH
#: Summary of the ``clearing`` care event; the UI renders the localised text from ``category`` and ``reason``.
CLEARING_SUMMARY = "Bed cleared ({termination_type})"
#: Summary of the ``position_corrected`` care event (GP-FR-068); the UI renders the localised text from ``category``.
POSITION_CORRECTED_SUMMARY = "Position corrected ({slot_id})"


@dataclass(frozen=True)
class PreparedSlot:
    """A slot of the layout of entry number ``entry_index``; ``sequence`` is the edge's, per entry."""

    entry_index: int
    slot: Slot
    sequence: int


@dataclass(frozen=True)
class PlannedSlots:
    """What ``plan_slots`` stored: the window and the slots with their ``sequence``."""

    run_key: str
    entry_key: str
    planned_from: date
    planned_until: date | None
    slots: list[tuple[str, int]]


@dataclass(frozen=True)
class BatchWindow:
    """One batch of a succession plan as a reservation asks for it: its window and how many plants it places."""

    planned_from: date
    planned_until: date | None
    needed: int


@dataclass(frozen=True)
class FreePlacement:
    """The points a grower set by hand for entry number ``entry_index`` (``free`` layout, GP-FR-072)."""

    entry_index: int
    points: tuple[tuple[float, float], ...]
    spacing_cm: float | None = None
    container_volume_l: float | None = None


@dataclass(frozen=True)
class PreparedLayout:
    slots: list[PreparedSlot]
    warnings: list[LayoutWarning]
    #: The bed's ``slot_rules_revision`` read with the slots V-04/V-06 ran against; the write hands it to its
    #: transaction, which refuses (409) when another slot or frame write of the bed landed since (#2773).
    slot_rules_revision: int


def entry_layout_of(entry: PlantingRunEntry, *, index: int = 0) -> EntryLayout | None:
    """The calculator input of an entry, or ``None`` when the entry plans no layout (none, or ``free``).

    ``free`` places the points by hand (GP-FR-072), so it creates no slots. A strategy without a spacing is
    refused: the calculator needs a distance, and the Steckbrief prefill is the dialog's job (GP-FR-061).
    """
    if entry.layout_strategy is None or entry.layout_strategy is LayoutStrategy.FREE:
        return None
    if entry.spacing_cm is None:
        raise PlanError(
            ERROR_SPACING_REQUIRED,
            "An entry with a layout strategy needs spacing_cm.",
            status_code=422,
            field=f"entries[{index}].spacing_cm",
            index=index,
        )
    return EntryLayout(
        layout_strategy=entry.layout_strategy,
        spacing_cm=entry.spacing_cm,
        row_spacing_cm=entry.row_spacing_cm,
        row_direction=entry.row_direction or RowDirection.ALONG_LENGTH,
        edge_margin_along_cm=entry.edge_margin_along_cm,
        edge_margin_across_cm=entry.edge_margin_across_cm,
        row_assignment=None if entry.row_assignment is None else tuple(entry.row_assignment),
    )


def _not_found(field: str) -> PlanValidationError:
    """422 ``reference.not_found`` — one text for a missing and for another tenant's key (GP-NFR-058)."""
    return PlanValidationError([(None, field, ERROR_REFERENCE_NOT_FOUND, {})])


class PlantingReservationService:
    def __init__(
        self,
        repo: IPlantingReservationRepository,
        run_repo: IPlantingRunRepository,
        site_repo: ISiteRepository,
        plan_repo: IGardenPlanRepository,
        care_events: CareEventService,
        dispatch_adjacency: AdjacencyDispatch | None = None,
    ) -> None:
        self._repo = repo
        self._runs = run_repo
        self._sites = site_repo
        self._plan = plan_repo
        self._care_events = care_events
        self._dispatch_adjacency = dispatch_adjacency

    def place_mixed_runs(self, write: MixedRunsWrite, *, tenant_key: str) -> MixedRunsOutcome:
        """Write the runs of a mixed culture in one transaction, then request the bed's adjacency recompute (#2463).

        The bed is resolved under ``tenant_key`` here as well: the write set was validated by the caller, but a
        write that stands on its own must not trust that (T-01…T-04).
        """
        location = resolve_owned_location(self._sites, write.location_key, tenant_key)
        outcome = self._repo.create_mixed_runs(write)
        request_adjacency_recompute(self._dispatch_adjacency, location.key or "")
        return outcome

    # ── Roles ─────────────────────────────────────────────────────────

    @staticmethod
    def _require_editor(role: TenantRole) -> None:
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")

    @staticmethod
    def _require_lead(role: TenantRole) -> None:
        if not MembershipEngine.can_delete_resource(role):
            raise ForbiddenError("Requires lead role.")

    # ── Anchors ───────────────────────────────────────────────────────

    def _owned_run(self, run_key: str, *, tenant_key: str) -> PlantingRun:
        run = self._runs.get_or_raise(run_key)
        verify_tenant_ownership(run, tenant_key, "PlantingRun")
        return run

    def _run_bed(self, run: PlantingRun, *, tenant_key: str) -> Location:
        """The bed a run reserves in; a run without one reserves nothing (422 ``run.without_location``)."""
        if not run.location_key:
            raise PlanError(
                "run.without_location",
                "The planting run has no location; set one before reserving slots.",
                status_code=422,
                field="location_key",
            )
        return resolve_owned_location(self._sites, run.location_key, tenant_key)

    @staticmethod
    def _window_of(run: PlantingRun) -> tuple[date, date | None]:
        """The window of a run: ``planned_from`` (default: the start date, else today) and ``planned_until``."""
        return run.planned_from or run.planned_start_date or today_utc(), run.planned_until

    # ── Layout (POST /planting-runs on a bed with geometry) ───────────

    def prepare_layout(
        self,
        location: Location,
        entries: list[PlantingRunEntry],
        *,
        tenant_key: str,
        free: Sequence[FreePlacement] = (),
    ) -> PreparedLayout | None:
        """The slots the entries' layouts need in ``location``, or ``None`` when nothing is to be placed.

        ``None`` for a bed without geometry (nothing to lay out on) and for entries without a layout strategy
        or with ``free`` — then ``POST /planting-runs`` stays what it was. Pure compute plus reads; nothing is
        written. The slots are new: a later run may take positions of an earlier one at a disjoint time through
        ``plan-slots``; a layout always adds its own.
        """
        layouts = [(index, entry, entry_layout_of(entry, index=index)) for index, entry in enumerate(entries)]
        planned = [(index, entry, layout) for index, entry, layout in layouts if layout is not None]
        placements = [placement for placement in free if placement.points]
        if (not planned and not placements) or location.geometry is None or not location.key:
            return None

        # The frame, the slots and the fence in one snapshot (#2773): the layout is computed in the frame read here,
        # and the write is refused when another slot or frame write of the bed lands after this read.
        basis = self._plan.load_slot_rule_basis(
            location.site_key, [location.key], tenant_key=tenant_key, include_archived=True
        )
        bed_key = location.key
        bed = basis.locations.get(bed_key)
        if bed is None:
            raise NotFoundError("Location", bed_key)
        frame = bed.geometry
        if frame is None:
            return None
        location = bed
        existing = basis.slots
        live = [slot for slot in existing if slot.archived_at is None]
        prefix = slot_id_prefix(location.name, bed_key)
        used_ids = {slot.slot_id for slot in existing}
        rank = max((slot.sequence or 0 for slot in existing), default=0)

        slots: list[PreparedSlot] = []
        warnings: list[LayoutWarning] = []
        results: list[tuple[int, PlantingRunEntry, LayoutResult]] = []
        for index, entry, layout in planned:
            result = compute_layout(frame, layout, entry.quantity)
            results.append((index, entry, result))
            warnings.extend(result.warnings)
        total = sum(len(result.slots) for _, _, result in results) + sum(len(p.points) for p in placements)
        self._check_quota(location, current=len(live), adding=total, tenant_key=tenant_key)

        ids = allocate_slot_ids(prefix, used_ids, total)
        cursor = 0
        for index, entry, result in results:
            for layout_slot in result.slots:
                slots.append(
                    PreparedSlot(
                        entry_index=index,
                        slot=self._slot_of(location, layout_slot, entry, ids[cursor], rank + cursor + 1),
                        sequence=layout_slot.sequence,
                    )
                )
                cursor += 1
        slots += self._free_slots(location, placements, ids[cursor:], rank + cursor)
        self._check_free_points_inside(location, slots)
        self._check_zone_overlap(slots, live)
        return PreparedLayout(slots=slots, warnings=warnings, slot_rules_revision=basis.revisions[location.key or ""])

    def _free_slots(
        self, location: Location, placements: Sequence[FreePlacement], ids: list[str], rank: int
    ) -> list[PreparedSlot]:
        """The slots of the hand-set points, in the order of the placements and their points."""
        flat = [
            (placement, sequence, point)
            for placement in placements
            for sequence, point in enumerate(placement.points, 1)
        ]
        try:
            return [
                PreparedSlot(
                    entry_index=placement.entry_index,
                    slot=self._free_slot_of(location, point, placement, ids[offset], rank + offset + 1),
                    sequence=sequence,
                )
                for offset, (placement, sequence, point) in enumerate(flat)
            ]
        except PydanticValidationError, InvalidOperation, OverflowError:
            raise PlanValidationError([(None, "free_points", "geometry.invalid", {})]) from None

    @staticmethod
    def _free_slot_of(
        location: Location, point: tuple[float, float], placement: FreePlacement, slot_id: str, rank: int
    ) -> Slot:
        return Slot(
            slot_id=slot_id,
            location_key=location.key or "",
            capacity_plants=1,
            slot_role=SlotRole.POSITION,
            geometry=PointGeometry(origin=point),
            sequence=rank,
            geometry_source=GeometrySource.EDITOR,
            container_volume_l=placement.container_volume_l,
            planned_spacing_cm=placement.spacing_cm if placement.spacing_cm and placement.spacing_cm > 0 else None,
        )

    @staticmethod
    def _check_free_points_inside(location: Location, prepared: list[PreparedSlot]) -> None:
        """V-04 for the points set by hand: a position outside the bed is refused (computed layouts stay inside)."""
        if location.geometry is None:
            return
        subjects = [
            (f"#{index}", item.slot.geometry)
            for index, item in enumerate(prepared)
            if item.slot.geometry_source is GeometrySource.EDITOR and item.slot.geometry is not None
        ]
        outside = slots_outside_bed(location.geometry, subjects)
        if outside:
            raise PlanValidationError([(None, "free_points", ERROR_SLOT_OUTSIDE_BED, {"key": key}) for key in outside])

    @staticmethod
    def _slot_of(location: Location, layout_slot: LayoutSlot, entry: PlantingRunEntry, slot_id: str, rank: int) -> Slot:
        geometry: PointGeometry | PolygonGeometry
        if layout_slot.point is not None:
            geometry = PointGeometry(origin=layout_slot.point)
        else:
            geometry = PolygonGeometry(points=tuple(layout_slot.outline or ()))
        return Slot(
            slot_id=slot_id,
            location_key=location.key or "",
            capacity_plants=layout_slot.capacity_plants,
            slot_role=layout_slot.slot_role,
            geometry=geometry,
            row_index=layout_slot.row_index,
            sequence=rank,
            geometry_source=GeometrySource.LAYOUT,
            planned_spacing_cm=entry.spacing_cm if entry.spacing_cm and entry.spacing_cm > 0 else None,
        )

    def _check_quota(self, location: Location, *, current: int, adding: int, tenant_key: str) -> None:
        """GP-NFR-017: at most 2 000 slots per bed and 8 000 per site."""
        if current + adding > MAX_SLOTS_PER_BATCH:
            raise PlanError(
                ERROR_QUOTA,
                f"A bed holds at most {MAX_SLOTS_PER_BATCH} slots.",
                status_code=422,
                limit=MAX_SLOTS_PER_BATCH,
                current=current + adding,
            )
        site_total = self._plan.count_active_slots(location.site_key, tenant_key=tenant_key)
        if site_total + adding > MAX_SLOTS_PER_SITE:
            raise PlanError(
                ERROR_QUOTA,
                f"A site holds at most {MAX_SLOTS_PER_SITE} slots.",
                status_code=422,
                limit=MAX_SLOTS_PER_SITE,
                current=site_total + adding,
            )

    @staticmethod
    def _check_zone_overlap(prepared: list[PreparedSlot], live: list[Slot]) -> None:
        """V-06: a new zone may not overlap a zone that is active or planned in the bed (archived ones do not count)."""
        zones = [(f"#{i}", p.slot.geometry) for i, p in enumerate(prepared) if p.slot.slot_role is SlotRole.ZONE]
        if not zones:
            return
        neighbours = [(slot.key or "", slot.geometry) for slot in live if slot.geometry is not None]
        pairs = overlapping_zones([(key, geometry) for key, geometry in [*zones, *neighbours] if geometry is not None])
        subject_keys = {key for key, _ in zones}
        findings: list[tuple[int | None, str, str, dict[str, Any]]] = [
            (None, "geometry", ERROR_SLOT_OVERLAP, {"key": first if first in subject_keys else second})
            for first, second in pairs
            if first in subject_keys or second in subject_keys
        ]
        if findings:
            raise PlanValidationError(findings)

    def place_layout(
        self,
        location: Location,
        run: PlantingRun,
        entries: list[PlantingRunEntry],
        prepared: PreparedLayout,
        *,
        tenant_key: str,
    ) -> list[str]:
        """Write the prepared slots and their edges for the stored ``run`` and its stored ``entries``.

        ``location`` came from :meth:`prepare_layout`'s caller, who resolved it under the tenant; the run is
        checked against the same tenant here so a run of another tenant can never be given slots.
        """
        verify_tenant_ownership(run, tenant_key, "PlantingRun")
        planned_from, planned_until = self._window_of(run)
        reserved = [
            NewReservedSlot(
                slot=item.slot,
                entry_key=entries[item.entry_index].key or "",
                planned_species_key=entries[item.entry_index].species_key,
                sequence=item.sequence,
            )
            for item in prepared.slots
        ]
        keys = self._repo.place_run_layout(
            RunSlotsWrite(
                location_key=location.key or "",
                run_key=run.key or "",
                planned_from=planned_from,
                planned_until=planned_until,
                slots=reserved,
                slot_rules_revision=prepared.slot_rules_revision,
            )
        )
        logger.info("planting_reservation.layout_placed", run_key=run.key, location_key=location.key, slots=len(keys))
        request_adjacency_recompute(self._dispatch_adjacency, location.key or "")
        return keys

    # ── GP-API-021: POST /planting-runs/{key}/plan-slots ──────────────

    def plan_slots(
        self,
        run_key: str,
        *,
        tenant_key: str,
        role: TenantRole,
        entry_key: str,
        slot_keys: list[str],
    ) -> PlannedSlots:
        """Set (replace) the run's reservation for one entry; the window and ``(slot_key, sequence)`` as stored.

        ``slot_keys`` must be unarchived slots of the run's bed (GP-NFR-058). V-08: a slot with an overlapping
        reservation of another run, or with a plant whose run ends after ``planned_from``, is 409
        ``slot.already_planned {conflicting_run_key, overlap_from, overlap_until}``. An empty list releases the
        entry's reservation.
        """
        self._require_editor(role)
        return self.reserve_slots(run_key, tenant_key=tenant_key, entry_key=entry_key, slot_keys=slot_keys)

    def reserve_slots(
        self,
        run_key: str,
        *,
        tenant_key: str,
        entry_key: str,
        slot_keys: list[str],
    ) -> PlannedSlots:
        """:meth:`plan_slots` without the role check, for a caller whose own route already gated the role.

        The one write path of a reservation: a succession plan's batches (GP-FR-074) reserve through here, so
        ownership, the slot set of the bed and V-08 (before and inside the transaction) are the same checks.
        """
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status in (PlantingRunStatus.COMPLETED, PlantingRunStatus.CANCELLED):
            raise InvalidRunStateError("plan_slots", run.status.value)
        location = self._run_bed(run, tenant_key=tenant_key)
        entry = self._entry_of_run(run_key, entry_key)
        self._check_slot_keys(slot_keys, location, tenant_key=tenant_key)

        planned_from, planned_until = self._window_of(run)

        def verify(reads: ReservationReads) -> None:
            conflicts = find_conflicts(
                slot_keys,
                run_key=run_key,
                entry_key=entry_key,
                planned_from=planned_from,
                planned_until=planned_until,
                reservations=reads.reservations_for(slot_keys, tenant_key=tenant_key),
                plants=reads.active_plants_in(slot_keys, tenant_key=tenant_key),
            )
            if conflicts:
                raise self._already_planned(conflicts)

        # The same check first without a transaction: the common refusal costs no lock.
        verify(_DirectReads(self._repo))
        self._repo.set_reservation(
            ReservationWrite(
                location_key=location.key or "",
                run_key=run_key,
                entry_key=entry_key,
                planned_species_key=entry.species_key,
                ordered_slot_keys=slot_keys,
                planned_from=planned_from,
                planned_until=planned_until,
                tenant_key=tenant_key,
            ),
            verify,
        )
        logger.info("planting_reservation.slots_planned", run_key=run_key, entry_key=entry_key, slots=len(slot_keys))
        request_adjacency_recompute(self._dispatch_adjacency, location.key or "")
        return PlannedSlots(
            run_key=run_key,
            entry_key=entry_key,
            planned_from=planned_from,
            planned_until=planned_until,
            slots=[(slot_key, sequence) for sequence, slot_key in enumerate(slot_keys, start=1)],
        )

    # ── GP-FR-074: the slots of a succession plan's batches ───────────

    def pick_batch_slots(
        self, location_key: str, windows: Sequence[BatchWindow], *, tenant_key: str
    ) -> list[list[str]]:
        """The slots each window reserves in the bed, in the order of ``windows``; nothing is written.

        Candidates are the bed's unarchived slots in ``sequence`` order. A window takes the first slots that are
        free in it (V-08) until their capacity holds its plants; a slot chosen for an earlier window counts as
        reserved for the later ones, so overlapping batches take different slots and disjoint ones may share.
        A bed without slots reserves nothing (an empty list per window). A bed whose positions together hold
        fewer plants than a window needs is 422 ``succession.not_enough_slots``; enough positions that are taken
        in the window are 409 ``slot.already_planned`` — both before anything is written.
        """
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        slots = self._plan.load_active_slots(
            location.site_key, [location.key or location_key], tenant_key=tenant_key, include_archived=False
        )
        candidates = [
            CandidateSlot(slot_key=slot.key, capacity=slot.capacity_plants)
            for slot in sorted(slots, key=lambda s: (s.sequence is None, s.sequence or 0, s.slot_id))
            if slot.key
        ]
        if not candidates:
            return [[] for _ in windows]
        capacity = sum(max(candidate.capacity, 1) for candidate in candidates)
        keys = [candidate.slot_key for candidate in candidates]
        reservations = self._repo.reservations_for(keys, tenant_key=tenant_key)
        plants = self._repo.active_plants_in(keys, tenant_key=tenant_key)
        picks: list[list[str]] = []
        for index, window in enumerate(windows):
            if window.needed > capacity:
                raise PlanError(
                    ERROR_NOT_ENOUGH_SLOTS,
                    "The bed has fewer positions than one batch needs.",
                    status_code=422,
                    field="plants_per_batch",
                    needed=window.needed,
                    available=capacity,
                )
            pick = pick_free_slots(
                candidates,
                needed=window.needed,
                planned_from=window.planned_from,
                planned_until=window.planned_until,
                reservations=reservations,
                plants=plants,
            )
            if not pick.chosen:
                # A batch of this same request holds no stored run yet: there is no key to name.
                raise self._already_planned(
                    [
                        replace(c, conflicting_run_key=None)
                        if (c.conflicting_run_key or "").startswith(_PENDING_BATCH)
                        else c
                        for c in pick.conflicts
                    ]
                )
            picks += [pick.chosen]
            # The batch is not stored yet; its pick holds the slots for the batches after it.
            reservations = reservations + [
                Reservation(
                    slot_key=slot_key,
                    run_key=f"{_PENDING_BATCH}{index}",
                    entry_key="",
                    planned_species_key="",
                    sequence=sequence,
                    planned_from=window.planned_from,
                    planned_until=window.planned_until,
                )
                for sequence, slot_key in enumerate(pick.chosen, start=1)
            ]
        return picks

    def release_run_reservations(self, run_key: str, *, tenant_key: str) -> int:
        """Drop every reservation of a ``planned`` run of the tenant; the slots stay (GP-FR-074 plan change).

        Role-free like :meth:`reserve_slots`: the caller's route gated the role. A run that already started keeps
        its reservations (they place its plants), so only a planned run is released here.
        """
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status is not PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("release_reservations", run.status.value)
        dropped = self._repo.drop_run_reservations(run_key, remove_layout_slots=False)
        if dropped and run.location_key:
            request_adjacency_recompute(self._dispatch_adjacency, run.location_key)
        logger.info("planting_reservation.run_released", run_key=run_key, edges=dropped)
        return dropped

    @staticmethod
    def _already_planned(conflicts: list[SlotConflict]) -> PlanError:
        first = conflicts[0]
        detail = first.as_detail()
        return PlanError(
            ERROR_ALREADY_PLANNED,
            "A slot is already planned or planted in that time window.",
            status_code=409,
            field="slot_keys",
            slot_key=first.slot_key,
            conflicting_run_key=detail["conflicting_run_key"],
            overlap_from=detail["overlap_from"],
            overlap_until=detail["overlap_until"],
            conflicts=[c.as_detail() for c in conflicts[:50]],
        )

    def _entry_of_run(self, run_key: str, entry_key: str) -> PlantingRunEntry:
        """The entry ``entry_key`` of the run; another run's entry and an absent one are 422 ``reference.not_found``."""
        try:
            entry = self._runs.get_entry_or_raise(entry_key)
        except NotFoundError:
            raise _not_found("entry_key") from None
        if entry.run_key != run_key:
            raise _not_found("entry_key")
        return entry

    def _check_slot_keys(self, slot_keys: list[str], location: Location, *, tenant_key: str) -> None:
        """``slot_keys`` ⊆ the unarchived slots of the run's bed, no repeats, at most one bed's worth (GP-NFR-058)."""
        if len(slot_keys) > MAX_RESERVED_SLOTS:
            raise PlanError(
                ERROR_QUOTA,
                f"A reservation holds at most {MAX_RESERVED_SLOTS} slots.",
                status_code=422,
                limit=MAX_RESERVED_SLOTS,
                current=len(slot_keys),
            )
        if len(set(slot_keys)) != len(slot_keys):
            raise PlanValidationError([(None, "slot_keys", "slot.duplicate_key", {})])
        if not slot_keys:
            return
        usable = {
            slot.key
            for slot in self._plan.load_active_slots(
                location.site_key, [location.key or ""], tenant_key=tenant_key, include_archived=False
            )
        }
        if not set(slot_keys) <= usable:
            raise _not_found("slot_keys")

    # ── GP-API-022: DELETE /planting-runs/{key}/plan-slots/{slot_key} ─

    def release_slot(self, run_key: str, slot_key: str, *, tenant_key: str, role: TenantRole) -> None:
        """Release one reservation. A grower may while the run is ``planned``; afterwards only the lead (SR-010)."""
        self._require_editor(role)
        run = self._owned_run(run_key, tenant_key=tenant_key)
        if run.status is not PlantingRunStatus.PLANNED:
            self._require_lead(role)
        slot, location = resolve_owned_slot(self._sites, slot_key, tenant_key)
        if location.key != run.location_key:
            raise NotFoundError("Slot", slot_key)
        if not self._repo.release_reservation(run_key, slot.key or slot_key):
            raise NotFoundError("Slot", slot_key)
        logger.info("planting_reservation.slot_released", run_key=run_key, slot_key=slot_key)
        request_adjacency_recompute(self._dispatch_adjacency, location.key or "")

    # ── GP-API-024: GET /locations/{key}/plantings ────────────────────

    def list_plantings(
        self,
        location_key: str,
        *,
        tenant_key: str,
        state: str | None,
        year: int | None,
        offset: int,
        limit: int,
    ) -> list[PlantingRow]:
        """A window of the bed's planned positions and plants (§11.3), optionally of one state and one year."""
        resolve_owned_location(self._sites, location_key, tenant_key)
        if state is not None and state not in PLANTING_STATES:
            raise PlanValidationError([(None, "state", "plantings.unknown_state", {"allowed": list(PLANTING_STATES)})])
        rows = self._repo.list_plantings(location_key, tenant_key=tenant_key, state=state, year=year)
        return rows[offset : offset + limit]

    # ── GP-FR-068: the care event of a corrected plant position ───────

    def record_position_correction(
        self,
        slot_key: str,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
    ) -> str | None:
        """Log ``care_event(position_corrected)`` for the plants standing in the slot; its key, or ``None``.

        "Correct position" moves the slot of a plant (slot and plant are 1:1, GP-FR-068), so the history
        names the plant. A slot nobody stands in (a planned or empty position) moved no plant: nothing to log.
        The event is server-only (``trigger = system``), a client cannot write it (SR-009).
        """
        self._require_editor(role)
        slot, location = resolve_owned_slot(self._sites, slot_key, tenant_key)
        plants = self._repo.active_plants_in([slot.key or slot_key], tenant_key=tenant_key)
        if not plants:
            return None
        view = self._care_events.create(
            CareEventInput(
                location_key=location.key or "",
                category="position_corrected",
                summary=POSITION_CORRECTED_SUMMARY.format(slot_id=slot.slot_id),
                plant_keys=sorted({plant.plant_key for plant in plants}),
                performed_at=datetime.now(UTC),
            ),
            tenant_key=tenant_key,
            user_key=user_key,
            role=role,
            origin=CareEventOrigin(trigger="system"),
        )
        logger.info("planting_reservation.position_corrected", slot_key=slot_key, plants=len(plants))
        return view.event.key

    # ── GP-API-019: POST /locations/{key}/clear ───────────────────────

    def clear_bed(
        self,
        location_key: str,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        termination_type: TerminationType,
        reason: str | None,
    ) -> ClearBedOutcome:
        """End every live run and plant of the bed, archive its slots and log a ``clearing`` care event.

        One transaction (GP-FR-055). The event is validated and shaped by :class:`CareEventService`
        (``trigger = system``, server-only category) and written with the rest.
        """
        self._require_editor(role)
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        now = datetime.now(UTC)
        event: CareEvent = self._care_events.build_event(
            CareEventInput(
                location_key=location_key,
                category="clearing",
                summary=CLEARING_SUMMARY.format(termination_type=termination_type.value),
                performed_at=now,
                reason=reason.strip() if reason and reason.strip() else None,
            ),
            tenant_key=tenant_key,
            user_key=user_key,
            role=role,
            origin=CareEventOrigin(trigger="system"),
        )
        outcome = self._repo.clear_bed(
            ClearBedWrite(
                location_key=location.key or location_key,
                tenant_key=tenant_key,
                termination_type=termination_type.value,
                removed_on=now.date(),
                event=event,
            )
        )
        logger.info(
            "planting_reservation.bed_cleared",
            location_key=location_key,
            termination_type=termination_type.value,
            plants=outcome.plants_removed,
            runs=outcome.runs_completed,
            archived=outcome.slots_archived,
        )
        request_adjacency_recompute(self._dispatch_adjacency, location.key or location_key)
        return outcome


class _DirectReads:
    """The V-08 reads against the database, for the check made before the transaction opens."""

    def __init__(self, repo: IPlantingReservationRepository) -> None:
        self._repo = repo

    def reservations_for(self, slot_keys: list[str], *, tenant_key: str) -> list[Reservation]:
        return self._repo.reservations_for(slot_keys, tenant_key=tenant_key)

    def active_plants_in(self, slot_keys: list[str], *, tenant_key: str) -> list[ActivePlant]:
        return self._repo.active_plants_in(slot_keys, tenant_key=tenant_key)
