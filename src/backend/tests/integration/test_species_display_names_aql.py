"""#2902 — the AQL readers that name a species follow the display rule against a real store.

Four repository reads projected one species name in AQL by taking the first entry of
``common_names`` (``FIRST(species.common_names)``, ``species.common_names[0]``) — in
species.yaml the English one. They now project both name fields and resolve them in Python
through :mod:`app.domain.models.species_names`. A double that returns a pre-resolved name
would prove nothing about the projection, so every read here runs against a server: an
English-first species with a language map must come back German (the canonical language;
these readers have no request language), a species without a map keeps its first listed
name, and one whose map lacks German shows no vernacular name (or the scientific name where
the reader has a single name field).
Needs a real ArangoDB (see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.plant_state_repository import ArangoPlantStateRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("species_display_names")
pytestmark = pytest.mark.usefixtures("arango_db")

A = "ten_a"
NOW = datetime(2026, 6, 10, 12, 0, tzinfo=UTC)

_DOCUMENTS = (
    col.SPECIES,
    col.CULTIVARS,
    col.SLOTS,
    col.GROWTH_PHASES,
    col.PHASE_SEQUENCE_ENTRIES,
    col.PHASE_DEFINITIONS,
    col.PLANT_INSTANCES,
    col.PLANTING_RUNS,
    col.PLANTING_RUN_ENTRIES,
    col.TASKS,
    col.TASK_TEMPLATES,
    col.WORKFLOW_TEMPLATES,
    col.WORKFLOW_EXECUTIONS,
    col.CARE_EVENTS,
    col.PEST_DETECTIONS,
    col.HARVEST_BATCHES,
    col.LOCATIONS,
    col.SITES,
    col.TANKS,
)
_EDGES = (col.RUN_CONTAINS, col.PLACED_IN, col.RUN_PLANNED_AT, col.TENANT_HAS_ACCESS)

#: ``species key -> (vernacular name expected, display name expected)`` in the canonical language.
_EXPECTED = {
    # English first, as species.yaml lists it; the map names the German one.
    "tomato": ("Tomate", "Tomate"),
    # A tenant's own species without a language map: its first listed name stands.
    "mine": ("Meine Gurke", "Meine Gurke"),
    # A row without the attribute is a species without a map.
    "legacy": ("Zwiebel", "Zwiebel"),
    # A map without German: no vernacular name; the single-name readers show the scientific one.
    "only_en": (None, "Cucurbita maxima"),
}


@pytest.fixture(scope="module")
def _database():
    client = ArangoClient(hosts=ARANGO_URL)
    try:
        system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        if system.has_database(TEST_DATABASE):
            system.delete_database(TEST_DATABASE)
        system.create_database(TEST_DATABASE)
        database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        for name in _DOCUMENTS:
            database.create_collection(name)
        for name in _EDGES:
            database.create_collection(name, edge=True)
        yield database
        system.delete_database(TEST_DATABASE)
    finally:
        client.close()


@pytest.fixture
def db(_database):
    for name in (*_DOCUMENTS, *_EDGES):
        _database.collection(name).truncate()
    _database.collection(col.SPECIES).insert_many(
        [
            {
                "_key": "tomato",
                "tenant_key": "",
                "scientific_name": "Solanum lycopersicum",
                "common_names": ["Tomato", "Tomate", "Paradeiser"],
                "common_names_i18n": {"en": ["Tomato"], "de": ["Tomate", "Paradeiser"]},
            },
            {
                "_key": "mine",
                "tenant_key": A,
                "scientific_name": "Cucumis sativus",
                "common_names": ["Meine Gurke", "Gurke"],
                "common_names_i18n": {},
            },
            {
                # A row stored before the map existed carries no attribute at all (AQL reads null).
                "_key": "legacy",
                "tenant_key": "",
                "scientific_name": "Allium cepa",
                "common_names": ["Zwiebel", "Onion"],
            },
            {
                "_key": "only_en",
                "tenant_key": "",
                "scientific_name": "Cucurbita maxima",
                "common_names": ["Pumpkin"],
                "common_names_i18n": {"en": ["Pumpkin"]},
            },
        ]
    )
    _database.collection(col.SITES).insert({"_key": "site", "tenant_key": A, "name": "Garten"})
    _database.collection(col.LOCATIONS).insert({"_key": "bed", "site_key": "site", "name": "Beet 1"})
    return _database


def _plants(db) -> None:
    db.collection(col.PLANT_INSTANCES).insert_many(
        [
            {
                "_key": f"p_{species}",
                "tenant_key": A,
                "instance_id": f"I-{species}",
                "species_key": species,
                "location_key": "bed",
                "planted_on": "2026-04-01",
                "removed_on": None,
            }
            for species in _EXPECTED
        ]
    )


class TestPlantInstanceDashboardGrid:
    def test_the_card_title_is_the_vernacular_name_by_the_rule(self, db) -> None:
        _plants(db)

        rows = ArangoPlantInstanceRepository(db).list_active_for_tenant(A, 50)

        names = {row["species_key"]: row["species_common_name"] for row in rows}
        assert names == {key: vernacular for key, (vernacular, _display) in _EXPECTED.items()}
        # the raw name fields are resolved, not passed on
        assert all("species_common_names" not in row and "species_common_names_i18n" not in row for row in rows)
        assert {row["species_key"]: row["species_scientific_name"] for row in rows}["only_en"] == "Cucurbita maxima"


class TestPlantStates:
    def test_a_standing_plant_is_named_by_the_rule(self, db) -> None:
        _plants(db)

        sources = ArangoPlantStateRepository(db).list_bed_plants("bed", tenant_key=A, now=NOW, offset=0, limit=50)

        assert {source.species_key: source.species_name for source in sources} == {
            key: vernacular for key, (vernacular, _display) in _EXPECTED.items()
        }

    def test_a_sown_slot_is_named_by_the_rule(self, db) -> None:
        db.collection(col.PLANTING_RUNS).insert({"_key": "run", "tenant_key": A, "status": "planned"})
        for index, species in enumerate(_EXPECTED):
            slot = f"s{index}"
            db.collection(col.SLOTS).insert(
                {"_key": slot, "slot_id": f"BED_{index:03}", "location_key": "bed", "sown_at": "2026-04-02"}
            )
            db.collection(col.PLANTING_RUN_ENTRIES).insert({"_key": f"e{index}", "species_key": species})
            db.collection(col.RUN_PLANNED_AT).insert(
                {
                    "_from": f"{col.PLANTING_RUNS}/run",
                    "_to": f"{col.SLOTS}/{slot}",
                    "entry_key": f"e{index}",
                    "planned_species_key": species,
                    "planned_from": "2026-04-01",
                }
            )

        sown = ArangoPlantStateRepository(db).list_sown_slots("bed", tenant_key=A)

        assert {slot.species_key: slot.species_name for slot in sown} == {
            key: vernacular for key, (vernacular, _display) in _EXPECTED.items()
        }


class TestWorkflowReads:
    def test_the_usage_stats_name_the_template_species_by_the_rule(self, db) -> None:
        db.collection(col.WORKFLOW_TEMPLATES).insert_many(
            [{"_key": f"wf_{species}", "tenant_key": "", "species_key": species} for species in _EXPECTED]
            + [{"_key": "wf_none", "tenant_key": "", "species_key": None}]
        )

        stats = ArangoTaskRepository(db).get_workflow_usage_stats(
            [*(f"wf_{species}" for species in _EXPECTED), "wf_none"], tenant_key=A
        )

        assert {key: value["species_name"] for key, value in stats.items()} == {
            **{f"wf_{key}": display for key, (_vernacular, display) in _EXPECTED.items()},
            "wf_none": "",
        }
        assert all(set(value) == {"species_name", "entity_count"} for value in stats.values())

    def test_the_executions_name_the_plant_species_by_the_rule(self, db) -> None:
        _plants(db)
        db.collection(col.WORKFLOW_EXECUTIONS).insert_many(
            [
                {
                    "_key": f"we_{species}",
                    "workflow_template_key": "wf",
                    "entity_type": "plant_instance",
                    "entity_key": f"p_{species}",
                    "created_at": f"2026-05-0{index + 1}T00:00:00+00:00",
                }
                for index, species in enumerate(_EXPECTED)
            ]
        )

        rows = ArangoTaskRepository(db).get_executions_for_template("wf", tenant_key=A)

        assert {row["key"]: row["species_name"] for row in rows} == {
            f"we_{key}": display for key, (_vernacular, display) in _EXPECTED.items()
        }
        assert all(not any(field.startswith("sp_") for field in row) for row in rows)


class TestRequestLanguage:
    """The request's language (``Accept-Language``) reaches every read: the English-tagged name for ``en``."""

    def test_english(self, db) -> None:
        _plants(db)
        db.collection(col.WORKFLOW_TEMPLATES).insert({"_key": "wf_tomato", "tenant_key": "", "species_key": "tomato"})
        db.collection(col.WORKFLOW_EXECUTIONS).insert(
            {
                "_key": "we",
                "workflow_template_key": "wf",
                "entity_type": "plant_instance",
                "entity_key": "p_tomato",
                "created_at": "2026-05-01T00:00:00+00:00",
            }
        )
        tasks = ArangoTaskRepository(db)

        grid = ArangoPlantInstanceRepository(db).list_active_for_tenant(A, 50, language="en")
        states = ArangoPlantStateRepository(db).list_bed_plants(
            "bed", tenant_key=A, now=NOW, offset=0, limit=50, language="en"
        )
        stats = tasks.get_workflow_usage_stats(["wf_tomato"], tenant_key=A, language="en")
        executions = tasks.get_executions_for_template("wf", tenant_key=A, language="en")

        assert {row["species_key"]: row["species_common_name"] for row in grid}["tomato"] == "Tomato"
        # a species without a map keeps its first listed name; a map without English falls back to German
        assert {row["species_key"]: row["species_common_name"] for row in grid}["mine"] == "Meine Gurke"
        assert {source.species_key: source.species_name for source in states}["tomato"] == "Tomato"
        assert stats["wf_tomato"]["species_name"] == "Tomato"
        assert [row["species_name"] for row in executions] == ["Tomato"]


