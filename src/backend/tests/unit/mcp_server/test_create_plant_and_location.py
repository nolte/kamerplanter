"""MCP ``create_plant`` and ``create_location`` (#2719, REQ-033 §2.3/§2.4).

Driven through the real :class:`ToolDispatcher` and the real ``PlantInstanceService`` / ``SiteService``
over repository doubles that store whole models and serve them by key, so the refusals asserted here are
the services' own — a stubbed service could only show that the tool calls it. Every refusal is asserted
at the store as well: a ``pytest.raises`` alone would pass for a refusal that came after a write.

The same flows run against a real ArangoDB in ``tests/integration/test_mcp_setup_tools.py``.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.api.v1.locations.schemas import LocationCreate
from app.api.v1.plant_instances.schemas import PlantCreate
from app.common.enums import McpPermission, SiteType, TenantRole
from app.common.exceptions import DuplicateError, ForbiddenError, NotFoundError, ValidationError
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Location, Site, Slot
from app.domain.models.species import Species
from app.domain.services.plant_instance_service import PlantInstanceService
from app.domain.services.site_service import SiteService
from app.domain.services.species_service import SpeciesService
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import ToolRegistry, load_tools
from app.mcp_server.tools.plant_reads import ListPlants
from app.mcp_server.tools.plants import CreatePlant
from app.mcp_server.tools.sites import CreateLocation, GetLocation
from tests.unit.domain.services.test_plant_instance_reference_resolution import FakeSpeciesRepo
from tests.unit.mcp_server.test_dispatcher import _FakeAuditRepo, _FakeIdempotencyRepo

OWN = "tenant-own"
FOREIGN = "tenant-foreign"


class _SiteRepo:
    """Sites, locations and slots as the application writes them: the tenant lives on the site only."""

    def __init__(self) -> None:
        self.sites = {
            "site_own": Site(_key="site_own", tenant_key=OWN, name="Garden", type=SiteType.OUTDOOR),
            "site_foreign": Site(_key="site_foreign", tenant_key=FOREIGN, name="Other", type=SiteType.OUTDOOR),
        }
        self.locations = {
            "loc_own": Location(_key="loc_own", name="Bed A", area_m2=2.0, site_key="site_own"),
            "loc_foreign": Location(_key="loc_foreign", name="Bed B", area_m2=2.0, site_key="site_foreign"),
        }
        self.slots = {"slot_foreign": Slot(_key="slot_foreign", slot_id="B_001", location_key="loc_foreign")}
        self.created: list[Location] = []

    def get_site_by_key(self, key):
        return self.sites.get(key)

    def get_location_by_key(self, key):
        return self.locations.get(key)

    def get_slot_by_key(self, key):
        return self.slots.get(key)

    def get_site_or_raise(self, key):
        if key not in self.sites:
            raise NotFoundError("Site", key)
        return self.sites[key]

    def get_location_or_raise(self, key):
        if key not in self.locations:
            raise NotFoundError("Location", key)
        return self.locations[key]

    def create_location(self, location: Location) -> Location:
        stored = location.model_copy(update={"key": f"loc_new_{len(self.created) + 1}"})
        self.locations[stored.key] = stored
        self.created.append(stored)
        return stored


class _PlantRepo:
    """Plants as stored; ``verify_references`` refuses a cultivar that is not the tenant's or global."""

    readable_cultivars = {"cv_own"}

    def __init__(self) -> None:
        self.store: dict[str, PlantInstance] = {}

    def verify_references(self, plant: PlantInstance) -> None:
        if plant.cultivar_key is not None and plant.cultivar_key not in self.readable_cultivars:
            raise NotFoundError("Cultivar", plant.cultivar_key)

    def get_by_instance_id(self, instance_id, *, tenant_key):
        return next(
            (p for p in self.store.values() if p.instance_id == instance_id and p.tenant_key == tenant_key), None
        )

    def create(self, plant: PlantInstance) -> PlantInstance:
        self.verify_references(plant)
        if self.get_by_instance_id(plant.instance_id, tenant_key=plant.tenant_key) is not None:
            raise DuplicateError("plant_instances", "instance_id", plant.instance_id)
        stored = plant.model_copy(update={"key": f"pl_{len(self.store) + 1}"})
        self.store[stored.key] = stored
        return stored

    def get_all(self, offset=0, limit=50, *, tenant_key=None):
        plants = [p for p in self.store.values() if p.tenant_key == tenant_key]
        return plants[offset : offset + limit], len(plants)


def _species(key: str, tenant: str) -> Species:
    return Species(_key=key, tenant_key=tenant, scientific_name=f"Testus {key}")


