"""#2002 — deleting a growth phase takes its requirement and nutrient profiles with it.

``ArangoLifecycleRepository.delete_phase`` removed the phase and its edges and left
the two profiles it owned behind, unreachable: every seed that replaced a species'
phases, and the ``DELETE /growth-phases/{key}`` route, leaked them. Measured on an
empty database: 155 orphans of each kind after one boot.
"""

from __future__ import annotations

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository
from app.domain.models.lifecycle import GrowthPhase
from app.domain.models.phase import NutrientProfile, RequirementProfile
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the cascade is AQL over a real server"),
]

_DB_NAME = run_database_name("lifecycle_delete_phase_profiles")


@pytest.fixture
def repo():
    system, database = create_database(_DB_NAME)
    yield ArangoLifecycleRepository(database)
    system.delete_database(_DB_NAME)


def _phase_with_profiles(repo: ArangoLifecycleRepository, name: str) -> tuple[str, str, str]:
    phase = repo.create_phase(
        GrowthPhase(name=name, display_name=name, lifecycle_key="lc-1", typical_duration_days=7, sequence_order=1)
    )
    key = phase.key or ""
    req = repo.create_requirement_profile(RequirementProfile(phase_key=key))
    nut = repo.create_nutrient_profile(NutrientProfile(phase_key=key))
    return key, req.key or "", nut.key or ""


def _exists(repo: ArangoLifecycleRepository, collection: str, key: str) -> bool:
    return bool(repo._db.collection(collection).has(key))


def test_deleting_a_phase_removes_the_profiles_it_owns(repo) -> None:
    phase_key, req_key, nut_key = _phase_with_profiles(repo, "vegetative")

    assert repo.delete_phase(phase_key) is True

    assert not _exists(repo, col.REQUIREMENT_PROFILES, req_key)
    assert not _exists(repo, col.NUTRIENT_PROFILES, nut_key)


def test_another_phases_profiles_are_kept(repo) -> None:
    doomed, _, _ = _phase_with_profiles(repo, "vegetative")
    kept, kept_req, kept_nut = _phase_with_profiles(repo, "flowering")

    repo.delete_phase(doomed)

    assert _exists(repo, col.REQUIREMENT_PROFILES, kept_req)
    assert _exists(repo, col.NUTRIENT_PROFILES, kept_nut)
    assert repo.get_requirement_profile(kept) is not None


def test_a_profile_another_phase_still_points_at_is_kept(repo) -> None:
    doomed, req_key, _ = _phase_with_profiles(repo, "vegetative")
    other, _, _ = _phase_with_profiles(repo, "flowering")
    repo._db.collection(col.REQUIRES_PROFILE).insert(
        {"_from": f"{col.GROWTH_PHASES}/{other}", "_to": f"{col.REQUIREMENT_PROFILES}/{req_key}"}
    )

    repo.delete_phase(doomed)

    assert _exists(repo, col.REQUIREMENT_PROFILES, req_key)


def test_a_failure_part_way_never_leaves_an_edge_to_a_removed_profile(repo, monkeypatch) -> None:
    """The steps are not one transaction; a failure between them must leave a readable phase.

    Measured before the reorder: profiles removed first, the edge detach failed, and
    ``get_requirement_profile`` dereferenced the dangling edge (``AttributeError``, a 500).
    """
    phase_key, req_key, nut_key = _phase_with_profiles(repo, "vegetative")

    def fail(*_args: object, **_kwargs: object) -> int:
        raise RuntimeError("injected failure while detaching edges")

    monkeypatch.setattr(repo, "delete_edges", fail)
    with pytest.raises(RuntimeError):
        repo.delete_phase(phase_key)
    monkeypatch.undo()

    assert repo.get_requirement_profile(phase_key) is not None
    assert repo.get_nutrient_profile(phase_key) is not None
    assert _exists(repo, col.REQUIREMENT_PROFILES, req_key)
    assert _exists(repo, col.NUTRIENT_PROFILES, nut_key)
