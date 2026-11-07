"""REQ-053 WP 1.9 (#2328) — the single-resource routes through the deployed app.

``app.main`` with the real ``GardenResourceService``, the real tenant gate and the in-memory repository of
``tests/support/garden_plan_fakes.py``. The unit tier shows what the service decides; this tier shows how a
decision reads on the wire — the status, the dotted code, ``details[0].active_plant_count`` — and that every
write route sits behind its gate. The role matrix is run through the gate (a viewer never reaches the
service) and, where the rule is data-dependent, through the service (a grower reaches it and is refused).
Cross-tenant negative tests per endpoint are WP 1.10; the 404 here is the tenant anchor each route shows.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import (
    get_garden_resource_service,
    get_planting_reservation_service,
    get_site_service,
    get_tenant_service,
)
from app.common.enums import BedStatus, NutrientDemand, TenantRole
from app.common.exceptions import NotFoundError
from app.domain.engines.nutrient_hint_engine import DEFAULT_CONFIG, NutrientHintConfig, SourcedThreshold
from app.domain.interfaces.care_event_repository import CareEventRow
from app.domain.models.bed_list_export import BedAssignee
from app.domain.models.care_event import CareEvent
from app.domain.models.garden_plan import BedCounters
from app.domain.models.site import Microclimate, SiteConditions, Slot, SoilProfile
from app.domain.models.species import Species
from app.domain.models.user import User
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.nutrient_hint_service import NutrientHintService
from app.domain.services.site_service import SiteService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakeObjects,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)

_BASE = "/api/v1/t/own"
_FOREIGN = "/api/v1/t/other"


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
def repo() -> FakePlanRepo:
    repository = FakePlanRepo(FakeSites(make_site()))
    repository.locations["bed"] = make_location("bed", name="Bed", geometry=rect(1, 1, 2, 1))
    repository.slots = [
        Slot.model_validate(
            {
                "_key": "s1",
                "slot_id": "BED_P1",
                "location_key": "bed",
                "geometry": {"kind": "point", "origin": [0.5, 0.5]},
            }
        )
    ]
    return repository


@pytest.fixture
def client(repo: FakePlanRepo) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    service = GardenResourceService(repo._sites, repo, FakeObjects(repo), GardenPlanService(repo._sites, repo))

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_garden_resource_service] = lambda: service
    app.dependency_overrides[get_site_service] = lambda: SiteService(repo._sites)
    # The slot correction asks the reservation service for the position event (GP-FR-068); the event is pinned in
    # ``test_planting_reservation_api.py``, here the call is the stub of a bed nobody stands in.
    app.dependency_overrides[get_planting_reservation_service] = lambda: SimpleNamespace(
        record_position_correction=lambda *args, **kwargs: None
    )
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def tree_body(**kw) -> dict:
    return {
        "object_type": "tree",
        "label": "Apple",
        "geometry": {"kind": "circle", "origin": [8, 8], "radius_m": 1.0},
        "props": {"crown_radius_m": 1.0},
        **kw,
    }


def slot_item(slot_id: str, x: float = 0.5, y: float = 0.5) -> dict:
    return {"slot_id": slot_id, "geometry": {"kind": "point", "origin": [x, y]}}


class TestTheBedList:
    def test_a_bed_filter_adds_the_counters(self, client, repo) -> None:
        repo.counters["bed"] = BedCounters(active_plant_count=3, open_task_count=2, next_due_at="2026-06-01T00:00:00Z")
        response = client(TenantRole.VIEWER).get(f"{_BASE}/locations", params={"site_key": SITE, "is_bed": "true"})

        assert response.status_code == 200
        (row,) = response.json()
        assert (row["key"], row["active_plant_count"], row["open_task_count"]) == ("bed", 3, 2)
        assert row["next_due_at"].startswith("2026-06-01")

    def test_a_plain_listing_is_unchanged_and_carries_no_counters(self, client, repo) -> None:
        repo.locations["tent"] = make_location("tent", name="Tent", location_type_key="greenhouse")
        response = client().get(f"{_BASE}/locations", params={"site_key": SITE})

        assert sorted(r["key"] for r in response.json()) == ["bed", "tent"]
        assert all(r["active_plant_count"] is None for r in response.json())

    def test_the_status_filter_selects_by_lifecycle(self, client, repo) -> None:
        repo.locations["old"] = make_location("old", name="Old", bed_status=BedStatus.RETIRED)
        response = client().get(f"{_BASE}/locations", params={"site_key": SITE, "bed_status": "retired"})
        assert [r["key"] for r in response.json()] == ["old"]

    def test_an_unknown_status_is_a_422(self, client) -> None:
        response = client().get(f"{_BASE}/locations", params={"site_key": SITE, "bed_status": "fallow"})
        assert response.status_code == 422

    def test_a_foreign_site_is_a_404(self, client) -> None:
        response = client().get(f"{_FOREIGN}/locations", params={"site_key": SITE, "is_bed": "true"})
        assert response.status_code == 404


class TestTheBedListAsCsv:
    """GP-FR-145/175, GP-API-068 (WP 8.25, #2668): ``format=csv`` on the bed list - columns, opt-in, hardening."""

    @staticmethod
    def _get(client, role: TenantRole = TenantRole.VIEWER, base: str = _BASE, **params: str):  # type: ignore[no-untyped-def]
        return client(role).get(f"{base}/locations", params={"site_key": SITE, "format": "csv", **params})

    @staticmethod
    def _text(response) -> str:  # type: ignore[no-untyped-def]
        return response.content.decode("utf-8-sig")

    @pytest.fixture(autouse=True)
    def beds(self, repo: FakePlanRepo) -> None:
        repo.locations["bed"] = make_location(
            "bed",
            name="Bed",
            geometry=rect(1, 1, 2, 1),
            irrigation_zone_key="zone_1",
            site_conditions=SiteConditions(microclimate=Microclimate(frost_risk="high"), slope_deg=2.5),
        )
        repo.counters["bed"] = BedCounters(active_plant_count=3)
        repo.assignees = [(TENANT, BedAssignee("bed", "u_sabine", "Sabine Gärtner"))]

    def test_a_viewer_downloads_the_default_columns_as_utf8_with_bom(self, client) -> None:
        response = self._get(client)

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert response.content.startswith(b"\xef\xbb\xbf")
        assert response.headers["content-disposition"].startswith('attachment; filename="bed-list-')
        assert response.headers["cache-control"] == "no-store"
        header, row = self._text(response).splitlines()
        assert header == "name,type,area_m2,status,soil_texture,irrigation_zone,active_plants"
        assert row == "Bed,Beet,2.0,active,,Tropf Ost,3"

    def test_without_the_opt_in_no_member_name_is_in_the_file(self, client, repo) -> None:
        text = self._text(self._get(client, columns="name,frost_risk"))

        assert "assigned_to" not in text and "Sabine" not in text
        assert repo.assignee_reads == []

    def test_with_the_opt_in_the_display_name_and_never_the_key(self, client) -> None:
        text = self._text(self._get(client, include_assignment="true"))

        header, row = text.splitlines()
        assert header.endswith(",active_plants,assigned_to")
        assert row.endswith(",Sabine Gärtner") and "u_sabine" not in text

    def test_the_site_features_are_selectable_and_the_excel_variant_has_a_decimal_comma(self, client) -> None:
        text = self._text(self._get(client, columns="name,slope_deg,frost_risk", delimiter="semicolon"))

        assert text.splitlines() == ["name;frost_risk;slope_deg", "Bed;high;2,5"]

    def test_the_type_names_follow_the_locale(self, client) -> None:
        assert self._text(self._get(client, columns="type", locale="en")).splitlines()[1] == "Bed"

    @pytest.mark.parametrize("columns", ["name,owner_email", "assigned_to"])
    def test_an_unknown_column_is_a_422(self, client, columns: str) -> None:
        response = self._get(client, columns=columns)

        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "export.unknown_column"

    def test_a_formula_in_a_bed_name_is_neutralised_on_the_wire(self, client, repo) -> None:
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"name": '=HYPERLINK("http://evil")'})

        text = self._text(self._get(client))

        assert "\n\"'=HYPERLINK" in text.replace("\r", "")

    def test_the_json_answer_is_unchanged(self, client) -> None:
        response = client().get(f"{_BASE}/locations", params={"site_key": SITE, "is_bed": "true"})

        assert response.headers["content-type"].startswith("application/json")
        assert response.json()[0]["active_plant_count"] == 3

    def test_a_foreign_site_is_a_404_also_as_csv(self, client) -> None:
        assert self._get(client, base=_FOREIGN).status_code == 404

    def test_is_bed_false_is_refused_the_download_lists_beds_only(self, client, repo) -> None:
        repo.locations["tent"] = make_location("tent", name="Tent", location_type_key="greenhouse")

        refused = self._get(client, is_bed="false")
        listed = self._text(self._get(client, columns="name")).splitlines()

        assert refused.status_code == 422
        assert refused.json()["details"][0]["code"] == "export.beds_only"
        assert listed == ["name", "Bed"]  # without a filter: the beds, not the tent

    def test_the_csv_draws_on_the_tenant_bucket_of_the_plan_exports(self, client) -> None:
        """GP-NFR-056: four callers stay under their ten each and still exhaust the tenant's thirty.

        The account override resolves no principal here, so the per-account bucket falls back to the address;
        four addresses are four per-account buckets, while the tenant bucket is the one tenant they share.
        """
        from app.config.settings import settings
        from app.main import app

        assert settings.rate_limit_plan_export_tenant == "30/minute"
        client()  # sets the role of the tenant double
        callers = [TestClient(app, client=(f"203.0.113.{n}", 40000)) for n in range(4)]
        statuses = [self._get(lambda *_, http=http: http).status_code for http in callers for _ in range(8)]

        assert statuses[:30] == [200] * 30 and statuses[30:] == [429, 429]
        json_list = callers[0].get(f"{_BASE}/locations", params={"site_key": SITE, "is_bed": "true"})
        assert json_list.status_code == 200  # the JSON list never counts

    def test_the_json_list_is_not_counted_against_the_csv_budget(self, client) -> None:
        from app.config.settings import settings

        budget = int(settings.rate_limit_plan_export.split("/")[0])
        json_statuses = {
            client().get(f"{_BASE}/locations", params={"site_key": SITE, "is_bed": "true"}).status_code
            for _ in range(budget + 3)
        }
        csv_statuses = [self._get(client).status_code for _ in range(budget + 1)]

        assert json_statuses == {200}
        assert csv_statuses[:budget] == [200] * budget and csv_statuses[budget] == 429


