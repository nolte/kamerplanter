from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any, Literal, Protocol

from app.common.datetimes import today_utc
from app.common.enums import PlanRole
from app.common.exceptions import PlanError, PlanValidationError, RotationViolationError
from app.config.constants import (
    DEFAULT_ROTATION_WINDOW_YEARS,
    MAX_ROTATION_TIMELINE_YEARS,
    MAX_ROTATION_WINDOW_YEARS,
    MIN_ROTATION_TIMELINE_YEARS,
)
from app.domain.interfaces.graph_repository import IGraphRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.rotation_history_repository import IRotationHistoryRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.site import Location
from app.domain.models.species import Species
from app.domain.services.location_ownership import resolve_owned_location
from app.domain.services.species_visibility import readable_species

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
ROTATION_OFF_LOCATION_TYPES: frozenset[str] = frozenset({"planter", "tent", "shelf"})

NOT_APPLICABLE_CONTAINER = "rotation.not_applicable.container"
NOT_APPLICABLE_EXEMPT = "rotation.not_applicable.rotation_exempt"

PauseSource = Literal["species", "family", "default"]
HistorySource = Literal["plant", "backfill"]


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
    """One family-year in a bed: what stood there (a plant) or what the grower recorded afterwards (a backfill)."""

    year: int
    family_key: str | None
    species_key: str | None
    plan_role: str
    season: str | None
    source: HistorySource
    event_key: str | None = None


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
    """Why the bed-level rotation check is off for this location, or ``None`` when it applies (GP-FR-137)."""
    if location.rotation_exempt:
        return NOT_APPLICABLE_EXEMPT
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


