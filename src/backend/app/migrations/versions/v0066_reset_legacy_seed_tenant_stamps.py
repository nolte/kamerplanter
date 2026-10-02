"""v0066 — reset the v0004 default-tenant stamp on global seed rows (#1805).

Migration ``v0004`` (``backfill_tenant_key.py``) stamped every row of the hybrid
catalogues whose ``tenant_key`` was empty with the key of a *default tenant* —
including the **global seed rows** that existed then. The cutovers of ``species``
(``v0036``) and ``cultivars`` (``v0038``) reset those stamps; the four remaining
catalogues never got one. Since tenant deletion (#1769) removes a tenant's rows,
a legacy volume would lose seeds with the default tenant.

What measuring a real ArangoDB showed (``tests/integration/test_v0066_*``)
-------------------------------------------------------------------------
Booting the current seed loaders over a volume stamped by the real
``backfill_tenant_key`` resets ``fertilizers``, ``nutrient_plans``,
``workflow_templates`` and ``task_templates`` on their own: each loader finds its
row by name across all tenants and rewrites it from a model whose
``tenant_key`` is ``""``. What no loader touches are the **children** the stamp
reached through ``CHILD_PROPAGATION`` — every ``nutrient_plan_phase_entries``
row of a seed plan stayed stamped (its model has no ``tenant_key``, so the update
merges and leaves the stamp). Tenant deletion selects phase entries by their own
``tenant_key``, so the default tenant's deletion stripped each seed plan of its
entries. This migration resets those children, and the four parents too, so the
reset does not hinge on a seed job having succeeded: a failed non-fatal seed
leaves the stamps until it is fixed.

Seed identity — conservative, and no wider than the loaders'
------------------------------------------------------------
A row is reset only when it carries a non-empty ``tenant_key`` **and** is named
by the shipped seed YAML, by the same key its loader matches on:

* ``fertilizers`` — ``(product_name, brand)``;
* ``nutrient_plans`` — ``name``; ``nutrient_plan_phase_entries`` — their plan is one;
* ``workflow_templates`` — ``name``; ``task_templates`` — ``(workflow name, name)``.

A name alone is not enough, because a tenant may have given its own plan a
seed's name. ``v0004`` stamped *one* tenant onto the seed rows, so the stamp is
proven by one of two facts (see ``_proven_stamps``): a child that carries it under
a *global* parent, or it being the key of more than half of all seed-named rows.
A seed-named row of any other tenant is left alone, and when no stamp is proven
nothing is reset. A volume whose parents the loaders already reset (the usual
state of a deployed volume) still yields the stamp from the entries left behind.

A row the YAML does not name — anything a tenant created, or a seed since
renamed or dropped — is left alone: resetting it would turn a tenant's own data
global, which is worse than leaving a stamp. A stamp on such a row is not
provable as a stamp, so it is not repaired. The loaders themselves claim a
same-named row of any tenant on the next boot, so this goes no further than they
already do.

Idempotency (M-3) — keyed on the stamp. A reset row has ``tenant_key == ""`` and
is skipped, so a re-run writes nothing. Dry-run (M-5) counts the plan and writes
nothing. Irreversible (M-6): the stamped default-tenant key is not recoverable,
and no one wants it back.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

_FERTILIZER_FILES = ("fertilizers.yaml", "plagron.yaml", "gardol.yaml")
_PLAN_FILES = (*_FERTILIZER_FILES, "nutrient_plans_outdoor.yaml", "nutrient_plans_ro.yaml")
_WORKFLOW_FILE = "workflows.yaml"
#: ``NUL`` cannot occur in a name, so a joined pair is unambiguous.
_SEP = "\x00"


@dataclass(frozen=True)
class SeedIdentities:
    """The names the shipped seed YAML gives its rows, by the key each loader matches on."""

    fertilizers: frozenset[tuple[str, str]]
    nutrient_plans: frozenset[str]
    workflow_templates: frozenset[str]
    task_templates: frozenset[tuple[str, str]]


def seed_identities() -> SeedIdentities:
    """Read the identities off the seed YAML (the loaders' own input, not a copy of it)."""
    fertilizers: set[tuple[str, str]] = set()
    for name in _FERTILIZER_FILES:
        fertilizers.update((f["product_name"], f["brand"]) for f in load_yaml(name).get("fertilizers", []))
    plans: set[str] = set()
    for name in _PLAN_FILES:
        plans.update(p["name"] for p in load_yaml(name).get("nutrient_plans", []))
    workflows = load_yaml(_WORKFLOW_FILE)
    return SeedIdentities(
        fertilizers=frozenset(fertilizers),
        nutrient_plans=frozenset(plans),
        workflow_templates=frozenset(w["name"] for w in workflows.get("workflow_templates", [])),
        task_templates=frozenset((t["workflow_name"], t["name"]) for t in workflows.get("task_templates", [])),
    )


#: The count an operator runs on a restored backup (never on production) before deploying.
#: ``stamped_by_tenant`` is per collection: the key that dominates the seed rows is the
#: ``v0004`` default tenant; ``entries_under_global_plan`` is the provable part by itself.
OPERATOR_COUNT_QUERY = """
RETURN {
  entries_under_global_plan: LENGTH(
    FOR d IN nutrient_plan_phase_entries
      FILTER d.tenant_key != null AND d.tenant_key != ""
      LET p = DOCUMENT(CONCAT("nutrient_plans/", d.plan_key))
      FILTER p != null AND (p.tenant_key == null OR p.tenant_key == "")
      RETURN 1),
  fertilizers_stamped_by_tenant: (FOR d IN fertilizers FILTER d.tenant_key != null AND d.tenant_key != ""
    COLLECT t = d.tenant_key WITH COUNT INTO n RETURN {tenant_key: t, rows: n}),
  nutrient_plans_stamped_by_tenant: (FOR d IN nutrient_plans FILTER d.tenant_key != null AND d.tenant_key != ""
    COLLECT t = d.tenant_key WITH COUNT INTO n RETURN {tenant_key: t, rows: n}),
  workflow_templates_stamped_by_tenant: (FOR d IN workflow_templates FILTER d.tenant_key != null AND d.tenant_key != ""
    COLLECT t = d.tenant_key WITH COUNT INTO n RETURN {tenant_key: t, rows: n}),
  task_templates_stamped_by_tenant: (FOR d IN task_templates FILTER d.tenant_key != null AND d.tenant_key != ""
    COLLECT t = d.tenant_key WITH COUNT INTO n RETURN {tenant_key: t, rows: n})
}
"""

#: One row per seed-named row, stamped or not: ``{collection, key, tenant_key[, parent_tenant_key]}``.
type Candidate = dict[str, str]

_QUERIES: dict[str, str] = {
    col.FERTILIZERS: (
        f"FOR d IN @@collection FILTER CONCAT(d.product_name, '{_SEP}', d.brand) IN @fertilizers "
        "RETURN {key: d._key, tenant_key: d.tenant_key || ''}"
    ),
    col.NUTRIENT_PLANS: (
        "FOR d IN @@collection FILTER d.name IN @plans RETURN {key: d._key, tenant_key: d.tenant_key || ''}"
    ),
    col.NUTRIENT_PLAN_PHASE_ENTRIES: (
        "FOR d IN @@collection "
        "LET p = DOCUMENT(CONCAT(@plan_collection, '/', d.plan_key)) "
        "FILTER p != null AND p.name IN @plans "
        "RETURN {key: d._key, tenant_key: d.tenant_key || '', parent_tenant_key: p.tenant_key || ''}"
    ),
    col.WORKFLOW_TEMPLATES: (
        "FOR d IN @@collection FILTER d.name IN @workflows RETURN {key: d._key, tenant_key: d.tenant_key || ''}"
    ),
    col.TASK_TEMPLATES: (
        "FOR d IN @@collection "
        "LET w = DOCUMENT(CONCAT(@workflow_collection, '/', d.workflow_template_key)) "
        f"FILTER w != null AND CONCAT(w.name, '{_SEP}', d.name) IN @task_templates "
        "RETURN {key: d._key, tenant_key: d.tenant_key || '', parent_tenant_key: w.tenant_key || ''}"
    ),
}


class ResetLegacySeedTenantStampsMigration(Migration):
    version = "0066"
    name = "reset_legacy_seed_tenant_stamps"
    description = (
        "Reset the v0004 default-tenant tenant_key on seed fertilizers, nutrient plans (and their phase entries), "
        "workflow templates and task templates to global '' so tenant deletion keeps them (#1805)."
    )
    reversible = False

    @staticmethod
    def _candidates(db: StandardDatabase) -> list[Candidate]:
        """Every row the seed YAML names, per collection, with its ``tenant_key`` (read-only)."""
        ids = seed_identities()
        bind: dict[str, Any] = {
            "fertilizers": [f"{name}{_SEP}{brand}" for name, brand in sorted(ids.fertilizers)],
            "plans": sorted(ids.nutrient_plans),
            "workflows": sorted(ids.workflow_templates),
            "task_templates": [f"{wf}{_SEP}{name}" for wf, name in sorted(ids.task_templates)],
            "plan_collection": col.NUTRIENT_PLANS,
            "workflow_collection": col.WORKFLOW_TEMPLATES,
        }
        found: list[Candidate] = []
        for collection, query in _QUERIES.items():
            if not db.has_collection(collection):
                continue
            wanted = {name: value for name, value in bind.items() if f"@{name}" in query}
            for row in db.aql.execute(query, bind_vars={"@collection": collection, **wanted}):
                found.append({"collection": collection, **row})
        return found

    @staticmethod
    def _proven_stamps(candidates: list[Candidate]) -> set[str]:
        """The ``tenant_key`` values proven to be the ``v0004`` default-tenant stamp.

        A key is proven by either of two facts:

        * **an orphaned child** — a phase entry or task template carries it under a
          *global* parent. A tenant cannot own a row under a global parent, so the
          key was stamped, not assigned (the state of a deployed volume, where the
          loaders already reset the parents);
        * **a majority** — it is on more than half of *all* seed-named rows, reset
          ones counted (the state right after ``v0004``, when every seed row
          carries it).

        Nothing else qualifies: a lone seed-named row of another tenant is neither,
        so it stays that tenant's.
        """
        proven = {row["tenant_key"] for row in candidates if row["tenant_key"] and row.get("parent_tenant_key") == ""}
        tally: dict[str, int] = {}
        for row in candidates:
            if row["tenant_key"]:
                tally[row["tenant_key"]] = tally.get(row["tenant_key"], 0) + 1
        proven.update(key for key, count in tally.items() if count * 2 > len(candidates))
        return proven

    @staticmethod
    def _apply(db: StandardDatabase, collection: str, keys: list[str]) -> None:
        if keys:
            db.aql.execute(
                "FOR key IN @keys UPDATE {_key: key, tenant_key: ''} IN @@collection",
                bind_vars={"keys": keys, "@collection": collection},
            )

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        candidates = self._candidates(db)
        stamps = self._proven_stamps(candidates)
        selected = [row for row in candidates if row["tenant_key"] and row["tenant_key"] in stamps]
        stamped = sum(1 for row in candidates if row["tenant_key"])

        per_collection: dict[str, int] = {}
        for row in selected:
            per_collection[row["collection"]] = per_collection.get(row["collection"], 0) + 1
        if not dry_run:
            for collection in per_collection:
                self._apply(db, collection, [row["key"] for row in selected if row["collection"] == collection])

        changed = len(selected)
        left_alone = stamped - changed
        logger.info(
            "reset_legacy_seed_tenant_stamps_dry_run" if dry_run else "reset_legacy_seed_tenant_stamps_applied",
            seed_named=len(candidates),
            changed=0 if dry_run else changed,
            to_update=changed,
            seed_named_other_tenant_left_alone=left_alone,
            proven_stamps=len(stamps),
            **per_collection,
        )
        details: dict[str, Any] = {
            **per_collection,
            "seed_named_other_tenant_left_alone": left_alone,
            "proven_stamps": len(stamps),
        }
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(candidates),
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details={"to_update": changed, **details} if dry_run else details,
        )


migration = ResetLegacySeedTenantStampsMigration()
