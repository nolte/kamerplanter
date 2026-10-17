"""The care event: one append-only line of a bed's care log (REQ-053 §20.10, §13).

WP 1.9 (#2328) needs exactly one writer — the bed-status change (``category =
bed_status_change``, GP-FR-046, GP-ACC-015) — so the model carries the **whole**
stored shape of §20.10 but only that path validates and writes it. The care-event
API (supersede, void, redact, the past-date rules of V-11/V-12/V-13) is WP 4.1 and
extends this model rather than replacing it.

Unlike ``locations``, ``slots`` and ``garden_objects`` a care event **does** carry
``tenant_key`` (§20.13, E-01): it is listed tenant-wide (GP-FR-107), so the tenant
is a column of the collection and not a property of one site.

``category`` is the union of ``TaskCategory`` and the protocol-only values below
(§20.10). It is a string here on purpose: a second enum would have to be kept in
step with ``TaskCategory`` by hand, and an enum member can never be retired.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.enums import TaskCategory

#: The categories a care event has that a task does not (§20.10).
PROTOCOL_ONLY_CATEGORIES: frozenset[str] = frozenset(
    {"note", "soil_analysis", "bed_status_change", "position_corrected", "planting", "removal", "clearing"}
)

#: Every value ``category`` may take.
CARE_EVENT_CATEGORIES: frozenset[str] = frozenset(c.value for c in TaskCategory) | PROTOCOL_ONLY_CATEGORIES

#: ``trigger`` values; the client may set ``manual`` / ``observation`` only, the server sets the rest (SR-009).
CARE_EVENT_TRIGGERS: frozenset[str] = frozenset(
    {"task", "reminder", "suggestion", "manual", "observation", "backfill", "system"}
)

CATEGORY_BED_STATUS_CHANGE = "bed_status_change"


class CareEvent(BaseModel):
    """A stored care event (§20.10). Immutable after creation except supersede / void / redaction (V-12)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    site_key: str
    location_key: str
    plant_keys: list[str] = Field(default_factory=list)
    category: str
    summary: str = Field(default="", max_length=500)
    performed_at: datetime
    performed_by_user_key: str | None = None
    performed_for_user_key: str | None = None
    performed_by_label: str | None = Field(default=None, max_length=200)
    trigger: str = "manual"
    task_key: str | None = None
    reason: str | None = Field(default=None, max_length=1000)
    product_ref: dict[str, Any] | None = None
    product_label: str | None = Field(default=None, max_length=200)
    quantity: float | None = None
    unit: str | None = None
    quantity_total: float | None = None
    quantity_total_unit: str | None = None
    material: str | None = None
    measurements: list[dict[str, Any]] | None = None
    observed_outcome: str | None = None
    outcome_rating: str = "unknown"
    photo_refs: list[str] = Field(default_factory=list)
    source_ref: dict[str, Any] | None = None
    supersedes_key: str | None = None
    superseded_by_key: str | None = None
    voided_at: datetime | None = None
    voided_by: str | None = None
    void_reason: str | None = None
    redacted_at: datetime | None = None
    redacted_by: str | None = None
    redaction_reason: str | None = None
    created_at: datetime | None = None
    created_by: str | None = None

    model_config = {"populate_by_name": True}

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in CARE_EVENT_CATEGORIES:
            raise ValueError(f"Unknown care event category '{value}'.")
        return value

    @field_validator("trigger")
    @classmethod
    def validate_trigger(cls, value: str) -> str:
        if value not in CARE_EVENT_TRIGGERS:
            raise ValueError(f"Unknown care event trigger '{value}'.")
        return value
