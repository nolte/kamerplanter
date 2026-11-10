"""Site settings ``sun_class_thresholds`` and ``reach_thresholds`` through the API (REQ-053 WP 8.24, #2667).

The deployed ``app.main`` app, the real ``SiteService`` and a repository double that keeps what each write would
store - the path a client takes. Covers GP-FR-164 (sun-class bounds, reference day), GP-FR-166 (reach) and the
orientation a stored aspect derives on ``PUT /locations`` (GP-FR-017/168).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_site_service, get_tenant_service
from app.domain.models.site import ReachThresholds, SiteConditions, SunClassThresholds
from app.domain.models.user import User
from app.domain.services.site_service import SiteService
from tests.api.test_location_and_slot_references_api import _Tenants
from tests.api.test_site_edit_keeps_server_maintained_fields import _Repo as _RecordingRepo

_BASE = "/api/v1/t/own"
_DEFAULT_SUN = SunClassThresholds().model_dump()
_DEFAULT_REACH = ReachThresholds().model_dump()
_CUSTOM_SUN = {
    "full_sun_min_hours": 7.0,
    "partial_shade_min_hours": 4.0,
    "shade_min_hours": 1.5,
    "reference_month": 7,
    "reference_day": 1,
}
_CUSTOM_REACH = {"both_sides_m": 1.4, "one_side_m": 0.7, "path_access_max_distance_m": 0.5}


class _Repo(_RecordingRepo):
    """Keeps the written site, as the merge-mode site repository would (a ``None`` is not written)."""

    def update_site(self, key, site):
        stored = super().update_site(key, site)
        self._sites[key] = stored
        return stored

    def create_site(self, site):
        created = site.model_copy(update={"key": "site_new"})
        self._sites["site_new"] = created
        return created


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


def _put(client: TestClient, **fields: Any):
    return client.put(f"{_BASE}/sites/site_own", json={"name": "Zuhause", "type": "outdoor", **fields})


class TestTheResponse:
    def test_a_site_without_stored_thresholds_answers_with_the_defaults(self, client: TestClient) -> None:
        body = client.get(f"{_BASE}/sites/site_own").json()

        assert body["sun_class_thresholds"] == _DEFAULT_SUN
        assert body["reach_thresholds"] == _DEFAULT_REACH
        assert (body["sun_class_thresholds"]["reference_month"], body["sun_class_thresholds"]["reference_day"]) == (
            6,
            21,
        )

    def test_the_list_answers_with_them_too(self, client: TestClient, repo: _Repo) -> None:
        repo.get_all_sites = lambda *a, **k: ([], 0)  # type: ignore[method-assign]
        repo.list_sites_window = lambda *a, **k: [repo._sites["site_own"]]  # type: ignore[method-assign]

        body = client.get(f"{_BASE}/sites").json()

        assert body[0]["reach_thresholds"] == _DEFAULT_REACH


class TestWritingThem:
    def test_an_edit_stores_and_answers_the_configured_values(self, client: TestClient, repo: _Repo) -> None:
        response = _put(client, sun_class_thresholds=_CUSTOM_SUN, reach_thresholds=_CUSTOM_REACH)

        assert response.status_code == 200
        assert response.json()["sun_class_thresholds"] == _CUSTOM_SUN
        assert response.json()["reach_thresholds"] == _CUSTOM_REACH
        assert repo.written["site"].reach_thresholds == ReachThresholds(**_CUSTOM_REACH)

    def test_an_edit_that_does_not_send_them_keeps_the_stored_values(self, client: TestClient, repo: _Repo) -> None:
        _put(client, sun_class_thresholds=_CUSTOM_SUN, reach_thresholds=_CUSTOM_REACH)

        response = _put(client, name="Zuhause (umbenannt)")

        assert response.status_code == 200
        assert repo.written["site"].sun_class_thresholds == SunClassThresholds(**_CUSTOM_SUN)
        assert repo.written["site"].reach_thresholds == ReachThresholds(**_CUSTOM_REACH)
        assert response.json()["reach_thresholds"] == _CUSTOM_REACH

    def test_sending_the_defaults_resets_them(self, client: TestClient) -> None:
        _put(client, reach_thresholds=_CUSTOM_REACH)

        response = _put(client, reach_thresholds=_DEFAULT_REACH)

        assert response.json()["reach_thresholds"] == _DEFAULT_REACH

    def test_thresholds_sent_without_the_path_distance_take_its_default(self, client: TestClient) -> None:
        """A client from before #2703 sends only the two reach values: the path distance is the 0.3 m default."""
        response = _put(client, reach_thresholds={"both_sides_m": 1.4, "one_side_m": 0.7})

        assert response.status_code == 200
        assert response.json()["reach_thresholds"]["path_access_max_distance_m"] == 0.3

    def test_a_create_takes_them(self, client: TestClient) -> None:
        response = client.post(
            f"{_BASE}/sites", json={"name": "Neu", "type": "outdoor", "reach_thresholds": _CUSTOM_REACH}
        )

        assert response.status_code == 201
        assert response.json()["reach_thresholds"] == _CUSTOM_REACH
        assert response.json()["sun_class_thresholds"] == _DEFAULT_SUN


