"""REQ-053 WP 8.26 (#2669) - the CSV bed list import against a real ArangoDB.

What no double can decide, measured here: that a confirmed import writes its valid lines through the plan's batch
transaction - every bed a ``rect`` hanging from the site through ``contains``, its zone with the ``zone_covers`` edge,
one ``import_csv`` row in the change log and one revision step - that a dry run leaves the database byte-identical,
and that a site of another tenant answers 404 before the file is read.

Every "nothing happened" assertion is paired with the positive control in the same test.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from arango import ArangoClient

from app.common.enums import SoilTexture, TenantRole
from app.common.exceptions import NotFoundError, PlanRevisionConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.irrigation_zone_repository import ArangoIrrigationZoneRepository
from app.data_access.arango.location_type_repository import ArangoLocationTypeRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.services.bed_csv_import_service import BedCsvImportService
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("bed_csv_import")
A, B = "ten_a", "ten_b"
USER = "u_sabine"
_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 8, "rotation_deg": 0}
_FILE = (
    "﻿Name;Typ;Breite_m;Länge_m;Bodenart;Zone\r\n"
    "Beet Nord;Beet;2,5;1,2;Lehm;Tropfer\r\n"
    "Kaputt;Beet;zwei;1;;\r\n"
    "=Hochbeet;raised bed;1.5;0.8;;\r\n"
).encode()


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)  # the production schema: the batch transaction declares its collections
    yield db
    system.delete_database(TEST_DATABASE)


def _site(key: str, tenant: str, name: str) -> dict[str, Any]:
    return {
        "_key": key,
        "tenant_key": tenant,
        "name": name,
        "type": "outdoor",
        "total_area_m2": 0.0,
        "timezone": "UTC",
        "plan": {"boundary": _BOUNDARY, "plan_revision": 2},
    }


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.USERS).insert({"_key": USER, "display_name": "Sabine"})
    for key, name, name_en, is_bed in (
        ("bed", "Beet", "Bed", True),
        ("raised_bed", "Hochbeet", "Raised Bed", True),
        ("greenhouse", "Gewächshaus", "Greenhouse", False),
    ):
        database.collection(col.LOCATION_TYPES).insert(
            {"_key": key, "name": name, "name_en": name_en, "is_bed": is_bed, "supports_layout": is_bed}
        )
    database.collection(col.SITES).insert(_site("site_a", A, "Garten A"))
    database.collection(col.SITES).insert(_site("site_b", B, "Garten B"))
    database.collection(col.IRRIGATION_ZONES).insert(
        {"_key": "zone_a", "tenant_key": A, "site_key": "site_a", "name": "Tropfer"}
    )
    database.collection(col.IRRIGATION_ZONES).insert(
        {"_key": "zone_b", "tenant_key": B, "site_key": "site_b", "name": "Tropfer"}
    )
    return database


def _service(db) -> BedCsvImportService:
    sites, plans = ArangoSiteRepository(db), ArangoGardenPlanRepository(db)
    zones = ArangoIrrigationZoneRepository(db)
    return BedCsvImportService(
        sites, plans, GardenPlanService(sites, plans, zones), ArangoLocationTypeRepository(db), zones
    )


def _import(db, *, site: str = "site_a", tenant: str = A, dry_run: bool, expected_revision: int | None = None):
    return _service(db).import_beds(
        site,
        tenant_key=tenant,
        user_key=USER,
        role=TenantRole.LEAD,
        content=_FILE,
        dry_run=dry_run,
        expected_revision=expected_revision,
    )


def _state(db) -> str:
    names = (col.SITES, col.LOCATIONS, col.CONTAINS, col.ZONE_COVERS, col.GARDEN_PLAN_AUDIT, col.IRRIGATION_ZONES)
    return json.dumps(
        {name: sorted(db.collection(name).all(), key=lambda d: d["_key"]) for name in names}, sort_keys=True
    )


class TestTheDryRun:
    def test_it_writes_nothing(self, db) -> None:
        before = _state(db)

        report = _import(db, dry_run=True)

        assert _state(db) == before
        assert [row.name for row in report.rows] == ["Beet Nord", "Hochbeet"] and report.plan_revision == 2
        assert [(e.line, e.column, e.code) for e in report.errors] == [(3, "Breite_m", "csv.invalid_number")]


class TestTheConfirmation:
    def test_the_valid_lines_land_in_one_transaction_with_their_edges_and_one_audit_row(self, db) -> None:
        report = _import(db, dry_run=False, expected_revision=2)

        assert report.applied is True and report.plan_revision == 3
        keys = {row.name: row.location_key for row in report.rows}
        assert set(keys) == {"Beet Nord", "Hochbeet"}  # the faulty line 3 is skipped
        north = db.collection(col.LOCATIONS).get(keys["Beet Nord"])
        assert north["site_key"] == "site_a" and north["location_type_key"] == "bed"
        assert north["geometry"] == {"kind": "rect", "origin": [0.0, 6.8], "width_m": 2.5, "length_m": 1.2,
                                     "rotation_deg": 0.0}  # fmt: skip
        assert north["soil_profile"]["soil_texture"] == SoilTexture.LOAM
        assert north["irrigation_zone_key"] == "zone_a"
        raised = db.collection(col.LOCATIONS).get(keys["Hochbeet"])
        assert raised["name"] == "Hochbeet" and raised.get("soil_profile") is None  # E-10: nothing invented
        assert raised["geometry"]["origin"] == [3.0, 7.2]  # 2.5 m + 0.5 m gap, hanging from the top edge y = 8
        contains = {edge["_to"] for edge in db.collection(col.CONTAINS).all()}
        assert contains == {f"{col.LOCATIONS}/{key}" for key in keys.values()}
        covers = [(e["_from"], e["_to"]) for e in db.collection(col.ZONE_COVERS).all()]
        assert covers == [(f"{col.IRRIGATION_ZONES}/zone_a", f"{col.LOCATIONS}/{keys['Beet Nord']}")]
        audit = [(row["op"], row["revision"], row["tenant_key"]) for row in db.collection(col.GARDEN_PLAN_AUDIT).all()]
        assert audit == [("import_csv", 3, A)]
        assert db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == 3

    def test_a_plan_changed_since_the_dry_run_writes_nothing(self, db) -> None:
        before = _state(db)

        with pytest.raises(PlanRevisionConflictError):
            _import(db, dry_run=False, expected_revision=1)

        assert _state(db) == before
        assert _import(db, dry_run=False, expected_revision=2).applied is True  # the positive control


class TestTheTenant:
    def test_a_foreign_site_is_a_404_and_its_zone_is_never_resolved(self, db) -> None:
        before = _state(db)

        with pytest.raises(NotFoundError):
            _import(db, site="site_b", tenant=A, dry_run=False)

        assert _state(db) == before
        report = _import(db, site="site_b", tenant=B, dry_run=False)  # the owner, positive control
        assert report.applied is True and report.rows[0].irrigation_zone_key == "zone_b"
