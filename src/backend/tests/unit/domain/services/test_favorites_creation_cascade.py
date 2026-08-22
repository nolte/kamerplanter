"""Creation cascades wherever removal cleans up (#1233).

`remove_favorite` has honoured `cascade_cleanup` since REQ-020 v1.5, so removing
a nutrient-plan favourite also removes the fertilizer favourites it produced.
Creation did not: `add_favorite` wrote a single edge, and the only caller that
cascaded was the onboarding wizard, by hand. `POST /favorites` with a
nutrient-plan key therefore produced no fertilizer favourites at all — removal
cleaned up something creation could no longer create.

These tests use a capturing fake db rather than a live ArangoDB, for the same
reason the sibling resolution tests do. The double is deliberately built so it
can FAIL: it answers `has` only for keys actually placed in a collection, and
its AQL stub returns only what the query was given. A double that answered every
key would let a broken `_resolve_collection` pass.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.domain.services.favorites_service import FavoritesService


class _FakeCollection:
    def __init__(
        self, present: set[str], sink: list[dict] | None = None, tenants: dict[str, str] | None = None
    ) -> None:
        self._present = present
        self._sink = sink
        self._tenants = tenants or {}

    def has(self, key: str) -> bool:
        return key in self._present

    def get(self, key: str) -> dict | None:
        """Serve the document `_verify_target_tenant_access` reads.

        Returns the real shape — a `tenant_key` the predicate can reject — so
        the double cannot certify a target the product would refuse. Absent from
        `_present` means absent, which is what a 404 is built from.
        """
        if key not in self._present:
            return None
        return {"_key": key, "tenant_key": self._tenants.get(key, "")}

    def insert(self, doc: dict, return_new: bool = False) -> dict:  # noqa: FBT001,FBT002
        if self._sink is not None:
            self._sink.append(doc)
        return {"new": doc}

    def update(self, doc: dict) -> dict:
        return doc


class _FakeAql:
    """Answers the two queries the service issues, and nothing else.

    The plan->fertilizer traversal returns whatever `plan_fertilizers` holds for
    the bound `plan_key`; the edge-existence query returns from `edges`. An
    unrecognised query raises, so a test cannot pass by accident on a query the
    double never anticipated.
    """

    def __init__(self, plan_fertilizers: dict[str, list[str]], edges: list[dict]) -> None:
        self._plan_fertilizers = plan_fertilizers
        self._edges = edges

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None) -> list:
        bind_vars = bind_vars or {}
        if "plan_uses_fertilizer" in query:
            return list(self._plan_fertilizers.get(bind_vars["plan_key"], []))
        if "user_favorites" in query and "FILTER e._from" in query:
            return [
                e for e in self._edges if e["_from"] == bind_vars.get("from_id") and e["_to"] == bind_vars.get("to_id")
            ]
        raise AssertionError(f"unexpected query: {query[:80]}")


class _FakeDb:
    def __init__(
        self,
        membership: dict[str, set[str]],
        *,
        plan_fertilizers: dict[str, list[str]] | None = None,
        existing_edges: list[dict] | None = None,
        tenants: dict[str, str] | None = None,
    ) -> None:
        self._membership = membership
        self._tenants = tenants or {}
        self.inserted: list[dict] = []
        self._edges = existing_edges or []
        self.aql = _FakeAql(plan_fertilizers or {}, self._edges)

    def collection(self, name: str) -> _FakeCollection:
        sink = self.inserted if name == col.USER_FAVORITES else None
        return _FakeCollection(self._membership.get(name, set()), sink, self._tenants)


def _service(db: _FakeDb) -> FavoritesService:
    return FavoritesService(db)  # type: ignore[arg-type]


def _targets(db: _FakeDb) -> list[str]:
    return [d["_to"] for d in db.inserted]


class TestCreationCascade:
    def test_favouriting_a_plan_also_favourites_its_fertilizers(self) -> None:
        db = _FakeDb(
            {col.NUTRIENT_PLANS: {"plan-1"}, col.FERTILIZERS: {"fert-a", "fert-b"}},
            plan_fertilizers={"plan-1": ["fert-a", "fert-b"]},
        )

        _service(db).add_favorite("u1", "plan-1", tenant_key="")

        assert _targets(db) == [
            f"{col.NUTRIENT_PLANS}/plan-1",
            f"{col.FERTILIZERS}/fert-a",
            f"{col.FERTILIZERS}/fert-b",
        ]

    def test_the_cascaded_edges_carry_their_origin(self) -> None:
        """`cascade_from_key` is what `_cleanup_cascade` matches on to remove them."""
        db = _FakeDb(
            {col.NUTRIENT_PLANS: {"plan-1"}, col.FERTILIZERS: {"fert-a"}},
            plan_fertilizers={"plan-1": ["fert-a"]},
        )

        _service(db).add_favorite("u1", "plan-1", tenant_key="")

        cascaded = [d for d in db.inserted if d["_to"].startswith(f"{col.FERTILIZERS}/")]
        assert [(d["source"], d["cascade_from_key"]) for d in cascaded] == [("cascade", "plan-1")]

    def test_favouriting_a_species_cascades_nothing(self) -> None:
        db = _FakeDb({col.SPECIES: {"tomato"}}, plan_fertilizers={"tomato": ["fert-a"]})

        _service(db).add_favorite("u1", "tomato", tenant_key="")

        assert _targets(db) == [f"{col.SPECIES}/tomato"]

    def test_re_favouriting_an_existing_plan_edge_backfills_its_fertilizers(self) -> None:
        """The migration case: a plan favourited before #1233 never cascaded."""
        existing = {"_from": f"{col.USERS}/u1", "_to": f"{col.NUTRIENT_PLANS}/plan-1", "source": "manual"}
        db = _FakeDb(
            {col.NUTRIENT_PLANS: {"plan-1"}, col.FERTILIZERS: {"fert-a"}},
            plan_fertilizers={"plan-1": ["fert-a"]},
            existing_edges=[existing],
        )

        _service(db).add_favorite("u1", "plan-1", tenant_key="")

        # No second plan edge — but the fertilizer it never had is now there.
        assert _targets(db) == [f"{col.FERTILIZERS}/fert-a"]

    def test_an_old_edge_without_target_type_still_cascades(self) -> None:
        """The stored field is not trusted; the resolved collection is.

        Edges written before `target_type` existed carry none. Reading the
        cascade decision off the document would silently skip exactly the
        records the backfill above is for.
        """
        existing = {"_from": f"{col.USERS}/u1", "_to": f"{col.NUTRIENT_PLANS}/plan-1", "source": "manual"}
        assert "target_type" not in existing
        db = _FakeDb(
            {col.NUTRIENT_PLANS: {"plan-1"}, col.FERTILIZERS: {"fert-a"}},
            plan_fertilizers={"plan-1": ["fert-a"]},
            existing_edges=[existing],
        )

        edge = _service(db).add_favorite("u1", "plan-1", tenant_key="")

        assert edge["target_type"] == col.NUTRIENT_PLANS
        assert _targets(db) == [f"{col.FERTILIZERS}/fert-a"]

    def test_a_cascade_cannot_re_enter_one(self) -> None:
        """Structural, not data-dependent.

        `cascade_fertilizers` calls the non-cascading primitive, so this holds
        even in the impossible arrangement where a fertilizer key ALSO resolves
        as a plan. Wiring that arrangement is the point: with the cascade calling
        `add_favorite`, this test recurses until the recursion limit.
        """
        db = _FakeDb(
            {col.NUTRIENT_PLANS: {"plan-1", "fert-a"}, col.FERTILIZERS: {"fert-a"}},
            plan_fertilizers={"plan-1": ["fert-a"], "fert-a": ["fert-a"]},
        )

        _service(db).add_favorite("u1", "plan-1", tenant_key="")

        assert _targets(db) == [f"{col.NUTRIENT_PLANS}/plan-1", f"{col.NUTRIENT_PLANS}/fert-a"]


