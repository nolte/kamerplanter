"""REQ-045 — server-authoritative dashboard widget catalog.

Holds the backend-side widget metadata (category, experience-level default,
sizing, gating module) and resolves per-user *availability* from the gates
that only the server knows about:

- REQ-042 module visibility (a widget whose ``required_module`` the user hid
  is unavailable),
- REQ-027 Light-Mode (``community_activity`` is filtered; ``daily_tip`` needs
  a whitelisted AI provider),
- REQ-024 permissions (dashboard widgets are read-only; every tenant member
  may read them, so no extra role gate is applied here today).

The widget-key set MUST stay in sync with the frontend
``dashboardWidgetCatalog`` and with ``KNOWN_WIDGET_KEYS`` in
``user_preference_service`` (contract test, REQ-045 §6).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.common.enums import ExperienceLevel, ModuleVisibilityState

# i18n keys the frontend resolves for the greyed-out "why not available" hint.
REASON_MODULE_HIDDEN = "dashboard.gate.moduleHidden"
REASON_LIGHT_MODE = "dashboard.gate.lightMode"
REASON_AI_DISABLED = "dashboard.gate.aiDisabled"


@dataclass(frozen=True)
class WidgetMeta:
    """Static, mode-independent metadata for one dashboard widget."""

    widget_key: str
    category: str
    default_level: ExperienceLevel
    default_size: dict[str, int]
    min_size: dict[str, int]
    max_size: dict[str, int]
    required_module: str | None = None
    light_gated: bool = False  # REQ-027: not selectable in Light mode at all
    requires_ai: bool = False  # REQ-031: needs a whitelisted AI provider


def _sz(w: int, h: int) -> dict[str, int]:
    return {"w": w, "h": h}


# Order matters only for a stable catalog response; grouping is by ``category``.
WIDGET_CATALOG: tuple[WidgetMeta, ...] = (
    WidgetMeta("quick_actions", "essentials", ExperienceLevel.BEGINNER, _sz(12, 2), _sz(4, 2), _sz(12, 4)),
    WidgetMeta("tasks_today", "essentials", ExperienceLevel.BEGINNER, _sz(4, 4), _sz(2, 3), _sz(8, 8), "tasks"),
    WidgetMeta("care_reminders", "essentials", ExperienceLevel.BEGINNER, _sz(4, 4), _sz(2, 3), _sz(8, 8), "care"),
    WidgetMeta(
        "active_plants_summary", "essentials", ExperienceLevel.BEGINNER, _sz(4, 3), _sz(2, 2), _sz(8, 6), "plants"
    ),
    WidgetMeta("onboarding_progress", "essentials", ExperienceLevel.BEGINNER, _sz(4, 3), _sz(2, 2), _sz(12, 4)),
    WidgetMeta(
        "daily_tip", "insights", ExperienceLevel.BEGINNER, _sz(4, 4), _sz(2, 3), _sz(8, 8), "ai", requires_ai=True
    ),
    WidgetMeta("weather_forecast", "insights", ExperienceLevel.BEGINNER, _sz(4, 3), _sz(2, 2), _sz(8, 6)),
    WidgetMeta("winter_protection", "cultivation", ExperienceLevel.BEGINNER, _sz(6, 4), _sz(3, 3), _sz(12, 8), "care"),
    WidgetMeta("ipm_alerts", "cultivation", ExperienceLevel.INTERMEDIATE, _sz(4, 4), _sz(2, 3), _sz(8, 8), "ipm"),
    WidgetMeta(
        "harvest_forecast", "insights", ExperienceLevel.INTERMEDIATE, _sz(4, 4), _sz(2, 3), _sz(8, 8), "harvest"
    ),
    WidgetMeta(
        "next_calendar_events",
        "cultivation",
        ExperienceLevel.INTERMEDIATE,
        _sz(4, 4),
        _sz(2, 3),
        _sz(8, 8),
        "calendar",
    ),
    WidgetMeta(
        "community_activity",
        "insights",
        ExperienceLevel.INTERMEDIATE,
        _sz(4, 4),
        _sz(2, 3),
        _sz(8, 8),
        light_gated=True,
    ),
    WidgetMeta("sensor_live", "monitoring", ExperienceLevel.EXPERT, _sz(4, 4), _sz(2, 3), _sz(8, 8), "sensors"),
    WidgetMeta("tank_status", "monitoring", ExperienceLevel.EXPERT, _sz(4, 4), _sz(2, 3), _sz(8, 8), "tanks"),
    WidgetMeta("phase_timeline", "cultivation", ExperienceLevel.EXPERT, _sz(8, 4), _sz(3, 3), _sz(12, 8), "plants"),
    WidgetMeta("vpd_gauge", "monitoring", ExperienceLevel.EXPERT, _sz(3, 4), _sz(2, 3), _sz(6, 8), "sensors"),
    WidgetMeta("plant_grid", "cultivation", ExperienceLevel.EXPERT, _sz(8, 5), _sz(4, 3), _sz(12, 10), "plants"),
)

WIDGET_BY_KEY: dict[str, WidgetMeta] = {w.widget_key: w for w in WIDGET_CATALOG}


@dataclass(frozen=True)
class WidgetAvailability:
    """Resolved catalog entry for one user (metadata + availability)."""

    meta: WidgetMeta
    available: bool
    unavailable_reason: str | None = field(default=None)


def resolve_widget_catalog(
    *,
    mode: str,
    module_visibility: dict[str, ModuleVisibilityState],
) -> list[WidgetAvailability]:
    """Resolve availability of every widget for the calling user.

    ``mode`` is ``settings.kamerplanter_mode`` ("light" | "full"). AI-gated
    widgets require a whitelisted provider, which today is only present in full
    mode (REQ-027 §2.1); Light mode therefore disables ``daily_tip`` and
    ``community_activity``.
    """

    is_light = mode == "light"
    resolved: list[WidgetAvailability] = []
    for meta in WIDGET_CATALOG:
        available = True
        reason: str | None = None
        if meta.required_module and module_visibility.get(meta.required_module) == ModuleVisibilityState.DISABLED:
            available, reason = False, REASON_MODULE_HIDDEN
        elif is_light and meta.light_gated:
            available, reason = False, REASON_LIGHT_MODE
        elif meta.requires_ai and is_light:
            available, reason = False, REASON_AI_DISABLED
        resolved.append(WidgetAvailability(meta=meta, available=available, unavailable_reason=reason))
    return resolved
