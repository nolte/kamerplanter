"""An edit through the API keeps the fields the server maintains — #2181 follow-up.

``PUT /sites/{key}``, ``PUT /locations/{key}`` and ``PUT /slots/{key}`` rebuild the
domain model from the request body (``Model(**body.model_dump())``). Every model
field the body schema does not declare therefore arrived at the repository with
its **default** — and the repositories write the whole model:

* ``Site.weather_source_priority`` — the denormalized view of the site's
  weather-source selection (REQ-046 §2.1), written only by
  ``WeatherSourceService.save_config`` — became ``[]`` on every site edit.
* ``Location.depth`` / ``Location.path`` — derived from the parent on create —
  became ``0`` / ``""`` on every location edit, so the site tree and the MCP
  location listing showed a nested bed as a root without a path.
* ``Slot.currently_occupied`` — set by placing a plant or a planting run — became
  ``False`` on every slot edit, so an occupied slot was offered to the next batch
  placement as free.

The deployed ``app.main`` app, the real ``SiteService`` and a repository double
that records what each update would write — the same path a client takes.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_site_service, get_tenant_service
from app.domain.models.user import User
from app.domain.services.site_service import SiteService
from tests.api.test_location_and_slot_references_api import _Repo as _ReferencesRepo
from tests.api.test_location_and_slot_references_api import _Tenants

_BASE = "/api/v1/t/own"


class _Repo(_ReferencesRepo):
    """Records the model each update would hand to ArangoDB."""

    def __init__(self) -> None:
        super().__init__()
        self.written: dict[str, object] = {}
        site = self._sites["site_own"]
        site.weather_source_priority = ["dwd", "open-meteo"]
        root = self._locations["loc_own"]
        root.depth, root.path = 0, "beet_a"
        child = root.model_copy(update={"key": "loc_child", "name": "Hochbeet Nord"})
        child.parent_location_key, child.depth, child.path = "loc_own", 1, "beet_a/hochbeet_nord"
        self._locations["loc_child"] = child
        self._slots["slot_own"].currently_occupied = True

    def update_site(self, key, site):
        self.written["site"] = site
        return site.model_copy(update={"key": key})

    def update_location(self, key, location):
        self.written["location"] = location
        return location.model_copy(update={"key": key})

    def update_slot(self, key, slot):
        self.written["slot"] = slot
        return super().update_slot(key, slot)


@pytest.fixture
def repo() -> _Repo:
    return _Repo()


@pytest.fixture
def client(repo: _Repo) -> Iterator[TestClient]:
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: User(_key="lead", email="lead@example.org", display_name="L")
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_site_service] = lambda: SiteService(repo)  # type: ignore[arg-type]
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_a_site_edit_keeps_the_weather_source_priority(client: TestClient, repo: _Repo) -> None:
    response = client.put(f"{_BASE}/sites/site_own", json={"name": "Zuhause (umbenannt)", "type": "indoor"})

    assert response.status_code == 200
    assert repo.written["site"].name == "Zuhause (umbenannt)"
    assert repo.written["site"].weather_source_priority == ["dwd", "open-meteo"]


def test_a_site_body_cannot_set_the_weather_source_priority(client: TestClient, repo: _Repo) -> None:
    """The view is the weather-source service's; a site edit neither clears nor sets it."""
    response = client.put(
        f"{_BASE}/sites/site_own",
        json={"name": "Zuhause", "type": "indoor", "weather_source_priority": ["openweathermap"]},
    )

    assert response.status_code == 200
    assert repo.written["site"].weather_source_priority == ["dwd", "open-meteo"]


def test_a_location_edit_keeps_its_place_in_the_tree(client: TestClient, repo: _Repo) -> None:
    response = client.put(
        f"{_BASE}/locations/loc_child",
        json={"name": "Hochbeet Nord", "site_key": "site_own", "parent_location_key": "loc_own", "area_m2": 2.0},
    )

    assert response.status_code == 200
    written = repo.written["location"]
    assert written.area_m2 == 2.0
    assert (written.depth, written.path) == (1, "beet_a/hochbeet_nord")


def test_a_renamed_or_moved_location_gets_the_path_create_would_give_it(client: TestClient, repo: _Repo) -> None:
    """Derived like on create: a rename or a move to the root re-derives depth and path."""
    response = client.put(
        f"{_BASE}/locations/loc_child",
        json={"name": "Hochbeet Süd", "site_key": "site_own", "parent_location_key": None, "area_m2": 2.0},
    )

    assert response.status_code == 200
    assert (repo.written["location"].depth, repo.written["location"].path) == (0, "hochbeet_süd")


def test_a_slot_edit_keeps_it_occupied(client: TestClient, repo: _Repo) -> None:
    response = client.put(f"{_BASE}/slots/slot_own", json={"slot_id": "LOCOWN_B2", "location_key": "loc_own"})

    assert response.status_code == 200
    assert repo.written["slot"].slot_id == "LOCOWN_B2"
    assert repo.written["slot"].currently_occupied is True
