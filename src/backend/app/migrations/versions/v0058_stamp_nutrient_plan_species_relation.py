"""v0058 — give every pre-#1618 nutrient plan an explicit, empty species relation.

#1618 adds ``NutrientPlan.species_keys``: the species a plan is written for, and
the relation the onboarding wizard's plan match filters on
(``ArangoNutrientPlanRepository.list_template_plan_summaries``). Plans stored
before the field existed carry no such attribute. This migration writes an
explicit ``[]`` into it — and **nothing else**.

* **Why ``[]`` and not a derived list.** The only rows whose species *can* be
  derived are the seeded template plans, whose source documents name their
  species. Those are maintained by the seed loaders (``species_names`` in the
  plan YAML, resolved against the species catalogue on every startup), and
  migrations run **before** seeds (NFR-016 O-1): a backfill here would be
  overwritten a second later by the seed, which would make two sources of truth
  for one relation. Every other plan — tenant-created, cloned, imported — has no
  source that names a species, and inventing one from its name or tags is
  exactly the guess the operator decision (2026-09-23) rules out.
* **Why write anything at all.** An empty relation matches no species. The read
  already treats an absent attribute as empty (``IS_ARRAY`` guard), so this is
  not what makes the filter correct; it makes the stored shape equal to the
  model's, so "attribute absent" no longer occurs and a document seen without it
  was written past the model.
* **Idempotent (M-3):** the scan selects ``!IS_ARRAY(doc.species_keys)`` only —
  absent or ``null``. A plan that already carries a list, empty or not, is never
  touched, including one a #1618 path wrote between deploy and migration run.
* **Not reversible (M-6):** after the run, "stamped by v0058" and "saved empty
  by a user" are indistinguishable, so ``down`` cannot know what to remove.
* **Dry run (M-5):** reports the plan and writes nothing.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: The #1618 relation field on ``nutrient_plans``.
SPECIES_RELATION_FIELD = "species_keys"


class StampNutrientPlanSpeciesRelationMigration(Migration):
    version = "0058"
    name = "stamp_nutrient_plan_species_relation"
    description = "Write an explicit empty species_keys relation on nutrient plans that predate #1618."
    reversible = False

    #: Only plans whose relation is absent or ``null``. A plan that carries a
    #: list — empty or linked — is already in its final shape.
    _SCAN_QUERY = """
    FOR doc IN @@collection
      FILTER !IS_ARRAY(doc.@field)
      RETURN doc._key
    """

    _TOTAL_QUERY = "RETURN LENGTH(@@collection)"

    def _plan(self, db: StandardDatabase) -> tuple[int, list[str]]:
        """Return ``(scanned, keys to stamp)`` without writing."""
        if not db.has_collection(col.NUTRIENT_PLANS):
            return 0, []
        scanned = int(next(iter(db.aql.execute(self._TOTAL_QUERY, bind_vars={"@collection": col.NUTRIENT_PLANS})), 0))
        keys = [
            str(k)
            for k in db.aql.execute(
                self._SCAN_QUERY,
                bind_vars={"@collection": col.NUTRIENT_PLANS, "field": SPECIES_RELATION_FIELD},
            )
        ]
        return scanned, keys

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        scanned, keys = self._plan(db)

        if not dry_run and keys:
            target = db.collection(col.NUTRIENT_PLANS)
            for key in keys:
                target.update({"_key": key, SPECIES_RELATION_FIELD: []}, silent=True)

        logger.info("stamp_nutrient_plan_species_relation", scanned=scanned, stamped=len(keys), dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else len(keys),
            dry_run=dry_run,
            details={"stamped": len(keys)},
        )


migration = StampNutrientPlanSpeciesRelationMigration()
