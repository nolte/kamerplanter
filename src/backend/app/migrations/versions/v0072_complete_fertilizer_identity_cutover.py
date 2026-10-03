"""v0072 — finish the fertilizer identity cutover v0069 started (review follow-up to #2030).

Two gaps in ``v0069`` (``tenant_scoped_fertilizer_identity_index``), both measured on a
real ArangoDB 3.12 (``tests/integration/test_v0072_*``). v0069 is shipped (merged to
``develop``), so its class is frozen (M-7); the correction is this version.

1. **A legacy index of type ``hash`` was not dropped.** ``ensure_collections`` created
   ``fertilizers(product_name, brand)`` with ``add_hash_index`` until June 2026; ArangoDB
   3.12 still reports such an index as ``type: "hash"``. v0069 matched only
   ``type == "persistent"``, so on a volume created in that window the collection-wide
   constraint stayed in force and the compound index was cosmetic — a tenant was still
   refused a product name a global seed holds. This version drops every **unique**
   index on exactly ``(product_name, brand)``, ``hash`` or ``persistent``; a non-unique
   one on the same fields (no code has ever created one) is left alone.

2. **An absent ``tenant_key`` is a second "global" value.** The compound index sees an
   absent attribute as ``null``, which is not ``""``: a legacy global row without the
   attribute and a global row with ``tenant_key == ""`` of the same pair were both
   accepted, while ``get_global_fertilizers`` treats both as the one global row. The
   species cutover closed the same gap first (``v0036`` stamped the absent attribute
   ``""`` before ``v0041`` made the compound index unique); here the order is the other
   way round, so the stamp skips a row whose pair already has a ``""`` twin — writing it
   would be refused by the index — and counts it instead.

Idempotent (M-3): a re-run finds no absent attribute it may stamp and no legacy index.
Dry-run (M-5) counts both and writes nothing. Irreversible (M-6): the absent attribute is
not restored, and the dropped index is the constraint #2000 retired.
"""

from __future__ import annotations

from typing import Any

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.collections import LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

#: Rows without the attribute, split into "may be stamped" and "a '' twin exists".
#: ``@stamp`` turns the read into the write; one statement, so the split and the write agree.
_ABSENT = """
LET rows = (
    FOR d IN @@fertilizers
        FILTER d.tenant_key == null
        LET twin = FIRST(
            FOR t IN @@fertilizers
                FILTER t.tenant_key == "" AND t.product_name == d.product_name AND t.brand == d.brand
                LIMIT 1 RETURN 1
        )
        RETURN {key: d._key, twin: twin != null}
)
LET stamped = @stamp ? (
    FOR r IN rows FILTER !r.twin UPDATE r.key WITH {tenant_key: ""} IN @@fertilizers RETURN 1
) : []
RETURN {
    stampable: LENGTH(FOR r IN rows FILTER !r.twin RETURN 1),
    twinned: LENGTH(FOR r IN rows FILTER r.twin RETURN 1),
    stamped: LENGTH(stamped)
}
"""


class CompleteFertilizerIdentityCutoverMigration(Migration):
    version = "0072"
    name = "complete_fertilizer_identity_cutover"
    description = (
        "Drop a unique (product_name, brand) fertilizer index of type hash that v0069 missed, and stamp an "
        "absent tenant_key on fertilizers as global '' (review follow-up to #2030 / #2000)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        # ``ensure_collections`` creates ``fertilizers`` (and the compound index) before
        # any migration runs, so neither needs probing here.
        fertilizers = db.collection(col.FERTILIZERS)
        legacy = [
            idx["id"]
            for idx in fertilizers.indexes()
            if idx["type"] in ("persistent", "hash")
            and idx["fields"] == LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS
            and idx["unique"]
        ]
        absent: dict[str, Any] = next(
            iter(db.aql.execute(_ABSENT, bind_vars={"@fertilizers": col.FERTILIZERS, "stamp": not dry_run})),
            {"stampable": 0, "twinned": 0, "stamped": 0},
        )
        if not dry_run:
            for index_id in legacy:
                fertilizers.delete_index(index_id, ignore_missing=True)

        planned = len(legacy) + int(absent["stampable"])
        details: dict[str, Any] = {
            "legacy_indexes_dropped": 0 if dry_run else len(legacy),
            "absent_tenant_key_stamped": int(absent["stamped"]),
            "absent_tenant_key_left_beside_global_twin": int(absent["twinned"]),
        }
        if dry_run:
            details = {**details, "to_update": planned, "legacy_indexes": len(legacy)}
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=planned + int(absent["twinned"]),
            changed=0 if dry_run else len(legacy) + int(absent["stamped"]),
            dry_run=dry_run,
            details=details,
        )


migration = CompleteFertilizerIdentityCutoverMigration()
