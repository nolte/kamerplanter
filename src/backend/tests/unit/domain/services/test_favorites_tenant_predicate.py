"""Favourites tenant predicate on the write path (#965 item 2).

Favourites are personal and span tenants (product decision): a user may
favourite a **global** catalogue entry (``tenant_key == ""``) or one owned by
their **own** (active) tenant, but never a **foreign** tenant's entry. This is
the #324-safe direction — the global catalogue must stay favouritable, so a
strict ``tenant_key == caller`` filter that hides global rows is the regression
we guard against.

The predicate applies only to tenant-owned catalogues
(``nutrient_plans``, ``fertilizers``, ``activities``); purely global collections
(``species``, ``botanical_families``) carry no ``tenant_key`` and are unaffected.

Uses a capturing fake db (no live ArangoDB): ``collection(name).has(key)``
drives ``_resolve_collection``; ``collection(name).get(key)`` returns the stored
row (with its ``tenant_key``) for the predicate; inserted favourite edges are
captured so a *refused* favourite can be proven to write **no** edge.
"""

from __future__ import annotations

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.domain.services.favorites_service import FavoritesService

CALLER_TENANT = "tenant-alice"
FOREIGN_TENANT = "tenant-bob"


class _FakeCollection:
    def __init__(self, name: str, rows: dict[str, dict], inserted: list[dict]) -> None:
        self._name = name
        self._rows = rows
        self._inserted = inserted

    def has(self, key: str) -> bool:
        return key in self._rows

    def get(self, key: str) -> dict | None:
        return self._rows.get(key)

    def insert(self, doc: dict, return_new: bool = False) -> dict:
        self._inserted.append(doc)
        return {"new": doc} if return_new else {}

    def update(self, doc: dict) -> dict:
        return doc


class _FakeAql:
    """Only the add_favorite existence probe runs here; no edge pre-exists."""

    def execute(self, query: str, bind_vars: dict | None = None):
        return iter([])


class _FakeDb:
    def __init__(self, rows_by_collection: dict[str, dict[str, dict]]) -> None:
        self._rows = rows_by_collection
        self.inserted_edges: list[dict] = []
        self.aql = _FakeAql()

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(name, self._rows.get(name, {}), self.inserted_edges)


def _service(rows_by_collection: dict[str, dict[str, dict]]) -> tuple[FavoritesService, _FakeDb]:
    db = _FakeDb(rows_by_collection)
    return FavoritesService(db), db  # type: ignore[arg-type]


def test_favorite_global_hybrid_entry_succeeds() -> None:
    # #324 counter-example: a global catalogue row (tenant_key == "") must stay
    # favouritable — the regression we must never reintroduce.
    service, db = _service({col.NUTRIENT_PLANS: {"plan-global": {"_key": "plan-global", "tenant_key": ""}}})

    edge = service.add_favorite("user-1", "plan-global", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.NUTRIENT_PLANS}/plan-global"
    assert len(db.inserted_edges) == 1


def test_favorite_own_tenant_hybrid_entry_succeeds() -> None:
    service, db = _service({col.FERTILIZERS: {"fert-own": {"_key": "fert-own", "tenant_key": CALLER_TENANT}}})

    edge = service.add_favorite("user-1", "fert-own", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.FERTILIZERS}/fert-own"
    assert len(db.inserted_edges) == 1


def test_favorite_foreign_tenant_hybrid_entry_is_refused_and_writes_no_edge() -> None:
    service, db = _service(
        {col.NUTRIENT_PLANS: {"plan-foreign": {"_key": "plan-foreign", "tenant_key": FOREIGN_TENANT}}}
    )

    with pytest.raises(NotFoundError):
        service.add_favorite("user-1", "plan-foreign", tenant_key=CALLER_TENANT)

    assert db.inserted_edges == []


def test_favorite_foreign_tenant_fertilizer_is_refused_and_writes_no_edge() -> None:
    service, db = _service({col.FERTILIZERS: {"fert-foreign": {"_key": "fert-foreign", "tenant_key": FOREIGN_TENANT}}})

    with pytest.raises(NotFoundError):
        service.add_favorite("user-1", "fert-foreign", tenant_key=CALLER_TENANT)

    assert db.inserted_edges == []


def test_favorite_foreign_tenant_activity_is_refused() -> None:
    # activities also carry Activity.tenant_key, so the same leak applied to them
    # and is closed the same way (beyond the two catalogues named in #965).
    service, db = _service({col.ACTIVITIES: {"act-foreign": {"_key": "act-foreign", "tenant_key": FOREIGN_TENANT}}})

    with pytest.raises(NotFoundError):
        service.add_favorite("user-1", "act-foreign", tenant_key=CALLER_TENANT)

    assert db.inserted_edges == []


def test_favorite_global_species_still_works() -> None:
    # species carry no tenant_key at all → predicate is skipped, non-hybrid path
    # is unaffected.
    service, db = _service({col.SPECIES: {"tomato": {"_key": "tomato"}}})

    edge = service.add_favorite("user-1", "tomato", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.SPECIES}/tomato"
    assert len(db.inserted_edges) == 1


def test_favorite_hybrid_entry_missing_row_is_refused() -> None:
    # _resolve_collection matched via has(), but the row cannot be re-read →
    # NotFoundError rather than a silent write against a phantom target.
    class _MissingRowCollection(_FakeCollection):
        def has(self, key: str) -> bool:  # noqa: ARG002 — force resolution to this collection
            return True

        def get(self, key: str) -> dict | None:  # noqa: ARG002
            return None

    class _MissingRowDb(_FakeDb):
        def collection(self, name: str) -> _FakeCollection:
            if name == col.NUTRIENT_PLANS:
                return _MissingRowCollection(name, {}, self.inserted_edges)
            return _FakeCollection(name, {}, self.inserted_edges)

    db = _MissingRowDb({})
    service = FavoritesService(db)  # type: ignore[arg-type]

    with pytest.raises(NotFoundError):
        service.add_favorite("user-1", "ghost-plan", tenant_key=CALLER_TENANT)

    assert db.inserted_edges == []
