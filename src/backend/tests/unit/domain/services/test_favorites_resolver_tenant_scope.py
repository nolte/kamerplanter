"""The favourite-target resolver carries the tenant predicate (#1538).

``FavoritesService._resolve_collection`` used to ask each catalogue
``collection.has(key)`` — a question about the *collection*, not about the
*caller*. Two consequences, both measured on ``develop`` @ ea596dd34:

* ``species`` carries a ``tenant_key`` since #808 (REQ-001 v4.0) but was not in
  ``_TENANT_OWNED_CATALOG_COLLECTIONS``, whose comment still claimed species were
  "purely global". A foreign tenant's private species was therefore genuinely
  favouritable — a cross-tenant write, not merely a side channel.
* For the catalogues that *were* guarded, resolution still succeeded on a foreign
  row and the refusal came from a second, later check, so the two refusal arms
  stayed two code paths with equal output. Scoping the resolution itself makes
  them one path.

The #324 direction is the counterweight and is asserted just as hard: a global
seed (``tenant_key == ""``), an own-tenant row, and a row explicitly **granted**
to the caller (#1092) must all stay favouritable. A strict
``tenant_key == caller`` filter passes the leak tests and fails these.

A capturing fake db stands in for ArangoDB. Its ``get`` returns the real row
shape (including ``tenant_key``); the grant edge is only reported for a genuinely
stored grant; the favourite edges it holds are real edge documents, so a removal
has to address the same ``_to`` the creation wrote. It deliberately does **not**
answer ``has``: the production code no longer calls it, and a double that answers
a method nothing calls invites a test to pass through a path the product does not
take. The red-first run quoted in the PR used a ``has``-capable variant of this
same double against the pre-fix code; it is not needed to keep the suite honest
going forward (review finding SCR-009).
"""

from __future__ import annotations

from typing import Any

import pytest
from arango.exceptions import DocumentGetError
from arango.request import Request
from arango.response import Response

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.domain.services.favorites_service import FavoritesService
from tests.support.onboarding_wiring import build_favorites_service

CALLER_TENANT = "tenant-alice"
FOREIGN_TENANT = "tenant-bob"


class _FakeCollection:
    def __init__(self, name: str, rows: dict[str, dict], inserted: list[dict]) -> None:
        self._name = name
        self._rows = rows
        self._inserted = inserted

    def get(self, key: str) -> dict | None:
        return self._rows.get(key)

    def insert(self, doc: dict, return_new: bool = False) -> dict:  # noqa: FBT001,FBT002
        self._inserted.append(doc)
        return {"new": doc} if return_new else {}

    def update(self, doc: dict) -> dict:
        return doc


class _FakeAql:
    """Answers the grant probe and the favourite-edge queries, nothing else.

    An unanticipated query raises, so a test cannot pass on a query the double
    never modelled. The removal query is matched the way the product writes it —
    on the **key parsed out of the stored** ``_to`` — so a removal that addressed
    a different collection than the creation wrote would return nothing here,
    exactly as it would against ArangoDB (review finding SCR-001).
    """

    def __init__(self, grants: set[tuple[str, str]], edges: list[dict]) -> None:
        self._grants = grants
        self._edges = edges

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None) -> Any:
        bind_vars = bind_vars or {}
        if col.TENANT_HAS_ACCESS in query:
            return iter([1] if (bind_vars.get("f"), bind_vars.get("t")) in self._grants else [])
        if "user_favorites" in query and "cascade_from_key" in query:
            removed = [
                e
                for e in self._edges
                if e["_from"] == bind_vars.get("from_id")
                and e.get("source") == "cascade"
                and e.get("cascade_from_key") == bind_vars.get("plan_key")
            ]
            for edge in removed:
                self._edges.remove(edge)
            return iter(removed)
        if "user_favorites" in query and "REMOVE" in query:
            removed = [
                e
                for e in self._edges
                if e["_from"] == bind_vars.get("from_id") and e["_to"].split("/", 1)[-1] == bind_vars.get("target_key")
            ]
            for edge in removed:
                self._edges.remove(edge)
            return iter(removed)
        if "user_favorites" in query:
            return iter(
                e for e in self._edges if e["_from"] == bind_vars.get("from_id") and e["_to"] == bind_vars.get("to_id")
            )
        if "plan_uses_fertilizer" in query:
            return iter([])
        raise AssertionError(f"unexpected query: {query[:80]}")


