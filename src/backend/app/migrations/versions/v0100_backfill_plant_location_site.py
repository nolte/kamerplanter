"""v0100 — #2499 (REQ-053 WP 3.8 follow-up): backfill ``location_key`` / ``site_key`` on ``plant_instances``.

**What.** ``planting_run_service.create_plants`` wrote ``plant_instances`` documents with ``slot_key`` set but
``location_key`` and ``site_key`` ``null`` until WP 3.8 fixed the writer. Every bed read finds a bed's plants by
``location_key`` (``plant-states``, the bed plan, the ``position_corrected`` plant check), so those plants stay
invisible. This version derives both from the plant's own slot: ``slot.location_key``, then that location's
``site_key``.

**Never guesses.** A field that is already set is never overwritten. A plant is only repaired when the chain
``plant.slot_key → slot.location_key → location.site_key → site`` resolves *and* the site belongs to the plant's
own tenant. Everything else is counted and listed under its reason and left untouched:

- ``no_slot`` — the plant has no ``slot_key`` (a human has to place it);
- ``slot_missing`` — its slot no longer exists;
- ``slot_without_location`` — its slot names no location;
- ``location_missing`` — the location (the slot's, or the plant's own) does not exist;
- ``location_without_site_key`` — the location exists but names no site;
- ``site_missing`` — the location names a site that does not exist;
- ``site_without_tenant`` — the site exists but carries no ``tenant_key`` (legacy data, not foreign data);
- ``cross_tenant`` — the plant has no ``tenant_key``, or the site belongs to another tenant;
- ``site_mismatch`` — the plant has no ``location_key`` but already a ``site_key`` that differs from the site
  derived through its slot; writing the slot's location would leave the two disagreeing.

A plant that already has a ``location_key`` takes ``site_key`` from that own location (same checks), not from its
slot. A plant that has a ``site_key`` but no ``location_key`` only receives the slot's location when its
``site_key`` equals the derived site. Only plants that actually receive a field count as updated.

**Idempotent (M-3).** Only plants with a null ``location_key`` or ``site_key`` match; after a run the repaired
ones no longer do, so a second run matches the same unresolvable remainder and changes nothing.

**Dry run (M-5, prod point P-2).** Full report, nothing written: ``will_update`` and its split, plus the
unresolvable plants per reason, the first :data:`_LISTED` keys each. Operators read
``plant_location_backfill_dry_run`` before the production run; the plants without a slot are the ones a human
has to place, ``site_without_tenant`` names legacy sites to stamp with their tenant before the run.

**Not reversible (M-6).** The values are derived facts; clearing them again would re-hide the plants.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: How many plant keys a report lists per reason before it only counts.
_LISTED = 25

#: Documents per ``UPDATE`` statement.
_BATCH_SIZE = 500

_SCAN = """
FOR p IN @@plants
  FILTER p.location_key == null OR p.site_key == null
  LET slot = p.slot_key == null ? null : DOCUMENT(@slots, p.slot_key)
  LET location = slot == null OR slot.location_key == null ? null : DOCUMENT(@locations, slot.location_key)
  LET own = p.location_key == null ? null : DOCUMENT(@locations, p.location_key)
  LET slot_site = location == null OR location.site_key == null ? null : DOCUMENT(@sites, location.site_key)
  LET own_site = own == null OR own.site_key == null ? null : DOCUMENT(@sites, own.site_key)
  RETURN {
    _key: p._key,
    tenant_key: p.tenant_key,
    location_key: p.location_key,
    site_key: p.site_key,
    slot_key: p.slot_key,
    slot_found: slot != null,
    slot_location_key: slot == null ? null : slot.location_key,
    location_found: location != null,
    location_site_tenant_key: slot_site == null ? null : slot_site.tenant_key,
    location_site_key: location == null ? null : location.site_key,
    location_site_found: slot_site != null,
    own_found: own != null,
    own_site_tenant_key: own_site == null ? null : own_site.tenant_key,
    own_site_key: own == null ? null : own.site_key,
    own_site_found: own_site != null
  }
"""

# The FILTER re-reads both fields: a plant stamped between the scan and this statement is not overwritten.
_APPLY = """
FOR u IN @updates
  LET current = DOCUMENT(@plants_name, u._key)
  FILTER current != null
  UPDATE u._key WITH {
    location_key: current.location_key == null ? u.location_key : current.location_key,
    site_key: current.site_key == null ? u.site_key : current.site_key
  } IN @@plants
