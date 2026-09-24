"""#1708 — the reads the derived tenant-scope guard found answering across tenants.

``tests/unit/guards/test_tenant_scoped_reads_are_derived.py`` inventories every
repository read over a tenant-bearing collection instead of a hand list. Run
against the tree it was written for, it named six reads that took no tenant and
had no tenant-owned anchor, and each was traced to a route that reaches it:

* ``ArangoWateringLogRepository.resolve_fertilizer_names`` — the watering-log
  routes resolve every ``fertilizers_used[].fertilizer_key`` of a log to
  ``"<product> (<brand>)"``. The key comes from the request body and nothing
  verifies it on write, so a log naming another tenant's *private* fertilizer
  read its product name and brand back out (the #952 plant-name shape, for
  fertilizers). The calendar's forecast overlay resolved names the same way.
* ``ArangoTaskRepository.get_executions_for_template`` — ``GET
  /t/{slug}/tasks/workflows/{key}/executions`` checks read access to the template,
  and a **system** template is readable by every tenant, so the list returned
  every tenant's executions of it with plant, location, tank and run names.
* ``ArangoTaskRepository.get_workflow_usage_stats`` — the workflow list's
  ``assigned_entity_count`` counted every tenant's tasks of a system template.
* ``ArangoTaskRepository.get_phase_suggestions`` — aggregated the phase names of
  *every* workflow template, including other tenants' private ones.
* ``ArangoHarvestRepository.get_yield_statistics_for_species`` — ``GET
  /t/{slug}/harvest/species/{key}/yield-stats`` resolved the caller's tenant and
  then aggregated the yields of every tenant's batches.
* ``ArangoSpeciesRepository.find_synonym_match_candidates`` — creating a species
  copies unset fields from a fuller synonym-linked record (#975); the candidates
  were every species of every tenant, so a tenant could name another tenant's
  private species among its synonyms and receive that tenant's field values.

Every test runs the production path — the real repository against a real server,
behind the real service and, where one exists, the real route — and pairs the
foreign row with the caller's **own** or a global row, so a read that returns
nothing at all cannot pass.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.graph_repository import ArangoGraphRepository
from app.data_access.arango.harvest_repository import ArangoHarvestRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.data_access.arango.watering_log_repository import ArangoWateringLogRepository
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.engines.quality_scoring_engine import QualityScoringEngine
from app.domain.engines.readiness_engine import ReadinessEngine
from app.domain.engines.watering_engine import WateringEngine
from app.domain.models.species import Species
from app.domain.services.harvest_service import HarvestService
from app.domain.services.species_service import SpeciesService
from app.domain.services.task_service import TaskService
from app.domain.services.watering_log_service import WateringLogService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("derived_read_scope")
TENANT_A = "tenant-alice"
TENANT_B = "tenant-bob"
SLUG_A = "alice"
SLUG_B = "bob"

_DOCUMENT_COLLECTIONS = (
    col.FERTILIZERS,
    col.WATERING_LOGS,
    col.PLANT_INSTANCES,
    col.SPECIES,
    col.CULTIVARS,
    col.TASKS,
    col.TASK_TEMPLATES,
    col.WORKFLOW_TEMPLATES,
    col.WORKFLOW_PHASES,
    col.WORKFLOW_EXECUTIONS,
    col.LOCATIONS,
    col.SITES,
    col.TANKS,
    col.PLANTING_RUNS,
    col.HARVEST_BATCHES,
    col.YIELD_METRICS,
    col.SLOTS,
    col.TENANTS,
)
_EDGE_COLLECTIONS = (
    col.TENANT_HAS_ACCESS,
    col.LOG_PLANT,
    col.LOG_SLOT,
    col.LOG_FERTILIZER,
    col.HAS_CULTIVAR,
    col.CONTAINS,
    col.HAS_SLOT,
    col.WF_EXECUTING,
    col.WF_GENERATED,
    col.HAS_TASK,
    col.INSTANCE_OF,
)

#: A shared (system) workflow template every tenant may read.
SYSTEM_WORKFLOW = "wf-system"


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _DOCUMENT_COLLECTIONS:
        db.create_collection(name)
    for name in _EDGE_COLLECTIONS:
        db.create_collection(name, edge=True)

    yield db

    system.delete_database(TEST_DATABASE)


def _seed(db) -> None:
    now = datetime.now(UTC).isoformat()
    # Fertilizers: a global product, and one private product per tenant.
    db.collection(col.FERTILIZERS).insert(
        {"_key": "fert-global", "tenant_key": "", "product_name": "Global Grow", "brand": "Everyone"}
    )
    for tenant, suffix, product in ((TENANT_A, "a", "Alice Mix"), (TENANT_B, "b", "Bob Secret Blend")):
        db.collection(col.FERTILIZERS).insert(
            {"_key": f"fert-{suffix}", "tenant_key": tenant, "product_name": product, "brand": f"Brand {suffix}"}
        )

    # Plants, a location under a site, a tank and a run per tenant.
    for tenant, suffix in ((TENANT_A, "a"), (TENANT_B, "b")):
        db.collection(col.SITES).insert({"_key": f"site-{suffix}", "tenant_key": tenant, "name": f"Site {suffix}"})
        db.collection(col.LOCATIONS).insert(
            {
                "_key": f"loc-{suffix}",
                "tenant_key": "",
                "site_key": f"site-{suffix}",
                "name": f"Bed {suffix}",
                "area_m2": 1.0,
            }
        )
        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": f"plant-{suffix}",
                "tenant_key": tenant,
                "instance_id": f"PI-{suffix}",
                "plant_name": f"Plant {suffix}",
                "species_key": "sp-shared",
                "planted_on": "2026-01-01",
                "removed_on": None,
            }
        )
        db.collection(col.TANKS).insert(
            {
                "_key": f"tank-{suffix}",
                "tenant_key": tenant,
                "name": f"Tank {suffix}",
                "tank_type": "nutrient",
                "volume_liters": 10.0,
            }
        )
        db.collection(col.PLANTING_RUNS).insert(
            {"_key": f"run-{suffix}", "tenant_key": tenant, "name": f"Run {suffix}", "run_type": "monoculture"}
        )

    # Workflows: one shared system template, one private template per tenant.
    db.collection(col.WORKFLOW_TEMPLATES).insert(
        {"_key": SYSTEM_WORKFLOW, "tenant_key": "", "name": "Shared plan", "is_system": True, "species_compatible": []}
    )
    for tenant, suffix in ((TENANT_A, "a"), (TENANT_B, "b")):
        db.collection(col.WORKFLOW_TEMPLATES).insert(
            {"_key": f"wf-{suffix}", "tenant_key": tenant, "name": f"Private {suffix}", "species_compatible": []}
        )
        db.collection(col.WORKFLOW_PHASES).insert(
            {
                "workflow_template_key": f"wf-{suffix}",
                "name": f"Secret phase {suffix}",
                "phase_order": 0,
                "duration_days": 7,
                "stress_tolerance": "low",
            }
        )
    db.collection(col.WORKFLOW_PHASES).insert(
        {
            "workflow_template_key": SYSTEM_WORKFLOW,
            "name": "Shared phase",
            "phase_order": 0,
            "duration_days": 7,
            "stress_tolerance": "low",
        }
    )

    # Executions of the SYSTEM template by both tenants, on every entity type.
    for suffix in ("a", "b"):
        for entity_type, entity_key in (
            ("plant_instance", f"plant-{suffix}"),
            ("location", f"loc-{suffix}"),
            ("tank", f"tank-{suffix}"),
            ("planting_run", f"run-{suffix}"),
        ):
            db.collection(col.WORKFLOW_EXECUTIONS).insert(
                {
                    "_key": f"we-{entity_type}-{suffix}",
                    "workflow_template_key": SYSTEM_WORKFLOW,
                    "entity_type": entity_type,
                    "entity_key": entity_key,
                    "completion_percentage": 0,
                    "on_schedule": True,
                    "created_at": now,
                }
            )

    # The system template's one step. Tasks are NOT seeded: a task of this
    # template only ever comes into being through ``POST .../instantiate``, and a
    # seeded row carrying a ``tenant_key`` is a shape that route never produced
    # before #1708 — the usage-count test below certified nothing while it relied
    # on one. Tests instantiate through the route instead (``_instantiate``).
    db.collection(col.TASK_TEMPLATES).insert(
        {
            "_key": "tt-system",
            "tenant_key": "",
            "workflow_template_key": SYSTEM_WORKFLOW,
            "name": "Step",
            "category": "maintenance",
            "trigger_type": "manual",
        }
    )

    # Harvests of the shared species: A yields 100 g, B 900 g.
    for tenant, suffix, grams in ((TENANT_A, "a", 100.0), (TENANT_B, "b", 900.0)):
        db.collection(col.HARVEST_BATCHES).insert(
            {"_key": f"hb-{suffix}", "tenant_key": tenant, "plant_key": f"plant-{suffix}", "harvest_date": now}
        )
        db.collection(col.YIELD_METRICS).insert(
            {"batch_key": f"hb-{suffix}", "total_yield_g": grams, "trim_waste_percent": 0.0}
        )


@pytest.fixture
def db(database):
    for name in database.collections():
        if not name["system"]:
            database.collection(name["name"]).truncate()
    _seed(database)
    return database


def _task_service(db) -> TaskService:
    return TaskService(ArangoTaskRepository(db), HSTValidator(), DependencyResolver())


def _client(overrides: dict, *, tenant_key: str = TENANT_A, slug: str = SLUG_A):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.v1.tenant_scoped.router import tenant_scoped_router
    from app.common.auth import get_current_tenant
    from app.common.enums import TenantRole
    from app.common.error_handlers import app_error_handler
    from app.common.exceptions import KamerplanterError
    from app.domain.models.tenant_context import TenantContext

    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)
    app.include_router(tenant_scoped_router, prefix="/api/v1")
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=tenant_key, tenant_slug=slug, user_key=f"user-{slug}", role=TenantRole.LEAD
    )
    app.dependency_overrides.update(overrides)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def task_clients(db, monkeypatch):
    """Route clients for tenant A and B over the test database.

    ``get_task_entity_guard`` is **not** overridden: the real guard builds the
    real plant/run/tank/site services through ``app.common.dependencies``, whose
    ``get_db`` is pointed at the test database — the anchor the route applies in
    production, not a double that could accept what the real one refuses.
    """
    from app.common import dependencies
    from app.common.dependencies import get_task_service

    monkeypatch.setattr(dependencies, "get_db", lambda: db)
    overrides = {get_task_service: lambda: _task_service(db)}
    return (
        _client(overrides),
        _client(overrides, tenant_key=TENANT_B, slug=SLUG_B),
    )


def _instantiate(client, slug: str, entity_type: str, entity_key: str):
    return client.post(
        f"/api/v1/t/{slug}/tasks/workflows/{SYSTEM_WORKFLOW}/instantiate",
        json={"entity_type": entity_type, "entity_key": entity_key},
    )


class TestFertilizerNamesResolveInsideTheTenant:
    """``GET /t/{slug}/watering-logs/{key}`` for a log naming a foreign private fertilizer."""

    def test_a_foreign_private_fertilizer_keeps_its_name(self, db) -> None:
        from app.common.dependencies import get_watering_log_service

        db.collection(col.WATERING_LOGS).insert(
            {
                "_key": "log-a",
                "tenant_key": TENANT_A,
                "volume_liters": 1.0,
                "plant_keys": ["plant-a"],
                "fertilizers_used": [
                    {"fertilizer_key": "fert-a", "ml_per_liter": 1.0},
                    {"fertilizer_key": "fert-global", "ml_per_liter": 1.0},
                    {"fertilizer_key": "fert-b", "ml_per_liter": 1.0},
                ],
            }
        )
        service = WateringLogService(ArangoWateringLogRepository(db), WateringEngine(), ArangoSiteRepository(db))
        client = _client({get_watering_log_service: lambda: service})

        response = client.get(f"/api/v1/t/{SLUG_A}/watering-logs/log-a")

        assert response.status_code == 200, response.text
        names = {f["key"]: f["name"] for f in response.json()["resolved_fertilizers"]}
        assert names["fert-a"] == "Alice Mix (Brand a)"
        assert names["fert-global"] == "Global Grow (Everyone)"
        assert names["fert-b"] == "fert-b", f"foreign fertilizer name leaked: {names['fert-b']!r}"


class TestWorkflowReadsStayInsideTheTenant:
    def test_executions_of_a_shared_template_are_the_callers_only(self, db) -> None:
        from app.common.dependencies import get_task_service

        client = _client({get_task_service: lambda: _task_service(db)})

        response = client.get(f"/api/v1/t/{SLUG_A}/tasks/workflows/{SYSTEM_WORKFLOW}/executions")

        assert response.status_code == 200, response.text
        keys = {row["key"] for row in response.json()}
        assert keys == {"we-plant_instance-a", "we-location-a", "we-tank-a", "we-planting_run-a"}, sorted(keys)
        names = " ".join(row["entity_name"] for row in response.json())
        assert "Plant b" not in names and "Bed b" not in names

    def test_usage_counts_of_a_shared_template_are_the_callers_only(self, task_clients) -> None:
        client_a, client_b = task_clients
        # A runs the shared template on one entity, B on two.
        assert _instantiate(client_a, SLUG_A, "plant_instance", "plant-a").status_code == 201
        assert _instantiate(client_b, SLUG_B, "plant_instance", "plant-b").status_code == 201
        assert _instantiate(client_b, SLUG_B, "tank", "tank-b").status_code == 201

        for client, slug, expected in ((client_a, SLUG_A, 1), (client_b, SLUG_B, 2)):
            response = client.get(f"/api/v1/t/{slug}/tasks/workflows")

            assert response.status_code == 200, response.text
            counts = {row["key"]: row["assigned_entity_count"] for row in response.json()}
            assert counts[SYSTEM_WORKFLOW] == expected, (slug, counts)

    def test_phase_suggestions_carry_no_foreign_private_phase(self, db) -> None:
        from app.common.dependencies import get_task_service

        client = _client({get_task_service: lambda: _task_service(db)})

        response = client.get(f"/api/v1/t/{SLUG_A}/tasks/phases/suggestions")

        assert response.status_code == 200, response.text
        names = {row["name"] for row in response.json()}
        assert {"Secret phase a", "Shared phase"} <= names, names
        assert "Secret phase b" not in names


class TestInstantiatedTasksBelongToTheCaller:
    """``POST /t/{slug}/tasks/workflows/{key}/instantiate`` — the production path (#1708).

    The route used to build every task without a ``tenant_key``, so the tasks it
    generated were in no tenant's list; and it bound the execution to whatever
    entity key and type arrived.
    """

    def test_the_generated_tasks_are_in_the_callers_list_only(self, task_clients) -> None:
        client_a, client_b = task_clients

        created = _instantiate(client_a, SLUG_A, "plant_instance", "plant-a")

        assert created.status_code == 201, created.text
        execution_key = created.json()["key"]
        mine = client_a.get(f"/api/v1/t/{SLUG_A}/tasks")
        assert mine.status_code == 200, mine.text
        assert [t["workflow_execution_key"] for t in mine.json()] == [execution_key], mine.json()
        theirs = client_b.get(f"/api/v1/t/{SLUG_B}/tasks")
        assert theirs.status_code == 200, theirs.text
        assert theirs.json() == []

    def test_a_foreign_entity_is_refused_and_nothing_is_written(self, db, task_clients) -> None:
        client_a, client_b = task_clients

        for entity_type, entity_key in (
            ("plant_instance", "plant-b"),
            ("location", "loc-b"),
            ("tank", "tank-b"),
            ("planting_run", "run-b"),
        ):
            response = _instantiate(client_a, SLUG_A, entity_type, entity_key)
            assert response.status_code == 404, (entity_type, response.text)

        assert db.collection(col.TASKS).count() == 0
        assert client_b.get(f"/api/v1/t/{SLUG_B}/tasks").json() == []
        executions = client_b.get(f"/api/v1/t/{SLUG_B}/tasks/workflows/{SYSTEM_WORKFLOW}/executions").json()
        assert {row["key"] for row in executions} == {
            "we-plant_instance-b",
            "we-location-b",
            "we-tank-b",
            "we-planting_run-b",
        }

    def test_an_unknown_entity_type_is_a_422(self, db, task_clients) -> None:
        client_a, _ = task_clients

        response = _instantiate(client_a, SLUG_A, "generic", "plant-a")

        assert response.status_code == 422, response.text
        assert db.collection(col.TASKS).count() == 0


class TestExecutionsByKeyStayInsideTheTenant:
    """``GET /executions/{key}`` and ``POST /executions/{key}/tasks`` (#1714).

    ``WorkflowExecution`` carries no ``tenant_key``; it belongs to the owner of
    the entity it runs on. Both routes loaded the execution by its bare key, so a
    member of A read B's execution, and could attach a task to it that then
    counted in B's execution record. A foreign execution must answer exactly what
    an unknown key answers — anything else is an existence oracle over ascending
    Arango keys. An execution whose entity no longer resolves belongs to nobody.
    """

    _ENTITIES = ("plant_instance", "location", "tank", "planting_run")

    @staticmethod
    def _shape(response) -> tuple[int, str | None, str | None]:
        body = response.json()
        details = body.get("details") or [{}]
        return response.status_code, body.get("error_code"), details[0].get("entity")

    def test_the_callers_own_execution_is_readable(self, task_clients) -> None:
        client_a, _ = task_clients

        for entity_type in self._ENTITIES:
            response = client_a.get(f"/api/v1/t/{SLUG_A}/tasks/executions/we-{entity_type}-a")

            assert response.status_code == 200, (entity_type, response.text)
            assert response.json()["key"] == f"we-{entity_type}-a"

    def test_a_foreign_execution_reads_as_an_unknown_key(self, task_clients) -> None:
        client_a, _ = task_clients
        unknown = client_a.get(f"/api/v1/t/{SLUG_A}/tasks/executions/we-does-not-exist")
        assert unknown.status_code == 404, unknown.text

        for entity_type in self._ENTITIES:
            response = client_a.get(f"/api/v1/t/{SLUG_A}/tasks/executions/we-{entity_type}-b")

            assert self._shape(response) == self._shape(unknown), (entity_type, response.text)
            assert "Plant b" not in response.text and "plant-b" not in response.text

    def test_an_orphaned_execution_belongs_to_nobody(self, db, task_clients) -> None:
        client_a, _ = task_clients
        db.collection(col.PLANT_INSTANCES).delete("plant-a")
        db.collection(col.WORKFLOW_EXECUTIONS).insert(
            {"_key": "we-generic-a", "workflow_template_key": SYSTEM_WORKFLOW, "entity_type": "generic"}
        )

        for key in ("we-plant_instance-a", "we-generic-a"):
            response = client_a.get(f"/api/v1/t/{SLUG_A}/tasks/executions/{key}")

            assert response.status_code == 404, (key, response.text)

    def test_a_task_cannot_be_attached_to_a_foreign_execution(self, db, task_clients) -> None:
        client_a, client_b = task_clients

        for entity_type in self._ENTITIES:
            response = client_a.post(
                f"/api/v1/t/{SLUG_A}/tasks/executions/we-{entity_type}-b/tasks", json={"name": "Intruder"}
            )

            assert response.status_code == 404, (entity_type, response.text)

        assert db.collection(col.TASKS).count() == 0
        assert client_b.get(f"/api/v1/t/{SLUG_B}/tasks").json() == []

    def test_a_task_can_be_attached_to_the_callers_own_execution(self, task_clients) -> None:
        client_a, _ = task_clients

        response = client_a.post(f"/api/v1/t/{SLUG_A}/tasks/executions/we-tank-a/tasks", json={"name": "Top up"})

        assert response.status_code == 201, response.text
        created = response.json()
        assert created["workflow_execution_key"] == "we-tank-a"
        assert (created["entity_type"], created["entity_key"]) == ("tank", "tank-a")
        mine = client_a.get(f"/api/v1/t/{SLUG_A}/tasks").json()
        assert [t["key"] for t in mine] == [created["key"]]


class TestYieldStatisticsStayInsideTheTenant:
    def test_the_species_yield_aggregates_the_callers_batches_only(self, db) -> None:
        from app.common.dependencies import get_harvest_service

        service = HarvestService(ArangoHarvestRepository(db), MagicMock(), ReadinessEngine(), QualityScoringEngine())
        client = _client({get_harvest_service: lambda: service})

        response = client.get(f"/api/v1/t/{SLUG_A}/harvest/species/sp-shared/yield-stats")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["batch_count"] == 1, body
        assert body["total_yield_g"] == 100.0, body


class TestSynonymInheritanceStaysInsideTheTenant:
    """``SpeciesService.create_species`` fills unset fields from a synonym-linked record."""

    def _service(self, db) -> SpeciesService:
        return SpeciesService(ArangoSpeciesRepository(db), ArangoGraphRepository(db))

    def test_a_foreign_private_species_lends_nothing(self, db) -> None:
        repo = ArangoSpeciesRepository(db)
        repo.upsert_by_normalized_scientific_name(
            Species(scientific_name="Bobus secretus", tenant_key=TENANT_B, description="Bob's private notes")
        )

        created = self._service(db).create_species(
            Species(scientific_name="Alicea nova", tenant_key=TENANT_A, synonyms=["Bobus secretus"])
        )

        assert created.description == "", f"foreign species content inherited: {created.description!r}"

    def test_a_global_species_still_lends_its_fields(self, db) -> None:
        """The inheritance itself is not switched off — a visible record still fills gaps."""
        repo = ArangoSpeciesRepository(db)
        repo.upsert_by_normalized_scientific_name(
            Species(scientific_name="Globa communis", tenant_key="", description="Public notes")
        )

        created = self._service(db).create_species(
            Species(scientific_name="Alicea altera", tenant_key=TENANT_A, synonyms=["Globa communis"])
        )

        assert created.description == "Public notes"
