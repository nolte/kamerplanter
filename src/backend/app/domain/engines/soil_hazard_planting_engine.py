"""Judges a planting against the soil hazards of its bed (REQ-053 §11.3a Nr. 6-7, GP-FR-193, #2888 F-21).

Pure logic, no data access: the bed's stored entries, the knowledge table (REQ-054 §5.2a), the facts of the species
to plant and today's date (UTC) come in, one verdict per hazard whose host the species is goes out. Never a blocker
and never ``CRITICAL`` (D-09): the planting dialog shows the verdicts, the grower decides.

The stage of a hazard follows from its confirmation and the **usable** (3/3-evidenced) durations only, read through
:class:`~app.domain.engines.soil_hazard_knowledge_engine.SoilHazardKnowledgeEngine`:

* an evidenced cultivation pause that has not elapsed - a ``WARNING`` that names its end;
* no evidenced pause - a ``WARNING`` without a time statement, until the evidenced maximum survival if there is one,
  otherwise without an end (operator decision P5: until the lead removes the hazard from the bed);
* after the evidenced pause - an ``INFO`` until the evidenced maximum survival, otherwise without an end;
* after the evidenced maximum survival - nothing, also where it is a lower bound (operator decision P3).

A soft hazard (``root_knot_nematode``, ``sclerotinia``) and a host whose own evidence is below 3/3 (operator decision
P4) never warn: every stage of theirs is an ``INFO``. A substrate renewed after the confirmation lifts the hazard
(§11.3a Nr. 7). Whether the location may carry soil hazards at all (vessels, hydroponics) is the caller's question.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.common.enums import EvidenceStatus, HostLevel, SoilHazard
from app.domain.engines.soil_hazard_knowledge_engine import ResolvedSoilHazardDurations, SoilHazardKnowledgeEngine
from app.domain.models.bed_soil_hazard import BedSoilHazard
from app.domain.models.soil_hazard_knowledge import HostEntry, SoilHazardKnowledge, SoilHazardKnowledgeTable

#: Inside an evidenced cultivation pause: a warning with its end (REQ-053 §11.3a Nr. 6).
SOIL_HAZARD_PAUSE = "soil_hazard.pause"
#: No evidenced pause: a warning without a time statement.
SOIL_HAZARD_NO_EVIDENCED_PAUSE = "soil_hazard.no_evidenced_pause"
#: After the evidenced pause: the residual risk, a hint.
SOIL_HAZARD_RESIDUAL = "soil_hazard.residual"
#: A soft hazard (host range too broad to warn): a hint in every stage.
SOIL_HAZARD_SOFT = "soil_hazard.soft"
#: A host whose evidence is below 3/3 (operator decision P4): a hint in every stage.
SOIL_HAZARD_UNCERTAIN_HOST = "soil_hazard.uncertain_host"

HazardStage = Literal["pause", "no_evidenced_pause", "residual"]
HazardSeverity = Literal["INFO", "WARNING"]

#: The finest host level first: a species name before its genus before its family (REQ-054 §5.2a).
_LEVEL_ORDER: tuple[HostLevel, ...] = (HostLevel.SPECIES, HostLevel.GENUS, HostLevel.FAMILY)


@dataclass(frozen=True)
class PlantedSpecies:
    """What the host check reads of the species to plant; an empty value names no level."""

    scientific_name: str
    genus: str
    family_name: str | None


@dataclass(frozen=True)
class HostMatch:
    """The host entry of the knowledge table the species matched, at its finest level."""

    level: HostLevel
    name: str
    evidenced: bool


@dataclass(frozen=True)
class SoilHazardVerdict:
    """What one soil hazard of the bed says about planting the species today."""

    hazard: SoilHazard
    confirmed_at: date
    stage: HazardStage
    severity: HazardSeverity
    code: str
    #: The end of the pause (``pause``) or of the evidenced residual risk (``residual``); ``None`` = no time statement.
    until: date | None
    host: HostMatch


def add_years(day: date, years: int) -> date:
    """``day`` moved by ``years`` calendar years; 29 February becomes 28 February in a common year."""
    try:
        return day.replace(year=day.year + years)
    except ValueError:
        return day.replace(year=day.year + years, day=28)


def _normalised(text: str | None) -> str:
    return " ".join(text.split()).casefold() if text else ""


def _matches(entry: HostEntry, species: PlantedSpecies) -> bool:
    """Whether the species falls under ``entry``; a species name also covers its infraspecific taxa."""
    name = _normalised(entry.name)
    if entry.level is HostLevel.SPECIES:
        own = _normalised(species.scientific_name)
        return own != "" and (own == name or own.startswith(f"{name} "))
    if entry.level is HostLevel.GENUS:
        return _normalised(species.genus) == name
    return _normalised(species.family_name) == name


def match_host(row: SoilHazardKnowledge, species: PlantedSpecies) -> HostMatch | None:
    """The host entry ``species`` falls under, or ``None`` when it is no host of ``row``'s hazard.

    The finest level decides: at each level from species to family a non-host ends the search with ``None`` (it
    lifts a host on a coarser level), a host ends it with the match. A species without a genus or a name falls back to
    its family; one without a family is no host of a family entry.
    """
    for level in _LEVEL_ORDER:
        if any(entry.level is level and _matches(entry, species) for entry in row.non_hosts):
            return None
        host = next((entry for entry in row.hosts if entry.level is level and _matches(entry, species)), None)
        if host is not None:
            return HostMatch(host.level, host.name, host.evidence.status is EvidenceStatus.EVIDENCED)
    return None


def hazard_stage(
    durations: ResolvedSoilHazardDurations, confirmed_at: date, today: date
) -> tuple[HazardStage, date | None] | None:
    """The stage of a hazard confirmed on ``confirmed_at`` and its end, or ``None`` once it says nothing any more.

    Reads only the usable durations (``None`` = not 3/3-evidenced). The end of a ``no_evidenced_pause`` warning is
    never returned: without an evidenced pause the warning carries no time statement (§11.3a Nr. 6).
    """
    pause = durations.soil_persistence_years
    survival_end = (
        add_years(confirmed_at, durations.max_survival_years) if durations.max_survival_years is not None else None
    )
    if pause is not None:
        pause_end = add_years(confirmed_at, pause)
        if today < pause_end:
            return "pause", pause_end
        if survival_end is None:
            return "residual", None
        return ("residual", survival_end) if today < survival_end else None
    if survival_end is None or today < survival_end:
        return "no_evidenced_pause", None
    return None


def _verdict(
    entry: BedSoilHazard, row: SoilHazardKnowledge, host: HostMatch, stage: HazardStage, until: date | None
) -> SoilHazardVerdict:
    severity: HazardSeverity
    if row.soft:
        code, severity = SOIL_HAZARD_SOFT, "INFO"
    elif not host.evidenced:
        code, severity = SOIL_HAZARD_UNCERTAIN_HOST, "INFO"
    elif stage == "pause":
        code, severity = SOIL_HAZARD_PAUSE, "WARNING"
    elif stage == "no_evidenced_pause":
        code, severity = SOIL_HAZARD_NO_EVIDENCED_PAUSE, "WARNING"
    else:
        code, severity = SOIL_HAZARD_RESIDUAL, "INFO"
    return SoilHazardVerdict(entry.hazard, entry.confirmed_at, stage, severity, code, until, host)


def judge_soil_hazards(
    entries: Sequence[BedSoilHazard],
    table: SoilHazardKnowledgeTable,
    species: PlantedSpecies,
    *,
    today: date,
    substrate_replaced_on: date | None = None,
    knowledge: SoilHazardKnowledgeEngine | None = None,
) -> list[SoilHazardVerdict]:
    """One verdict per soil hazard of the bed whose host ``species`` is, warnings first, then by hazard key.

    An entry whose substrate was renewed after its confirmation (``substrate_replaced_on > confirmed_at``) says
    nothing: the pathogen left with the old soil (§11.3a Nr. 7, research R-004.3 a/b).
    """
    engine = knowledge or SoilHazardKnowledgeEngine()
    rows = {row.hazard: row for row in table.hazards}
    verdicts: list[SoilHazardVerdict] = []
    for entry in entries:
        if substrate_replaced_on is not None and substrate_replaced_on > entry.confirmed_at:
            continue
        row = rows[entry.hazard]
        host = match_host(row, species)
        if host is None:
            continue
        stage = hazard_stage(engine.resolve_durations(row), entry.confirmed_at, today)
        if stage is None:
            continue
        verdicts.append(_verdict(entry, row, host, *stage))
    return sorted(verdicts, key=lambda v: (v.severity != "WARNING", v.hazard.value))
