"""REQ-053 WP 7.14 (#2480) - the underlay on the wire: PUT/DELETE ``/plan/underlay``, the read model, the PDF option.

``app.main`` with the real tenant gate; the repository and the attachments are doubles. What is measured is what a
client receives: the role gate, the 422 of a non-finite number (``Infinity`` once answered 500 on a sibling route),
the 422 ``reference.not_found`` of an attachment that is not the caller's own, the plan read model carrying the
calibration for every member, and the JSON export that never does.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import (
    get_auth_provider,
    get_garden_plan_export_service,
    get_garden_plan_service,
    get_garden_plan_underlay_service,
    get_tenant_service,
)
from app.common.enums import AttachmentCategory, TenantRole
from app.domain.models.site import SitePlan
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_plan_underlay_service import GardenPlanUnderlayService
from tests.api.test_garden_plan_export_api import _Tenants, _Tokens
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)
from tests.support.underlay_fakes import FakeUnderlayAttachments

_BASE = "/api/v1/t/own"
_UNDERLAY = f"{_BASE}/sites/{SITE}/plan/underlay"
_PLAN = f"{_BASE}/sites/{SITE}/plan"
_PDF = f"{_BASE}/print/garden-plan/{SITE}"
_BODY = {
    "attachment_key": "att_1",
    "calibration": {"p1_px": [100, 200], "p2_px": [500, 200], "distance_m": 4.0},
    "origin": [1.0, 5.0],
    "rotation_deg": 15.0,
    "opacity": 0.4,
}


@pytest.fixture
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 6, "rotation_deg": 0}, plan_revision=4
    )
    repository = FakePlanRepo(FakeSites(site))
    repository.locations["bed"] = make_location("bed", "Beet 1", geometry=rect(1, 1, 2, 1))
    return repository


@pytest.fixture
def attachments() -> FakeUnderlayAttachments:
    fake = FakeUnderlayAttachments()
    fake.add("att_1", tenant_key=TENANT)
    fake.add("att_foreign", tenant_key=OTHER_TENANT)
    fake.add("att_plant", tenant_key=TENANT, category=AttachmentCategory.PLANT)
    return fake


@pytest.fixture
def client(repo: FakePlanRepo, attachments: FakeUnderlayAttachments) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    plan_service = GardenPlanService(repo._sites, repo)
    export_service = GardenPlanExportService(
        repo._sites, repo, plan_service, attachment_service=attachments.as_service()
    )
    underlay_service = GardenPlanUnderlayService(repo._sites, repo, attachments, attachments.as_service())  # type: ignore[arg-type]
    app.dependency_overrides[get_auth_provider] = _Tokens
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_garden_plan_service] = lambda: plan_service
    app.dependency_overrides[get_garden_plan_export_service] = lambda: export_service
    app.dependency_overrides[get_garden_plan_underlay_service] = lambda: underlay_service
    _Tenants.role = TenantRole.GROWER

    def build() -> TestClient:
        http = TestClient(app)
        http.headers["Authorization"] = "Bearer token-sabine"
        return http

    try:
        yield build
    finally:
        _Tenants.role = TenantRole.VIEWER
        app.dependency_overrides.clear()


class TestPut:
    def test_it_stores_the_calibration_and_every_member_reads_it_with_the_plan(self, client) -> None:
        response = client().put(_UNDERLAY, json=_BODY)

        assert response.status_code == 200
        assert response.json()["calibration"] == _BODY["calibration"]
        _Tenants.role = TenantRole.VIEWER
        settings = client().get(_PLAN).json()["plan"]
        assert settings["underlay"]["attachment_key"] == "att_1" and settings["underlay"]["opacity"] == 0.4
        assert settings["plan_revision"] == 4, "the picture is not a structural change"

    def test_a_viewer_is_refused(self, client) -> None:
        _Tenants.role = TenantRole.VIEWER

        assert client().put(_UNDERLAY, json=_BODY).status_code == 403

    @pytest.mark.parametrize("attachment", ["att_foreign", "att_plant", "att_nobody"])
    def test_an_attachment_that_is_not_my_underlay_is_a_422_reference_not_found(self, client, attachment) -> None:
        response = client().put(_UNDERLAY, json={**_BODY, "attachment_key": attachment})

        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "reference.not_found"
        assert OTHER_TENANT not in response.text

    @pytest.mark.parametrize(
        "patch",
        [
            {"opacity": "NaN"},
            {"rotation_deg": "Infinity"},
            {"origin": ["-Infinity", 0]},
            {"calibration": {**_BODY["calibration"], "distance_m": "Infinity"}},
            {"calibration": {**_BODY["calibration"], "p1_px": ["NaN", 0]}},
            {"calibration": {**_BODY["calibration"], "p2_px": [100, 200]}},
            {"calibration": {**_BODY["calibration"], "distance_m": 0}},
        ],
    )
    def test_non_finite_and_degenerate_numbers_are_a_422_never_a_500(self, client, patch) -> None:
        text = (
            '{"attachment_key":"att_1","calibration":'
            + _json(patch.get("calibration", _BODY["calibration"]))
            + ',"origin":'
            + _json(patch.get("origin", _BODY["origin"]))
            + ',"rotation_deg":'
            + _json(patch.get("rotation_deg", _BODY["rotation_deg"]))
            + ',"opacity":'
            + _json(patch.get("opacity", _BODY["opacity"]))
            + "}"
        )

        response = client().put(_UNDERLAY, content=text, headers={"Content-Type": "application/json"})

        assert response.status_code == 422, response.text

    def test_a_site_of_another_tenant_is_a_404(self, client) -> None:
        response = client().put(f"{_BASE}/sites/site_foreign/plan/underlay", json=_BODY)

        assert response.status_code == 404


def _json(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "[" + ",".join(_json(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(f'"{key}":{_json(item)}' for key, item in value.items()) + "}"
    return repr(value)


class TestDelete:
    def test_it_removes_the_picture_and_is_idempotent(self, client, attachments) -> None:
        client().put(_UNDERLAY, json=_BODY)

        assert client().delete(_UNDERLAY).status_code == 204
        assert client().delete(_UNDERLAY).status_code == 204

        assert client().get(_PLAN).json()["plan"].get("underlay") is None
        assert attachments.deleted == [("att_1", TENANT)]

    def test_a_viewer_is_refused(self, client) -> None:
        _Tenants.role = TenantRole.VIEWER

        assert client().delete(_UNDERLAY).status_code == 403


class TestNeverExportedAndPrintedOnlyOnRequest:
    def test_the_json_export_does_not_carry_it(self, client) -> None:
        client().put(_UNDERLAY, json=_BODY)

        response = client().get(f"{_PLAN}/export")

        assert response.status_code == 200
        assert "underlay" not in response.text and "att_1" not in response.text

    def test_the_svg_never_carries_it(self, client) -> None:
        client().put(_UNDERLAY, json=_BODY)

        response = client().get(f"{_PLAN}/render.svg")

        assert "<image" not in response.text and "att_1" not in response.text

    def test_the_pdf_is_a_pdf_with_and_without_the_option(self, client) -> None:
        client().put(_UNDERLAY, json=_BODY)

        assert client().get(_PDF).content[:5] == b"%PDF-"
        assert client().get(_PDF, params={"underlay": "true"}).content[:5] == b"%PDF-"
        assert client().get(_PDF, params={"underlay": "maybe"}).status_code == 422
