"""The seed sync carries vernacular names and their language map onto existing rows (#2902).

``common_names_i18n`` is new and no migration may add it (the privacy reservations
hold the next migration numbers), so an existing installation receives it through
the seed loaders' update path. Measured against a real server:

* a GLOBAL species seeded before the field existed gains the map — and the corrected
  name list — on the next boot, from ``species.yaml`` (``run_seed``) and from
  ``adventskalender.yaml`` (``run_seed_adventskalender``, which until now synced only
  ``growing_periods`` onto an existing row);
* a TENANT's own species that shares the scientific name keeps the names its owner
  gave it.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.seed_adventskalender import run_seed_adventskalender
from app.migrations.seed_data import run_seed
from app.migrations.yaml_loader import load_yaml
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the seed sync is measured against a real server"),
]

_DB_NAME = run_database_name("seed_common_names_sync")


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch):
    system, database = create_database(_DB_NAME)
    bind_database(monkeypatch, database)
    yield database
    system.delete_database(_DB_NAME)


def _rows(db: StandardDatabase, scientific_name: str) -> list[dict[str, Any]]:
    return list(
        db.aql.execute(
            "FOR doc IN @@c FILTER doc.scientific_name == @name RETURN doc",
            bind_vars={"@c": col.SPECIES, "name": scientific_name},
        )
    )


def _seed_entry(filename: str, list_key: str, scientific_name: str) -> dict[str, Any]:
    return next(e for e in load_yaml(filename)[list_key] if e["scientific_name"] == scientific_name)


def test_a_global_row_from_before_the_field_gains_the_map_from_species_yaml(db: StandardDatabase) -> None:
    planted = db.collection(col.SPECIES).insert(
        {"scientific_name": "Daucus carota", "common_names": ["Carrot", "Karotte", "Möhre"], "tenant_key": ""}
    )

    run_seed()

    row = db.collection(col.SPECIES).get(planted["_key"])
    seed = _seed_entry("species.yaml", "species", "Daucus carota")
    assert row["common_names_i18n"] == seed["common_names_i18n"]
    assert row["common_names_i18n"]["de"][0] == "Möhre"
    assert row["common_names"] == seed["common_names"]


def test_a_tenants_own_species_keeps_its_names(db: StandardDatabase) -> None:
    planted = db.collection(col.SPECIES).insert(
        {"scientific_name": "Pisum sativum", "common_names": ["Meine Erbse"], "tenant_key": "t-grower"}
    )

    run_seed()

    row = db.collection(col.SPECIES).get(planted["_key"])
    assert row["common_names"] == ["Meine Erbse"]
    assert not row.get("common_names_i18n")


def test_a_global_row_gains_the_map_from_the_adventskalender(db: StandardDatabase) -> None:
    seed = _seed_entry("adventskalender.yaml", "new_species", "Allium porrum")
    planted = db.collection(col.SPECIES).insert(
        {"scientific_name": "Allium porrum", "common_names": ["Leek", "Porree"], "tenant_key": ""}
    )

    run_seed_adventskalender()

    rows = _rows(db, "Allium porrum")
    assert [r["_key"] for r in rows] == [planted["_key"]]
    assert rows[0]["common_names"] == seed["common_names"]
    assert rows[0]["common_names_i18n"] == seed["common_names_i18n"]
    assert rows[0]["common_names_i18n"]["de"][0] == "Porree"
