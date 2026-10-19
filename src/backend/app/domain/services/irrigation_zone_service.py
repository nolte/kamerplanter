"""Irrigation zones of a site: CRUD and bed assignment (REQ-053 §14, §21.6 GP-API-050/051; WP 7.1, #2467).

**Order of the checks (SR-013).** Tenant anchor (404) → role (403) → references of the body (422
``reference.not_found``) → the coupling fields (422) → the write. A foreign and an absent zone, site or bed
answer identically.

**Ownership is resolved here, never in the router** (T-01…T-03, #2107). Every public method takes
``*, tenant_key: str`` without a default. A new zone hangs off the path's site, resolved through
:func:`~app.domain.services.location_ownership.require_owned_site`; an existing zone is loaded under the
tenant and its ``site_key`` is the stored one (T-01). Every key of a request body is resolved under the tenant
**and** the zone's site (GP-NFR-058): ``location_keys`` are locations of that site (T-03), ``water_source_key``
is a ``water_source`` garden object of that site.

**Roles (§21.8 "Bewässerungszone").** Reading: every member; creating, changing and assigning beds: from
grower; deleting: lead only. The router gate says the same; the service repeats it so a second caller (an MCP
tool, a task) cannot skip it.

**Logs carry no user text** (GP-NFR-060): keys, counts and codes — never a zone name or a schedule hint.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from pydantic import BaseModel

from app.common.enums import CareEventAllocation, FlowRateSource, GardenObjectType, TenantRole
from app.common.exceptions import ForbiddenError, PlanError, PlanValidationError
from app.common.types import IrrigationZoneKey, SiteKey
from app.domain.calculators.irrigation_zone_demand_calculator import (
    ZoneDemand,
    days_of_supply,
    irrigation_system_differs,
    zone_demand,
)
from app.domain.calculators.overdue_calculator import is_overdue
from app.domain.calculators.zone_allocation_calculator import divide_volume
from app.domain.engines.garden_plan_engine import ERROR_REFERENCE_NOT_FOUND
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.care_event_repository import ICareEventRepository
from app.domain.interfaces.garden_object_repository import IGardenObjectRepository
from app.domain.interfaces.irrigation_zone_repository import IIrrigationZoneRepository
from app.domain.models.care_event import CareEvent
from app.domain.models.garden_object import GardenObject
from app.domain.models.irrigation_zone import (
    COUPLING_FIELDS,
    BedShare,
    IrrigationZone,
    IrrigationZoneInput,
    IrrigationZonePatch,
    IrrigationZoneView,
    NextPlannedView,
    ZoneCoverageChange,
    ZoneHint,
    ZoneStatusView,
    ZoneWateringInput,
    ZoneWateringResult,
)
from app.domain.services.care_event_service import check_performed_instant
from app.domain.services.location_ownership import (
    SiteAnchorBatchSource,
    find_owned_locations,
    require_owned_site,
)

logger = structlog.get_logger()

#: The code of a coupling field set before WP 7.4 delivers the technical coupling (SR-014).
ERROR_COUPLING_NOT_AVAILABLE = "irrigation_zone.coupling_not_available"
#: 422 of a watering round on a zone that covers no bed / on ``by_area`` when no bed has an area.
ERROR_NO_BEDS = "irrigation_zone.no_beds"
ERROR_NO_BED_AREA = "irrigation_zone.no_bed_area"

#: The fields a PATCH writes on the document (the coupling fields are refused before).
_PATCH_COLUMNS: tuple[str, ...] = (
    "name",
    "irrigation_type",
    "water_source_key",
    "color",
    "schedule_hint",
    "application_efficiency",
)


def _dump(model: BaseModel, **options: Any) -> dict[str, Any]:
    """``model_dump`` through a receiver typed as the pydantic base (see the call-graph sweep's blind-spot ceiling)."""
    return model.model_dump(**options)


def _not_found(field: str) -> PlanValidationError:
    """422 ``reference.not_found`` — one text for a missing and for another tenant's or site's key (GP-NFR-058)."""
    return PlanValidationError([(None, field, ERROR_REFERENCE_NOT_FOUND, {})])


def _refuse_coupling(sent: dict[str, Any]) -> None:
    """422 for a coupling field that carries a value; the defaults (``null``, ``manual``) are accepted."""
    for name in COUPLING_FIELDS:
        if name not in sent:
            continue
        value = sent[name]
        if value is None or (name == "flow_rate_source" and value == FlowRateSource.MANUAL):
            continue
        raise PlanError(
            ERROR_COUPLING_NOT_AVAILABLE,
            "The actuator and flow-rate coupling of a zone is not available yet.",
            status_code=422,
            field=name,
        )


class IrrigationZoneService:
    def __init__(
        self,
        zone_repo: IIrrigationZoneRepository,
        site_repo: SiteAnchorBatchSource,
        object_repo: IGardenObjectRepository,
        care_repo: ICareEventRepository,
    ) -> None:
        self._zones = zone_repo
        self._sites = site_repo
        self._objects = object_repo
        self._care = care_repo

    # ── Roles ─────────────────────────────────────────────────────────────

    @staticmethod
    def _require_editor(role: TenantRole) -> None:
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")

    @staticmethod
    def _require_lead(role: TenantRole) -> None:
        if not MembershipEngine.can_delete_resource(role):
            raise ForbiddenError("Requires lead role.")

    # ── Reads (GP-API-050) ────────────────────────────────────────────────

    def list_zones(self, site_key: SiteKey, *, tenant_key: str, offset: int, limit: int) -> list[IrrigationZoneView]:
        require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)
        zones = self._zones.list_zones_by_site(site_key, tenant_key=tenant_key, offset=offset, limit=limit)
        return self._views(zones, tenant_key=tenant_key)

    def get_zone(self, key: IrrigationZoneKey, *, tenant_key: str) -> IrrigationZoneView:
        zone = self._zones.get_zone_or_raise(key, tenant_key=tenant_key)
        return self._views([zone], tenant_key=tenant_key)[0]

    def _views(self, zones: list[IrrigationZone], *, tenant_key: str) -> list[IrrigationZoneView]:
        covered = self._zones.covered_location_keys([zone.key or "" for zone in zones], tenant_key=tenant_key)
        return [IrrigationZoneView(zone=zone, location_keys=tuple(covered.get(zone.key or "", []))) for zone in zones]

    # ── Writes (GP-API-050) ───────────────────────────────────────────────

    def create_zone(
        self, site_key: SiteKey, *, tenant_key: str, role: TenantRole, data: IrrigationZoneInput
    ) -> IrrigationZoneView:
        """A zone on the path's site (T-01: the site is never read from the body)."""
        require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)
        self._require_editor(role)
        if data.water_source_key is not None:
            self._resolve_water_source(data.water_source_key, site_key, tenant_key=tenant_key)
        _refuse_coupling({name: getattr(data, name) for name in data.model_fields_set})
        zone = IrrigationZone(
            tenant_key=tenant_key,
            site_key=site_key,
            name=data.name,
            irrigation_type=data.irrigation_type,
            water_source_key=data.water_source_key,
            color=data.color,
            schedule_hint=data.schedule_hint,
            application_efficiency=data.application_efficiency,
        )
        created = self._zones.create_zone(zone, tenant_key=tenant_key)
        logger.info(
            "irrigation_zone.created",
            zone_key=created.key,
            site_key=site_key,
            irrigation_type=created.irrigation_type.value,
        )
        return IrrigationZoneView(zone=created, location_keys=())

    def patch_zone(
        self, key: IrrigationZoneKey, *, tenant_key: str, role: TenantRole, patch: IrrigationZonePatch
    ) -> IrrigationZoneView:
        """Change the fields present; ``water_source_key: null`` unlinks the water source."""
        stored = self._zones.get_zone_or_raise(key, tenant_key=tenant_key)
        self._require_editor(role)
        sent = {name: getattr(patch, name) for name in patch.model_fields_set}
        if sent.get("water_source_key") is not None:
            self._resolve_water_source(str(sent["water_source_key"]), stored.site_key, tenant_key=tenant_key)
        _refuse_coupling(sent)
        # The stored row with the change laid over it runs through the model's validation (stripping included).
        merged = IrrigationZone(
            **{
                **_dump(stored, by_alias=True),
                **{name: value for name, value in sent.items() if name in _PATCH_COLUMNS},
            }
        )
        before = _dump(stored, mode="json")
        after = _dump(merged, mode="json")
        fields = {name: after[name] for name in _PATCH_COLUMNS if after[name] != before[name]}
        updated = self._zones.update_zone(key, fields, tenant_key=tenant_key) if fields else stored
        if fields:
            logger.info("irrigation_zone.updated", zone_key=key, fields=sorted(fields))
        return self.get_zone(updated.key or key, tenant_key=tenant_key)

    def delete_zone(self, key: IrrigationZoneKey, *, tenant_key: str, user_key: str, role: TenantRole) -> None:
        """Delete the zone (lead only); its beds are released and the delete is audited (SR-011)."""
        stored = self._zones.get_zone_or_raise(key, tenant_key=tenant_key)
        self._require_lead(role)
        released = self._zones.delete_zone(key, tenant_key=tenant_key, user_key=user_key)
        logger.info(
            "irrigation_zone.deleted",
            zone_key=key,
            site_key=stored.site_key,
            released_count=len(released),
        )

    # ── GP-API-051: the beds of a zone ────────────────────────────────────

    def replace_locations(
        self, key: IrrigationZoneKey, *, tenant_key: str, role: TenantRole, location_keys: list[str]
    ) -> tuple[IrrigationZoneView, ZoneCoverageChange]:
        """Make ``location_keys`` the zone's beds; a bed another zone covered moves to this one.

        Every key must be a location of the zone's own site (GP-NFR-058, T-03); a foreign, absent or
        other-site key is 422 ``reference.not_found`` at ``location_keys[i]`` and nothing is written.
        """
        zone = self._zones.get_zone_or_raise(key, tenant_key=tenant_key)
        self._require_editor(role)
        self._resolve_locations(location_keys, zone.site_key, tenant_key=tenant_key)
        change = self._zones.replace_zone_locations(key, location_keys, tenant_key=tenant_key)
        logger.info(
            "irrigation_zone.locations_replaced",
            zone_key=key,
            site_key=zone.site_key,
            added=len(change.added),
            removed=len(change.removed),
            moved=len(change.moved_from),
        )
        return self.get_zone(key, tenant_key=tenant_key), change

    # ── GP-API-052: the status ────────────────────────────────────────────

    def zone_status(self, key: IrrigationZoneKey, *, tenant_key: str, now: datetime | None = None) -> ZoneStatusView:
        """Last and next watering, today's demand and the 30-day consumption of the zone's beds (every member).

        Demand (WP 7.5) is REQ-037's depth x area per bed of the day (UTC calendar day, like the overdue rule),
        net always and gross only with a known efficiency; nothing is estimated where a source is missing (E-10).
        """
        moment = now or datetime.now(UTC)
        zone = self._zones.get_zone_or_raise(key, tenant_key=tenant_key)
        covered = self._zones.covered_location_keys([key], tenant_key=tenant_key).get(key, [])
        facts = self._zones.watering_facts(covered, tenant_key=tenant_key, now=moment)
        planned = facts.next_planned
        bed_demands = self._zones.bed_demands(zone.site_key, covered, tenant_key=tenant_key, on_date=moment.date())
        demand = zone_demand(zone.irrigation_type, zone.application_efficiency, bed_demands)
        return ZoneStatusView(
            zone_key=zone.key or key,
            last_watering=facts.last_watering,
            next_planned=NextPlannedView(
                task_key=planned.task_key,
                location_key=planned.location_key,
                due_date=planned.due_date,
                overdue=is_overdue(planned.due_date, moment),
            )
            if planned is not None
            else None,
            demand_liters_today=demand.net_liters if bed_demands else None,
            consumption_liters_30d=facts.consumption_liters,
            demand_gross_liters_today=demand.gross_liters if bed_demands else None,
            application_efficiency=demand.efficiency.value,
            efficiency_source=demand.efficiency.source,
            hints=self._hints(zone, covered, demand, tenant_key=tenant_key),
        )

    def _hints(
        self, zone: IrrigationZone, bed_keys: list[str], demand: ZoneDemand, *, tenant_key: str
    ) -> tuple[ZoneHint, ...]:
        """GP-FR-119: how many days the water source lasts, and beds equipped otherwise than the zone says."""
        hints: list[ZoneHint] = []
        daily = demand.gross_liters if demand.gross_liters is not None else demand.net_liters
        if zone.water_source_key and daily > 0:
            source = self._objects.get_garden_object_by_key(zone.water_source_key, tenant_key=tenant_key)
            capacity = getattr(getattr(source, "props", None), "capacity_liters", None)
            days = days_of_supply(capacity, daily)
            if days is not None:
                hints.append(
                    ZoneHint(
                        "water_source_lasts_days",
                        {"days": days, "capacity_liters": float(capacity or 0), "daily_liters": daily},
                    )
                )
        owned = find_owned_locations(self._sites, bed_keys, tenant_key)
        differing = sorted(
            key
            for key, bed in owned.items()
            if bed.site_key == zone.site_key and irrigation_system_differs(zone.irrigation_type, bed.irrigation_system)
        )
        if differing:
            hints.append(
                ZoneHint(
                    "irrigation_system_differs",
                    {"zone_type": zone.irrigation_type.value, "location_keys": differing},
                )
            )
        return tuple(hints)

    # ── GP-API-053: a watering round ──────────────────────────────────────

    def log_watering(
        self,
        key: IrrigationZoneKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        data: ZoneWateringInput,
    ) -> ZoneWateringResult:
        """One ``care_event(watering)`` per bed of the zone, in one transaction (GP-FR-117).

        The total is divided by ``area_m2`` or evenly and every event is marked with the ``allocation``, so an
        allocated quantity is never taken for a measured one. A bed without an area is left out of ``by_area``
        and named in the answer; no area anywhere is 422 ``irrigation_zone.no_bed_area``. ``performed_at`` obeys
        V-11 (five minutes ahead, a year back). Nothing is written when anything is refused.
        """
        zone = self._zones.get_zone_or_raise(key, tenant_key=tenant_key)
        self._require_editor(role)
        performed_at = data.performed_at or datetime.now(UTC)
        check_performed_instant(performed_at)
        bed_keys = self._zones.covered_location_keys([key], tenant_key=tenant_key).get(key, [])
        if not bed_keys:
            raise PlanError(ERROR_NO_BEDS, "The zone covers no bed to water.", status_code=422, field="location_keys")
        owned = find_owned_locations(self._sites, bed_keys, tenant_key)
        beds = [owned[bed] for bed in bed_keys if bed in owned and owned[bed].site_key == zone.site_key]
        by_area = data.allocation is CareEventAllocation.BY_AREA
        placed = [bed for bed in beds if bed.area_m2 > 0] if by_area else beds
        skipped = tuple(bed.key or "" for bed in beds if bed not in placed)
        if not placed:
            raise PlanError(
                ERROR_NO_BED_AREA,
                "No bed of the zone has an area to divide the total by; use `equal`.",
                status_code=422,
                field="allocation",
            )
        liters = divide_volume(data.volume_liters, [bed.area_m2 if by_area else 1.0 for bed in placed])
        summary = data.summary or f"Watering round, zone {zone.name}"
        events = [
            CareEvent(
                tenant_key=tenant_key,
                site_key=bed.site_key,
                location_key=bed.key or "",
                category="watering",
                summary=summary[:500],
                performed_at=performed_at,
                performed_by_user_key=user_key,
                trigger="manual",
                quantity=share,
                unit="l",
                allocation=data.allocation,
                created_by=user_key,
            )
            for bed, share in zip(placed, liters, strict=True)
        ]
        stored = self._care.insert_many(events, tenant_key=tenant_key)
        logger.info(
            "irrigation_zone.watering_logged",
            zone_key=key,
            site_key=zone.site_key,
            allocation=data.allocation.value,
            beds=len(stored),
            skipped=len(skipped),
        )
        return ZoneWateringResult(
            event_keys=tuple(event.key or "" for event in stored),
            shares=tuple(
                BedShare(location_key=e.location_key, liters=share) for e, share in zip(stored, liters, strict=True)
            ),
            allocation=data.allocation,
            performed_at=performed_at,
            skipped_location_keys=skipped,
        )

    # ── References ────────────────────────────────────────────────────────

    def _resolve_locations(self, location_keys: list[str], site_key: str, *, tenant_key: str) -> None:
        """GP-NFR-058 / T-03: every key is a location of the tenant on the zone's site; all misses are named.

        One location read for the whole set through
        :func:`~app.domain.services.location_ownership.find_owned_locations` (the site anchor, resolved once per
        site); a key that is absent, another tenant's or on another site is ``reference.not_found`` at its index.
        """
        owned = find_owned_locations(self._sites, location_keys, tenant_key)
        findings: list[tuple[int | None, str, str, dict[str, Any]]] = [
            (None, f"location_keys[{index}]", ERROR_REFERENCE_NOT_FOUND, {})
            for index, location_key in enumerate(location_keys)
            if location_key not in owned or owned[location_key].site_key != site_key
        ]
        if findings:
            raise PlanValidationError(findings[:50])

    def _resolve_water_source(self, object_key: str, site_key: str, *, tenant_key: str) -> GardenObject:
        """GP-NFR-058: ``water_source_key`` is a ``water_source`` garden object of the zone's site."""
        found = self._objects.get_garden_object_by_key(object_key, tenant_key=tenant_key)
        if found is None or found.site_key != site_key or found.object_type is not GardenObjectType.WATER_SOURCE:
            raise _not_found("water_source_key")
        return found
