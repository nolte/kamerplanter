"""REQ-053 WP 1.10 (#2329) — every garden-plan endpoint refuses a foreign tenant, against a real ArangoDB.

``locations``, ``slots`` and ``garden_objects`` carry no ``tenant_key`` (E-01, #2107): their tenant is the
parent site's. That makes the ownership walk the only isolation there is, so it is measured end to end —
real routes, real services, real repositories, real server — with the caller a member of tenant A and every
key addressed one that tenant B owns.

**What a refusal has to be** (GP-NFR-050, GP-NFR-058, GP-ACC-014):

* 404, and the *same* body as for a key that does not exist at all (the key substituted) — a different text
  is the existence oracle the 404 exists to prevent;
* no name, key or tenant of B anywhere in the body;
* the database is byte-identical afterwards (a rejected write wrote nothing);
* no ``garden_plan.batch_applied`` log line.

**Falsified against the same expression.** :func:`_assert_refused` is the one assertion every case runs.
:class:`TestTheMatrixCanFail` runs it against an *unscoped* stub — services that answer for the owning
tenant whatever the caller is — and requires it to raise for every case, so a refusal check that passed
vacuously would fail there. Every refusal is paired with the owner's positive control (the same call, as B,
succeeds) so an endpoint that is simply broken cannot pass as "isolated".

**The route list is derived, not listed by hand**: :class:`TestTheMatrixCoversTheRouters`
walks the four routers and fails on a route the matrix does not name.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest
from arango import ArangoClient
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from app.api.v1.auth.router import limiter
from app.api.v1.tenant_scoped.router import tenant_scoped_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_adjacency_dispatch,
    get_adjacency_service,
    get_bed_rotation_service,
    get_garden_plan_export_service,
    get_garden_plan_service,
    get_garden_resource_service,
    get_planting_reservation_service,
    get_planting_run_service,
    get_site_service,
)
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.garden_object_repository import ArangoGardenObjectRepository
from app.data_access.arango.garden_plan_repository import (
    _BATCH_WRITE,
    _SLOT_BATCH_WRITE,
    ArangoGardenPlanRepository,
)
from app.data_access.arango.graph_repository import ArangoGraphRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.planting_reservation_repository import (
    _CLEAR_WRITE,
    _QUICK_WRITE,
    ArangoPlantingReservationRepository,
)
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.rotation_history_repository import ArangoRotationHistoryRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.models.garden_object import GardenObject
from app.domain.models.site import Location, Slot
from app.domain.models.tenant_context import TenantContext
from app.domain.services.adjacency_service import AdjacencyService
from app.domain.services.bed_rotation_service import BedRotationService
from app.domain.services.care_event_service import CareEventService
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.location_ownership import resolve_owned_location, resolve_owned_slot
from app.domain.services.planting_reservation_service import PlantingReservationService
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.site_service import SiteService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.care_event_fakes import FakeAttachmentRepo, FakeAttachmentService, FakeFertilizers, FakeMemberships

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("garden_plan_tenant_isolation")
A, B = "ten_a", "ten_b"
SLUG_A, SLUG_B = "alice", "bob"
USER = "u_sabine"
#: Strings that exist only in tenant B's data; none may appear in a response to tenant A.
B_SECRETS = (
    "Bobs Geheimbeet",
    "Bobs Garten",
    "Bobs Eiche",
    "site_b",
    "bed_b",
    "slot_b",
    "slot2_b",
    "obj_b",
    "zone_b",
    "ev_b",
    B,
)
_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 20, "length_m": 20, "rotation_deg": 0}
_RECT = {"kind": "rect", "origin": [1, 1], "width_m": 2, "length_m": 1, "rotation_deg": 0}


#: Every collection a route of these four routers can write — the plan batch's and the slot batch's write sets
#: plus the fixture's own — truncated per test and compared before/after a refused write.
_TOUCHED: tuple[str, ...] = tuple(
    dict.fromkeys(
        (
            col.SITES,
            col.LOCATIONS,
            col.SLOTS,
            col.GARDEN_OBJECTS,
            col.GARDEN_PLAN_AUDIT,
            col.ADJACENT_TO,
            col.CARE_EVENTS,
            col.IRRIGATION_ZONES,
            col.LOCATION_TYPES,
            col.USERS,
            col.PLANT_INSTANCES,
            col.SPECIES,
            col.BOTANICAL_FAMILIES,
            col.TASKS,
            *_BATCH_WRITE,
            *_SLOT_BATCH_WRITE,
            *_CLEAR_WRITE,
            *_QUICK_WRITE,
        )
    )
)


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    # The production schema, graph and indexes: the listings traverse ``kamerplanter_graph``.
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


def _site(key: str, tenant: str, name: str) -> dict[str, Any]:
    return {
        "_key": key,
        "tenant_key": tenant,
        "name": name,
        "type": "outdoor",
        "total_area_m2": 0.0,
        "timezone": "UTC",
        "plan": {"boundary": _BOUNDARY, "plan_revision": 1, "north_angle_deg": 0.0},
    }


def _bed(key: str, site: str, name: str) -> dict[str, Any]:
    # Deliberately no ``tenant_key`` (E-01): the site is the only anchor.
    return {
        "_key": key,
        "site_key": site,
        "name": name,
        "location_type_key": "bed",
        "area_m2": 2.0,
        "depth": 0,
        "path": key,
        "bed_status": "active",
        "geometry": _RECT,
    }


def _slot(key: str, bed: str) -> dict[str, Any]:
    return {
        "_key": key,
        "slot_id": key.upper(),
        "location_key": bed,
        "capacity_plants": 1,
        "currently_occupied": False,
        "slot_role": "position",
        "geometry": {"kind": "point", "origin": [0.5, 0.5]},
        "archived_at": None,
    }


def _tree(key: str, site: str, label: str) -> dict[str, Any]:
    return {
        "_key": key,
        "site_key": site,
        "object_type": "tree",
        "label": label,
        "geometry": {"kind": "circle", "origin": [10, 10], "radius_m": 1},
        "props": {"object_type": "tree", "crown_radius_m": 1, "foliage": "deciduous"},
        "off_site": False,
        "locked": False,
        "z_order": 0,
    }


@pytest.fixture(autouse=True)
def _no_rate_limit(monkeypatch):
    """The rate limit is not under test, and the repeated calls of one case would trip it."""
    monkeypatch.setattr(limiter, "enabled", False)


@pytest.fixture
def db(database):
    for name in _TOUCHED:
        database.collection(name).truncate()
    database.collection(col.USERS).insert({"_key": USER, "display_name": "Sabine"})
    database.collection(col.LOCATION_TYPES).insert({"_key": "bed", "name": "Bed", "is_bed": True})
    for site, tenant, name in (("site_a", A, "Alices Garten"), ("site_b", B, "Bobs Garten")):
        database.collection(col.SITES).insert(_site(site, tenant, name))
        database.collection(col.IRRIGATION_ZONES).insert(
            {"_key": f"zone_{site[-1]}", "tenant_key": tenant, "site_key": site}
        )
    for suffix, site, bed_name, tree_name in (
        ("a", "site_a", "Alices Beet", "Alices Birke"),
        ("b", "site_b", "Bobs Geheimbeet", "Bobs Eiche"),
    ):
        database.collection(col.LOCATIONS).insert(_bed(f"bed_{suffix}", site, bed_name))
        database.collection(col.SLOTS).insert(_slot(f"slot_{suffix}", f"bed_{suffix}"))
        database.collection(col.HAS_SLOT).insert(
            {"_from": f"{col.LOCATIONS}/bed_{suffix}", "_to": f"{col.SLOTS}/slot_{suffix}"}
        )
        # a second slot per tenant: the manual adjacency routes (WP 3.3) need two ends
        database.collection(col.SLOTS).insert(_slot(f"slot2_{suffix}", f"bed_{suffix}"))
        database.collection(col.HAS_SLOT).insert(
            {"_from": f"{col.LOCATIONS}/bed_{suffix}", "_to": f"{col.SLOTS}/slot2_{suffix}"}
        )
        database.collection(col.GARDEN_OBJECTS).insert(_tree(f"obj_{suffix}", site, tree_name))
    # WP 3.4: a global species and family for the rotation hints, and one backfilled year of tenant B's bed
    database.collection(col.SPECIES).insert(
        {
            "_key": "sp",
            "scientific_name": "Solanum lycopersicum",
            "genus": "Solanum",
            "family_key": "fam",
            "tenant_key": "",
        }
    )
    database.collection(col.BOTANICAL_FAMILIES).insert({"_key": "fam", "name": "Solanaceae", "rotation_pause_years": 3})
    database.collection(col.CARE_EVENTS).insert(
        {
            "_key": "ev_b",
            "tenant_key": B,
            "site_key": "site_b",
            "location_key": "bed_b",
            "category": "planting",
            "summary": "Backfill",
            "performed_at": "2024-07-01T12:00:00Z",
            "trigger": "backfill",
            "created_by": USER,
            "rotation_entry": {"year": 2024, "family_key": "fam", "plan_role": "main_crop"},
        }
    )
    return database


# ── The application under test: real routes, real services, real repositories ──────────────────────


def _services(
    db,
) -> tuple[GardenPlanService, GardenResourceService, SiteService, PlantingReservationService, PlantingRunService]:
    sites = ArangoSiteRepository(db)
    plan_repo = ArangoGardenPlanRepository(db)
    plan = GardenPlanService(sites, plan_repo)
    resources = GardenResourceService(sites, plan_repo, ArangoGardenObjectRepository(db), plan)
    run_repo = ArangoPlantingRunRepository(db)
    reservation_repo = ArangoPlantingReservationRepository(db)
    care = CareEventService(
        ArangoCareEventRepository(db),
        sites,
        FakeMemberships(),
        FakeFertilizers(),
        FakeAttachmentRepo(),
        FakeAttachmentService(),
    )
    reservations = PlantingReservationService(reservation_repo, run_repo, sites, plan_repo, care)

    def species(key: str, *, tenant_key: str) -> SimpleNamespace:
        if key != "sp":
            raise NotFoundError("Species", key)
        return SimpleNamespace(scientific_name="Solanum lycopersicum", green_manure_suitable=False)

    runs = PlantingRunService(
        run_repo,
        ArangoPlantInstanceRepository(db),
        PlantingRunEngine(),
        site_repo=sites,
        species_resolver=species,
        reservations=reservations,
        reservation_repo=reservation_repo,
    )
    return plan, resources, SiteService(sites), reservations, runs


class _Unscoped:
    """The deliberately unscoped stub: answers for ``B`` whoever asks.

    Every ``tenant_key`` the router hands in is replaced with the owning tenant's before the real service
    runs — exactly what a service that skipped its ownership predicate would let through.
    """

    def __init__(self, inner: object) -> None:
        self._inner = inner

    def __getattr__(self, name: str) -> Any:
        target = getattr(self._inner, name)
        if not callable(target):
            return target

        def call(*args: Any, **kwargs: Any) -> Any:
            if "tenant_key" in kwargs:
                kwargs["tenant_key"] = B
            return target(*args, **kwargs)

        return call


def _rotation_service(db) -> BedRotationService:
    sites = ArangoSiteRepository(db)
    species = ArangoSpeciesRepository(db)
    families = ArangoBotanicalFamilyRepository(db)
    graph = ArangoGraphRepository(db)
    care_repo = ArangoCareEventRepository(db)
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    validator = CropRotationValidator(
        ArangoPlantInstanceRepository(db),
        species,
        graph,
        site_repo=sites,
        family_repo=families,
        history_repo=ArangoRotationHistoryRepository(db),
    )
    return BedRotationService(sites, ArangoGardenPlanRepository(db), graph, species, families, care, validator)


def _client(db, *, tenant: str = A, role: TenantRole = TenantRole.LEAD, unscoped: bool = False) -> TestClient:
    plan, resources, sites, reservations, runs = _services(db)
    rotation: Any = _rotation_service(db)
    adjacency: Any = AdjacencyService(
        ArangoSiteRepository(db), ArangoGardenPlanRepository(db), ArangoGraphRepository(db)
    )
    export: Any = GardenPlanExportService(ArangoSiteRepository(db), ArangoGardenPlanRepository(db), plan)
    if unscoped:
        adjacency = _Unscoped(adjacency)
        rotation = _Unscoped(rotation)
        export = _Unscoped(export)
        plan, resources, sites, reservations, runs = (  # type: ignore[assignment]
            _Unscoped(plan),
            _Unscoped(resources),
            _Unscoped(sites),
            _Unscoped(reservations),
            _Unscoped(runs),
        )
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.include_router(tenant_scoped_router, prefix="/api/v1")
    context = TenantContext(tenant_key=tenant, tenant_slug=SLUG_A if tenant == A else SLUG_B, user_key=USER, role=role)
    app.dependency_overrides[get_current_tenant] = lambda: context
    app.dependency_overrides[get_garden_plan_service] = lambda: plan
    app.dependency_overrides[get_garden_resource_service] = lambda: resources
    app.dependency_overrides[get_site_service] = lambda: sites
    app.dependency_overrides[get_planting_reservation_service] = lambda: reservations
    app.dependency_overrides[get_planting_run_service] = lambda: runs
    app.dependency_overrides[get_adjacency_service] = lambda: adjacency
    app.dependency_overrides[get_bed_rotation_service] = lambda: rotation
    app.dependency_overrides[get_garden_plan_export_service] = lambda: export
    app.dependency_overrides[get_adjacency_dispatch] = lambda: lambda _location_key: None  # no broker in this tier
    return TestClient(app, raise_server_exceptions=False)


# ── The matrix: one row per route that a foreign tenant addresses by key ───────────────────────────


@dataclass(frozen=True)
class Case:
    """One request, written for the keys of *one* tenant's resources (``bed_b`` …), plus its absent twin."""

    name: str
    method: str
    path: str
    body: Any = None
    params: dict[str, str] = field(default_factory=dict)
    #: The success status as the owner (the positive control).
    owner_status: int = 200
    #: A write is checked for "the database did not change".
    writes: bool = False
    #: Marks the routes whose success logs ``garden_plan.batch_applied``.
    logs_batch: bool = False

    def for_keys(self, mapping: dict[str, str]) -> Case:
        """The same request with every key in ``mapping`` replaced — in path, params and body."""

        def swap(value: Any) -> Any:
            if isinstance(value, str):
                for old, new in mapping.items():
                    value = value.replace(old, new)
                return value
            if isinstance(value, list):
                return [swap(item) for item in value]
            if isinstance(value, dict):
                return {key: swap(item) for key, item in value.items()}
            return value

        return Case(
            self.name,
            self.method,
            swap(self.path),
            swap(copy.deepcopy(self.body)),
            swap(dict(self.params)),
            self.owner_status,
            self.writes,
            self.logs_batch,
        )


