"""Request/response schemas of the care log (REQ-053 §20.10, §21.2; GP-API-033…037, GP-API-041).

The request bodies are the domain input models (:class:`CareEventInput`, :class:`CareEventCorrection`) with a
documented example: what a client may send is decided once, in the domain, and ``extra="forbid"`` there turns a
forged ``trigger = task``, ``task_key``, ``source_ref``, ``created_by`` or ``tenant_key`` into a 422.

The response never carries an account key (GP-API-034): ``performed_by`` / ``performed_for`` are display
names, the third party's label or ``"anonymisiert"``, and ``created_by_me`` tells the caller whether they may
correct the entry.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.config import JsonDict

from app.domain.models.care_event import CareEventCorrection, CareEventInput, CareEventView

_EXAMPLE: JsonDict = {
    "location_key": "loc_b03",
    "plant_keys": ["pi_tom_003", "pi_tom_004"],
    "category": "feeding",
    "summary": "Tomatoes fed with nettle tea",
    "performed_at": "2026-06-14T18:30:00Z",
    "reason": "Leaves are yellowing, two weeks since the last dose",
    "product_ref": {"kind": "fertilizer", "key": "fert_nettle_tea"},
    "quantity": 2.0,
    "unit": "l_per_m2",
    "outcome_rating": "unknown",
}


class CareEventCreate(CareEventInput):
    """``POST /care-events`` (GP-API-033); ``trigger`` is ``manual`` or ``observation`` and defaults to ``manual``."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [_EXAMPLE]})


class CareEventSupersedeRequest(CareEventCorrection):
    """``POST /care-events/{key}/supersede`` (GP-API-036): the corrected entry; the bed and the trigger are kept."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{k: v for k, v in _EXAMPLE.items() if k != "location_key"} | {"quantity": 3.0}]
        },
    )


class CareEventVoidRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"reason": "undo"}]})

    reason: str = Field(
        min_length=1,
        max_length=200,
        description="Why it is cancelled. `undo` marks the author taking back their own entry within ten minutes.",
    )


class CareEventRedactRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [{"reason": "Personal data of a third party"}]}
    )

    reason: str = Field(
        min_length=1,
        max_length=500,
        description="The ground of the redaction. It stays on the entry: name the ground, never the redacted data.",
    )


class CareEventResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [_EXAMPLE | {"key": "ce_8d2e", "performed_by": "Sabine"}]})

    key: str
    site_key: str
    location_key: str
    plant_keys: list[str] = Field(default_factory=list)
    category: str
    summary: str
    performed_at: datetime
    #: Display name, the third party's label, or `anonymisiert`; never an account key.
    performed_by: str | None = None
    performed_for: str | None = None
    #: A third party who did the work, typed by whoever logged it (no full names, SR-006); `[redacted]` afterwards.
    performed_by_label: str | None = None
    created_by_me: bool = False
    trigger: str
    task_key: str | None = None
    reason: str | None = None
    product_ref: dict[str, Any] | None = None
    product_label: str | None = None
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
    void_reason: str | None = None
    redacted_at: datetime | None = None
    redaction_reason: str | None = None
    created_at: datetime | None = None
    #: The supersede chain, oldest first; filled by `GET /care-events/{key}` only.
    chain: list[str] = Field(default_factory=list)


def care_event_to_response(view: CareEventView) -> CareEventResponse:
    event = view.event
    return CareEventResponse(
        key=event.key or "",
        site_key=event.site_key,
        location_key=event.location_key,
        plant_keys=event.plant_keys,
        category=event.category,
        summary=event.summary,
        performed_at=event.performed_at,
        performed_by=view.performed_by,
        performed_for=view.performed_for,
        performed_by_label=event.performed_by_label,
        created_by_me=view.created_by_me,
        trigger=event.trigger,
        task_key=event.task_key,
        reason=event.reason,
        product_ref=event.product_ref,
        product_label=event.product_label,
        quantity=event.quantity,
        unit=event.unit,
        quantity_total=event.quantity_total,
        quantity_total_unit=event.quantity_total_unit,
        material=event.material,
        measurements=event.measurements,
        observed_outcome=event.observed_outcome,
        outcome_rating=event.outcome_rating,
        photo_refs=event.photo_refs,
        source_ref=event.source_ref,
        supersedes_key=event.supersedes_key,
        superseded_by_key=event.superseded_by_key,
        voided_at=event.voided_at,
        void_reason=event.void_reason,
        redacted_at=event.redacted_at,
        redaction_reason=event.redaction_reason,
        created_at=event.created_at,
        chain=view.chain_keys,
    )
