"""#3015 — the service side of the plant list's location filter and run projection.

The router hands ``location_key`` and the page's keys to :class:`PlantInstanceService`; which repository read each
one reaches, and what the run projection answers without a run repository, is decided here.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.domain.services.plant_instance_service import PlantInstanceService


def _service(run_repo: MagicMock | None = None) -> tuple[PlantInstanceService, MagicMock]:
    plant_repo = MagicMock()
    service = PlantInstanceService(plant_repo, MagicMock(), MagicMock(), MagicMock(), planting_run_repo=run_repo)
    return service, plant_repo


def test_a_location_narrows_the_window_to_the_location_read() -> None:
    service, repo = _service()

    service.list_plants_window(tenant_key="t-1", limit=200, after="p-9", location_key="loc-1")

    repo.list_window_at_location.assert_called_once_with(
        tenant_key="t-1", location_key="loc-1", offset=0, limit=200, after="p-9"
    )
    repo.list_window.assert_not_called()


@pytest.mark.parametrize("location_key", [None, ""])
def test_without_a_location_the_whole_tenant_is_paged(location_key) -> None:
    service, repo = _service()

    service.list_plants_window(tenant_key="t-1", limit=200, location_key=location_key)

    repo.list_window.assert_called_once_with(offset=0, limit=200, tenant_key="t-1", after=None)
    repo.list_window_at_location.assert_not_called()


def test_run_refs_are_one_read_for_the_page() -> None:
    run_repo = MagicMock()
    run_repo.get_run_refs_for_plants.return_value = {"p-1": [{"key": "r", "name": "R", "status": "active"}]}
    service, _ = _service(run_repo)

    refs = service.run_refs_for_plants(["p-1", "p-2"], tenant_key="t-1")

    assert refs == {"p-1": [{"key": "r", "name": "R", "status": "active"}]}
    run_repo.get_run_refs_for_plants.assert_called_once_with(["p-1", "p-2"], tenant_key="t-1")


def test_run_refs_without_a_run_repository_or_plants_are_empty() -> None:
    run_repo = MagicMock()
    service, _ = _service(run_repo)

    assert _service()[0].run_refs_for_plants(["p-1"], tenant_key="t-1") == {}
    assert service.run_refs_for_plants([], tenant_key="t-1") == {}
    run_repo.get_run_refs_for_plants.assert_not_called()
