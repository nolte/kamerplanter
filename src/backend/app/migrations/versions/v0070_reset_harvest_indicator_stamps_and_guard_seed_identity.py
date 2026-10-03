"""v0070 — reset the v0004 stamp on seed harvest indicators, re-dedupe, guard the identity (#2001).

Two gaps #1956 / ``v0066`` / ``v0068`` left, both measured against a real ArangoDB
(``tests/integration/test_v0070_*``).

1. The v0004 stamp on ``harvest_indicators``
--------------------------------------------
``backfill_tenant_key`` (v0004) stamped ``harvest_indicators`` with the default
tenant's key too; ``v0066`` reset only fertilizers, nutrient plans (+ entries),
workflow and task templates. The stamp does **not** make tenant deletion remove the
row — the erasure inventory lists ``harvest_indicators`` as a global catalogue that
it never touches — but it does make ``v0068`` skip the row: ``tenant_key`` is an
attribute the loader never writes, so a stamped row is "not a row the loader wrote"
and is in no duplicate group. On a legacy volume the stamped original therefore
survived ``v0068`` beside one surviving copy of each identity.

**Proof of the stamp.** ``HarvestIndicator`` has no ``tenant_key`` field and nothing
else writes one: every ``tenant_key`` on this collection was put there by v0004.
That is a stronger proof than ``v0066`` could have for its catalogues, where tenants
own rows. The reset is nevertheless held to the *seed-identified* rows, the way
``v0066`` is: a row is reset only when it is one the seed names — a row with a
species by ``(species scientific_name, indicator_type, measurement_unit)`` (the
loader's own identity, ``find_indicator``), a species-less legacy row by the exact
content of a seed entry (``v0068``'s rule). A row an operator created is left as it
is. The attribute is **removed**, not emptied: ``v0068`` treats any extra attribute,
an empty ``tenant_key`` included, as "not written by the loader".

Then ``v0068`` is run again (delegated, not re-implemented — the ``v0026`` → ``v0010``
precedent): the reset rows now join their duplicate groups, the oldest of each group
(the pre-v0004 original) is kept, and a copy an observation refers to is kept.

2. No concurrency guard on the create-if-absent seeds
-----------------------------------------------------
The seed registry runs on every replica without a lock, and the create-if-absent
writes (harvest indicators by identity, IPM edges by vertex pair) look before they
write. Unique indexes make the storage layer refuse the second of two replicas:
``harvest_indicators(species_key, indicator_type, measurement_unit)`` **sparse** (a
species-less legacy row is outside it) and ``(_from, _to)`` on ``targets_pest``,
``targets_disease``, ``contraindicated_with``. ``ensure_collections`` tries to create
them on every boot but runs *before* the migrations, so on a legacy volume the
duplicates this migration removes block them; they are created here, after the
de-duplication. A duplicate this migration may not remove (one an observation refers
to, one with operator-edited content) keeps its index from being created: that is
logged with the count, the boot continues, and every later boot retries.

Idempotent (M-3): a re-run finds no stamp, no duplicate and every index present and
writes nothing. Dry-run (M-5) writes nothing and reports the stamps it would reset
and the duplicates removable *now*; the duplicates the reset would expose are bounded
by the stamp count. Irreversible (M-6): the stamped key is the v0004 default tenant's,
which nobody wants back, and the removed rows are copies of a kept one.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.collections import (
    EDGE_PAIR_FIELDS,
    HARVEST_INDICATOR_IDENTITY_FIELDS,
    UNIQUE_PAIR_EDGE_COLLECTIONS,
    ensure_unique_index_when_clean,
    has_unique_index,
)
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.versions.v0068_dedupe_seed_rows_multiplied_per_boot import migration as _v0068
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

#: The content fields a seed entry writes besides the species (``v0068._SEED_FIELDS``).
_CONTENT_FIELDS = (
    "indicator_type",
    "measurement_unit",
    "measurement_method",
    "observation_frequency",
    "reliability_score",
)

_STAMPED = """
FOR d IN @@indicators
    FILTER HAS(d, "tenant_key")
    LET species = d.species_key ? DOCUMENT(@species_collection, d.species_key) : null
    RETURN {
        key: d._key,
        species_key: d.species_key,
        species_name: species.scientific_name,
        content: [d.indicator_type, d.measurement_unit, d.measurement_method, d.observation_frequency,
                  d.reliability_score]
    }
