"""v0044 — give every fertilizer stock an owner, via its product (#1268).

``FertilizerStock`` carried no ``tenant_key``. A stock is inventory — a batch
number, a purchase price, a volume in one garden's cupboard — not catalogue
data. Without an owner, ``get_stocks`` returned every row for a product, so for
a GLOBAL fertilizer (the seeded catalogue, i.e. the common case) every tenant
listed every other tenant's inventory, and after #1265's pairing fix could still
edit it.

**Attribution rule (operator decision, 2026-08-22).** A stock inherits the
tenant of the fertilizer it belongs to. That is the only evidence of ownership
in the data model: nothing else records who bought a bottle.

**A stock of a GLOBAL fertilizer is left unstamped and counted.** A global
product has no tenant to inherit, and the stock rows on it are exactly the pile
this migration exists to break up — so there is no owner to derive, only one to
invent. Splitting them by guesswork would hand somebody else's purchase record
to a stranger, and stamping them globally would keep them readable by everyone,
which is the state being ended.

**Consequence, stated rather than discovered.** An unstamped stock
(``tenant_key == ""``) is invisible to every tenant in ``full`` mode, because a
real tenant key is never empty and ``get_stocks`` filters on strict equality.
That is the fail-safe direction — shown to nobody rather than to everybody — but
it does mean such a row disappears from the UI until an administrator attributes
it. This is why ``details`` reports the count and the keys: the number is the
operator's work list, not decoration. In ``light`` mode the sole operator
resolves to ``""`` and still sees them, which is correct for a single-operator
install.

**Rows already corrupted by the pre-#1265 update path are not repaired here.**
A stock written through the old `update_stock` carries the literal
``fertilizer_key: "temp"``, which resolves to no product, so it is counted as
orphaned rather than attributed. Repairing it would mean guessing which product
it belonged to, and the field that said so was the one overwritten.

Idempotent (M-3): only stocks whose stored ``tenant_key`` differs from the
derived one are written, so a re-run reports ``changed == 0``.

Not reversible (M-6): the pre-migration state is "no attribute at all", which
cannot be told apart afterwards from a deliberate empty stamp — and removing the
field again would silently disarm the filter that now depends on it.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


class AttributeFertilizerStocksMigration(Migration):
    version = "0044"
    name = "attribute_fertilizer_stocks"
    description = "Derive each fertilizer stock's tenant from its product (#1268)."
    reversible = False

    #: One statement, so the read and the write cannot disagree about which
    #: stocks are in scope. The product is resolved by key rather than joined,
    #: because a stock whose ``fertilizer_key`` matches nothing — the "temp"
    #: rows the pre-#1265 update path wrote — must be *counted*, not dropped
    #: silently by an inner join.
    _PLAN_QUERY = f"""
    FOR stock IN {col.FERTILIZER_STOCKS}
      LET product = DOCUMENT(CONCAT('{col.FERTILIZERS}/', stock.fertilizer_key))
      RETURN {{
        key: stock._key,
        stored: stock.tenant_key,
        product_found: product != null,
        owner: product != null ? product.tenant_key : null
      }}
    """

    def _plan(self, db: StandardDatabase) -> tuple[list[dict[str, str]], int, list[str], list[str]]:
        """Return ``(writes, scanned, global_product_keys, orphan_keys)`` without writing.

        Pure, so a dry run reports the numbers the real run would produce. A dry
        run that took a different path would describe a plan nobody executes.
        """
        if not db.has_collection(col.FERTILIZER_STOCKS) or not db.has_collection(col.FERTILIZERS):
            return [], 0, [], []

        rows = list(db.aql.execute(self._PLAN_QUERY))
        writes: list[dict[str, str]] = []
        on_global: list[str] = []
        orphans: list[str] = []

        for row in rows:
            if not row.get("product_found"):
                orphans.append(row["key"])
                continue
            owner = row.get("owner") or ""
            if not owner:
                on_global.append(row["key"])
                continue
            if (row.get("stored") or "") != owner:
                writes.append({"key": row["key"], "tenant_key": owner})

        return writes, len(rows), on_global, orphans

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        writes, scanned, on_global, orphans = self._plan(db)

        if not dry_run and writes:
            stocks = db.collection(col.FERTILIZER_STOCKS)
            for write in writes:
                stocks.update({"_key": write["key"], "tenant_key": write["tenant_key"]})

        logger.info(
            "attribute_fertilizer_stocks",
            scanned=scanned,
            attributed=len(writes),
            on_global_product=len(on_global),
            orphaned=len(orphans),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else len(writes),
            dry_run=dry_run,
            details={
                "attributed": len(writes),
                # The keys, not just the count: an operator cannot attribute a
                # stock they cannot name, and these rows are invisible in the UI
                # until somebody does.
                "on_global_product_left_unstamped": on_global,
                # Separately, because these mean something different: a stock
                # whose product does not resolve is evidence of the pre-#1265
                # corruption, not of an ambiguous owner.
                "orphaned_left_unstamped": orphans,
            },
        )


#: Module-level instance the discovery loader binds (framework contract).
migration = AttributeFertilizerStocksMigration()