_NEW_OBJECT = {
    "object_type": "tree",
    "label": "Intruder",
    "geometry": {"kind": "circle", "origin": [15, 15], "radius_m": 1},
    "props": {"object_type": "tree", "crown_radius_m": 1, "foliage": "deciduous"},
}
_BATCH_OP = {
    "op": "update_fields",
    "entity": "garden_object",
    "key": "obj_b",
    "fields": {"label": "Taken over"},
}

#: The owner's keys: ``site_b``, ``bed_b``, ``slot_b``, ``obj_b``. Replaced by the absent twin below.
CASES: tuple[Case, ...] = (
    # garden_plan (WP 1.8)
    Case("get_plan", "GET", "/sites/site_b/plan"),
    Case("list_plan_audit", "GET", "/sites/site_b/plan/audit"),
    # REQ-053 WP 5.2, GP-API-004 / GP-API-006: the JSON backup and the SVG read a whole site - a foreign one is a 404.
    Case("export_plan", "GET", "/sites/site_b/plan/export"),
    Case("render_plan_svg", "GET", "/sites/site_b/plan/render.svg"),
    Case(
        "put_boundary",
        "PUT",
        "/sites/site_b/plan/boundary",
        {"boundary": {**_BOUNDARY, "width_m": 15}, "north_angle_deg": 10.0},
        writes=True,
        logs_batch=True,
    ),
    Case(
        "apply_batch",
        "POST",
        "/sites/site_b/plan/batch",
        {"expected_revision": 1, "operations": [_BATCH_OP]},
        writes=True,
        logs_batch=True,
    ),
    # garden_objects (WP 1.9)
    Case("list_garden_objects", "GET", "/sites/site_b/garden-objects"),
    Case(
        "create_garden_object",
        "POST",
        "/sites/site_b/garden-objects",
        _NEW_OBJECT,
        owner_status=201,
        writes=True,
        logs_batch=True,
    ),
    Case("get_garden_object", "GET", "/garden-objects/obj_b"),
    Case(
        "patch_garden_object", "PATCH", "/garden-objects/obj_b", {"label": "Taken over"}, writes=True, logs_batch=True
    ),
    Case("delete_garden_object", "DELETE", "/garden-objects/obj_b", owner_status=204, writes=True, logs_batch=True),
    # locations (WP 1.9)
    Case("list_locations", "GET", "/locations", params={"site_key": "site_b"}),
    Case("list_beds", "GET", "/locations", params={"site_key": "site_b", "is_bed": "true"}),
    Case(
        "create_location",
        "POST",
        "/locations",
        {"name": "Intruder", "site_key": "site_b", "area_m2": 1.0, "location_type_key": "bed"},
        owner_status=201,
        writes=True,
    ),
    Case(
        "update_location",
        "PUT",
        "/locations/bed_b",
        {"name": "Taken over", "site_key": "site_b", "area_m2": 2.0, "location_type_key": "bed"},
        writes=True,
    ),
    Case("get_location", "GET", "/locations/bed_b"),
    Case("list_location_children", "GET", "/locations/bed_b/children"),
    Case("get_location_summary", "GET", "/locations/bed_b/summary"),
    Case("patch_location", "PATCH", "/locations/bed_b", {"name": "Taken over"}, writes=True),
    Case(
        "change_location_status",
        "POST",
        "/locations/bed_b/status",
        {"bed_status": "retired", "reason": "Take over"},
        writes=True,
    ),
    Case("delete_location", "DELETE", "/locations/bed_b", owner_status=204, writes=True, logs_batch=True),
    Case(
        "apply_slot_batch",
        "POST",
        "/locations/bed_b/slots/batch",
        {
            "mode": "append",
            "slots": [{"slot_id": "INTRUDER_1", "geometry": {"kind": "point", "origin": [0.4, 0.5]}}],
        },
        writes=True,
        owner_status=200,
    ),
    # REQ-053 WP 3.1, GP-API-016: a pure compute over the bed's geometry - nothing is written, nothing leaks.
    Case(
        "preview_planting_layout",
        "POST",
        "/locations/bed_b/planting-layout/preview",
        {"entry": {"layout_strategy": "grid", "spacing_cm": 30}},
    ),
    # REQ-053 WP 3.2, GP-API-024 / GP-API-019 / GP-API-017: the plantings of a bed, clearing it, quick planting.
    Case("list_plantings", "GET", "/locations/bed_b/plantings"),
    Case("clear_bed", "POST", "/locations/bed_b/clear", {"termination_type": "senesced"}, writes=True),
    Case(
        "quick_planting",
        "POST",
        "/locations/bed_b/quick-planting",
        {"species_key": "sp", "quantity": 2, "layout_strategy": "grid", "spacing_cm": 50},
        owner_status=201,
        writes=True,
    ),
    # REQ-053 WP 3.4, GP-API-025 / 039 / 042: rotation hints, the timeline and the history backfill of a bed.
    Case("validate_planting", "POST", "/locations/bed_b/validate-planting", {"species_key": "sp"}),
    Case("get_rotation", "GET", "/locations/bed_b/rotation"),
    Case(
        "backfill_history",
        "POST",
        "/locations/bed_b/history/backfill",
        {"year": date.today().year - 2, "family_key": "fam"},
        owner_status=201,
        writes=True,
    ),
    Case("cancel_backfill", "DELETE", "/locations/bed_b/history/backfill/ev_b", owner_status=204, writes=True),
    # slots (WP 1.9 + the reads of the single resource)
    Case("list_slots", "GET", "/slots", params={"location_key": "bed_b"}),
    Case("get_slot", "GET", "/slots/slot_b"),
    Case(
        "create_slot",
        "POST",
        "/slots",
        {"slot_id": "INTRUDER_SLOT", "location_key": "bed_b"},
        owner_status=201,
        writes=True,
    ),
    Case("update_slot", "PUT", "/slots/slot_b", {"slot_id": "SLOT_B", "location_key": "bed_b"}, writes=True),
    Case("patch_slot", "PATCH", "/slots/slot_b", {"capacity_plants": 3}, writes=True),
    Case("delete_slot", "DELETE", "/slots/slot_b", owner_status=204, writes=True),
    # REQ-053 WP 3.3, SR-021: the manual neighbourhood of two slots - both ends are resolved under the tenant.
    Case(
        "set_manual_adjacency",
        "PUT",
        "/slots/slot_b/adjacent/slot2_b",
        {"distance_cm": 20},
        owner_status=204,
        writes=True,
    ),
    Case("remove_manual_adjacency", "DELETE", "/slots/slot_b/adjacent/slot2_b", owner_status=204, writes=True),
)