class TestSubstrateTarget:
    def test_a_substrate_key_resolves(self) -> None:
        """Substrates are favouritable in the UI and were not a server-side target."""
        db = _FakeDb({col.SUBSTRATES: {"biobizz-lightmix"}})

        assert _service(db)._resolve_collection("biobizz-lightmix") == col.SUBSTRATES

    def test_substrates_are_a_tenant_owned_catalogue(self) -> None:
        """`Substrate` carries a `tenant_key`, so it needs the same predicate as
        nutrient plans and fertilizers — otherwise a foreign tenant's substrate
        would be favouritable while a foreign plan is not."""
        from app.domain.services.favorites_service import _TENANT_OWNED_CATALOG_COLLECTIONS

        assert col.SUBSTRATES in _TENANT_OWNED_CATALOG_COLLECTIONS


class TestTheDoubleCanRefuse:
    """A double that accepts everything certifies nothing.

    The tenant predicate is the one rule these fakes could most easily paper
    over, so it gets an explicit negative: a substrate owned by ANOTHER tenant
    must raise, through the same `_FakeCollection.get` the positive tests use.
    """

    def test_a_foreign_tenants_substrate_is_refused(self) -> None:
        import pytest

        from app.common.exceptions import NotFoundError

        db = _FakeDb({col.SUBSTRATES: {"their-mix"}}, tenants={"their-mix": "tenant-b"})

        with pytest.raises(NotFoundError):
            _service(db).add_favorite("u1", "their-mix", tenant_key="tenant-a")

        assert db.inserted == []

    def test_an_own_tenants_substrate_is_accepted(self) -> None:
        db = _FakeDb({col.SUBSTRATES: {"our-mix"}}, tenants={"our-mix": "tenant-a"})

        _service(db).add_favorite("u1", "our-mix", tenant_key="tenant-a")

        assert _targets(db) == [f"{col.SUBSTRATES}/our-mix"]
