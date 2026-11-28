from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal, Protocol

from app.common.datetimes import today_utc
from app.common.enums import FailureCauseClass, PlanRole, TerminationCause, TerminationType
from app.common.exceptions import PlanError, PlanValidationError, RotationViolationError
from app.config.constants import (
    DEFAULT_ROTATION_WINDOW_YEARS,
    MAX_ROTATION_TIMELINE_YEARS,
    MAX_ROTATION_WINDOW_YEARS,
    MIN_ROTATION_TIMELINE_YEARS,
)
from app.domain.engines.bed_soil_hazard_engine import LocatedSoilHazard, effective_soil_hazards
from app.domain.engines.soil_hazard_planting_engine import PlantedSpecies, SoilHazardVerdict, judge_soil_hazards
from app.domain.interfaces.graph_repository import IGraphRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.rotation_history_repository import IRotationHistoryRepository, PlantedRow
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.soil_hazard_knowledge_source import ISoilHazardKnowledgeSource
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.bed_soil_hazard import CONTAINER_LOCATION_TYPES, BedSoilHazard
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.failure_cause import SOIL_BORNE_CLASSES
from app.domain.models.site import Location
from app.domain.models.species import Species
from app.domain.services.location_ancestry import location_ancestors
from app.domain.services.location_ownership import find_owned_location, read_slot, resolve_owned_location
from app.domain.services.species_visibility import readable_cultivar, readable_species

Severity = Literal["OK", "INFO", "WARNING", "CRITICAL"]

#: Strongest first: the order every result list is sorted in, the slot level and the bed level alike.
SEVERITY_ORDER: dict[str, int] = {"CRITICAL": 0, "WARNING": 1, "INFO": 2, "OK": 3}


@dataclass
class RotationValidationResult:
    severity: Severity
    message: str
    nitrogen_benefit: str | None = None
    pest_risk: dict | None = field(default=None)
    rotation_benefit: dict | None = field(default=None)


#: Location types whose substrate is changed instead of rotated (GP-FR-137, REQ-001): the bed-level check is off.
#: The vessels of REQ-053 §11.3a Nr. 5, which carry no soil hazard either (#2888 F-20) - one set for both.
ROTATION_OFF_LOCATION_TYPES: frozenset[str] = CONTAINER_LOCATION_TYPES

NOT_APPLICABLE_CONTAINER = "rotation.not_applicable.container"
NOT_APPLICABLE_EXEMPT = "rotation.not_applicable.rotation_exempt"
#: The bed's own switch (``Location.rotation_enabled = False``, #2544) turned the check off.
NOT_APPLICABLE_DISABLED = "rotation.not_applicable.disabled"

PauseSource = Literal["species", "family", "default"]
#: ``planned``: a run still planned at the bed (GP-FR-135 future columns) - only the rotation matrix reads it.
HistorySource = Literal["plant", "backfill", "planned"]

#: The order of the entries of one year, earliest in the season first (#2764): a spring pre-crop before the main
#: crop it preceded, an autumn follow-up after it. A plant carries no season; it reads as the main season.
SEASON_ORDER: dict[str | None, int] = {"spring": 0, "main": 1, None: 1, "autumn": 2}

#: A replant of the same family after a loss to one of these causes: the cause may sit in the soil (#2888).
BIOTIC_TERMINATION_CAUSES: frozenset[str] = frozenset({TerminationCause.DISEASE.value, TerminationCause.PEST.value})
#: Losses with no soil-borne link: frost, heat, drought, waterlogging, neglect, mechanical damage and premature
#: bolting (REQ-053 §11.3a Nr. 2, #2888 F-19) - no residual hint.
ABIOTIC_TERMINATION_CAUSES: frozenset[str] = frozenset(
    {
        TerminationCause.BOLTING.value,
        TerminationCause.FROST.value,
        TerminationCause.HEAT.value,
        TerminationCause.DROUGHT.value,
        TerminationCause.WATERLOGGING.value,
        TerminationCause.NEGLECT.value,
        TerminationCause.MECHANICAL.value,
    }
)
REPLANT_AFTER_BIOTIC_FAILURE = "rotation.replant_after_biotic_failure"
REPLANT_CAUSE_UNKNOWN = "rotation.replant_cause_unknown"
#: A loss with a cause class (REQ-053 §11.3a Nr. 4, #2888 F-21): a foliar disease - remove the residues, do not compost.
REPLANT_FOLIAR_DISEASE = "rotation.replant_foliar_disease"
#: A soil-borne loss without a confirmed pathogen on the bed: an overridable warning.
REPLANT_SOIL_BORNE = "rotation.replant_soil_borne"

#: Cause classes of a loss that leave nothing in the bed: no residual hint (§11.3a Nr. 4).
NO_HINT_FAILURE_CLASSES: frozenset[str] = frozenset(
    {FailureCauseClass.ABIOTIC.value, FailureCauseClass.MECHANICAL.value, FailureCauseClass.PEST_FOLIAR.value}
)
_SOIL_BORNE_CLASS_VALUES: frozenset[str] = frozenset(cls.value for cls in SOIL_BORNE_CLASSES)


def _substrate_replaced_on(location: Location) -> date | None:
    """The day the bed's substrate was renewed (REQ-053 §11.3a Nr. 7), ``None`` when never."""
    return location.soil_profile.substrate_replaced_on if location.soil_profile is not None else None


#: The longest stay that is still "one season" for the replant rule (REQ-053 v1.61 §11.3a Nr. 3, D-S4).
MAX_ONE_SEASON_DAYS = 365


def _stood_one_season(planted_on: date, removed_on: date) -> bool:
    """Whether a plant stood one season at most: planted at most :data:`MAX_ONE_SEASON_DAYS` (UTC days) before its loss.

    The operator decision names "the same or the previous calendar year"; the day bound alone keeps its own example
    apart - April 2024 to September 2025 lies in "the year before" too, yet stood through two summers and must count
    (D-S4, REQ-053 v1.62 §11.3a Nr. 3). Within 365 days the calendar-year condition always holds.
    """
    return (removed_on - planted_on).days <= MAX_ONE_SEASON_DAYS


class FamilySource(Protocol):
    """The one read the bed-level check needs of the botanical-family catalogue (a global catalogue)."""

    def get_by_key(self, key: str) -> BotanicalFamily | None: ...


