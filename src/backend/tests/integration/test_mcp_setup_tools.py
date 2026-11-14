"""MCP setup tools end to end: ``create_location``, ``create_plant`` (#2719) and the garden-plan and
succession tools of #2776 (REQ-033 §2.3/§2.4).

Driven through the real dispatcher, the real tools, services and repositories over a real ArangoDB, so the
refusals asserted here are the services' own. Every refusal is asserted at the store as well: a
``pytest.raises`` alone would pass for a refusal that came after a write.
"""

from __future__ import annotations

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import DuplicateError, ForbiddenError, NotFoundError, ValidationError
from tests.support.arango_integration import run_database_name
from tests.support.boundary_harness import TENANT_A, TENANT_B, open_env

pytestmark = pytest.mark.usefixtures("arango_db")

_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}


@pytest.fixture(scope="module")
def env():
    e = open_env(run_database_name("mcp_setup_tools"))
    yield e
    e.close()


@pytest.fixture
def db(env):
    from app.data_access.arango import collections as col

    database = env.db
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.SITES).insert(
        {
            "_key": "site-a",
            "tenant_key": TENANT_A,
            "name": "A",
            "type": "outdoor",
            "plan": {"boundary": _BOUNDARY, "plan_revision": 1},
        }
    )
    database.collection(col.LOCATION_TYPES).insert({"_key": "bed", "name": "Bed", "is_bed": True})
    database.collection(col.SITES).insert({"_key": "site-b", "tenant_key": TENANT_B, "name": "B", "type": "outdoor"})
    database.collection(col.LOCATIONS).insert({"_key": "loc-b", "site_key": "site-b", "name": "Bed B", "area_m2": 4})
    database.collection(col.SLOTS).insert({"_key": "slot-b", "slot_id": "B_001", "location_key": "loc-b"})
    database.collection(col.HAS_SLOT).insert({"_from": f"{col.LOCATIONS}/loc-b", "_to": f"{col.SLOTS}/slot-b"})
    for key, tenant in (("sp-global", ""), ("sp-b", TENANT_B)):
        database.collection(col.SPECIES).insert(
            {"_key": key, "scientific_name": f"Species {key}", "tenant_key": tenant}
        )
    database.collection(col.CULTIVARS).insert(
        {"_key": "cv-b", "name": "Foreign", "species_key": "sp-global", "tenant_key": TENANT_B}
    )
    return database


def _principal(role: TenantRole = TenantRole.LEAD):
    from app.mcp_server.principal import McpPrincipal, McpTenantMembership

    member = McpTenantMembership(tenant_key=TENANT_A, tenant_slug="alice", tenant_name="Alice", role=role)
    return McpPrincipal(account_key="user-a", display_name="Alice", is_service_account=True, memberships=(member,))


async def _call(tool: str, args: dict, role: TenantRole = TenantRole.LEAD):
    from app.common.dependencies import get_mcp_dispatcher

    return await get_mcp_dispatcher().dispatch(_principal(role), tool, args)


def _count(db, collection: str, **match) -> int:
    return sum(1 for doc in db.collection(collection).all() if all(doc.get(k) == v for k, v in match.items()))


# ── tools/list ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("tool", ["create_location", "create_plant"])
def test_the_tool_publishes_dry_run_and_idempotency_in_its_schema(tool: str):
    from app.mcp_server.registry import load_tools

    properties = load_tools().get(tool).spec().input_schema["properties"]
    assert {"tenant", "dry_run", "idempotency_key"} <= set(properties)


# ── create_location ───────────────────────────────────────────────────────────


_LOCATION = {"name": "Greenhouse bed", "site_key": "site-a", "area_m2": 6.0, "location_type_key": "bed"}


@pytest.mark.asyncio
async def test_a_location_dry_run_validates_and_writes_nothing(db):
    from app.data_access.arango import collections as col

    response = await _call("create_location", {**_LOCATION, "dry_run": True})

    assert response.dry_run is True
    assert response.data["site_key"] == "site-a" and response.data["key"] is None
    assert _count(db, col.LOCATIONS, site_key="site-a") == 0