class _FakeDb:
    def __init__(
        self,
        rows_by_collection: dict[str, dict[str, dict]],
        *,
        grants: set[tuple[str, str]] | None = None,
        edges: list[dict] | None = None,
    ) -> None:
        self._rows = rows_by_collection
        # One list, shared with the AQL double on purpose: an edge the service
        # inserts is immediately visible to the queries that read and remove
        # edges, so an add-then-remove test measures the real round trip instead
        # of two disconnected fakes (review finding SCR-001).
        self.inserted_edges: list[dict] = edges if edges is not None else []
        self.aql = _FakeAql(grants or set(), self.inserted_edges)

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(name, self._rows.get(name, {}), self.inserted_edges)


def _service(
    rows_by_collection: dict[str, dict[str, dict]],
    *,
    grants: set[tuple[str, str]] | None = None,
    edges: list[dict] | None = None,
) -> tuple[FavoritesService, _FakeDb]:
    db = _FakeDb(rows_by_collection, grants=grants, edges=edges)
    return build_favorites_service(db), db  # type: ignore[arg-type]


# ── The leak: a foreign tenant's row must not be favouritable ──────────────────


def test_foreign_tenant_species_is_not_favouritable() -> None:
    """RED before #1538: species was missing from the tenant-owned set.

    ``Species.tenant_key`` exists since #808, so a tenant-private species is a
    real row a foreign caller could favourite. The pre-fix service wrote the edge
    and returned it.
    """
    service, db = _service({col.SPECIES: {"sp-foreign": {"_key": "sp-foreign", "tenant_key": FOREIGN_TENANT}}})

    with pytest.raises(NotFoundError):
        service.add_favorite("user-1", "sp-foreign", tenant_key=CALLER_TENANT)

    assert db.inserted_edges == []


def test_resolver_does_not_resolve_a_foreign_row() -> None:
    """The decision itself is tenant-scoped, not a later second check.

    Asserts the very expression the rule is about: resolution of a foreign row
    yields nothing, so the "unresolvable" and "foreign" arms are one path.
    """
    service, _ = _service(
        {col.NUTRIENT_PLANS: {"plan-foreign": {"_key": "plan-foreign", "tenant_key": FOREIGN_TENANT}}}
    )

    assert service._resolve_collection("plan-foreign", tenant_key=CALLER_TENANT) is None


# ── The counterweight (#324): global, own and granted rows stay favouritable ──


def test_global_species_stays_favouritable() -> None:
    service, db = _service({col.SPECIES: {"tomato": {"_key": "tomato", "tenant_key": ""}}})

    edge = service.add_favorite("user-1", "tomato", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.SPECIES}/tomato"
    assert len(db.inserted_edges) == 1


def test_species_row_without_a_tenant_key_field_stays_favouritable() -> None:
    """Seed rows written before #808 carry no ``tenant_key`` field at all.

    A missing field and a null one both mean "global" in the hybrid-catalogue
    union; a predicate that only knows ``== ""`` would blank them.
    """
    service, db = _service({col.SPECIES: {"basil": {"_key": "basil"}}})

    edge = service.add_favorite("user-1", "basil", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.SPECIES}/basil"
    assert len(db.inserted_edges) == 1


def test_own_tenant_species_stays_favouritable() -> None:
    service, db = _service({col.SPECIES: {"sp-own": {"_key": "sp-own", "tenant_key": CALLER_TENANT}}})

    edge = service.add_favorite("user-1", "sp-own", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.SPECIES}/sp-own"
    assert len(db.inserted_edges) == 1


