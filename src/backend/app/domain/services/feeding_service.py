from app.common.tenant_guard import verify_tenant_ownership
from app.common.types import FeedingEventKey
from app.domain.engines.nutrient_engine import RunoffAnalyzer
from app.domain.interfaces.feeding_repository import IFeedingRepository
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.models.feeding_event import FeedingEvent
from app.domain.services.feeding_references import FillEventAnchors, require_owned_fill_event
from app.domain.services.fertilizer_references import assert_fertilizers_visible


class FeedingService:
    def __init__(
        self,
        repo: IFeedingRepository,
        fertilizer_repo: IFertilizerRepository | None = None,
        *,
        fill_event_anchors: FillEventAnchors | None = None,
    ) -> None:
        self._repo = repo
        self._fertilizer_repo = fertilizer_repo
        # #1872 C6: a fill event's tenant is its tank's; ``ITankRepository`` answers both.
        self._fill_event_anchors = fill_event_anchors
        self._runoff_analyzer = RunoffAnalyzer()

    # ── CRUD ─────────────────────────────────────────────────────────

    def list_events(
        self,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str = "",
    ) -> tuple[list[FeedingEvent], int]:
        return self._repo.get_all(offset, limit, tenant_key=tenant_key)

    def get_event(self, key: FeedingEventKey, tenant_key: str = "") -> FeedingEvent:
        event = self._repo.get_or_raise(key)
        if tenant_key:
            verify_tenant_ownership(event, tenant_key, "FeedingEvent")
        return event

    def create_event(self, event: FeedingEvent) -> FeedingEvent:
        """Persist a feeding event whose fertilizer lines the event's tenant can see (#1713).

        The repository also writes a ``feeding_used`` edge per line, so an
        unchecked key would put an edge into another tenant's product.
        """
        assert_fertilizers_visible(
            self._fertilizer_repo,
            (f.fertilizer_key for f in event.fertilizers_used),
            tenant_key=event.tenant_key,
            field="fertilizers_used",
            owner="FeedingService",
        )
        # The fill event under the event's tenant (#1872 C6): REST and the MCP
        # feeding tool both land here, and both stored the key verbatim.
        if event.tank_fill_event_key:
            require_owned_fill_event(self._fill_event_anchors, event.tank_fill_event_key, event.tenant_key)
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

    def get_by_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[FeedingEvent]:
        """A plant's feeding history, scoped to ``tenant_key`` (#927).

        ``plant_key`` is never resolved against the caller's tenant here; the
        repository's tenant predicate is what turns a foreign key into an empty
        list instead of another tenant's fertigation record.
        """
        return self._repo.get_by_plant(plant_key, offset, limit, tenant_key=tenant_key)

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
