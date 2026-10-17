from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.common.types import SiteKey
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    PlanAuditEntry,
    PlanBatchOutcome,
    PlanBatchWrite,
    PlantShortInfo,
    TaskCounter,
)
from app.domain.models.site import Location, Slot


@dataclass
class PlanReadData:
    """The documents behind ``GET /sites/{key}/plan``, read in one pass (GP-NFR-002)."""

    locations: list[Location] = field(default_factory=list)
    garden_objects: list[GardenObject] = field(default_factory=list)
    slots: list[Slot] = field(default_factory=list)
    plants: list[PlantShortInfo] = field(default_factory=list)
    task_counters: dict[str, TaskCounter] = field(default_factory=dict)
    #: Display name of the account that last changed the plan structure; ``None`` when unknown or erased.
    plan_updated_by_name: str | None = None


class IGardenPlanRepository(ABC):
    """Persistence of the garden plan beyond the single documents (REQ-053 §21.1, §21.3).

    Locations and garden objects carry no ``tenant_key`` (E-01, #2107): every read here
    takes the tenant keyword-only without a default and joins the site inside the query,
    so a foreign site answers with nothing instead of with its rows (§22.3 T-04).
    """

    @abstractmethod
    def load_structure(self, site_key: SiteKey, *, tenant_key: str) -> tuple[list[Location], list[GardenObject]]:
        """Every location and garden object of a site of ``tenant_key`` (the batch's working-copy basis)."""

    @abstractmethod
    def load_read_model(
        self, site_key: SiteKey, *, tenant_key: str, include_plants: bool, include_tasks: bool
    ) -> PlanReadData:
        """The documents of the plan read model; slots of archived runs are left out."""

    @abstractmethod
    def load_active_slots(self, site_key: SiteKey, location_keys: list[str], *, tenant_key: str) -> list[Slot]:
        """Slots (``archived_at`` null) of the named locations, which must belong to the tenant's site (V-04)."""

    @abstractmethod
    def bed_type_flags(self, location_type_keys: list[str]) -> dict[str, bool]:
        """``location_type_key`` → ``is_bed`` for the keys that resolve; an unknown key is absent."""

    @abstractmethod
    def count_active_plants(self, location_keys: list[str], *, tenant_key: str) -> int:
        """Plants of ``tenant_key`` with ``removed_on = null`` standing in any of the locations (V-09)."""

    @abstractmethod
    def apply_plan_batch(self, write: PlanBatchWrite) -> PlanBatchOutcome:
        """Write the set in one transaction, after re-checking the revision inside it (GP-NFR-013).

        Raises:
            PlanRevisionConflictError: the stored ``plan_revision`` is not the one expected.
            NotFoundError: the site is gone or not the tenant's.
        """

    @abstractmethod
    def list_audit(self, site_key: SiteKey, *, tenant_key: str, offset: int, limit: int) -> list[PlanAuditEntry]:
        """The site's plan change log, newest first."""