def _setup(role: TenantRole = TenantRole.LEAD):
    site_repo = _SiteRepo()
    plant_repo = _PlantRepo()
    species_service = SpeciesService(
        FakeSpeciesRepo({"sp_global": _species("sp_global", ""), "sp_foreign": _species("sp_foreign", FOREIGN)}),
        MagicMock(),
        MagicMock(),
    )
    plant_service = PlantInstanceService(
        plant_repo, site_repo, MagicMock(), MagicMock(), species_service=species_service
    )
    registry = ToolRegistry()
    for tool in (CreatePlant(), CreateLocation(), GetLocation(), ListPlants()):
        registry.register(tool)
    dispatcher = ToolDispatcher(
        registry,
        MCPAuditLogger(_FakeAuditRepo()),
        IdempotencyStore(_FakeIdempotencyRepo()),
        services={"plant_instance_service": plant_service, "site_service": SiteService(site_repo)},
    )
    membership = McpTenantMembership(tenant_key=OWN, tenant_slug="own", tenant_name="Own", role=role)
    principal = McpPrincipal(account_key="sa-1", display_name="bot", is_service_account=True, memberships=(membership,))
    return dispatcher, principal, plant_repo, site_repo


_PLANT = {"instance_id": "TOM-001", "species_key": "sp_global", "planted_on": "2026-04-01", "site_key": "site_own"}
_LOCATION = {"name": "Bed C", "site_key": "site_own", "area_m2": 3.0}


# ── Contract ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("name", "permission"), [("create_plant", McpPermission.WRITE), ("create_location", McpPermission.SETUP)]
)
def test_the_tool_is_registered_tenant_scoped_with_dry_run_and_idempotency(name: str, permission: McpPermission):
    tool = load_tools().get(name)
    assert tool is not None
    assert tool.permission is permission
    assert tool.write and tool.tenant_scoped
    assert {"tenant", "dry_run", "idempotency_key"} <= set(tool.spec().input_schema["properties"])


def test_create_plant_takes_what_the_rest_create_body_takes():
    call_fields = {"tenant", "dry_run", "idempotency_key"}
    assert set(CreatePlant.Input.model_fields) - call_fields == set(PlantCreate.model_fields)


def test_create_location_takes_what_the_rest_create_body_takes():
    """Besides the plan fields of the geometry path (#2776), the tool is ``POST /locations``: no field more."""
    call_fields = {"tenant", "dry_run", "idempotency_key"}
    plan_fields = {"geometry", "height_m", "description", "sun_exposure"}
    assert set(CreateLocation.Input.model_fields) - call_fields - plan_fields == set(LocationCreate.model_fields)


# ── create_location ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_location_dry_run_validates_and_writes_nothing():
    dispatcher, principal, _plants, sites = _setup()

    response = await dispatcher.dispatch(principal, "create_location", {**_LOCATION, "dry_run": True})

    assert response.dry_run is True
    assert response.data["site_key"] == "site_own" and response.data["key"] is None
    assert sites.created == []


@pytest.mark.asyncio
async def test_a_location_is_created_and_get_location_reads_it():
    dispatcher, principal, _plants, sites = _setup()

    response = await dispatcher.dispatch(principal, "create_location", _LOCATION)

    (stored,) = sites.created
    assert response.data["key"] == response.data["location_key"] == stored.key
    assert response.data["area_m2"] == 3.0
    read = await dispatcher.dispatch(principal, "get_location", {"location_key": stored.key})
    assert read.data["site_key"] == "site_own"


@pytest.mark.asyncio
async def test_a_nested_location_takes_its_parents_site_and_depth():
    dispatcher, principal, _plants, sites = _setup()

    response = await dispatcher.dispatch(
        principal,
        "create_location",
        {"name": "Shelf", "site_key": "site_own", "area_m2": 1, "parent_location_key": "loc_own"},
    )

    assert response.data["depth"] == 1 and response.data["parent_location_key"] == "loc_own"
    assert sites.created[0].site_key == "site_own"


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    "overrides",
    [{"site_key": "site_foreign"}, {"parent_location_key": "loc_foreign"}, {"site_key": "site_nowhere"}],
    ids=["foreign-site", "foreign-parent", "unknown-site"],
)
async def test_a_location_on_a_foreign_anchor_is_not_found_and_nothing_is_stored(overrides, dry_run: bool):
    dispatcher, principal, _plants, sites = _setup()

    with pytest.raises(NotFoundError):
        await dispatcher.dispatch(principal, "create_location", {**_LOCATION, **overrides, "dry_run": dry_run})

    assert sites.created == []


