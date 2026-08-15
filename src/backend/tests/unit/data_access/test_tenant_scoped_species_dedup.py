"""The species dedup key is per tenant, not global (#1162).

`v0026` promoted a **global** unique index on `scientific_name_normalized`: one
row per taxon across the whole installation. A tenant creating a species another
tenant already held privately therefore ran silently onto that foreign row — the
UPSERT matched, returned the other tenant's document, and reported success for a
species the caller can never see. No error, no duplicate, and nothing to show.

The key is now `(tenant_key, scientific_name_normalized)`.

**What is given up, deliberately:** REQ-048 Stufe 1's "one taxon, one row" across
the installation. What survives is the part that was actually load-bearing — the
system context (`tenant_key == ""`) still yields exactly one row per taxon in the
shared seed catalogue, and that is what the phase resolver and the lineage graph
read.

Two properties have to hold *together*, and testing either alone is what would let
this ship half-done:

* two tenants can each hold their own row for one taxon — the defect being fixed;
* one tenant still cannot hold two — the guarantee being kept.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.collections import (
    LEGACY_GLOBAL_NAME_INDEX_FIELDS,
    SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS,
)
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.domain.models.species import Species

_MINE = "tenant_acme"
_THEIRS = "tenant_other"


class _Aql:
    """A UPSERT double keyed on whatever the query filters by.

    Deliberately reads the filter out of the query text rather than assuming the
    filter is the normalized name: the whole change under test is *which fields
    the filter names*, so a double that hardcoded the old key would agree with the
    old behaviour no matter what the repository does.
    """

    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.docs = docs
        self.filters_seen: list[dict[str, Any]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        assert bind_vars is not None
        if "UPSERT" in query:
            import re

            filter_fields = re.findall(r"(\w+):\s*@(\w+)", query.split("INSERT")[0])
            criteria = {field: bind_vars[var] for field, var in filter_fields if var in bind_vars}
            self.filters_seen.append(criteria)
            for doc in self.docs:
                if all(doc.get(field) == value for field, value in criteria.items()):
                    return iter([doc])  # type: ignore[return-value]
            new = dict(bind_vars["doc"])
            new.setdefault("_key", f"sp{len(self.docs) + 1}")
            self.docs.append(new)
            return iter([new])  # type: ignore[return-value]
        # Two different lookups reach here and they must not be conflated — the
        # exact-tenant one binds `@tenant`, the visibility union binds
        # `@tenant_key`. A first version of this double only understood the first,
        # so the union query matched nothing: the "foreign species is not visible"
        # test passed while the "own species IS visible" test failed, i.e. the
        # negative was green for the wrong reason.
        by_name = [d for d in self.docs if d.get("scientific_name_normalized") == bind_vars.get("norm")]
        if "tenant" in bind_vars:
            matches = [d for d in by_name if d.get("tenant_key") == bind_vars["tenant"]]
        else:
            caller = bind_vars.get("tenant_key")
            matches = [d for d in by_name if d.get("tenant_key") in (caller, "", None)]
        return iter(matches[:1])  # type: ignore[return-value]


class _Db:
    def __init__(self, docs: list[dict[str, Any]] | None = None) -> None:
        self.aql = _Aql(docs if docs is not None else [])

    def collection(self, name: str) -> Any:  # pragma: no cover - not used here
        raise AssertionError("the repository must go through AQL for these paths")


def _repo(docs: list[dict[str, Any]] | None = None) -> ArangoSpeciesRepository:
    return ArangoSpeciesRepository(_Db(docs))  # type: ignore[arg-type]


def _species(tenant_key: str, name: str = "Solanum lycopersicum") -> Species:
    return Species(scientific_name=name, tenant_key=tenant_key)


# ── the defect: a tenant could not hold its own row ──────────────────────────


def test_two_tenants_can_each_hold_the_same_taxon() -> None:
    """The measured defect. Before #1162 the second create returned the first row."""
    repo = _repo()

    first = repo.upsert_by_normalized_scientific_name(_species(_MINE))
    second = repo.upsert_by_normalized_scientific_name(_species(_THEIRS))

    assert first.tenant_key == _MINE
    assert second.tenant_key == _THEIRS
    assert first.key != second.key


def test_the_upsert_filters_on_the_tenant_as_well_as_the_name() -> None:
    """Pins the filter itself, because the behaviour above could also be produced
    by a repository that had stopped deduplicating entirely."""
    repo = _repo()

    repo.upsert_by_normalized_scientific_name(_species(_MINE))

    assert repo._db.aql.filters_seen[0] == {  # type: ignore[attr-defined]
        "scientific_name_normalized": "solanum lycopersicum",
        "tenant_key": _MINE,
    }


