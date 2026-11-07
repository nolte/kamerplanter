"""REQ-053 WP 4.1 (#2400) — the care-log routes through the deployed app.

``app.main`` with the real ``CareEventService``, the real tenant gate and the in-memory doubles of
``tests/support/care_event_fakes.py``. The unit tier shows what the service decides; this tier shows how a
decision reads on the wire: the status, the dotted code, that the response never carries an account key, that a
body cannot carry the server-owned fields, and — per endpoint — that **another tenant's event answers 404**
(GP-NFR-050: the cross-tenant negative test of every route) with a body that names nothing about it.
"""

from __future__ import annotations

import json
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

    def test_an_area_dose_of_80_g_per_m2_stores_rate_and_total(self, client) -> None:
        # Review acceptance "area dosing" on the 2 m² test bed: quantity and unit as sent, total = rate × area.
        created = logged(client, category="feeding", quantity=80, unit="g_per_m2")

        assert (created["quantity"], created["unit"]) == (80, "g_per_m2")
        assert (created["quantity_total"], created["quantity_total_unit"]) == (160.0, "g")

    def test_a_zero_dose_per_m2_answers_422_with_its_code(self, client, world) -> None:
        response = client().post(_OWN, json=body(category="feeding", quantity=0, unit="g_per_m2"))

        assert response.status_code == 422
        detail = response.json()["details"][0]
        assert (detail["code"], detail["field"]) == ("care_event.area_dose_not_positive", "quantity")
        assert world.repo.inserted == []

    @pytest.mark.parametrize("literal", ["Infinity", "-Infinity", "NaN"])
    def test_a_quantity_that_is_no_finite_number_answers_422(self, client, world, literal) -> None:
        raw = json.dumps(body(category="feeding", unit="g_per_m2")).rstrip("}") + f', "quantity": {literal}}}'
        response = client().post(_OWN, content=raw, headers={"Content-Type": "application/json"})

        assert response.status_code == 422
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

    def test_a_naive_range_is_read_as_utc(self, client, world) -> None:
        entry = logged(client, performed_at="2026-06-01T10:00:00")
        assert world.repo.events[entry["key"]].performed_at.tzinfo is not None

        inside = client().get(_OWN, params={"from": "2026-06-01T09:00:00", "to": "2026-06-01T11:00:00"}).json()
        outside = client().get(_OWN, params={"from": "2026-06-01T11:00:00", "to": "2026-06-01T12:00:00"}).json()

        assert [row["key"] for row in inside] == [entry["key"]]
        assert outside == []

    def test_a_third_party_label_is_shown_beside_the_account_that_logged_it(self, client) -> None:
        entry = logged(client, performed_by_label="the neighbour")

        assert (entry["performed_by"], entry["performed_by_label"]) == ("Sabine", "the neighbour")

    def test_a_viewer_reads(self, client) -> None:
        entry = logged(client)

        assert client(TenantRole.VIEWER).get(f"{_OWN}/{entry['key']}").status_code == 200
        assert client(TenantRole.VIEWER).get(_OWN).status_code == 200


class TestRangeBounds:
    def test_a_naive_and_an_aware_bound_are_compared_as_utc_not_a_500(self, client) -> None:
        response = client().get(_OWN, params={"from": "2026-06-01T00:00:00", "to": "2026-06-02T00:00:00Z"})

        assert response.status_code == 200

    def test_a_to_before_from_is_422(self, client) -> None:
        response = client().get(_OWN, params={"from": "2026-06-02T00:00:00", "to": "2026-06-01T00:00:00Z"})

        assert response.status_code == 422


