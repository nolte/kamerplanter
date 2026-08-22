"""v0044 derives a stock's owner from its product (#1268).

The migration exists so the new strict stock filter has something to filter *by*.
Its interesting cases are all in the residue: the stocks it deliberately does
**not** attribute, and whether it reports them loudly enough that an operator can
act — because an unattributed stock is invisible to every tenant afterwards.

Two residues, and they mean different things:

* a stock on a GLOBAL product has no owner to inherit — that pile is what this
  migration exists to break up, and splitting it by guesswork would hand one
  garden's purchase record to another;
* a stock whose product does not resolve at all is evidence of the pre-#1265
  corruption (`update_stock` wrote the literal `fertilizer_key: "temp"`), not of
  an ambiguous owner.

The AQL double answers the migration's *own* query text and refuses one it does
not recognise. A double that silently returned `[]` for an unknown query would
make every assertion here pass vacuously, including the idempotence one, which is
supposed to see an empty write list.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.migrations.versions.v0044_attribute_fertilizer_stocks import (
    AttributeFertilizerStocksMigration,
)

_STOCKS = "fertilizer_stocks"
_FERTS = "fertilizers"


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self.docs = docs
        self.updates: list[dict[str, Any]] = []

    def update(self, patch: dict[str, Any]) -> None:
        self.updates.append(patch)
        self.docs[patch["_key"]].update({k: v for k, v in patch.items() if k != "_key"})


class _Aql:
    def __init__(self, stocks: _Collection, ferts: _Collection) -> None:
        self._stocks = stocks
        self._ferts = ferts

    def execute(self, query: str, bind_vars: dict | None = None) -> list[dict[str, Any]]:
        normalised = re.sub(r"\s+", " ", query).strip()
        if _STOCKS not in normalised or _FERTS not in normalised:
            raise AssertionError(f"unexpected query, this double cannot answer it: {normalised!r}")
        if "stock.fertilizer_key" not in normalised:
            raise AssertionError(
                "the migration no longer derives ownership from stock.fertilizer_key. That reference "
                "is the only evidence of who owns a stock; anything else would be a guess."
            )
        rows = []
        for key, stock in self._stocks.docs.items():
            product = self._ferts.docs.get(stock.get("fertilizer_key"))
            rows.append(
                {
                    "key": key,
                    "stored": stock.get("tenant_key"),
                    "product_found": product is not None,
                    "owner": product.get("tenant_key") if product else None,
                }
            )
        return rows


class _Db:
    def __init__(self, stocks: _Collection, ferts: _Collection) -> None:
        self._cols = {_STOCKS: stocks, _FERTS: ferts}
        self.aql = _Aql(stocks, ferts)

    def has_collection(self, name: str) -> bool:
        return name in self._cols

    def collection(self, name: str) -> _Collection:
        return self._cols[name]


def _db(stocks: dict[str, dict], ferts: dict[str, dict]) -> _Db:
    return _Db(_Collection(stocks), _Collection(ferts))


@pytest.fixture
def migration() -> AttributeFertilizerStocksMigration:
    return AttributeFertilizerStocksMigration()


class TestAttribution:
    def test_a_stock_inherits_its_products_tenant(self, migration) -> None:
        db = _db(
            {"s1": {"fertilizer_key": "f1"}},
            {"f1": {"tenant_key": "tenant-a"}},
        )

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 1
        assert db.collection(_STOCKS).docs["s1"]["tenant_key"] == "tenant-a"

    def test_a_stock_on_a_global_product_is_left_unstamped_and_named(self, migration) -> None:
        """No owner to derive — only one to invent."""
        db = _db(
            {"s1": {"fertilizer_key": "f-global"}},
            {"f-global": {"tenant_key": ""}},
        )

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["on_global_product_left_unstamped"] == ["s1"]
        assert db.collection(_STOCKS).docs["s1"].get("tenant_key") is None

    def test_a_temp_row_counts_as_orphaned_not_as_global(self, migration) -> None:
        """The pre-#1265 corruption. Repairing it would mean guessing which
        product it belonged to, and that field was the one overwritten."""
        db = _db(
            {"s1": {"fertilizer_key": "temp"}},
            {"f1": {"tenant_key": "tenant-a"}},
        )

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details["orphaned_left_unstamped"] == ["s1"]
        assert report.details["on_global_product_left_unstamped"] == []

    def test_the_two_residues_are_reported_separately(self, migration) -> None:
        """Collapsing them would hide which rows an operator can actually fix."""
        db = _db(
            {
                "s-ok": {"fertilizer_key": "f1"},
                "s-global": {"fertilizer_key": "f-global"},
                "s-temp": {"fertilizer_key": "temp"},
            },
            {"f1": {"tenant_key": "tenant-a"}, "f-global": {"tenant_key": ""}},
        )

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.scanned == 3
        assert report.details["attributed"] == 1
        assert report.details["on_global_product_left_unstamped"] == ["s-global"]
        assert report.details["orphaned_left_unstamped"] == ["s-temp"]


class TestDiscipline:
    def test_a_dry_run_writes_nothing_but_reports_the_same_plan(self, migration) -> None:
        db = _db({"s1": {"fertilizer_key": "f1"}}, {"f1": {"tenant_key": "tenant-a"}})

        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["attributed"] == 1
        assert db.collection(_STOCKS).updates == []

    def test_a_second_run_changes_nothing(self, migration) -> None:
        db = _db({"s1": {"fertilizer_key": "f1"}}, {"f1": {"tenant_key": "tenant-a"}})
        migration.up(db)  # type: ignore[arg-type]

        second = migration.up(db)  # type: ignore[arg-type]

        assert second.changed == 0

    def test_an_absent_collection_is_not_an_error(self, migration) -> None:
        class _Empty:
            aql = None

            def has_collection(self, name: str) -> bool:
                return False

        report = migration.up(_Empty())  # type: ignore[arg-type]

        assert report.scanned == 0
        assert report.changed == 0

    def test_it_declares_itself_irreversible(self, migration) -> None:
        """The pre-migration state is 'no attribute at all', indistinguishable
        afterwards from a deliberate empty stamp."""
        assert migration.reversible is False