@pytest.mark.asyncio
async def test_a_location_with_a_tank_the_tenant_does_not_own_is_refused():
    """No tank repository wired: the service fails closed rather than storing an unchecked key."""
    dispatcher, principal, _plants, sites = _setup()

    with pytest.raises(NotFoundError):
        await dispatcher.dispatch(principal, "create_location", {**_LOCATION, "tank_key": "tank_x", "dry_run": True})

    assert sites.created == []


@pytest.mark.asyncio
async def test_create_location_needs_the_setup_permission():
    dispatcher, principal, _plants, sites = _setup(TenantRole.GROWER)

    with pytest.raises(ForbiddenError):
        await dispatcher.dispatch(principal, "create_location", _LOCATION)

    assert sites.created == []


@pytest.mark.asyncio
async def test_the_same_idempotency_key_creates_one_location():
    dispatcher, principal, _plants, sites = _setup()
    args = {**_LOCATION, "idempotency_key": "bed-c"}

    first = await dispatcher.dispatch(principal, "create_location", args)
    second = await dispatcher.dispatch(principal, "create_location", args)

    assert len(sites.created) == 1
    assert second.idempotent_replay is True and second.data["key"] == first.data["key"]


# ── create_plant ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_plant_dry_run_validates_and_writes_nothing():
    dispatcher, principal, plants, _sites = _setup(TenantRole.GROWER)

    response = await dispatcher.dispatch(principal, "create_plant", {**_PLANT, "dry_run": True})

    assert response.dry_run is True
    assert response.data["instance_id"] == "TOM-001" and response.data["plant_key"] is None
    assert plants.store == {}


@pytest.mark.asyncio
async def test_a_plant_is_created_in_the_bound_tenant_and_listed():
    dispatcher, principal, plants, _sites = _setup(TenantRole.GROWER)

    response = await dispatcher.dispatch(principal, "create_plant", {**_PLANT, "location_key": "loc_own"})

    (stored,) = plants.store.values()
    assert stored.tenant_key == OWN and stored.location_key == "loc_own"
    assert stored.planted_on == date(2026, 4, 1)
    assert response.data["plant_key"] == stored.key
    listed = await dispatcher.dispatch(principal, "list_plants", {})
    assert [item["plant_key"] for item in listed.data["items"]] == [stored.key]


@pytest.mark.asyncio
async def test_the_same_idempotency_key_creates_one_plant():
    dispatcher, principal, plants, _sites = _setup(TenantRole.GROWER)
    args = {**_PLANT, "idempotency_key": "tom-1"}

    first = await dispatcher.dispatch(principal, "create_plant", args)
    second = await dispatcher.dispatch(principal, "create_plant", args)

    assert len(plants.store) == 1
    assert second.idempotent_replay is True and second.data["plant_key"] == first.data["plant_key"]


@pytest.mark.asyncio
async def test_a_dry_run_refuses_a_taken_instance_id_like_the_write():
    dispatcher, principal, plants, _sites = _setup(TenantRole.GROWER)
    await dispatcher.dispatch(principal, "create_plant", _PLANT)

    for dry_run in (True, False):
        with pytest.raises(DuplicateError):
            await dispatcher.dispatch(principal, "create_plant", {**_PLANT, "dry_run": dry_run})

    assert len(plants.store) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    "overrides",
    [
        {"site_key": "site_foreign"},
        {"site_key": None, "location_key": "loc_foreign"},
        {"site_key": None, "slot_key": "slot_foreign"},
        {"species_key": "sp_foreign"},
        {"cultivar_key": "cv_foreign"},
    ],
    ids=["site", "location", "slot", "species", "cultivar"],
)
async def test_a_key_of_another_tenant_is_refused_and_nothing_is_stored(overrides, dry_run: bool):
    """#1868/#1872: every caller-supplied key is resolved under the bound tenant, on the dry run as on the write."""
    dispatcher, principal, plants, _sites = _setup(TenantRole.GROWER)
    args = {key: value for key, value in {**_PLANT, **overrides}.items() if value is not None}

    with pytest.raises(NotFoundError):
        await dispatcher.dispatch(principal, "create_plant", {**args, "dry_run": dry_run})

    assert plants.store == {}


@pytest.mark.asyncio
async def test_an_empty_key_is_a_caller_error_not_a_lookup():
    dispatcher, principal, plants, _sites = _setup(TenantRole.GROWER)

    with pytest.raises(ValidationError):
        await dispatcher.dispatch(principal, "create_plant", {**_PLANT, "species_key": ""})

    assert plants.store == {}


@pytest.mark.asyncio
async def test_a_viewer_may_not_create_a_plant():
    dispatcher, principal, plants, _sites = _setup(TenantRole.VIEWER)

    with pytest.raises(ForbiddenError):
        await dispatcher.dispatch(principal, "create_plant", _PLANT)

    assert plants.store == {}