@dataclass(frozen=True)
class RotationFinding:
    """One reason to look twice, or the absence of one (GP-FR-131). Always a hint, never a blocker (D-09)."""

    severity: Severity
    code: str
    message: str
    family_key: str | None = None
    #: Display name of ``family_key`` from the family catalogue; ``None`` when the family is unknown or unnamed.
    #: Consumers must never show ``family_key`` as a name in its place.
    family_name: str | None = None
    species_key: str | None = None
    last_year: int | None = None
    years_since: int | None = None
    pause_years: int | None = None
    pause_source: PauseSource | None = None
    plan_role: str | None = None
    pest_risk: dict[str, Any] | None = None
    #: The cause of the loss a replant follows (``rotation.replant_*`` findings only, #2888).
    termination_cause: str | None = None
    #: The cause class of that loss (``rotation.replant_*`` findings of a loss with a class, #2888 F-21).
    failure_cause_class: str | None = None
    #: ``soil_hazard.*`` findings only (REQ-053 §11.3a Nr. 6, #2888 F-21): the hazard of the bed, its confirmation,
    #: the stage, the end of the pause or of the evidenced residual risk (``None`` = no time statement) and the host
    #: entry of the knowledge table the species matched.
    hazard: str | None = None
    hazard_confirmed_at: date | None = None
    hazard_stage: str | None = None
    hazard_until: date | None = None
    host_level: str | None = None
    host_name: str | None = None
    #: A hazard inherited from a location above the bed (REQ-053 v1.61 §11.3a Nr. 6): that location's key and name,
    #: read from the bed's own checked parent chain; both ``None`` for a hazard of the bed itself.
    hazard_location_key: str | None = None
    hazard_location_name: str | None = None


@dataclass(frozen=True)
class BedRotationResult:
    location_key: str
    species_key: str
    applicable: bool
    not_applicable_reason: str | None
    severity: Severity
    findings: list[RotationFinding]
    rotation_window_years: int
    rotation_reset_at: date | None = None


@dataclass(frozen=True)
class HistoryEntry:
    """One family-year in a bed: what stood there (a plant), what the grower recorded afterwards (a backfill) or, in
    the rotation matrix only, a run still planned there (``planned``)."""

    year: int
    family_key: str | None
    species_key: str | None
    plan_role: str
    season: str | None
    source: HistorySource
    event_key: str | None = None


def _history_order(entry: HistoryEntry) -> tuple[Any, ...]:
    """Newest year first; within a year spring, main, autumn (:data:`SEASON_ORDER`), then family, species, source."""
    return (
        -entry.year,
        SEASON_ORDER.get(entry.season, 1),
        entry.family_key or "",
        entry.species_key or "",
        entry.source,
    )


@dataclass(frozen=True)
class TimelineEntry:
    year: int
    season: str | None
    family_key: str | None
    family_name: str | None
    species_key: str | None
    nutrient_demand: str | None
    plan_role: str
    source: HistorySource
    event_key: str | None = None


@dataclass(frozen=True)
class RotationTimeline:
    location_key: str
    years: int
    from_year: int
    to_year: int
    applicable: bool
    not_applicable_reason: str | None
    rotation_reset_at: date | None
    entries: list[TimelineEntry]


def pause_severity(years_since: int, pause_years: int) -> Severity:
    """The nearer the last crop of the family, the stronger the hint: at most half the pause elapsed is critical."""
    return "CRITICAL" if years_since * 2 <= pause_years else "WARNING"


def resolve_pause_years(
    species: Species, family: BotanicalFamily | None, rotation_window_years: int
) -> tuple[int, PauseSource]:
    """Species override, else the family default, else the window the caller passed (GP-FR-131, K-004)."""
    if species.rotation_pause_years is not None:
        return species.rotation_pause_years, "species"
    if family is not None and family.rotation_pause_years is not None:
        return family.rotation_pause_years, "family"
    return rotation_window_years, "default"


def not_applicable_reason(location: Location) -> str | None:
    """Why the bed-level rotation check is off for this location, or ``None`` when it applies (GP-FR-137).

    Precedence: a permanent crop (``rotation_exempt``) is off whatever else is set; then the bed's own switch
    ``rotation_enabled`` (``True`` on, ``False`` off, #2544); then the type default - off for ``planter`` /
    ``tent`` / ``shelf``, on for every other type. ``rotation_enabled = None`` is today's behaviour.
    """
    if location.rotation_exempt:
        return NOT_APPLICABLE_EXEMPT
    if location.rotation_enabled is True:
        return None
    if location.rotation_enabled is False:
        return NOT_APPLICABLE_DISABLED
    if location.location_type_key in ROTATION_OFF_LOCATION_TYPES:
        return NOT_APPLICABLE_CONTAINER
    return None


def get_field(row: Mapping[str, Any], key: str, default: Any = None) -> Any:
    """``row[key]`` or ``default`` — a graph row is a plain mapping."""
    return row[key] if key in row else default  # noqa: SIM401 — one resolved site instead of a dict call per use


def _pause_of(holder: Species | BotanicalFamily | None) -> int | None:
    """The pause a species or a family names, ``None`` when it names none."""
    return holder.rotation_pause_years if holder is not None else None


def _name_or_none(name: str | None) -> str | None:
    """A usable family name, ``None`` for a missing or blank one."""
    return name.strip() or None if name else None


def _pause_finding(
    family_key: str,
    family_name: str | None,
    pause: int,
    source: PauseSource,
    same: list[HistoryEntry],
    today_year: int,
) -> RotationFinding | None:
    """The finding for the most recent year the same family stood in the bed, if the pause has not elapsed."""
    if not same:
        return None
    last = max(same, key=lambda e: e.year)
    years_since = today_year - last.year
    if years_since >= pause:
        return None
    when = "this year" if years_since == 0 else f"{years_since} year(s) ago"
    role = " as green manure" if last.plan_role == PlanRole.GREEN_MANURE.value else ""
    return RotationFinding(
        pause_severity(years_since, pause),
        "rotation.pause_not_elapsed",
        f"{_family_phrase(family_name)} grew in this bed{role} {when}; the pause is {pause} year(s) ({source}).",
        family_key=family_key,
        family_name=family_name,
        species_key=last.species_key,
        last_year=last.year,
        years_since=years_since,
        pause_years=pause,
        pause_source=source,
        plan_role=last.plan_role,
    )


