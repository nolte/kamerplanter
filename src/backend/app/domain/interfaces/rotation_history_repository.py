"""What stood in a bed, as the crop-rotation validator reads it (REQ-053 GP-FR-131, GP-FR-103).

Two sources, one port: the plants that were placed in the bed's slots (``plant_instances``) and the years a
grower filled in afterwards (``care_events`` with ``category = planting``, ``trigger = backfill``). Both reads take
the tenant keyword-only without a default and filter on it; the bed itself is resolved by the caller through the
ownership anchor (a bed has no ``tenant_key`` of its own, #2107).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime

from app.domain.models.care_event import RotationEntry


@dataclass(frozen=True)
class PlantedRow:
    """One plant that stood, or stands, in the bed. ``plan_role`` is the role of the run it belongs to."""

    plant_key: str
    species_key: str
    planted_on: date
    removed_on: date | None
    plan_role: str = "main_crop"


@dataclass(frozen=True)
class BackfillRow:
    """One year a grower recorded after the fact (GP-API-042); never a cancelled or superseded entry."""

    event_key: str
    performed_at: datetime
    entry: RotationEntry
    created_by: str | None = None


class IRotationHistoryRepository(ABC):
    @abstractmethod
    def list_plantings(self, location_key: str, *, since: date, tenant_key: str) -> list[PlantedRow]:
        """Plants of ``tenant_key`` in a slot of the bed (archived slots included) that stood on or after ``since``."""

    @abstractmethod
    def list_backfills(self, location_key: str, *, since: datetime, tenant_key: str) -> list[BackfillRow]:
        """Live backfill events of the bed performed on or after ``since``, newest first."""
