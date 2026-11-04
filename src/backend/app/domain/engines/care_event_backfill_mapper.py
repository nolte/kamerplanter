"""Turns one domain document into the care event that logs it (REQ-053 GP-FR-105, GP-NFR-015 ``M4``; WP 8.1, #2644).

Pure rules, no database: the migration ``v0104`` reads the four domain-event collections, resolves each document's
bed in the database (``plant / slot -> location -> site``) and hands the *resolved row* to the functions below.
Dry run and real run take this one path, so a dry run counts what a real run writes.

What the mapper decides (and the migration never re-decides):

* **Which bed, which tenant** (:func:`resolve_anchor`). The bed comes from the references of the document (its
  plants, slots or its own ``location_key``); site and tenant come from the *bed's site*, never from the source
  document alone. A document stamped with another tenant than the bed's site, one that names more than one bed, one
  that names a reference nobody can resolve and one without any reference are **counted and never written**
  (:class:`SkipReason`).
* **The R-25 window** (:func:`window_start`, :func:`performed_at_of`). A backfilled event older than the retention
  period of the care log (NFR-011 R-25, five years) would be anonymised by the next sweep, so it is not written at
  all; it is counted as outside the window.
* **The event** (:func:`map_document`). ``trigger = backfill``; ``source_ref = {collection, key}`` is the marker
  that makes a second run write nothing (unique-sparse index of WP 4.1) and the migration reversible;
  ``performed_by_user_key`` only from an *account reference* of the source (``applied_by_key``,
  ``harvested_by_key``), otherwise ``None`` — a display text typed into a form (``performed_by``, ``harvester``,
  ``applied_by``) is a name, not an account, and free-text ``notes`` are not copied (SR-006). A value the source does
  not state stays ``None`` (E-10): a treatment dosage has no unit, so the event carries no quantity; no product is
  resolved (the source stays reachable through ``source_ref``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.common.datetimes import replace_year
from app.domain.models.care_event import CARE_EVENT_UNITS, CareEvent

WATERING_EVENTS = "watering_events"
FEEDING_EVENTS = "feeding_events"
TREATMENT_APPLICATIONS = "treatment_applications"
HARVEST_BATCHES = "harvest_batches"
#: A confirmed care reminder of a plant (REQ-053 GP-FR-106, WP 8.3). It carries no ``tenant_key`` of its own.
CARE_CONFIRMATIONS = "care_confirmations"

#: The domain-event collections a care event can log (GP-FR-105, GP-FR-106), in the order the report lists them.
SOURCE_COLLECTIONS: tuple[str, ...] = (
    WATERING_EVENTS,
    FEEDING_EVENTS,
    TREATMENT_APPLICATIONS,
    HARVEST_BATCHES,
    CARE_CONFIRMATIONS,
)

#: Sources whose documents carry no ``tenant_key``: the plant's tenant (which must equal the bed's site's) is the
#: document's tenant. Every other source is stamped, and a stamp that disagrees with the bed's site is never written.
UNSTAMPED_SOURCES: frozenset[str] = frozenset({CARE_CONFIRMATIONS})

#: Sources of which only some documents are a performed care: a skipped or snoozed reminder is not (the scan
#: filters ``action`` and the dry run counts only the performed ones).
ACTION_FILTERS: dict[str, str] = {CARE_CONFIRMATIONS: "confirmed"}

#: The attribute that carries the instant of each source (``performed_at`` of the event).
TIME_FIELDS: dict[str, str] = {
    WATERING_EVENTS: "watered_at",
    FEEDING_EVENTS: "timestamp",
    TREATMENT_APPLICATIONS: "applied_at",
    HARVEST_BATCHES: "harvest_date",
    CARE_CONFIRMATIONS: "confirmed_at",
}

#: The attribute that holds an *account reference* (a user key); sources without one never name a performer.
ACCOUNT_FIELDS: dict[str, str | None] = {
    WATERING_EVENTS: None,  # ``performed_by`` is free text typed into the form, not an account
    FEEDING_EVENTS: None,
    TREATMENT_APPLICATIONS: "applied_by_key",
    HARVEST_BATCHES: "harvested_by_key",
    CARE_CONFIRMATIONS: None,  # a confirmation names no account; the live path stamps the caller (GP-NFR-054)
}

#: ``category`` of the event per source (§20.10): a treatment keeps the PflSchG category (``pest_control``).
CATEGORIES: dict[str, str] = {
    WATERING_EVENTS: "watering",
    FEEDING_EVENTS: "feeding",
    TREATMENT_APPLICATIONS: "pest_control",
    HARVEST_BATCHES: "harvest",
}

#: ``ReminderType`` -> care-event ``category`` (GP-FR-106), closed: a new reminder type has no category until it is
#: added here (``tests/unit/domain/engines/test_care_event_backfill_mapper.py`` pins that every one has an entry).
#: Checks and inspections are ``monitoring``; none of them is ``pest_control`` / ``ipm`` (the PflSchG treatment
#: categories keep the longer retention, and a check is not a treatment).
REMINDER_CATEGORIES: dict[str, str] = {
    "watering": "watering",
    "fertilizing": "feeding",
    "repotting": "transplant",
    "pest_check": "monitoring",
    "location_check": "monitoring",
    "humidity_check": "monitoring",
    "deadheading": "pruning",
    "tuber_dig": "maintenance",
    "storage_check": "monitoring",
    "spring_uncover": "uncovering",
    "winter_protection": "covering",
    "dormancy_health_check": "monitoring",
    "quarter_climate_check": "monitoring",
}

SUMMARIES: dict[str, str] = {
    WATERING_EVENTS: "Watering (backfilled)",
    FEEDING_EVENTS: "Feeding (backfilled)",
    TREATMENT_APPLICATIONS: "Plant protection treatment (backfilled)",
    HARVEST_BATCHES: "Harvest (backfilled)",
    CARE_CONFIRMATIONS: "Care reminder confirmed",
}

TRIGGER_BACKFILL = "backfill"
TRIGGER_REMINDER = "reminder"


class SkipReason(StrEnum):
    """Why a source document in the window is **not** written. Every one is counted by the dry run."""

    #: The document names no plant, slot or location at all (a bed-less record, e.g. a bed-level harvest batch).
    NO_REFERENCE = "no_reference"
    #: A reference points at nothing (a deleted plant or slot), or the location / its site is gone.
    UNRESOLVED = "unresolved"
    #: Some references resolve and some do not — which bed the rest belonged to is a guess, so none is written.
    PARTLY_UNRESOLVED = "partly_unresolved"
    #: The references resolve to more than one bed; one source has one ``source_ref``, so it is not split.
    MULTIPLE_BEDS = "multiple_beds"
    #: The bed's location names no site, or the site has no tenant (legacy data): no tenant can be derived.
    SITE_WITHOUT_TENANT = "site_without_tenant"
    #: The document, one of its plants or the bed's site belong to different tenants (or the document has none).
    TENANT_MISMATCH = "tenant_mismatch"
    #: A reminder type no category is mapped for (a confirmation of a type added after this mapping).
    UNMAPPED_CATEGORY = "unmapped_category"


@dataclass(frozen=True)
class BedAnchor:
    """The bed a source document resolved to, with the tenant and site taken from the bed's site."""

    tenant_key: str
    site_key: str
    location_key: str
    #: Plants of the document that stand in the bed (a slot reference names no plant); sorted, unique.
    plant_keys: tuple[str, ...] = ()


