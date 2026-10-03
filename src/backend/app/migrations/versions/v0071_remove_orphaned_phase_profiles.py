"""v0071 — remove the requirement and nutrient profiles their deleted phase left behind (#2002).

``ArangoLifecycleRepository.delete_phase`` removed a growth phase and its edges but
not the ``requirement_profiles`` / ``nutrient_profiles`` the phase owned. Every seed
that replaced a species' generic phases with its own left the old phase's two
profiles behind, and ``adventskalender`` and ``plant_info_extended`` traded the five
phases of one species on every start — measured against a real ArangoDB: 155
orphans of each kind after the first boot of an empty database, 5 more per boot
after that (943 → 948 → 953). ``delete_phase`` now takes the profiles with it and the
two loaders no longer trade; this migration removes what was already left.

What is removed — a profile only when **both** hold:

* no ``requires_profile`` / ``uses_nutrients`` edge points at it — nothing can read
  it: the profile API and every consumer reach a profile through its phase's edge;
* its ``phase_key`` names no existing growth phase — no phase it could still belong to.

A profile with an edge, or whose phase still exists (an edge lost some other way),
is kept. The profiles are a global catalogue (children of a growth phase), so no
tenant data is involved.

Idempotent (M-3): a second run finds no orphan and writes nothing. Dry-run (M-5)
counts and writes nothing. Both collections are cleaned in one transaction. The log
carries counts only. Irreversible (M-6): what is removed was unreachable, and there is
no phase to give it back to.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: ``profile collection → the edge collection that reaches it from its phase``.
_PROFILE_EDGES = {
    col.REQUIREMENT_PROFILES: col.REQUIRES_PROFILE,
    col.NUTRIENT_PROFILES: col.USES_NUTRIENTS,
}

_ORPHANS = """
FOR p IN @@profiles
    FILTER LENGTH(FOR e IN @@edges FILTER e._to == p._id LIMIT 1 RETURN 1) == 0
    FILTER p.phase_key == null OR p.phase_key == "" OR DOCUMENT(@phases, p.phase_key) == null
    RETURN p._key
"""


class RemoveOrphanedPhaseProfilesMigration(Migration):
    version = "0071"
    name = "remove_orphaned_phase_profiles"
    description = (
        "Remove requirement_profiles / nutrient_profiles that no phase edge reaches and whose phase_key names "
        "no growth phase — the children delete_phase left behind (#2002)."
    )
    reversible = False

    @staticmethod
    def _plan(db: StandardDatabase) -> dict[str, list[str]]:
        """``{profile collection: orphan keys}`` — read-only."""
        plan: dict[str, list[str]] = {}
        for profiles, edges in _PROFILE_EDGES.items():
            if not (db.has_collection(profiles) and db.has_collection(edges)):
                continue
            plan[profiles] = list(
                db.aql.execute(
                    _ORPHANS,
                    bind_vars={"@profiles": profiles, "@edges": edges, "phases": col.GROWTH_PHASES},
                )
            )
        return plan

    @staticmethod
    def _apply(db: StandardDatabase, plan: dict[str, list[str]]) -> int:
        """Remove the planned rows in one transaction, re-checking each inside it.

        The plan was read before the transaction; a phase edge written in between (a
        pod of the previous release still serving) must keep its profile, so the
        orphan condition is evaluated again on the planned keys.
        """
        writes = [name for name, keys in plan.items() if keys]
        if not writes:
            return 0
        reads = [_PROFILE_EDGES[name] for name in writes] + [col.GROWTH_PHASES]
        transaction = db.begin_transaction(read=reads, write=writes)
        removed = 0
        try:
            for profiles in writes:
                cursor = transaction.aql.execute(
                    """
                    FOR key IN @keys
                        LET p = DOCUMENT(@profiles_name, key)
                        FILTER p != null
                        FILTER LENGTH(FOR e IN @@edges FILTER e._to == p._id LIMIT 1 RETURN 1) == 0
                        FILTER p.phase_key == null OR p.phase_key == "" OR DOCUMENT(@phases, p.phase_key) == null
                        REMOVE p IN @@profiles
                        RETURN 1
                    """,
                    bind_vars={
                        "keys": plan[profiles],
                        "@profiles": profiles,
                        "profiles_name": profiles,
                        "@edges": _PROFILE_EDGES[profiles],
                        "phases": col.GROWTH_PHASES,
                    },
                )
                removed += len(list(cursor))
            transaction.commit_transaction()
        except Exception:
            transaction.abort_transaction()
            raise
        return removed

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        plan = self._plan(db)
        per_collection = {name: len(keys) for name, keys in plan.items()}
        planned = sum(per_collection.values())
        removed = 0 if dry_run else self._apply(db, plan)

        logger.info(
            "remove_orphaned_phase_profiles_dry_run" if dry_run else "remove_orphaned_phase_profiles_applied",
            removed=removed,
            to_remove=planned,
            **per_collection,
        )
        details: dict[str, Any] = dict(per_collection)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=planned,
            changed=removed,
            dry_run=dry_run,
            details={"to_remove": planned, **details} if dry_run else details,
        )


migration = RemoveOrphanedPhaseProfilesMigration()