class TestTheSummary:
    def test_any_member_reads_the_head_of_the_bed_view(self, client, repo) -> None:
        repo.counters["bed"] = BedCounters(
            active_plant_count=2, species_keys=["sp_a"], last_care_at="2026-06-14T18:30:00Z"
        )
        response = client(TenantRole.VIEWER).get(f"{_BASE}/locations/bed/summary")

        assert response.status_code == 200
        body = response.json()
        assert (body["season_state"], body["is_bed"], body["active_plant_count"]) == ("planted", True, 2)
        assert body["species_keys"] == ["sp_a"] and body["last_care_at"].startswith("2026-06-14")
        assert body["area_m2"] == 2.0

    def test_a_foreign_bed_is_a_404(self, client) -> None:
        assert client().get(f"{_FOREIGN}/locations/bed/summary").status_code == 404


class TestTheNutrientHint:
    """GP-FR-125 (WP 8.10): the bed summary carries the hint - a state and codes, never a number."""

    @staticmethod
    def _install(repo: FakePlanRepo, config: NutrientHintConfig, feedings: list[CareEvent]) -> None:
        from app.main import app

        species = SimpleNamespace(
            get_by_key=lambda key: Species(
                _key=key, scientific_name="Solanum lycopersicum", nutrient_demand=NutrientDemand.HEAVY_FEEDER
            ),
            is_granted_to=lambda key, tenant_key: False,
        )
        events = SimpleNamespace(
            list_events=lambda criteria, *, tenant_key, offset, limit: [
                CareEventRow(event=e)
                for e in feedings
                if e.category == criteria.category and e.tenant_key == tenant_key
            ]
        )
        validator = SimpleNamespace(
            bed_rotation_entries=lambda location, *, tenant_key: ([], None),
            timeline_resolver=lambda tenant_key: SimpleNamespace(family=lambda key: None, species=lambda key: None),
        )
        hints = NutrientHintService(species, events, validator, config)  # type: ignore[arg-type]
        service = GardenResourceService(
            repo._sites, repo, FakeObjects(repo), GardenPlanService(repo._sites, repo), nutrient_hint=lambda: hints
        )
        app.dependency_overrides[get_garden_resource_service] = lambda: service

    def test_without_a_sourced_threshold_a_bed_answers_insufficient_data(self, client, repo) -> None:
        repo.counters["bed"] = BedCounters(active_plant_count=1, species_keys=["sp_tomato"])
        self._install(repo, DEFAULT_CONFIG, [])
        body = client(TenantRole.VIEWER).get(f"{_BASE}/locations/bed/summary").json()
        assert body["nutrient_hint"] == {
            "state": "insufficient_data",
            "confidence": "low",
            "reasons": ["thresholds_without_source"],
            "compost_and_p_withheld": False,
            "sources": [],
            "withheld_source": None,
        }

    def test_with_a_sourced_test_threshold_the_wire_says_likely_deficit_without_a_number(self, client, repo) -> None:
        repo.counters["bed"] = BedCounters(active_plant_count=1, species_keys=["sp_tomato"])
        fed = CareEvent(
            tenant_key=TENANT,
            site_key=SITE,
            location_key="bed",
            category="feeding",
            summary="x",
            performed_at=datetime.now(UTC) - timedelta(days=90),
        )
        nulls = {each: SourcedThreshold() for each in NutrientDemand}
        config = NutrientHintConfig(
            likely_deficit_after_days={**nulls, NutrientDemand.HEAVY_FEEDER: SourcedThreshold(60, "test source")}
        )
        self._install(repo, config, [fed])
        hint = client(TenantRole.VIEWER).get(f"{_BASE}/locations/bed/summary").json()["nutrient_hint"]
        assert (hint["state"], hint["reasons"], hint["sources"]) == (
            "likely_deficit",
            ["feeding_overdue"],
            ["test source"],
        )
        assert not [v for v in hint.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]

    def test_a_location_that_is_no_bed_carries_no_hint(self, client, repo) -> None:
        repo.locations["tent"] = make_location("tent", name="Tent", location_type_key="greenhouse")
        self._install(repo, DEFAULT_CONFIG, [])
        body = client().get(f"{_BASE}/locations/tent/summary").json()
        assert body["is_bed"] is False and body["nutrient_hint"] is None


