from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError

from app.common.enums import SuccessionPlanStatus

#: The longest window one batch may hold its slots: three years, the bound of ``Cultivar.days_to_maturity``.
MAX_BATCH_DURATION_DAYS = 1095

# ── Operational quotas (REQ-013 §2 v2.9, #2776 SEC-001) ──────────────────────
# Not agronomic values: they bound the work one generation does. Every batch is a planting run, an entry, a slot
# choice and a graph edge written in one request; unbounded, a plan of a ten-year window sown daily would
# materialise thousands of runs in a single call (REST and MCP alike, a dry run included).

#: Batches one succession plan may hold (two years sown weekly).
MAX_SUCCESSION_BATCHES = 104
#: The longest gap between two sowings.
MAX_SUCCESSION_INTERVAL_DAYS = 365
#: The longest sowing window, ``end_date - start_date``: three years.
MAX_SUCCESSION_WINDOW_DAYS = 1096
#: Plants one batch may hold.
MAX_PLANTS_PER_BATCH = 10_000
#: The error type (and published code) of a breached quota; the context names ``quota``, ``limit`` and ``current``.
ERROR_SUCCESSION_QUOTA = "succession.quota_exceeded"


def succession_batch_count(start_date: date, end_date: date, interval_days: int) -> int:
    """Batches sown on ``start_date`` and then every ``interval_days`` up to and including ``end_date``."""
    span_days = (end_date - start_date).days
    if span_days < 0 or interval_days < 1:
        return 0
    return span_days // interval_days + 1


def check_succession_quotas(start_date: date, end_date: date, interval_days: int) -> None:
    """Refuse a schedule over the window or batch quota (``succession.quota_exceeded {quota, limit, current}``).

    Shared by the domain model and every request schema that builds one, so REST, MCP and the update path refuse
    the same plan with the same 422 (BACKEND.md §5.4).
    """
    window = (end_date - start_date).days
    if window > MAX_SUCCESSION_WINDOW_DAYS:
        raise PydanticCustomError(
            ERROR_SUCCESSION_QUOTA,
            "The sowing window may span at most {limit} days, this one spans {current}.",
            {"quota": "window_days", "limit": MAX_SUCCESSION_WINDOW_DAYS, "current": window},
        )
    batches = succession_batch_count(start_date, end_date, interval_days)
    if batches > MAX_SUCCESSION_BATCHES:
        raise PydanticCustomError(
            ERROR_SUCCESSION_QUOTA,
            "A succession plan may hold at most {limit} batches, this schedule yields {current}.",
            {"quota": "batches", "limit": MAX_SUCCESSION_BATCHES, "current": batches},
        )


class SuccessionPlan(BaseModel):
    """REQ-013 §2 — staggered-sowing plan that generates a series of PlantingRuns.

    A succession plan (Staffelanbau) describes a species that is re-sown at a
    fixed interval across a growing window ("all 3 weeks re-sow lettuce"). The
    plan auto-generates one PlantingRun per batch; ``total_batches`` is derived
    from the schedule and ``completed_batches`` tracks how many batches have
    already been generated.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    species_key: str
    cultivar_key: str | None = None
    interval_days: int = Field(ge=1, le=MAX_SUCCESSION_INTERVAL_DAYS)
    start_date: date
    end_date: date
    plants_per_batch: int = Field(ge=1, le=MAX_PLANTS_PER_BATCH)
    total_batches: int = Field(default=0, ge=0)
    completed_batches: int = Field(default=0, ge=0)
    status: SuccessionPlanStatus = SuccessionPlanStatus.PLANNED
    reminder_days_before: int = Field(default=3, ge=0)
    #: How long one batch holds its slots, in days (GP-FR-065 ``planned_until``, set by hand); ``None`` = open end.
    batch_duration_days: int | None = Field(default=None, ge=1, le=MAX_BATCH_DURATION_DAYS)
    location_key: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_date_range(self) -> SuccessionPlan:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        check_succession_quotas(self.start_date, self.end_date, self.interval_days)
        return self