def _class_finding(
    replaced: PlantedRow,
    family_key: str,
    family_name: str | None,
    *,
    bed_hazards: frozenset[str],
    substrate_replaced_on: date | None,
) -> RotationFinding | None:
    """The residual hint of a loss that carries a cause class (REQ-053 §11.3a Nr. 4, #2888 F-21).

    ``abiotic``, ``mechanical``, ``pest_foliar``: nothing. ``disease_foliar``: an ``INFO`` - remove the residues, do
    not put them on the garden compost. ``pest_soil`` / ``disease_soil``: an overridable ``WARNING``, unless the
    confirmed pathogen stands on the bed as a soil hazard (its own finding speaks, §11.3a Nr. 6) or the substrate was
    renewed after the loss (§11.3a Nr. 7). ``unknown``: an ``INFO``.
    """
    cls = replaced.failure_cause_class
    if cls in NO_HINT_FAILURE_CLASSES:
        return None
    if cls == FailureCauseClass.DISEASE_FOLIAR.value:
        severity: Severity = "INFO"
        code = REPLANT_FOLIAR_DISEASE
        message = (
            "The plant this replant follows died from a foliar disease; remove its residues and keep them off the "
            "garden compost."
        )
    elif cls in _SOIL_BORNE_CLASS_VALUES:
        removed = replaced.removed_on
        renewed = substrate_replaced_on is not None and removed is not None and substrate_replaced_on > removed
        recorded = replaced.failure_pathogen_confirmed is True and replaced.failure_pathogen in bed_hazards
        if renewed or recorded:
            return None
        severity = "WARNING"
        code = REPLANT_SOIL_BORNE
        message = (
            "The plant this replant follows died from a soil-borne cause without a confirmed pathogen; the new plant "
            "can fail the same way."
        )
    else:
        severity = "INFO"
        code = REPLANT_CAUSE_UNKNOWN
        message = "The plant this replant follows died from an unknown cause."
    return RotationFinding(
        severity,
        code,
        message,
        family_key=family_key,
        family_name=family_name,
        species_key=replaced.species_key,
        last_year=replaced.removed_on.year if replaced.removed_on is not None else None,
        termination_cause=replaced.termination_cause,
        failure_cause_class=cls,
    )


def _replant_finding(
    replaced: PlantedRow,
    family_key: str,
    family_name: str | None,
    *,
    bed_hazards: frozenset[str] = frozenset(),
    substrate_replaced_on: date | None = None,
) -> RotationFinding | None:
    """The residual hint of replanting the same family after ``replaced`` died in its season (#2888).

    A loss with a cause class follows the class (:func:`_class_finding`, REQ-053 §11.3a Nr. 4). A loss without one
    (legacy data, "Beet räumen") follows its ``termination_cause`` as before: disease or pest a ``WARNING`` - if the
    cause sits in the soil, the new plant can fail the same way; no cause or ``unknown`` (or a cause this rule does not
    know yet) an ``INFO``; a frost, heat, drought, waterlogging, neglect, mechanical or bolting loss leaves nothing in
    the soil: no finding. Never ``CRITICAL`` - a hint, not a block (D-09).
    """
    if replaced.failure_cause_class is not None:
        return _class_finding(
            replaced,
            family_key,
            family_name,
            bed_hazards=bed_hazards,
            substrate_replaced_on=substrate_replaced_on,
        )
    cause = replaced.termination_cause
    if cause in ABIOTIC_TERMINATION_CAUSES:
        return None
    if cause in BIOTIC_TERMINATION_CAUSES:
        severity: Severity = "WARNING"
        code = REPLANT_AFTER_BIOTIC_FAILURE
        message = (
            f"The plant this replant follows died from {cause} in its season; if the cause sits in the soil, "
            "the new plant can fail the same way."
        )
    else:
        severity = "INFO"
        code = REPLANT_CAUSE_UNKNOWN
        message = "The plant this replant follows died in its season from an unrecorded cause."
    return RotationFinding(
        severity,
        code,
        message,
        family_key=family_key,
        family_name=family_name,
        species_key=replaced.species_key,
        last_year=replaced.removed_on.year if replaced.removed_on is not None else None,
        termination_cause=cause,
    )


def _family_phrase(family_name: str | None) -> str:
    """The family in an English message: its name, never its database key."""
    return f"Family '{family_name}'" if family_name else "The same family"


def _hazard_message(verdict: SoilHazardVerdict, origin_name: str | None = None) -> str:
    """The English text of a soil-hazard finding; the UI words it from the code and the fields."""
    hazard = verdict.hazard.value
    confirmed = verdict.confirmed_at.isoformat()
    if verdict.stage == "pause":
        stage = f"keep its hosts out of this bed until {verdict.until.year if verdict.until else '?'}"
    elif verdict.stage == "no_evidenced_pause":
        stage = "no cultivation pause is evidenced"
    elif verdict.until is not None:
        stage = f"the pause is over, a residual risk remains until {verdict.until.year}"
    else:
        stage = "the pause is over, a residual risk remains"
    where = f"at '{origin_name}' above this bed" if origin_name is not None else "in this bed"
    return f"This species is a host of {hazard}, confirmed {where} on {confirmed}; {stage}."


def soil_hazard_finding(
    verdict: SoilHazardVerdict, species_key: str, origin: Location | None = None
) -> RotationFinding:
    """A verdict of :func:`judge_soil_hazards` as a finding of the planting check (REQ-053 §11.3a Nr. 6).

    ``origin`` is the location above the bed that holds an inherited hazard (``None`` for the bed's own).
    """
    return RotationFinding(
        verdict.severity,
        verdict.code,
        _hazard_message(verdict, origin.name if origin is not None else None),
        species_key=species_key,
        hazard=verdict.hazard.value,
        hazard_confirmed_at=verdict.confirmed_at,
        hazard_stage=verdict.stage,
        hazard_until=verdict.until,
        host_level=verdict.host.level.value,
        host_name=verdict.host.name,
        hazard_location_key=origin.key if origin is not None else None,
        hazard_location_name=origin.name if origin is not None else None,
    )