def test_granted_species_stays_favouritable() -> None:
    """#1092: an explicit grant is the third way in, and it must survive the fix.

    This is the test a *too strict* repair fails: the row is owned by a foreign
    tenant, so an ownership-only predicate hides it — but its owner shared it, and
    ``SpeciesService.get_species`` lets the recipient read it.
    """
    service, db = _service(
        {col.SPECIES: {"sp-shared": {"_key": "sp-shared", "tenant_key": FOREIGN_TENANT}}},
        grants={(f"{col.TENANTS}/{CALLER_TENANT}", f"{col.SPECIES}/sp-shared")},
    )

    edge = service.add_favorite("user-1", "sp-shared", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.SPECIES}/sp-shared"
    assert len(db.inserted_edges) == 1


def test_a_grant_to_another_tenant_does_not_admit_the_caller() -> None:
    """The grant arm is addressed to one tenant, not to everyone."""
    service, db = _service(
        {col.SPECIES: {"sp-shared": {"_key": "sp-shared", "tenant_key": FOREIGN_TENANT}}},
        grants={(f"{col.TENANTS}/tenant-carol", f"{col.SPECIES}/sp-shared")},
    )

    with pytest.raises(NotFoundError):
        service.add_favorite("user-1", "sp-shared", tenant_key=CALLER_TENANT)

    assert db.inserted_edges == []


def test_global_botanical_family_stays_favouritable() -> None:
    """Botanical families carry no ownership marker at all and stay unguarded."""
    service, db = _service({col.BOTANICAL_FAMILIES: {"solanaceae": {"_key": "solanaceae"}}})

    edge = service.add_favorite("user-1", "solanaceae", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.BOTANICAL_FAMILIES}/solanaceae"
    assert len(db.inserted_edges) == 1


def test_global_nutrient_plan_stays_favouritable() -> None:
    service, db = _service({col.NUTRIENT_PLANS: {"plan-global": {"_key": "plan-global", "tenant_key": ""}}})

    edge = service.add_favorite("user-1", "plan-global", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.NUTRIENT_PLANS}/plan-global"
    assert len(db.inserted_edges) == 1


def test_resolver_resolves_a_global_row() -> None:
    service, _ = _service({col.SUBSTRATES: {"coco": {"_key": "coco", "tenant_key": ""}}})

    assert service._resolve_collection("coco", tenant_key=CALLER_TENANT) == col.SUBSTRATES


def test_resolution_continues_past_a_foreign_row_into_a_visible_one() -> None:
    """A foreign row shadowing a visible one of the same key must not end the search.

    Keys are unique per collection, not across them; ``_resolve_collection`` walks
    six collections in order. If a foreign hit *stopped* the walk, a visible row
    further down would become unfavouritable — over-strictness by control flow
    rather than by predicate.
    """
    service, _ = _service(
        {
            col.SPECIES: {"shared-key": {"_key": "shared-key", "tenant_key": FOREIGN_TENANT}},
            col.SUBSTRATES: {"shared-key": {"_key": "shared-key", "tenant_key": ""}},
        }
    )

    assert service._resolve_collection("shared-key", tenant_key=CALLER_TENANT) == col.SUBSTRATES


# ── Error handling: a datastore failure is a 5xx, not a 404 ───────────────────


def _document_get_error(error_num: int, status_code: int, message: str) -> DocumentGetError:
    """Build the genuine driver exception, not a stand-in for it."""
    response = Response(
        method="get",
        url="http://arangodb:8529/_api/document/species/tomato",
        headers={},
        status_code=status_code,
        status_text=message,
        raw_body=f'{{"error":true,"errorNum":{error_num},"errorMessage":"{message}","code":{status_code}}}',
    )
    response.error_code = error_num
    response.error_message = message
    return DocumentGetError(response, Request(method="get", endpoint="/_api/document/species/tomato"))


