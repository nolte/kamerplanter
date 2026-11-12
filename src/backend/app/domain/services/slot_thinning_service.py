"""Sowing a row or zone and thinning it into plants (REQ-053 §11.3 "gesät", §12 ``thinning``, Anhang A 60, W-015).

Direct sowing in a ``row``/``zone`` slot creates no plant per seed: the slot records the sowing day (``sown_at``) and
the plan shows it as *sown*. **Thinning** ("Vereinzeln") turns it into plants: their number follows from the slot's
length or area and the spacing the seedlings are thinned to
(:func:`~app.domain.calculators.thinning_calculator.thinning_count`), the plants stand in the slot as plants of the
run that reserved it, ``sown_at`` is cleared and a ``thinning`` care event names them — one transaction.

**No agronomic default** (E-10): the spacing is the run entry's ``thinning_to_cm``, else the grower's value in the
request; without either and without an explicit ``count`` the request is refused with
``thinning.spacing_required`` (422) and the dialog asks for it. A zone's row spacing (#2862) is the grower's value,
else the run entry's ``row_spacing_cm``, else the lower value of the species profile's ``row_spacing_cm`` (GP-FR-061);
without one the zone is counted on the square-grid estimate — no row spacing is ever made up.

**Ownership is resolved here, never in the router** (#2107): every method takes ``*, tenant_key: str`` without a
default and resolves the slot through its bed and site (:func:`resolve_owned_slot`; a slot carries no tenant) — a
foreign and an absent slot answer alike (404). The reserving run is read under the same tenant. Writes need the
grower role (403 for a viewer), checked here as well as at the route.

**Logs carry no user text** (GP-NFR-060): keys and counts only.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time

import structlog

from app.common.datetimes import today_utc
from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError, WriteConflictError
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.calculators.range_parser import parse_range_lower
from app.domain.calculators.thinning_calculator import SOWABLE_ROLES, sown_measure, thinning_count, thinning_formula
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.engines.slot_reservation_engine import LIVE_RUN_STATUSES, Reservation
from app.domain.interfaces.planting_reservation_repository import IPlantingReservationRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.care_event import CareEventInput, CareEventOrigin
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_reservation import (
    MAX_THINNING_SPACING_CM,
    QUICK_PLANTING_MAX_QUANTITY,
    QuickPlantedPlant,
    RowSpacingSource,
    SlotThinningInput,
    SlotThinningOutcome,
    SlotThinningPlan,
    SlotThinningWrite,
)
from app.domain.models.planting_run import MAX_SPACING_CM, MIN_ROW_SPACING_CM, PlantingRun, PlantingRunEntry
from app.domain.models.site import Slot
from app.domain.models.species import Species
from app.domain.services.care_event_service import CareEventService
from app.domain.services.location_ownership import resolve_owned_slot
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.species_visibility import readable_species

logger = structlog.get_logger()

#: The summary of the ``thinning`` care event; data, not prose (no user text).
THINNING_SUMMARY = "Thinned slot {slot_id} to {count} plants"
#: A sowing day may lie this many days back: two years cover an overwintering or biennial direct sowing recorded late
#: (agrobiology review of WP 10.9); older is no sowing of this slot's crop.
MAX_SOWING_AGE_DAYS = 730

ERROR_NOT_SOWABLE = "slot.not_sowable"
ERROR_NOT_SOWN = "slot.not_sown"
ERROR_OCCUPIED = "slot.occupied"
ERROR_NO_RUN = "thinning.no_run"
ERROR_SPACING_REQUIRED = "thinning.spacing_required"
ERROR_NO_MEASURE = "thinning.no_measure"
ERROR_TOO_MANY = "plan.quota_exceeded"
ERROR_SOWN_IN_FUTURE = "slot.sown_in_future"
ERROR_SOWN_TOO_LONG_AGO = "slot.sown_too_long_ago"
ERROR_PLANTED_IN_FUTURE = "thinning.planted_in_future"
ERROR_SPACING_RANGE = "thinning.spacing_out_of_range"


class SlotThinningService:
    def __init__(
        self,
        sites: ISiteRepository,
        reservations: IPlantingReservationRepository,
        runs: IPlantingRunRepository,
        run_service: PlantingRunService,
        care_events: CareEventService,
        species: ISpeciesRepository,
        engine: PlantingRunEngine | None = None,
    ) -> None:
        self._sites = sites
        self._species = species
        self._reservations = reservations
        self._runs = runs
        self._run_service = run_service
        self._care_events = care_events
        self._engine = engine or PlantingRunEngine()

    # ── Sowing ────────────────────────────────────────────────────────

    def mark_sown(self, slot_key: str, *, tenant_key: str, role: TenantRole, sown_at: date) -> Slot:
        """Record the direct sowing of a ``row``/``zone`` slot the tenant's live run reserves (§11.3 "gesät").

        Raises:
            ForbiddenError: a viewer (403).
            NotFoundError: the slot is not the tenant's (404).
            PlanError: the slot is a position (422 ``slot.not_sowable``), plants stand in it (409 ``slot.occupied``).
            PlanValidationError: the day lies in the future or more than two years back (422).
        """
        self._require_editor(role)
        slot, location = resolve_owned_slot(self._sites, slot_key, tenant_key)
        self._require_sowable(slot)
        today = today_utc()
        if sown_at > today:
            raise PlanValidationError([(None, "sown_at", ERROR_SOWN_IN_FUTURE, {})])
        if (today - sown_at).days > MAX_SOWING_AGE_DAYS:
            raise PlanValidationError([(None, "sown_at", ERROR_SOWN_TOO_LONG_AGO, {"max_days": MAX_SOWING_AGE_DAYS})])
        self._live_reservation(slot, tenant_key)
        self._require_no_plant(slot, tenant_key)
        stored_key = slot.key or slot_key
        if not self._reservations.mark_slot_sown(
            location.key or slot.location_key, stored_key, sown_at=sown_at, tenant_key=tenant_key
        ):
            raise PlanError(ERROR_OCCUPIED, "The slot changed while it was being sown.", status_code=409)
        logger.info("slot.sown", slot_key=stored_key)
        stored = self._sites.get_slot_by_key(stored_key)
        if stored is None:
            raise NotFoundError("Slot", slot_key)
        return stored

    # ── Thinning ──────────────────────────────────────────────────────

    def plan_thinning(self, slot_key: str, *, tenant_key: str) -> SlotThinningPlan:
        """What thinning the sown slot would do: the run's spacing (or ``None``) and the count it gives. All roles."""
        slot, _location = resolve_owned_slot(self._sites, slot_key, tenant_key)
        sown_at = self._require_sown(slot)
        reservation = self._live_reservation(slot, tenant_key)
        _run, entry, species = self._run_and_entry(reservation, tenant_key)
        measure = sown_measure(slot.slot_role, slot.geometry)
        spacing = entry.thinning_to_cm
        row_spacing, row_source = _row_spacing_of(entry, species)
        suggested = (
            thinning_count(measure, spacing, row_spacing) if measure is not None and spacing is not None else None
        )
        return SlotThinningPlan(
            slot_key=slot.key or slot_key,
            slot_id=slot.slot_id,
            slot_role=slot.slot_role.value,
            sown_at=sown_at,
            run_key=reservation.run_key,
            entry_key=entry.key or reservation.entry_key,
            species_key=entry.species_key,
            cultivar_key=entry.cultivar_key,
            measure_kind=measure.kind if measure is not None else None,
            measure_value=round(measure.value, 3) if measure is not None else None,
            thinning_to_cm=spacing,
            suggested_count=suggested,
            row_spacing_cm=row_spacing,
            row_spacing_source=row_source,
            species_row_spacing_cm=species.row_spacing_cm,
            count_formula=thinning_formula(measure, row_spacing) if measure is not None else None,
        )

    def thin_slot(
        self,
        slot_key: str,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        request: SlotThinningInput,
    ) -> SlotThinningOutcome:
        """Turn the sown slot into plants of its run, clear ``sown_at`` and log ``thinning`` — one transaction.

        Raises:
            ForbiddenError: a viewer (403).
            NotFoundError: the slot is not the tenant's (404).
            PlanError: not sowable (422), not sown (422), plants stand in it (409), no live run reserves it (422),
                more plants than one write takes (422 ``plan.quota_exceeded``).
            PlanValidationError: neither a spacing nor a count (422 ``thinning.spacing_required``), or the slot
                has no measure to divide (422 ``thinning.no_measure``).
        """
        self._require_editor(role)
        slot, location = resolve_owned_slot(self._sites, slot_key, tenant_key)
        sown_at = self._require_sown(slot)
        self._require_no_plant(slot, tenant_key)
        reservation = self._live_reservation(slot, tenant_key)
        run, entry, species = self._run_and_entry(reservation, tenant_key)
        count = self._count_of(slot, entry, species, request)
        today = today_utc()
        planted_on = request.planted_on or today
        if planted_on < sown_at:
            raise PlanValidationError([(None, "planted_on", "thinning.before_sowing", {})])
        if planted_on > today:
            raise PlanValidationError([(None, "planted_on", ERROR_PLANTED_IN_FUTURE, {})])

        now = datetime.now(UTC)
        location_key = location.key or slot.location_key
        # The seedlings left standing have emerged: they start in the phase after germination, on the thinning day.
        phase_key, phase_name = self._run_service.thinning_phase_of(entry.species_key)
        phase_started_at = datetime.combine(planted_on, time.min, tzinfo=UTC)
        # The plants to store: ids of the entry's prefix free at the bed, the run's crop, the first phase.
        existing = self._runs.get_existing_ids_at_location(location_key)
        sized = PlantingRunEntry(
            species_key=entry.species_key, cultivar_key=entry.cultivar_key, quantity=count, id_prefix=entry.id_prefix
        )
        plants = [
            PlantInstance(
                tenant_key=tenant_key,
                instance_id=spec["instance_id"],
                species_key=entry.species_key,
                cultivar_key=entry.cultivar_key,
                site_key=location.site_key,
                location_key=location_key,
                slot_key=slot.key,
                planted_on=planted_on,
                current_phase_key=phase_key or None,
                current_phase_started_at=phase_started_at,
            )
            for spec in self._engine.generate_plant_ids(location_key, [sized], existing)
        ]
        drafts = [
            QuickPlantedPlant(plant=plant, slot_index=0, history=_history_of(phase_key, phase_name, phase_started_at))
            for plant in plants
        ]
        event = self._care_events.build_event(
            CareEventInput(
                location_key=location_key,
                category="thinning",
                summary=THINNING_SUMMARY.format(slot_id=slot.slot_id, count=count),
                performed_at=now,
            ),
            tenant_key=tenant_key,
            user_key=user_key,
            role=role,
            origin=CareEventOrigin(trigger="system"),
        )
        try:
            outcome = self._reservations.thin_sown_slot(
                SlotThinningWrite(
                    location_key=location_key,
                    slot_key=slot.key or slot_key,
                    sown_at=sown_at,
                    run_key=reservation.run_key,
                    entry_key=reservation.entry_key,
                    tenant_key=tenant_key,
                    plants=drafts,
                    event=event,
                    phase_started_at=phase_started_at,
                    run_history=_history_of(phase_key, phase_name, phase_started_at),
                    run_phase_key=phase_key or None,
                )
            )
        except WriteConflictError:
            raise PlanError(ERROR_NOT_SOWN, "The slot changed while it was being thinned.", status_code=409) from None
        # REQ-022 — every stored plant gets its care profile, best-effort per plant (as `create_plants` does).
        for plant, plant_key in zip(plants, outcome.plant_keys, strict=True):
            plant.key = plant_key
        self._run_service.care_profile_bootstrap(plants)
        logger.info(
            "slot.thinned",
            slot_key=slot.key or slot_key,
            run_key=reservation.run_key,
            plants=len(outcome.plant_keys),
            run_started=outcome.run_started,
        )
        return outcome

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _require_editor(role: TenantRole) -> None:
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")

    @staticmethod
    def _require_sowable(slot: Slot) -> None:
        if slot.slot_role not in SOWABLE_ROLES:
            raise PlanError(
                ERROR_NOT_SOWABLE, "Only a row or a zone slot can be sown.", status_code=422, field="slot_role"
            )
        if slot.archived_at is not None:
            raise PlanError(ERROR_NOT_SOWABLE, "An archived slot is history.", status_code=422, field="archived_at")

    def _require_sown(self, slot: Slot) -> date:
        self._require_sowable(slot)
        if slot.sown_at is None:
            raise PlanError(ERROR_NOT_SOWN, "The slot is not sown.", status_code=422, field="sown_at")
        return slot.sown_at

    def _require_no_plant(self, slot: Slot, tenant_key: str) -> None:
        if self._reservations.active_plants_in([slot.key or ""], tenant_key=tenant_key):
            raise PlanError(ERROR_OCCUPIED, "Plants stand in the slot already.", status_code=409)

    def _live_reservation(self, slot: Slot, tenant_key: str) -> Reservation:
        """The tenant's live reservation of the slot — the one that starts first when two runs follow each other."""
        live = [
            reservation
            for reservation in self._reservations.reservations_for([slot.key or ""], tenant_key=tenant_key)
            if reservation.run_status in LIVE_RUN_STATUSES
        ]
        if not live:
            raise PlanError(
                ERROR_NO_RUN, "No planting run of the tenant reserves this slot.", status_code=422, field="slot_key"
            )
        return min(live, key=lambda r: (r.planned_from or date.max, r.run_key, r.sequence))

    def _run_and_entry(
        self, reservation: Reservation, tenant_key: str
    ) -> tuple[PlantingRun, PlantingRunEntry, Species]:
        run = self._runs.get_by_key(reservation.run_key)
        if run is None:
            raise NotFoundError("PlantingRun", reservation.run_key)
        verify_tenant_ownership(run, tenant_key, "PlantingRun")
        entries = self._runs.get_entries(reservation.run_key)
        entry = next((e for e in entries if e.key == reservation.entry_key), None)
        if entry is None and len(entries) == 1:
            entry = entries[0]
        if entry is None:
            raise PlanError(ERROR_NO_RUN, "The run has no entry for this slot.", status_code=422, field="slot_key")
        # The stored species is resolved under the tenant before the plants are stamped with it and its phase data
        # is read: an entry written before #1876 may still name another tenant's species (#1963).
        species = readable_species(self._species, entry.species_key, tenant_key)
        if species is None:
            raise NotFoundError("Species", entry.species_key)
        return run, entry, species

    @staticmethod
    def _count_of(slot: Slot, entry: PlantingRunEntry, species: Species, request: SlotThinningInput) -> int:
        """The grower's count, else the slot's measure divided by the spacing — never a default spacing (E-10).

        A zone's row spacing: the request's when it names the field (an explicit ``null`` asks for the square grid),
        else the run's, else the species profile's (:func:`_row_spacing_of`).
        """
        if request.count is not None:
            count = request.count
        else:
            spacing = request.thinning_to_cm if request.thinning_to_cm is not None else entry.thinning_to_cm
            if spacing is None:
                raise PlanValidationError([(None, "thinning_to_cm", ERROR_SPACING_REQUIRED, {})])
            if not 0 < spacing <= MAX_THINNING_SPACING_CM:
                raise PlanValidationError(
                    [(None, "thinning_to_cm", ERROR_SPACING_RANGE, {"max": MAX_THINNING_SPACING_CM})]
                )
            measure = sown_measure(slot.slot_role, slot.geometry)
            if measure is None:
                raise PlanValidationError([(None, "count", ERROR_NO_MEASURE, {})])
            if "row_spacing_cm" in request.model_fields_set:
                row_spacing = request.row_spacing_cm
            else:
                row_spacing, _source = _row_spacing_of(entry, species)
            count = thinning_count(measure, spacing, row_spacing)
        if count > QUICK_PLANTING_MAX_QUANTITY:
            raise PlanError(
                ERROR_TOO_MANY,
                f"Thinning creates at most {QUICK_PLANTING_MAX_QUANTITY} plants at once.",
                status_code=422,
                field="count",
                limit=QUICK_PLANTING_MAX_QUANTITY,
                current=count,
            )
        return count


def _row_spacing_of(entry: PlantingRunEntry, species: Species) -> tuple[float | None, RowSpacingSource | None]:
    """The row spacing a zone is counted with and where it came from: the run entry, else the species profile.

    The species stores a range string; its lower value is read, as the planting dialog prefills it (GP-FR-061). A
    profile value the parser cannot read or that lies outside the layout's row-spacing bounds (GP-FR-060) is no
    value. Neither source → ``(None, None)``: the zone falls back to the square-grid estimate (E-10, no constant).
    """
    if entry.row_spacing_cm is not None:
        return entry.row_spacing_cm, "run"
    from_profile = parse_range_lower(species.row_spacing_cm)
    if from_profile is not None and MIN_ROW_SPACING_CM <= from_profile <= MAX_SPACING_CM:
        return from_profile, "species"
    return None, None


def _history_of(phase_key: str, phase_name: str, now: datetime) -> PhaseHistory | None:
    if not phase_key:
        return None
    return PhaseHistory(phase_key=phase_key, phase_name=phase_name, entered_at=now, transition_reason="initial")


__all__ = ["MAX_SOWING_AGE_DAYS", "THINNING_SUMMARY", "SlotThinningService"]
