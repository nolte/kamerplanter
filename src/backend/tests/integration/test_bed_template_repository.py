"""REQ-053 WP 7.8 (#2474) - the bed-template store and migration v0101 against a real ArangoDB (production schema).

What no double can decide, measured here:

* a read admits the system rows (``tenant_key`` absent) and the tenant's own - nothing of another tenant;
* a write names the row's owner: a tenant's key never reaches a system row and ``None`` never reaches a tenant's,
  and a row that is not the owner's raises ``NotFoundError`` instead of writing;
* ``keepNull: false`` removes a cleared value instead of storing ``null``, and a nested object is replaced whole;
* the bootstrap builds the ``(tenant_key, name)`` index; migration v0101 builds the same on an older volume,
  inserts the system templates under their fixed keys, never overwrites an edited one, and a second run changes
  nothing; every system template is a valid ``BedTemplate`` that can be placed.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.bed_template_repository import ArangoBedTemplateRepository
from app.domain.calculators.template_placement_calculator import place_geometry
from app.domain.models.bed_template import BedTemplate
from app.domain.models.site import Location
from app.migrations.support.legacy_indexes import indexes_on
from app.migrations.versions.v0101_bed_template_index_and_system_templates import (
    SYSTEM_TEMPLATES,
    TEMPLATE_INDEX_FIELDS,
    migration,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the repository's AQL and the migration's writes run against a real server"),
]

TEST_DATABASE = run_database_name("bed_template_repository")
A, B = "ten_a", "ten_b"
_RECT = {"kind": "rect", "origin": [0, 0], "width_m": 2, "length_m": 1, "rotation_deg": 0}


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    for name in (col.BED_TEMPLATES, col.LOCATION_TYPES, col.TASK_TEMPLATES):
        database.collection(name).truncate()
    database.collection(col.LOCATION_TYPES).insert_many(
        [{"_key": "bed", "name": "Bed", "is_bed": True}, {"_key": "greenhouse", "name": "House", "is_bed": False}]
    )
    return database


def _template(name: str, tenant: str | None, **extra: Any) -> BedTemplate:
    return BedTemplate(name=name, tenant_key=tenant, location_type_key="bed", default_geometry=_RECT, **extra)


@pytest.fixture
def repo(db) -> ArangoBedTemplateRepository:
    return ArangoBedTemplateRepository(db)


class TestReads:
    def test_a_tenant_reads_the_system_rows_and_its_own_never_another_tenants(self, repo) -> None:
        sys_row = repo.create_template(_template("System", None))
        own = repo.create_template(_template("Own", A, created_by="u_x"))
        theirs = repo.create_template(_template("Theirs", B))

        listed = repo.list_visible(tenant_key=A, offset=0, limit=50)

        assert sorted(t.key or "" for t in listed) == sorted([sys_row.key or "", own.key or ""])
        assert repo.get_visible_by_key(theirs.key or "", tenant_key=A) is None
        assert repo.get_visible_by_key(sys_row.key or "", tenant_key=A) is not None
        assert repo.visible_keys([sys_row.key or "", own.key or "", theirs.key or "", "nope"], tenant_key=A) == {
            sys_row.key,
            own.key,
        }

    def test_the_system_row_is_stored_without_a_tenant_key(self, repo, db) -> None:
        created = repo.create_template(_template("System", None))

        assert "tenant_key" not in db.collection(col.BED_TEMPLATES).get(created.key or "")
        assert created.is_system

    def test_the_list_is_sorted_by_name_and_windowed(self, repo) -> None:
        for name in ("c", "a", "b"):
            repo.create_template(_template(name, A))

        assert [t.name for t in repo.list_visible(tenant_key=A, offset=1, limit=1)] == ["b"]

    def test_an_empty_tenant_is_refused_not_read_across_tenants(self, repo) -> None:
        with pytest.raises(ValueError, match="tenant_key"):
            repo.list_visible(tenant_key="", offset=0, limit=10)

    def test_the_count_is_the_tenants_own_only(self, repo) -> None:
        repo.create_template(_template("System", None))
        repo.create_template(_template("Own", A))
        repo.create_template(_template("Theirs", B))

        assert (repo.count_owned(tenant_key=A), repo.count_owned(tenant_key=B)) == (1, 1)

    def test_task_template_keys_resolve_to_the_tenants_and_the_global_ones(self, repo, db) -> None:
        db.collection(col.TASK_TEMPLATES).insert_many(
            [
                {"_key": "tt_global", "tenant_key": "", "name": "g"},
                {"_key": "tt_a", "tenant_key": A, "name": "a"},
                {"_key": "tt_b", "tenant_key": B, "name": "b"},
            ]
        )

        assert repo.visible_task_template_keys(["tt_global", "tt_a", "tt_b", "nope"], tenant_key=A) == {
            "tt_global",
            "tt_a",
        }

    def test_the_bed_type_flags_name_only_the_types_that_exist(self, repo) -> None:
        assert repo.bed_type_flags(["bed", "greenhouse", "nope"]) == {"bed": True, "greenhouse": False}


class TestWrites:
    def test_an_update_names_the_owner_and_cannot_reach_the_other_kind_of_row(self, repo) -> None:
        sys_row = repo.create_template(_template("System", None))
        own = repo.create_template(_template("Own", A))

        with pytest.raises(NotFoundError):
            repo.update_template(sys_row.key or "", {"name": "taken"}, owner_tenant_key=A)
        with pytest.raises(NotFoundError):
            repo.update_template(own.key or "", {"name": "taken"}, owner_tenant_key=None)
        with pytest.raises(NotFoundError):
            repo.update_template(own.key or "", {"name": "taken"}, owner_tenant_key=B)

        assert repo.update_template(own.key or "", {"name": "Renamed"}, owner_tenant_key=A).name == "Renamed"
        assert repo.update_template(sys_row.key or "", {"name": "Curated"}, owner_tenant_key=None).name == "Curated"

    def test_a_cleared_value_is_removed_and_a_nested_object_is_replaced_whole(self, repo, db) -> None:
        own = repo.create_template(
            _template("Own", A, height_m=0.4, default_layout={"row_spacing_cm": 25, "spacing_cm": 20})
        )

        repo.update_template(
            own.key or "", {"height_m": None, "default_layout": {"spacing_cm": 30}}, owner_tenant_key=A
        )

        stored = db.collection(col.BED_TEMPLATES).get(own.key or "")
        assert "height_m" not in stored
        assert stored["default_layout"] == {"spacing_cm": 30}
        assert stored["updated_at"]

    def test_a_delete_names_the_owner_too(self, repo) -> None:
        sys_row = repo.create_template(_template("System", None))
        own = repo.create_template(_template("Own", A))

        assert repo.delete_template(sys_row.key or "", owner_tenant_key=A) is False
        assert repo.delete_template(own.key or "", owner_tenant_key=None) is False
        assert repo.delete_template(own.key or "", owner_tenant_key=B) is False
        assert repo.delete_template(own.key or "", owner_tenant_key=A) is True
        assert repo.delete_template(sys_row.key or "", owner_tenant_key=None) is True


def _index_fields(db) -> list[list[str]]:
    return [row["fields"] for row in db.collection(col.BED_TEMPLATES).indexes()]


class TestMigrationV0101:
    def test_the_bootstrap_builds_the_index_with_the_tenant_first(self, db) -> None:
        assert list(TEMPLATE_INDEX_FIELDS) == col.BED_TEMPLATE_TENANT_INDEX_FIELDS
        assert col.BED_TEMPLATE_TENANT_INDEX_FIELDS[0] == "tenant_key"
        assert indexes_on(db.collection(col.BED_TEMPLATES), TEMPLATE_INDEX_FIELDS)

    def test_it_inserts_the_system_templates_under_fixed_keys_and_is_idempotent(self, db) -> None:
        first = migration.up(db)
        second = migration.up(db)

        assert first.changed == len(SYSTEM_TEMPLATES) and second.changed == 0
        keys = {doc["_key"] for doc in db.collection(col.BED_TEMPLATES).all()}
        assert keys == {key for key, *_ in SYSTEM_TEMPLATES}
        assert all("tenant_key" not in doc for doc in db.collection(col.BED_TEMPLATES).all())

    def test_it_never_overwrites_a_template_an_operator_edited(self, db) -> None:
        migration.up(db)
        db.collection(col.BED_TEMPLATES).update({"_key": "sys_bed_2x1", "name": "Edited by the operator"})

        report = migration.up(db)

        assert report.changed == 0
        assert db.collection(col.BED_TEMPLATES).get("sys_bed_2x1")["name"] == "Edited by the operator"

    def test_it_creates_the_index_on_a_volume_that_predates_it(self, db) -> None:
        collection = db.collection(col.BED_TEMPLATES)
        for index in indexes_on(collection, TEMPLATE_INDEX_FIELDS):
            collection.delete_index(index["id"])
        assert not indexes_on(collection, TEMPLATE_INDEX_FIELDS)

        report = migration.up(db)

        assert report.details["index_created"] is True
        assert indexes_on(collection, TEMPLATE_INDEX_FIELDS)

    def test_a_dry_run_writes_nothing(self, db) -> None:
        report = migration.up(db, dry_run=True)

        assert report.dry_run and report.changed == 0
        assert report.details["will_create"] == [key for key, *_ in SYSTEM_TEMPLATES]
        assert db.collection(col.BED_TEMPLATES).count() == 0

    def test_every_system_template_is_valid_and_can_be_placed(self, db) -> None:
        migration.up(db)
        templates = [BedTemplate(**doc) for doc in db.collection(col.BED_TEMPLATES).all()]

        assert len(templates) == len(SYSTEM_TEMPLATES) and all(t.is_system for t in templates)
        for template in templates:
            Location(
                name=template.name,
                location_type_key=template.location_type_key,
                area_m2=0.0,
                geometry=place_geometry(template.default_geometry, origin=(5, 5), rotation_deg=0),
                height_m=template.height_m,
            )

    def test_the_two_raised_bed_standards_are_both_shipped_and_nothing_agronomic_is_invented(self, db) -> None:
        migration.up(db)
        by_key = {doc["_key"]: BedTemplate(**doc) for doc in db.collection(col.BED_TEMPLATES).all()}

        large = by_key["sys_raised_bed_1_2x2_4"].default_geometry.model_dump()
        small = by_key["sys_raised_bed_2x1x0_8"]
        assert (large["width_m"], large["length_m"]) == (1.2, 2.4)
        assert small.default_geometry.model_dump()["width_m"] == 2.0 and small.height_m == 0.8
        layouts = [(t.default_layout.row_spacing_cm, t.default_layout.spacing_cm) for t in by_key.values()]
        assert set(layouts) == {(None, None)}
        assert all(t.soil_profile_defaults is None and t.recurring_task_templates == [] for t in by_key.values())
