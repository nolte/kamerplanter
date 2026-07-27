"""Botanical-families router: species counts come from one bulk lookup (REQ-001).

House style: router functions invoked directly with a fake repository — the
router is the unit, the repository is the doubled I/O boundary.

The guarantee under test is a *wiring* one. ``get_species_counts_by_family`` was
added to collapse the list endpoint's per-row count queries into a single
aggregate round-trip, but nothing called it: ``list_families`` still went through
``_family_response``, i.e. one ``get_species_count_by_family`` per row (N+1).
These tests pin the wiring from both sides — the list endpoint must use the bulk
lookup exactly once and never the per-family one, while the single-row endpoints
must keep using the per-family one (a bulk aggregate over the whole species
collection to serve one row would be strictly worse).
"""

from __future__ import annotations

import pytest

from app.api.v1.botanical_families.router import (
    create_family,
    get_family,
    get_family_species,
    list_families,
    update_family,
)
from app.api.v1.botanical_families.schemas import FamilyCreate
from app.common.exceptions import NotFoundError
from app.common.pagination import PaginationParams
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.species import Species


def _family(key: str, name: str) -> BotanicalFamily:
    return BotanicalFamily(_key=key, name=name)


class _FakeFamilyRepo:
    """Mimics the slice of ArangoBotanicalFamilyRepository the router calls.

    Counts every call to the two count methods so a test can assert *how* the
    counts were resolved, not just that the numbers came out right.
    """

    def __init__(
        self,
        families: list[BotanicalFamily] | None = None,
        counts: dict[str, int] | None = None,
        species: list[Species] | None = None,
    ) -> None:
        self._families = list(families or [])
        self._counts = dict(counts or {})
        self._species = list(species or [])
        self.bulk_count_calls = 0
        self.per_family_count_calls: list[str] = []
        self.species_by_family_calls: list[str] = []

    def get_all_families(self, offset: int = 0, limit: int = 50) -> tuple[list[BotanicalFamily], int]:
        return self._families[offset : offset + limit], len(self._families)

    def get_species_counts_by_family(self) -> dict[str, int]:
        self.bulk_count_calls += 1
        # Families without species are absent from the map, exactly like the AQL
        # aggregate — this is what makes the router's ``.get(key, 0)`` load-bearing.
        return dict(self._counts)

    def get_species_count_by_family(self, family_key: str) -> int:
        self.per_family_count_calls.append(family_key)
        return self._counts.get(family_key, 0)

    def get_by_key(self, key: str) -> BotanicalFamily | None:
        return next((f for f in self._families if f.key == key), None)

    def get_species_by_family(self, family_key: str) -> list[Species]:
        self.species_by_family_calls.append(family_key)
        return list(self._species)

    def create_family(self, family: BotanicalFamily) -> BotanicalFamily:
        return family

    def update_family(self, key: str, family: BotanicalFamily) -> BotanicalFamily:
        return _family(key, family.name)


class TestListFamiliesUsesBulkCounts:
    def test_resolves_every_count_in_one_bulk_lookup(self):
        repo = _FakeFamilyRepo(
            families=[_family("rosaceae", "Rosaceae"), _family("fabaceae", "Fabaceae")],
            counts={"rosaceae": 7, "fabaceae": 3},
        )

        result = list_families(pagination=PaginationParams(), repo=repo)

        assert [r.species_count for r in result] == [7, 3]
        assert repo.bulk_count_calls == 1
        # The N+1 regression guard: not a single per-row count query.
        assert repo.per_family_count_calls == []

    def test_bulk_lookup_stays_single_as_the_page_grows(self):
        families = [_family(f"famil{i}aceae", f"Famil{i}aceae") for i in range(10)]
        repo = _FakeFamilyRepo(families=families, counts={f.key or "": 1 for f in families})

        result = list_families(pagination=PaginationParams(), repo=repo)

        assert len(result) == 10
        # One round-trip regardless of page size — the whole point of the rewire.
        assert repo.bulk_count_calls == 1
        assert repo.per_family_count_calls == []

    def test_family_absent_from_the_map_reports_zero(self):
        repo = _FakeFamilyRepo(
            families=[_family("rosaceae", "Rosaceae"), _family("lamiaceae", "Lamiaceae")],
            counts={"rosaceae": 7},
        )

        result = list_families(pagination=PaginationParams(), repo=repo)

        assert [(r.key, r.species_count) for r in result] == [("rosaceae", 7), ("lamiaceae", 0)]

    def test_pagination_is_still_honoured(self):
        repo = _FakeFamilyRepo(
            families=[_family("rosaceae", "Rosaceae"), _family("fabaceae", "Fabaceae")],
            counts={"rosaceae": 7, "fabaceae": 3},
        )

        result = list_families(pagination=PaginationParams(offset=1, limit=1), repo=repo)

        assert [r.key for r in result] == ["fabaceae"]
        assert repo.bulk_count_calls == 1


class TestSingleRowEndpointsKeepPerFamilyCount:
    def test_get_family_uses_the_per_family_count(self):
        repo = _FakeFamilyRepo(families=[_family("rosaceae", "Rosaceae")], counts={"rosaceae": 7})

        result = get_family(key="rosaceae", repo=repo)

        assert result.species_count == 7
        assert repo.per_family_count_calls == ["rosaceae"]
        # No collection-wide aggregate to serve a single row.
        assert repo.bulk_count_calls == 0

    def test_create_family_uses_the_per_family_count(self):
        repo = _FakeFamilyRepo(counts={})

        result = create_family(body=FamilyCreate(name="Rosaceae"), repo=repo)

        assert result.species_count == 0
        assert repo.per_family_count_calls == [""]
        assert repo.bulk_count_calls == 0

    def test_update_family_uses_the_per_family_count(self):
        repo = _FakeFamilyRepo(counts={"rosaceae": 7})

        result = update_family(key="rosaceae", body=FamilyCreate(name="Rosaceae"), repo=repo)

        assert result.species_count == 7
        assert repo.per_family_count_calls == ["rosaceae"]
        assert repo.bulk_count_calls == 0


class TestFamilySpeciesEndpoint:
    def test_returns_the_species_assigned_to_the_family(self):
        repo = _FakeFamilyRepo(
            families=[_family("rosaceae", "Rosaceae")],
            species=[Species(_key="sp1", scientific_name="Rosa canina", family_key="rosaceae")],
        )

        result = get_family_species(key="rosaceae", repo=repo)

        assert [s.scientific_name for s in result] == ["Rosa canina"]
        # The assignment is resolved by family key, not by walking an edge.
        assert repo.species_by_family_calls == ["rosaceae"]


class TestUnknownFamilyIsNotFound:
    """SCR-008 guard: ``NotFoundError`` moved from function-local to module-level.

    A hoisted import that got mis-resolved would surface here as an ImportError
    or NameError instead of the 404 contract.
    """

    def test_get_family_raises_not_found(self):
        repo = _FakeFamilyRepo(families=[])

        with pytest.raises(NotFoundError):
            get_family(key="missing", repo=repo)

    def test_get_family_species_raises_not_found(self):
        repo = _FakeFamilyRepo(families=[])

        with pytest.raises(NotFoundError):
            get_family_species(key="missing", repo=repo)