def _family_phrase(family_name: str | None) -> str:
    """The family in an English message: its name, never its database key."""
    return f"Family '{family_name}'" if family_name else "The same family"


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
    ) -> None:
        self._plant_repo = plant_repo
        self._species_repo = species_repo
        self._graph_repo = graph_repo
        self._sites: ISiteRepository | None = site_repo
        self._families: FamilySource | None = family_repo
        self._history: IRotationHistoryRepository | None = history_repo

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
        """
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

    def _family_cached(self, key: str, cache: dict[str, BotanicalFamily | None]) -> BotanicalFamily | None:
        if key not in cache:
            cache[key] = self._family_source().get_by_key(key)
        return cache[key]

    def _family_source(self) -> FamilySource:
        return self._bed_collaborators()[1]

    def _family_of(self, species_key: str, cache: dict[str, str | None], tenant_key: str) -> str | None:
        """The family of a stored species key, resolved under the tenant (a legacy key may name a foreign species)."""
        if species_key not in cache:
            species = readable_species(self._species_repo, species_key, tenant_key)
            cache[species_key] = species.family_key if species is not None else None
        return cache[species_key]

    def _bed_history(
        self, location: Location, *, from_year: int, tenant_key: str
    ) -> tuple[list[HistoryEntry], date | None]:
        """Every family-year of the bed since ``from_year``, from ``rotation_reset_at`` on (GP-FR-131).

        Plants count for every year they stood (a plant put in last spring and still there occupies this year too);
        a green manure counts with its family; a mixed bed contributes every family of the year. A backfill counts
        for its calendar year. Duplicates (ten tomato plants in one year) collapse into one entry.
        """
        history: IRotationHistoryRepository = self._bed_collaborators()[2]
        today: date = today_utc()
        reset_at = location.soil_profile.rotation_reset_at if location.soil_profile is not None else None
        since = date(from_year, 1, 1)
        if reset_at is not None and reset_at > since:
            since = reset_at
        family_cache: dict[str, str | None] = {}
        found: dict[tuple[Any, ...], HistoryEntry] = {}
        for plant in history.list_plantings(location.key or "", since=since, tenant_key=tenant_key):
            end = min(plant.removed_on or today, today)
            first = max(plant.planted_on, since)
            family = self._family_of(plant.species_key, family_cache, tenant_key)
            for year in range(first.year, end.year + 1):
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
        ordered = sorted(entries, key=lambda e: (-e.year, e.family_key or "", e.species_key or "", e.source))
        return ordered, reset_at

    def validate_planting_in_location(
        self,
        location_key: str,
        species_key: str,
        *,
        tenant_key: str,
        rotation_window_years: int = DEFAULT_ROTATION_WINDOW_YEARS,
    ) -> BedRotationResult:
        """Crop-rotation hint for planting ``species_key`` in the bed ``location_key`` (GP-FR-131, GP-API-025).

        The history of **all** slots of the bed, from ``rotation_reset_at`` on, decides: how many years ago the
        same family stood there, against the pause of the species (override), the family, or
        ``rotation_window_years`` (at most 8). A green manure counts with its family. The answer is a list of
        findings with a severity and a reason — never an error for a violation (D-09: the grower decides).
        Off for ``planter`` / ``tent`` / ``shelf`` and ``rotation_exempt`` beds (GP-FR-137).

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

        reason = not_applicable_reason(location)
        if reason is not None:
            return BedRotationResult(
                location_key, species_key, False, reason, "OK", [], rotation_window_years, reset_at
            )
        if not species.family_key:
            finding = RotationFinding(
                "INFO", "rotation.no_family", "No family assigned — cannot evaluate rotation.", species_key=species_key
            )
            return BedRotationResult(
                location_key, species_key, True, None, "INFO", [finding], rotation_window_years, reset_at
            )

        family = families.get_by_key(species.family_key)
        pause, source = resolve_pause_years(species, family, rotation_window_years)
        today_year = today_utc().year
        entries, reset_at = self._bed_history(location, from_year=today_year - max(pause, 1), tenant_key=tenant_key)
        findings = self._rotation_findings(
            species.family_key,
            _name_or_none(family.name if family is not None else None),
            pause,
            source,
            entries,
            today_year,
        )
        findings = sorted(findings, key=lambda f: SEVERITY_ORDER[f.severity])
        severity = findings[0].severity if findings else "OK"
        return BedRotationResult(
            location_key, species_key, True, None, severity, findings, rotation_window_years, reset_at
        )

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

    def rotation_timeline(self, location_key: str, *, tenant_key: str, years: int | None = None) -> RotationTimeline:
        """Family, nutrient demand and plan role per year for a bed (GP-API-039, GP-FR-103, GP-ACC-028).

        ``years`` defaults to ``max(rotation_pause_years of the families involved, 5)`` and is at most 10.
        """
        sites: ISiteRepository = self._bed_collaborators()[0]
        location = resolve_owned_location(sites, location_key, tenant_key)
        if years is not None and not 1 <= years <= MAX_ROTATION_TIMELINE_YEARS:
            raise PlanError(
                "rotation.years_out_of_range",
                f"years must lie within 1..{MAX_ROTATION_TIMELINE_YEARS}.",
                status_code=422,
                field="years",
                limit=MAX_ROTATION_TIMELINE_YEARS,
            )
        today_year = today_utc().year
        entries, reset_at = self._bed_history(
            location, from_year=today_year - MAX_ROTATION_TIMELINE_YEARS + 1, tenant_key=tenant_key
        )
        family_cache: dict[str, BotanicalFamily | None] = {}

        def family(key: str | None) -> BotanicalFamily | None:
            return self._family_cached(key, family_cache) if key is not None else None

        species_cache: dict[str, Species | None] = {}

        def species_of(key: str | None) -> Species | None:
            if key is None:
                return None
            if key not in species_cache:
                species_cache[key] = readable_species(self._species_repo, key, tenant_key)
            return species_cache[key]

        if years is None:
            # The longest pause a family or a species override names (an unsourced family adds nothing): the
            # look-back must reach as far as the validator does.
            pauses = [
                named
                for e in entries
                for named in (_pause_of(species_of(e.species_key)), _pause_of(family(e.family_key)))
                if named is not None
            ]
            years = min(max([*pauses, MIN_ROTATION_TIMELINE_YEARS]), MAX_ROTATION_TIMELINE_YEARS)
        from_year = today_year - years + 1

        rows = [
            self._timeline_row(entry, family(entry.family_key), species_of(entry.species_key))
            for entry in entries
            if entry.year >= from_year
        ]
        return RotationTimeline(
            location_key,
            years,
            from_year,
            today_year,
            not_applicable_reason(location) is None,
            not_applicable_reason(location),
            reset_at,
            rows,
        )
