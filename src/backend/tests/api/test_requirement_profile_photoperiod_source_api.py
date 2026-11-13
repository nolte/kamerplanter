"""The provenance of a profile's light hours through the profile API (#2857, REQ-003, REQ-053 §9.2a W-016.6).

``POST`` / ``PUT /profiles/requirements`` is the profile editor: a person states the hours, so the server stores
``photoperiod_source = sourced`` whatever the body says - a client cannot claim ``generated`` or ``default``.
``POST /profiles/generate-defaults/{phase_key}`` is the generator: its table gives ``generated``, a phase name outside
it ``default``. ``GET`` returns what is stored, ``null`` for a profile from before the provenance.

The deployed ``app.main`` app, the real ``PhaseService`` and a repository double that records what each write hands it.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user, get_is_platform_admin
from app.common.dependencies import get_phase_service
from app.common.enums import PhotoperiodSource
from app.common.exceptions import NotFoundError
from app.domain.models.lifecycle import GrowthPhase
from app.domain.models.phase import NutrientProfile, RequirementProfile
from app.domain.models.user import User
from app.domain.services.phase_service import PhaseService

_BASE = "/api/v1/profiles"


def _phase(key: str, name: str) -> GrowthPhase:
    return GrowthPhase(
        _key=key, name=name, display_name=name.title(), lifecycle_key="lc", typical_duration_days=30, sequence_order=1
    )


class _ProfileRepo:
    """Phases and requirement profiles by key; records the profile each write would store."""

    def __init__(self) -> None:
        self.phases = {key: _phase(key, name) for key, name in (("ph_flower", "flowering"), ("ph_harvest", "harvest"))}
        self.requirements: dict[str, RequirementProfile] = {
            # Stored before the provenance existed: no photoperiod_source.
            "ph_legacy": RequirementProfile(_key="rp_legacy", phase_key="ph_legacy", photoperiod_hours=18.0),
        }
        self.written: list[RequirementProfile] = []

    def get_phase_or_raise(self, key: str) -> GrowthPhase:
        phase = self.phases.get(key)
        if phase is None:
            raise NotFoundError("GrowthPhase", key)
        return phase

    def get_requirement_profile(self, phase_key: str) -> RequirementProfile | None:
        return self.requirements.get(phase_key)

    def create_requirement_profile(self, profile: RequirementProfile) -> RequirementProfile:
        self.written.append(profile)
        return profile.model_copy(update={"key": f"rp_{len(self.written)}"})

    def update_requirement_profile(self, key: str, profile: RequirementProfile) -> RequirementProfile:
        self.written.append(profile)
        return profile.model_copy(update={"key": key})

    def create_nutrient_profile(self, profile: NutrientProfile) -> NutrientProfile:
        return profile.model_copy(update={"key": "np_1"})


@pytest.fixture
def repo() -> _ProfileRepo:
    return _ProfileRepo()


@pytest.fixture
def client(repo: _ProfileRepo) -> Iterator[TestClient]:
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: User(_key="admin", email="admin@example.org", display_name="A")
    app.dependency_overrides[get_is_platform_admin] = lambda: True
    app.dependency_overrides[get_phase_service] = lambda: PhaseService(repo, MagicMock())  # type: ignore[arg-type]
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


class TestAPersonsEntryIsSourced:
    def test_create_stores_sourced(self, client: TestClient, repo: _ProfileRepo) -> None:
        response = client.post(f"{_BASE}/requirements", json={"phase_key": "ph_flower", "photoperiod_hours": 12.0})

        assert response.status_code == 201
        assert (repo.written[-1].photoperiod_hours, repo.written[-1].photoperiod_source) == (
            12.0,
            PhotoperiodSource.SOURCED,
        )
        assert response.json()["photoperiod_source"] == "sourced"

    def test_update_stores_sourced(self, client: TestClient, repo: _ProfileRepo) -> None:
        response = client.put(
            f"{_BASE}/requirements/rp_legacy", json={"phase_key": "ph_legacy", "photoperiod_hours": 16}
        )

        assert response.status_code == 200
        assert repo.written[-1].photoperiod_source == PhotoperiodSource.SOURCED
        assert response.json()["photoperiod_source"] == "sourced"

    @pytest.mark.parametrize("claimed", ["generated", "default", None])
    def test_a_client_cannot_claim_another_origin(self, client: TestClient, repo: _ProfileRepo, claimed) -> None:
        body = {"phase_key": "ph_flower", "photoperiod_hours": 12.0, "photoperiod_source": claimed}

        created = client.post(f"{_BASE}/requirements", json=body)
        updated = client.put(f"{_BASE}/requirements/rp_1", json=body)

        assert (created.status_code, updated.status_code) == (201, 200)
        assert [p.photoperiod_source for p in repo.written] == [PhotoperiodSource.SOURCED] * 2


class TestTheGeneratorsOrigin:
    def test_a_table_phase_is_generated(self, client: TestClient) -> None:
        response = client.post(f"{_BASE}/generate-defaults/ph_flower")

        assert response.status_code == 200
        req = response.json()["requirement_profile"]
        assert (req["photoperiod_hours"], req["photoperiod_source"]) == (12.0, "generated")

    def test_a_phase_outside_the_table_is_the_default(self, client: TestClient) -> None:
        req = client.post(f"{_BASE}/generate-defaults/ph_harvest").json()["requirement_profile"]

        assert (req["photoperiod_hours"], req["photoperiod_source"]) == (18.0, "default")


def test_a_profile_from_before_the_provenance_reads_null(client: TestClient) -> None:
    response = client.get(f"{_BASE}/requirements/ph_legacy")

    assert response.status_code == 200
    assert response.json()["photoperiod_source"] is None
