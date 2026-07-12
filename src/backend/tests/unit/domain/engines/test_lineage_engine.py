"""Tests for the REQ-017 LineageEngine.

Covers ancestor-path wrapping, the descendant pass-through and the genus/family
graft-compatibility heuristic (§3). The graph traversal itself is faked at the
repository boundary; the AQL cycle guard is exercised in
``test_propagation_repository``.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import GraftCompatibilityLevel
from app.common.exceptions import NotFoundError
from app.data_access.repositories.propagation_repository import PropagationRepository
from app.domain.engines.lineage_engine import LineageEngine, LineagePath


def _species(genus: str, family_key: str | None) -> SimpleNamespace:
    return SimpleNamespace(genus=genus, family_key=family_key)


def _engine(*, species_map: dict | None = None, paths=None, descendants=None) -> LineageEngine:
    repo = MagicMock(spec=PropagationRepository)
    repo.trace_ancestor_paths.return_value = paths or []
    repo.list_ancestors.return_value = []
    repo.list_descendants.return_value = descendants or []

    species_repo = MagicMock()
    species_map = species_map or {}

    def _get_or_raise(key):
        if key not in species_map:
            raise NotFoundError("Species", key)
        return species_map[key]

    species_repo.get_or_raise.side_effect = _get_or_raise
    return LineageEngine(repo, species_repo)


# ── Ancestry ───────────────────────────────────────────────────────────────────


def test_trace_ancestors_wraps_paths() -> None:
    engine = _engine(paths=[["mother-1", "grandmother-1"]])

    result = engine.trace_ancestors("pup-1", "tenant-a")

    assert result == [LineagePath(plant_keys=("mother-1", "grandmother-1"))]


def test_trace_ancestors_empty_for_root_plant() -> None:
    engine = _engine(paths=[])
    assert engine.trace_ancestors("root", "tenant-a") == []


def test_trace_descendants_pass_through() -> None:
    child = SimpleNamespace(key="pup-1")
    engine = _engine(descendants=[child])
    assert engine.trace_descendants("mother-1", "tenant-a") == [child]


# ── Graft compatibility (§3) ────────────────────────────────────────────────────


def test_same_genus_is_compatible() -> None:
    engine = _engine(
        species_map={
            "tomato": _species("Solanum", "solanaceae"),
            "tomato2": _species("Solanum", "solanaceae"),
        }
    )

    result = engine.check_graft_compatibility("tomato", "tomato2")

    assert result.compatible is True
    assert result.level == GraftCompatibilityLevel.COMPATIBLE
    assert result.same_genus is True
    assert engine.is_graft_compatible("tomato", "tomato2") is True


def test_same_family_different_genus_is_possibly_compatible() -> None:
    engine = _engine(
        species_map={
            "tomato": _species("Solanum", "solanaceae"),
            "pepper": _species("Capsicum", "solanaceae"),
        }
    )

    result = engine.check_graft_compatibility("tomato", "pepper")

    assert result.compatible is True
    assert result.level == GraftCompatibilityLevel.POSSIBLY_COMPATIBLE
    assert result.same_genus is False
    assert result.same_family is True


def test_different_family_is_incompatible() -> None:
    engine = _engine(
        species_map={
            "tomato": _species("Solanum", "solanaceae"),
            "cucumber": _species("Cucumis", "cucurbitaceae"),
        }
    )

    result = engine.check_graft_compatibility("tomato", "cucumber")

    assert result.compatible is False
    assert result.level == GraftCompatibilityLevel.INCOMPATIBLE


def test_unknown_species_raises_not_found() -> None:
    engine = _engine(species_map={"tomato": _species("Solanum", "solanaceae")})
    with pytest.raises(NotFoundError):
        engine.check_graft_compatibility("tomato", "ghost")
