"""Locations and slots answer only for the caller's own tenant, foreign and unknown alike — #1871 B1, B13, B14.

* **B13** — the location and slot routers resolved a location unscoped and then
  checked its **site**: a foreign location answered ``NotFoundError("Site",
  <the other tenant's site key>)`` while an unknown one answered
  ``NotFoundError("Location", key)`` — an existence oracle that echoed the other
  tenant's site key.
* **B14** — ``GET /locations?site_key=<own>&parent_location_key=<foreign>`` checked
  only the site and listed the foreign location's children.
* **B1** — ``PUT /slots/{key}`` verified the existing slot and stored the body's
  ``location_key`` as given: the slot's derived tenant flipped to the victim.

The deployed ``app.main`` app, the real ``get_current_tenant``, the real
``SiteService`` over the repository double locations and slots are measured
with elsewhere (no ``tenant_key`` on them, only on the site).
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_site_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.user import User
from app.domain.services.site_service import SiteService
from tests.unit.domain.services.test_site_service_location_tenant import OWN, FakeSiteRepo


class _Repo(FakeSiteRepo):
    def __init__(self) -> None:
        super().__init__()
        self.slot_writes: list = []

    def get_site_or_raise(self, key):
        site = self._sites.get(key)
        if site is None:
            raise NotFoundError("Site", key)
        return site

    def get_location_children(self, parent_key):
        return [loc for loc in self._locations.values() if loc.parent_location_key == parent_key]

    def get_locations_by_site(self, site_key):
        return [loc for loc in self._locations.values() if loc.site_key == site_key]

    def get_slots_by_location(self, location_key):
        return [s for s in self._slots.values() if s.location_key == location_key]

    def update_slot(self, key, slot):
        self.slot_writes.append((key, slot.location_key))
        return slot.model_copy(update={"key": key})


class _Tenants:
    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        if slug != "own":
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=OWN, slug="own")

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        return SimpleNamespace(role=TenantRole.LEAD, admin_scopes=[], is_active=True) if tenant_key == OWN else None

    def get_personal_tenant(self, user_key: str) -> None:
        return None


@pytest.fixture
def repo() -> _Repo:
    repo = _Repo()
    child = repo._locations["loc_foreign"].model_copy(update={"key": "loc_foreign_child", "name": "Geheimbeet"})
    child.parent_location_key = "loc_foreign"
    repo._locations["loc_foreign_child"] = child
    return repo


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


_BASE = "/api/v1/t/own"


@pytest.mark.parametrize(
    "path",
    [f"{_BASE}/locations/loc_foreign", f"{_BASE}/locations/loc_foreign/children", f"{_BASE}/slots/slot_foreign"],
)
def test_a_foreign_location_or_slot_answers_like_an_unknown_one(client: TestClient, path: str) -> None:
    foreign = client.get(path)
    unknown = client.get(path.replace("_foreign", "_nowhere"))

    assert foreign.status_code == unknown.status_code == 404
    # Same answer, key for key: only the probed key itself may differ.
    assert str(foreign.json()["details"]) == str(unknown.json()["details"]).replace("_nowhere", "_foreign")
    assert "site_foreign" not in foreign.text


def test_the_children_of_a_foreign_location_are_not_listed_under_an_own_site(client: TestClient) -> None:
    response = client.get(f"{_BASE}/locations", params={"site_key": "site_own", "parent_location_key": "loc_foreign"})

    assert response.status_code == 404
    assert "Geheimbeet" not in response.text


def test_a_slot_cannot_be_moved_to_a_foreign_location(client: TestClient, repo: _Repo) -> None:
    response = client.put(f"{_BASE}/slots/slot_own", json={"slot_id": "LOCOWN_A1", "location_key": "loc_foreign"})

    assert response.status_code == 404
    assert repo.slot_writes == []


def test_own_locations_and_slots_still_work(client: TestClient, repo: _Repo) -> None:
    assert client.get(f"{_BASE}/locations/loc_own").status_code == 200
    assert client.get(f"{_BASE}/slots/slot_own").status_code == 200
    assert (
        client.put(f"{_BASE}/slots/slot_own", json={"slot_id": "LOCOWN_A1", "location_key": "loc_own"}).status_code
        == 200
    )
