"""The seed sync carries the names per language onto existing diseases and beneficials (#2936).

``common_names_i18n`` is new on ``Disease`` and ``Beneficial`` and no migration may add
it (the privacy reservations hold the next migration numbers), so an existing
installation receives it through the seed loaders' update path. Measured against a
real server: a disease and a beneficial stored before the field existed gain the map
on the next ``run_seed``, and nothing else about their identity changes.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.seed_data import run_seed
from app.migrations.yaml_loader import load_yaml
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the seed sync is measured against a real server"),
]

_DB_NAME = run_database_name("seed_ipm_names_sync")


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch):
    system, database = create_database(_DB_NAME)
    bind_database(monkeypatch, database)
    yield database
    system.delete_database(_DB_NAME)


def _rows(db: StandardDatabase, collection: str, field: str, value: str) -> list[dict[str, Any]]:
    return list(
        db.aql.execute(
            "FOR doc IN @@c FILTER doc[@field] == @value RETURN doc",
            bind_vars={"@c": collection, "field": field, "value": value},
        )
    )


def test_a_disease_from_before_the_field_gains_its_names_per_language(db: StandardDatabase) -> None:
    planted = db.collection(col.DISEASES).insert(
        {"scientific_name": "Erysiphe spp.", "common_name": "Powdery Mildew", "pathogen_type": "fungal"}
    )

    run_seed()

    rows = _rows(db, col.DISEASES, "scientific_name", "Erysiphe spp.")
    seed = next(d for d in load_yaml("ipm.yaml")["diseases"] if d["scientific_name"] == "Erysiphe spp.")
    assert [r["_key"] for r in rows] == [planted["_key"]]
    assert rows[0]["common_names_i18n"] == seed["common_names_i18n"]
    assert rows[0]["common_names_i18n"]["de"] == ["Echter Mehltau"]


def test_a_beneficial_from_before_the_field_gains_its_names_per_language(db: StandardDatabase) -> None:
    planted = db.collection(col.BENEFICIALS).insert(
        {"slug": "predatory_mite", "common_name": "Raubmilben", "scientific_name": "Phytoseiidae"}
    )

    run_seed()

    rows = _rows(db, col.BENEFICIALS, "slug", "predatory_mite")
    assert [r["_key"] for r in rows] == [planted["_key"]]
    assert rows[0]["common_names_i18n"] == {"de": ["Raubmilben"], "en": ["Predatory mites"]}
