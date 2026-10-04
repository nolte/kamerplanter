"""#1963 — a legacy row whose reference field is foreign, against a real ArangoDB.

v0067 (#1878) drops the cross-tenant *edge* a #1871 hole wrote and leaves the source
document alone, because every source mirrors the same key in its own field. After it
the edge and the field disagree, and a reader that follows the field instead of the
edge still reaches the foreign row. This module seeds exactly that post-v0067 state —
the edge gone, the field foreign — and drives the **production** readers and the
repair, each next to the rows that must survive (the tenant's own, a global species, a
granted one), so a reader that returns nothing at all cannot pass.

What the measurement found, per field (see the inventory in the PR body):

* ``planting_run_entries.species_key`` is dereferenced by three readers that trusted
  it: ``create_plants`` (reads the species' phase data and stamps its key on every new
  plant), ``get_phase_timeline`` (reads the species' phases and, in the route, its
  scientific name) and the irrigation task (reads its crop coefficient).
* ``equipment.location_key``, ``location_assignments.location_key`` and
  ``watering_logs.slot_keys`` are never dereferenced by a reader — they are only echoed
  as a string — so for them the repair is the migration (v0080) that restores the
  agreement between field and edge.
* ``feeds_from`` has no mirrored field at all.

What this cannot say: how many such rows a real installation holds. The numbers here are
synthetic.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.inventree_repository import ArangoInvenTreeRepository
from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository
from app.data_access.arango.location_assignment_repository import ArangoLocationAssignmentRepository
from app.data_access.arango.phase_sequence_repository import ArangoPhaseSequenceRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.data_access.arango.watering_log_repository import ArangoWateringLogRepository
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.species_service import SpeciesService
from app.migrations.support.legacy_foreign_fields import COUNT_QUERIES
from app.migrations.versions.v0080_null_foreign_reference_fields import migration
from app.tasks.irrigation_tasks import _resolve_species_kc
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("legacy_foreign_fields")
TENANT = "A"


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)
    client.close()


def _seed(db) -> None:
    """The post-v0067 state: tenant A's rows name tenant B's rows through their own field."""

    def put(collection: str, **doc) -> None:
        db.collection(collection).insert(doc)

    for name in (
        col.SITES, col.LOCATIONS, col.SLOTS, col.HAS_SLOT, col.SPECIES, col.LIFECYCLE_CONFIGS, col.HAS_LIFECYCLE,
        col.GROWTH_PHASES, col.CONSISTS_OF, col.EQUIPMENT, col.LOCATION_ASSIGNMENTS, col.WATERING_LOGS,
        col.PLANTING_RUNS, col.PLANTING_RUN_ENTRIES, col.PLANT_INSTANCES, col.RUN_CONTAINS, col.TENANT_HAS_ACCESS,
        col.TENANTS, col.PLACED_IN,
    ):  # fmt: skip
        db.collection(name).truncate()

    put(col.SITES, _key="siteA", tenant_key="A")
    put(col.SITES, _key="siteB", tenant_key="B")
    put(col.LOCATIONS, _key="locA", site_key="siteA", name="own bed")
    put(col.LOCATIONS, _key="locB", site_key="siteB", name="foreign bed")
    put(col.SLOTS, _key="slotA", location_key="locA")
    put(col.SLOTS, _key="slotB", location_key="locB")
    put(col.HAS_SLOT, _from="locations/locA", _to="slots/slotA")
    put(col.HAS_SLOT, _from="locations/locB", _to="slots/slotB")

    # Species: global, tenant B's private one, and one of B's granted to A. Each has phase data.
    put(col.TENANTS, _key="A")
    put(
        col.SPECIES,
        _key="spG",
        scientific_name_normalized="global species",
        tenant_key="",
        scientific_name="Global species",
        default_crop_coefficient_kc=0.8,
    )
    put(
        col.SPECIES,
        _key="spB",
        scientific_name_normalized="foreign private species",
        tenant_key="B",
        scientific_name="Foreign private species",
        default_crop_coefficient_kc=0.9,
    )
    put(
        col.SPECIES,
        _key="spGr",
        scientific_name_normalized="granted species",
        tenant_key="B",
        scientific_name="Granted species",
        default_crop_coefficient_kc=0.7,
    )
    put(col.TENANT_HAS_ACCESS, _from="tenants/A", _to="species/spGr")
    for sp in ("spG", "spB", "spGr"):
        put(col.LIFECYCLE_CONFIGS, _key=f"lc{sp}", species_key=sp, cycle_type="annual")
        put(col.HAS_LIFECYCLE, _from=f"species/{sp}", _to=f"lifecycle_configs/lc{sp}")
        put(
            col.GROWTH_PHASES, _key=f"gp{sp}", name=f"phase of {sp}", lifecycle_key=f"lc{sp}",
            typical_duration_days=7, sequence_order=0,
        )  # fmt: skip
        put(col.CONSISTS_OF, _from=f"lifecycle_configs/lc{sp}", _to=f"growth_phases/gp{sp}")

    # Equipment: a legacy foreign location, the tenant's own, and a location that no longer exists.
    put(col.EQUIPMENT, _key="eqForeign", tenant_key="A", name="Fan", equipment_type="tool", location_key="locB")
    put(col.EQUIPMENT, _key="eqOwn", tenant_key="A", name="Lamp", equipment_type="tool", location_key="locA")
    put(col.EQUIPMENT, _key="eqDangling", tenant_key="A", name="Pump", equipment_type="tool", location_key="gone")
    put(col.EQUIPMENT, _key="eqNone", tenant_key="A", name="Hose", equipment_type="tool")

    # Assignments: counted, never rewritten (location_key is required on the model).
    put(col.LOCATION_ASSIGNMENTS, _key="asForeign", tenant_key="A", membership_key="m", location_key="locB")
    put(col.LOCATION_ASSIGNMENTS, _key="asOwn", tenant_key="A", membership_key="m", location_key="locA")

    # Watering logs: foreign slot next to an own one; only a foreign slot; foreign slot with a plant.
    common = {"tenant_key": "A", "logged_at": "2026-01-01T00:00:00+00:00", "application_method": "drench"}
    put(col.WATERING_LOGS, _key="wlMixed", slot_keys=["slotB", "slotA"], plant_keys=[], volume_liters=1.0, **common)
    put(col.WATERING_LOGS, _key="wlOnlyForeign", slot_keys=["slotB"], plant_keys=[], volume_liters=1.0, **common)
    put(col.WATERING_LOGS, _key="wlWithPlant", slot_keys=["slotB"], plant_keys=["p1"], volume_liters=1.0, **common)
    put(col.WATERING_LOGS, _key="wlOwn", slot_keys=["slotA"], plant_keys=[], volume_liters=1.0, **common)

    # Planting runs and entries.
    put(col.PLANTING_RUNS, _key="runGlobal", tenant_key="A", name="global", run_type="monoculture", status="planned")
    put(col.PLANTING_RUNS, _key="runForeign", tenant_key="A", name="foreign", run_type="monoculture", status="planned")
    put(col.PLANTING_RUNS, _key="runGranted", tenant_key="A", name="granted", run_type="monoculture", status="planned")
    put(
        col.PLANTING_RUN_ENTRIES,
        _key="enG",
        run_key="runGlobal",
        tenant_key="A",
        species_key="spG",
        quantity=1,
        id_prefix="GLB",
    )
    put(
        col.PLANTING_RUN_ENTRIES,
        _key="enB",
        run_key="runForeign",
        tenant_key="A",
        species_key="spB",
        quantity=2,
        id_prefix="FOR",
    )
    put(
        col.PLANTING_RUN_ENTRIES,
        _key="enGr",
        run_key="runGranted",
        tenant_key="A",
        species_key="spGr",
        quantity=1,
        id_prefix="GRA",
    )

    # An active run with one plant per species, to read the phase timeline of.
    put(col.PLANTING_RUNS, _key="runActive", tenant_key="A", name="active", run_type="monoculture", status="active")
    for sp, pref in (("spG", "GLB"), ("spB", "FOR"), ("spGr", "GRA")):
        put(
            col.PLANTING_RUN_ENTRIES,
            _key=f"enT{sp}",
            run_key="runActive",
            tenant_key="A",
            species_key=sp,
            quantity=1,
            id_prefix=pref,
        )
        put(
            col.PLANT_INSTANCES, _key=f"pl{sp}", tenant_key="A", instance_id=f"{pref}-1", species_key=sp,
            planted_on="2026-01-01", current_phase=f"phase of {sp}",
        )  # fmt: skip
        put(col.RUN_CONTAINS, _from="planting_runs/runActive", _to=f"plant_instances/pl{sp}")


@pytest.fixture
def legacy(database):
    _seed(database)
    return database


def _service(db) -> tuple[PlantingRunService, ArangoPlantingRunRepository, ArangoSpeciesRepository]:
    species_repo = ArangoSpeciesRepository(db)
    species_service = SpeciesService(species_repo, MagicMock(), MagicMock())
    run_repo = ArangoPlantingRunRepository(db)
    service = PlantingRunService(
        run_repo,
        ArangoPlantInstanceRepository(db),
        PlantingRunEngine(),
        phase_repo=ArangoLifecycleRepository(db),
        site_repo=ArangoSiteRepository(db),
        phase_seq_repo=ArangoPhaseSequenceRepository(db),
        species_resolver=lambda key, *, tenant_key: species_service.get_species(key, tenant_key=tenant_key),
    )
    return service, run_repo, species_repo


def _plant_species(db) -> list[str]:
    return sorted(d["species_key"] for d in db.collection(col.PLANT_INSTANCES).all() if not d["_key"].startswith("pl"))


# -- readers of planting_run_entries.species_key ---------------------------------


def test_create_plants_refuses_a_legacy_entry_species_the_tenant_cannot_read(legacy) -> None:
    service, _, _ = _service(legacy)

    with pytest.raises(NotFoundError):
        service.create_plants("runForeign")

    # Nothing was planted or activated for the refused run ...
    assert _plant_species(legacy) == []
    assert legacy.collection(col.PLANTING_RUNS).get("runForeign")["status"] == "planned"
    # ... while a global species and a granted one still plant.
    service.create_plants("runGlobal")
    service.create_plants("runGranted")
    assert _plant_species(legacy) == ["spG", "spGr"]


def test_phase_timeline_skips_a_legacy_entry_species_the_tenant_cannot_read(legacy) -> None:
    service, _, _ = _service(legacy)

    timelines = service.get_phase_timeline("runActive")

    assert sorted(t["species_key"] for t in timelines) == ["spG", "spGr"]
    assert "phase of spB" not in {p["phase_name"] for t in timelines for p in t["phases"]}


def test_the_irrigation_task_reads_only_a_species_the_tenant_can_read(legacy) -> None:
    _, run_repo, species_repo = _service(legacy)
    foreign_run = run_repo.get_by_key("runForeign")
    global_run = run_repo.get_by_key("runGlobal")
    granted_run = run_repo.get_by_key("runGranted")

    assert _resolve_species_kc(foreign_run, run_repo, species_repo) == (None, None)
    assert _resolve_species_kc(global_run, run_repo, species_repo)[0] == 0.8
    assert _resolve_species_kc(granted_run, run_repo, species_repo)[0] == 0.7


# -- the fields no reader dereferences: v0080 restores field/edge agreement ------


def _counts(db) -> dict[str, dict[str, int]]:
    return {name: {r["verdict"]: r["n"] for r in db.aql.execute(query)} for name, query in COUNT_QUERIES.items()}


def test_the_count_queries_name_the_legacy_rows_before_anything_is_written(legacy) -> None:
    assert _counts(legacy) == {
        "equipment_location_foreign": {"null_field": 1, "unclassified": 1},
        "watering_log_slots_foreign": {"drop_foreign_slots": 2, "left_would_orphan": 1},
        "location_assignment_location_foreign": {"left_required_field": 1},
        "planting_run_entry_species_unreadable": {"left_required_field": 2},
    }


def test_a_dry_run_reads_and_writes_nothing(legacy) -> None:
    report = migration.up(legacy, dry_run=True)

    assert report.changed == 0
    assert legacy.collection(col.EQUIPMENT).get("eqForeign")["location_key"] == "locB"
    assert legacy.collection(col.WATERING_LOGS).get("wlMixed")["slot_keys"] == ["slotB", "slotA"]


def test_the_migration_repairs_exactly_what_the_count_names_and_is_idempotent(legacy) -> None:
    first = migration.up(legacy)

    equipment = {d["_key"]: d.get("location_key") for d in legacy.collection(col.EQUIPMENT).all()}
    assert equipment == {"eqForeign": None, "eqOwn": "locA", "eqDangling": "gone", "eqNone": None}
    logs = {d["_key"]: d["slot_keys"] for d in legacy.collection(col.WATERING_LOGS).all()}
    assert logs == {"wlMixed": ["slotA"], "wlOnlyForeign": ["slotB"], "wlWithPlant": [], "wlOwn": ["slotA"]}
    # Required fields are counted and left.
    assert legacy.collection(col.LOCATION_ASSIGNMENTS).get("asForeign")["location_key"] == "locB"
    assert legacy.collection(col.PLANTING_RUN_ENTRIES).get("enB")["species_key"] == "spB"
    assert first.changed == 1 + 2  # one equipment row, two watering logs

    second = migration.up(legacy)

    assert second.changed == 0
    assert _counts(legacy) == {
        "equipment_location_foreign": {"unclassified": 1},
        "watering_log_slots_foreign": {"left_would_orphan": 1},
        "location_assignment_location_foreign": {"left_required_field": 1},
        "planting_run_entry_species_unreadable": {"left_required_field": 2},
    }


def test_after_the_repair_the_readers_echo_no_foreign_key(legacy) -> None:
    migration.up(legacy)

    equipment = ArangoInvenTreeRepository(legacy).get_equipment("eqForeign")
    log = ArangoWateringLogRepository(legacy).get_by_key("wlMixed")
    assignments = ArangoLocationAssignmentRepository(legacy).list_by_tenant("A")

    assert equipment is not None and equipment.location_key is None
    assert log is not None and list(log.slot_keys) == ["slotA"]
    # The one echo left is the required field the migration cannot null (reported in the counts).
    assert sorted(a.location_key for a in assignments) == ["locA", "locB"]