class TestFilterByMember:
    """#2411 item 1 (SR-020): a viewer or grower filters by themselves only; a lead (or management) by anyone."""

    @pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER])
    def test_a_viewer_or_grower_may_filter_by_themselves(self, client, role) -> None:
        entry = logged(client)

        response = client(role).get(_OWN, params={"performed_by": "u_sabine"})

        assert response.status_code == 200
        assert [row["key"] for row in response.json()] == [entry["key"]]

    @pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER])
    def test_a_viewer_or_grower_may_not_filter_by_a_colleague(self, client, role) -> None:
        logged(client)

        response = client(role).get(_OWN, params={"performed_by": "u_tom"})

        assert response.status_code == 403

    def test_a_lead_may_filter_by_a_colleague(self, client) -> None:
        logged(client)

        response = client(TenantRole.LEAD).get(_OWN, params={"performed_by": "u_sabine"})

        assert response.status_code == 200 and len(response.json()) == 1


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


class TestCsvDownload:
    """WP 8.4 (#2647, GP-FR-104, GP-API-034): ``GET /care-events?format=csv`` - the list, as a file, under its rules."""

    @staticmethod
    def _text(response) -> str:  # type: ignore[no-untyped-def]
        return response.content.decode("utf-8-sig")

    def test_it_downloads_the_entries_as_utf8_csv_with_bom(self, client) -> None:
        logged(client, summary="Äpfel gegossen", quantity=2.5, unit="l")

        response = client().get(_OWN, params={"format": "csv"})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert response.content.startswith(b"\xef\xbb\xbf")
        assert response.headers["content-disposition"].startswith('attachment; filename="care-events-')
        assert (
            response.headers["x-content-type-options"] == "nosniff" and response.headers["cache-control"] == "no-store"
        )
        header, row = self._text(response).splitlines()[:2]
        assert header.startswith("performed_at,category,summary,")
        assert "Äpfel gegossen" in row and "2.5" in row

    def test_a_formula_in_an_entry_is_neutralised_on_the_wire(self, client) -> None:
        logged(client, summary='=HYPERLINK("http://evil")')

        text = self._text(client().get(_OWN, params={"format": "csv"}))

        assert "'=HYPERLINK" in text and ",=HYPERLINK" not in text

    def test_the_semicolon_variant_uses_the_semicolon(self, client) -> None:
        logged(client)

        header = self._text(client().get(_OWN, params={"format": "csv", "delimiter": "semicolon"})).splitlines()[0]

        assert header.startswith("performed_at;category;")

    def test_the_excel_variant_has_a_semicolon_and_a_decimal_comma(self, client) -> None:
        logged(client, quantity=2.5, unit="l")

        row = self._text(client().get(_OWN, params={"format": "csv", "delimiter": "semicolon"})).splitlines()[1]

        assert ";2,5;l;" in row
        assert ",2.5,l," in self._text(client().get(_OWN, params={"format": "csv"})).splitlines()[1]

    def test_it_answers_the_same_filters_as_the_json(self, client) -> None:
        logged(client, category="watering", summary="water")
        logged(client, category="feeding", summary="feed")

        csv_rows = self._text(client().get(_OWN, params={"format": "csv", "category": "feeding"})).splitlines()
        json_rows = client().get(_OWN, params={"category": "feeding"}).json()

        assert len(csv_rows) - 1 == len(json_rows) == 1 and "feed" in csv_rows[1]

    def test_no_account_key_is_in_the_file(self, client) -> None:
        logged(client)

        text = self._text(client().get(_OWN, params={"format": "csv"}))

        assert "u_sabine" not in text and "Sabine" in text  # the display name, never the key

    @pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER])
    def test_a_viewer_or_grower_filtering_by_a_colleague_is_403_for_csv_too(self, client, role) -> None:
        logged(client)

        response = client(role).get(_OWN, params={"format": "csv", "performed_by": "u_tom"})

        assert response.status_code == 403
        # counter-case: on themselves it is allowed, so the 403 above is the role rule
        assert client(role).get(_OWN, params={"format": "csv", "performed_by": "u_sabine"}).status_code == 200

    def test_a_lead_may_filter_the_csv_by_a_colleague(self, client) -> None:
        logged(client)

        assert (
            client(TenantRole.LEAD).get(_OWN, params={"format": "csv", "performed_by": "u_sabine"}).status_code == 200
        )

    def test_another_tenants_log_is_not_in_the_file_and_its_bed_is_a_404(self, client) -> None:
        logged(client)

        other = client(TenantRole.LEAD).get(_OTHER, params={"format": "csv"})
        foreign_bed = client(TenantRole.LEAD).get(_OTHER, params={"format": "csv", "location_key": "bed"})

        assert other.status_code == 200 and len(self._text(other).splitlines()) == 1  # the header only
        assert foreign_bed.status_code == 404

    def test_a_tenant_with_nothing_logged_gets_the_header_only(self, client) -> None:
        text = self._text(client().get(_OWN, params={"format": "csv"}))

        assert len(text.splitlines()) == 1

    def test_more_than_50000_rows_is_422_and_exactly_50000_is_a_file(self, client, world) -> None:
        template = logged(client)
        stored = world.repo.events[template["key"]]
        for index in range(49_999):  # the one above plus 49 999 = 50 000
            world.repo.events[f"bulk{index}"] = stored.model_copy(update={"key": f"bulk{index}"})
        exactly = client().get(_OWN, params={"format": "csv"})
        world.repo.events["one_more"] = stored.model_copy(update={"key": "one_more"})

        refused = client().get(_OWN, params={"format": "csv"})

        assert exactly.status_code == 200 and len(self._text(exactly).splitlines()) == 50_001
        assert refused.status_code == 422
        assert refused.json()["details"][0]["code"] == "export.too_many_rows"

    def test_the_json_list_is_not_counted_against_the_csv_budget(self, client) -> None:
        from app.config.settings import settings

        budget = int(settings.rate_limit_care_events_export.split("/")[0])
        logged(client)

        json_statuses = {client().get(_OWN).status_code for _ in range(budget + 5)}
        csv_statuses = [client().get(_OWN, params={"format": "csv"}).status_code for _ in range(budget + 2)]

        assert json_statuses == {200}
        assert csv_statuses[:budget] == [200] * budget and csv_statuses[budget:] == [429, 429]