@pytest.mark.asyncio
async def test_a_location_is_created_under_its_site_and_readable_again(db):
    response = await _call("create_location", _LOCATION)

    key = response.data["key"]
    assert key and response.data["area_m2"] == 6.0
    read = await _call("get_location", {"location_key": key})
    assert read.data["site_key"] == "site-a" and read.data["name"] == "Greenhouse bed"


@pytest.mark.asyncio
async def test_a_nested_location_takes_its_parents_site_and_depth(db):
    parent = await _call("create_location", _LOCATION)

    child = await _call(
        "create_location",
        {"name": "Shelf", "site_key": "site-a", "area_m2": 1.0, "parent_location_key": parent.data["key"]},
    )

    assert child.data["depth"] == 1
    assert child.data["parent_location_key"] == parent.data["key"]


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    "overrides",
    [{"site_key": "site-b"}, {"parent_location_key": "loc-b"}, {"site_key": "site-nowhere"}],
    ids=["foreign-site", "foreign-parent", "unknown-site"],
)
async def test_a_location_on_a_foreign_anchor_is_not_found_and_nothing_is_stored(db, overrides, dry_run: bool):
    from app.data_access.arango import collections as col

    before = db.collection(col.LOCATIONS).count()
    with pytest.raises(NotFoundError):
        await _call("create_location", {**_LOCATION, **overrides, "dry_run": dry_run})
    assert db.collection(col.LOCATIONS).count() == before


@pytest.mark.asyncio
async def test_create_location_is_a_setup_tool_a_grower_may_not_call(db):
    from app.data_access.arango import collections as col

    with pytest.raises(ForbiddenError):
        await _call("create_location", _LOCATION, role=TenantRole.GROWER)
    assert _count(db, col.LOCATIONS, site_key="site-a") == 0


@pytest.mark.asyncio
async def test_the_same_idempotency_key_creates_one_location(db):
    from app.data_access.arango import collections as col

    args = {**_LOCATION, "idempotency_key": "bed-1"}
    first = await _call("create_location", args)
    second = await _call("create_location", args)

    assert second.idempotent_replay is True and second.data["key"] == first.data["key"]
    assert _count(db, col.LOCATIONS, site_key="site-a") == 1


# ── create_plant ──────────────────────────────────────────────────────────────


_PLANT = {"instance_id": "TOM-001", "species_key": "sp-global", "planted_on": "2026-04-01", "site_key": "site-a"}


@pytest.mark.asyncio
async def test_a_plant_dry_run_validates_and_writes_nothing(db):
    from app.data_access.arango import collections as col

    response = await _call("create_plant", {**_PLANT, "dry_run": True}, role=TenantRole.GROWER)

    assert response.dry_run is True and response.data["instance_id"] == "TOM-001"
    assert db.collection(col.PLANT_INSTANCES).count() == 0


@pytest.mark.asyncio
async def test_a_created_plant_is_listed_and_takes_a_feeding_event(db):
    from app.data_access.arango import collections as col

    created = await _call("create_plant", _PLANT, role=TenantRole.GROWER)
    plant_key = created.data["plant_key"]

    stored = db.collection(col.PLANT_INSTANCES).get(plant_key)
    assert stored["tenant_key"] == TENANT_A
    listed = await _call("list_plants", {}, role=TenantRole.GROWER)
    assert [item["plant_key"] for item in listed.data["items"]] == [plant_key]
    fed = await _call(
        "record_feeding_event", {"plant_key": plant_key, "volume_applied_liters": 0.5}, role=TenantRole.GROWER
    )
    assert fed.dry_run is False


@pytest.mark.asyncio
async def test_a_plant_in_a_created_location_is_placed_there(db):
    location = await _call("create_location", _LOCATION)

    created = await _call("create_plant", {**_PLANT, "location_key": location.data["key"]}, role=TenantRole.GROWER)

    assert created.data["location_key"] == location.data["key"]


