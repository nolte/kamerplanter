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
            {"_key": f"loc-{suffix}", "tenant_key": "", "site_key": f"site-{suffix}", "name": f"Bed {suffix}"}
        )
        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": f"plant-{suffix}",
                "tenant_key": tenant,
                "instance_id": f"PI-{suffix}",
                "plant_name": f"Plant {suffix}",
                "species_key": "sp-shared",
                "removed_on": None,
            }
        )
        db.collection(col.TANKS).insert({"_key": f"tank-{suffix}", "tenant_key": tenant, "name": f"Tank {suffix}"})
        db.collection(col.PLANTING_RUNS).insert(
            {"_key": f"run-{suffix}", "tenant_key": tenant, "name": f"Run {suffix}"}
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

    # Tasks instantiated from the system template: A on one plant, B on two.
    db.collection(col.TASK_TEMPLATES).insert(
        {"_key": "tt-system", "tenant_key": "", "workflow_template_key": SYSTEM_WORKFLOW, "name": "Step"}
    )
    for tenant, entity in ((TENANT_A, "plant-a"), (TENANT_B, "plant-b"), (TENANT_B, "plant-b2")):
        db.collection(col.TASKS).insert(
            {"tenant_key": tenant, "template_key": "tt-system", "entity_key": entity, "name": "Step"}
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


def _client(overrides: dict):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.v1.tenant_scoped.router import tenant_scoped_router
    from app.common.auth import get_current_tenant
    from app.common.enums import TenantRole
    from app.domain.models.tenant_context import TenantContext

    app = FastAPI()
    app.include_router(tenant_scoped_router, prefix="/api/v1")
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_A, tenant_slug=SLUG_A, user_key="user-a", role=TenantRole.LEAD
    )
    app.dependency_overrides.update(overrides)
    return TestClient(app, raise_server_exceptions=False)


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

    def test_usage_counts_of_a_shared_template_are_the_callers_only(self, db) -> None:
        from app.common.dependencies import get_task_service

        client = _client({get_task_service: lambda: _task_service(db)})

        response = client.get(f"/api/v1/t/{SLUG_A}/tasks/workflows")

        assert response.status_code == 200, response.text
        counts = {row["key"]: row["assigned_entity_count"] for row in response.json()}
        assert counts[SYSTEM_WORKFLOW] == 1, counts

    def test_phase_suggestions_carry_no_foreign_private_phase(self, db) -> None:
        from app.common.dependencies import get_task_service

        client = _client({get_task_service: lambda: _task_service(db)})

        response = client.get(f"/api/v1/t/{SLUG_A}/tasks/phases/suggestions")

        assert response.status_code == 200, response.text
        names = {row["name"] for row in response.json()}
        assert {"Secret phase a", "Shared phase"} <= names, names
        assert "Secret phase b" not in names


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