def test_connection_failure_propagates_instead_of_becoming_a_404() -> None:
    """RED before #1538: ``except Exception: continue`` reported the DB outage as 404.

    python-arango raises ``ConnectionAbortedError`` when no host answers; the
    pre-fix loop swallowed it for every catalogue and ended in
    ``NotFoundError`` — a 404 that means "the database is down".
    """

    class _UnreachableDb(_FakeDb):
        def collection(self, name: str) -> _FakeCollection:
            raise ConnectionAbortedError("Can't connect to host(s) within limit (3)")

    db = _UnreachableDb({})
    service = build_favorites_service(db)

    with pytest.raises(ConnectionAbortedError):
        service.add_favorite("user-1", "tomato", tenant_key=CALLER_TENANT)


def test_a_server_error_on_one_catalogue_propagates() -> None:
    """Anything that is not "this catalogue does not exist" surfaces (5xx)."""

    class _FailingCollection(_FakeCollection):
        def get(self, key: str) -> dict | None:
            raise _document_get_error(11, 401, "not authorized to execute this request")

    class _FailingDb(_FakeDb):
        def collection(self, name: str) -> _FakeCollection:
            if name == col.SPECIES:
                return _FailingCollection(name, {}, self.inserted_edges)
            return super().collection(name)

    db = _FailingDb({})
    service = build_favorites_service(db)

    with pytest.raises(DocumentGetError):
        service.add_favorite("user-1", "tomato", tenant_key=CALLER_TENANT)


def test_a_missing_catalogue_is_skipped_and_the_walk_continues() -> None:
    """A collection that does not exist is not an error for *this* key.

    It is a deployment defect, so it is logged — but the remaining catalogues are
    still asked, and a key found in one of them still resolves.
    """

    class _AbsentCollection(_FakeCollection):
        def get(self, key: str) -> dict | None:
            raise _document_get_error(1203, 404, "collection or view not found")

    class _PartialDb(_FakeDb):
        def collection(self, name: str) -> _FakeCollection:
            if name == col.SPECIES:
                return _AbsentCollection(name, {}, self.inserted_edges)
            return super().collection(name)

    db = _PartialDb({col.SUBSTRATES: {"coco": {"_key": "coco", "tenant_key": ""}}})
    service = build_favorites_service(db)

    edge = service.add_favorite("user-1", "coco", tenant_key=CALLER_TENANT)

    assert edge["_to"] == f"{col.SUBSTRATES}/coco"


def test_an_unresolvable_key_is_still_a_404() -> None:
    service, db = _service({})

    with pytest.raises(NotFoundError) as error:
        service.add_favorite("user-1", "nowhere", tenant_key=CALLER_TENANT)

    assert error.value.details[0]["entity"] == "favorite_target"
    assert db.inserted_edges == []


# ── Removal stays permissive on purpose ──────────────────────────────────────


def test_removal_of_an_edge_to_a_foreign_row_still_works() -> None:
    """Removal must not trap an edge that leaked before this fix.

    The edge is anchored on the caller's own ``user_key``, so removal cannot leak
    across tenants — and applying the add-path predicate here would leave the
    user unable to clean up exactly the rows #1538 stops them from creating.
    """
    edge = {
        "_from": f"{col.USERS}/user-1",
        "_to": f"{col.SPECIES}/sp-foreign",
        "source": "manual",
    }
    service, _ = _service(
        {col.SPECIES: {"sp-foreign": {"_key": "sp-foreign", "tenant_key": FOREIGN_TENANT}}},
        edges=[edge],
    )

    assert service.remove_favorite("user-1", "sp-foreign") is True


