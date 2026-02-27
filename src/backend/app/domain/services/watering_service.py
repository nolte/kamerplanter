from app.common.exceptions import NotFoundError
from app.common.types import LocationKey, SlotKey, WateringEventKey
from app.domain.engines.watering_engine import WateringEngine
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.watering_repository import IWateringRepository
from app.domain.models.watering_event import WateringEvent


class WateringService:
    def __init__(
        self,
        repo: IWateringRepository,
        engine: WateringEngine,
        site_repo: ISiteRepository,
    ) -> None:
        self._repo = repo
        self._engine = engine
        self._site_repo = site_repo

    # ── Create ─────────────────────────────────────────────────────────

    def create_event(self, event: WateringEvent) -> dict:
        """Create a watering event and return it with any warnings."""
        # Look up irrigation system from the slot's location
        irrigation_system = None
        first_slot = self._site_repo.get_slot_by_key(event.slot_keys[0])
        if first_slot is not None:
            location = self._site_repo.get_location_by_key(first_slot.location_key)
            if location is not None:
                irrigation_system = location.irrigation_system

        warnings = self._engine.validate_and_warn(event, irrigation_system)
        created = self._repo.create(event)
        return {"event": created, "warnings": warnings}

    # ── Read ───────────────────────────────────────────────────────────

    def get_event(self, key: WateringEventKey) -> WateringEvent:
        event = self._repo.get_by_key(key)
        if event is None:
            raise NotFoundError("WateringEvent", key)
        return event

    def list_events(
        self, offset: int = 0, limit: int = 50,
    ) -> tuple[list[WateringEvent], int]:
        return self._repo.get_all(offset, limit)

    def get_by_slot(
        self, slot_key: SlotKey, offset: int = 0, limit: int = 50,
    ) -> list[WateringEvent]:
        return self._repo.get_by_slot(slot_key, offset, limit)

    def get_by_location(
        self, location_key: LocationKey, offset: int = 0, limit: int = 50,
    ) -> list[WateringEvent]:
        return self._repo.get_by_location(location_key, offset, limit)

    def get_stats(self, location_key: LocationKey) -> dict:
        return self._repo.get_stats_by_location(location_key)