_ABSENT = {
    "site_b": "site_gone",
    "bed_b": "bed_gone",
    "slot_b": "slot_gone",
    "slot2_b": "slot2_gone",
    "obj_b": "obj_gone",
    "ev_b": "ev_gone",
}


def _url(case: Case, slug: str) -> str:
    return f"/api/v1/t/{slug}{case.path}"


def _send(client: TestClient, case: Case, slug: str):
    return client.request(case.method, _url(case, slug), json=case.body, params=case.params or None)


def _snapshot(db) -> dict[str, list[dict[str, Any]]]:
    return {
        name: sorted(db.collection(name).all(), key=lambda doc: json.dumps(doc, sort_keys=True)) for name in _TOUCHED
    }


def _canonical(text: str) -> str:
    """The body without what differs per request by construction: the error id and the timestamp."""
    payload = json.loads(text)
    payload.pop("error_id", None)
    payload.pop("timestamp", None)
    return json.dumps(payload, sort_keys=True)


def _detail(case: Case, response) -> str:
    return f"{case.name}: {response.status_code} {response.text}"


def _assert_refused(db, client: TestClient, case: Case) -> None:
    """The single expression every negative runs: 404, the absent key's body, nothing of B, nothing written."""
    before = _snapshot(db)
    with capture_logs() as logs:
        refused = _send(client, case, SLUG_A)
        absent = _send(client, case.for_keys(_ABSENT), SLUG_A)

    assert refused.status_code == 404, _detail(case, refused)
    assert absent.status_code == 404, _detail(case, absent)
    # The caller's own path/params/body may be echoed back; what B owns beyond them must not be.
    sent = json.dumps([case.path, case.params, case.body])
    echoed = refused.text
    for key in (secret for secret in B_SECRETS if secret in sent):
        echoed = echoed.replace(key, "")
    leaked = [secret for secret in B_SECRETS if secret in echoed]
    assert leaked == [], f"{case.name} echoed {leaked}: {refused.text}"
    # Same answer for a foreign and an absent key: the only difference allowed is the key the caller sent.
    swapped = _canonical(refused.text)
    for old, new in _ABSENT.items():
        swapped = swapped.replace(old, new)
    assert swapped == _canonical(absent.text), (
        f"{case.name} tells a foreign key from an absent one: {refused.text} / {absent.text}"
    )
    assert [entry for entry in logs if entry["event"] == "garden_plan.batch_applied"] == [], case.name
    assert _snapshot(db) == before, f"{case.name} changed the database"


