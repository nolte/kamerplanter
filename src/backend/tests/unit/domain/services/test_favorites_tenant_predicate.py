"""Favourites tenant predicate on the write path (#965 item 2).

Favourites are personal and span tenants (product decision): a user may
favourite a **global** catalogue entry (``tenant_key == ""``) or one owned by
their **own** (active) tenant, but never a **foreign** tenant's entry. This is
the #324-safe direction — the global catalogue must stay favouritable, so a
strict ``tenant_key == caller`` filter that hides global rows is the regression
we guard against.

The predicate applies to tenant-owned catalogues (``species`` since #1538,
``nutrient_plans``, ``fertilizers``, ``activities``, ``substrates``);
``botanical_families`` carries no ownership field and is unaffected. Since #1538
the predicate lives inside ``_resolve_collection`` — a row the caller may not see
does not resolve — so these tests exercise one code path, not two with equal
output. The three-arm visibility union (own ∪ global ∪ granted) has its own
suite in ``test_favorites_resolver_tenant_scope.py``.

Uses a capturing fake db (no live ArangoDB): ``collection(name).get(key)``
returns the stored row (with its ``tenant_key``) and drives both resolution and
the predicate; inserted favourite edges are captured so a *refused* favourite can
be proven to write **no** edge.
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
    # A seeded species row carries no tenant_key field (or an empty one) → the
    # global arm of the union admits it. Species became tenant-owned in #808 and
    # joined the guarded set in #1538; the seeded catalogue must stay favouritable
    # (#324), which is what this asserts.
    service, db = _service({col.SPECIES: {"tomato": {"_key": "tomato"}}})

    edge = service.add_favorite("user-1", "tomato", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.SPECIES}/tomato"
    assert len(db.inserted_edges) == 1


def test_favorite_unresolvable_key_is_a_404_not_a_500() -> None:
    # SEC-002: a key that matches no collection at all used to raise ValueError →
    # 500, distinguishable from a foreign-tenant row's 404 — a cross-tenant
    # existence oracle. It must now answer the same NotFoundError (404).
    service, db = _service({})  # no collection carries the key

    with pytest.raises(NotFoundError):
        service.add_favorite("user-1", "does-not-exist-anywhere", tenant_key=CALLER_TENANT)

    assert db.inserted_edges == []


def test_a_foreign_row_and_an_unknown_key_publish_the_same_entity() -> None:
    """The two refusals must be indistinguishable in ``details[0].entity`` (#1465).

    SEC-002 collapsed them in the *message*; #1437 then made ``entity`` the field
    a client is told to branch on, and #1465 made its values stable. Naming the
    resolved catalogue here would hand that oracle straight back: ``nutrient_plan``
    would mean "this key exists in some tenant", ``favorite_target`` would mean "it
    exists nowhere".

    Since #1538 the two arms are the same code path — ``_resolve_collection``
    carries the tenant predicate, so a foreign row resolves to nothing exactly as
    an unknown key does. This test stays as the guard on the *published* field:
    it is what a future resolver change would have to keep true.
    """
    foreign, _ = _service(
        {col.NUTRIENT_PLANS: {"plan-foreign": {"_key": "plan-foreign", "tenant_key": FOREIGN_TENANT}}}
    )
    unknown, _ = _service({})

    with pytest.raises(NotFoundError) as foreign_error:
        foreign.add_favorite("user-1", "plan-foreign", tenant_key=CALLER_TENANT)
    with pytest.raises(NotFoundError) as unknown_error:
        unknown.add_favorite("user-1", "plan-foreign", tenant_key=CALLER_TENANT)

    assert foreign_error.value.details[0]["entity"] == "favorite_target"
    assert unknown_error.value.details[0]["entity"] == "favorite_target"
    assert foreign_error.value.details[0] == unknown_error.value.details[0]
