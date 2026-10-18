"""Crop rotation and companion hints for a bed, and the years a grower fills in afterwards (REQ-053 WP 3.4).

* :meth:`BedRotationService.validate_planting` — ``POST /locations/{key}/validate-planting`` (GP-API-025,
  GP-FR-131/132): the rotation finding of
  :class:`~app.domain.engines.crop_rotation_validator.CropRotationValidator` plus the companion-planting hints of
  the neighbours. **Hints only, never an error for a violation** (D-09).
* :meth:`BedRotationService.rotation_timeline` — ``GET /locations/{key}/rotation`` (GP-API-039, GP-FR-103).
* :meth:`BedRotationService.backfill` / :meth:`~BedRotationService.cancel_backfill` — ``POST`` / ``DELETE``
  ``/locations/{key}/history/backfill`` (GP-API-042): a ``care_event(planting, trigger = backfill)`` the **server**
  stamps through the care-event service of WP 4.1 (the V-11 exception; a client body never carries the trigger, SR-009).

Every public method takes ``*, tenant_key: str`` without a default. The bed is resolved through
:mod:`~app.domain.services.location_ownership` (a bed has no ``tenant_key`` of its own, #2107); every key in a body
(species, family, slot) is resolved under the tenant before anything is read or written (GP-NFR-058).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

import structlog

from app.common.datetimes import today_utc
from app.common.enums import PlanRole, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.config.constants import DEFAULT_ROTATION_WINDOW_YEARS
from app.domain.engines.crop_rotation_validator import (
    SEVERITY_ORDER,
    BedRotationResult,
    CropRotationValidator,
    FamilySource,
    RotationTimeline,
    Severity,
)
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.care_event_repository import ICareEventRepository
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.graph_repository import IGraphRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.care_event import (
    BACKFILL_MAX_AGE_DAYS,
    CareEventInput,
    CareEventOrigin,
    RotationEntry,
)
from app.domain.services.care_event_service import CareEventService
from app.domain.services.location_ownership import resolve_owned_location, resolve_owned_slot
from app.domain.services.species_visibility import readable_species

logger = structlog.get_logger()

#: ``void_reason`` of a backfilled year taken back (GP-API-042).
BACKFILL_ERROR_REASON = "backfill_error"
#: The first backfilled year is ``current year - 10``, the last ``current year - 1`` (GP-API-042).
BACKFILL_YEARS_BACK = 10

#: ``performed_at`` of a backfilled year: the middle of the season, or 1 July when none is named (GP-API-042).
_SEASON_MIDDLE: dict[str | None, tuple[int, int]] = {
    "spring": (4, 15),
    None: (7, 1),
    "main": (7, 1),
    "autumn": (9, 15),
}

ERROR_YEAR_RANGE = "backfill.year_out_of_range"
ERROR_FAMILY_MISMATCH = "backfill.family_mismatch"

NeighbourScope = Literal["slot", "bed"]


@dataclass(frozen=True)
class NeighbourHint:
    """A companion-planting hint about a species standing, or planned, next to the new planting (GP-FR-132)."""

    severity: Severity
    code: str
    message: str
    species_key: str
    slot_keys: list[str]
    score: float | None = None


@dataclass(frozen=True)
class BedPlantingValidation:
    rotation: BedRotationResult
    neighbours: list[NeighbourHint]
    #: ``slot``: the neighbours of one named slot via ``adjacent_to``; ``bed``: every species standing in the bed.
    neighbour_scope: NeighbourScope
    #: The strongest severity of the rotation finding and the neighbour hints.
    severity: Severity


@dataclass(frozen=True)
class BackfillOutcome:
    care_event_key: str
    performed_at: datetime
    entry: RotationEntry


def _not_found(field: str) -> PlanValidationError:
    return PlanValidationError([(None, field, "reference.not_found", {})])


class BedRotationService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        plan_repo: IGardenPlanRepository,
        graph_repo: IGraphRepository,
        species_repo: ISpeciesRepository,
        family_repo: FamilySource,
        care_repo: ICareEventRepository,
        care_service: CareEventService,
        validator: CropRotationValidator,
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._graph = graph_repo
        self._species = species_repo
        self._families = family_repo
        self._care_repo = care_repo
        self._care = care_service
        self._validator = validator

    # ── Reads ────────────────────────────────────────────────────────────────

    def validate_planting(
        self,
        location_key: str,
        species_key: str,
        *,
        tenant_key: str,
        slot_key: str | None = None,
        rotation_window_years: int | None = None,
    ) -> BedPlantingValidation:
        """Rotation and neighbour hints for planting ``species_key`` in the bed (GP-API-025).

        With ``slot_key`` the neighbours are the species in the slots next to it (``adjacent_to``, WP 3.3); without
        one every species standing or planned in the bed counts as a possible neighbour, and an incompatible one is
        an ``INFO`` — nobody knows yet where the new plant will stand.
        """
        rotation = self._validator.validate_planting_in_location(
            location_key,
            species_key,
            tenant_key=tenant_key,
            rotation_window_years=rotation_window_years or DEFAULT_ROTATION_WINDOW_YEARS,
        )
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        scope: NeighbourScope = "bed"
        neighbour_slots: set[str] | None = None
        if slot_key is not None:
            slot, slot_location = resolve_owned_slot(self._sites, slot_key, tenant_key)
            if slot_location.key != location.key:
                raise NotFoundError("Slot", slot_key)
            scope = "slot"
            neighbour_slots = {
                row["slot"].get("_key", "") for row in self._graph.get_adjacent_slots(slot.key or slot_key)
            } - {""}
        hints = self._neighbour_hints(
            location.key or location_key, species_key, scope, neighbour_slots, tenant_key=tenant_key
        )
        severities = [rotation.severity, *(hint.severity for hint in hints)]
        return BedPlantingValidation(rotation, hints, scope, min(severities, key=lambda s: SEVERITY_ORDER[s]))

    def _neighbour_hints(
        self,
        location_key: str,
        species_key: str,
        scope: NeighbourScope,
        neighbour_slots: set[str] | None,
        *,
        tenant_key: str,
    ) -> list[NeighbourHint]:
        present: dict[str, list[str]] = {}
        for hint in self._plan.load_slot_species_hints(location_key, tenant_key=tenant_key):
            if neighbour_slots is None or hint.slot_key in neighbour_slots:
                present.setdefault(hint.species_key, []).append(hint.slot_key)
        if not present:
            return []
        incompatible = {
            row["species"].get("_key", "")
            for row in self._graph.get_incompatible_species(species_key, tenant_key=tenant_key)
        }
        compatible = {
            row["species"].get("_key", ""): row.get("score")
            for row in self._graph.get_compatible_species(species_key, tenant_key=tenant_key)
        }
        warn: Severity = "WARNING" if scope == "slot" else "INFO"
        hints: list[NeighbourHint] = []
        for other, slots in sorted(present.items()):
            name = self._species_name(other, tenant_key=tenant_key)
            if other in incompatible:
                hints.append(
                    NeighbourHint(
                        warn,
                        "companion.incompatible",
                        f"Incompatible neighbour: {name}.",
                        other,
                        sorted(set(slots)),
                    )
                )
            elif other in compatible:
                hints.append(
                    NeighbourHint(
                        "OK",
                        "companion.compatible",
                        f"Compatible neighbour: {name}.",
                        other,
                        sorted(set(slots)),
                        score=compatible[other],
                    )
                )
        hints.sort(key=lambda h: (SEVERITY_ORDER[h.severity], h.species_key))
        return hints

    def _species_name(self, species_key: str, *, tenant_key: str) -> str:
        """The name of a stored species key, only if the tenant may read it (else the key itself, #2082)."""
        species = readable_species(self._species, species_key, tenant_key)
        return species.scientific_name if species is not None else species_key

    def rotation_timeline(self, location_key: str, *, tenant_key: str, years: int | None = None) -> RotationTimeline:
        """Family, nutrient demand and plan role per year (GP-API-039, GP-ACC-028)."""
        return self._validator.rotation_timeline(location_key, tenant_key=tenant_key, years=years)

    # ── Backfill (GP-API-042) ────────────────────────────────────────────────

    def backfill(
        self,
        location_key: str,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        year: int,
        season: Literal["spring", "main", "autumn"] | None,
        species_key: str | None,
        family_key: str | None,
        plan_role: PlanRole,
    ) -> BackfillOutcome:
        """Record what stood in the bed in an earlier year (GP-FR-131 "Was stand hier {Jahr}?").

        The server writes ``care_event(planting, trigger = backfill)`` with ``performed_at`` at the middle of the
        season (1 July without one). ``year`` lies within ``current year - 10 .. current year - 1``. Species and
        family are resolved under the tenant; a species names its family, and a given family must agree with it.
        """
        resolve_owned_location(self._sites, location_key, tenant_key)
        this_year = today_utc().year
        if not this_year - BACKFILL_YEARS_BACK <= year <= this_year - 1:
            raise PlanError(
                ERROR_YEAR_RANGE,
                f"year must lie within {this_year - BACKFILL_YEARS_BACK}..{this_year - 1}.",
                status_code=422,
                field="year",
                minimum=this_year - BACKFILL_YEARS_BACK,
                maximum=this_year - 1,
            )
        resolved_family = family_key
        if species_key is not None:
            species = self._validator.visible_species(species_key, tenant_key=tenant_key)
            if resolved_family is None:
                resolved_family = species.family_key or None
            elif species.family_key and species.family_key != resolved_family:
                raise PlanError(
                    ERROR_FAMILY_MISMATCH,
                    "The species belongs to another family than family_key.",
                    status_code=422,
                    field="family_key",
                )
        family_name: str | None = None
        if resolved_family is not None:
            family = self._families.get_by_key(resolved_family)
            if family is None:
                raise _not_found("family_key")
            family_name = family.name
        if resolved_family is None and plan_role != PlanRole.FALLOW:
            raise PlanValidationError([(None, "family_key", "backfill.family_required", {})])

        month, day = _SEASON_MIDDLE[season]
        performed_at = datetime(year, month, day, 12, 0, tzinfo=UTC)
        entry = RotationEntry(
            year=year, season=season, family_key=resolved_family, species_key=species_key, plan_role=plan_role
        )
        summary = f"Backfill {year}: {family_name or 'fallow'} ({plan_role.value})"
        view = self._care.create(
            CareEventInput(location_key=location_key, category="planting", summary=summary, performed_at=performed_at),
            tenant_key=tenant_key,
            user_key=user_key,
            role=role,
            origin=CareEventOrigin(trigger="backfill", max_age_days=BACKFILL_MAX_AGE_DAYS, rotation_entry=entry),
        )
        logger.info("bed_rotation.backfilled", location_key=location_key, year=year, plan_role=plan_role.value)
        return BackfillOutcome(view.event.key or "", performed_at, entry)

    def cancel_backfill(
        self, location_key: str, event_key: str, *, tenant_key: str, user_key: str, role: TenantRole
    ) -> None:
        """Take a backfilled year back (``void_reason = backfill_error``): its author, or a lead (GP-API-042).

        Only a backfill of **this** bed can be cancelled here; any other event, a foreign one and an absent one
        answer the same 404, so the route cannot probe the care log.
        """
        if not MembershipEngine.can_edit_resource(role):
            raise ForbiddenError("Requires at least grower role.")
        resolve_owned_location(self._sites, location_key, tenant_key)
        event = self._care_repo.get(event_key, tenant_key=tenant_key)
        if (
            event is None
            or event.location_key != location_key
            or event.category != "planting"
            or event.trigger != "backfill"
        ):
            raise NotFoundError("CareEvent", event_key)
        if event.created_by != user_key and not MembershipEngine.can_delete_resource(role):
            raise ForbiddenError("Only the author or a lead may cancel this backfilled year.")
        self._care_repo.void(
            event_key, tenant_key=tenant_key, voided_by=user_key, reason=BACKFILL_ERROR_REASON, at=datetime.now(UTC)
        )
        logger.info("bed_rotation.backfill_cancelled", location_key=location_key, event_key=event_key)