#: Routes of the four routers that no case addresses, each with the reason — an entry that names a route
#: the routers no longer have fails, and so does a route missing from both this dict and :data:`CASES`.
_OTHER_ROUTES: dict[tuple[str, str], str] = {
    **{
        (method, path): "sensor and frost-warning routes of a location are served by the sensor and weather "
        "services and predate REQ-053 (#1871 pinned them); WP 1.10 covers the garden-plan services"
        for method, path in (
            ("GET", "/locations/{key}/sensors"),
            ("POST", "/locations/{key}/sensors"),
            ("PUT", "/locations/{key}/sensors/{sensor_key}"),
            ("DELETE", "/locations/{key}/sensors/{sensor_key}"),
            ("GET", "/locations/{key}/sensors/live"),
            ("GET", "/locations/{key}/frost-warning"),
        )
    },
}


def _route_pattern(path: str) -> re.Pattern[str]:
    return re.compile(
        "^" + re.sub(r"\{[^/]+\}", "[^/]+", re.escape(path).replace(r"\{", "{").replace(r"\}", "}")) + "$"
    )


def _routes_of_the_four_routers() -> set[tuple[str, str]]:
    from app.api.v1.garden_objects.tenant_router import router as garden_objects
    from app.api.v1.garden_plan.tenant_router import router as garden_plan
    from app.api.v1.locations.tenant_router import router as locations
    from app.api.v1.slots.tenant_router import router as slots

    found: set[tuple[str, str]] = set()
    for router in (garden_plan, garden_objects, locations, slots):
        for route in router.routes:
            path = f"{router.prefix}{route.path.removeprefix(router.prefix)}"
            found.update((method, path) for method in route.methods)
    return found


