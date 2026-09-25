#!/usr/bin/env python3
"""Seed a tenant, and a control tenant, into every collection of the tenant-erasure inventory (#1769).

Runs **inside the backend container** of the reach stack (``stack.py
seed-tenant`` ships it there with ``seed_privacy_subject.py``, whose model-valid
row builder it reuses) and prints one JSON record to stdout. It is an
environment step: it asserts nothing about reach.

What gets a row
---------------
For both the tenant under test and a control tenant, one model-valid row per
entry of ``TenantErasureEngine.INVENTORY`` — the list the executing path reads,
never a copy:

* an entry without a parent carries its tenant field (``tenant_key``, or
  ``tenant_scope`` on an API key) = the tenant;
* an entry with parents is reached **only** through its first parent: the
  foreign key names the tenant's parent row and ``tenant_key`` (where the model
  has one) keeps its empty default, never the tenant (the ``locations``/``slots``
  shape of #1397);
* the deletion-record collection is skipped: its row is the act's proof;
* an ``pseudonymize`` entry's account-key fields (read off the account erasure's
  tombstone rules, as the engine does) hold the member's key, and their free-text
  companions a marker.

Then one edge per named-graph edge definition whose ``_from`` side can hold a
seeded row of the tenant, pointing at a seeded row of the same tenant on the
``_to`` side when one exists — so the sweep has edges between tenant rows,
from retained rows to deleted ones, and the control tenant has the same.

A row stamped with the tenant in a collection nobody declared is **not** seeded:
that would make the probe measure a failure it constructs itself.

``--personal-of <subject>`` (#1788) makes the tenant under test the subject's
**personal** tenant instead of an organisation: owned by the subject (an account
``reach:seed:privacy-subject`` wrote), the inventory's membership row the
subject's own and its only active one, the retention rows carrying the subject's
key. The control tenant keeps a member of its own, so an account erasure of the
subject has no business changing it. The act is then the subject's account
erasure, not a tenant deletion.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seed_privacy_subject import SeedError, Seeder  # noqa: E402 — shipped beside this file

from app.config.settings import settings  # noqa: E402
from app.data_access.arango import collections as col  # noqa: E402
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine  # noqa: E402
from arango import ArangoClient  # noqa: E402


#: Values a model validator demands that a marker cannot supply, per collection.
#: Only the shape, never the list of collections: those come off the inventory.
SHAPE_OVERRIDES: dict[str, Any] = {
    "slots": lambda: {"slot_id": f"REACH{secrets.token_hex(3).upper()}_A1"},
    "actuators": lambda: {"protocol": "manual"},
    "calendar_feeds": lambda: {"token": secrets.token_hex(16)},
    "control_rules": lambda: {
        "condition": {"operator": "gt", "threshold": 30.0},
        "hysteresis": {"on_threshold": 30.0, "off_threshold": 28.0},
    },
    "control_schedules": lambda: {"entries": [{"time_on": "06:00", "time_off": "18:00"}]},
    "maintenance_schedules": lambda: {"interval_days": 14, "reminder_days_before": 3},
    "phase_control_profiles": lambda: {
        "target_photoperiod_hours": 18.0,
        "target_light_ppfd": 600,
        "target_temperature_day_c": 24.0,
        "target_temperature_night_c": 20.0,
        "target_humidity_day_percent": 60,
        "target_humidity_night_percent": 55,
    },
    # Reached through its tank only: the other two parent slots stay empty.
    "sensors": lambda: {"site_key": None, "location_key": None},
    "species": lambda: {"scientific_name": f"Reachia seed{secrets.token_hex(3)}"},
    "watering_logs": lambda: {"plant_keys": [f"reach-plant-{secrets.token_hex(3)}"]},
}


def _seed_one(seeder: Seeder, tenant: str, member: str, role: str, *, personal: bool = False) -> None:
    plan = TenantErasureEngine().build_plan(tenant)
    rules = {rule.collection: rule for rule in plan.pseudonymizations}
    seeder.document(
        plan.tenant_collection,
        {"slug": tenant, "owner_user_key": member, "tenant_type": "personal" if personal else "organization"},
        role=f"{role}:tenant",
        key=tenant,
    )
    own: dict[str, str] = {}
    for entry in plan.entries:
        if entry.collection == TenantErasureEngine.RECORD_COLLECTION:
            # The deletion's own proof, written by the act — seeding one would
            # put a record the act did not write in front of the records observer.
            continue
        overrides: dict[str, Any] = dict(SHAPE_OVERRIDES.get(entry.collection, dict)())
        if entry.parents:
            parent = entry.parents[0]
            overrides[parent.field] = own[parent.collection]
            overrides.update(parent.where)
            # The shape production writes: a parent-chained row's own tenant
            # field is never filled (#1397) and keeps the model default. A marker
            # here would be a value no write path produces — and one the executor
            # rightly treats as another tenant's row (#1769 review SEC-004).
            overrides["tenant_key"] = ""
        else:
            overrides[entry.tenant_field] = tenant
        rule = rules.get(entry.collection)
        if rule is not None:
            overrides[rule.user_field] = member
        if personal and entry.collection == col.MEMBERSHIPS:
            # The owner's own membership, and the only active one (#1788).
            overrides.update({"user_key": member, "is_active": True})
        row = seeder.document(entry.collection, overrides, role=f"{role}:{entry.action}")
        own[entry.collection] = row["key"]

    rows = {row["collection"]: row for row in seeder.rows if row["role"].startswith(f"{role}:")}
    for definition in col.GRAPH_EDGE_DEFINITIONS:
        source = next((rows[name] for name in definition["from_vertex_collections"] if name in rows), None)
        if source is None:
            continue
        target = next((rows[name]["id"] for name in definition["to_vertex_collections"] if name in rows), None)
        target = target or f"{definition['to_vertex_collections'][0]}/reach-target-{secrets.token_hex(4)}"
        edge = {"_key": seeder.new_key(), "_from": source["id"], "_to": target}
        seeder._insert(definition["edge_collection"], edge, kind="edge", role=f"{role}:edge", edge=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--control", required=True)
    parser.add_argument(
        "--personal-of",
        default=None,
        help="seed the tenant as this (already seeded) account's personal tenant, it the only member (#1788)",
    )
    args = parser.parse_args(argv)

    client = ArangoClient(hosts=f"http://{settings.arangodb_host}:{settings.arangodb_port}")
    database = client.db(
        settings.arangodb_database,
        username=settings.arangodb_username,
        password=settings.arangodb_password,
    )
    for tenant in (args.tenant, args.control):
        if database.collection(TenantErasureEngine.TENANT_COLLECTION).has(tenant):
            print(f"seed: tenant '{tenant}' already exists; tear the stack down first", file=sys.stderr)
            return 1
    if args.personal_of is not None and not database.collection(col.USERS).has(args.personal_of):
        print(
            f"seed: account '{args.personal_of}' does not exist; run reach:seed:privacy-subject first", file=sys.stderr
        )
        return 1
    member = args.personal_of or f"reach-member-{secrets.token_hex(4)}"
    control_member = f"reach-member-{secrets.token_hex(4)}" if args.personal_of else member
    seeder = Seeder(database, member)
    try:
        _seed_one(seeder, args.tenant, member, "tenant", personal=args.personal_of is not None)
        _seed_one(seeder, args.control, control_member, "control")
    except SeedError as exc:
        print(f"seed: {exc}", file=sys.stderr)
        return 1
    record = {"tenant": args.tenant, "control": args.control, "member": member, "rows": seeder.rows}
    json.dump(record, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
