from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import ExperienceLevel, ModuleVisibilityState

CORE_MODULE_KEYS: frozenset[str] = frozenset({"dashboard", "plants", "locations", "settings", "onboarding"})

# ── REQ-045 Individualisierbares Dashboard ──────────────────────────────
DASHBOARD_LAYOUT_SCHEMA_VERSION = 2
# Grid columns per breakpoint (UI-NFR-001): Desktop / Tablet / Mobile.
GRID_COLS_BY_BREAKPOINT: dict[str, int] = {"lg": 12, "md": 8, "sm": 4}
GRID_MAX_COLUMNS = 12


class DashboardWidgetInstance(BaseModel):
    """Which widget (+ config) — breakpoint-independent (REQ-045)."""

    instance_id: str = Field(default_factory=lambda: f"w-{uuid4().hex[:12]}")
    widget_key: str
    config: dict[str, object] = Field(default_factory=dict)


class WidgetPlacement(BaseModel):
    """Position/size of a widget instance in a breakpoint grid (REQ-045).

    ``w`` is clamped client-side to the column count of the respective
    breakpoint (react-grid-layout); the model permits up to the lg maximum.
    """

    instance_id: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(ge=1, le=GRID_MAX_COLUMNS)
    h: int = Field(ge=1, le=24)


class DashboardLayout(BaseModel):
    """Personalized dashboard layout of a user (REQ-045).

    Set semantics: holds the user's complete widget list. An unknown
    ``widget_key`` (not in the backend widget registry) is dropped and
    logged on save — analogous to module_visibility (REQ-042). Positions
    live per breakpoint in ``placements``; a missing breakpoint is derived
    client-side from ``lg``.
    """

    schema_version: int = DASHBOARD_LAYOUT_SCHEMA_VERSION
    widgets: list[DashboardWidgetInstance] = Field(default_factory=list)
    placements: dict[str, list[WidgetPlacement]] = Field(default_factory=dict)

    @field_validator("widgets")
    @classmethod
    def _unique_instance_ids(cls, widgets: list[DashboardWidgetInstance]) -> list[DashboardWidgetInstance]:
        ids = [w.instance_id for w in widgets]
        if len(ids) != len(set(ids)):
            raise ValueError("instance_id values in the dashboard layout must be unique")
        return widgets

    @model_validator(mode="after")
    def _placements_are_consistent(self) -> DashboardLayout:
        known = {w.instance_id for w in self.widgets}
        for breakpoint_key, places in self.placements.items():
            if breakpoint_key not in GRID_COLS_BY_BREAKPOINT:
                raise ValueError(f"unknown breakpoint: {breakpoint_key}")
            for placement in places:
                if placement.instance_id not in known:
                    raise ValueError(f"placement references unknown instance_id: {placement.instance_id}")
        return self


class UserPreference(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    experience_level: ExperienceLevel = ExperienceLevel.BEGINNER
    onboarding_completed: bool = False
    locale: str = "de"
    theme: str = "system"
    temperature_unit: str = "celsius"
    watering_can_liters: float = 10.0
    smart_home_enabled: bool = False
    # UI-NFR-019 Kiosk mode — greenhouse operation with gloves/dirty hands.
    # ``kiosk_enabled`` activates the touch-optimized kiosk shell; ``high_contrast``
    # is the WCAG-AAA theme (auto-default in kiosk, R-005; standalone-usable, R-045).
    kiosk_enabled: bool = False
    high_contrast: bool = False
    module_visibility: dict[str, ModuleVisibilityState] = Field(
        default_factory=dict,
        description=(
            "Personal per-module visibility overrides. Key = module key from the "
            "frontend catalog; value = explicit visibility. Modules without an "
            "entry follow the experience level (REQ-021). Core modules are ignored."
        ),
    )
    dashboard_layout: DashboardLayout | None = Field(
        default=None,
        description=(
            "Personalized dashboard layout (REQ-045). null/absent => the "
            "frontend renders the experience-level default (not materialized)."
        ),
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("module_visibility", mode="after")
    @classmethod
    def _drop_core_overrides(cls, value: dict[str, ModuleVisibilityState]) -> dict[str, ModuleVisibilityState]:
        return {k: v for k, v in value.items() if k not in CORE_MODULE_KEYS}