def _pest_finding(
    family_key: str,
    family_name: str | None,
    risk: Mapping[str, Any],
    recent: set[str | None],
    other_name: Callable[[str], str | None],
) -> RotationFinding | None:
    """A high shared-pest risk with a family that grew in the bed within the pause."""
    other = get_field(get_field(risk, "family", {}), "_key", "")
    if other not in recent or get_field(risk, "risk_level") != "high":
        return None
    other_family = get_field(risk, "family", {})
    name = _name_or_none(get_field(other_family, "name", None)) or other_name(other)
    own = f"'{family_name}'" if family_name else "this family"
    theirs = f"'{name}'" if name else "another family"
    return RotationFinding(
        "WARNING",
        "rotation.pest_risk",
        f"High pest risk between {own} and {theirs}, which grew in this bed recently.",
        family_key=other,
        family_name=name,
        pest_risk={
            "shared_pests": get_field(risk, "shared_pests", []),
            "shared_diseases": get_field(risk, "shared_diseases", []),
            "risk_level": get_field(risk, "risk_level"),
        },
    )


class TimelineResolver:
    """Cached lookups of the family catalogue and the tenant-visible species for one timeline or matrix read."""

    def __init__(self, families: FamilySource, species_repo: ISpeciesRepository, tenant_key: str) -> None:
        self._families = families
        self._species_repo = species_repo
        self._tenant_key = tenant_key
        self._family_cache: dict[str, BotanicalFamily | None] = {}
        self._species_cache: dict[str, Species | None] = {}

    def family(self, key: str | None) -> BotanicalFamily | None:
        if key is None:
            return None
        if key not in self._family_cache:
            self._family_cache[key] = self._families.get_by_key(key)
        return self._family_cache[key]

    def species(self, key: str | None) -> Species | None:
        if key is None:
            return None
        if key not in self._species_cache:
            self._species_cache[key] = readable_species(self._species_repo, key, self._tenant_key)
        return self._species_cache[key]


