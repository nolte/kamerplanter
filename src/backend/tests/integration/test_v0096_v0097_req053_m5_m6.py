"""#2325 (REQ-053 M6 + M5, GP-ACC-037/049/038) — v0096 and v0097 measured on a real ArangoDB.

* v0096 renames the family feeder level, flags a legacy nitrogen fixer, lists the
  species without a sourced level, converts a stored rotation-plan row — and the family
  importer that runs right after the migrations re-reads the rewritten rows through the
  renamed enum without a crash (the enum-retirement trap);
* v0097 rewrites the stored cron rules to RRULE (``0 8 * * 1`` → GP-ACC-038) and leaves
  RRULEs alone; with an unconvertible rule present it writes nothing and reports
  ``precondition_unmet``;
* a second run of either changes no document (``_rev`` stays), a dry run writes nothing.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0096_v0097_req053_m5_m6.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.domain.models.botanical_family import BotanicalFamily
from app.migrations.versions import v0096_nutrient_demand_split as m6_module
from app.migrations.versions.v0096_nutrient_demand_split import migration as m6
from app.migrations.versions.v0097_recurrence_cron_to_rrule import migration as m5
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migrations' scans and batched UPDATE statements are AQL over a real server"),
]

_DB_NAME = run_database_name("v0096_v0097_req053_m5_m6")


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield database
    system.delete_database(_DB_NAME)


def _revs(db, collection: str) -> dict[str, str]:  # type: ignore[no-untyped-def]
    return {doc["_key"]: doc["_rev"] for doc in db.collection(collection).all()}


def _pre_m6(db) -> None:  # type: ignore[no-untyped-def]
    families = db.collection(col.BOTANICAL_FAMILIES)
    families.insert(
        {"_key": "fabaceae", "name": "Fabaceae", "typical_nutrient_demand": "light", "nitrogen_fixing": True}
    )
    families.insert({"_key": "solanaceae", "name": "Solanaceae", "typical_nutrient_demand": "heavy"})
    families.insert({"_key": "rosaceae", "name": "Rosaceae", "typical_nutrient_demand": "medium_feeder"})
    species = db.collection(col.SPECIES)
    species.insert(
        {
            "_key": "pea",
            "scientific_name": "Pisum sativum",
            "scientific_name_normalized": "pisum sativum",
            "nutrient_demand_level": "nitrogen_fixer",
            "nutrient_demand": "light_feeder",
        }
    )
    species.insert(
        {
            "_key": "tomato",
            "scientific_name": "Solanum lycopersicum",
            "scientific_name_normalized": "solanum lycopersicum",
            "nutrient_demand_level": "heavy_feeder",
        }
    )
    species.insert(
        {
            "_key": "carrot",
            "scientific_name": "Daucus carota",
            "scientific_name_normalized": "daucus carota",
            "nutrient_demand": "medium_feeder",
        }
    )
    db.create_collection(m6_module.CROP_ROTATION_PLANS)
    plans = db.collection(m6_module.CROP_ROTATION_PLANS)
    plans.insert({"_key": "y1", "demand_level": "heavy_feeder"})
    plans.insert({"_key": "y2", "demand_level": "green_manure"})


class TestM6NutrientDemandSplit:
    def test_families_species_and_plans_are_converted(self, db) -> None:  # type: ignore[no-untyped-def]
        _pre_m6(db)

        report = m6.up(db)

        families = {d["_key"]: d["typical_nutrient_demand"] for d in db.collection(col.BOTANICAL_FAMILIES).all()}
        assert families == {"fabaceae": "light_feeder", "solanaceae": "heavy_feeder", "rosaceae": "medium_feeder"}
        for doc in db.collection(col.BOTANICAL_FAMILIES).all():
            assert BotanicalFamily.model_validate(doc).typical_nutrient_demand.value == families[doc["_key"]]
        pea = db.collection(col.SPECIES).get("pea")
        assert pea["nitrogen_fixing"] is True and pea["nutrient_demand"] == "light_feeder"
        assert "nutrient_demand" not in db.collection(col.SPECIES).get("tomato")
        plans = {d["_key"]: d for d in db.collection(m6_module.CROP_ROTATION_PLANS).all()}
        assert (plans["y1"]["nutrient_demand"], plans["y1"]["plan_role"]) == ("heavy_feeder", "main_crop")
        assert plans["y2"]["plan_role"] == "green_manure" and "nutrient_demand" not in plans["y2"]
        assert "demand_level" not in plans["y1"] and "demand_level" not in plans["y2"]
        assert report.changed == 2 + 1 + 2
        gap = report.details[col.SPECIES]["without_nutrient_demand"]
        assert gap == {"count": 1, "listed": ["Solanum lycopersicum"]}

    def test_a_second_run_changes_nothing(self, db) -> None:  # type: ignore[no-untyped-def]
        _pre_m6(db)
        m6.up(db)
        before = {c: _revs(db, c) for c in (col.BOTANICAL_FAMILIES, col.SPECIES, m6_module.CROP_ROTATION_PLANS)}

        report = m6.up(db)

        assert report.changed == 0
        assert {c: _revs(db, c) for c in before} == before

    def test_the_dry_run_writes_nothing(self, db) -> None:  # type: ignore[no-untyped-def]
        _pre_m6(db)
        before = {c: _revs(db, c) for c in (col.BOTANICAL_FAMILIES, col.SPECIES, m6_module.CROP_ROTATION_PLANS)}

        report = m6.up(db, dry_run=True)

        assert report.changed == 0 and report.details[col.BOTANICAL_FAMILIES]["will_update"] == 2
        assert {c: _revs(db, c) for c in before} == before
        assert db.collection(col.BOTANICAL_FAMILIES).get("fabaceae")["typical_nutrient_demand"] == "light"


class TestM5RecurrenceCronToRrule:
    def _tasks(self, db, *, with_refusal: bool = False) -> None:  # type: ignore[no-untyped-def]
        tasks = db.collection(col.TASKS)
        tasks.insert({"_key": "monday", "tenant_key": "t", "name": "Mulchen", "recurrence_rule": "0 8 * * 1"})
        tasks.insert({"_key": "rrule", "tenant_key": "t", "name": "Gießen", "recurrence_rule": "FREQ=DAILY"})
        tasks.insert({"_key": "one_off", "tenant_key": "t", "name": "Ernte"})
        if with_refusal:
            tasks.insert({"_key": "steps", "tenant_key": "t", "name": "Lüften", "recurrence_rule": "*/15 * * * *"})

    def test_the_gp_acc_038_rule_is_converted(self, db) -> None:  # type: ignore[no-untyped-def]
        self._tasks(db)

        report = m5.up(db)

        assert db.collection(col.TASKS).get("monday")["recurrence_rule"] == "FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0"
        assert db.collection(col.TASKS).get("rrule")["recurrence_rule"] == "FREQ=DAILY"
        assert (report.scanned, report.changed, report.precondition_unmet) == (2, 1, False)

    def test_a_second_run_changes_nothing(self, db) -> None:  # type: ignore[no-untyped-def]
        self._tasks(db)
        m5.up(db)
        before = _revs(db, col.TASKS)

        report = m5.up(db)

        assert report.changed == 0 and _revs(db, col.TASKS) == before

    def test_an_unconvertible_rule_is_parked_and_the_version_is_recorded(self, db) -> None:  # type: ignore[no-untyped-def]
        self._tasks(db, with_refusal=True)
        tasks = db.collection(col.TASKS)
        tasks.insert({"_key": "free", "tenant_key": "t2", "name": "Text", "recurrence_rule": "weekly"})
        before = _revs(db, col.TASKS)

        dry = m5.up(db, dry_run=True)
        assert _revs(db, col.TASKS) == before
        report = m5.up(db)

        assert {p["_key"]: (p["tenant_key"], p["rule"]) for p in dry.details["parked"]["listed"]} == {
            "steps": ("t", "*/15 * * * *"),
            "free": ("t2", "weekly"),
        }
        assert report.precondition_unmet is False and report.changed == 3
        steps = tasks.get("steps")
        assert steps["recurrence_rule"] is None and steps["recurrence_rule_unconvertible"] == "*/15 * * * *"
        assert tasks.get("free")["recurrence_rule_unconvertible"] == "weekly"
        assert tasks.get("monday")["recurrence_rule"] == "FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0"
        after = _revs(db, col.TASKS)
        assert m5.up(db).changed == 0 and _revs(db, col.TASKS) == after