class TestTheMatrixCoversTheRouters:
    def test_every_route_has_a_case_or_a_named_reason(self) -> None:
        routes = _routes_of_the_four_routers()
        uncovered = sorted(
            route
            for route in routes
            if route not in _OTHER_ROUTES
            and not any(
                case.method == route[0] and _route_pattern(route[1]).match(case.path.split("?")[0]) for case in CASES
            )
        )

        assert uncovered == [], f"routes no case addresses and no reason names: {uncovered}"
        assert len(routes) >= 30, "the route walk saw almost nothing"

    def test_every_named_exception_is_still_a_route(self) -> None:
        assert sorted(set(_OTHER_ROUTES) - _routes_of_the_four_routers()) == []

    def test_every_case_addresses_a_real_route(self) -> None:
        routes = _routes_of_the_four_routers()
        orphan = sorted(
            case.name
            for case in CASES
            if not any(
                method == case.method and _route_pattern(path).match(case.path.split("?")[0]) for method, path in routes
            )
        )
        assert orphan == []


class TestAForeignTenantIsRefusedOnEveryRoute:
    @pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
    def test_the_route_answers_404_like_an_absent_key_and_writes_nothing(self, db, case: Case) -> None:
        _assert_refused(db, _client(db), case)

    @pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
    def test_the_owner_reaches_the_same_resource(self, db, case: Case) -> None:
        """The positive control: the call is valid, so the 404 above is the tenancy and nothing else."""
        with capture_logs() as logs:
            response = _send(_client(db, tenant=B), case, SLUG_B)

        assert response.status_code == case.owner_status, _detail(case, response)
        applied = [entry for entry in logs if entry["event"] == "garden_plan.batch_applied"]
        assert bool(applied) is case.logs_batch, f"{case.name}: {logs}"


