"""The care event: one append-only line of a bed's care log (REQ-053 §20.10, §13).

The model carries the **whole** stored shape of §20.10. WP 1.9 (#2328) wrote the first rows (the bed-status
change); WP 4.1 (#2400) adds the care-event service and API on top — supersede, void, redact and the rules V-11 /
V-12 / V-13 — and the input models below. What a client may send (:class:`CareEventInput`) and what only the server
sets (:class:`CareEventOrigin`) are separate types, so no HTTP body can reach ``trigger = task``, ``task_key``,
``source_ref`` or the backfill window (SR-009).

Unlike ``locations``, ``slots`` and ``garden_objects`` a care event **does** carry
``tenant_key`` (§20.13, E-01): it is listed tenant-wide (GP-FR-107), so the tenant
is a column of the collection and not a property of one site.

``category`` is the union of ``TaskCategory`` and the protocol-only values below
(§20.10). It is a string here on purpose: a second enum would have to be kept in
step with ``TaskCategory`` by hand, and an enum member can never be retired.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.enums import CareEventAllocation, EcMethod, PhMethod, PlanRole, TaskCategory

#: The erasure marker of an account key (mirrors ``ErasureEngine``; the model layer may not import an engine).
ANONYMIZED_MARKER = "_anonymized"

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

#: What the client writes (GP-FR-100, §20.10); every other trigger is set by the server.
CLIENT_TRIGGERS: frozenset[str] = frozenset({"manual", "observation"})

#: Categories only server code writes: the bed-status route, slot corrections, the plant/removal derivations,
#: clearing (WP 3.2) and the backfill (WP 3.4). ``POST /care-events`` refuses them — a client-made
#: ``bed_status_change`` would bypass the status machine (V-10), a client-made ``planting`` would forge the
#: crop-rotation history (GP-FR-103).
SERVER_ONLY_CATEGORIES: frozenset[str] = frozenset(
    {CATEGORY_BED_STATUS_CHANGE, "position_corrected", "planting", "removal", "clearing"}
)

#: ``unit`` values (GP-FR-100). ``l_per_m2`` / ``g_per_m2`` are area doses; the service derives ``quantity_total``.
CARE_EVENT_UNITS: frozenset[str] = frozenset({"l", "ml", "g", "kg", "l_per_m2", "g_per_m2", "cm", "pieces"})
OUTCOME_RATINGS: frozenset[str] = frozenset({"positive", "neutral", "negative", "unknown"})

#: ``measurements`` exist only on these categories (§20.10).
MEASUREMENT_CATEGORIES: frozenset[str] = frozenset({"soil_analysis", "ec_check"})
MEASUREMENT_PARAMETERS: tuple[str, ...] = ("ph", "ec", "n_min", "p", "k", "mg", "humus", "caco3", "moisture")

#: PflSchG §11: the care log of a treatment keeps the longer retention (NFR-011 R-25).
PFLSCHG_CATEGORIES: frozenset[str] = frozenset({TaskCategory.PEST_CONTROL.value, TaskCategory.IPM.value})

#: The marker a redaction (GP-FR-109) and the retention anonymisation (R-25) write into free-text fields.
REDACTED = "[redacted]"
#: The free-text fields of a care event (GP-FR-109) — redacted as one set, never one by one.
FREE_TEXT_FIELDS: tuple[str, ...] = ("summary", "reason", "observed_outcome", "product_label", "performed_by_label")
#: The five account references of a stored care event (GP-NFR-055); the erasure and the retention clear all of them.
ACCOUNT_FIELDS: tuple[str, ...] = (
    "performed_by_user_key",
    "performed_for_user_key",
    "created_by",
    "voided_by",
    "redacted_by",
)

#: Window of V-11 (GP-ACC-025): a client event is at most five minutes ahead and a year back; a backfill reaches
#: ten years.
FUTURE_TOLERANCE_MINUTES = 5
MAX_AGE_DAYS = 365
BACKFILL_MAX_AGE_DAYS = 3650
#: A backfilled year is a calendar year (GP-API-042): ``current year - 10`` mid-season can lie this far back.
BACKFILL_YEAR_WINDOW_DAYS = BACKFILL_MAX_AGE_DAYS + 366
#: ``void`` with ``void_reason = undo`` by the author is a grower's right for this long (GP-API-037, GP-FR-149).
UNDO_WINDOW_MINUTES = 10
#: ``reason`` of an author taking back their own entry inside the window (GP-API-037, GP-FR-149).
UNDO_REASON = "undo"

MAX_PLANTS_PER_EVENT = 200
MAX_PHOTOS_PER_EVENT = 10


#: Seasons of a backfilled year (GP-API-042): the ``performed_at`` the server stamps is the middle of the season.
BACKFILL_SEASONS: tuple[str, ...] = ("spring", "main", "autumn")


class RotationEntry(BaseModel):
    """What a backfilled ``planting`` event says about the bed: the family that stood there (GP-API-042, GP-FR-131).

    Server-set only (a client body cannot carry it: :class:`CareEventInput` has no such field), so the crop-rotation
    history cannot be forged through ``POST /care-events`` (SR-009). ``family_key`` is ``None`` for a fallow year
    only, which occupies the bed with no family.
    """

    model_config = ConfigDict(extra="forbid")

    year: int = Field(ge=1900, le=2200)
    season: Literal["spring", "main", "autumn"] | None = None
    family_key: str | None = Field(default=None, min_length=1, max_length=200)
    species_key: str | None = Field(default=None, min_length=1, max_length=200)
    plan_role: PlanRole = PlanRole.MAIN_CROP

    @model_validator(mode="after")
    def _family_unless_fallow(self) -> Self:
        if self.family_key is None and self.plan_role != PlanRole.FALLOW:
            raise ValueError("A planted year names the family that stood in the bed.")
        return self


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
    #: ``measured`` unless a zone watering round divided a total over its beds (GP-FR-117); server-set only.
    allocation: CareEventAllocation = CareEventAllocation.MEASURED
    material: str | None = None
    measurements: list[dict[str, Any]] | None = None
    observed_outcome: str | None = None
    outcome_rating: str = "unknown"
    photo_refs: list[str] = Field(default_factory=list)
    source_ref: dict[str, Any] | None = None
    #: The family / species / role of a backfilled ``planting`` event (WP 3.4); ``None`` on every other event.
    rotation_entry: RotationEntry | None = None
    supersedes_key: str | None = None
    superseded_by_key: str | None = None
    voided_at: datetime | None = None
    voided_by: str | None = None
    void_reason: str | None = None
    redacted_at: datetime | None = None
    redacted_by: str | None = None
    redaction_reason: str | None = None
    #: Set once by ``retention.anonymize_expired_care_events`` (NFR-011 R-25): the person fields, the free texts and
    #: the photos are gone and the sweep selects the row no more. A system mutation like the redaction, not an edit.
    retention_anonymized_at: datetime | None = None
    #: The client's id of a buffered write (WP 9.3), unique per tenant (sparse index, v0106); ``None`` when the
    #: client sent none and on every server-made event.
    client_event_id: str | None = None
    #: The digest of the request that wrote this event (:func:`~app.domain.models.client_event.client_event_digest`);
    #: a replay with another body under the same id is refused.
    client_event_digest: str | None = None
    #: The client's id of the zone round that wrote this event with its siblings (REQ-053 WP 9.13, "rain -
    #: skipped"): every event of the round carries the raw id, so a replay finds the stored round whatever the
    #: zone covers now (sparse index ``(tenant_key, client_round_id)``, bootstrap-only). ``None`` everywhere else.
    client_round_id: str | None = None
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


# ── What a client may send (GP-API-033) ─────────────────────────────────────────


class ProductRef(BaseModel):
    """A fertilizer of the catalogue (global or the tenant's own); resolved server-side (GP-NFR-058)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["fertilizer"]
    key: str = Field(min_length=1, max_length=200)


#: The classes of a lab result by the CAL method (A very low ... E very high), taken over exactly as stated.
CONTENT_CLASSES: tuple[str, ...] = ("A", "B", "C", "D", "E")
#: Parameters a CAL content class exists for (REQ-053 §15.1: P, K, Mg in mg per 100 g).
CONTENT_CLASS_PARAMETERS: frozenset[str] = frozenset({"p", "k", "mg"})
#: The physical range of the parameters that land in the soil profile; a value outside is a typing error.
_PROFILE_RANGES: dict[str, tuple[float, float]] = {
    "ph": (0.0, 14.0),
    "ec": (0.0, float("inf")),
    "humus": (0.0, 100.0),
    "caco3": (0.0, 100.0),
}


class Measurement(BaseModel):
    """One soil or EC measurement (§15.1, §20.10).

    **Method rules (U-002/U-003, WP 8.7).** A conductivity of a ``soil_analysis`` needs its ``ec_method`` (checked on
    the event: a nutrient-solution ``ec_check`` has no soil extraction method; no salt assessment without it); a
    ``content_class`` (A-E) is only *taken over* from a lab result by the CAL method for P, K or Mg - a test kit or a
    sensor has none, and the system never computes one. ``ph_method`` is the method of a pH value.
    """

    model_config = ConfigDict(extra="forbid")

    parameter: Literal["ph", "ec", "n_min", "p", "k", "mg", "humus", "caco3", "moisture"]
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=20)
    extraction_method: str | None = Field(default=None, max_length=60)
    sample_depth_cm: float | None = Field(default=None, ge=0, le=1000)
    source: str = Field(default="manual", max_length=40)
    ec_method: EcMethod | None = None
    ph_method: PhMethod | None = None
    content_class: Literal["A", "B", "C", "D", "E"] | None = None

    @model_validator(mode="after")
    def _method_rules(self) -> Self:
        if self.ec_method is not None and self.parameter != "ec":
            raise ValueError("ec_method belongs to a conductivity.")
        if self.ph_method is not None and self.parameter != "ph":
            raise ValueError("ph_method belongs to a pH value.")
        if self.content_class is not None and not (
            self.source == "lab" and self.extraction_method == "cal" and self.parameter in CONTENT_CLASS_PARAMETERS
        ):
            raise ValueError(
                "A content class is taken over only from a lab result by the CAL method for P, K or Mg; "
                "it is never computed."
            )
        if self.parameter in _PROFILE_RANGES:
            low, high = _PROFILE_RANGES[self.parameter]
            if not low <= self.value <= high:
                raise ValueError(f"The value of '{self.parameter}' is outside its possible range.")
        return self


