from typing import TYPE_CHECKING

from app.common.exceptions import NotFoundError
from app.domain.engines.nutrient_engine import RunoffAnalyzer

if TYPE_CHECKING:
    from app.common.types import FeedingEventKey
    from app.domain.interfaces.feeding_repository import IFeedingRepository
    from app.domain.models.feeding_event import FeedingEvent


class FeedingService:
    def __init__(self, repo: IFeedingRepository) -> None:
        self._repo = repo
        self._runoff_analyzer = RunoffAnalyzer()

    # ── CRUD ─────────────────────────────────────────────────────────

    def list_events(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[FeedingEvent], int]:
        return self._repo.get_all(offset, limit)

    def get_event(self, key: FeedingEventKey) -> FeedingEvent:
        event = self._repo.get_by_key(key)
        if event is None:
            raise NotFoundError("FeedingEvent", key)
        return event

    def create_event(self, event: FeedingEvent) -> FeedingEvent:
        return self._repo.create(event)

    def update_event(self, key: FeedingEventKey, data: dict) -> FeedingEvent:
        existing = self.get_event(key)
        allowed_fields = {
            "application_method",
            "is_supplemental",
            "volume_applied_liters",
            "measured_ec_before",
            "measured_ec_after",
            "measured_ph_before",
            "measured_ph_after",
            "runoff_ec",
            "runoff_ph",
            "runoff_volume_liters",
            "notes",
        }
        for field, value in data.items():
            if field in allowed_fields:
                setattr(existing, field, value)
        return self._repo.update(key, existing)

    def delete_event(self, key: FeedingEventKey) -> bool:
        self.get_event(key)
        return self._repo.delete(key)

    # ── Queries ──────────────────────────────────────────────────────

    def get_by_plant(self, plant_key: str, offset: int = 0, limit: int = 50) -> list[FeedingEvent]:
        return self._repo.get_by_plant(plant_key, offset, limit)

    # ── Runoff analysis ──────────────────────────────────────────────

    def analyze_runoff(self, key: FeedingEventKey) -> dict:
        event = self.get_event(key)

        if (
            event.measured_ec_before is None
            or event.runoff_ec is None
            or event.measured_ph_before is None
            or event.runoff_ph is None
            or event.runoff_volume_liters is None
        ):
            return {"error": "Insufficient runoff data for analysis"}

        return self._runoff_analyzer.analyze(
            input_ec_ms=event.measured_ec_before,
            runoff_ec_ms=event.runoff_ec,
            input_ph=event.measured_ph_before,
            runoff_ph=event.runoff_ph,
            input_volume_liters=event.volume_applied_liters,
            runoff_volume_liters=event.runoff_volume_liters,
        )