class TestTheParentOfAListingIsResolvedUnderTheTenant:
    """``GET /locations?site_key=<own>&parent_location_key=<foreign>`` — the site is the caller's, the parent is not."""

    def _list(self, client: TestClient, parent: str):
        return client.get(f"/api/v1/t/{SLUG_A}/locations", params={"site_key": "site_a", "parent_location_key": parent})

    def test_a_foreign_parent_answers_like_an_absent_one(self, db) -> None:
        client = _client(db)

        foreign, absent = self._list(client, "bed_b"), self._list(client, "bed_gone")

        assert (foreign.status_code, absent.status_code) == (404, 404), (foreign.text, absent.text)
        assert _canonical(foreign.text).replace("bed_b", "bed_gone") == _canonical(absent.text)
        assert [s for s in B_SECRETS if s != "bed_b" and s in foreign.text] == []

    def test_the_own_parent_lists_its_children(self, db) -> None:
        assert self._list(_client(db), "bed_a").status_code == 200

    def test_a_parent_check_that_ignores_the_tenant_lists_the_foreign_children(self, db, monkeypatch) -> None:
        """Falsification: with the service's own ownership step unscoped, the same request is a 200."""

        def unscoped(self, key, *, tenant_key):
            location = self._repo.get_location_by_key(key)
            if location is None:
                raise NotFoundError("Location", key)
            return location

        monkeypatch.setattr(SiteService, "get_location", unscoped)

        assert self._list(_client(db), "bed_b").status_code == 200


class TestTheMatrixCanFail:
    """The same assertion, aimed at services that skip the ownership predicate, must raise — for every case."""

    @pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
    def test_an_unscoped_stub_is_caught_by_the_refusal_check(self, db, case: Case) -> None:
        with pytest.raises(AssertionError):
            _assert_refused(db, _client(db, unscoped=True), case)


# ── reference.not_found per body field that exists in wave 1 (GP-NFR-058, GP-ACC-041) ───────────────


def _error_codes(response) -> list[str]:
    payload = response.json()
    items = payload.get("details") or payload.get("errors") or []
    codes = [item.get("code") for item in items if isinstance(item, dict)]
    return [code for code in codes if code] or [payload.get("code", "")]


@dataclass(frozen=True)
class ReferenceCase:
    name: str
    method: str
    path: str
    field_name: str
    build: Callable[[str], Any]
    foreign: str
    own: str
    missing: str


REFERENCE_CASES: tuple[ReferenceCase, ...] = (
    ReferenceCase(
        "garden_object.parent_location_key",
        "POST",
        "/sites/site_a/garden-objects",
        "parent_location_key",
        lambda key: {**_NEW_OBJECT, "parent_location_key": key},
        "bed_b",
        "bed_a",
        "bed_gone",
    ),
    ReferenceCase(
        "batch.create_location.data.parent_location_key",
        "POST",
        "/sites/site_a/plan/batch",
        "data.parent_location_key",
        lambda key: {
            "expected_revision": 1,
            "operations": [
                {
                    "op": "create_location",
                    "temp_key": "t1",
                    "data": {
                        "name": "Intruder",
                        "location_type_key": "bed",
                        "parent_location_key": key,
                        "geometry": {"kind": "rect", "origin": [8, 8], "width_m": 1, "length_m": 1, "rotation_deg": 0},
                    },
                }
            ],
        },
        "bed_b",
        "bed_a",
        "bed_gone",
    ),
    ReferenceCase(
        "batch.create_garden_object.data.parent_location_key",
        "POST",
        "/sites/site_a/plan/batch",
        "data.parent_location_key",
        lambda key: {
            "expected_revision": 1,
            "operations": [
                {
                    "op": "create_garden_object",
                    "temp_key": "t1",
                    "data": {**_NEW_OBJECT, "parent_location_key": key},
                }
            ],
        },
        "bed_b",
        "bed_a",
        "bed_gone",
    ),
    *(
        ReferenceCase(
            f"batch.{op}.{entity}.key",
            "POST",
            "/sites/site_a/plan/batch",
            "key",
            lambda key, op=op, entity=entity, extra=extra: {
                "expected_revision": 1,
                "operations": [{"op": op, "entity": entity, "key": key, **extra}],
            },
            "bed_b" if entity == "location" else "obj_b",
            "bed_a" if entity == "location" else "obj_a",
            "bed_gone" if entity == "location" else "obj_gone",
        )
        for op, extra in (("delete", {}), ("set_locked", {"locked": True}), ("set_z_order", {"z_order": 3}))
        for entity in ("location", "garden_object")
    ),
    ReferenceCase(
        "location.irrigation_zone_key",
        "PATCH",
        "/locations/bed_a",
        "irrigation_zone_key",
        lambda key: {"irrigation_zone_key": key},
        "zone_b",
        "zone_a",
        "zone_gone",
    ),
)


