"""#2955 — pest names per language survive a real write: replaced whole, German derived.

The pest repository replaces ``common_names_i18n`` whole (as the disease one, #2936) and
writes the derived ``common_name_de`` even when it became ``None``: the default write
drops ``None`` fields, which would leave a stale German name in the row, and the next
read would put it back into the map. The mocked-repository API test cannot see either;
this test writes through the real ``ArangoIpmRepository``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from arango.database import StandardDatabase
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.ipm.router import router as ipm_router
from app.common.auth import get_current_user, get_is_platform_admin, require_platform_admin
from app.common.dependencies import get_ipm_service
from app.data_access.arango import collections as col
from app.data_access.arango.ipm_repository import ArangoIpmRepository
from app.domain.services.ipm_service import IpmService
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the update semantics of nested objects and nulls are the server's"),
]

_DB_NAME = run_database_name("ipm_pest_names_update")
_MITES = {"en": ["Spider Mites"], "de": ["Spinnmilben"]}


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch):
    system, database = create_database(_DB_NAME)
    bind_database(monkeypatch, database)
    yield database
    system.delete_database(_DB_NAME)


def _client(db: StandardDatabase) -> TestClient:
    def _user() -> SimpleNamespace:
        return SimpleNamespace(key="user_1")

    service = IpmService(ArangoIpmRepository(db), MagicMock(), MagicMock(), MagicMock())
    app = FastAPI()
    app.include_router(ipm_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_ipm_service] = lambda: service
    app.dependency_overrides[require_platform_admin] = _user
    app.dependency_overrides[get_is_platform_admin] = lambda: True
    return TestClient(app)


def _plant(db: StandardDatabase) -> str:
    return db.collection(col.PESTS).insert(
        {
            "scientific_name": "Tetranychus urticae",
            "common_name": "Spider Mites",
            "common_name_de": "Spinnmilben",
            "common_names_i18n": _MITES,
        }
    )["_key"]


def test_a_put_without_german_removes_it_from_the_map_and_the_compat_field(db: StandardDatabase) -> None:
    key = _plant(db)
    client = _client(db)

    resp = client.put(f"/api/v1/ipm/pests/{key}", json={"common_names_i18n": {"en": ["Spider Mites"]}})
    reread = client.get(f"/api/v1/ipm/pests/{key}").json()

    assert resp.status_code == 200
    stored = db.collection(col.PESTS).get(key)
    assert stored["common_names_i18n"] == {"en": ["Spider Mites"]}
    assert stored.get("common_name_de") is None
    # The stale German name did not come back on the next read.
    assert reread["common_names_i18n"] == {"en": ["Spider Mites"]}
    assert reread["common_name_de"] is None


def test_a_put_of_the_german_field_alone_rewrites_the_maps_german_entry(db: StandardDatabase) -> None:
    key = _plant(db)

    resp = _client(db).put(f"/api/v1/ipm/pests/{key}", json={"common_name_de": "Gemeine Spinnmilbe"})

    assert resp.status_code == 200
    stored = db.collection(col.PESTS).get(key)
    assert stored["common_names_i18n"] == {"en": ["Spider Mites"], "de": ["Gemeine Spinnmilbe"]}
    assert stored["common_name_de"] == "Gemeine Spinnmilbe"


def test_a_row_from_before_the_map_is_read_with_its_german_entry(db: StandardDatabase) -> None:
    key = db.collection(col.PESTS).insert(
        {"scientific_name": "Tetranychus urticae", "common_name": "Spider Mites", "common_name_de": "Spinnmilben"}
    )["_key"]

    body = _client(db).get(f"/api/v1/ipm/pests/{key}").json()

    assert body["common_names_i18n"] == {"de": ["Spinnmilben"]}
