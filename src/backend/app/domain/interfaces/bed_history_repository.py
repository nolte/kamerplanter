"""The combined history of a bed: care events and the planting events derived from plants and runs.

REQ-053 GP-FR-102, GP-API-038 (WP 4.5, #2423). One read, one port: the care log is stored (``care_events``), the
planting events are **derived** (``plant_instances``, ``planting_runs``) and never stored a second time, so the two
sources merge by time in the database and one page is cut from the merged order.

The read takes the tenant keyword-only without a default. ``locations`` and ``slots`` carry no ``tenant_key``
(#2107): the caller resolves the bed through the ownership anchor first, and the plants, runs and events are
filtered on ``tenant_key`` here as well.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.domain.interfaces.care_event_repository import CareEventRow

PlantingEventKind = Literal["plant_planted", "plant_removed", "run_started", "run_completed"]


@dataclass(frozen=True)
class BedHistoryFilter:
    """The filters of ``GET /locations/{key}/history`` (GP-API-038, GP-FR-102)."""

    category: str | None = None
    plant_key: str | None = None
    performed_from: datetime | None = None
    performed_to: datetime | None = None
    #: An account key; a planting event has no performer, so the filter leaves the derived events out.
    performed_by: str | None = None
    #: ``False`` hides the superseded entries and the ``position_corrected`` entries (corrections).
    include_corrections: bool = False


@dataclass(frozen=True)
class PlantingEvent:
    """A planting event derived from a plant or a run; the plant or the run it names is the tenant's."""

    kind: PlantingEventKind
    at: datetime
    #: ``planting`` for planted / started, ``removal`` for removed / completed (the care-log categories).
    category: Literal["planting", "removal"]
    plant_key: str | None = None
    species_key: str | None = None
    #: The name the grower gave the plant, else its instance id.
    plant_name: str | None = None
    termination_type: str | None = None
    run_key: str | None = None
    run_name: str | None = None
    run_status: str | None = None


@dataclass(frozen=True)
class BedHistoryRow:
    """One line of the merged history: exactly one of ``care`` and ``planting`` is set."""

    at: datetime
    care: CareEventRow | None = None
    planting: PlantingEvent | None = None


class IBedHistoryRepository(ABC):
    @abstractmethod
    def list_history(
        self, location_key: str, criteria: BedHistoryFilter, *, tenant_key: str, offset: int, limit: int
    ) -> list[BedHistoryRow]:
        """One page of the bed's merged history, newest first (ties broken by id, so a page boundary is stable)."""