def _assert_reference_refused(db, client: TestClient, case: ReferenceCase) -> None:
    """The single expression every reference negative runs: 422 ``reference.not_found``, the absent key's body."""
    before = _snapshot(db)
    url = f"/api/v1/t/{SLUG_A}{case.path}"
    with capture_logs() as logs:
        refused = client.request(case.method, url, json=case.build(case.foreign))
        absent = client.request(case.method, url, json=case.build(case.missing))

    assert refused.status_code == 422, refused.text
    assert "reference.not_found" in _error_codes(refused), refused.text
    assert case.field_name in refused.text, refused.text
    assert [secret for secret in B_SECRETS if secret in refused.text.replace(case.foreign, "")] == [], refused.text
    assert _canonical(refused.text).replace(case.foreign, case.missing) == _canonical(absent.text), (
        refused.text,
        absent.text,
    )
    assert [entry for entry in logs if entry["event"] == "garden_plan.batch_applied"] == []
    assert _snapshot(db) == before, "a refused reference changed the database"


class TestABodyReferenceToAForeignKeyIsReferenceNotFound:
    @pytest.mark.parametrize("case", REFERENCE_CASES, ids=lambda case: case.name)
    def test_a_foreign_key_is_indistinguishable_from_an_absent_one_and_writes_nothing(
        self, db, case: ReferenceCase
    ) -> None:
        _assert_reference_refused(db, _client(db), case)

    @pytest.mark.parametrize("case", REFERENCE_CASES, ids=lambda case: case.name)
    def test_the_own_key_passes_the_reference_check(self, db, case: ReferenceCase) -> None:
        """The positive control: a key of the caller's own tenant is not ``reference.not_found``."""
        response = _client(db).request(case.method, f"/api/v1/t/{SLUG_A}{case.path}", json=case.build(case.own))

        assert "reference.not_found" not in response.text, response.text

    def test_no_slot_batch_body_field_can_name_a_foreign_key(self, db) -> None:
        """Wave 1's slot batch takes the bed in the path only; a key smuggled into the body is a 422, not a lookup."""
        client = _client(db)
        before = _snapshot(db)
        for smuggled in ("location_key", "key", "slot_key", "site_key"):
            body = {
                "mode": "append",
                "slots": [
                    {"slot_id": "INTRUDER_1", "geometry": {"kind": "point", "origin": [0.4, 0.5]}, smuggled: "bed_b"}
                ],
            }
            response = client.post(f"/api/v1/t/{SLUG_A}/locations/bed_a/slots/batch", json=body)
            assert response.status_code == 422, (smuggled, response.text)
            assert "reference.not_found" not in response.text
        assert _snapshot(db) == before


class TestTheReferenceChecksCanFail:
    """The same expression, with the reference resolution unscoped, must raise — for every body field."""

    @pytest.fixture
    def unscoped_references(self, db, monkeypatch) -> None:
        def every_structure(self, site_key, *, tenant_key):
            return (
                [Location(**doc) for doc in db.collection(col.LOCATIONS).all()],
                [GardenObject(**doc) for doc in db.collection(col.GARDEN_OBJECTS).all()],
            )

        def any_zone(self, zone_key, *, tenant_key):
            return "site_a" if db.collection(col.IRRIGATION_ZONES).has(zone_key) else None

        monkeypatch.setattr(ArangoGardenPlanRepository, "load_structure", every_structure)
        monkeypatch.setattr(ArangoGardenPlanRepository, "irrigation_zone_site_key", any_zone)

    @pytest.mark.parametrize("case", REFERENCE_CASES, ids=lambda case: case.name)
    def test_an_unscoped_resolution_is_caught(self, db, unscoped_references, case: ReferenceCase) -> None:
        with pytest.raises(AssertionError):
            _assert_reference_refused(db, _client(db), case)


# ── GP-ACC-046: the anchor, the model inventory and the AQL ───────────────────────────────────────


