"""The parent chain two soil rules read (REQ-053 §11.3a Nr. 5 v1.60, #2888 O3/O5): within the site, and it ends.

``Location`` carries no ``tenant_key`` (#2107); the walk starts at a location the caller resolved under the tenant and
follows a parent only inside that location's site. A corrupt ``parent_location_key`` that names another site's row -
another tenant's, possibly - must end the chain like an absent parent, and a cycle must terminate.
"""

from __future__ import annotations

import pytest

from app.common.exceptions import StoredDocumentInvalidError
from app.domain.models.site import Location
from app.domain.services.location_ancestry import MAX_LOCATION_ANCESTORS, location_ancestors


def _loc(key: str, parent: str | None = None, site: str = "site_own") -> Location:
    return Location(_key=key, name=key, site_key=site, area_m2=1.0, parent_location_key=parent)


class _Store:
    def __init__(self, *locations: Location) -> None:
        self.rows: dict[str, Location] = {loc.key or "": loc for loc in locations}
        self.broken: dict[str, dict] = {}
        self.reads: list[str] = []

    def get_location_by_key(self, key: str) -> Location | None:
        self.reads.append(key)
        if key in self.broken:
            raise StoredDocumentInvalidError("Location", key, ["soil_hazards"], stored=self.broken[key])
        return self.rows.get(key)


def test_the_chain_is_nearest_parent_first() -> None:
    store = _Store(_loc("garden"), _loc("zone", "garden"), _loc("bed", "zone"))

    assert [loc.key for loc in location_ancestors(store, store.rows["bed"])] == ["zone", "garden"]


def test_a_location_without_a_parent_has_none() -> None:
    store = _Store(_loc("garden"))

    assert location_ancestors(store, store.rows["garden"]) == []
    assert store.reads == []


def test_a_parent_in_another_site_ends_the_chain() -> None:
    """A corrupt parent key naming another tenant's location is never read as this bed's parent."""
    store = _Store(_loc("foreign_garden", site="site_foreign"), _loc("bed", "foreign_garden"))

    assert location_ancestors(store, store.rows["bed"]) == []


def test_an_absent_parent_ends_the_chain() -> None:
    store = _Store(_loc("bed", "gone"))

    assert location_ancestors(store, store.rows["bed"]) == []


def test_a_cycle_terminates() -> None:
    store = _Store(_loc("a", "b"), _loc("b", "a"), _loc("bed", "a"))

    assert [loc.key for loc in location_ancestors(store, store.rows["bed"])] == ["a", "b"]
    assert store.reads == ["a", "b"]


def test_a_location_naming_itself_as_parent_terminates() -> None:
    store = _Store(_loc("bed", "bed"))

    assert location_ancestors(store, store.rows["bed"]) == []


def test_a_chain_longer_than_the_cap_is_cut() -> None:
    keys = [f"l{i}" for i in range(MAX_LOCATION_ANCESTORS + 5)]
    store = _Store(*(_loc(key, keys[i + 1] if i + 1 < len(keys) else None) for i, key in enumerate(keys)))

    assert len(location_ancestors(store, store.rows["l0"])) == MAX_LOCATION_ANCESTORS


def test_a_broken_parent_of_another_site_reads_as_absent_not_as_a_409() -> None:
    store = _Store(_loc("bed", "foreign"))
    store.broken["foreign"] = {"_key": "foreign", "site_key": "site_foreign"}

    assert location_ancestors(store, store.rows["bed"]) == []


def test_a_broken_parent_of_the_own_site_is_the_409() -> None:
    store = _Store(_loc("bed", "own"))
    store.broken["own"] = {"_key": "own", "site_key": "site_own"}

    with pytest.raises(StoredDocumentInvalidError):
        location_ancestors(store, store.rows["bed"])