class _CareEventFields(BaseModel):
    """The descriptive fields of a care event a client sends, on create and on a correction alike (GP-FR-100).

    Deliberately absent: ``tenant_key`` (the path), ``site_key`` (derived from the owned location),
    ``performed_by_user_key`` and ``created_by`` (the token, GP-NFR-054), ``task_key``, ``source_ref``,
    ``quantity_total`` and the supersede/void/redaction columns (server-owned). ``extra="forbid"`` turns a
    client that sends one of them into a 422 instead of a silently ignored field.
    """

    model_config = ConfigDict(extra="forbid")

    plant_keys: list[str] = Field(default_factory=list, max_length=MAX_PLANTS_PER_EVENT)
    category: str
    summary: str = Field(min_length=1, max_length=500)
    performed_at: datetime
    performed_for_user_key: str | None = Field(default=None, max_length=200)
    #: A third party who did the work (``performed_by_label``): free text, no full names (SR-006).
    performed_by_label: str | None = Field(default=None, max_length=80)
    reason: str | None = Field(default=None, max_length=1000)
    product_ref: ProductRef | None = None
    product_label: str | None = Field(default=None, max_length=200)
    quantity: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    unit: str | None = None
    material: str | None = Field(default=None, max_length=200)
    measurements: list[Measurement] | None = Field(default=None, max_length=50)
    observed_outcome: str | None = Field(default=None, max_length=2000)
    outcome_rating: str = "unknown"
    photo_refs: list[str] = Field(default_factory=list, max_length=MAX_PHOTOS_PER_EVENT)

    @field_validator("category")
    @classmethod
    def _known_category(cls, value: str) -> str:
        if value not in CARE_EVENT_CATEGORIES:
            raise ValueError(f"Unknown care event category '{value}'.")
        return value

    @field_validator("unit")
    @classmethod
    def _known_unit(cls, value: str | None) -> str | None:
        if value is not None and value not in CARE_EVENT_UNITS:
            raise ValueError(f"Unknown unit '{value}'.")
        return value

    @field_validator("outcome_rating")
    @classmethod
    def _known_rating(cls, value: str) -> str:
        if value not in OUTCOME_RATINGS:
            raise ValueError(f"Unknown outcome rating '{value}'.")
        return value

    @field_validator("summary")
    @classmethod
    def _summary_has_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("The summary must not be blank.")
        return value.strip()

    @field_validator("performed_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        """A naive instant is read as UTC (§20.13: ``performed_at`` is UTC)."""
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.measurements is not None and self.category not in MEASUREMENT_CATEGORIES:
            raise ValueError("measurements are allowed on soil_analysis and ec_check events only.")
        if self.category == "soil_analysis" and any(
            m.parameter == "ec" and m.ec_method is None for m in self.measurements or ()
        ):
            raise ValueError("A conductivity of a soil analysis needs its ec_method.")
        if self.quantity is not None and self.unit is None:
            raise ValueError("A quantity needs a unit.")
        if len(set(self.plant_keys)) != len(self.plant_keys):
            raise ValueError("plant_keys must not repeat a key.")
        if len(set(self.photo_refs)) != len(self.photo_refs):
            raise ValueError("photo_refs must not repeat a reference.")
        return self


class CareEventInput(_CareEventFields):
    """The body of ``POST /care-events`` (GP-API-033): the bed and, as the one client choice of trigger, its kind."""

    location_key: str = Field(min_length=1, max_length=200)
    trigger: str = "manual"
    #: A buffered write's id (WP 9.3): a replay with the same id answers the stored event, never a second one.
    client_event_id: UUID | None = None

    @field_validator("trigger")
    @classmethod
    def _client_trigger(cls, value: str) -> str:
        if value not in CLIENT_TRIGGERS:
            raise ValueError("A client may set the trigger 'manual' or 'observation' only.")
        return value


class CareEventCorrection(_CareEventFields):
    """The body of ``POST /care-events/{key}/supersede`` (GP-API-036): the corrected fields.

    No ``location_key`` (a correction stays on the bed of its predecessor, V-13) and no ``trigger`` (the
    predecessor's is kept — a corrected task log stays a task log).
    """


@dataclass(frozen=True)
class CareEventOrigin:
    """Server-side provenance of an event: the fields no HTTP body can carry (SR-009).

    ``None`` as the origin of :meth:`CareEventService.create` means "a client": ``trigger`` comes from the input
    (``manual`` / ``observation``) and the server-only categories are refused. A caller inside the server — the
    task completion (WP 4.3, ``trigger = task``), clearing (WP 3.2, ``system``), the backfill (WP 3.4,
    ``backfill``) — passes one.
    """

    trigger: str
    task_key: str | None = None
    #: ``{"collection": ..., "key": ...}``: the specialist document this event is the log line of.
    source_ref: dict[str, str] | None = None
    #: V-11 exempts server-made backfill events (GP-API-042, GP-FR-105): they reach ten years back.
    max_age_days: int = MAX_AGE_DAYS
    #: Set by the backfill (WP 3.4) only; the family the bed carried that year.
    rotation_entry: RotationEntry | None = None

    def __post_init__(self) -> None:
        if self.trigger not in CARE_EVENT_TRIGGERS:
            raise ValueError(f"Unknown care event trigger '{self.trigger}'.")
        if self.max_age_days > BACKFILL_YEAR_WINDOW_DAYS:
            raise ValueError("A backfill reaches ten calendar years back at most.")
        if self.rotation_entry is not None and self.trigger != "backfill":
            raise ValueError("Only a backfill carries a rotation entry.")


#: What the API shows for an account that is erased or gone (GP-API-034).
PERFORMED_BY_ANONYMISED = "anonymisiert"


def display_performer(
    account_key: str | None,
    display_name: str | None,
    label: str | None = None,
    *,
    anonymised: str = PERFORMED_BY_ANONYMISED,
) -> str | None:
    """Who carried the care out, as the API names them: a display name, the third party's label, or "anonymisiert".

    Never the account key (GP-API-034). An account key whose user document is gone or that carries the erasure
    marker reads ``anonymised`` ("anonymisiert" unless a printed document passes its own language's word);
    no key and no label (a system entry) reads ``None``.
    """
    if account_key:
        return display_name if display_name and account_key != ANONYMIZED_MARKER else anonymised
    return label or None


class CareEventView(BaseModel):
    """A stored event with the readable names of the accounts it refers to (GP-API-034, never an account key)."""

    event: CareEvent
    #: Display name, the third party's label, or ``"anonymisiert"``; ``None`` for a system entry.
    performed_by: str | None = None
    #: Display name of the member the care was done for (``performed_for_user_key``); ``None`` when none.
    performed_for: str | None = None
    #: Whether the caller logged this entry (``created_by``) — the owner may correct it (GP-API-036).
    created_by_me: bool = False
    #: The Supersede chain of an event, oldest first (GP-API-035); empty for a list row.
    chain_keys: list[str] = Field(default_factory=list)
    #: Readable names of the event's plants, in ``plant_keys`` order; a plant that is gone is left out (#2514).
    plant_names: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class LoggedCareEvent:
    """What ``POST /care-events`` answers: the event, and whether it was a replay of a stored one (WP 9.3).

    ``replayed`` is ``True`` when the ``client_event_id`` named an event stored before - the first answer was
    201, a replay is 200 with the same body.
    """

    view: CareEventView
    replayed: bool = False