def action_filter(collection: str) -> str | None:
    """The ``action`` value a performed document of ``collection`` has, or ``None`` when every document is one."""
    # Not ``.get``: the write-route detector counts a ``.get`` on a module constant as an untyped receiver.
    return ACTION_FILTERS[collection] if collection in ACTION_FILTERS else None  # noqa: SIM401


def window_start(now: datetime, years: int) -> datetime:
    """The instant before which a care event is outside R-25: ``years`` calendar years back, UTC, whole seconds.

    The expression of ``RetentionService.care_event_anonymisation_cutoff`` (pinned equal by a test), so an event this
    backfill writes is never one the next retention sweep would anonymise.
    """
    now = now.astimezone(UTC)
    return replace_year(now, now.year - years).replace(microsecond=0)


def performed_at_of(document: dict[str, Any], collection: str) -> datetime | None:
    """The instant of ``document`` as an aware UTC datetime; ``None`` when it has none or it is not a date."""
    raw = document.get(TIME_FIELDS[collection])
    if isinstance(raw, datetime):
        value = raw
    elif isinstance(raw, str) and raw.strip():
        try:
            value = datetime.fromisoformat(raw.strip())
        except ValueError:
            return None
    else:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def account_of(document: dict[str, Any], collection: str) -> str | None:
    """The account the source names as the one who recorded it; ``None`` for a source without an account reference."""
    field = ACCOUNT_FIELDS[collection]
    value = document.get(field) if field else None
    return value if isinstance(value, str) and value.strip() else None


