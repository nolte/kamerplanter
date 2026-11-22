"""#2936 — ``PUT /ipm/diseases/{key}`` replaces the stored names per language, measured on a real server.

ArangoDB merges object values on update by default (python-arango ``merge=True``), so a
``PUT`` that sends fewer languages - or ``{}`` to clear the map - wrote nothing the
stored map lost: the removed language survived. The mocked-repository API test cannot
see that; this test writes through the real ``ArangoIpmRepository``.
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
    pytest.mark.allow_db_connection("the update semantics of nested objects are the server's"),
]

_DB_NAME = run_database_name("ipm_disease_names_update")


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
    return db.collection(col.DISEASES).insert(
        {
            "scientific_name": "Erysiphe spp.",
            "common_name": "Powdery Mildew",
            "pathogen_type": "fungal",
            "common_names_i18n": {"en": ["Powdery Mildew"], "de": ["Echter Mehltau"]},
        }
    )["_key"]


def test_a_put_with_fewer_languages_removes_the_missing_one(db: StandardDatabase) -> None:
    key = _plant(db)

    resp = _client(db).put(f"/api/v1/ipm/diseases/{key}", json={"common_names_i18n": {"en": ["Powdery Mildew"]}})

    assert resp.status_code == 200
    assert db.collection(col.DISEASES).get(key)["common_names_i18n"] == {"en": ["Powdery Mildew"]}


def test_a_put_with_an_empty_map_clears_it(db: StandardDatabase) -> None:
    key = _plant(db)

    resp = _client(db).put(f"/api/v1/ipm/diseases/{key}", json={"common_names_i18n": {}})

    assert resp.status_code == 200
    assert db.collection(col.DISEASES).get(key)["common_names_i18n"] == {}


def test_a_put_without_the_field_keeps_the_map(db: StandardDatabase) -> None:
    key = _plant(db)

    resp = _client(db).put(f"/api/v1/ipm/diseases/{key}", json={"description": "white coating"})

    assert resp.status_code == 200
    stored = db.collection(col.DISEASES).get(key)
    assert stored["common_names_i18n"] == {"en": ["Powdery Mildew"], "de": ["Echter Mehltau"]}
    assert stored["description"] == "white coating"