@pytest.mark.asyncio
async def test_the_same_idempotency_key_creates_one_plant(db):
    from app.data_access.arango import collections as col

    args = {**_PLANT, "idempotency_key": "tom-1"}
    first = await _call("create_plant", args, role=TenantRole.GROWER)
    second = await _call("create_plant", args, role=TenantRole.GROWER)

    assert second.idempotent_replay is True and second.data["plant_key"] == first.data["plant_key"]
    assert db.collection(col.PLANT_INSTANCES).count() == 1


@pytest.mark.asyncio
async def test_a_dry_run_refuses_a_taken_instance_id_like_the_write(db):
    from app.data_access.arango import collections as col

    await _call("create_plant", _PLANT, role=TenantRole.GROWER)

    for dry_run in (True, False):
        with pytest.raises(DuplicateError):
            await _call("create_plant", {**_PLANT, "dry_run": dry_run}, role=TenantRole.GROWER)
    assert db.collection(col.PLANT_INSTANCES).count() == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    "overrides",
    [
        {"site_key": "site-b"},
        {"site_key": None, "location_key": "loc-b"},
        {"site_key": None, "slot_key": "slot-b"},
        {"species_key": "sp-b"},
        {"cultivar_key": "cv-b"},
    ],
    ids=["site", "location", "slot", "species", "cultivar"],
)
async def test_a_key_of_another_tenant_is_refused_and_nothing_is_stored(db, overrides, dry_run: bool):
    from app.data_access.arango import collections as col

    args = {key: value for key, value in {**_PLANT, **overrides}.items() if value is not None}
    with pytest.raises(NotFoundError):
        await _call("create_plant", {**args, "dry_run": dry_run}, role=TenantRole.GROWER)
    assert db.collection(col.PLANT_INSTANCES).count() == 0


@pytest.mark.asyncio
async def test_an_empty_key_is_a_caller_error_not_a_lookup(db):
    with pytest.raises(ValidationError):
        await _call("create_plant", {**_PLANT, "species_key": ""}, role=TenantRole.GROWER)


@pytest.mark.asyncio
async def test_a_viewer_may_not_create_a_plant(db):
    from app.data_access.arango import collections as col

    with pytest.raises(ForbiddenError):
        await _call("create_plant", _PLANT, role=TenantRole.VIEWER)
    assert db.collection(col.PLANT_INSTANCES).count() == 0


# ── create_location with a geometry (#2776) ───────────────────────────────────


def _rect(x: float, y: float, w: float = 2, h: float = 1) -> dict:
    return {"kind": "rect", "origin": [x, y], "width_m": w, "length_m": h, "rotation_deg": 0}


_BED = {"name": "Beet 1", "site_key": "site-a", "location_type_key": "bed", "geometry": _rect(1, 1)}


@pytest.mark.asyncio
async def test_a_bed_with_a_geometry_is_placed_and_its_area_derived(db):
    from app.data_access.arango import collections as col

    dry = await _call("create_location", {**_BED, "dry_run": True})
    assert dry.data["area_m2"] == 2.0 and _count(db, col.LOCATIONS, site_key="site-a") == 0

    response = await _call("create_location", _BED)

    stored = db.collection(col.LOCATIONS).get(response.data["key"])
    assert stored["site_key"] == "site-a" and stored["area_m2"] == 2.0
    assert db.collection(col.SITES).get("site-a")["plan"]["plan_revision"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("geometry", "code"),
    [(_rect(9, 9, 4, 4), "geometry.outside_parent"), (_rect(1.5, 1.2), "bed.overlap")],
    ids=["V-03", "V-05"],
)
async def test_a_bed_breaking_a_plan_rule_is_refused_with_its_code(db, geometry, code: str):
    from app.data_access.arango import collections as col
    from app.mcp_server.base import McpToolError

    await _call("create_location", _BED)

    with pytest.raises(McpToolError) as refused:
        await _call("create_location", {**_BED, "name": "Beet 2", "geometry": geometry})

    assert code in {finding["code"] for finding in refused.value.error_details["findings"]}
    assert _count(db, col.LOCATIONS, site_key="site-a") == 1