"""


def _apply(db: StandardDatabase, updates: Sequence[dict[str, Any]]) -> None:
    for start in range(0, len(updates), _BATCH_SIZE):
        chunk = list(updates[start : start + _BATCH_SIZE])
        db.aql.execute(
            _APPLY, bind_vars={"@plants": col.PLANT_INSTANCES, "plants_name": col.PLANT_INSTANCES, "updates": chunk}
        )


def _reason(row: dict[str, Any]) -> str | None:
    """Why the plant cannot be repaired (``None`` = it can).

    A plant that already has a ``location_key`` takes its site from that very location, never from the slot's:
    the two may disagree and a plant must not end up in one location and another location's site. A plant that
    already has a ``site_key`` only takes the slot's location when that location's site is the same one.
    """
    if row.get("location_key") is not None:
        if not row["own_found"]:
            return "location_missing"
        return _site_reason(
            row,
            site_key=row.get("own_site_key"),
            site_found=bool(row.get("own_site_found")),
            site_tenant=row.get("own_site_tenant_key"),
        )
    if not row.get("slot_key"):
        return "no_slot"
    if not row["slot_found"]:
        return "slot_missing"
    if not row.get("slot_location_key"):
        return "slot_without_location"
    if not row["location_found"]:
        return "location_missing"
    reason = _site_reason(
        row,
        site_key=row.get("location_site_key"),
        site_found=bool(row.get("location_site_found")),
        site_tenant=row.get("location_site_tenant_key"),
    )
    if reason is None and row.get("site_key") is not None and row["site_key"] != row.get("location_site_key"):
        return "site_mismatch"
    return reason


def _site_reason(row: dict[str, Any], *, site_key: str | None, site_found: bool, site_tenant: str | None) -> str | None:
    """Resolve the site anchoring the location and check it belongs to the plant's tenant (#1397).

    ``Location.tenant_key`` / ``Slot.tenant_key`` are never filled by the write path, so the tenant is the
    anchoring site's. Each broken link of the chain has its own reason, so the dry run tells legacy data (a site
    without a tenant) apart from really foreign data (a site of another tenant).
    """
    if not site_key:
        return "location_without_site_key"
    if not site_found:
        return "site_missing"
    plant_tenant = row.get("tenant_key")
    if not plant_tenant:
        return "cross_tenant"
    if not site_tenant:
        return "site_without_tenant"
    if site_tenant != plant_tenant:
        return "cross_tenant"
    return None


def _plan(db: StandardDatabase) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    cursor = cast(
        Cursor,
        db.aql.execute(
            _SCAN,
            bind_vars={
                "@plants": col.PLANT_INSTANCES,
                "slots": col.SLOTS,
                "locations": col.LOCATIONS,
                "sites": col.SITES,
            },
        ),
    )
    rows: list[dict[str, Any]] = list(cursor)
    updates: list[dict[str, Any]] = []
    unresolved: dict[str, dict[str, Any]] = {}
    sets_location = 0
    sets_site = 0
    for row in rows:
        reason = _reason(row)
        if reason is not None:
            bucket = unresolved.setdefault(reason, {"count": 0, "listed": []})
            bucket["count"] += 1
            if len(bucket["listed"]) < _LISTED:
                bucket["listed"].append(str(row["_key"]))
            continue
        # A resolved row always carries both: the slot's (or own) location and that location's existing site.
        has_location = row["location_key"] is not None
        update: dict[str, Any] = {"_key": row["_key"], "location_key": None, "site_key": None}
        if not has_location:
            sets_location += 1
            update["location_key"] = row["slot_location_key"]
        if row["site_key"] is None:
            sets_site += 1
            update["site_key"] = row["own_site_key" if has_location else "location_site_key"]
        updates.append(update)
    details: dict[str, Any] = {
        "scanned_missing_location_or_site": len(rows),
        "sets_location_key": sets_location,
        "sets_site_key": sets_site,
        "listed_keys": [str(u["_key"]) for u in updates[:_LISTED]],
        "unresolved": unresolved,
        "unresolved_count": sum(b["count"] for b in unresolved.values()),
    }
    return updates, details, len(rows)


class BackfillPlantLocationSiteMigration(Migration):
    version = "0100"
    name = "backfill_plant_location_site"
    description = (
        "#2499: derive location_key and site_key of plants written by create_plants before the WP 3.8 fix "
        "from plant.slot_key -> slot.location_key -> location.site_key; never overwrites, same-tenant only, "
        "plants without a resolvable slot are listed in the dry run."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.PLANT_INSTANCES):
            return MigrationReport(
                version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run, details={}
            )
        updates, details, scanned = _plan(db)
        details["will_update" if dry_run else "updated"] = len(updates)
        if dry_run:
            logger.info("plant_location_backfill_dry_run", pending_changes=len(updates), details=details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )
        _apply(db, updates)
        logger.info("plant_location_backfill_applied", changed=len(updates), details=details)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=len(updates), dry_run=False, details=details
        )


migration = BackfillPlantLocationSiteMigration()
