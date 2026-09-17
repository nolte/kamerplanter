#!/usr/bin/env python
"""Read-only audit of plants that have no ``CareProfile`` (#1444).

**Reads only**, and it connects that way too: it opens the configured database
directly rather than through ``ArangoConnection``, whose ``connect()`` calls
``sys_db.create_database(...)`` when the database is absent. An audit that can
create its own empty target is an audit that reports "no plant is missing a care
profile" about a database it has just made. Same reasoning, same shape, as
``audit_oauth_links.py``.

## Why this exists

``CareReminderService.get_or_create_profile`` is the only thing that creates a
``CareProfile``. Until PR #1440 two **read** paths called it and therefore
persisted on a plain ``GET`` — the profile endpoint, and the tenant care dashboard
for *every* unprofiled plant of the tenant at once. That was a viewer-writable
surface (#1422) and had to go; PR #1440 replaced it with a bootstrap on the
creation paths.

The bootstrap covers plants created **from then on**. A plant created earlier, in
a tenant where nobody ever opened the care dashboard, can still have no profile —
and the nightly generator iterates **stored profiles**, so such a plant is not
"skipped" by it, it is absent from the iteration entirely. No counter in that task
is reached by it and nothing in its log says so.

Whether that population is large, small or empty has never been measured. This
script measures it. It proposes nothing and writes nothing.

## What it counts

Non-removed ``plant_instances`` with no ``care_profiles`` document whose
``plant_key`` names them, grouped by the plant's own ``tenant_key``. The predicate
is imported from ``app.data_access.arango.care_reminder_repository`` rather than
spelled out here, so this audit, the nightly warning in ``care_tasks.py`` and the
later backfill migration select the SAME population. A second copy of the FILTER
is a second answer to "how many plants are affected".

**Through the ``plant_key`` field, not the ``has_care_profile`` edge.** Both are
written together, but only the field is ever read back (``get_profile_by_plant_key``
→ ``find_one_by_field("plant_key", …)``, and the generator reads
``profile.plant_key``). A count taken through the edge would answer a question
nothing acts on.

## For the migration that may follow

``expected_profiles_to_create`` in the JSON is exactly the number of rows the
backfill has to write, and re-running this script afterwards is its positive
control: the figure must be **0**, with ``plants_active`` unchanged. A backfill
that leaves it non-zero wrote profiles for a different population than the one
audited here.

## Exit codes

* ``0`` — every non-removed plant has a care profile.
* ``3`` — plants without a profile were found. Distinct from ``0`` so
  ``audit_care_profiles.py && echo clean`` cannot print ``clean`` over a listing.
* ``1`` — the audit could not run (database unreachable, or a collection that is
  created at bootstrap is missing, which means the target is uninitialised rather
  than empty). Never a zero, because "nothing found" and "nothing read" must not
  share an exit code.
* ``2`` — bad arguments.

## Usage

    python scripts/audit_care_profiles.py
    python scripts/audit_care_profiles.py --json | jq .expected_profiles_to_create
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from arango.exceptions import ArangoError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: How many individual plant keys the readable report lists before it caps. The
#: JSON carries the same capped sample — the COUNTS are never capped, which is the
#: distinction that matters: an operator acts on the count and spot-checks the keys.
KEY_LISTING_LIMIT = 50

#: Exit code for "the audit ran and found plants without a profile". See the module
#: docstring: 0 means nothing found, 1 means the audit could not run.
EXIT_FINDINGS = 3

#: The stored sentinel for a plant that belongs to no tenant. Such a plant is
#: invisible to every tenant-scoped generator run (``generate_due_care_reminders``
#: compares ``plant.tenant_key != tenant_key``), so it is reported under its own
#: label rather than folded into the other rows.
TENANTLESS = ""


def label_for(tenant_key: str, names: dict[str, str]) -> str:
    """How a tenant row is named in the readable report.

    The tenantless row is spelled out rather than shown as an empty column: it is
    the row an operator is most likely to misread as a formatting glitch, and it is
    the one no tenant-scoped run will ever process.
    """
    if tenant_key == TENANTLESS:
        return "(no tenant — invisible to every tenant-scoped run)"
    name = names.get(tenant_key)
    return f"{tenant_key} ({name})" if name else tenant_key


def build_report(
    by_tenant: list[dict],
    *,
    plants_total: int,
    plants_active: int,
    profiles_total: int,
    orphan_profiles: int,
    sample: list[dict],
    tenant_names: dict[str, str],
) -> dict:
    """Assemble the machine-readable report from the raw query results.

    Pure, so the arithmetic and the labelling can be pinned without a database.

    ``missing_total`` is summed from the per-tenant rows rather than read from a
    separate count query: two queries can disagree, and if they ever did, the
    number an operator reads and the number the migration writes would be the two
    that disagreed.
    """
    missing_total = sum(int(row["missing"]) for row in by_tenant)
    tenants = [
        {
            "tenant_key": row["tenant_key"],
            "tenant_name": tenant_names.get(row["tenant_key"]),
            "missing": int(row["missing"]),
        }
        for row in by_tenant
    ]
    return {
        "plants_total": plants_total,
        "plants_active": plants_active,
        "plants_removed": plants_total - plants_active,
        "care_profiles_total": profiles_total,
        "orphan_profiles": orphan_profiles,
        "missing_total": missing_total,
        "tenants_affected": len(tenants),
        "by_tenant": tenants,
        # The migration's precondition and its positive control in one field: it
        # writes exactly this many profiles, and a re-run afterwards must report 0.
        "expected_profiles_to_create": missing_total,
        "sample_keys": sample[:KEY_LISTING_LIMIT],
        "sample_truncated": len(sample) > KEY_LISTING_LIMIT or missing_total > len(sample),
    }


def render(report: dict, tenant_names: dict[str, str]) -> list[str]:
    """The readable summary, as lines. Returned rather than printed so a test can
    read what an operator reads — asserting on captured stdout would pin the
    printing, not the wording."""
    lines = [
        f"plants stored:                   {report['plants_total']}",
        f"  non-removed (in scope):        {report['plants_active']}",
        f"  removed (out of scope):        {report['plants_removed']}",
        f"care profiles stored:            {report['care_profiles_total']}",
        f"  without a live plant:          {report['orphan_profiles']}  (counted as 'skipped' by the nightly run)",
        "",
        f"plants WITHOUT a care profile:   {report['missing_total']}  in {report['tenants_affected']} tenant(s)",
    ]
    if report["missing_total"] == 0:
        lines += [
            "",
            "Every non-removed plant has a care profile. The nightly generator can see",
            "all of them, so no backfill is warranted on this installation.",
        ]
        return lines

    lines.append("")
    for row in report["by_tenant"]:
        lines.append(f"    {row['missing']:>6}  {label_for(row['tenant_key'], tenant_names)}")
    lines += [
        "",
        "These plants receive NO REQ-022 reminder and are invisible to the nightly",
        "generator: it iterates stored profiles, so they are not counted as 'skipped'",
        "either — they are absent from the run entirely.",
        "",
        f"A backfill would create exactly {report['expected_profiles_to_create']} profile(s). Re-running this",
        "audit after it must report 0, with 'non-removed (in scope)' unchanged.",
    ]
    if report["sample_keys"]:
        lines += ["", "sample (for a manual look):"]
        for plant in report["sample_keys"]:
            lines.append(
                f"    {plant['key']}  tenant={plant.get('tenant_key') or '-'}  "
                f"id={plant.get('instance_id') or '-'}  "
                f"name={plant.get('plant_name') or '-'}  "
                f"planted={plant.get('planted_on') or 'no date'}"
            )
        if report["sample_truncated"]:
            lines.append(f"    … listing caps at {KEY_LISTING_LIMIT}; the COUNTS above are complete.")
    return lines


def _unreachable(settings, exc: Exception) -> str:
    return (
        f"cannot read database {settings.arangodb_database!r} at "
        f"{settings.arangodb_host}:{settings.arangodb_port}: {exc}\n"
        f"Check ARANGODB_DATABASE / host / port / credentials. This script does not "
        f"create anything."
    )


def _uninitialised(collection: str, database: str) -> str:
    return (
        f"{collection} does not exist in {database!r}. That collection is created at "
        f"bootstrap, so this is an uninitialised database rather than an empty one — "
        f"check ARANGODB_DATABASE. Refusing to report zero over a collection that was "
        f"never read."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of plants without a CareProfile (#1444).")
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable report only (the exit code is unchanged)",
    )
    args = parser.parse_args()

    from arango import ArangoClient

    from app.config.settings import settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.care_reminder_repository import (
        unprofiled_plant_keys_aql,
        unprofiled_plants_by_tenant_aql,
    )

    # NOT `ArangoConnection`: its `connect()` creates the database when absent, so a
    # mistyped ARANGODB_DATABASE would leave this script reporting an all-clear about
    # an empty database it had just created.
    client = ArangoClient(hosts=f"http://{settings.arangodb_host}:{settings.arangodb_port}")
    db = client.db(
        settings.arangodb_database,
        username=settings.arangodb_username,
        password=settings.arangodb_password,
    )

    try:
        # OSError as well as ArangoError: when every configured host fails,
        # python-arango raises the built-in `ConnectionAbortedError`, an OSError
        # subclass that is not an ArangoError — a mistyped host or port would
        # otherwise produce a raw traceback instead of this message.
        present = {name: db.has_collection(name) for name in (col.PLANT_INSTANCES, col.CARE_PROFILES, col.TENANTS)}
    except (ArangoError, OSError) as exc:
        print(_unreachable(settings, exc), file=sys.stderr)
        return 1

    for name, exists in present.items():
        if not exists:
            # All three are in DOCUMENT_COLLECTIONS and created unconditionally at
            # bootstrap, so an absence cannot mean "nothing has been created yet".
            print(_uninitialised(name, settings.arangodb_database), file=sys.stderr)
            return 1

    totals_query = f"""
    LET plants_total = LENGTH(FOR p IN {col.PLANT_INSTANCES} RETURN 1)
    LET plants_active = LENGTH(FOR p IN {col.PLANT_INSTANCES} FILTER p.removed_on == null RETURN 1)
    LET profiles_total = LENGTH(FOR c IN {col.CARE_PROFILES} RETURN 1)
    LET orphan_profiles = LENGTH(
      FOR c IN {col.CARE_PROFILES}
        LET plant = DOCUMENT(CONCAT('{col.PLANT_INSTANCES}/', c.plant_key))
        FILTER plant == null OR plant.removed_on != null
        RETURN 1
    )
    RETURN {{
      plants_total: plants_total,
      plants_active: plants_active,
      profiles_total: profiles_total,
      orphan_profiles: orphan_profiles
    }}
    """
    bind_collections = {"@plants": col.PLANT_INSTANCES, "@profiles": col.CARE_PROFILES}

    try:
        totals = next(iter(db.aql.execute(totals_query)), None) or {}
        by_tenant = list(db.aql.execute(unprofiled_plants_by_tenant_aql(), bind_vars=dict(bind_collections)))
        sample = list(
            db.aql.execute(
                unprofiled_plant_keys_aql(),
                bind_vars={**bind_collections, "limit": KEY_LISTING_LIMIT},
            )
        )
        tenant_names = {
            row["key"]: row["name"]
            for row in db.aql.execute(f"FOR t IN {col.TENANTS} RETURN {{key: t._key, name: t.name}}")
        }
    except (ArangoError, OSError) as exc:
        print(_unreachable(settings, exc), file=sys.stderr)
        return 1

    report = build_report(
        by_tenant,
        plants_total=int(totals.get("plants_total", 0)),
        plants_active=int(totals.get("plants_active", 0)),
        profiles_total=int(totals.get("profiles_total", 0)),
        orphan_profiles=int(totals.get("orphan_profiles", 0)),
        sample=sample,
        tenant_names=tenant_names,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        for line in render(report, tenant_names):
            print(line)
        print()
        print("--- JSON ---")
        print(json.dumps(report, indent=2, sort_keys=True, default=str))

    if report["missing_total"]:
        if not args.json:
            print()
            print(
                f"Exit {EXIT_FINDINGS}: plants without a care profile were found. This audit "
                f"writes nothing — creating the profiles is the #1444 backfill migration's job."
            )
        return EXIT_FINDINGS
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