class CropRotationValidator:
    """Validates crop rotation rules for a slot — and, since REQ-053 WP 3.4, for a whole bed.

    The slot-level :meth:`validate_planting` is the original check (kept for the planting-run flow). The bed-level
    :meth:`validate_planting_in_location` and :meth:`rotation_timeline` merge the history of every slot of a bed
    (GP-FR-131, GP-FR-103); their collaborators are optional so the slot-level construction sites stay as they are.
    """

    def __init__(
        self,
        plant_repo: IPlantInstanceRepository,
        species_repo: ISpeciesRepository,
        graph_repo: IGraphRepository | None = None,
        *,
        site_repo: ISiteRepository | None = None,
        family_repo: FamilySource | None = None,
        history_repo: IRotationHistoryRepository | None = None,
        soil_hazards: ISoilHazardKnowledgeSource | None = None,
    ) -> None:
        self._plant_repo = plant_repo
        self._species_repo = species_repo
        self._graph_repo = graph_repo
        self._sites: ISiteRepository | None = site_repo
        self._families: FamilySource | None = family_repo
        self._history: IRotationHistoryRepository | None = history_repo
        #: The soil-hazard knowledge table (REQ-054 §5.2a); without it the bed check reports no soil hazard.
        self._soil_hazards: ISoilHazardKnowledgeSource | None = soil_hazards

    def validate_planting(
        self,
        slot_key: str,
        species_key: str,
        rotation_window_years: int = DEFAULT_ROTATION_WINDOW_YEARS,
        *,
        tenant_key: str,
    ) -> list[RotationValidationResult]:
        """Check crop rotation and return differentiated results.

        ``tenant_key`` is required and keyword-only (#927): the slot history this
        reads is a tenant-scoped repository query, and the results name the
        botanical families previously grown in that bed.

        The bed's switch decides first (GP-FR-137, D-09, #2544): when the slot's bed is off
        (:func:`not_applicable_reason` - ``rotation_exempt``, ``rotation_enabled = False`` or a
        ``planter`` / ``tent`` / ``shelf`` not switched on) the answer is one ``INFO`` and nothing is
        read, so neither a planting nor a run's ``create_plants`` is refused on that bed. Needs
        ``site_repo``; without it (a construction that predates the switch) every slot is checked.
        """
        off_reason = self._slot_not_applicable_reason(slot_key, tenant_key)
        if off_reason is not None:
            return [
                RotationValidationResult(
                    severity="INFO", message=f"Crop rotation does not apply to this bed ({off_reason})"
                )
            ]

        results: list[RotationValidationResult] = []

        species = self._species_repo.get_by_key(species_key)
        if species is None:
            return [RotationValidationResult(severity="CRITICAL", message="Species not found")]

        planned_family_key = species.family_key
        if not planned_family_key:
            return [RotationValidationResult(severity="INFO", message="No family assigned — cannot evaluate rotation")]

        # Check if planned family is nitrogen-fixing
        planned_family = None
        try:
            from app.common.dependencies import get_family_repo

            family_repo = get_family_repo()
            planned_family = family_repo.get_by_key(planned_family_key)
        except Exception:
            pass

        history = self._plant_repo.get_history_by_slot(slot_key, years=rotation_window_years, tenant_key=tenant_key)

        for past_plant in history:
            past_species = self._species_repo.get_by_key(past_plant.species_key)
            if past_species is None:
                continue

            past_family_key = past_species.family_key
            if not past_family_key:
                continue

            # CRITICAL: Same family planted within rotation window
            if past_family_key == planned_family_key:
                results.append(
                    RotationValidationResult(
                        severity="CRITICAL",
                        message=(
                            f"Same family '{planned_family_key}' was planted in this slot"
                            f" within the last {rotation_window_years} years"
                        ),
                    )
                )
                continue

            # WARNING: shared pest risk (high)
            if self._graph_repo:
                pest_risks = self._graph_repo.get_pest_risks(planned_family_key)
                for pr in pest_risks:
                    pr_family_key = pr["family"].get("_key", "")
                    if pr_family_key == past_family_key and pr.get("risk_level") == "high":
                        results.append(
                            RotationValidationResult(
                                severity="WARNING",
                                message=(
                                    f"High pest risk between family '{planned_family_key}'"
                                    f" and previously planted '{past_family_key}'"
                                ),
                                pest_risk={
                                    "shared_pests": pr.get("shared_pests", []),
                                    "shared_diseases": pr.get("shared_diseases", []),
                                    "risk_level": pr.get("risk_level"),
                                },
                            )
                        )

            # OK: good rotation (benefit edge exists)
            if self._graph_repo:
                successors = self._graph_repo.get_rotation_successors(past_family_key)
                for succ in successors:
                    succ_family_key = succ["family"].get("_key", "")
                    if succ_family_key == planned_family_key:
                        results.append(
                            RotationValidationResult(
                                severity="OK",
                                message=(
                                    f"Good rotation: '{planned_family_key}' is a recommended"
                                    f" successor for '{past_family_key}'"
                                ),
                                rotation_benefit={
                                    "benefit_score": succ.get("benefit_score", 0.0),
                                    "benefit_reason": succ.get("benefit_reason", ""),
                                },
                            )
                        )

        # Nitrogen benefit note
        if planned_family and getattr(planned_family, "nitrogen_fixing", False):
            for r in results:
                r.nitrogen_benefit = "Nitrogen-fixing species improves soil for subsequent crops"

        if not results:
            results.append(
                RotationValidationResult(
                    severity="INFO",
                    message="No specific rotation recommendation for this combination",
                )
            )

        # Legacy compat: return highest severity first
        results.sort(key=lambda r: SEVERITY_ORDER.get(r.severity, 99))

        return results

    def _slot_not_applicable_reason(self, slot_key: str, tenant_key: str) -> str | None:
        """Why the rotation check is off for the bed of ``slot_key``, or ``None`` when it applies.

        ``None`` too when the bed cannot be read: no ``site_repo``, an unknown slot, or a bed of another tenant -
        those keep the slot check they had (a foreign slot's history is empty under the tenant anyway).
        """
        if self._sites is None or not slot_key:
            return None
        slot = read_slot(self._sites, slot_key, tenant_key)
        if slot is None or not slot.location_key:
            return None
        location = find_owned_location(self._sites, slot.location_key, tenant_key)
        return not_applicable_reason(location) if location is not None else None

    def validate_or_raise(
        self,
        slot_key: str,
        species_key: str,
        rotation_window_years: int = DEFAULT_ROTATION_WINDOW_YEARS,
        *,
        tenant_key: str,
    ) -> None:
        results = self.validate_planting(slot_key, species_key, rotation_window_years, tenant_key=tenant_key)
        for r in results:
            if r.severity == "CRITICAL":
                species = self._species_repo.get_by_key(species_key)
                family = species.family_key if species else "unknown"
                raise RotationViolationError(family, slot_key, rotation_window_years)

    # ── Bed level (REQ-053 WP 3.4, GP-FR-131, GP-FR-103) ─────────────────────────

    def _bed_collaborators(self) -> tuple[ISiteRepository, FamilySource, IRotationHistoryRepository]:
        if self._sites is None or self._families is None or self._history is None:
            raise RuntimeError("The bed-level rotation check needs site_repo, family_repo and history_repo.")
        return self._sites, self._families, self._history

    def visible_species(self, species_key: str, *, tenant_key: str) -> Species:
        """The species behind ``species_key`` if the tenant can see it (own, global or granted), else a 422.

        A foreign tenant's species answers exactly like an unknown key (GP-NFR-058): the reference in a body is
        ``reference.not_found`` for both.
        """
        species = readable_species(self._species_repo, species_key, tenant_key) if species_key and tenant_key else None
        if species is None:
            raise PlanValidationError([(None, "species_key", "reference.not_found", {})])
        return species

    @staticmethod
    def _check_window(rotation_window_years: int) -> None:
        if not 1 <= rotation_window_years <= MAX_ROTATION_WINDOW_YEARS:
            raise PlanError(
                "rotation.window_out_of_range",
                f"rotation_window_years must lie within 1..{MAX_ROTATION_WINDOW_YEARS}.",
                status_code=422,
                field="rotation_window_years",
                limit=MAX_ROTATION_WINDOW_YEARS,
            )

    def _family_source(self) -> FamilySource:
        return self._bed_collaborators()[1]

    def _family_of(self, species_key: str, cache: dict[str, str | None], tenant_key: str) -> str | None:
        """The family of a stored species key, resolved under the tenant (a legacy key may name a foreign species)."""
        if species_key not in cache:
            species = readable_species(self._species_repo, species_key, tenant_key)
            cache[species_key] = species.family_key if species is not None else None
        return cache[species_key]

    @staticmethod
    def _history_since(location: Location, from_year: int) -> date:
        """1 January of ``from_year``, or the bed's ``rotation_reset_at`` when that is later (GP-FR-131)."""
        reset_at = location.soil_profile.rotation_reset_at if location.soil_profile is not None else None
        since = date(from_year, 1, 1)
        return reset_at if reset_at is not None and reset_at > since else since

    def _replaced_plant(
        self, location: Location, plant_key: str | None, *, tenant_key: str
    ) -> tuple[PlantedRow, bool] | None:
        """The plant a replant names and whether it leaves out all its years - or ``None`` when it counts (#2888).

        It must be a plant of this bed and this tenant (the tenant- and bed-scoped history read is the predicate),
        must have died (``termination_type = died``) after the bed's ``rotation_reset_at``, and the replant must fall
        into its season (:meth:`_replant_season`). A key that fails any of it - unknown, another tenant's, another
        bed's, a harvested or senesced plant, a loss of an earlier season - is ignored: the plant counts as before and
        the answer says nothing about it (no oracle for another tenant's plants).
        """
        if not plant_key:
            return None
        history: IRotationHistoryRepository = self._bed_collaborators()[2]
        today: date = today_utc()
        # A season reaches back at most one window: the bounded look-back of the rotation check (8 years).
        since = self._history_since(location, today.year - MAX_ROTATION_WINDOW_YEARS)
        for plant in history.list_plantings(location.key or "", since=since, tenant_key=tenant_key):
            if (
                plant.plant_key == plant_key
                and plant.termination_type == TerminationType.DIED.value
                and plant.removed_on is not None
            ):
                whole = self._replant_season(plant, today, tenant_key=tenant_key)
                return (plant, whole) if whole is not None else None
        return None

    def _replant_season(self, plant: PlantedRow, today: date, *, tenant_key: str) -> bool | None:
        """Whether a replant today falls into the season of the died ``plant`` (REQ-053 §11.3a Nr. 3, #2888 F-21).

        ``True``: inside its cultivation window (``planted_on + days_to_maturity`` of the plant's cultivar - the only
        culture duration the catalogue keeps) **and** it stood one season at most (:func:`_stood_one_season`, operator
        decision D-S4 2026-11-28) - the plant is no previous crop at all, so an autumn garlic replaced in March does
        not count for last year either. A plant inside its window that stood longer leaves out only the year of its
        loss (``False``): a 1000-day cultivar planted in April 2024 and lost in September 2025 counts for 2024.
        ``False``: the calendar-year rule - only the year of the loss is
        left out, earlier years still count; it applies to a plant without a cultivar or a cultivar without
        ``days_to_maturity`` (or one the tenant may not read), and to a plant that stood past its window (a perennial
        crop). ``None``: outside the season - the plant counts as a previous crop.
        """
        removed = plant.removed_on
        if removed is None:
            return None
        cultivar = readable_cultivar(self._species_repo, plant.cultivar_key, tenant_key) if plant.cultivar_key else None
        days = cultivar.days_to_maturity if cultivar is not None and cultivar.species_key == plant.species_key else None
        window_end = plant.planted_on + timedelta(days=days) if days is not None else None
        if window_end is None or removed > window_end:
            return False if removed.year == today.year else None
        if today > window_end:
            return None
        if _stood_one_season(plant.planted_on, removed):
            return True
        # Longer than one season: exactly the perennial rule above (REQ-053 v1.62 §11.3a Nr. 3) - only the year of the
        # loss stays out, and only for a replant in that year; in a later year the plant counts in full.
        return False if removed.year == today.year else None

    def _bed_history(
        self,
        location: Location,
        *,
        from_year: int,
        tenant_key: str,
        skip_plant_key: str | None = None,
        skip_whole: bool = False,
    ) -> tuple[list[HistoryEntry], date | None]:
        """Every family-year of the bed since ``from_year``, from ``rotation_reset_at`` on (GP-FR-131).

        Newest year first; within a year by :data:`SEASON_ORDER` (spring, main, autumn), so every view that groups
        these rows by year - the bed's timeline and the site rotation matrix - lists a year chronologically.
        Plants count for every year they stood (a plant put in last spring and still there occupies this year too);
        a green manure counts with its family; a mixed bed contributes every family of the year. A backfill counts
        for its calendar year. Duplicates (ten tomato plants in one year) collapse into one entry.

        ``skip_plant_key`` leaves one plant's current year out - only the planting check passes it, for the plant a
        replant replaces (#2888, :meth:`_replaced_plant`); the timeline and the rotation matrix never do. With
        ``skip_whole`` the plant leaves out every year it stood (a replant inside its cultivation window, §11.3a Nr. 3).
        """
        history: IRotationHistoryRepository = self._bed_collaborators()[2]
        today: date = today_utc()
        reset_at = location.soil_profile.rotation_reset_at if location.soil_profile is not None else None
        since = self._history_since(location, from_year)
        family_cache: dict[str, str | None] = {}
        found: dict[tuple[Any, ...], HistoryEntry] = {}
        for plant in history.list_plantings(location.key or "", since=since, tenant_key=tenant_key):
            if skip_whole and skip_plant_key is not None and plant.plant_key == skip_plant_key:
                continue
            end = min(plant.removed_on or today, today)
            # The replaced plant leaves out the year it died in (the current one); a year it stood before that - a
            # perennial that lived through last season - was a real previous crop and still counts.
            last_year = end.year - 1 if skip_plant_key is not None and plant.plant_key == skip_plant_key else end.year
            first = max(plant.planted_on, since)
            family = self._family_of(plant.species_key, family_cache, tenant_key)
            for year in range(first.year, last_year + 1):
                entry = HistoryEntry(year, family, plant.species_key, plant.plan_role, None, "plant")
                found[(year, family, plant.species_key, plant.plan_role, None, "plant")] = entry
        for row in history.list_backfills(
            location.key or "", since=datetime(since.year, since.month, since.day, tzinfo=UTC), tenant_key=tenant_key
        ):
            entry_data = row.entry
            entry = HistoryEntry(
                entry_data.year,
                entry_data.family_key,
                entry_data.species_key,
                entry_data.plan_role.value,
                entry_data.season,
                "backfill",
                row.event_key,
            )
            found[(row.event_key,)] = entry
        entries = [e for e in found.values() if e.year >= from_year]
        return sorted(entries, key=_history_order), reset_at

    def validate_planting_in_location(
        self,
        location_key: str,
        species_key: str,
        *,
        tenant_key: str,
        rotation_window_years: int = DEFAULT_ROTATION_WINDOW_YEARS,
        replant_of_plant_key: str | None = None,
    ) -> BedRotationResult:
        """Crop-rotation hint for planting ``species_key`` in the bed ``location_key`` (GP-FR-131, GP-API-025).

        The history of **all** slots of the bed, from ``rotation_reset_at`` on, decides: how many years ago the
        same family stood there, against the pause of the species (override), the family, or
        ``rotation_window_years`` (at most 8). A green manure counts with its family. The answer is a list of
        findings with a severity and a reason — never an error for a violation (D-09: the grower decides).
        Off for ``rotation_exempt`` beds and, unless the bed is switched on (``rotation_enabled``), for ``planter`` /
        ``tent`` / ``shelf``; a bed switched off is off whatever its type (GP-FR-137, :func:`not_applicable_reason`).

        ``replant_of_plant_key`` names the plant a replant replaces (REQ-053 §11.3 "ausgefallen", §11.3a Nr. 3, #2888):
        a died plant of this bed and tenant is no previous crop for this one check when the replant falls into its
        season - inside its cultivation window (``planted_on`` plus its cultivar's ``days_to_maturity``) in no year,
        without a window or after standing past it only in the year of its loss (:meth:`_replant_season`).
        Replanting its family adds a residual hint from its cause class, else its ``termination_cause``
        (:func:`_replant_finding`). Any other key is ignored without an error.

        The bed's soil hazards are checked for every species whose host it is, also when the rotation check is off
        (REQ-053 §11.3a Nr. 6, :meth:`_soil_hazard_findings`).

        ``tenant_key`` is required and keyword-only (#2107): the bed is resolved through its site, the species must
        be visible to the tenant, and the history is read under the tenant.

        Raises:
            NotFoundError: the bed is absent or another tenant's.
            PlanValidationError: ``species_key`` is unknown or not visible (422 ``reference.not_found``).
            PlanError: ``rotation_window_years`` lies outside 1..8 (422 ``rotation.window_out_of_range``).
        """
        sites: ISiteRepository = self._bed_collaborators()[0]
        families: FamilySource = self._bed_collaborators()[1]
        location = resolve_owned_location(sites, location_key, tenant_key)
        self._check_window(rotation_window_years)
        species = self.visible_species(species_key, tenant_key=tenant_key)
        reset_at = location.soil_profile.rotation_reset_at if location.soil_profile is not None else None
        family = families.get_by_key(species.family_key) if species.family_key else None
        family_name = _name_or_none(family.name if family is not None else None)
        # The soil hazards hang on the soil, not on the rotation: checked before the rotation switch (GP-FR-137,
        # REQ-053 §11.3a Nr. 6) - a rotation_exempt bed or one switched off still reports them.
        # The soil's hazards: the bed's own and its parent chain's (a walnut's juglone at the garden above), none in
        # a vessel or at an own hydroponic value; under inherited hydroponics only its own (REQ-053 §11.3a Nr. 5
        # v1.61) - one read for both uses below.
        bed_hazards = effective_soil_hazards(location, location_ancestors(sites, location))
        hazards = self._soil_hazard_findings(location, bed_hazards, species, family_name)

        reason = not_applicable_reason(location)
        if reason is not None:
            return self._bed_result(location_key, species_key, reason, hazards, rotation_window_years, reset_at)
        if not species.family_key:
            finding = RotationFinding(
                "INFO", "rotation.no_family", "No family assigned — cannot evaluate rotation.", species_key=species_key
            )
            return self._bed_result(
                location_key, species_key, None, [*hazards, finding], rotation_window_years, reset_at
            )

        pause, source = resolve_pause_years(species, family, rotation_window_years)
        today_year = today_utc().year
        replaced = self._replaced_plant(location, replant_of_plant_key, tenant_key=tenant_key)
        entries, reset_at = self._bed_history(
            location,
            from_year=today_year - max(pause, 1),
            tenant_key=tenant_key,
            skip_plant_key=replaced[0].plant_key if replaced is not None else None,
            skip_whole=replaced[1] if replaced is not None else False,
        )
        findings = self._rotation_findings(species.family_key, family_name, pause, source, entries, today_year)
        if replaced is not None and self._family_of(replaced[0].species_key, {}, tenant_key) == species.family_key:
            residual = _replant_finding(
                replaced[0],
                species.family_key,
                family_name,
                bed_hazards=frozenset(located.entry.hazard.value for located in bed_hazards),
                substrate_replaced_on=_substrate_replaced_on(location),
            )
            if residual is not None:
                findings = [residual, *findings]
        return self._bed_result(location_key, species_key, None, [*hazards, *findings], rotation_window_years, reset_at)

    @staticmethod
    def _bed_result(
        location_key: str,
        species_key: str,
        reason: str | None,
        findings: list[RotationFinding],
        rotation_window_years: int,
        reset_at: date | None,
    ) -> BedRotationResult:
        """The answer: strongest finding first (a stable sort keeps soil hazards ahead within a strength)."""
        ordered = sorted(findings, key=lambda f: SEVERITY_ORDER[f.severity])
        severity = ordered[0].severity if ordered else "OK"
        return BedRotationResult(
            location_key, species_key, reason is None, reason, severity, ordered, rotation_window_years, reset_at
        )

    def _soil_hazard_findings(
        self, location: Location, located: list[LocatedSoilHazard], species: Species, family_name: str | None
    ) -> list[RotationFinding]:
        """One finding per soil hazard of the bed whose host the species is (REQ-053 §11.3a Nr. 6, GP-FR-193).

        ``located`` are the hazards the bed's soil carries (``bed_soil_hazard_engine.effective_soil_hazards``), each
        with the location above the bed that holds it, if inherited - one per hazard key.
        """
        entries: list[BedSoilHazard] = [item.entry for item in located]
        origins = {item.entry.hazard: item.origin for item in located}
        if not entries or self._soil_hazards is None:
            return []
        planted = PlantedSpecies(species.scientific_name, species.genus, family_name)
        verdicts = judge_soil_hazards(
            entries,
            self._soil_hazards.get_table(),
            planted,
            today=today_utc(),
            substrate_replaced_on=_substrate_replaced_on(location),
        )
        return [soil_hazard_finding(verdict, species.key or "", origins.get(verdict.hazard)) for verdict in verdicts]

    def _rotation_findings(
        self,
        family_key: str,
        family_name: str | None,
        pause: int,
        source: PauseSource,
        entries: list[HistoryEntry],
        today_year: int,
    ) -> list[RotationFinding]:
        if pause == 0:  # "no pause needed" (rotation_pause_years = 0): nothing to check, nothing to verify
            return []
        occupied = [e for e in entries if e.family_key is not None and e.plan_role != PlanRole.FALLOW.value]
        same = [e for e in occupied if e.family_key == family_key]
        pause_finding = _pause_finding(family_key, family_name, pause, source, same, today_year)
        recent = {e.family_key for e in occupied if today_year - e.year < pause and e.family_key != family_key}
        pest_findings = (
            [
                f
                for f in (
                    _pest_finding(family_key, family_name, risk, recent, self._name_of_family)
                    for risk in self._graph_repo.get_pest_risks(family_key)
                )
                if f
            ]
            if self._graph_repo is not None
            else []
        )
        findings = ([pause_finding] if pause_finding else []) + pest_findings
        if not occupied and not findings:
            return [
                RotationFinding(
                    "INFO",
                    "rotation.no_history",
                    f"No planting is recorded for this bed in the last {pause} year(s) — the rotation cannot be "
                    "verified. Record earlier years with the history backfill.",
                    family_key=family_key,
                    family_name=family_name,
                    pause_years=pause,
                    pause_source=source,
                )
            ]
        return findings

    def _name_of_family(self, key: str) -> str | None:
        """The catalogue name of a family key, ``None`` when it is not in the catalogue."""
        family = self._family_source().get_by_key(key)
        return _name_or_none(family.name if family is not None else None)

    @staticmethod
    def _timeline_row(entry: HistoryEntry, fam: BotanicalFamily | None, species: Species | None) -> TimelineEntry:
        """One row: demand from the species, else the family; none for a green manure or a fallow year."""
        demand: str | None = None
        if entry.plan_role == PlanRole.MAIN_CROP.value and entry.family_key is not None:
            if species is not None and species.nutrient_demand is not None:
                demand = species.nutrient_demand.value
            elif fam is not None:
                demand = fam.typical_nutrient_demand.value
        return TimelineEntry(
            entry.year,
            entry.season,
            entry.family_key,
            fam.name if fam is not None else None,
            entry.species_key,
            demand,
            entry.plan_role,
            entry.source,
            entry.event_key,
        )

    def timeline_resolver(self, tenant_key: str) -> TimelineResolver:
        """The cached family and species lookups one timeline read (or one matrix page) shares."""
        return TimelineResolver(self._family_source(), self._species_repo, tenant_key)

    def bed_rotation_entries(self, location: Location, *, tenant_key: str) -> tuple[list[HistoryEntry], date | None]:
        """Every family-year of the bed within the longest look-back a timeline offers (GP-FR-103).

        The one history read behind ``GET /locations/{key}/rotation`` and the site rotation matrix: both call it,
        then :meth:`timeline_years` and :meth:`timeline_rows`, so a matrix cell is the timeline row by construction.
        """
        return self._bed_history(
            location, from_year=today_utc().year - MAX_ROTATION_TIMELINE_YEARS + 1, tenant_key=tenant_key
        )

    def with_planned_entries(
        self, location: Location, entries: list[HistoryEntry], *, to_year: int, tenant_key: str
    ) -> list[HistoryEntry]:
        """``entries`` plus the runs still planned at the bed, up to ``to_year`` (GP-FR-135, §32.5 item A).

        Only the site rotation matrix calls it: the bed timeline, the planting check, the succession recommendation
        and the nutrient hint read what stood, never a plan. A planned run counts for every year of its window from
        today on - a window with an open end for its start year only - so a run whose window ended before today, a
        cancelled, an active or a finished run is not there (an active run's plants are). A plan carries no season and
        reads as the main season: a year in which a plant stood or a main-season backfill is recorded keeps only what
        stood (the actual planting wins over the plan). A run of another tenant is not read; a species the tenant may
        not see names no family, as for a plant.
        """
        history: IRotationHistoryRepository = self._bed_collaborators()[2]
        today: date = today_utc()
        # the main season: a plant carries none and reads as the main season (SEASON_ORDER)
        occupied = {e.year for e in entries if e.season in (None, "main")}
        family_cache: dict[str, str | None] = {}
        found: dict[tuple[Any, ...], HistoryEntry] = {}
        for run in history.list_planned_runs(location.key or "", tenant_key=tenant_key):
            if run.planned_from is None:
                continue
            end = run.planned_until or run.planned_from
            if end < today:
                continue
            for year in range(max(run.planned_from, today).year, min(end.year, to_year) + 1):
                if year in occupied:
                    continue
                for species_key in run.species_keys:
                    family = self._family_of(species_key, family_cache, tenant_key)
                    found[(year, family, species_key, run.plan_role)] = HistoryEntry(
                        year, family, species_key, run.plan_role, None, "planned"
                    )
        return sorted([*entries, *found.values()], key=_history_order)

    @staticmethod
    def check_timeline_years(years: int | None) -> None:
        """422 ``rotation.years_out_of_range`` for a ``years`` outside ``1..MAX_ROTATION_TIMELINE_YEARS``."""
        if years is not None and not 1 <= years <= MAX_ROTATION_TIMELINE_YEARS:
            raise PlanError(
                "rotation.years_out_of_range",
                f"years must lie within 1..{MAX_ROTATION_TIMELINE_YEARS}.",
                status_code=422,
                field="years",
                limit=MAX_ROTATION_TIMELINE_YEARS,
            )

    @staticmethod
    def timeline_years(entries: list[HistoryEntry], years: int | None, resolver: TimelineResolver) -> int:
        """``years`` as asked, else ``max(longest pause a species or family of ``entries`` names, 5)``, at most 10.

        An unsourced family adds nothing: the look-back must reach as far as the validator does.
        """
        if years is not None:
            return years
        pauses = [
            named
            for e in entries
            for named in (_pause_of(resolver.species(e.species_key)), _pause_of(resolver.family(e.family_key)))
            if named is not None
        ]
        return min(max([*pauses, MIN_ROTATION_TIMELINE_YEARS]), MAX_ROTATION_TIMELINE_YEARS)

    def timeline_rows(
        self, entries: list[HistoryEntry], *, from_year: int, resolver: TimelineResolver
    ) -> list[TimelineEntry]:
        """The rows of the years ``from_year`` and later - the single expression every rotation view reads."""
        return [
            self._timeline_row(entry, resolver.family(entry.family_key), resolver.species(entry.species_key))
            for entry in entries
            if entry.year >= from_year
        ]

    def rotation_timeline(self, location_key: str, *, tenant_key: str, years: int | None = None) -> RotationTimeline:
        """Family, nutrient demand and plan role per year for a bed (GP-API-039, GP-FR-103, GP-ACC-028).

        ``years`` defaults to ``max(rotation_pause_years of the families involved, 5)`` and is at most 10.
        """
        sites: ISiteRepository = self._bed_collaborators()[0]
        location = resolve_owned_location(sites, location_key, tenant_key)
        self.check_timeline_years(years)
        today_year = today_utc().year
        entries, reset_at = self.bed_rotation_entries(location, tenant_key=tenant_key)
        resolver = self.timeline_resolver(tenant_key)
        years = self.timeline_years(entries, years, resolver)
        from_year = today_year - years + 1
        rows = self.timeline_rows(entries, from_year=from_year, resolver=resolver)
        reason = not_applicable_reason(location)
        return RotationTimeline(location_key, years, from_year, today_year, reason is None, reason, reset_at, rows)
