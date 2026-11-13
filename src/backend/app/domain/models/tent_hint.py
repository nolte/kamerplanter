"""The light-schedule hints of a tent or shelf level (REQ-053 §9.2a, W-016.6, V-23): what the location summary shows.

The rules that produce them are the pure :mod:`app.domain.engines.tent_rules_engine`; this module only holds the
input and result types, so the summary's read model (:class:`~app.domain.models.garden_plan.BedSummaryView`) and the
repository port can carry them without the model layer importing an engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.common.enums import PhotoperiodSource

TentHintCode = Literal["tent.photoperiod_conflict", "tent.photoperiod_unknown"]
TentHintSeverity = Literal["info", "warning"]

#: Different photoperiods among the plants of one light schedule.
HINT_PHOTOPERIOD_CONFLICT: TentHintCode = "tent.photoperiod_conflict"
#: Plants of one light schedule whose phase names no sourced photoperiod - the check could not judge them (E-10,
#: #2857): no profile, or hours nobody chose for the species (``generated``, ``default``, origin unknown).
HINT_PHOTOPERIOD_UNKNOWN: TentHintCode = "tent.photoperiod_unknown"


#: Unknown plants a ``tent.photoperiod_unknown`` hint names; the rest is only counted (``unknown_plant_count``).
MAX_NAMED_UNKNOWN_PLANTS = 5


@dataclass(frozen=True)
class PhaseLabel:
    """A phase as the hint names it: its machine name and both catalogue display names (#2889).

    The server words nothing here: the client picks the name for its UI language (German, else its own phase
    translation of ``code``, else English, else ``code``). An empty display name means the catalogue holds none.
    """

    code: str
    display_name: str = ""
    display_name_de: str = ""


@dataclass(frozen=True)
class PlantPhotoperiod:
    """A standing plant of the location with the photoperiod its current phase asks for (``None`` = no profile).

    The tent rule judges the hours only with ``photoperiod_source == sourced`` (#2857,
    :func:`~app.domain.engines.tent_rules_engine.judged_photoperiod`): any other origin - ``generated``, ``default``,
    or ``None`` for a profile that predates the provenance or no profile at all - is no statement about the plant.
    """

    plant_key: str
    #: Display name of the current phase; ``None`` when the plant has none or it does not resolve.
    phase_name: str | None
    photoperiod_hours: float | None
    #: Machine name of the current phase (``seedling``, ``flowering``, ...); decides whether the plant is young.
    phase_code: str | None = None
    #: What the grower calls the plant (its name, else its id); shown when its photoperiod is unknown.
    display_name: str = ""
    #: The current phase with both display names; ``None`` when the plant has no phase that resolves.
    phase_label: PhaseLabel | None = None
    #: Where the profile's hours came from; ``None`` without a profile or for one stored before the provenance.
    photoperiod_source: PhotoperiodSource | None = None


@dataclass(frozen=True)
class PhotoperiodGroup:
    """The plants that ask for one photoperiod, with the names of the phases they are in."""

    photoperiod_hours: float
    plant_count: int
    #: Display names as the server falls back (English, else the machine name) - kept for older clients.
    phase_names: tuple[str, ...]
    #: The phases of these plants, one per machine name, sorted by it - what a client words in its language.
    phases: tuple[PhaseLabel, ...] = ()


@dataclass(frozen=True)
class TentHint:
    code: TentHintCode
    severity: TentHintSeverity
    #: The photoperiods the plants with a known one ask for, longest first.
    groups: tuple[PhotoperiodGroup, ...]
    #: Plants whose phase names no sourced photoperiod.
    unknown_plant_count: int
    #: The first :data:`MAX_NAMED_UNKNOWN_PLANTS` of them by name, so the hint can say which plants it could not judge.
    unknown_plant_names: tuple[str, ...] = ()
