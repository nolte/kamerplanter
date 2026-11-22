"""REQ-053 GP-FR-052 / GP-UX-028 (#2899) — the bed label PDF on the wire.

``app.main`` with the real print service, the real print engine (WeasyPrint), the real tenant gate and the real
``get_current_user``; only the auth provider, the tenant lookup and the site reads are doubles. What is measured is
what a client receives: the status, the attachment header, the bed's name and site in the PDF's text layer, and the
QR code's URL as the link annotation of the code - the same string the QR image encodes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.common.dependencies import get_auth_provider, get_print_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError, UnauthorizedError
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.models.location_type import LocationType
from app.domain.models.site import Location, Site
from app.domain.models.user import User
from app.domain.services.print_service import PrintService
from tests.support.pdf_text import pdf_text

_TENANT = "ten_own"
_OTHER = "ten_other"
_BASE = "/api/v1/t/own/print/location-label"
_APP = "https://garden.example.org"


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
    """``own`` is the caller's tenant; the caller is an active member with ``role``."""

    role = TenantRole.VIEWER

    def get_tenant_by_slug(self, slug: str):
        if slug != "own":
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=_TENANT, slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str):
        return SimpleNamespace(role=type(self).role, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str):
        return None


class _Sites:
    """The anchor reads of ``location_ownership``: one own site with a bed and a shed, one foreign site with a bed."""

    def __init__(self) -> None:
        self.sites = {
            "site_own": Site(_key="site_own", tenant_key=_TENANT, name="Schrebergarten", type="outdoor"),
            "site_foreign": Site(_key="site_foreign", tenant_key=_OTHER, name="Nachbarsgarten", type="outdoor"),
        }
        self.locations = {
            "bed_1": Location(
                _key="bed_1", name="Hochbeet Süd", site_key="site_own", location_type_key="raised_bed", area_m2=2.4
            ),
            "shed": Location(
                _key="shed", name="Geräteschuppen", site_key="site_own", location_type_key="room", area_m2=0
            ),
            "bed_foreign": Location(
                _key="bed_foreign",
                name="Fremdes Beet",
                site_key="site_foreign",
                location_type_key="raised_bed",
                area_m2=3,
            ),
        }

    def get_site_by_key(self, key):
        return self.sites.get(key)

    def get_location_by_key(self, key):
        return self.locations.get(key)

    def get_slot_by_key(self, key):
        return None


class _Types:
    _types = {
        "raised_bed": LocationType(_key="raised_bed", name="Hochbeet", name_en="Raised bed", is_bed=True),
        "room": LocationType(_key="room", name="Raum", name_en="Room"),
    }

    def get_by_key(self, key):
        return self._types.get(key)


def _service() -> PrintService:
    return PrintService(
        nutrient_plan_service=MagicMock(),
        care_reminder_service=MagicMock(),
        fertilizer_repo=MagicMock(),
        plant_repo=MagicMock(),
        species_repo=MagicMock(),
        site_repo=_Sites(),  # type: ignore[arg-type]
        app_base_url=_APP,
        location_type_repo=_Types(),  # type: ignore[arg-type]
    )


def _link_uris(content: bytes) -> list[str]:
    """Every URI link annotation of the PDF, page by page."""
    uris: list[str] = []
    for page in PdfReader(BytesIO(content)).pages:
        for annotation in page.get("/Annots") or []:
            action = annotation.get_object().get("/A")
            if action is not None and "/URI" in action:
                uris.append(str(action["/URI"]))
    return uris


@pytest.fixture
def client() -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    app.dependency_overrides[get_auth_provider] = _Tokens
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_print_service] = _service

    def build(token: str | None = "token-sabine") -> TestClient:
        http = TestClient(app)
        if token is not None:
            http.headers["Authorization"] = f"Bearer {token}"
        return http

    try:
        yield build
    finally:
        _Tenants.role = TenantRole.VIEWER
        app.dependency_overrides.clear()


class TestTheBedLabel:
    def test_it_is_a_pdf_attachment_naming_the_bed_its_site_type_and_area(self, client) -> None:
        response = client().get(f"{_BASE}/bed_1")

        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"] == 'attachment; filename="bed-label-bed_1.pdf"'
        lines = pdf_text(response.content).splitlines()
        assert "Beet-Etikett" in lines and "Hochbeet Süd" in lines
        assert {"Standort: Schrebergarten", "Typ: Hochbeet", "Fläche: 2,4 m²"} <= set(lines)
        assert "Scanne den QR-Code: Er öffnet das Beet im Feldmodus." in lines

    def test_the_qr_code_opens_the_bed_in_field_mode(self, client) -> None:
        response = client().get(f"{_BASE}/bed_1", params={"qr_size_mm": 25})

        assert response.status_code == 200, response.text
        # The link of the QR code is the URL the code encodes (one string, `location_label_url`).
        assert set(_link_uris(response.content)) == {f"{_APP}/standorte/sites/site_own/plan?mode=field&bed=bed_1"}

    def test_another_location_opens_its_own_page_and_prints_no_area_of_zero(self, client) -> None:
        response = client().get(f"{_BASE}/shed", params={"locale": "en"})

        assert response.status_code == 200, response.text
        assert set(_link_uris(response.content)) == {f"{_APP}/standorte/locations/shed"}
        lines = pdf_text(response.content).splitlines()
        assert "Location label" in lines and "Type: Room" in lines
        assert not [line for line in lines if line.startswith("Area")]

    def test_every_member_may_print_it(self, client) -> None:
        for role in TenantRole:
            _Tenants.role = role
            assert client().get(f"{_BASE}/bed_1").status_code == 200, role


class TestTheRefusals:
    def test_a_bed_of_another_tenant_is_not_found_and_leaks_nothing(self, client) -> None:
        response = client().get(f"{_BASE}/bed_foreign")

        assert response.status_code == 404, response.text
        assert "Fremdes Beet" not in response.text and "Nachbarsgarten" not in response.text

    def test_an_absent_location_is_not_found(self, client) -> None:
        assert client().get(f"{_BASE}/missing").status_code == 404

    def test_without_a_session_it_is_refused(self, client) -> None:
        assert client(token=None).get(f"{_BASE}/bed_1").status_code == 401

    @pytest.mark.parametrize("size", [19, 61])
    def test_a_qr_size_outside_20_to_60_mm_is_refused(self, client, size: int) -> None:
        assert client().get(f"{_BASE}/bed_1", params={"qr_size_mm": size}).status_code == 422