class TestPatch:
    def test_a_note_answers_with_the_location_and_the_unchanged_revision(self, client, repo) -> None:
        response = client().patch(f"{_BASE}/locations/bed", json={"notes": "Rain cover", "sun_exposure": "full_sun"})

        assert response.status_code == 200
        body = response.json()
        assert (body["notes"], body["sun_exposure"], body["plan_revision"]) == ("Rain cover", "full_sun", 5)
        assert repo.applied == []

    def test_a_geometry_raises_the_revision(self, client, repo) -> None:
        response = client().patch(f"{_BASE}/locations/bed", json={"geometry": rect(4, 4, 3, 2)})
        assert response.status_code == 200
        assert (response.json()["plan_revision"], response.json()["area_m2"]) == (6, 6.0)

    def test_a_geometry_outside_the_boundary_is_a_422_with_its_code(self, client, repo) -> None:
        response = client().patch(f"{_BASE}/locations/bed", json={"geometry": rect(9.5, 9.5)})
        assert response.status_code == 422 and response.json()["details"][0]["code"] == "geometry.outside_parent"
        assert repo.applied == []

    def test_an_empty_body_and_an_unknown_field_are_422(self, client) -> None:
        assert client().patch(f"{_BASE}/locations/bed", json={}).status_code == 422
        assert client().patch(f"{_BASE}/locations/bed", json={"site_key": "site_foreign"}).status_code == 422

    def test_a_foreign_zone_is_a_422_reference_not_found(self, client, repo) -> None:
        repo.zones["z"] = (OTHER_TENANT, SITE)
        response = client().patch(f"{_BASE}/locations/bed", json={"irrigation_zone_key": "z"})
        assert response.status_code == 422 and response.json()["details"][0]["code"] == "reference.not_found"

    def test_a_viewer_is_refused_at_the_gate(self, client, repo) -> None:
        assert client(TenantRole.VIEWER).patch(f"{_BASE}/locations/bed", json={"notes": "x"}).status_code == 403
        assert repo.field_updates == []

    def test_a_foreign_bed_is_a_404_and_nothing_is_written(self, client, repo) -> None:
        response = client(TenantRole.LEAD).patch(f"{_FOREIGN}/locations/bed", json={"notes": "x"})
        assert response.status_code == 404 and repo.field_updates == [] and repo.applied == []

    def test_a_location_write_can_neither_set_nor_clear_last_analysis_at(self, client, repo) -> None:
        """#2706: the server owns the instant of the newest analysis; a sent one is a precondition (409 when stale)."""
        analysed = "2026-03-01T09:00:00Z"
        repo.locations["bed"] = make_location(
            "bed", name="Bed", geometry=rect(1, 1, 2, 1), soil_profile=SoilProfile(ph=6.4, last_analysis_at=analysed)
        )

        stale = client().patch(
            f"{_BASE}/locations/bed", json={"soil_profile": {"ph": 6.4, "last_analysis_at": "2099-01-01T00:00:00Z"}}
        )
        matching = client().patch(
            f"{_BASE}/locations/bed",
            json={"soil_profile": {"ph": 6.4, "drainage": "poor", "last_analysis_at": analysed}},
        )
        omitted = client().patch(f"{_BASE}/locations/bed", json={"soil_profile": {"ph": 6.5, "drainage": "good"}})
        cleared = client().patch(f"{_BASE}/locations/bed", json={"soil_profile": None})

        assert stale.status_code == 409 and stale.json()["error_code"] == "soil_profile.stale"
        assert matching.status_code == omitted.status_code == cleared.status_code == 200
        assert matching.json()["soil_profile"]["drainage"] == "poor"
        assert omitted.json()["soil_profile"]["last_analysis_at"].startswith("2026-03-01T09:00:00")
        assert omitted.json()["soil_profile"]["drainage"] == "good"  # the rest of the profile is the client's
        assert "hand_values" not in omitted.json()["soil_profile"]  # server bookkeeping is not on the wire
        assert cleared.json()["soil_profile"] is None  # null stores null, bookkeeping included (#2706 review)

    def test_a_bed_without_an_analysis_cannot_get_last_analysis_at(self, client, repo) -> None:
        stale = client().patch(
            f"{_BASE}/locations/bed", json={"soil_profile": {"last_analysis_at": "2099-01-01T00:00:00Z"}}
        )
        response = client().patch(f"{_BASE}/locations/bed", json={"soil_profile": {"last_analysis_at": None}})

        assert stale.status_code == 409
        assert response.status_code == 200 and response.json()["soil_profile"]["last_analysis_at"] is None