#: Another tenant's private species, and one of its private species granted to ``A`` (#1092).
B = "ten_b"
FOREIGN = "foreign"
GRANTED = "granted"


def _scoped_species(db) -> None:
    db.collection(col.SPECIES).insert_many(
        [
            {
                "_key": FOREIGN,
                "tenant_key": B,
                "scientific_name": "Secretus privatus",
                "common_names": ["Geheimkraut"],
                "common_names_i18n": {"de": ["Geheimkraut"]},
            },
            {
                "_key": GRANTED,
                "tenant_key": B,
                "scientific_name": "Communis datus",
                "common_names": ["Teilkraut"],
                "common_names_i18n": {"de": ["Teilkraut"]},
            },
        ]
    )
    db.collection(col.CULTIVARS).insert_many(
        [
            {"_key": "cv_foreign", "species_key": FOREIGN, "name": "Geheime Sorte"},
            {"_key": "cv_granted", "species_key": GRANTED, "name": "Geteilte Sorte"},
        ]
    )
    db.collection(col.TENANT_HAS_ACCESS).insert({"_from": f"{col.TENANTS}/{A}", "_to": f"{col.SPECIES}/{GRANTED}"})


def _legacy_plants(db) -> None:
    """``A``'s plants written before the species reference was verified (#2082): one names ``B``'s private species."""
    db.collection(col.PLANT_INSTANCES).insert_many(
        [
            {
                "_key": f"p_{species}",
                "tenant_key": A,
                "instance_id": f"I-{species}",
                "species_key": species,
                "cultivar_key": f"cv_{species}",
                "location_key": "bed",
                "planted_on": "2026-04-01",
                "removed_on": None,
            }
            for species in (FOREIGN, GRANTED)
        ]
    )


