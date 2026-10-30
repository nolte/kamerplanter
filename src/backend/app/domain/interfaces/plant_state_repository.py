"""What the plant-states read needs from storage (REQ-053 GP-API-054, WP 3.7).

Two reads of the same shape: the standing plants of one bed (the API) or of several beds at once (the plan's
SVG/PDF, one window for the whole site instead of one per bed), with everything the marker and the info bubble
show, gathered in a fixed number of queries (never one per plant). The tenant is keyword-only without a default
and every stage filters on it; the beds themselves are resolved by the service through the ownership anchor first
(a bed has no ``tenant_key`` of its own, #2107).

**No free text leaves the repository** (SR-006/SR-020): no task instruction, no note, no user name. A task
contributes its name, category and due day; a finding its label.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.calculators.plant_state_calculator import OpenTask


@dataclass(frozen=True)
class NextTask:
    """The next due open task of a plant: name, category and day; ``due`` is ``None`` for an undated task."""

    name: str
    category: str
    due: date | None = None


@dataclass(frozen=True)
class PlantStateSource:
    """The raw facts about one standing plant. The calculator turns them into the visual state."""

    plant_key: str
    instance_id: str
    species_key: str
    planted_on: date
    slot_key: str | None = None
    slot_id: str | None = None
    cultivar_key: str | None = None
    species_name: str | None = None
    scientific_name: str | None = None
    cultivar_name: str | None = None
    phase_key: str | None = None
    phase_name: str | None = None
    phase_started_on: date | None = None
    phase_typical_days: int | None = None
    phase_allows_harvest: bool = False
    phase_is_terminal: bool = False
    open_tasks: tuple[OpenTask, ...] = field(default_factory=tuple)
    next_task: NextTask | None = None
    last_watering_at: datetime | None = None
    last_feeding_at: datetime | None = None
    open_finding_count: int = 0
    finding_label: str | None = None
    harvest_batch_count: int = 0
    harvested_total_g: float | None = None
    cover_photo_ref: str | None = None


class IPlantStateRepository(ABC):
    @abstractmethod
    def list_bed_plants(
        self, location_key: str, *, tenant_key: str, now: datetime, offset: int, limit: int
    ) -> list[PlantStateSource]:
        """A window of the tenant's standing plants in the bed, ordered by plant key, with all facts joined in."""

    @abstractmethod
    def list_plants_in_beds(
        self, bed_keys: list[str], *, tenant_key: str, now: datetime, offset: int, limit: int
    ) -> list[PlantStateSource]:
        """A window of the tenant's standing plants in any of the beds, ordered by plant key, with the same facts as
        :meth:`list_bed_plants` — one window for many beds, so a site costs a fixed number of statements per page."""