def test_an_empty_caller_tenant_sees_only_global_rows() -> None:
    """Light mode / anonymous: no tenant owns a row and none holds a grant.

    ``tenant_key == ""`` must not accidentally match rows whose own
    ``tenant_key`` is empty *as an owner* while also admitting foreign ones — it
    collapses to the global arm, which is what ``SpeciesService.get_species``
    does for the same input.
    """
    service, _ = _service(
        {
            col.SPECIES: {
                "sp-global": {"_key": "sp-global", "tenant_key": ""},
                "sp-foreign": {"_key": "sp-foreign", "tenant_key": FOREIGN_TENANT},
            }
        },
        grants={(f"{col.TENANTS}/", f"{col.SPECIES}/sp-foreign")},
    )

    assert service._resolve_collection("sp-global", tenant_key="") == col.SPECIES
    assert service._resolve_collection("sp-foreign", tenant_key="") is None


def test_the_system_context_resolves_a_foreign_row() -> None:
    """``tenant_key=None`` means *no predicate*, and it has to really mean it.

    This is the double's honesty check in the other direction: if the fake rows
    were shaped so that nothing ever looked foreign, every leak test above would
    be vacuous. The same row that resolves to ``None`` for a tenant caller
    resolves normally without one.
    """
    service, _ = _service({col.SPECIES: {"sp-foreign": {"_key": "sp-foreign", "tenant_key": FOREIGN_TENANT}}})

    assert service._resolve_collection("sp-foreign", tenant_key=CALLER_TENANT) is None
    assert service._resolve_collection("sp-foreign", tenant_key=None) == col.SPECIES


# ── Review findings SCR-001 / SCR-005 / SCR-006 ──────────────────────────────


def test_add_and_remove_address_the_same_edge_when_a_key_exists_twice() -> None:
    """SCR-001: the two verbs must not answer different questions about one key.

    The add path deliberately walks past a row the caller cannot see and lands on
    the next visible one (``test_resolution_continues_past_a_foreign_row_into_a_visible_one``).
    A removal that re-resolved the key tenant-blind stopped at the *first*
    catalogue merely holding it — here the foreign species — and addressed
    ``species/shared-key`` while the creation had written
    ``substrates/shared-key``. The user could not remove the favourite they had
    just created. Removal now reads the stored edge instead of resolving.
    """
    service, db = _service(
        {
            col.SPECIES: {"shared-key": {"_key": "shared-key", "tenant_key": FOREIGN_TENANT}},
            col.SUBSTRATES: {"shared-key": {"_key": "shared-key", "tenant_key": ""}},
        }
    )

    edge = service.add_favorite("user-1", "shared-key", tenant_key=CALLER_TENANT)
    assert edge["_to"] == f"{col.SUBSTRATES}/shared-key"

    assert service.remove_favorite("user-1", "shared-key") is True
    assert db.inserted_edges == []


def test_removal_reports_false_when_no_edge_exists() -> None:
    """The permissive removal still distinguishes "removed" from "nothing there"."""
    service, _ = _service({col.SUBSTRATES: {"coco": {"_key": "coco", "tenant_key": ""}}})

    assert service.remove_favorite("user-1", "coco") is False


def test_a_grant_on_a_non_grantable_collection_does_not_admit_the_caller() -> None:
    """SCR-006a: ``_GRANTABLE_COLLECTIONS`` is a rule, so it needs a falsifier.

    ``tenant_has_access`` points only at species and cultivars; a grant edge
    aimed at a nutrient plan is not a thing the graph can hold. If the resolver
    probed grants for *every* tenant-owned catalogue, this stored grant would
    admit the caller to a foreign plan — and every other test would stay green.
    """
    service, db = _service(
        {col.NUTRIENT_PLANS: {"plan-foreign": {"_key": "plan-foreign", "tenant_key": FOREIGN_TENANT}}},
        grants={(f"{col.TENANTS}/{CALLER_TENANT}", f"{col.NUTRIENT_PLANS}/plan-foreign")},
    )

    with pytest.raises(NotFoundError):
        service.add_favorite("user-1", "plan-foreign", tenant_key=CALLER_TENANT)

    assert db.inserted_edges == []