class TestStoredSpeciesKeyIsNoReadGrant:
    """A stored ``species_key`` names a species only when its tenant may read it: own, global or granted."""

    def test_the_dashboard_grid(self, db) -> None:
        _scoped_species(db)
        _legacy_plants(db)

        rows = {row["species_key"]: row for row in ArangoPlantInstanceRepository(db).list_active_for_tenant(A, 50)}

        assert rows[FOREIGN]["species_common_name"] is None
        assert rows[FOREIGN]["species_scientific_name"] is None
        assert rows[FOREIGN]["cultivar_name"] is None
        assert rows[GRANTED]["species_common_name"] == "Teilkraut"
        assert rows[GRANTED]["cultivar_name"] == "Geteilte Sorte"

    def test_the_phase_definition_list(self, db) -> None:
        _scoped_species(db)
        _legacy_plants(db)
        db.collection(col.PHASE_DEFINITIONS).insert({"_key": "def", "name": "vegetative"})
        db.collection(col.PHASE_SEQUENCE_ENTRIES).insert({"_key": "entry", "phase_definition_key": "def"})
        db.collection(col.PLANT_INSTANCES).update_match({"tenant_key": A}, {"current_phase_key": "entry"})

        rows = {
            row["species_key"]: row
            for row in ArangoPlantInstanceRepository(db).list_active_in_phase_definition(A, "def")
        }

        assert rows[FOREIGN]["species_scientific_name"] is None
        assert rows[FOREIGN]["species_common_names"] == []
        assert rows[GRANTED]["species_scientific_name"] == "Communis datus"

    def test_the_bed_plants(self, db) -> None:
        _scoped_species(db)
        _legacy_plants(db)

        sources = ArangoPlantStateRepository(db).list_bed_plants("bed", tenant_key=A, now=NOW, offset=0, limit=50)

        by_species = {source.species_key: source for source in sources}
        assert (by_species[FOREIGN].species_name, by_species[FOREIGN].scientific_name) == (None, None)
        assert by_species[FOREIGN].cultivar_name is None
        assert by_species[GRANTED].species_name == "Teilkraut"
        assert by_species[GRANTED].cultivar_name == "Geteilte Sorte"

    def test_the_sown_slots_name_a_granted_species(self, db) -> None:
        _scoped_species(db)
        db.collection(col.PLANTING_RUNS).insert({"_key": "run", "tenant_key": A, "status": "planned"})
        for index, species in enumerate((FOREIGN, GRANTED)):
            slot = f"s{index}"
            db.collection(col.SLOTS).insert(
                {"_key": slot, "slot_id": f"BED_{index:03}", "location_key": "bed", "sown_at": "2026-04-02"}
            )
            db.collection(col.PLANTING_RUN_ENTRIES).insert(
                {"_key": f"e{index}", "species_key": species, "cultivar_key": f"cv_{species}"}
            )
            db.collection(col.RUN_PLANNED_AT).insert(
                {
                    "_from": f"{col.PLANTING_RUNS}/run",
                    "_to": f"{col.SLOTS}/{slot}",
                    "entry_key": f"e{index}",
                    "planned_species_key": species,
                    "planned_from": "2026-04-01",
                }
            )

        sown = {slot.species_key: slot for slot in ArangoPlantStateRepository(db).list_sown_slots("bed", tenant_key=A)}

        assert (sown[FOREIGN].species_name, sown[FOREIGN].cultivar_name) == (None, None)
        assert sown[GRANTED].species_name == "Teilkraut"
        assert sown[GRANTED].cultivar_name == "Geteilte Sorte"

    def test_the_workflow_reads(self, db) -> None:
        _scoped_species(db)
        _legacy_plants(db)
        db.collection(col.WORKFLOW_TEMPLATES).insert_many(
            [{"_key": f"wf_{species}", "tenant_key": A, "species_key": species} for species in (FOREIGN, GRANTED)]
        )
        db.collection(col.WORKFLOW_EXECUTIONS).insert_many(
            [
                {
                    "_key": f"we_{species}",
                    "workflow_template_key": "wf",
                    "entity_type": "plant_instance",
                    "entity_key": f"p_{species}",
                    "created_at": f"2026-05-0{index + 1}T00:00:00+00:00",
                }
                for index, species in enumerate((FOREIGN, GRANTED))
            ]
        )
        tasks = ArangoTaskRepository(db)

        stats = tasks.get_workflow_usage_stats([f"wf_{FOREIGN}", f"wf_{GRANTED}"], tenant_key=A)
        executions = {row["key"]: row["species_name"] for row in tasks.get_executions_for_template("wf", tenant_key=A)}

        assert stats[f"wf_{FOREIGN}"]["species_name"] == ""
        assert stats[f"wf_{GRANTED}"]["species_name"] == "Teilkraut"
        assert executions == {f"we_{FOREIGN}": "", f"we_{GRANTED}": "Teilkraut"}
