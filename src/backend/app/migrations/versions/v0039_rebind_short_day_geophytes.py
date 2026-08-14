"""v0039 — move short-day geophytes off ``photoperiodic_ornamental`` (#1149).

``resolve_phase_sequence_name`` used to answer ``photoperiodic_ornamental`` for a
species that is both short-day and a bulb geophyte: rule 1 fired before rule 4
could see ``bulb_geophyte``. The resolver now excludes geophytes from rule 1, so a
**fresh** install binds ``Dahlia pinnata`` to ``geophyte_fine``.

An **existing** install does not follow: ``v0027`` already wrote the
``photoperiodic_ornamental`` edge and a shipped migration is a frozen record of
what it did, not a live statement of what is correct. Without this migration the
two would diverge permanently — the failure mode
``test_photoperiodic_ornamental_seed_convergence`` exists to catch, and did.

**What the wrong binding schedules.** ``photoperiodic_ornamental`` runs
``active_growth → short_day_induction → bract_coloring → rest_phase``. A dahlia
has no bracts. The two phases its year actually turns on — ``tuber_formation``
and ``dry_storage`` — exist only in ``geophyte_fine``, so nothing in the assigned
lifecycle ever prompted lifting and storing the tubers of a species marked
``frost_sensitivity: sensitive`` before frost.

**Scope guard, deliberately narrow.** Only an edge that currently points at
``photoperiodic_ornamental`` is moved, and only for a species this migration's own
map names. A species someone has since bound by hand to something else is left
alone: this repairs one classifier mistake, it does not re-assert the classifier
over every operator decision made since.

Idempotent (M-3): a re-run finds the edges already on ``geophyte_fine`` and
reports ``changed == 0``. Irreversible (M-6) in the same sense as ``v0027`` — the
prior target is not recorded per edge, and re-deriving it would mean re-running
the old, wrong rule.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: The sequence these species were wrongly bound to, and the only one this
#: migration will move an edge *off*.
_WRONG_SEQUENCE = "photoperiodic_ornamental"

#: The sequence they belong on.
_TARGET_SEQUENCE = "geophyte_fine"

#: Species that are both short-day and ``bulb_geophyte`` in the seed catalogue, and
#: therefore hit the rule-1 defect. Listed rather than derived from the live
#: attributes on purpose: a migration must do the same thing on every install, and
#: an attribute-derived set would silently widen if a later seed edit changed a
#: species' ``growth_habit``.
_AFFECTED_SPECIES: frozenset[str] = frozenset({"Dahlia pinnata", "Dahlia x cultorum"})


class RebindShortDayGeophytesMigration(Migration):
    version = "0039"
    name = "rebind_short_day_geophytes"
    description = "Move short-day bulb geophytes from photoperiodic_ornamental to geophyte_fine (#1149)."
    reversible = False

    def _scan(self, db: StandardDatabase, collection: str) -> list[dict[str, Any]]:
        """Return every document of ``collection`` (missing collection → empty list)."""
        if not db.has_collection(collection):
            return []
        return list(db.aql.execute(f"FOR d IN {collection} RETURN d"))

    def _plan(self, db: StandardDatabase) -> list[dict[str, str]]:
        """Return ``[{edge_key, to_id}]`` for every edge that must move.

        Pure and dry-run-safe. Returns an empty plan — never raises — when the
        species, the target sequence or the collections are absent, so the
        migration is a clean no-op on a fresh or partially-seeded database.
        """
        sequences = self._scan(db, col.PHASE_SEQUENCES)
        seq_key_by_name = {s.get("name"): s["_key"] for s in sequences}
        seq_name_by_id = {f"{col.PHASE_SEQUENCES}/{s['_key']}": s.get("name") for s in sequences}

        target_key = seq_key_by_name.get(_TARGET_SEQUENCE)
        if not target_key:
            return []
        target_id = f"{col.PHASE_SEQUENCES}/{target_key}"

        affected_from_ids = {
            f"{col.SPECIES}/{s['_key']}"
            for s in self._scan(db, col.SPECIES)
            if s.get("scientific_name") in _AFFECTED_SPECIES
        }
        if not affected_from_ids:
            return []

        plan: list[dict[str, str]] = []
        for edge in self._scan(db, col.HAS_PHASE_SEQUENCE):
            if edge.get("_from") not in affected_from_ids:
                continue
            # The scope guard: move only off the one wrong sequence. An edge already
            # on the target is the idempotent re-run; an edge on anything else is an
            # operator's binding and is not this migration's business.
            if seq_name_by_id.get(edge.get("_to", "")) != _WRONG_SEQUENCE:
                continue
            plan.append({"edge_key": edge["_key"], "to_id": target_id})
        return plan

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        plan = self._plan(db)

        if not dry_run:
            for item in plan:
                db.aql.execute(
                    f"UPDATE {{_key: @key, _to: @to_id}} IN {col.HAS_PHASE_SEQUENCE}",
                    bind_vars={"key": item["edge_key"], "to_id": item["to_id"]},
                )

        logger.info("rebind_short_day_geophytes", rebound=len(plan), dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(plan),
            changed=0 if dry_run else len(plan),
            dry_run=dry_run,
            details={"to_rebind": len(plan)} if dry_run else {"rebound": len(plan)},
        )


#: Module-level instance the discovery loader binds (framework contract).
migration = RebindShortDayGeophytesMigration()