def test_the_grantable_set_follows_the_graph_definition() -> None:
    """SCR-002: the set is derived from ``tenant_has_access``, not hand-listed."""
    from app.domain.services.favorites_service import (
        _FAVOURITABLE_COLLECTIONS,
        _GRANTABLE_COLLECTIONS,
    )

    definitions = [d for d in col.GRAPH_EDGE_DEFINITIONS if d["edge_collection"] == col.TENANT_HAS_ACCESS]
    assert len(definitions) == 1, "tenant_has_access must have exactly one edge definition to derive from"
    to_vertices = frozenset(definitions[0]["to_vertex_collections"])

    assert frozenset(to_vertices) & frozenset(_FAVOURITABLE_COLLECTIONS) == _GRANTABLE_COLLECTIONS
    assert col.SPECIES in _GRANTABLE_COLLECTIONS
    assert col.CULTIVARS in to_vertices and col.CULTIVARS not in _GRANTABLE_COLLECTIONS


def test_a_missing_catalogue_does_not_swallow_a_row_in_another_one() -> None:
    """SCR-006c: the 1203 skip is per-catalogue, not a verdict on the key.

    An absent collection must not end the walk, and it must not make a key that
    only *it* could have held resolve to something else. Both halves are asserted
    on the same db so the skip cannot be green for the wrong reason.
    """

    class _AbsentCollection(_FakeCollection):
        def get(self, key: str) -> dict | None:
            raise _document_get_error(1203, 404, "collection or view not found")

    class _PartialDb(_FakeDb):
        def collection(self, name: str) -> _FakeCollection:
            if name == col.SPECIES:
                return _AbsentCollection(name, {}, self.inserted_edges)
            return super().collection(name)

    db = _PartialDb({col.SUBSTRATES: {"coco": {"_key": "coco", "tenant_key": ""}}})
    service = build_favorites_service(db)

    assert service._resolve_collection("coco", tenant_key=CALLER_TENANT) == col.SUBSTRATES
    assert service._resolve_collection("only-in-the-absent-one", tenant_key=CALLER_TENANT) is None


def test_a_document_handle_is_not_a_key_and_does_not_resolve() -> None:
    """SCR-005: ``species/tomato`` is a handle, and the driver accepts it.

    ``collection("species").get("species/tomato")`` returns the real row — the
    prefix matches, so ``_validate_id`` passes it — and ``_add_one`` then builds
    ``_to = "species/species/tomato"``, which ArangoDB rejects with
    ``[HTTP 400][ERR 1233]``: a 500 for malformed client input. Measured against a
    live ArangoDB; pre-existing (``has()`` behaved the same), refused here because
    this is the one place both verbs pass through.
    """

    class _HandleTolerantCollection(_FakeCollection):
        def get(self, key: str) -> dict | None:
            # The driver's behaviour, not a convenience: a handle whose prefix is
            # this collection resolves to the row.
            return self._rows.get(key.split("/", 1)[-1] if key.startswith(f"{self._name}/") else key)

    class _HandleTolerantDb(_FakeDb):
        def collection(self, name: str) -> _FakeCollection:
            return _HandleTolerantCollection(name, self._rows.get(name, {}), self.inserted_edges)

    db = _HandleTolerantDb({col.SPECIES: {"tomato": {"_key": "tomato", "tenant_key": ""}}})
    service = build_favorites_service(db)

    # The double proves it would have resolved without the guard …
    assert db.collection(col.SPECIES).get("species/tomato") is not None
    # … and the guard is what stops it.
    assert service._resolve_collection("species/tomato", tenant_key=CALLER_TENANT) is None

    with pytest.raises(NotFoundError):
        service.add_favorite("user-1", "species/tomato", tenant_key=CALLER_TENANT)

    assert db.inserted_edges == []