class TestStatus:
    def test_the_transition_logs_a_care_event_gp_acc_015(self, client, repo) -> None:
        response = client(TenantRole.LEAD).post(
            f"{_BASE}/locations/bed/status", json={"bed_status": "retired", "reason": "Dismantled"}
        )

        assert response.status_code == 200
        assert (response.json()["bed_status"], response.json()["plan_revision"]) == ("retired", 6)
        assert [(e.category, e.reason) for e in repo.care_events] == [("bed_status_change", "Dismantled")]

    def test_a_forbidden_transition_is_a_422_with_its_code_gp_acc_015(self, client, repo) -> None:
        response = client(TenantRole.LEAD).post(f"{_BASE}/locations/bed/status", json={"bed_status": "planned"})
        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "bed_status.invalid_transition"
        assert repo.care_events == []

    def test_retiring_without_a_reason_is_a_422(self, client) -> None:
        response = client(TenantRole.LEAD).post(f"{_BASE}/locations/bed/status", json={"bed_status": "retired"})
        assert response.status_code == 422 and response.json()["details"][0]["code"] == "bed_status.reason_required"

    def test_a_bed_with_plants_is_a_409(self, client, repo) -> None:
        repo.active_plants = 1
        response = client(TenantRole.LEAD).post(
            f"{_BASE}/locations/bed/status", json={"bed_status": "retired", "reason": "x"}
        )
        assert response.status_code == 409 and response.json()["details"][0]["active_plant_count"] == 1

    def test_a_grower_may_not_retire_and_a_viewer_never_reaches_the_service(self, client, repo) -> None:
        body = {"bed_status": "retired", "reason": "x"}
        assert client(TenantRole.GROWER).post(f"{_BASE}/locations/bed/status", json=body).status_code == 403
        assert client(TenantRole.VIEWER).post(f"{_BASE}/locations/bed/status", json=body).status_code == 403
        assert repo.care_events == [] and repo.applied == []

    def test_a_foreign_bed_is_a_404(self, client, repo) -> None:
        response = client(TenantRole.LEAD).post(
            f"{_FOREIGN}/locations/bed/status", json={"bed_status": "retired", "reason": "x"}
        )
        assert response.status_code == 404 and repo.care_events == []


