"""REQ-053 WP 5.2 (#2431) — the plan SVG, the PDF and the JSON backup on the wire.

``app.main`` with the real export service, the real tenant gate and the real ``get_current_user`` (only the auth
provider and the repository are doubles), so what is measured is what a client receives: the status, the headers
GP-NFR-052 (e) prescribes **as they leave the middleware stack** (the app's own security-headers middleware writes
a Content-Security-Policy of its own; the route's has to survive it), the 422 of a query that is not in the
vocabulary, the 404 of a foreign site, and the two rate-limit buckets of GP-NFR-056.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterator
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import (
    get_auth_provider,
    get_garden_plan_export_service,
    get_garden_plan_service,
    get_tenant_service,
)
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError, UnauthorizedError
from app.config.settings import settings
from app.domain.engines.plan_svg_engine import ALLOWED_ATTRIBUTES, ALLOWED_ELEMENTS
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.interfaces.plant_state_repository import IPlantStateRepository, PlantStateSource
from app.domain.models.garden_plan import PlantShortInfo
from app.domain.models.site import SitePlan
from app.domain.models.user import User
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_service import GardenPlanService
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

_BASE = "/api/v1/t/own"
_SVG = f"{_BASE}/sites/{SITE}/plan/render.svg"
_EXPORT = f"{_BASE}/sites/{SITE}/plan/export"
_PDF = f"{_BASE}/print/garden-plan/{SITE}"
_ROUTES = {"svg": _SVG, "json": _EXPORT, "pdf": _PDF}
HOSTILE = '"><image href="http://169.254.169.254/"/>'
SVG = "{http://www.w3.org/2000/svg}"


class _Tokens(IAuthProvider):
    """``token-<name>`` is the account ``u_<name>``; anything else is unauthenticated."""

    def resolve_user(self, authorization, *, client_ip):
        user = self.resolve_user_optional(authorization, client_ip=client_ip)
        if user is None:
            raise UnauthorizedError("no token")
        return user

    def resolve_user_optional(self, authorization, *, client_ip):
        token = (authorization or "").removeprefix("Bearer ")
        if not token.startswith("token-"):
            return None
        name = token.removeprefix("token-")
        return User(_key=f"u_{name}", email=f"{name}@example.org", display_name=name.title())

    def is_authentication_required(self) -> bool:
        return True


class _Tenants:
    """``own`` is TENANT and ``other`` is OTHER_TENANT; every caller is an active member of both, as a grower."""

    role = TenantRole.VIEWER

    def get_tenant_by_slug(self, slug: str):
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str):
        return SimpleNamespace(role=type(self).role, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str):
        return None


class _OneBedOfStates(IPlantStateRepository):
    """The plant-state source of the one bed ``bed``; records the tenant every read carries."""

    def __init__(self, rows: list[PlantStateSource]) -> None:
        self.rows = rows
        self.tenants: list[str] = []

    def list_bed_plants(self, location_key, *, tenant_key, now, offset, limit):
        self.tenants.append(tenant_key)
        return self.rows[offset : offset + limit] if location_key == "bed" else []

    def list_plants_in_beds(self, bed_keys, *, tenant_key, now, offset, limit):
        self.tenants.append(tenant_key)
        return self.rows[offset : offset + limit] if "bed" in bed_keys else []


class _PhaseNames:
    def __init__(self, names: dict[str, str]) -> None:
        self.names = names

    def get_phase_by_key(self, key):
        return SimpleNamespace(key=key, name=self.names[key]) if key in self.names else None


def _tags_of(root: ET.Element) -> set[str]:
    return {element.tag.removeprefix(SVG) for element in root.iter()}


def _attributes_of(root: ET.Element) -> set[str]:
    return {name for element in root.iter() for name in element.attrib}


@pytest.fixture
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 6, "rotation_deg": 0}, plan_revision=4
    )
    # A site of the other tenant with the same plan: the cross-tenant probes must be refused, not merely empty.
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"})
    repository = FakePlanRepo(FakeSites(site, foreign))
    repository.locations["bed"] = make_location("bed", "Beet 1", geometry=rect(1, 1, 2, 1))
    return repository


@pytest.fixture
def client(repo: FakePlanRepo) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    plan_service = GardenPlanService(repo._sites, repo)
    export_service = GardenPlanExportService(repo._sites, repo, plan_service)
    app.dependency_overrides[get_auth_provider] = _Tokens
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_garden_plan_service] = lambda: plan_service
    app.dependency_overrides[get_garden_plan_export_service] = lambda: export_service

    def build(token: str = "token-sabine") -> TestClient:
        http = TestClient(app)
        http.headers["Authorization"] = f"Bearer {token}"
        return http

    try:
        yield build
    finally:
        _Tenants.role = TenantRole.VIEWER
        app.dependency_overrides.clear()


class TestTheSvgDownload:
    def test_it_is_an_attachment_that_cannot_be_sniffed_or_made_to_load_anything(self, client) -> None:
        response = client().get(_SVG)

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
        assert response.headers["content-disposition"] == f'attachment; filename="garden-plan-{SITE}.svg"'
        assert response.headers["x-content-type-options"] == "nosniff"
        # The route's own policy, not the app-wide one the middleware writes for JSON.
        assert response.headers["content-security-policy"] == "default-src 'none'; style-src 'unsafe-inline'"

    def test_the_body_is_the_scaled_plan(self, client) -> None:
        response = client().get(_SVG)

        root = ET.fromstring(response.text)
        assert root.attrib["data-scale"] == "50" and response.headers["x-plan-scale"] == "1:50"
        assert [e.attrib["data-key"] for e in root.iter(f"{SVG}polygon") if e.attrib.get("data-key")] == ["bed"]

    def test_every_role_may_download_it(self, client) -> None:
        for role in TenantRole:
            _Tenants.role = role
            assert client().get(_SVG).status_code == 200, role

    def test_a_hostile_name_arrives_as_text(self, client, repo) -> None:
        repo.locations["bed"] = make_location("bed", HOSTILE, geometry=rect(1, 1, 2, 1))

        response = client().get(_SVG)

        root = ET.fromstring(response.text)
        assert not list(root.iter(f"{SVG}image"))
        assert HOSTILE in [e.text for e in root.iter(f"{SVG}title")]

    def test_plant_states_and_phase_colours_reach_the_download(self, client, repo) -> None:
        """#2489 smoke: with a plant-state source and a phase name the SVG on the wire carries the phase-coloured
        disc, the badge and the legend entries, and stays inside the allowlist."""
        from app.main import app

        repo.plants = [PlantShortInfo(key="p1", instance_id="P1", species_key="sp", location_key="bed", phase_key="ph")]
        states = _OneBedOfStates(
            [
                PlantStateSource(
                    plant_key="p1",
                    instance_id="P1",
                    species_key="sp",
                    planted_on=date(2026, 4, 1),
                    phase_key="ph",
                    open_finding_count=1,
                )
            ]
        )
        stated = GardenPlanExportService(
            repo._sites,
            repo,
            GardenPlanService(repo._sites, repo),
            plant_state_repo=states,
            phase_repo=_PhaseNames({"ph": "flowering"}),  # type: ignore[arg-type]
        )
        app.dependency_overrides[get_garden_plan_export_service] = lambda: stated

        response = client().get(_SVG, params={"locale": "en"})

        assert response.status_code == 200
        root = ET.fromstring(response.text)
        assert _tags_of(root) <= ALLOWED_ELEMENTS and _attributes_of(root) <= ALLOWED_ATTRIBUTES
        (layer,) = [e for e in root.iter() if e.attrib.get("id") == "layer-plants"]
        assert [c.attrib["fill"] for c in layer.findall(f"{SVG}circle")] == ["#AB47BC"]
        assert len(layer.findall(f"{SVG}g")) == 1, "the one badge (open finding)"
        (legend,) = [e for e in root.iter() if e.attrib.get("id") == "legend"]
        assert {"Phase: Flowering", "Ring: growing", "Triangle: finding"} <= {e.text for e in legend.iter(f"{SVG}text")}
        assert states.tenants == [TENANT]

    def test_the_accent_colour_is_applied_when_it_is_a_hex_colour(self, client) -> None:
        response = client().get(_SVG, params={"color": "#C62828"})

        root = ET.fromstring(response.text)
        (boundary,) = [e for e in root.iter() if e.attrib.get("id") == "layer-boundary"]
        assert boundary[0].attrib["stroke"] == "#C62828"

    def test_layers_and_locale_narrow_and_translate_the_drawing(self, client) -> None:
        response = client().get(_SVG, params={"layers": "grid", "locale": "en"})

        root = ET.fromstring(response.text)
        ids = {e.attrib.get("id") for e in root.iter()}
        assert "layer-grid" in ids and "layer-beds" not in ids
        assert "Maßstäblicher" not in response.text and "Garden plan to scale" in response.text

    def test_a_scale_in_the_vocabulary_is_used(self, client) -> None:
        response = client().get(_SVG, params={"scale": "1:100"})

        assert ET.fromstring(response.text).attrib["data-scale"] == "100"

    def test_a_large_plan_suggests_a3_in_a_header(self, client, repo) -> None:
        repo._sites.sites[SITE].plan = SitePlan(
            boundary={"kind": "rect", "origin": [0, 0], "width_m": 50, "length_m": 36, "rotation_deg": 0},
            plan_revision=1,
        )

        response = client().get(_SVG)

        assert response.headers["x-plan-suggested-paper"] == "a3"

    def test_an_empty_plan_is_a_422_with_its_published_code(self, client, repo) -> None:
        repo._sites.sites[SITE].plan = SitePlan(plan_revision=1)
        repo.locations.clear()

        response = client().get(_SVG)

        assert response.status_code == 422 and response.json()["error_code"] == "plan.empty"


class TestTheQueryVocabulary:
    """GP-NFR-052 (c): nothing outside the enums and the patterns reaches the writer."""

    @pytest.mark.parametrize(
        ("name", "value"),
        [
            ("color", "red"),
            ("color", "C62828"),
            ("color", "#C6282"),
            ("color", '#C62828"><image href="http://169.254.169.254/"/>'),
            ("color", "url(#x)"),
            ("scale", "1:60"),
            ("scale", "50"),
            ("scale", "1:50;x"),
            ("layers", "beds,fish"),
            ("layers", "beds;rm"),
            ("layers", "x" * 65),
            ("locale", "fr"),
            ("locale", "de\nX"),
            ("paper", "a5"),
            ("orientation", "diagonal"),
        ],
    )
    @pytest.mark.parametrize("route", ["svg", "pdf"])
    def test_a_value_outside_the_vocabulary_is_a_422_and_renders_nothing(self, client, route, name, value) -> None:
        response = client().get(_ROUTES[route], params={name: value})

        assert response.status_code == 422, response.text
        assert response.headers["content-type"].startswith("application/json")

    def test_an_unknown_layer_names_the_field(self, client) -> None:
        response = client().get(_SVG, params={"layers": "beds,fish"})

        assert response.json()["details"][0]["field"] == "layers"

    def test_an_empty_layer_list_draws_only_the_always_on_parts(self, client) -> None:
        response = client().get(_SVG, params={"layers": ""})

        assert response.status_code == 200
        ids = {e.attrib.get("id") for e in ET.fromstring(response.text).iter()}
        assert "layer-beds" not in ids and {"layer-boundary", "scale-bar", "north-arrow"} <= ids


class TestTheJsonBackup:
    def test_it_is_a_versioned_attachment(self, client) -> None:
        response = client().get(_EXPORT)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert response.headers["content-disposition"] == f'attachment; filename="garden-plan-{SITE}.json"'
        assert response.headers["x-content-type-options"] == "nosniff"
        body = response.json()
        assert body["schema_version"] == "1"
        assert [loc["key"] for loc in body["locations"]] == ["bed"]
        assert not {"plants", "tasks", "events"} & set(body)

    def test_a_viewer_may_back_up_the_plan(self, client) -> None:
        _Tenants.role = TenantRole.VIEWER

        assert client().get(_EXPORT).status_code == 200


class TestThePdf:
    def test_it_is_a_pdf_attachment_with_the_scale_in_a_header(self, client) -> None:
        response = client().get(_PDF)

        assert response.status_code == 200
        assert response.content[:5] == b"%PDF-"
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"] == f'attachment; filename="garden-plan-{SITE}.pdf"'
        assert response.headers["x-plan-scale"] == "1:50"
        assert "x-plan-suggested-paper" not in response.headers

    def test_a_fixed_scale_that_does_not_fit_is_a_422_naming_scale_and_paper(self, client, repo) -> None:
        repo._sites.sites[SITE].plan = SitePlan(
            boundary={"kind": "rect", "origin": [0, 0], "width_m": 28, "length_m": 20, "rotation_deg": 0},
            plan_revision=1,
        )

        response = client().get(_PDF, params={"scale": "1:20"})

        assert response.status_code == 422
        detail = response.json()["details"][0]
        assert detail["code"] == "plan.does_not_fit" and detail["scale"] == "1:20" and detail["paper"] == "a4"

    def test_the_bed_list_is_optional(self, client) -> None:
        assert client().get(_PDF, params={"bed_list": "true"}).status_code == 200
        assert client().get(_PDF, params={"bed_list": "maybe"}).status_code == 422


class TestAForeignSite:
    """GP-ACC-014 for the exports: a site of another tenant is an absent one, on all three routes."""

    @pytest.mark.parametrize("route", ["svg", "json", "pdf"])
    def test_a_site_of_another_tenant_is_a_404_that_does_not_name_its_owner(self, client, route) -> None:
        urls = {
            "svg": f"{_BASE}/sites/site_foreign/plan/render.svg",
            "json": f"{_BASE}/sites/site_foreign/plan/export",
            "pdf": f"{_BASE}/print/garden-plan/site_foreign",
        }

        response = client().get(urls[route])

        assert response.status_code == 404
        assert response.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert OTHER_TENANT not in json.dumps(response.json()), "the owner of the site must not be named"

    @pytest.mark.parametrize("route", ["svg", "json", "pdf"])
    def test_my_site_under_another_tenants_slug_is_a_404(self, client, route) -> None:
        url = _ROUTES[route].replace("/t/own/", "/t/other/")

        response = client().get(url)

        assert response.status_code == 404

    @pytest.mark.parametrize("route", ["svg", "json", "pdf"])
    def test_an_unknown_site_answers_like_a_foreign_one(self, client, route) -> None:
        url = _ROUTES[route].replace(SITE, "site_nobody")
        foreign = _ROUTES[route].replace(SITE, "site_foreign")

        absent, other = client().get(url), client().get(foreign)

        assert absent.status_code == other.status_code == 404
        assert absent.json()["error_code"] == other.json()["error_code"]

    @pytest.mark.parametrize("route", ["svg", "json", "pdf"])
    def test_without_a_token_nothing_is_served(self, client, route) -> None:
        http = client()
        http.headers.pop("Authorization")

        assert http.get(_ROUTES[route]).status_code == 401


class TestRateLimits:
    """GP-NFR-056: 10 a minute per account and route, 30 a minute per tenant, 429 with ``Retry-After``."""

    def test_the_budgets_are_the_specified_ones(self) -> None:
        assert settings.rate_limit_plan_export == "10/minute"
        assert settings.rate_limit_plan_export_tenant == "30/minute"

    @pytest.mark.parametrize("route", ["svg", "json"])
    def test_the_eleventh_request_of_one_account_is_refused(self, client, route) -> None:
        http = client()
        statuses = [http.get(_ROUTES[route]).status_code for _ in range(10)]
        limited = http.get(_ROUTES[route])

        assert statuses == [200] * 10
        assert limited.status_code == 429
        assert 1 <= int(limited.headers["retry-after"]) <= 60

    def test_the_eleventh_pdf_of_one_account_is_refused(self, client) -> None:
        http = client()
        statuses = [http.get(_PDF, params={"layers": ""}).status_code for _ in range(10)]

        assert statuses == [200] * 10
        assert http.get(_PDF).status_code == 429

    def test_another_account_has_its_own_budget(self, client) -> None:
        for _ in range(10):
            assert client("token-anna").get(_SVG).status_code == 200
        assert client("token-anna").get(_SVG).status_code == 429

        assert client("token-ben").get(_SVG).status_code == 200

    def test_the_tenant_budget_is_shared_by_its_members(self, client) -> None:
        """Four accounts stay under their ten each and still exhaust the tenant's thirty."""
        statuses = [client(f"token-member{member}").get(_SVG).status_code for member in range(4) for _ in range(8)]

        assert statuses[:30] == [200] * 30
        assert statuses[30:] == [429, 429]

    def test_another_tenants_budget_is_untouched_by_an_exhausted_one(self, client) -> None:
        for member in range(3):
            for _ in range(10):
                client(f"token-member{member}").get(_SVG)
        assert client("token-late").get(_SVG).status_code == 429

        other = client("token-late").get(f"{_BASE.replace('own', 'other')}/sites/site_foreign/plan/render.svg")

        assert other.status_code == 200


class TestTenantBudgetIsSharedByTheRoutes:
    def test_svg_json_and_pdf_draw_on_one_tenant_bucket(self, client) -> None:
        """30 a minute for the tenant in total: ten each from three routes use it up, the next is refused."""
        statuses = []
        for member in range(3):
            http = client(f"token-member{member}")
            statuses += [http.get(_SVG).status_code for _ in range(5)]
            statuses += [http.get(_EXPORT).status_code for _ in range(3)]
            statuses += [http.get(_PDF, params={"layers": ""}).status_code for _ in range(2)]
        assert statuses == [200] * 30

        assert client("token-late").get(_EXPORT).status_code == 429


def test_cors_exposes_the_plan_headers(client) -> None:
    response = client().get(_SVG, headers={"Origin": "http://localhost:5173"})

    exposed = response.headers.get("access-control-expose-headers", "")
    assert "X-Plan-Scale" in exposed and "X-Plan-Suggested-Paper" in exposed
