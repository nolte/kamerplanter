"""Soil hazards of a bed: record, take over from a loss, remove, read (REQ-054 §5.2, AP-API-012, #2888 F-20).

Who may do what is the router's gate (``require_permission(LOCATION, UPDATE)`` to record, ``DELETE`` - lead only - to
remove); this service holds what the gate cannot: the bed belongs to the caller's tenant (through its site, a
``Location`` carries no ``tenant_key``), a vessel or a hydroponic location carries no soil hazard (hydroponics as the
location inherits it from its parents, O5), ``juglone`` stands at any other location and every other hazard only at a
bed (O3), and a loss becomes an entry only when its pathogen is listed and confirmed - whatever the client sends. The
removal writes its row of the plan change log (O6) in the transaction that removes the entry. Every method that loads
by key and writes takes ``*, tenant_key`` without a default and resolves the bed under it (#2107, MT-010); a foreign
and an unknown bed answer the same 404.

The knowledge table is read through ``ISoilHazardKnowledgeSource`` - one instance per process, loaded at start-up
(``app.main.lifespan``), so a corrupt table stops the boot instead of the first request that shows a hazard.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

import structlog

from app.common.enums import PathogenConfirmationSource, SoilHazard
from app.common.exceptions import KamerplanterError, NotFoundError, PlanError
from app.common.log_privacy import log_tenant
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.engines.bed_soil_hazard_engine import (
    LossNotPromotableError,
    entry_from_loss,
    follow_up_for_loss,
    merged_entries,
    resolve_entries,
    soil_hazard_refusal,
)
from app.domain.interfaces.bed_soil_hazard_repository import (
    IBedSoilHazardRepository,
    SoilHazardRemoval,
    SoilHazardWrite,
)
from app.domain.interfaces.location_type_repository import ILocationTypeRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.soil_hazard_knowledge_source import ISoilHazardKnowledgeSource
from app.domain.models.bed_soil_hazard import (
    BedSoilHazard,
    ResolvedBedSoilHazard,
    SoilHazardFollowUp,
    confirmation_date_violation,
)
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Location
from app.domain.services.location_ancestry import location_ancestors
from app.domain.services.location_ownership import find_owned_location, resolve_owned_location

logger = structlog.get_logger(__name__)

#: 422 when the loss named by ``plant_key`` cannot become an entry (no soil-borne loss, no listed or no confirmed
#: pathogen, ``juglone``).
ERROR_LOSS_NOT_CONFIRMED = "soil_hazard.loss_not_confirmed"
#: 422 when the plant of ``plant_key`` did not stand in this bed.
ERROR_PLANT_NOT_IN_BED = "soil_hazard.plant_not_in_bed"
#: 422 for a confirmation dated after today (UTC) / before 1900 (``confirmation_date_violation``).
ERROR_CONFIRMED_IN_FUTURE = "soil_hazard.confirmed_in_future"
ERROR_CONFIRMED_TOO_EARLY = "soil_hazard.confirmed_too_early"
_DATE_MESSAGES: dict[str, str] = {
    ERROR_CONFIRMED_IN_FUTURE: "A soil hazard cannot be confirmed in the future.",
    ERROR_CONFIRMED_TOO_EARLY: "A soil hazard cannot be confirmed before 1900.",
}

_REFUSAL_MESSAGES: dict[str, str] = {
    "soil_hazard.container": (
        "A planter, tent, shelf or container group has no soil hazard: its substrate is replaced, not rotated."
    ),
    "soil_hazard.not_a_bed": "Only a bed carries this soil hazard; an area that is no bed carries juglone only.",
    "soil_hazard.hydroponic": "A hydroponic location has no soil: clean and disinfect the system instead.",
}


@dataclass(frozen=True)
class RecordOutcome:
    """The bed's soil hazards after a record; ``changed`` is ``False`` when the bed already held the hazard confirmed
    as late or later and nothing was written (#2888 F-20 review D3)."""

    entries: list[ResolvedBedSoilHazard]
    changed: bool


class BedSoilHazardService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        location_types: ILocationTypeRepository,
        plants: IPlantInstanceRepository,
        hazards: IBedSoilHazardRepository,
        knowledge: ISoilHazardKnowledgeSource,
    ) -> None:
        self._sites = site_repo
        self._types = location_types
        self._plants = plants
        self._hazards = hazards
        self._knowledge = knowledge

    # ── Read ──────────────────────────────────────────────────────────────

    def follow_up_for_loss(self, plant: PlantInstance, *, tenant_key: str) -> SoilHazardFollowUp | None:
        """What to propose after ``plant``'s loss was recorded: an offer, the clean-system hint or nothing.

        Proposes only; writes nothing (REQ-053 §11.3a Nr. 5: "nur auf Angebot"). ``plant`` is the tenant's plant as
        the remove call returned it; its location is read under ``tenant_key`` and a foreign one proposes nothing.
        """
        if not plant.location_key:
            return None
        # The loss is stored before this runs: a suggestion that cannot be computed (a stored location or type that
        # fails validation, a database hiccup) must never turn the recorded removal into an error the client would
        # retry into a 422. It proposes nothing and says so in the log (#2888 F-20 review D2).
        try:
            location = find_owned_location(self._sites, plant.location_key, tenant_key)
            if location is None:
                return None
            return follow_up_for_loss(
                plant, location, is_bed=self._is_bed(location), ancestors=location_ancestors(self._sites, location)
            )
        except KamerplanterError as exc:
            logger.warning(
                "soil_hazard_follow_up_failed",
                plant_key=plant.key,
                location_key=plant.location_key,
                error_code=exc.error_code,
                tenant=log_tenant(tenant_key),
            )
            return None

    # ── Write ─────────────────────────────────────────────────────────────

    def record(
        self,
        location_key: str,
        *,
        tenant_key: str,
        hazard: SoilHazard,
        confirmed_at: date,
        source: PathogenConfirmationSource,
    ) -> RecordOutcome:
        """Record a confirmed soil hazard of the bed by hand (grower and above).

        One entry per hazard: a later confirmation replaces the stored one, an earlier or equal one changes nothing
        - so recording never shortens a hazard; only :meth:`remove` (lead) takes one away.
        """
        location = self._writable_bed(location_key, tenant_key=tenant_key, hazard=hazard)
        violation = confirmation_date_violation(confirmed_at)
        if violation is not None:
            code = f"soil_hazard.{violation}"
            raise PlanError(code, _DATE_MESSAGES[code], status_code=422, field="confirmed_at")
        entry = BedSoilHazard(hazard=hazard, confirmed_at=confirmed_at, source=source)
        return self._write_entry(location, entry, tenant_key=tenant_key)

    def take_over_loss(self, location_key: str, *, tenant_key: str, plant_key: str) -> RecordOutcome:
        """Take the confirmed pathogen of ``plant_key``'s loss over into the bed - the accepted offer.

        Pathogen, date (the day of the loss) and source come from the stored loss, never from the request, so an
        unconfirmed or unlisted loss cannot become an entry through any client (REQ-053 §11.3a Nr. 5). The bed is held
        to the bed rule: a loss never names ``juglone``, the one hazard an area that is no bed takes.
        """
        location = self._writable_bed(location_key, tenant_key=tenant_key, hazard=None)
        plant = self._plants.get_by_key(plant_key)
        if plant is None:
            raise NotFoundError("PlantInstance", plant_key)
        verify_tenant_ownership(plant, tenant_key, "PlantInstance")
        if plant.location_key != location.key:
            raise PlanError(
                ERROR_PLANT_NOT_IN_BED,
                "The plant did not stand in this bed.",
                status_code=422,
                field="plant_key",
            )
        try:
            entry = entry_from_loss(plant)
        except LossNotPromotableError as exc:
            raise PlanError(
                ERROR_LOSS_NOT_CONFIRMED,
                f"The loss cannot become a soil hazard: {exc.reason}.",
                status_code=422,
                field="plant_key",
            ) from exc
        return self._write_entry(location, entry, tenant_key=tenant_key)

    def remove(self, location_key: str, hazard: SoilHazard, *, tenant_key: str, user_key: str) -> None:
        """Remove the bed's entry of ``hazard`` (lead only, by the router's gate); 404 if the bed holds none.

        The same transaction writes the row of the plan change log (``garden_plan_audit``, operator decision O6
        2026-11-27): who (``user_key``), when, which bed, which hazard and its ``confirmed_at``.
        """
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        removal: SoilHazardRemoval = self._hazards.remove_soil_hazard(
            location_key, hazard, tenant_key=tenant_key, user_key=user_key, at=datetime.now(UTC)
        )
        if removal.status == "location_not_found":
            raise NotFoundError("Location", location_key)
        if removal.status == "not_held":
            raise NotFoundError("BedSoilHazard", hazard.value)
        logger.info(
            "soil_hazard_removed", location_key=location.key, hazard=hazard.value, tenant=log_tenant(tenant_key)
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _is_bed(self, location: Location) -> bool:
        """``LocationType.is_bed`` of the location's type; ``False`` for an empty or unknown type key."""
        location_type = self._types.get_by_key(location.location_type_key) if location.location_type_key else None
        return location_type is not None and location_type.is_bed

    def _writable_bed(self, location_key: str, *, tenant_key: str, hazard: SoilHazard | None) -> Location:
        """The tenant's location, refused with 422 unless it may carry ``hazard``; 404 for foreign and unknown.

        ``hazard = None`` (a loss, pathogen not read yet) is held to the bed rule.
        """
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        refusal = soil_hazard_refusal(
            location,
            is_bed=self._is_bed(location),
            hazard=hazard,
            ancestors=location_ancestors(self._sites, location),
        )
        if refusal is not None:
            raise PlanError(refusal.value, _REFUSAL_MESSAGES[refusal.value], status_code=422, field="location")
        return location

    def _write_entry(self, location: Location, entry: BedSoilHazard, *, tenant_key: str) -> RecordOutcome:
        location_key = location.key or ""
        written: SoilHazardWrite = self._hazards.change_soil_hazards(
            location_key,
            tenant_key=tenant_key,
            change=lambda stored: tuple(merged_entries(stored, entry)),
        )
        if written.status == "location_not_found":
            raise NotFoundError("Location", location_key)
        if written.status == "written":
            logger.info(
                "soil_hazard_recorded",
                location_key=location_key,
                hazard=entry.hazard.value,
                source=entry.source.value,
                tenant=log_tenant(tenant_key),
            )
        return RecordOutcome(
            entries=resolve_entries(written.entries, self._knowledge.get_table()), changed=written.status == "written"
        )
