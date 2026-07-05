import structlog

from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.user_preference import DashboardLayout, UserPreference

logger = structlog.get_logger()

# REQ-045 — backend widget registry. MUST stay in sync with the frontend
# ``dashboardWidgetCatalog`` (contract test, REQ-045 §6).
KNOWN_WIDGET_KEYS: frozenset[str] = frozenset(
    {
        "quick_actions",
        "active_plants_summary",
        "tasks_today",
        "care_reminders",
        "daily_tip",
        "weather_forecast",
        "onboarding_progress",
        "winter_protection",
        "ipm_alerts",
        "harvest_forecast",
        "next_calendar_events",
        "community_activity",
        "sensor_live",
        "tank_status",
        "phase_timeline",
        "vpd_gauge",
        "plant_grid",
    }
)


def _sanitize_layout(layout: DashboardLayout) -> DashboardLayout:
    """Drop widgets with an unknown widget_key (warn-log), keep the rest.

    Deliberately tolerant (like module_visibility): the backend does not
    reject a whole layout just because one widget key does not (yet/anymore)
    exist — forward/backward compatibility across client versions.
    """
    keep: list = []
    dropped: list = []
    for widget in layout.widgets:
        (keep if widget.widget_key in KNOWN_WIDGET_KEYS else dropped).append(widget)
    if dropped:
        logger.warning(
            "dashboard_layout.unknown_widgets_dropped",
            widget_keys=[w.widget_key for w in dropped],
        )
    # Prune placements referencing orphaned instance_ids (per-breakpoint consistency).
    kept_ids = {w.instance_id for w in keep}
    pruned = {
        breakpoint_key: [p for p in places if p.instance_id in kept_ids]
        for breakpoint_key, places in layout.placements.items()
    }
    return layout.model_copy(update={"widgets": keep, "placements": pruned})


KNOWN_MODULE_KEYS: frozenset[str] = frozenset(
    {
        "dashboard",
        "plants",
        "locations",
        "settings",
        "onboarding",
        "care",
        "calendar",
        "watering",
        "tasks",
        "nutrition",
        "tanks",
        "substrates",
        "calculators",
        "ipm",
        "harvest",
        "post_harvest",
        "runs",
        "propagation",
        "master_data",
        "companion",
        "sensors",
        "automation",
        "smart_home",
        "ai",
    }
)


class UserPreferenceService:
    def __init__(self, db) -> None:
        from app.data_access.arango import collections as col

        # Service-embedded dict view: methods below wrap the raw dict into
        # UserPreference themselves, so opt into raw mode (FR-002 A3).
        self._repo = BaseArangoRepository(db, col.USER_PREFERENCES, raw=True)

    def get_preferences(self, user_key: str) -> UserPreference:
        docs = self._repo.find_by_field("user_key", user_key)
        if docs:
            return UserPreference(**docs[0])
        # Auto-create defaults
        pref = UserPreference(user_key=user_key)
        doc = self._repo.create(pref)
        return UserPreference(**doc)

    def update_preferences(self, user_key: str, updates: dict) -> UserPreference:
        mv = updates.get("module_visibility")
        if mv:
            unknown = set(mv) - KNOWN_MODULE_KEYS
            if unknown:
                logger.warning("unknown_module_visibility_keys", keys=sorted(unknown))
        # REQ-045 — sanitize a submitted layout (drop unknown widgets). An
        # explicit null resets to the experience-level default; "unset" (key
        # absent) leaves the stored layout untouched — the router uses
        # exclude_unset so this distinction survives.
        if "dashboard_layout" in updates and updates["dashboard_layout"] is not None:
            layout = DashboardLayout.model_validate(updates["dashboard_layout"])
            updates["dashboard_layout"] = _sanitize_layout(layout).model_dump()
        pref = self.get_preferences(user_key)
        data = pref.model_dump()
        data.update(updates)
        updated = UserPreference(**data)
        doc = self._repo.update(pref.key or "", updated)
        return UserPreference(**doc)