class TestDelete:
    def test_a_bed_with_two_plants_is_a_409_with_the_count_gp_acc_012(self, client, repo) -> None:
        repo.active_plants = 2
        response = client(TenantRole.LEAD).delete(f"{_BASE}/locations/bed")

        assert response.status_code == 409
        assert response.json()["error_code"] == "location.has_active_plants"
        assert response.json()["details"][0]["active_plant_count"] == 2
        assert "bed" in repo.locations

    def test_a_lead_deletes_an_empty_bed(self, client, repo) -> None:
        response = client(TenantRole.LEAD).delete(f"{_BASE}/locations/bed")
        assert response.status_code == 204 and "bed" not in repo.locations

    def test_a_grower_is_refused_at_the_gate(self, client, repo) -> None:
        assert client(TenantRole.GROWER).delete(f"{_BASE}/locations/bed").status_code == 403
        assert "bed" in repo.locations

    def test_a_foreign_bed_is_a_404_and_stays(self, client, repo) -> None:
        assert client(TenantRole.LEAD).delete(f"{_FOREIGN}/locations/bed").status_code == 404
        assert "bed" in repo.locations


class TestGardenObjects:
    def test_create_get_list_patch_delete(self, client, repo) -> None:
        created = client().post(f"{_BASE}/sites/{SITE}/garden-objects", json=tree_body())
        assert created.status_code == 201
        key = created.json()["key"]
        assert created.json()["site_key"] == SITE and "created_by" not in created.text

        assert client(TenantRole.VIEWER).get(f"{_BASE}/garden-objects/{key}").json()["label"] == "Apple"
        assert [o["key"] for o in client(TenantRole.VIEWER).get(f"{_BASE}/sites/{SITE}/garden-objects").json()] == [key]

        patched = client().patch(f"{_BASE}/garden-objects/{key}", json={"label": "Pear", "z_order": 3})
        assert (patched.status_code, patched.json()["label"], patched.json()["z_order"]) == (200, "Pear", 3)

        assert client(TenantRole.GROWER).delete(f"{_BASE}/garden-objects/{key}").status_code == 403
        assert client(TenantRole.LEAD).delete(f"{_BASE}/garden-objects/{key}").status_code == 204
        assert client().get(f"{_BASE}/garden-objects/{key}").status_code == 404

    def test_a_body_with_a_site_key_is_ignored_by_design_and_refused_when_unknown(self, client) -> None:
        # ``GardenObjectCreate`` has no ``site_key`` (T-01): pydantic's default ignores the extra, and the
        # object lands on the path's site, never on the one the body names.
        response = client().post(f"{_BASE}/sites/{SITE}/garden-objects", json=tree_body(site_key="site_foreign"))
        assert response.status_code == 201 and response.json()["site_key"] == SITE

    def test_a_props_class_that_does_not_fit_is_a_422_at_the_request(self, client, repo) -> None:
        response = client().post(
            f"{_BASE}/sites/{SITE}/garden-objects", json=tree_body(props={"crown_radius_m": 1.0, "surface": "gravel"})
        )
        assert response.status_code == 422 and repo.objects == {}

    def test_outside_the_boundary_is_a_422_v03(self, client) -> None:
        body = tree_body(geometry={"kind": "circle", "origin": [30, 30], "radius_m": 1.0})
        response = client().post(f"{_BASE}/sites/{SITE}/garden-objects", json=body)
        assert response.status_code == 422 and response.json()["details"][0]["code"] == "geometry.outside_parent"

    def test_a_viewer_cannot_write(self, client, repo) -> None:
        assert (
            client(TenantRole.VIEWER).post(f"{_BASE}/sites/{SITE}/garden-objects", json=tree_body()).status_code == 403
        )
        assert repo.objects == {}

    def test_every_route_answers_404_for_another_tenants_site_and_object(self, client, repo) -> None:
        key = client().post(f"{_BASE}/sites/{SITE}/garden-objects", json=tree_body()).json()["key"]
        other = client(TenantRole.LEAD)
        responses = [
            other.get(f"{_FOREIGN}/sites/{SITE}/garden-objects"),
            other.post(f"{_FOREIGN}/sites/{SITE}/garden-objects", json=tree_body()),
            other.get(f"{_FOREIGN}/garden-objects/{key}"),
            other.patch(f"{_FOREIGN}/garden-objects/{key}", json={"label": "stolen"}),
            other.delete(f"{_FOREIGN}/garden-objects/{key}"),
        ]
        assert [r.status_code for r in responses] == [404] * 5
        assert repo.objects[key].label == "Apple" and len(repo.objects) == 1