_REFUSED = [
    # A misspelt key must not be dropped silently (the stored value would fall back to the default).
    pytest.param({"reach_thresholds": {"both_sides_m": 1.5, "one_sides_m": 0.8}}, id="reach-misspelt-key"),
    pytest.param({"sun_class_thresholds": {"full_sun_min_hours": 6, "shade_min_hour": 2}}, id="sun-misspelt-key"),
    # These two reach the ``> 0`` rule alone: every ordering rule holds for them (counter-probed, #2667).
    pytest.param({"reach_thresholds": {"both_sides_m": 1.2, "one_side_m": 0}}, id="reach-one-zero-only-positivity"),
    pytest.param({"sun_class_thresholds": {"shade_min_hours": 0}}, id="sun-shade-zero-only-positivity"),
    # Refused by the ``> 0`` rule and by the ordering rule as well.
    pytest.param({"reach_thresholds": {"both_sides_m": 0}}, id="reach-both-zero"),
    pytest.param({"reach_thresholds": {"one_side_m": -0.6}}, id="reach-one-negative"),
    pytest.param({"reach_thresholds": {"both_sides_m": 1.0, "one_side_m": 1.2}}, id="reach-one-above-both"),
    # #2703: the path distance is 0 m (touching) up to 1 m.
    pytest.param({"reach_thresholds": {"path_access_max_distance_m": -0.1}}, id="path-distance-negative"),
    pytest.param({"reach_thresholds": {"path_access_max_distance_m": 30}}, id="path-distance-above-bound"),
    pytest.param({"reach_thresholds": {"path_access_max_distance_m": "0.3m"}}, id="path-distance-no-number"),
    pytest.param({"sun_class_thresholds": {"full_sun_min_hours": 0}}, id="sun-full-zero"),
    pytest.param({"sun_class_thresholds": {"shade_min_hours": -1}}, id="sun-shade-negative"),
    pytest.param({"sun_class_thresholds": {"partial_shade_min_hours": 0}}, id="sun-partial-zero"),
    pytest.param(
        {"sun_class_thresholds": {"full_sun_min_hours": 3, "partial_shade_min_hours": 6}}, id="sun-not-descending"
    ),
    pytest.param({"sun_class_thresholds": {"reference_month": 2, "reference_day": 30}}, id="sun-no-such-day"),
    pytest.param({"sun_class_thresholds": {"full_sun_min_hours": 25}}, id="sun-more-than-a-day"),
]


class TestRefusedValues:
    @pytest.mark.parametrize("fields", _REFUSED)
    def test_an_edit_with_an_invalid_threshold_is_422_and_writes_nothing(
        self, client: TestClient, repo: _Repo, fields: dict[str, Any]
    ) -> None:
        response = _put(client, **fields)

        assert response.status_code == 422
        assert "site" not in repo.written

    @pytest.mark.parametrize("fields", _REFUSED)
    def test_a_create_with_an_invalid_threshold_is_422(self, client: TestClient, fields: dict[str, Any]) -> None:
        response = client.post(f"{_BASE}/sites", json={"name": "Neu", "type": "outdoor", **fields})

        assert response.status_code == 422


class TestOrientationOnALocationEdit:
    def test_a_stored_aspect_derives_the_orientation_over_the_body(self, client: TestClient, repo: _Repo) -> None:
        """``PUT /locations`` keeps ``site_conditions`` (#2623); its aspect, not the body, names the orientation."""
        repo._locations["loc_own"] = repo._locations["loc_own"].model_copy(
            update={"site_conditions": SiteConditions(aspect_deg=225.0)}
        )

        response = client.put(
            f"{_BASE}/locations/loc_own",
            json={"name": "Beet A", "site_key": "site_own", "area_m2": 1.0, "orientation": "north"},
        )

        assert response.status_code == 200
        assert repo.written["location"].orientation == "southwest"

    def test_without_an_aspect_the_body_sets_one_of_the_eight_values(self, client: TestClient, repo: _Repo) -> None:
        response = client.put(
            f"{_BASE}/locations/loc_own",
            json={"name": "Beet A", "site_key": "site_own", "area_m2": 1.0, "orientation": "northwest"},
        )

        assert response.status_code == 200
        assert repo.written["location"].orientation == "northwest"

    def test_an_unknown_orientation_is_422(self, client: TestClient) -> None:
        response = client.put(
            f"{_BASE}/locations/loc_own",
            json={"name": "Beet A", "site_key": "site_own", "area_m2": 1.0, "orientation": "up"},
        )

        assert response.status_code == 422