class TestTheOwnershipAnchor:
    def test_resolve_owned_location_refuses_the_other_tenants_location(self, db) -> None:
        sites = ArangoSiteRepository(db)

        with pytest.raises(NotFoundError):
            resolve_owned_location(sites, "bed_a", tenant_key=B)
        with pytest.raises(NotFoundError):
            resolve_owned_location(sites, "bed_b", tenant_key=A)
        with pytest.raises(NotFoundError):
            resolve_owned_location(sites, "bed_b", tenant_key="")

    def test_a_foreign_and_an_absent_location_answer_with_the_same_message(self, db) -> None:
        sites = ArangoSiteRepository(db)
        messages = []
        for key in ("bed_b", "bed_gone"):
            with pytest.raises(NotFoundError) as exc:
                resolve_owned_location(sites, key, tenant_key=A)
            messages.append(str(exc.value).replace(key, "<key>"))

        assert messages[0] == messages[1]
        assert not any(secret in messages[0] for secret in B_SECRETS if secret != "bed_b")

    def test_the_owner_resolves_its_own_location_and_slot(self, db) -> None:
        sites = ArangoSiteRepository(db)

        assert resolve_owned_location(sites, "bed_b", tenant_key=B).key == "bed_b"
        slot, location = resolve_owned_slot(sites, "slot_b", tenant_key=B)
        assert (slot.key, location.key) == ("slot_b", "bed_b")

    def test_resolve_owned_slot_refuses_the_other_tenants_slot(self, db) -> None:
        sites = ArangoSiteRepository(db)

        with pytest.raises(NotFoundError):
            resolve_owned_slot(sites, "slot_b", tenant_key=A)

    @pytest.mark.parametrize("model", [Location, Slot, GardenObject], ids=lambda model: model.__name__)
    def test_the_model_declares_no_tenant_key(self, model) -> None:
        assert "tenant_key" not in model.model_fields

    def test_the_documents_the_routes_write_carry_no_tenant_key(self, db) -> None:
        client = _client(db)
        created = client.post(f"/api/v1/t/{SLUG_A}/sites/site_a/garden-objects", json=_NEW_OBJECT)
        assert created.status_code == 201, created.text
        client.post(
            f"/api/v1/t/{SLUG_A}/locations/bed_a/slots/batch",
            json={
                "mode": "append",
                "slots": [{"slot_id": "OWN_SLOT_1", "geometry": {"kind": "point", "origin": [1, 1]}}],
            },
        )
        client.patch(f"/api/v1/t/{SLUG_A}/locations/bed_a", json={"name": "Renamed"})

        written = [
            doc
            for name in (col.LOCATIONS, col.SLOTS, col.GARDEN_OBJECTS)
            for doc in db.collection(name).all()
            if doc["_key"] in {created.json()["key"], "bed_a"} or str(doc.get("slot_id", "")).startswith("OWN_")
        ]
        assert len(written) == 3, written
        assert [doc["_key"] for doc in written if "tenant_key" in doc] == []


_TENANTLESS = {col.LOCATIONS, col.SLOTS, col.GARDEN_OBJECTS}
_FOR = re.compile(r"\bFOR\s+(\w+)\s+IN\s+(@@\w+|\w+)")


def tenant_predicates_on_tenantless_collections(query: str, bind_vars: dict[str, Any] | None) -> list[str]:
    """The aliases of ``locations`` / ``slots`` / ``garden_objects`` that the query reads ``.tenant_key`` from."""
    binds = bind_vars or {}
    found = []
    for alias, source in _FOR.findall(query):
        collection = binds.get(source[1:], "") if source.startswith("@@") else source
        if collection in _TENANTLESS and re.search(rf"\b{alias}\.tenant_key\b", query):
            found.append(f"{alias} IN {collection}")
    return found


class TestTheAqlNeverReadsATenantKeyOffATenantlessCollection:
    @pytest.fixture
    def executed(self, monkeypatch) -> Iterator[list[tuple[str, dict[str, Any] | None]]]:
        from arango.aql import AQL

        seen: list[tuple[str, dict[str, Any] | None]] = []
        original = AQL.execute

        def recording(self, query, *args, **kwargs):
            seen.append((query, kwargs.get("bind_vars")))
            return original(self, query, *args, **kwargs)

        monkeypatch.setattr(AQL, "execute", recording)
        yield seen

    def test_every_query_the_matrix_runs_is_clean(self, db, executed) -> None:
        for tenant, slug in ((A, SLUG_A), (B, SLUG_B)):
            client = _client(db, tenant=tenant)
            for case in CASES:
                if not case.writes:
                    _send(client, case, slug)
        _send(_client(db, tenant=B), next(c for c in CASES if c.name == "apply_batch"), SLUG_B)
        _send(_client(db, tenant=B), next(c for c in CASES if c.name == "apply_slot_batch"), SLUG_B)
        _send(_client(db, tenant=B), next(c for c in CASES if c.name == "change_location_status"), SLUG_B)

        assert len(executed) > 20, "the scan saw almost no AQL — it measures nothing"
        reads_the_collections = [
            (query, binds)
            for query, binds in executed
            if _TENANTLESS
            & {*(v for v in (binds or {}).values() if isinstance(v, str)), *re.findall(r"\bIN\s+(\w+)", query)}
        ]
        assert reads_the_collections, "no executed query touched locations, slots or garden_objects"
        offenders = [
            (hits, query)
            for query, binds in executed
            if (hits := tenant_predicates_on_tenantless_collections(query, binds))
        ]
        assert offenders == []

    def test_the_scanner_finds_a_planted_predicate_through_a_bind_variable(self) -> None:
        planted = "FOR l IN @@col FILTER l.tenant_key == @tenant_key RETURN l"

        assert tenant_predicates_on_tenantless_collections(planted, {"@col": col.LOCATIONS}) == ["l IN locations"]
        assert tenant_predicates_on_tenantless_collections("FOR s IN slots RETURN s.tenant_key", None) == ["s IN slots"]
        # The anchor's own predicate (on the site) and other collections' tenant keys are legitimate.
        site = "FOR l IN @@col LET site = DOCUMENT(@@sites, l.site_key) FILTER site.tenant_key == @tenant_key RETURN l"
        assert tenant_predicates_on_tenantless_collections(site, {"@col": col.LOCATIONS, "@@sites": "sites"}) == []
        assert (
            tenant_predicates_on_tenantless_collections(
                "FOR p IN @@plants FILTER p.tenant_key == @t RETURN p", {"@plants": col.PLANT_INSTANCES}
            )
            == []
        )
