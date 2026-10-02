"""v0068 — remove the exact duplicates the seed loaders wrote on every boot (#1956).

Until #1956 ``run_seed`` appended the whole harvest-indicator set (173 rows) on every
start — the collection has no unique index, so the insert its ``try/except`` guarded
never failed — and the IPM treatment edges (``targets_pest``, ``targets_disease``,
``contraindicated_with``) were written again the same way (92 + 69 + 15 per boot).
The loaders are fixed; every production volume that booted N times still carries N
copies. This migration removes the copies and nothing else.

What is removed — conservative, and no wider than the loaders' own output
------------------------------------------------------------------------
* ``harvest_indicators``: a row is removed only when **all** of these hold:

  - another row has *identical content* (every attribute except ``_key``/``_id``/``_rev``
    and the two timestamps) — the oldest of the group is kept;
  - the content is exactly what an entry of ``harvest_indicators.yaml`` writes (its
    four content fields, ``description`` absent, no further attribute); a row an
    operator edited — a tuned reliability score, a description — no longer equals a seed
    entry, so it is never in a group at all;
  - no observation refers to the row (``harvest_observations.indicator_key`` or a
    ``uses_indicator`` edge). A referenced duplicate is **kept** and counted, because
    removing it would leave a user's observation pointing at nothing.

  The removed row's ``has_harvest_indicator`` edge goes with it; the kept row's edge stays.

  Legacy rows written when the species was not yet resolvable carry no ``species_key``.
  Nine different species' ``brix`` entries are one identical, species-less row each
  boot, so such rows form one group per content and one is kept: no species can reach
  them, and the seed now creates the resolved rows itself.

* ``targets_pest`` / ``targets_disease`` / ``contraindicated_with``: an edge is removed only
  when another edge joins the same two vertices **and** carries nothing but ``created_at``.
  The oldest is kept.

Idempotency (M-3) — a second run finds no group of more than one and writes nothing.
Dry-run (M-5) counts the plan and writes nothing; every write is one transaction.
Irreversible (M-6): the removed rows are copies of a row that is kept, so there is
nothing to restore, and the keys of the copies are not worth keeping.

Operator count before deploying, on a restored backup (``arangosh``)::

    FOR d IN harvest_indicators
        COLLECT c = UNSET(d, "_key", "_id", "_rev", "created_at", "updated_at") WITH COUNT INTO n
        FILTER n > 1
        RETURN {content: c, copies: n}
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

#: The attributes ``HarvestIndicator`` stores for a seed entry, besides ``species_key``.
_SEED_FIELDS = (
    "indicator_type",
    "measurement_unit",
    "measurement_method",
    "observation_frequency",
    "reliability_score",
)
_SYSTEM_FIELDS = frozenset({"_key", "_id", "_rev", "created_at", "updated_at"})
_EDGE_COLLECTIONS = (col.TARGETS_PEST, col.TARGETS_DISEASE, col.CONTRAINDICATED_WITH)
_PLAIN_EDGE_FIELDS = frozenset({"_key", "_id", "_rev", "_from", "_to", "created_at"})
_REFERENCED_BY_OBSERVATION = """
FOR o IN @@observations FILTER o.indicator_key != null AND o.indicator_key != "" RETURN DISTINCT o.indicator_key
"""
_REFERENCED_BY_EDGE = "FOR e IN @@uses RETURN DISTINCT PARSE_IDENTIFIER(e._to).key"


def _age_order(doc: dict[str, Any]) -> tuple[str, int, str]:
    """Oldest first: creation time, then the numeric key ArangoDB assigns in write order."""
    key = str(doc["_key"])
    return (str(doc.get("created_at") or ""), int(key) if key.isdigit() else 0, key)


def _seed_content() -> tuple[set[tuple[Any, ...]], set[tuple[Any, ...]]]:
    """Content tuples the seed YAML writes: ``(species_name, *fields)`` and species-less ``(*fields)``."""
    entries = load_yaml("harvest_indicators.yaml").get("harvest_indicators", [])
    named = {(e["species_name"], *(e[f] for f in _SEED_FIELDS)) for e in entries}
    anonymous = {tuple(e[f] for f in _SEED_FIELDS) for e in entries}
    return named, anonymous


class DedupeSeedRowsMultipliedPerBootMigration(Migration):
    version = "0068"
    name = "dedupe_seed_rows_multiplied_per_boot"
    description = (
        "Remove exact duplicate harvest_indicators rows and IPM treatment edges the seed loaders "
        "appended on every boot (#1956); keeps one per group, never a row that differs or is referenced."
    )
    reversible = False

    @staticmethod
    def _plan_indicators(db: StandardDatabase) -> tuple[list[str], int, int]:
        """``(keys to remove, groups, duplicates kept because an observation refers to them)``."""
        if not db.has_collection(col.HARVEST_INDICATORS):
            return [], 0, 0
        named, anonymous = _seed_content()
        species_names = (
            {
                row["key"]: row["name"]
                for row in db.aql.execute("FOR s IN species RETURN {key: s._key, name: s.scientific_name}")
            }
            if db.has_collection(col.SPECIES)
            else {}
        )
        referenced: set[str] = set()
        if db.has_collection(col.HARVEST_OBSERVATIONS):
            referenced.update(
                db.aql.execute(_REFERENCED_BY_OBSERVATION, bind_vars={"@observations": col.HARVEST_OBSERVATIONS})
            )
        if db.has_collection(col.USES_INDICATOR):
            referenced.update(db.aql.execute(_REFERENCED_BY_EDGE, bind_vars={"@uses": col.USES_INDICATOR}))

        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for doc in db.collection(col.HARVEST_INDICATORS).all():
            extra = set(doc) - _SYSTEM_FIELDS - {*_SEED_FIELDS, "species_key", "description"}
            if extra or doc.get("description"):
                continue  # not a row the loader wrote
            fields = tuple(doc.get(f) for f in _SEED_FIELDS)
            species_key = doc.get("species_key")
            if species_key:
                if (species_names.get(species_key), *fields) not in named:
                    continue
            elif fields not in anonymous:
                continue
            groups[(species_key or None, *fields)].append(doc)

        remove: list[str] = []
        duplicate_groups = 0
        kept_referenced = 0
        for docs in groups.values():
            if len(docs) < 2:
                continue
            duplicate_groups += 1
            for doc in sorted(docs, key=_age_order)[1:]:
                if doc["_key"] in referenced:
                    kept_referenced += 1
                else:
                    remove.append(doc["_key"])
        return remove, duplicate_groups, kept_referenced

    @staticmethod
    def _plan_edges(db: StandardDatabase) -> dict[str, list[str]]:
        """``{edge collection: keys to remove}`` — the younger of two plain edges joining the same vertices."""
        plan: dict[str, list[str]] = {}
        for collection in _EDGE_COLLECTIONS:
            if not db.has_collection(collection):
                continue
            groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
            for edge in db.collection(collection).all():
                if set(edge) - _PLAIN_EDGE_FIELDS:
                    continue  # carries data of its own
                groups[(edge["_from"], edge["_to"])].append(edge)
            plan[collection] = [
                e["_key"] for edges in groups.values() if len(edges) > 1 for e in sorted(edges, key=_age_order)[1:]
            ]
        return plan

    @staticmethod
    def _apply(db: StandardDatabase, indicator_keys: list[str], edge_plan: dict[str, list[str]]) -> None:
        writes = [col.HARVEST_INDICATORS, col.HAS_HARVEST_INDICATOR, *(c for c, keys in edge_plan.items() if keys)]
        transaction = db.begin_transaction(write=writes)
        try:
            if indicator_keys:
                ids = [f"{col.HARVEST_INDICATORS}/{key}" for key in indicator_keys]
                transaction.aql.execute(
                    "FOR e IN @@edges FILTER e._to IN @ids REMOVE e IN @@edges",
                    bind_vars={"@edges": col.HAS_HARVEST_INDICATOR, "ids": ids},
                )
                transaction.aql.execute(
                    "FOR key IN @keys REMOVE key IN @@collection",
                    bind_vars={"keys": indicator_keys, "@collection": col.HARVEST_INDICATORS},
                )
            for collection, keys in edge_plan.items():
                if keys:
                    transaction.aql.execute(
                        "FOR key IN @keys REMOVE key IN @@collection",
                        bind_vars={"keys": keys, "@collection": collection},
                    )
            transaction.commit_transaction()
        except Exception:
            transaction.abort_transaction()
            raise

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        indicator_keys, groups, kept_referenced = self._plan_indicators(db)
        edge_plan = self._plan_edges(db)
        per_collection = {
            col.HARVEST_INDICATORS: len(indicator_keys),
            **{c: len(keys) for c, keys in edge_plan.items()},
        }
        removed = sum(per_collection.values())
        scanned = db.collection(col.HARVEST_INDICATORS).count() if db.has_collection(col.HARVEST_INDICATORS) else 0

        if not dry_run and removed:
            self._apply(db, indicator_keys, edge_plan)

        logger.info(
            "dedupe_seed_rows_dry_run" if dry_run else "dedupe_seed_rows_applied",
            duplicate_indicator_groups=groups,
            duplicate_indicators_kept_because_referenced=kept_referenced,
            **{f"removed_{name}": count for name, count in per_collection.items()},
        )
        details: dict[str, Any] = {
            "duplicate_indicator_groups": groups,
            "duplicate_indicators_kept_because_referenced": kept_referenced,
            **per_collection,
        }
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else removed,
            dry_run=dry_run,
            details={"to_remove": removed, **details} if dry_run else details,
        )


migration = DedupeSeedRowsMultipliedPerBootMigration()
