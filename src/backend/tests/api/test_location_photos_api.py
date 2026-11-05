"""REQ-053 WP 8.18 (#2661) - the bed-photo routes through the deployed app.

``app.main`` with the real tenant gate, the real ``LocationPhotoService`` / ``GardenResourceService`` and the
in-memory doubles of ``tests/support``. What is pinned here is how a decision reads on the wire: the status, the
code, the response shape #2662 consumes, and that every write route sits behind its gate (a viewer never reaches
the service). The cross-tenant matrix is ``tests/integration/test_garden_plan_tenant_isolation.py``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.mapping import to_response
from app.api.v1.locations.schemas import LocationResponse
from app.common.auth import get_current_user
from app.common.dependencies import (
    get_garden_resource_service,
    get_location_photo_service,
    get_tenant_service,
)
from app.common.enums import AttachmentCategory, TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.user import User
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.location_photo_service import LocationPhotoService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakeObjects,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
from tests.support.location_photo_fakes import FakeLocationPhotoRepo, FakePhotoAttachments

_BASE = "/api/v1/t/own"
_FOREIGN = "/api/v1/t/other"
ME = "u_sabine"


class _Tenants:
    role = TenantRole.GROWER

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=type(self).role, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str) -> None:
        return None


class World:
    def __init__(self) -> None:
        self.repo = FakePlanRepo(FakeSites(make_site()))
        self.repo.locations["bed"] = make_location("bed", "Beet 1")
        self.repo.locations["bed2"] = make_location("bed2", "Beet 2")
        self.attachments = FakePhotoAttachments(self.repo)
        self.photos = LocationPhotoService(
            self.repo._sites, FakeLocationPhotoRepo(self.repo, self.attachments), self.attachments, self._attachments
        )
        plans = GardenPlanService(self.repo._sites, self.repo, photos=self._photo_service)
        self.resources = GardenResourceService(
            self.repo._sites, self.repo, FakeObjects(self.repo), plans, photos=self._photo_service
        )

    def _attachments(self) -> FakePhotoAttachments:
        return self.attachments

    def _photo_service(self) -> LocationPhotoService:
        return self.photos

    def link(self, attachment_id: str, *, created_by: str = ME, key: str = "bed") -> None:
        if attachment_id not in self.attachments.rows:
            self.attachments.add(attachment_id, tenant_key=TENANT, created_by=created_by)
        self.photos.add_photo(key, attachment_id, tenant_key=TENANT, user_key=created_by, role=TenantRole.LEAD)


@pytest.fixture
def world() -> World:
    return World()


@pytest.fixture
def client(world: World) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(_key=ME, email="s@example.org", display_name="Sabine")
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_location_photo_service] = lambda: world.photos
    app.dependency_overrides[get_garden_resource_service] = lambda: world.resources
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def _detail_codes(response) -> list[str]:
    return [item.get("code") for item in response.json().get("details", [])]


class TestTheResponseShape:
    def test_get_lists_the_photos_newest_first_with_cover_uris_and_can_remove(self, client, world) -> None:
        world.link("p1")
        world.link("p2", created_by="u_tom")

        response = client(TenantRole.VIEWER).get(f"{_BASE}/locations/bed/photos")

        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"location_key", "cover_photo_ref", "photos", "max_photos"}
        assert body["location_key"] == "bed" and body["cover_photo_ref"] == "p1" and body["max_photos"] == 50
        assert [photo["attachment_id"] for photo in body["photos"]] == ["p2", "p1"]
        first = body["photos"][1]
        assert set(first) == {
            "attachment_id",
            "uri",
            "thumbnail_uris",
            "mime_type",
            "byte_size",
            "caption",
            "taken_on",
            "created_at",
            "is_cover",
            "can_remove",
        }
        assert first["uri"] == "/api/v1/t/own/attachments/p1" and first["is_cover"] is True
        assert first["thumbnail_uris"]["small"] == "/api/v1/t/own/attachments/p1/thumbnails/128"
        assert [photo["can_remove"] for photo in body["photos"]] == [False, False]  # a viewer removes nothing
        assert "storage_key" not in response.text and "u_tom" not in response.text and "created_by" not in response.text

    def test_the_bed_answer_carries_its_cover_but_not_the_list(self, world) -> None:
        """``GET /locations/{key}`` and the bed list map through ``LocationResponse``: the cover id, no gallery."""
        world.link("p1")
        world.link("p2")

        response = to_response(world.repo.locations["bed"], LocationResponse).model_dump(mode="json")

        assert response["cover_photo_ref"] == "p1" and "photo_refs" not in response


class TestAdd:
    def test_a_grower_links_an_uploaded_bed_photo(self, client, world) -> None:
        world.attachments.add("p1", tenant_key=TENANT)

        response = client(TenantRole.GROWER).post(f"{_BASE}/locations/bed/photos", json={"attachment_id": "p1"})

        assert response.status_code == 201
        assert response.json()["cover_photo_ref"] == "p1" and world.repo.locations["bed"].photo_refs == ["p1"]
        assert response.json()["photos"][0]["can_remove"] is True

    @pytest.mark.parametrize(
        ("tenant", "category"),
        [(OTHER_TENANT, AttachmentCategory.LOCATION), (TENANT, AttachmentCategory.PLANT), (None, None)],
        ids=["foreign_attachment", "wrong_category", "absent"],
    )
    def test_anything_but_the_tenants_bed_photo_is_422_reference_not_found(self, client, world, tenant, category):
        if tenant is not None:
            world.attachments.add("p_x", tenant_key=tenant, category=category)

        response = client().post(f"{_BASE}/locations/bed/photos", json={"attachment_id": "p_x"})

        assert response.status_code == 422 and _detail_codes(response) == ["reference.not_found"]
        assert world.repo.locations["bed"].photo_refs == []

    def test_a_viewer_is_refused_at_the_gate(self, client, world) -> None:
        world.attachments.add("p1", tenant_key=TENANT)

        response = client(TenantRole.VIEWER).post(f"{_BASE}/locations/bed/photos", json={"attachment_id": "p1"})

        assert response.status_code == 403 and world.repo.locations["bed"].photo_refs == []

    def test_a_foreign_bed_is_404(self, client, world) -> None:
        world.attachments.add("p1", tenant_key=OTHER_TENANT)

        response = client(TenantRole.LEAD).post(f"{_FOREIGN}/locations/bed/photos", json={"attachment_id": "p1"})

        assert response.status_code == 404 and world.repo.locations["bed"].photo_refs == []

    @pytest.mark.parametrize(
        "body", [{}, {"attachment_id": ""}, {"attachment_id": "x" * 65}, {"attachment_id": "p", "x": 1}]
    )
    def test_a_malformed_body_is_422(self, client, body) -> None:
        assert client().post(f"{_BASE}/locations/bed/photos", json=body).status_code == 422


class TestTheKeyIsBounded:
    """SEC-003: a bed key longer than an ArangoDB document key (254) is refused before any lookup."""

    @pytest.mark.parametrize(
        ("method", "suffix", "body"),
        [
            ("get", "/photos", None),
            ("post", "/photos", {"attachment_id": "p1"}),
            ("put", "/photos/cover", {"attachment_id": None}),
            ("delete", "/photos/p1", None),
        ],
        ids=["list", "add", "cover", "remove"],
    )
    def test_an_overlong_key_is_422_and_a_maximal_one_is_looked_up(self, client, method, suffix, body) -> None:
        def call(key: str):
            request = getattr(client(TenantRole.LEAD), method)
            url = f"{_BASE}/locations/{key}{suffix}"
            return request(url, json=body) if body is not None else request(url)

        assert call("k" * 255).status_code == 422
        # The control: 254 characters pass the bound and reach the lookup, which finds no such bed.
        assert call("k" * 254).status_code == 404


class TestCover:
    def test_the_cover_must_be_a_photo_of_the_bed_and_null_clears_it(self, client, world) -> None:
        world.link("p1")
        world.link("p2")
        world.link("elsewhere", key="bed2")

        chosen = client().put(f"{_BASE}/locations/bed/photos/cover", json={"attachment_id": "p2"})
        refused = client().put(f"{_BASE}/locations/bed/photos/cover", json={"attachment_id": "elsewhere"})
        cleared = client().put(f"{_BASE}/locations/bed/photos/cover", json={"attachment_id": None})

        assert chosen.status_code == 200 and chosen.json()["cover_photo_ref"] == "p2"
        assert refused.status_code == 422 and refused.json()["error_code"] == "location.cover_not_a_photo"
        assert cleared.status_code == 200 and cleared.json()["cover_photo_ref"] is None

    def test_a_viewer_is_refused_at_the_gate(self, client, world) -> None:
        world.link("p1")

        response = client(TenantRole.VIEWER).put(f"{_BASE}/locations/bed/photos/cover", json={"attachment_id": None})

        assert response.status_code == 403 and world.repo.locations["bed"].cover_photo_ref == "p1"


class TestRemove:
    def test_a_grower_removes_an_own_photo_and_the_cover_is_cleared(self, client, world) -> None:
        world.link("p1")

        response = client(TenantRole.GROWER).delete(f"{_BASE}/locations/bed/photos/p1")

        assert response.status_code == 200 and response.json() == {
            "location_key": "bed",
            "cover_photo_ref": None,
            "photos": [],
            "max_photos": 50,
        }
        assert world.attachments.deleted == ["p1"]

    def test_another_members_photo_is_lead_only(self, client, world) -> None:
        world.link("theirs", created_by="u_tom")

        refused = client(TenantRole.GROWER).delete(f"{_BASE}/locations/bed/photos/theirs")
        assert refused.status_code == 403 and world.repo.locations["bed"].photo_refs == ["theirs"]

        removed = client(TenantRole.LEAD).delete(f"{_BASE}/locations/bed/photos/theirs")
        assert removed.status_code == 200 and world.attachments.deleted == ["theirs"]

    def test_a_viewer_is_refused_at_the_gate(self, client, world) -> None:
        world.link("p1")

        assert client(TenantRole.VIEWER).delete(f"{_BASE}/locations/bed/photos/p1").status_code == 403
        assert world.repo.locations["bed"].photo_refs == ["p1"]

    def test_a_photo_the_bed_does_not_show_is_404(self, client, world) -> None:
        world.link("elsewhere", key="bed2")

        response = client(TenantRole.LEAD).delete(f"{_BASE}/locations/bed/photos/elsewhere")

        assert response.status_code == 404 and world.attachments.deleted == []


class TestTheBedDelete:
    def test_deleting_the_bed_deletes_its_photos_but_not_one_another_bed_shows(self, client, world) -> None:
        world.link("own")
        world.link("shared")
        world.link("shared", key="bed2")

        response = client(TenantRole.LEAD).delete(f"{_BASE}/locations/bed")

        assert response.status_code == 204 and "bed" not in world.repo.locations
        assert world.attachments.deleted == ["own"]
        assert world.repo.locations["bed2"].photo_refs == ["shared"] and "shared" in world.attachments.rows

    def test_a_failing_discard_does_not_turn_the_committed_delete_into_a_500(self, client, world) -> None:
        world.link("own")
        world.attachments.fail_with = TimeoutError("storage unreachable")

        response = client(TenantRole.LEAD).delete(f"{_BASE}/locations/bed")

        assert response.status_code == 204 and "bed" not in world.repo.locations