class TestSlots:
    def test_a_correction_inside_the_bed(self, client) -> None:
        response = client().patch(
            f"{_BASE}/slots/s1", json={"geometry": {"kind": "point", "origin": [1.0, 0.25]}, "capacity_plants": 2}
        )
        assert response.status_code == 200
        assert (response.json()["geometry"]["origin"], response.json()["capacity_plants"]) == ([1.0, 0.25], 2)
        assert response.json()["geometry_source"] == "editor"

    def test_outside_the_bed_is_a_422_v04(self, client) -> None:
        response = client().patch(f"{_BASE}/slots/s1", json={"geometry": {"kind": "point", "origin": [2.6, 0.5]}})
        assert response.status_code == 422 and response.json()["details"][0]["code"] == "slot.outside_bed"

    def test_a_viewer_is_refused_and_a_foreign_slot_is_a_404(self, client) -> None:
        assert client(TenantRole.VIEWER).patch(f"{_BASE}/slots/s1", json={"capacity_plants": 2}).status_code == 403
        assert client(TenantRole.LEAD).patch(f"{_FOREIGN}/slots/s1", json={"capacity_plants": 2}).status_code == 404

    def test_the_batch_replaces_and_reports_keys_in_request_order(self, client, repo) -> None:
        response = client().post(
            f"{_BASE}/locations/bed/slots/batch",
            json={"mode": "replace_unoccupied", "slots": [slot_item("BED_N1"), slot_item("BED_N2", 1.5, 0.5)]},
        )

        assert response.status_code == 200
        body = response.json()
        assert (body["deleted_count"], body["kept_count"], len(body["created_keys"])) == (1, 0, 2)
        assert [s.slot_id for s in repo.slots] == ["BED_N1", "BED_N2"]

    def test_a_defective_batch_names_the_position_and_changes_nothing(self, client, repo) -> None:
        response = client().post(
            f"{_BASE}/locations/bed/slots/batch",
            json={"mode": "replace_unoccupied", "slots": [slot_item("BED_N1"), slot_item("BED_N2", 3.5)]},
        )
        assert response.status_code == 422
        assert (response.json()["details"][0]["code"], response.json()["details"][0]["index"]) == (
            "slot.outside_bed",
            1,
        )
        assert [s.slot_id for s in repo.slots] == ["BED_P1"]

    def test_a_duplicate_id_is_a_422_and_an_unknown_mode_too(self, client) -> None:
        body = {"mode": "append", "slots": [slot_item("BED_P1")]}
        assert client().post(f"{_BASE}/locations/bed/slots/batch", json=body).status_code == 422
        assert client().post(f"{_BASE}/locations/bed/slots/batch", json={**body, "mode": "merge"}).status_code == 422

    def test_a_viewer_is_refused_and_a_foreign_bed_is_a_404(self, client, repo) -> None:
        body = {"mode": "append", "slots": [slot_item("BED_N1")]}
        assert client(TenantRole.VIEWER).post(f"{_BASE}/locations/bed/slots/batch", json=body).status_code == 403
        assert client(TenantRole.LEAD).post(f"{_FOREIGN}/locations/bed/slots/batch", json=body).status_code == 404
        assert [s.slot_id for s in repo.slots] == ["BED_P1"]

    def test_the_eleventh_batch_in_a_minute_is_rate_limited(self, client) -> None:
        c = client()
        for number in range(10):
            body = {"mode": "append", "slots": [slot_item(f"BED_R{number}", 0.1 + number * 0.1)]}
            assert c.post(f"{_BASE}/locations/bed/slots/batch", json=body).status_code == 200
        limited = c.post(
            f"{_BASE}/locations/bed/slots/batch", json={"mode": "append", "slots": [slot_item("BED_LATE")]}
        )
        assert limited.status_code == 429


class TestTheContract:
    def test_the_new_operations_are_published_with_their_error_responses(self) -> None:
        from app.main import app

        paths = app.openapi()["paths"]
        t = "/api/v1/t/{tenant_slug}"
        assert {"get", "post"} <= set(paths[f"{t}/sites/{{key}}/garden-objects"])
        assert {"get", "patch", "delete"} == set(paths[f"{t}/garden-objects/{{key}}"])
        assert {"get", "patch", "put", "delete"} <= set(paths[f"{t}/locations/{{key}}"])
        assert set(paths[f"{t}/locations/{{key}}/summary"]) == {"get"}
        assert set(paths[f"{t}/locations/{{key}}/status"]) == {"post"}
        assert set(paths[f"{t}/locations/{{key}}/slots/batch"]) == {"post"}
        assert "patch" in paths[f"{t}/slots/{{key}}"]
        assert {"403", "409", "422"} <= set(paths[f"{t}/locations/{{key}}/status"]["post"]["responses"])