@pytest.mark.asyncio
async def test_a_plant_in_a_placed_bed_shows_in_the_beds_rotation_matrix_row(db):
    from app.common.dependencies import get_rotation_matrix_service

    bed = await _call("create_location", _BED)
    await _call(
        "create_plant",
        {**_PLANT, "location_key": bed.data["key"], "planted_on": "2026-04-01"},
        role=TenantRole.GROWER,
    )

    matrix = get_rotation_matrix_service().rotation_matrix("site-a", tenant_key=TENANT_A)

    (row,) = [b for b in matrix.beds if b.location_key == bed.data["key"]]
    assert "sp-global" in {entry.species_key for entry in row.entries}


# ── Succession (#2776) ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_succession_plan_generates_runs_list_planting_runs_finds(db):
    from app.data_access.arango import collections as col

    plan = await _call(
        "create_succession_plan",
        {
            "name": "Salat",
            "species_key": "sp-global",
            "interval_days": 14,
            "start_date": "2027-04-01",
            "end_date": "2027-04-29",
            "plants_per_batch": 4,
        },
        role=TenantRole.GROWER,
    )
    key = plan.data["succession_plan_key"]

    preview = await _call(
        "generate_succession_runs", {"succession_plan_key": key, "dry_run": True}, role=TenantRole.GROWER
    )
    assert preview.data["generated_count"] == 3 and db.collection(col.PLANTING_RUNS).count() == 0

    generated = await _call("generate_succession_runs", {"succession_plan_key": key}, role=TenantRole.GROWER)
    listed = await _call("list_planting_runs", {}, role=TenantRole.GROWER)

    assert generated.data["generated_count"] == 3
    assert sorted(item["run_key"] for item in listed.data["items"]) == sorted(
        run["run_key"] for run in generated.data["runs"]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    "overrides",
    [{"location_key": "loc-b"}, {"species_key": "sp-b"}, {"cultivar_key": "cv-b"}],
    ids=["location", "species", "cultivar"],
)
async def test_a_succession_plan_with_a_foreign_key_is_refused(db, overrides, dry_run: bool):
    from app.data_access.arango import collections as col

    args = {
        "name": "Salat",
        "species_key": "sp-global",
        "interval_days": 14,
        "start_date": "2027-04-01",
        "end_date": "2027-04-29",
        "plants_per_batch": 4,
        **overrides,
        "dry_run": dry_run,
    }
    with pytest.raises(NotFoundError):
        await _call("create_succession_plan", args, role=TenantRole.GROWER)
    assert db.collection(col.SUCCESSION_PLANS).count() == 0


@pytest.mark.asyncio
async def test_succession_plans_are_listed_and_read_in_the_own_tenant_only(db):
    from app.data_access.arango import collections as col

    created = await _call(
        "create_succession_plan",
        {
            "name": "Salat",
            "species_key": "sp-global",
            "interval_days": 14,
            "start_date": "2027-04-01",
            "end_date": "2027-04-29",
            "plants_per_batch": 4,
        },
        role=TenantRole.GROWER,
    )
    own = created.data["succession_plan_key"]
    db.collection(col.SUCCESSION_PLANS).insert(
        {
            "_key": "plan-b",
            "tenant_key": TENANT_B,
            "name": "Foreign",
            "species_key": "sp-b",
            "interval_days": 7,
            "start_date": "2027-04-01",
            "end_date": "2027-04-15",
            "plants_per_batch": 2,
            "total_batches": 3,
        }
    )

    listed = await _call("list_succession_plans", {}, role=TenantRole.VIEWER)
    got = await _call("get_succession_plan", {"succession_plan_key": own}, role=TenantRole.VIEWER)

    assert listed.data["total"] == 1
    assert [item["succession_plan_key"] for item in listed.data["items"]] == [own]
    assert got.data["name"] == "Salat" and got.data["total_batches"] == 3
    for key in ("plan-b", "plan-missing"):
        with pytest.raises(NotFoundError):
            await _call("get_succession_plan", {"succession_plan_key": key}, role=TenantRole.VIEWER)
