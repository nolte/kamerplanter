"""Starter kits are offered on *visibility*, not on grants (#1178 regression).

`#1092` added the `tenant_has_access` edge and, with it, created the collection.
`StarterKitService` had been asking that collection for the tenant's granted
species; while it did not exist the lookup returned `None` and every kit was
shown. From the moment it existed the lookup returned an **empty set** — nobody
has been granted anything — and the filter kept only kits naming no species.

Every seeded kit names species. So the onboarding wizard showed **zero cards to
every tenant**, and the e2e-smoke lane went from seven consecutive greens to
failing on the merge commit itself and every run after.

The empty-set handling was not the mistake: "no grants" is a real answer, and an
absent store must never reveal more than a populated one. The mistake was
treating a grant as the *only* source of visibility. A grant is **additive** — it
opens a row the tenant could not otherwise see — and every starter-kit species is
global seed data that needs no grant at all.

These tests pin both directions. A test that only checked "a granted species makes
its kit visible" would pass against the broken version too.
"""

from __future__ import annotations

import pytest

from app.domain.services.starter_kit_service import StarterKitService

_GLOBAL_SPECIES = "sp_tomato"
_OWN_SPECIES = "sp_my_mint"
_GRANTED_SPECIES = "sp_shared_basil"
_FOREIGN_SPECIES = "sp_someone_elses"

_KITS = [
    {
        "kit_id": "balcony",
        "name": "Balkon",
        "difficulty": "beginner",
        "sort_order": 1,
        "species_keys": [_GLOBAL_SPECIES],
    },
    {"kit_id": "mine", "name": "Eigenes", "difficulty": "beginner", "sort_order": 2, "species_keys": [_OWN_SPECIES]},
    {
        "kit_id": "shared",
        "name": "Geteilt",
        "difficulty": "beginner",
        "sort_order": 3,
        "species_keys": [_GRANTED_SPECIES],
    },
    {
        "kit_id": "foreign",
        "name": "Fremd",
        "difficulty": "beginner",
        "sort_order": 4,
        "species_keys": [_FOREIGN_SPECIES],
    },
    {"kit_id": "speciesless", "name": "Ohne Arten", "difficulty": "beginner", "sort_order": 5, "species_keys": []},
]


class _Db:
    """Answers the visibility query from explicit fixtures.

    ``visible`` is what the *union* would return, so the double models the
    contract the service depends on rather than re-deriving the three arms — the
    service's job here is what it does with that answer.
    """

    def __init__(self, visible: set[str] | None, *, has_species: bool = True) -> None:
        self._visible = visible
        self._has_species = has_species
        self.queries: list[str] = []

    def has_collection(self, name: str) -> bool:
        return self._has_species if name == "species" else True

    def collection(self, name: str):  # pragma: no cover - unused by these paths
        raise AssertionError(f"unexpected collection access: {name}")

    class _Aql:
        def __init__(self, outer: _Db) -> None:
            self._outer = outer

        def execute(self, query: str, bind_vars: dict | None = None):
            self._outer.queries.append(query)
            if self._outer._visible is None:
                raise RuntimeError("species collection unreachable")
            return list(self._outer._visible)

    @property
    def aql(self) -> _Db._Aql:
        return _Db._Aql(self)


def _service(visible: set[str] | None, *, has_species: bool = True) -> StarterKitService:
    service = StarterKitService.__new__(StarterKitService)
    service._db = _Db(visible, has_species=has_species)
    service.list_kits = lambda difficulty=None: [_Kit(**k) for k in _KITS]  # type: ignore[method-assign]
    return service


class _Kit:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _ids(kits) -> list[str]:
    return [k.kit_id for k in kits]


# ── the regression itself ────────────────────────────────────────────────────


def test_a_tenant_with_no_grants_still_sees_the_seeded_kits() -> None:
    """The #1178 case, stated as the first test because it is the one that broke.

    A brand-new tenant has been granted nothing. Every starter-kit species is
    global seed data, so every kit must still be offered — an empty grant set is
    not an empty *visibility* set.
    """
    kits = _service({_GLOBAL_SPECIES}).list_kits_for_tenant("tenant_new")

    assert "balcony" in _ids(kits)


def test_the_wizard_is_never_empty_for_a_tenant_that_can_see_the_catalogue() -> None:
    """The user-visible symptom, asserted directly.

    The broken version returned exactly one kit — the species-less one — which is
    indistinguishable from "the catalogue failed to load" in the UI.
    """
    kits = _service({_GLOBAL_SPECIES, _OWN_SPECIES}).list_kits_for_tenant("t1")

    assert len(kits) > 1


# ── the three arms, each on its own ──────────────────────────────────────────


def test_a_kit_whose_species_is_the_tenants_own_is_offered() -> None:
    assert "mine" in _ids(_service({_OWN_SPECIES}).list_kits_for_tenant("t1"))


def test_a_kit_whose_species_was_granted_is_offered() -> None:
    """The arm #1092 added — and the only one the broken version got right, which
    is why a test written from the grant side alone would have missed everything."""
    assert "shared" in _ids(_service({_GRANTED_SPECIES}).list_kits_for_tenant("t1"))


def test_a_kit_whose_only_species_is_invisible_is_not_offered() -> None:
    """The filter still filters. Restoring the kits must not have restored
    "show everything" — that was the pre-#1092 behaviour, and it is the reason
    the grant work touched this service at all.
    """
    assert "foreign" not in _ids(_service({_GLOBAL_SPECIES}).list_kits_for_tenant("t1"))


def test_a_kit_naming_no_species_is_always_offered() -> None:
    assert "speciesless" in _ids(_service(set()).list_kits_for_tenant("t1"))


def test_a_tenant_seeing_nothing_at_all_still_gets_only_the_species_less_kit() -> None:
    """The empty *visibility* set — as opposed to the empty grant set — is a real
    answer and is treated as one. This is the case the old code's `None` conflated
    with "the store is missing"."""
    assert _ids(_service(set()).list_kits_for_tenant("t1")) == ["speciesless"]


# ── degradation ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("broken", [None], ids=["query raises"])
def test_an_unreachable_species_collection_degrades_to_showing_everything(broken) -> None:
    """Deliberately fail-open, and deliberately *not* the failure above.

    A starter kit names nothing tenant-private — it is seed-data advice on what to
    plant — so opening it costs no isolation. Failing closed would leave a new
    user staring at an empty wizard because of an infrastructure hiccup, which is
    exactly the symptom this whole file exists to prevent.
    """
    assert len(_service(broken).list_kits_for_tenant("t1")) == len(_KITS)


def test_a_missing_species_collection_degrades_the_same_way() -> None:
    assert len(_service(set(), has_species=False).list_kits_for_tenant("t1")) == len(_KITS)


# ── the query itself ─────────────────────────────────────────────────────────


def test_the_visibility_query_carries_all_three_arms() -> None:
    """Pinned at the source, because the double answers from a fixture: it models
    what the union returns, so it cannot notice an arm going missing from the AQL.

    All three must be present. Dropping the global arm reproduces #1178 exactly;
    dropping the grant arm silently undoes #1092.
    """
    service = _service({_GLOBAL_SPECIES})
    service.list_kits_for_tenant("t1")

    query = service._db.queries[0]

    assert "doc.tenant_key == @tenant_key" in query, "own rows"
    assert 'doc.tenant_key == ""' in query, "the global seed catalogue — its absence is #1178"
    assert "tenant_has_access" in query, "explicit grants — their absence undoes #1092"
