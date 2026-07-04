from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import (
    HardinessRating,
    SpringAction,
    TuberStatus,
    WinterAction,
    WinterQuarterLight,
    WinterWatering,
)


class OverwinteringProfileTemplate(BaseModel):
    """REQ-022 §OverwinteringProfile — species-level overwintering *template*.

    Distinct from :class:`~app.domain.models.overwintering_profile.OverwinteringProfile`,
    which is a per-instance (plant / planting-run) record. This template captures the
    species-specific overwintering knowledge curated in the plant Steckbriefe
    (``spec/knowledge/plants/*.md`` §4.3 "Überwinterung") so that auto-generation can
    seed instance profiles with species-accurate values instead of generic defaults.

    Reference data only: not tenant-scoped, no subject, no runtime D5 enforcement
    (the instance flow validates D5 against the actual site zone).
    """

    key: str | None = Field(default=None, alias="_key")

    # Subject: the species this template describes.
    species_scientific_name: str
    species_key: str | None = None

    # Hardiness assessment.
    hardiness_zone_min: str | None = None
    hardiness_rating: HardinessRating

    # Winter action (path A in-situ protection or path B relocation).
    winter_action: WinterAction
    #: Optional: a ``none`` action on a fully hardy species has no meaningful month.
    winter_action_month: int | None = Field(default=None, ge=1, le=12)

    # Spring reactivation.
    spring_action: SpringAction | None = None
    spring_action_month: int | None = Field(default=None, ge=1, le=12)

    # Winter quarter conditions (path B).
    winter_quarter_temp_min: float | None = None
    winter_quarter_temp_max: float | None = None
    winter_quarter_light: WinterQuarterLight | None = None
    winter_watering: WinterWatering | None = None

    # Tuber/bulb storage cycle (hardiness_rating == dig_and_store).
    storage_medium: str | None = None
    storage_check_interval_days: int | None = Field(default=None, ge=1, le=365)
    tuber_status: TuberStatus | None = None

    notes: str | None = None
    #: Provenance of the curated data (default: the plant Steckbriefe).
    source: str = "steckbrief"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    def winter_quarter_fields(self) -> dict:
        """The winter-quarter / storage subset of this template (non-null only).

        Single source of truth for adapting a template onto an ``OverwinteringProfile``
        — shared by care-reminder resolution and auto-generation enrichment so the two
        paths cannot drift.
        """
        fields = {
            "winter_quarter_temp_min": self.winter_quarter_temp_min,
            "winter_quarter_temp_max": self.winter_quarter_temp_max,
            "winter_quarter_light": self.winter_quarter_light,
            "winter_watering": self.winter_watering,
            "storage_medium": self.storage_medium,
            "storage_check_interval_days": self.storage_check_interval_days,
            "tuber_status": self.tuber_status,
        }
        return {k: v for k, v in fields.items() if v is not None}

    @model_validator(mode="after")
    def _validate_tuber_status(self) -> OverwinteringProfileTemplate:
        """``tuber_status`` is only meaningful for the dig-and-store rating."""
        if self.tuber_status is not None and self.hardiness_rating != HardinessRating.DIG_AND_STORE:
            raise ValueError("tuber_status is only valid when hardiness_rating is 'dig_and_store'.")
        return self

    @model_validator(mode="after")
    def _validate_temp_range(self) -> OverwinteringProfileTemplate:
        """Winter-quarter min must not exceed max when both are given."""
        if (
            self.winter_quarter_temp_min is not None
            and self.winter_quarter_temp_max is not None
            and self.winter_quarter_temp_min > self.winter_quarter_temp_max
        ):
            raise ValueError("winter_quarter_temp_min must not exceed winter_quarter_temp_max.")
        return self
