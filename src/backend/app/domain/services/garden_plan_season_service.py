"""New season from the previous year: ``POST /sites/{key}/plan/new-season`` (REQ-053 GP-FR-171, WP 7.16).

The semantics are the operator's of 2026-10-19 (#2466 item 7), nothing more:

* the **same site** - there is no target;
* per bed **without an active plant**, the slot geometries of the runs that ended in the previous calendar year are
  re-created as **unoccupied** slots (``geometry_source = season_copy``). A run's slots become history when it is
  closed (GP-FR-055, ``archived_at``), so "ended in the previous year" is read from that stamp - the one record of the
  end of a run that reaches the slot;
* a bed with an active plant is **skipped and reported**, a retired bed too; the **zones stay as they are**;
* **no plant and no run is created** (GP-FR-078 stays COULD), and history and rotation hints are left alone: the
  archived slots are read, never changed;
* one transaction through the batch write (revision check inside, audit row, 2 000 slots per bed, 8 000 per site),
  **lead only**.

**Idempotence.** A position that already stands as a live slot in the bed (same geometry) is not copied again, so
a second run of the same year finds nothing to do and a bed that was re-planted by hand is not doubled.

**Revision.** ``expected_revision`` is optional: when the caller sends the revision it saw (the dialog's dry run),
a different stored revision is a 409 ``plan.revision_conflict``; without it the revision this call read is the basis,
and the transaction still refuses a writer that lost the race. The audit row carries counts only, no free text.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from time import perf_counter

import structlog

from app.common.enums import BedStatus, GeometrySource, TenantRole
from app.common.exceptions import PlanError, PlanRevisionConflictError
from app.common.types import SiteKey
from app.domain.engines.garden_plan_engine import slots_outside_bed
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.garden_plan import MAX_SLOTS_PER_BATCH, MAX_SLOTS_PER_SITE, PlanBatchWrite
from app.domain.models.garden_plan_season import (
    MAX_SEASON_YEARS_AHEAD,
    MIN_SEASON_YEAR,
    PlanSeasonReport,
    SeasonBedOutcome,
)
from app.domain.models.site import Location, Slot
from app.domain.services.adjacency_service import AdjacencyDispatch, request_adjacency_recompute
from app.domain.services.location_ownership import require_owned_site

logger = structlog.get_logger()

ERROR_YEAR = "season.invalid_year"
ERROR_QUOTA = "plan.quota_exceeded"


def _geometry_id(slot: Slot) -> str:
    assert slot.geometry is not None  # noqa: S101 - callers filter on it
    return slot.geometry.model_dump_json()


class GardenPlanSeasonService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        plan_repo: IGardenPlanRepository,
        *,
        dispatch_adjacency: AdjacencyDispatch | None = None,
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._dispatch_adjacency = dispatch_adjacency

    def new_season(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        year: int,
        dry_run: bool,
        expected_revision: int | None = None,
    ) -> PlanSeasonReport:
        """Check order: tenant anchor (404 for a foreign site) -> lead (403) -> year (422) -> revision (409)."""
        started = perf_counter()
        site = require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)
        if not MembershipEngine.can_delete_resource(role):
            raise PlanError("season.forbidden", "Only a lead may start a new season.", status_code=403, field="request")
        _check_year(year)
        revision = site.plan.plan_revision if site.plan is not None else 0
        if expected_revision is not None and expected_revision != revision:
            raise PlanRevisionConflictError(current_revision=revision, changed_by=None, changed_at=None)

        report = PlanSeasonReport(year=year, source_year=year - 1, dry_run=dry_run, plan_revision=revision)
        inserts: list[tuple[str, Slot]] = []
        self._plan_the_beds(report, inserts, site_key, tenant_key=tenant_key, year=year)
        report.slots_to_create = len(inserts)
        if (
            report.slots_to_create
            and self._plan.count_active_slots(site_key, tenant_key=tenant_key) + len(inserts) > MAX_SLOTS_PER_SITE
        ):
            raise PlanError(
                ERROR_QUOTA,
                "The site would exceed its slot limit.",
                status_code=422,
                field="slots",
                limit=MAX_SLOTS_PER_SITE,
            )
        if dry_run or not inserts:
            logger.info(
                "garden_plan.new_season_checked",
                site_key=site_key,
                year=year,
                beds_copied=report.beds_copied,
                slots=report.slots_to_create,
                dry_run=dry_run,
            )
            return report

        write = PlanBatchWrite(
            site_key=site_key,
            tenant_key=tenant_key,
            editor_key=user_key,
            expected_revision=revision,
            basis_revision=revision,
            slot_inserts=inserts,
            audit=[
                {
                    "op": "season_copy",
                    "entity": "site",
                    "key": site_key,
                    "summary": f"year {year}: {report.beds_copied} beds, {report.slots_to_create} slots",
                }
            ],
        )
        outcome = self._plan.apply_plan_batch(write)
        for bed in {bed for bed, _ in inserts}:
            request_adjacency_recompute(self._dispatch_adjacency, bed)
        report.applied = True
        report.plan_revision = outcome.plan_revision
        logger.info(
            "garden_plan.new_season_applied",
            site_key=site_key,
            year=year,
            revision=outcome.plan_revision,
            beds_copied=report.beds_copied,
            slots=report.slots_to_create,
            duration_ms=round((perf_counter() - started) * 1000),
        )
        return report

    def _plan_the_beds(
        self,
        report: PlanSeasonReport,
        inserts: list[tuple[str, Slot]],
        site_key: str,
        *,
        tenant_key: str,
        year: int,
    ) -> None:
        locations, _ = self._plan.load_structure(site_key, tenant_key=tenant_key)
        beds: dict[str, Location] = {loc.key: loc for loc in locations if loc.key}
        outcomes: list[SeasonBedOutcome] = []
        if not beds:
            return
        everything = self._plan.load_active_slots(site_key, sorted(beds), tenant_key=tenant_key, include_archived=True)
        live: dict[str, list[Slot]] = defaultdict(list)
        history: dict[str, list[Slot]] = defaultdict(list)
        for slot in everything:
            if slot.archived_at is None:
                live[slot.location_key].append(slot)
            elif slot.geometry is not None and _ended_in(slot.archived_at, year - 1):
                history[slot.location_key].append(slot)
        planted = self._plan.locations_with_active_plants(sorted(history), tenant_key=tenant_key)
        for bed_key in sorted(history):
            bed = beds[bed_key]
            if bed_key in planted:
                outcomes += [SeasonBedOutcome(location_key=bed_key, status="skipped_active_plants")]
                continue
            if bed.bed_status is BedStatus.RETIRED:
                outcomes += [SeasonBedOutcome(location_key=bed_key, status="skipped_retired")]
                continue
            standing: list[Slot] = live.get(bed_key, [])
            known_ids: set[str] = {slot.slot_id for slot in everything if slot.location_key == bed_key}
            taken: set[str] = {_geometry_id(slot) for slot in standing if slot.geometry is not None}
            fresh: list[Slot] = _distinct_places(history[bed_key], taken)
            outside: set[str] = set()
            if bed.geometry is not None and fresh:
                outside = set(
                    slots_outside_bed(bed.geometry, [(slot.slot_id, slot.geometry) for slot in fresh if slot.geometry])
                )
            fresh = [slot for slot in fresh if slot.slot_id not in outside]
            if not fresh:
                outcomes += [
                    SeasonBedOutcome(location_key=bed_key, status="nothing_to_copy", slots_outside_bed=len(outside))
                ]
                continue
            if len(standing) + len(fresh) > MAX_SLOTS_PER_BATCH:
                outcomes += [
                    SeasonBedOutcome(
                        location_key=bed_key,
                        status="skipped_slot_quota",
                        slots=len(fresh),
                        slots_outside_bed=len(outside),
                    )
                ]
                continue
            sequence = max([s.sequence or 0 for s in standing] + [0])
            inserts += [
                (bed_key, _re_created(old, bed_key, year, number, sequence + number, known_ids))
                for number, old in enumerate(fresh, start=1)
            ]
            outcomes += [
                SeasonBedOutcome(
                    location_key=bed_key, status="copied", slots=len(fresh), slots_outside_bed=len(outside)
                )
            ]
        report.beds = outcomes
        report.beds_copied = sum(1 for item in outcomes if item.status == "copied")
        report.beds_skipped = sum(1 for item in outcomes if item.status.startswith("skipped"))


def _distinct_places(old_slots: list[Slot], taken: set[str]) -> list[Slot]:
    """One slot per place not yet taken, in the old order; ``taken`` grows by what is returned."""
    ordered = sorted(old_slots, key=lambda s: (s.sequence or 0, s.slot_id))
    signatures: dict[str, Slot] = {}
    for old in ordered:
        signatures.setdefault(_geometry_id(old), old)
    chosen = [slot for signature, slot in signatures.items() if signature not in taken]
    taken |= set(signatures)
    return chosen


def _check_year(year: int) -> None:
    """422 for a year outside ``MIN_SEASON_YEAR`` .. next year; the route's schema already refuses a non-integer."""
    latest = datetime.now(UTC).year + MAX_SEASON_YEARS_AHEAD
    if isinstance(year, bool) or not MIN_SEASON_YEAR <= year <= latest:
        raise PlanError(ERROR_YEAR, "The year is out of range.", status_code=422, field="year")


def _ended_in(archived_at: datetime, calendar_year: int) -> bool:
    stamp = archived_at if archived_at.tzinfo is not None else archived_at.replace(tzinfo=UTC)
    return stamp.astimezone(UTC).year == calendar_year


def _re_created(old: Slot, bed_key: str, year: int, number: int, sequence: int, known_ids: set[str]) -> Slot:
    """A fresh, unoccupied slot at the old one's place. Its id is new in the bed (ids stay unique per location)."""
    slot_id = f"S{year}_{number:03d}"
    while slot_id in known_ids:
        slot_id += "X"
    known_ids.add(slot_id)
    return Slot(
        slot_id=slot_id,
        location_key=bed_key,
        capacity_plants=old.capacity_plants,
        currently_occupied=False,
        slot_role=old.slot_role,
        geometry=old.geometry,
        row_index=old.row_index,
        sequence=sequence,
        geometry_source=GeometrySource.SEASON_COPY,
        container_volume_l=old.container_volume_l,
        planned_spacing_cm=old.planned_spacing_cm,
    )