class TestClientEventId:
    """REQ-053 WP 9.3: a buffered care event replayed with its ``client_event_id`` is answered, never stored twice."""

    def test_a_replay_answers_200_with_the_same_event(self, client, world) -> None:
        payload = body(client_event_id="5f7c7c1e-0b55-4c2b-9a8e-2b2f0b1e6a11")

        first = client().post(_OWN, json=payload)
        replays = [client().post(_OWN, json=payload) for _ in range(2)]

        assert first.status_code == 201, first.text
        assert [r.status_code for r in replays] == [200, 200]
        assert all(r.json() == first.json() for r in replays)  # the same body shape as the first answer
        assert first.json()["client_event_id"] == payload["client_event_id"]
        assert len(world.repo.inserted) == 1

    def test_the_same_id_with_another_body_is_409(self, client, world) -> None:
        client_id = "0d6f1d0e-4d4c-4f61-8d8f-4b0e5a4f2c11"
        assert client().post(_OWN, json=body(client_event_id=client_id)).status_code == 201

        response = client().post(_OWN, json=body(client_event_id=client_id, summary="Something else"))

        assert response.status_code == 409, response.text
        assert response.json()["error_code"] == "client_event.payload_mismatch"
        assert len(world.repo.inserted) == 1

    def test_an_id_that_is_no_uuid_is_422(self, client, world) -> None:
        response = client().post(_OWN, json=body(client_event_id="not-a-uuid"))

        assert response.status_code == 422
        assert world.repo.inserted == []

    def test_without_an_id_every_post_is_a_new_event(self, client, world) -> None:
        # The positive control: the replay rule needs the id; two plain posts stay two entries.
        assert [client().post(_OWN, json=body()).status_code for _ in range(2)] == [201, 201]
        assert len(world.repo.inserted) == 2