def resolve_anchor(row: dict[str, Any], collection: str | None = None) -> BedAnchor | SkipReason:
    """Resolve the bed of a scanned source row, or say why there is none.

    ``row`` is what the migration's scan returns per document::

        {"doc": {...}, "refs": [{"ref", "kind": "plant" | "slot" | None, "location_key", "plant_tenant"}],
         "own_location_key": str | None,
         "locations": [{"key", "found", "site_key", "site_found", "site_tenant"}]}

    The tenant is the bed's site's; the document's own ``tenant_key`` (and the tenant of each plant it names) must
    agree with it — a mismatch is never written (GP-NFR-051: the tenant comes from the owner, not from a stamp).
    """
    refs: list[dict[str, Any]] = list(row.get("refs") or [])
    own_location = row.get("own_location_key")
    if not refs and not own_location:
        return SkipReason.NO_REFERENCE
    unresolved = [ref for ref in refs if not ref["kind"] or not ref["location_key"]]
    if unresolved:
        return SkipReason.PARTLY_UNRESOLVED if len(unresolved) < len(refs) or own_location else SkipReason.UNRESOLVED
    locations: list[dict[str, Any]] = list(row.get("locations") or [])
    if len(locations) > 1:
        return SkipReason.MULTIPLE_BEDS
    if not locations:  # pragma: no cover - a reference with a location always yields a location row
        return SkipReason.UNRESOLVED
    bed = locations[0]
    if not bed.get("found") or not bed.get("site_key") or not bed.get("site_found"):
        return SkipReason.UNRESOLVED
    site_tenant = bed.get("site_tenant")
    if not site_tenant:
        return SkipReason.SITE_WITHOUT_TENANT
    document = row.get("doc") or {}
    if collection == CARE_CONFIRMATIONS and document.get("reminder_type") not in REMINDER_CATEGORIES:
        return SkipReason.UNMAPPED_CATEGORY
    plants = [ref for ref in refs if ref["kind"] == "plant"]
    if collection in UNSTAMPED_SOURCES:
        # No stamp to compare: the plant's tenant is the document's, and it must be the bed's site's.
        if not plants:
            return SkipReason.TENANT_MISMATCH
    elif document.get("tenant_key") != site_tenant:
        return SkipReason.TENANT_MISMATCH
    if any(ref["plant_tenant"] != site_tenant for ref in plants):
        return SkipReason.TENANT_MISMATCH
    return BedAnchor(
        tenant_key=str(site_tenant),
        site_key=str(bed["site_key"]),
        location_key=str(bed["key"]),
        plant_keys=tuple(sorted({str(ref["ref"]) for ref in plants})),
    )


def _quantity(collection: str, document: dict[str, Any]) -> dict[str, Any]:
    """``quantity`` / ``unit`` (and the bed total) as the source states them; nothing is derived or converted."""
    fields: dict[str, Any] = {}
    if collection == WATERING_EVENTS:
        volume = document.get("volume_liters")
        if isinstance(volume, int | float):
            fields = {"quantity": float(volume), "unit": "l"}
    elif collection == FEEDING_EVENTS:
        dose, dose_unit = document.get("dose_quantity"), document.get("dose_unit")
        volume = document.get("volume_applied_liters")
        if isinstance(dose, int | float) and dose_unit in CARE_EVENT_UNITS:
            fields = {"quantity": float(dose), "unit": dose_unit}
        elif isinstance(volume, int | float):
            fields = {"quantity": float(volume), "unit": "l"}
        total, total_unit = document.get("quantity_total"), document.get("quantity_total_unit")
        if fields and isinstance(total, int | float) and total_unit in CARE_EVENT_UNITS:
            fields |= {"quantity_total": float(total), "quantity_total_unit": total_unit}
    elif collection == HARVEST_BATCHES:
        grams = document.get("wet_weight_g")
        if isinstance(grams, int | float):
            fields = {"quantity": float(grams), "unit": "g"}
    # A treatment's ``dosage`` has no unit in the source: a number without a unit is not a quantity (E-10).
    return fields


def map_document(
    collection: str,
    document: dict[str, Any],
    anchor: BedAnchor,
    performed_at: datetime,
    *,
    trigger: str = TRIGGER_BACKFILL,
    performed_by_user_key: str | None = None,
    quantity: float | None = None,
    unit: str | None = None,
) -> CareEvent:
    """The care event that logs ``document`` in ``anchor``'s bed; reads nothing but its arguments.

    The backfill and the consistency job call it with the defaults. The live write of a care confirmation
    (WP 8.3) calls the same function with ``trigger = reminder`` and the caller as ``performed_by_user_key`` (and a
    volume the caller typed): one mapping per source, whoever asks.
    """
    key = document.get("_key") or document.get("key")
    if not key:
        raise ValueError(f"A {collection} document without a key cannot be referenced by source_ref.")
    quantity_fields = _quantity(collection, document)
    if quantity is not None and unit in CARE_EVENT_UNITS:
        quantity_fields = {"quantity": float(quantity), "unit": unit}
    return CareEvent(
        tenant_key=anchor.tenant_key,
        site_key=anchor.site_key,
        location_key=anchor.location_key,
        plant_keys=list(anchor.plant_keys),
        category=_category(collection, document),
        summary=SUMMARIES[collection],
        performed_at=performed_at,
        performed_by_user_key=performed_by_user_key or account_of(document, collection),
        trigger=trigger,
        source_ref={"collection": collection, "key": str(key)},
        **quantity_fields,
    )


def _category(collection: str, document: dict[str, Any]) -> str:
    if collection == CARE_CONFIRMATIONS:
        reminder_type = document.get("reminder_type")
        if reminder_type not in REMINDER_CATEGORIES:
            raise ValueError(f"No care-event category is mapped for the reminder type '{reminder_type}'.")
        return REMINDER_CATEGORIES[str(reminder_type)]
    return CATEGORIES[collection]