"""


def _seed_identities() -> tuple[set[tuple[Any, ...]], set[tuple[Any, ...]]]:
    """``(species_name, indicator_type, measurement_unit)`` and the species-less content tuples the YAML writes."""
    entries = load_yaml("harvest_indicators.yaml").get("harvest_indicators", [])
    named = {(e["species_name"], e["indicator_type"], e["measurement_unit"]) for e in entries}
    anonymous = {tuple(e[f] for f in _CONTENT_FIELDS) for e in entries}
    return named, anonymous


def _index_targets() -> list[tuple[str, list[str], bool]]:
    """``(collection, fields, sparse)`` of every identity index this migration guarantees."""
    return [
        (col.HARVEST_INDICATORS, HARVEST_INDICATOR_IDENTITY_FIELDS, True),
        *((name, EDGE_PAIR_FIELDS, False) for name in UNIQUE_PAIR_EDGE_COLLECTIONS),
    ]


class ResetHarvestIndicatorStampsAndGuardSeedIdentityMigration(Migration):
    version = "0070"
    name = "reset_harvest_indicator_stamps_and_guard_seed_identity"
    description = (
        "Remove the v0004 tenant_key stamp from seed harvest_indicators, re-run the v0068 de-duplication, and "
        "create the unique seed-identity indexes on harvest_indicators and the IPM treatment edges (#2001)."
    )
    reversible = False

    @staticmethod
    def _stamped_seed_rows(db: StandardDatabase) -> tuple[list[str], int]:
        """``(keys of seed-identified stamped rows, stamped rows left alone)`` — read-only."""
        if not db.has_collection(col.HARVEST_INDICATORS):
            return [], 0
        named, anonymous = _seed_identities()
        reset: list[str] = []
        left_alone = 0
        rows = db.aql.execute(
            _STAMPED, bind_vars={"@indicators": col.HARVEST_INDICATORS, "species_collection": col.SPECIES}
        )
        for row in rows:
            # ``content`` is ordered like ``_CONTENT_FIELDS``: type and unit lead, as in the loader's identity.
            content = tuple(row["content"])
            named_row = (row["species_name"], *content[:2])
            seed_named = named_row in named if row["species_key"] else content in anonymous
            if seed_named:
                reset.append(row["key"])
            else:
                left_alone += 1
        return reset, left_alone

    @staticmethod
    def _missing_indexes(db: StandardDatabase) -> list[tuple[str, list[str], bool]]:
        return [
            (name, fields, sparse)
            for name, fields, sparse in _index_targets()
            if db.has_collection(name) and not has_unique_index(db.collection(name), fields, sparse=sparse)
        ]

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        reset_keys, left_alone = self._stamped_seed_rows(db)
        if reset_keys and not dry_run:
            db.aql.execute(
                "FOR key IN @keys UPDATE {_key: key, tenant_key: null} IN @@indicators OPTIONS {keepNull: false}",
                bind_vars={"keys": reset_keys, "@indicators": col.HARVEST_INDICATORS},
            )

        # The reset rows join their duplicate groups only now; v0068's rules decide what goes.
        dedupe = _v0068.up(db, dry_run=dry_run)

        missing = self._missing_indexes(db)
        created: list[str] = []
        blocked: list[str] = []
        if not dry_run:
            for name, fields, sparse in missing:
                if ensure_unique_index_when_clean(db.collection(name), fields, sparse=sparse):
                    created.append(name)
                else:
                    blocked.append(name)
            if blocked:
                logger.warning(
                    "seed_identity_index_blocked_by_duplicates",
                    collections=blocked,
                    hint="duplicates remain that v0068 may not remove (referenced or edited); every boot retries",
                )

        removed = int(dedupe.details.get("to_remove", 0)) if dry_run else dedupe.changed
        changed = len(reset_keys) + removed + len(created)
        details: dict[str, Any] = {
            "stamps_reset": len(reset_keys),
            "stamped_rows_left_alone": left_alone,
            "duplicates_removed": removed,
            "indexes_created": created,
            "indexes_blocked": blocked,
        }
        if dry_run:
            details = {
                **details,
                "to_update": len(reset_keys) + removed + len(missing),
                "indexes_missing": [name for name, _, _ in missing],
            }
        logger.info(
            "reset_harvest_indicator_stamps_dry_run" if dry_run else "reset_harvest_indicator_stamps_applied",
            stamps_reset=len(reset_keys),
            stamped_rows_left_alone=left_alone,
            duplicates_removed=removed,
            indexes_created=len(created),
            indexes_blocked=len(blocked),
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(reset_keys) + left_alone,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details=details,
        )


migration = ResetHarvestIndicatorStampsAndGuardSeedIdentityMigration()
