"""Crop rotation and companion hints for a bed, and the years a grower fills in afterwards (REQ-053 WP 3.4).

* :meth:`BedRotationService.validate_planting` — ``POST /locations/{key}/validate-planting`` (GP-API-025,
  GP-FR-131/132): the rotation finding of
  :class:`~app.domain.engines.crop_rotation_validator.CropRotationValidator` plus the companion-planting hints of
  the neighbours. **Hints only, never an error for a violation** (D-09).
* :meth:`BedRotationService.rotation_timeline` — ``GET /locations/{key}/rotation`` (GP-API-039, GP-FR-103).
* :meth:`BedRotationService.succession_recommendation` - ``GET /locations/{key}/succession-recommendation``
  (GP-FR-133): the families and species that fit the next step of the feeder cycle. Order only, no amounts.
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
from app.domain.engines.companion_planting_engine import CompanionVerdict, judge_neighbour
from app.domain.engines.crop_rotation_validator import (
    SEVERITY_ORDER,
    BedRotationResult,
    CropRotationValidator,
    FamilySource,
    RotationTimeline,
    Severity,
    _name_or_none,
    get_field,
    not_applicable_reason,
)
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.succession_recommendation_engine import (
    PreviousYear,
    SuccessionTarget,
    basis_family_keys,
    pause_held_back,
    planting_year,
    previous_year,
    species_fits,
    target_after,
)
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.graph_repository import IGraphRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.care_event import (
    BACKFILL_YEAR_WINDOW_DAYS,
    CareEventInput,
    CareEventOrigin,
    RotationEntry,
)
from app.domain.models.species_names import CANONICAL_NAME_LANGUAGE, localized_vernacular_name
from app.domain.services.care_event_service import BACKFILL_ERROR_REASON, CareEventService
from app.domain.services.location_ownership import resolve_owned_location, resolve_owned_slot
from app.domain.services.species_visibility import readable_species

logger = structlog.get_logger()

#: The first backfilled year is ``current year - 10``, the last ``current year - 1`` (GP-API-042).
BACKFILL_YEARS_BACK = 10

#: ``performed_at`` of a backfilled year: the middle of the season, or 1 July when none is named (GP-API-042).
_SEASON_MIDDLE: dict[str | None, tuple[int, int]] = {
    "spring": (4, 15),
    None: (7, 1),
    "main": (7, 1),
    "autumn": (9, 15),
}

#: At most this many families, and this many species per family, are listed (the response is bounded).
MAX_SUCCESSION_FAMILIES = 20
MAX_SUCCESSION_SPECIES_PER_FAMILY = 10
#: Candidate families evaluated per request (one species query each).
MAX_SUCCESSION_CANDIDATES = 40

SuccessionStatus = Literal[
    "ok",
    "not_applicable",
    "no_history",
    "demand_unknown",
    "no_successor_data",
    "no_matching_species",
]

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
class SuccessionSpecies:
    species_key: str
    scientific_name: str
    common_name: str | None
    nutrient_demand: str | None
    nitrogen_fixing: bool | None


@dataclass(frozen=True)
class SuccessionFamily:
    family_key: str
    family_name: str | None
    benefit_score: float | None
    benefit_reason: str | None
    #: The pause the family keeps in a bed; ``None`` when no source names one (nothing is assumed).
    pause_years: int | None
    species: list[SuccessionSpecies]


@dataclass(frozen=True)
class HeldBackFamily:
    """A follow-up family left out because its pause in this bed is not over."""

    family_key: str
    family_name: str | None
    last_year: int
    pause_years: int


@dataclass(frozen=True)
class SuccessionRecommendation:
    location_key: str
    applicable: bool
    not_applicable_reason: str | None
    status: SuccessionStatus
    previous: PreviousYear | None
    target: SuccessionTarget | None
    families: list[SuccessionFamily]
    held_back: list[HeldBackFamily]
    #: A fallow year is an option of the restoring step (it needs no species).
    fallow_option: bool


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
        care_service: CareEventService,
        validator: CropRotationValidator,
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._graph = graph_repo
        self._species = species_repo
        self._families = family_repo
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
        replant_of_plant_key: str | None = None,
    ) -> BedPlantingValidation:
        """Rotation and neighbour hints for planting ``species_key`` in the bed (GP-API-025).

        With ``slot_key`` the neighbours are the species in the slots next to it (``adjacent_to``, WP 3.3); without
        one every species standing or planned in the bed counts as a possible neighbour, and an incompatible one is
        an ``INFO`` — nobody knows yet where the new plant will stand. ``replant_of_plant_key`` names the died plant a
        replant replaces (#2888); the validator checks it under ``tenant_key`` and ignores any other key.
        """
        rotation = self._validator.validate_planting_in_location(
            location_key,
            species_key,
            tenant_key=tenant_key,
            rotation_window_years=rotation_window_years or DEFAULT_ROTATION_WINDOW_YEARS,
            replant_of_plant_key=replant_of_plant_key,
        )
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        scope: NeighbourScope = "bed"
        neighbour_slots: set[str] | None = None
        if slot_key is not None:
            try:
                slot, slot_location = resolve_owned_slot(self._sites, slot_key, tenant_key)
            except NotFoundError:
                raise _not_found("slot_key") from None
            if slot_location.key != location.key:
                raise _not_found("slot_key")
            scope = "slot"
            neighbour_slots = {
                get_field(row["slot"], "_key", "") for row in self._graph.get_adjacent_slots(slot.key or slot_key)
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
            get_field(row["species"], "_key", "")
            for row in self._graph.get_incompatible_species(species_key, tenant_key=tenant_key)
        }
        compatible = {
            get_field(row["species"], "_key", ""): get_field(row, "score")
            for row in self._graph.get_compatible_species(species_key, tenant_key=tenant_key)
        }
        warn: Severity = "WARNING" if scope == "slot" else "INFO"
        hints = [
            found
            for other, slots in sorted(present.items())
            if (
                found := self._hint(
                    other, slots, judge_neighbour(other, incompatible, compatible), warn, tenant_key=tenant_key
                )
            )
            is not None
        ]
        return sorted(hints, key=lambda h: (SEVERITY_ORDER[h.severity], h.species_key))

    def _hint(
        self,
        other: str,
        slots: list[str],
        verdict: CompanionVerdict,
        warn: Severity,
        *,
        tenant_key: str,
    ) -> NeighbourHint | None:
        """The hint for one neighbour species; *verdict* is the shared per-pair rule (:func:`judge_neighbour`)."""
        if verdict.status == "unknown":
            return None
        name = self._species_name(other, tenant_key=tenant_key)
        slot_keys = sorted(set(slots))
        if verdict.status == "incompatible":
            return NeighbourHint(warn, "companion.incompatible", f"Incompatible neighbour: {name}.", other, slot_keys)
        return NeighbourHint(
            "OK", "companion.compatible", f"Compatible neighbour: {name}.", other, slot_keys, score=verdict.score
        )

    def _species_name(self, species_key: str, *, tenant_key: str) -> str:
        """The name of a stored species key, only if the tenant may read it (else the key itself, #2082)."""
        species = readable_species(self._species, species_key, tenant_key)
        return species.scientific_name if species is not None else species_key

    def rotation_timeline(self, location_key: str, *, tenant_key: str, years: int | None = None) -> RotationTimeline:
        """Family, nutrient demand and plan role per year (GP-API-039, GP-ACC-028)."""
        return self._validator.rotation_timeline(location_key, tenant_key=tenant_key, years=years)

    def succession_recommendation(
        self, location_key: str, *, tenant_key: str, language: str = CANONICAL_NAME_LANGUAGE
    ) -> SuccessionRecommendation:
        """The families and species for the next year of a bed, by the feeder cycle and ``rotation_after`` (GP-FR-133).

        The previous year is the latest year of the bed's rotation timeline that has an entry; the step after it
        follows heavy -> medium -> light feeder -> green manure / fallow -> heavy. Candidate families are the
        ``rotation_after`` successors of the crop families (:func:`basis_family_keys`); a species whose pause in this
        bed - its own override, else its family's - is not over in the year of planting is left out, and a family with
        no species left is reported as held back. Species qualify only by their own stored ``nutrient_demand`` (or
        ``green_manure_suitable`` for the restoring step) and only if the tenant may read them. **Hints only:** no
        amount, and no recommendation is made for a step that cannot be derived (the ``status`` says why).
        """
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        reason = not_applicable_reason(location)
        if reason is not None:
            return SuccessionRecommendation(location_key, False, reason, "not_applicable", None, None, [], [], False)

        resolver = self._validator.timeline_resolver(tenant_key)
        entries, _reset_at = self._validator.bed_rotation_entries(location, tenant_key=tenant_key)
        today_year = today_utc().year
        rows = self._validator.timeline_rows(entries, from_year=today_year - 9, resolver=resolver)
        previous = previous_year(rows)
        if previous is None:
            return SuccessionRecommendation(location_key, True, None, "no_history", None, None, [], [], False)
        target = target_after(previous)
        if target is None:
            return SuccessionRecommendation(location_key, True, None, "demand_unknown", previous, None, [], [], False)
        # A fallow year is an option of the restoring step whatever the edge data says: it needs no species.
        fallow = target == "restoring"

        # Candidate families: the successors of the crop families, strongest edge first.
        basis = basis_family_keys(rows, previous)
        candidates: dict[str, tuple[float | None, str | None]] = {}
        for family_key in basis:
            for row in self._graph.get_rotation_successors(family_key):
                successor = get_field(row["family"], "_key", "")
                if not successor or successor in basis:
                    continue
                score = get_field(row, "benefit_score")
                if successor not in candidates or (score or 0.0) > (candidates[successor][0] or 0.0):
                    candidates[successor] = (score, get_field(row, "benefit_reason") or None)
        if not candidates:
            return SuccessionRecommendation(
                location_key, True, None, "no_successor_data", previous, target, [], [], fallow
            )

        last_stood: dict[str, int] = {
            key: max(row.year for row in rows if row.family_key == key and row.plan_role != PlanRole.FALLOW.value)
            for key in {row.family_key for row in rows if row.family_key and row.plan_role != PlanRole.FALLOW.value}
        }

        year = planting_year(previous, today_year)
        families: list[SuccessionFamily] = []
        held_back: list[HeldBackFamily] = []
        ordered = sorted(candidates, key=lambda key: (-(candidates[key][0] or 0.0), key))
        for family_key in ordered[:MAX_SUCCESSION_CANDIDATES]:
            score, benefit_reason = candidates[family_key]
            family = resolver.family(family_key)
            family_pause = family.rotation_pause_years if family is not None else None
            fitting = [
                species
                for species in self._species.search(family_key=family_key, tenant_key=tenant_key)
                if species_fits(species, target)
            ]
            if not fitting:
                continue
            # The pause is the species' own override, else the family's (as the planting hint reads it).
            last = last_stood[family_key] if family_key in last_stood else None  # noqa: SIM401 - call-graph ceiling
            open_species = [
                species
                for species in fitting
                if not pause_held_back(
                    last,
                    species.rotation_pause_years if species.rotation_pause_years is not None else family_pause,
                    year,
                )
            ]
            name = _name_or_none(family.name if family is not None else None)
            if not open_species:
                longest = max(
                    species.rotation_pause_years if species.rotation_pause_years is not None else family_pause or 0
                    for species in fitting
                )
                if len(held_back) < MAX_SUCCESSION_FAMILIES and last is not None:
                    held_back += [HeldBackFamily(family_key, name, last, longest)]
                continue
            if len(families) >= MAX_SUCCESSION_FAMILIES:
                continue
            open_species = sorted(open_species, key=lambda species: species.scientific_name)
            families += [
                SuccessionFamily(
                    family_key,
                    name,
                    score,
                    benefit_reason,
                    family_pause,
                    [
                        SuccessionSpecies(
                            species.key or "",
                            species.scientific_name,
                            # In the request's language (#2902).
                            localized_vernacular_name(species.common_names, species.common_names_i18n, language),
                            species.nutrient_demand.value if species.nutrient_demand is not None else None,
                            species.nitrogen_fixing,
                        )
                        for species in open_species[:MAX_SUCCESSION_SPECIES_PER_FAMILY]
                    ],
                )
            ]
        status: SuccessionStatus = "ok" if families or fallow else "no_matching_species"
        return SuccessionRecommendation(location_key, True, None, status, previous, target, families, held_back, fallow)

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
            origin=CareEventOrigin(trigger="backfill", max_age_days=BACKFILL_YEAR_WINDOW_DAYS, rotation_entry=entry),
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
        event = self._care.get(event_key, tenant_key=tenant_key, user_key=user_key).event
        if event.location_key != location_key or event.category != "planting" or event.trigger != "backfill":
            raise NotFoundError("CareEvent", event_key)
        # The care-event service decides who may cancel (the author of a backfilled year, or a lead) and refuses
        # a closed entry; it also writes the log line, so this path leaves no second void implementation behind.
        self._care.void(event_key, reason=BACKFILL_ERROR_REASON, tenant_key=tenant_key, user_key=user_key, role=role)
        logger.info("bed_rotation.backfill_cancelled", location_key=location_key, event_key=event_key)
