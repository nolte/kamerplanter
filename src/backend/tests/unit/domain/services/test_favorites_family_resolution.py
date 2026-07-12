"""Favorites collection-resolution contract for botanical families (#550).

Before #550 ``FavoritesService._resolve_collection`` only knew SPECIES /
NUTRIENT_PLANS / FERTILIZERS / ACTIVITIES, so favoriting a botanical family
raised ``ValueError`` in ``add_favorite``. The crop-rotation "favorites" filter
needs families to be favoritable, so ``BOTANICAL_FAMILIES`` must resolve. Uses a
capturing fake db (no live ArangoDB): the collection whose ``has`` returns True
is the one the key belongs to.
"""

from __future__ import annotations

from app.data_access.arango import collections as col
from app.domain.services.favorites_service import FavoritesService


class _FakeCollection:
    def __init__(self, present_keys: set[str]) -> None:
        self._present = present_keys

    def has(self, key: str) -> bool:
        return key in self._present


class _FakeDb:
    """Routes collection lookups; only the named collection holds the key."""

    def __init__(self, membership: dict[str, set[str]]) -> None:
        self._membership = membership

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(self._membership.get(name, set()))


def test_resolves_botanical_family_key() -> None:
    db = _FakeDb({col.BOTANICAL_FAMILIES: {"solanaceae"}})
    service = FavoritesService(db)  # type: ignore[arg-type]

    assert service._resolve_collection("solanaceae") == col.BOTANICAL_FAMILIES


def test_species_still_resolves_before_families() -> None:
    # A species key present in the species collection must resolve there — the
    # families entry must not shadow existing resolution order.
    db = _FakeDb({col.SPECIES: {"tomato"}})
    service = FavoritesService(db)  # type: ignore[arg-type]

    assert service._resolve_collection("tomato") == col.SPECIES


def test_unknown_key_resolves_to_none() -> None:
    db = _FakeDb({})
    service = FavoritesService(db)  # type: ignore[arg-type]

    assert service._resolve_collection("ghost") is None
