"""REQ-053 WP 4.1 (#2400) — the care-log routes through the deployed app.

``app.main`` with the real ``CareEventService``, the real tenant gate and the in-memory doubles of
``tests/support/care_event_fakes.py``. The unit tier shows what the service decides; this tier shows how a
decision reads on the wire: the status, the dotted code, that the response never carries an account key, that a
body cannot carry the server-owned fields, and — per endpoint — that **another tenant's event answers 404**
(GP-NFR-050: the cross-tenant negative test of every route) with a body that names nothing about it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_care_event_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.user import User
from app.domain.services.care_event_service import CareEventService
from tests.support.care_event_fakes import (
    FakeAttachmentRepo,
    FakeAttachmentService,
    FakeCareEventRepo,
    FakeFertilizers,
    FakeMemberships,
)
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)

_OWN = "/api/v1/t/own/care-events"
_OTHER = "/api/v1/t/other/care-events"

#: Keys that name an account or the tenant; none of them may appear in a response.
_FORBIDDEN_FIELDS = (
    "tenant_key",
    "performed_by_user_key",
    "performed_for_user_key",
    "created_by",
    "voided_by",
    "redacted_by",
)


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


@pytest.fixture
def world() -> SimpleNamespace:
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed", geometry=rect(1, 1, 2, 1))
    repo = FakeCareEventRepo()
    repo.plants = {"pi_here": (TENANT, "bed"), "pi_foreign": (OTHER_TENANT, "bed")}
    attachments = FakeAttachmentRepo()
    attachment_service = FakeAttachmentService()
    service = CareEventService(repo, sites, FakeMemberships(), FakeFertilizers(), attachments, attachment_service)
    return SimpleNamespace(repo=repo, attachments=attachments, attachment_service=attachment_service, service=service)


@pytest.fixture
def client(world) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_care_event_service] = lambda: world.service
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def body(**overrides) -> dict:
    return {
        "location_key": "bed",
        "category": "watering",
        "summary": "Watered the tomatoes",
        "performed_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        **overrides,
    }


def corrected(**overrides) -> dict:
    return {k: v for k, v in body(summary="Corrected", **overrides).items() if k != "location_key"}


def logged(client, **overrides) -> dict:
    response = client().post(_OWN, json=body(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


class TestLogging:
    def test_a_care_event_is_created_for_the_caller(self, client, world) -> None:
        created = logged(client, plant_keys=["pi_here"], quantity=2.0, unit="l_per_m2")

        assert created["performed_by"] == "Sabine"
        assert created["created_by_me"] is True
        assert (created["trigger"], created["site_key"], created["location_key"]) == ("manual", "site_1", "bed")
        assert created["quantity_total"] == 4.0
        stored = world.repo.events[created["key"]]
        assert (stored.tenant_key, stored.performed_by_user_key, stored.created_by) == (TENANT, "u_sabine", "u_sabine")

    def test_no_response_field_names_an_account_or_the_tenant(self, client) -> None:
        created = logged(client, performed_for_user_key="u_lead")

        assert created["performed_for"] == "Lena"
        for name in _FORBIDDEN_FIELDS:
            assert name not in created

    @pytest.mark.parametrize(
        "forged",
        [
            {"trigger": "task"},
            {"trigger": "backfill"},
            {"task_key": "task_1"},
            {"source_ref": {"collection": "feeding_events", "key": "fe_1"}},
            {"created_by": "u_other"},
            {"performed_by_user_key": "u_other"},
            {"tenant_key": OTHER_TENANT},
            {"site_key": "site_foreign"},
            {"quantity_total": 99.0},
            {"supersedes_key": "ce_1"},
            {"voided_at": "2026-01-01T00:00:00Z"},
        ],
    )
    def test_a_body_cannot_carry_a_server_owned_field(self, client, world, forged) -> None:
        response = client().post(_OWN, json=body(**forged))

        assert response.status_code == 422
        assert world.repo.inserted == []

    def test_a_server_only_category_is_a_422(self, client, world) -> None:
        response = client().post(_OWN, json=body(category="bed_status_change"))

        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "care_event.category_server_only"
        assert world.repo.inserted == []

    def test_the_past_and_future_limits_answer_422_with_their_codes(self, client) -> None:
        future = client().post(_OWN, json=body(performed_at=(datetime.now(UTC) + timedelta(minutes=10)).isoformat()))
        old = client().post(_OWN, json=body(performed_at=(datetime.now(UTC) - timedelta(days=400)).isoformat()))

        assert future.status_code == old.status_code == 422
        assert future.json()["details"][0]["code"] == "care_event.performed_in_future"
        assert old.json()["details"][0]["code"] == "care_event.too_old"

    def test_a_viewer_cannot_log(self, client, world) -> None:
        response = client(TenantRole.VIEWER).post(_OWN, json=body())

        assert response.status_code == 403
        assert world.repo.inserted == []


class TestSupersedeVoidRedact:
    def test_a_correction_keeps_both_rows_and_the_list_shows_the_new_one(self, client) -> None:
        first = logged(client)

        second = client().post(f"{_OWN}/{first['key']}/supersede", json=corrected(quantity=3.0, unit="l"))

        assert second.status_code == 201
        assert second.json()["supersedes_key"] == first["key"]
        listed = client().get(_OWN, params={"location_key": "bed"}).json()
        assert [row["key"] for row in listed] == [second.json()["key"]]
        both = client().get(_OWN, params={"location_key": "bed", "include_superseded": "true"}).json()
        assert {row["key"] for row in both} == {first["key"], second.json()["key"]}
        detail = client().get(f"{_OWN}/{second.json()['key']}").json()
        assert detail["chain"] == [first["key"], second.json()["key"]]

    def test_an_entry_cannot_be_patched(self, client) -> None:
        first = logged(client)

        assert client().patch(f"{_OWN}/{first['key']}", json={"summary": "x"}).status_code == 405

    def test_a_second_correction_of_the_same_entry_is_a_422(self, client) -> None:
        first = logged(client)
        client().post(f"{_OWN}/{first['key']}/supersede", json=corrected())

        again = client().post(f"{_OWN}/{first['key']}/supersede", json=corrected())

        assert again.status_code == 422
        assert again.json()["details"][0]["code"] == "care_event.sequence"

    def test_the_author_undoes_an_entry_and_a_grower_cannot_cancel_otherwise(self, client) -> None:
        mine = logged(client)
        other = logged(client)

        undone = client().post(f"{_OWN}/{mine['key']}/void", json={"reason": "undo"})
        refused = client().post(f"{_OWN}/{other['key']}/void", json={"reason": "I changed my mind"})

        assert undone.status_code == 200 and undone.json()["void_reason"] == "undo"
        assert refused.status_code == 403

    def test_a_lead_voids_with_any_reason_and_redacts(self, client, world) -> None:
        world.attachments.add("att_1", created_by="u_sabine")
        entry = logged(client, summary="Frau Mueller hat gegossen", photo_refs=["att_1"])

        voided = client(TenantRole.LEAD).post(f"{_OWN}/{entry['key']}/void", json={"reason": "duplicate"})
        redacted = client(TenantRole.LEAD).post(f"{_OWN}/{entry['key']}/redact", json={"reason": "names a neighbour"})

        assert voided.status_code == 200
        assert redacted.status_code == 200
        assert redacted.json()["summary"] == "[redacted]"
        assert redacted.json()["photo_refs"] == []
        assert world.attachment_service.deleted == [(TENANT, "att_1")]
        assert world.repo.audit[0]["op"] == "redact"

    def test_a_grower_cannot_redact(self, client, world) -> None:
        entry = logged(client)

        response = client().post(f"{_OWN}/{entry['key']}/redact", json={"reason": "x"})

        assert response.status_code == 403
        assert world.repo.events[entry["key"]].summary != "[redacted]"
        assert world.repo.audit == []


class TestReads:
    def test_filters_and_validation(self, client) -> None:
        logged(client, category="feeding", plant_keys=["pi_here"])
        logged(client, category="watering")

        feeding = client().get(_OWN, params={"category": "feeding"}).json()
        by_plant = client().get(_OWN, params={"plant_key": "pi_here"}).json()

        assert [row["category"] for row in feeding] == ["feeding"]
        assert len(by_plant) == 1
        assert client().get(_OWN, params={"category": "no_such"}).status_code == 422
        assert client().get(_OWN, params={"limit": 500}).status_code == 422
        assert (
            client().get(_OWN, params={"from": "2026-06-02T00:00:00Z", "to": "2026-06-01T00:00:00Z"}).status_code == 422
        )

    def test_a_viewer_reads(self, client) -> None:
        entry = logged(client)

        assert client(TenantRole.VIEWER).get(f"{_OWN}/{entry['key']}").status_code == 200
        assert client(TenantRole.VIEWER).get(_OWN).status_code == 200


class TestAnotherTenantSeesNothing:
    """GP-NFR-050, GP-ACC-041 — the cross-tenant negative test of every route.

    The caller is a member of both tenants (the fake gate), so the **path tenant** is the only difference:
    an event of tenant ``own`` is asked for under tenant ``other``.
    """

    def test_every_keyed_route_answers_404_and_names_nothing(self, client, world) -> None:
        entry = logged(client)
        key = entry["key"]

        responses = [
            client(TenantRole.LEAD).get(f"{_OTHER}/{key}"),
            client(TenantRole.LEAD).post(f"{_OTHER}/{key}/supersede", json=corrected()),
            client(TenantRole.LEAD).post(f"{_OTHER}/{key}/void", json={"reason": "x"}),
            client(TenantRole.LEAD).post(f"{_OTHER}/{key}/redact", json={"reason": "x"}),
        ]

        for response in responses:
            assert response.status_code == 404, response.text
            assert all("tenant" not in str(detail) for detail in response.json()["details"])
            assert OTHER_TENANT not in response.text and TENANT not in response.text
        stored = world.repo.events[key]
        assert stored.superseded_by_key is None and stored.voided_at is None and stored.redacted_at is None
        assert world.repo.audit == []

    def test_the_other_tenants_list_is_empty(self, client) -> None:
        logged(client)

        assert client().get(_OTHER).json() == []

    def test_a_bed_of_another_tenant_is_404_and_a_plant_of_another_tenant_is_422(self, client, world) -> None:
        # ``bed`` is tenant-own's; asked for under tenant ``other`` it is a foreign bed.
        foreign_bed = client().post(_OTHER, json=body())
        foreign_plant = client().post(_OWN, json=body(plant_keys=["pi_foreign"]))

        assert foreign_bed.status_code == 404
        assert foreign_plant.status_code == 422
        assert foreign_plant.json()["details"][0]["code"] == "reference.not_found"
        assert world.repo.inserted == []

    def test_a_foreign_photo_a_foreign_product_and_a_foreign_member_are_422(self, client, world) -> None:
        world.attachments.add("att_foreign", tenant_key=OTHER_TENANT)

        for overrides in (
            {"photo_refs": ["att_foreign"]},
            {"product_ref": {"kind": "fertilizer", "key": "fert_foreign"}},
            {"performed_for_user_key": "u_foreign"},
        ):
            response = client().post(_OWN, json=body(**overrides))
            assert response.status_code == 422, overrides
            assert response.json()["details"][0]["code"] == "reference.not_found"

        assert world.repo.inserted == []

    def test_a_supersedes_target_of_another_tenant_is_404(self, client, world) -> None:
        mine = logged(client)
        world.repo.events[mine["key"]] = world.repo.events[mine["key"]].model_copy(update={"tenant_key": OTHER_TENANT})

        response = client(TenantRole.LEAD).post(f"{_OWN}/{mine['key']}/supersede", json=corrected())

        assert response.status_code == 404
        assert world.repo.events[mine["key"]].superseded_by_key is None