# ── the guarantee that is kept ───────────────────────────────────────────────


def test_one_tenant_still_cannot_hold_two_rows_for_a_taxon() -> None:
    """The half that stops this being "dedup was removed".

    Without it, every assertion above is satisfied by a repository that inserts
    unconditionally — which is a far worse outcome than the bug being fixed.
    """
    repo = _repo()

    first = repo.upsert_by_normalized_scientific_name(_species(_MINE))
    again = repo.upsert_by_normalized_scientific_name(_species(_MINE))

    assert first.key == again.key


def test_the_global_catalogue_still_holds_one_row_per_taxon() -> None:
    """The system context (`tenant_key == ""`) is what the resolver and lineage read.

    REQ-048 Stufe 1's real subject was the shared catalogue, and that guarantee is
    unchanged — seeds, migrations and enrichment all write under `""`.
    """
    repo = _repo()

    first = repo.upsert_by_normalized_scientific_name(_species(""))
    again = repo.upsert_by_normalized_scientific_name(_species(""))

    assert first.key == again.key


def test_normalization_still_decides_what_counts_as_the_same_row() -> None:
    """#1148 interaction: the compound key is *the same normalization*, per tenant.

    A hybrid-marker variant must still collapse onto the existing row — otherwise
    this change would have quietly reopened the duplicate class #1148 closed.
    """
    repo = _repo()

    first = repo.upsert_by_normalized_scientific_name(_species(_MINE, "Fragaria x ananassa"))
    variant = repo.upsert_by_normalized_scientific_name(_species(_MINE, "Fragaria × ananassa"))

    assert first.key == variant.key


# ── the scoped lookup the create path uses ───────────────────────────────────


def test_the_scoped_lookup_does_not_see_a_foreign_row() -> None:
    """`create_species` asks "does an exact match already exist?" before inheriting
    synonym fields. Asking unscoped would find a foreign tenant's row and suppress
    the inheritance for a record that has no twin in this tenant at all."""
    docs = [
        {
            "_key": "sp1",
            "scientific_name": "Solanum lycopersicum",
            "scientific_name_normalized": "solanum lycopersicum",
            "tenant_key": _THEIRS,
        }
    ]
    repo = _repo(docs)

    assert repo.get_by_normalized_scientific_name_for_tenant("Solanum lycopersicum", _MINE) is None
    assert repo.get_by_normalized_scientific_name_for_tenant("Solanum lycopersicum", _THEIRS) is not None


# ── visibility, which is a third question again ──────────────────────────────


def test_a_foreign_private_species_is_not_visible() -> None:
    """The oracle this change would otherwise have opened.

    While the dedup key was global there was exactly one row per taxon, so
    "does it exist?" and "can you see it?" could not disagree. Per-tenant rows make
    them different questions — and the identification flow asks the *visibility*
    one. Answering it unscoped would report another tenant's private species as
    already catalogued.
    """
    docs = [
        {
            "_key": "sp1",
            "scientific_name": "Monstera deliciosa",
            "scientific_name_normalized": "monstera deliciosa",
            "tenant_key": _THEIRS,
        }
    ]

    assert _repo(docs).find_visible_by_normalized_scientific_name("Monstera deliciosa", _MINE) is None


@pytest.mark.parametrize("owner", [_MINE, ""])
def test_an_own_or_global_species_is_visible(owner: str) -> None:
    """Both arms of the hybrid union, or the fix above would read as "see nothing"."""
    docs = [
        {
            "_key": "sp1",
            "scientific_name": "Monstera deliciosa",
            "scientific_name_normalized": "monstera deliciosa",
            "tenant_key": owner,
        }
    ]

    assert _repo(docs).find_visible_by_normalized_scientific_name("Monstera deliciosa", _MINE) is not None


# ── the index definition itself ──────────────────────────────────────────────


def test_the_index_names_the_tenant_first() -> None:
    """An index serves a prefix of its fields, and every scoped read filters on the
    tenant first — so the order is a performance property, not cosmetics."""
    assert SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS == ["tenant_key", "scientific_name_normalized"]


def test_the_legacy_field_list_is_still_named() -> None:
    """v0041 has to *recognise* the old index to drop it.

    If this constant were deleted along with the old behaviour, the migration
    could no longer find the global index — and leaving that index in place keeps
    the stricter constraint in force, making the whole change inert.
    """
    assert LEGACY_GLOBAL_NAME_INDEX_FIELDS == ["scientific_name_normalized"]
    assert LEGACY_GLOBAL_NAME_INDEX_FIELDS != SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS


@pytest.mark.parametrize("collection", [col.SPECIES])
def test_the_species_collection_is_the_one_indexed(collection: str) -> None:
    assert collection == "species"
