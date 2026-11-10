"""The light-schedule hints of a tent or shelf level (REQ-053 §9.2a, W-016.6, V-23): what the location summary shows.

The rules that produce them are the pure :mod:`app.domain.engines.tent_rules_engine`; this module only holds the
input and result types, so the summary's read model (:class:`~app.domain.models.garden_plan.BedSummaryView`) and the
repository port can carry them without the model layer importing an engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TentHintCode = Literal["tent.photoperiod_conflict", "tent.photoperiod_unknown"]
TentHintSeverity = Literal["info", "warning"]

#: Different photoperiods among the plants of one light schedule.
HINT_PHOTOPERIOD_CONFLICT: TentHintCode = "tent.photoperiod_conflict"
#: Plants of one light schedule whose phase names no photoperiod - the check could not judge them (E-10).
HINT_PHOTOPERIOD_UNKNOWN: TentHintCode = "tent.photoperiod_unknown"


#: Unknown plants a ``tent.photoperiod_unknown`` hint names; the rest is only counted (``unknown_plant_count``).
MAX_NAMED_UNKNOWN_PLANTS = 5


@dataclass(frozen=True)
class PlantPhotoperiod:
    """A standing plant of the location with the photoperiod its current phase asks for (``None`` = unknown)."""

    plant_key: str
    #: Display name of the current phase; ``None`` when the plant has none or it does not resolve.
    phase_name: str | None
    photoperiod_hours: float | None
    #: Machine name of the current phase (``seedling``, ``flowering``, ...); decides whether the plant is young.
    phase_code: str | None = None
    #: What the grower calls the plant (its name, else its id); shown when its photoperiod is unknown.
    display_name: str = ""


@dataclass(frozen=True)
class PhotoperiodGroup:
    """The plants that ask for one photoperiod, with the names of the phases they are in."""

    photoperiod_hours: float
    plant_count: int
    phase_names: tuple[str, ...]


@dataclass(frozen=True)
class TentHint:
    code: TentHintCode
    severity: TentHintSeverity
    #: The photoperiods the plants with a known one ask for, longest first.
    groups: tuple[PhotoperiodGroup, ...]
    #: Plants whose phase names no photoperiod.
    unknown_plant_count: int
    #: The first :data:`MAX_NAMED_UNKNOWN_PLANTS` of them by name, so the hint can say which plants it could not judge.
    unknown_plant_names: tuple[str, ...] = ()
