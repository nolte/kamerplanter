"""The one scan of the domain-event collections for care events they have not got yet (REQ-053 GP-FR-105; WP 8.1/8.2).

Shared by the M4 backfill migration (``v0104``, every document inside the R-25 window) and the daily
``care_events_consistency`` job (WP 8.2, the last N days), so there is one resolution of ``plant / slot -> location ->
site -> tenant`` and one "already logged" test (the unique-sparse ``source_ref`` index), whichever of the two asks.
It reads and returns rows; the rules that turn a row into a care event (or into a reason it is not one) are the pure
:mod:`app.domain.engines.care_event_backfill_mapper`.
"""

from __future__ import annotations

from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.engines.care_event_backfill_mapper import TIME_FIELDS, action_filter

#: The documents inside the window with everything the mapper needs: every reference resolved to its location, every
#: location to its site and the site's tenant (``site_tenant_active``: ``false`` for a stored tenant that is not
#: ``active``, ``null`` when no tenant document is found — the callers' own gate decides that case), and whether a
#: line for the document exists already. The references of
#: the four shapes: ``plant_key`` (feeding, treatment, harvest), ``plant_keys`` (feeding, watering alias) and
#: ``slot_keys`` (watering). A key is a plant when a plant has it, otherwise a slot.
SCAN_AQL = """
FOR d IN @@source
  FILTER @action == null OR d.action == @action
  LET ts = DATE_TIMESTAMP(d[@time_field])
  FILTER ts != null AND ts >= @cutoff_ms
  SORT d._key
  LET refs = (
    FOR r IN UNIQUE(FLATTEN([[d.plant_key], d.plant_keys || [], d.slot_keys || []]))
      FILTER r != null AND r != ""
      LET p = DOCUMENT(@plants, r)
      LET s = p == null ? DOCUMENT(@slots, r) : null
      LET plant_slot = p != null AND p.location_key == null AND p.slot_key != null ? DOCUMENT(@slots, p.slot_key) : null
      LET location_key = p != null
        ? (p.location_key != null ? p.location_key : (plant_slot == null ? null : plant_slot.location_key))
        : (s == null ? null : s.location_key)
      RETURN {
        ref: r,
        kind: p != null ? "plant" : (s != null ? "slot" : null),
        location_key: location_key == "" ? null : location_key,
        plant_tenant: p == null ? null : p.tenant_key
      }
  )
  LET own_location_key = d.location_key == null OR d.location_key == "" ? null : d.location_key
  LET location_keys = UNIQUE(APPEND(
    (FOR r IN refs FILTER r.location_key != null RETURN r.location_key),
    own_location_key == null ? [] : [own_location_key]
  ))
  LET locations = (
    FOR lk IN location_keys
      LET l = DOCUMENT(@locations, lk)
      LET site = l == null OR l.site_key == null OR l.site_key == "" ? null : DOCUMENT(@sites, l.site_key)
      LET tenant = site == null OR site.tenant_key == null ? null : DOCUMENT(@tenants, site.tenant_key)
      RETURN {
        key: lk,
        found: l != null,
        site_key: l == null ? null : l.site_key,
        site_found: site != null,
        site_tenant: site == null ? null : site.tenant_key,
        site_tenant_active: tenant == null
          ? null
          : (tenant.status == "active" OR (tenant.status == null AND tenant.is_active != false))
      }
  )
  LET document_tenant = d.tenant_key != null
    ? d.tenant_key
    : FIRST(FOR r IN refs FILTER r.plant_tenant != null RETURN r.plant_tenant)
  LET present = FIRST(
    FOR e IN @@events
      FILTER e.tenant_key == document_tenant AND e.source_ref.collection == @source AND e.source_ref.key == d._key
      LIMIT 1
      RETURN 1
  ) != null
  RETURN { doc: d, refs, own_location_key, locations, present }
"""


def scan_candidates(
    db: StandardDatabase, source: str, cutoff_ms: int, *, batch_size: int = 200, ttl_seconds: int = 600
) -> Cursor:
    """The documents of ``source`` at or after ``cutoff_ms`` (epoch ms), sorted by key, each with its resolved refs.

    A sorted non-streaming cursor: the server fixes its result before the first batch, so writes applied while the
    cursor is read never change which rows it yields.
    """
    bind_vars: dict[str, Any] = {
        "@source": source,
        "@events": col.CARE_EVENTS,
        "source": source,
        "time_field": TIME_FIELDS[source],
        "action": action_filter(source),
        "cutoff_ms": cutoff_ms,
        "plants": col.PLANT_INSTANCES,
        "slots": col.SLOTS,
        "locations": col.LOCATIONS,
        "sites": col.SITES,
        "tenants": col.TENANTS,
    }
    return cast(
        Cursor,
        db.aql.execute(SCAN_AQL, bind_vars=bind_vars, batch_size=batch_size, ttl=cast(Any, ttl_seconds), stream=False),
    )
