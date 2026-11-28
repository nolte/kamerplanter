"""#2888 F-20 - the soil-hazard writes of a bed against ArangoDB.

What only the database can show: the bed is resolved through its site's tenant **inside** the transaction (a
``Location`` has no ``tenant_key``), an unchanged list writes nothing, the stored entries load back into the model,
and a concurrent write to the same bed conflicts instead of one of the two lists being lost. The lead's removal and its
``garden_plan_audit`` row commit together (#2888 O6), and the parent chain is read through the real site repository
(O3/O5). The service end to end
with the real repositories - the offer after a loss and its acceptance - closes the file. The decisions are pinned
in ``tests/unit/domain/engines/test_bed_soil_hazard_engine.py`` and ``tests/api/test_bed_soil_hazards_api.py``.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest
from arango import ArangoClient

from app.api.v1.locations.schemas import LocationCreate
from app.common.enums import PathogenConfirmationSource, SoilHazard
from app.common.exceptions import NotFoundError, PlanError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.bed_soil_hazard_repository import ArangoBedSoilHazardRepository
from app.data_access.arango.location_type_repository import ArangoLocationTypeRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.transactions import stream_transaction
from app.data_access.knowledge.soil_hazard_knowledge_source import YamlSoilHazardKnowledgeSource
from app.domain.models.bed_soil_hazard import BedSoilHazard
from app.domain.models.site import Location
from app.domain.services.bed_soil_hazard_service import BedSoilHazardService
from app.domain.services.site_service import SiteService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("bed_soil_hazard_repository")
A, B = "ten_a", "ten_b"

CLUBROOT = BedSoilHazard(
    hazard=SoilHazard.CLUBROOT, confirmed_at=date(2025, 6, 1), source=PathogenConfirmationSource.LAB_TEST
)
WHITE_ROT = BedSoilHazard(
    hazard=SoilHazard.WHITE_ROT, confirmed_at=date(2026, 7, 1), source=PathogenConfirmationSource.ADVISORY_SERVICE
)


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


def _bed(key: str, site: str, **extra: Any) -> dict[str, Any]:
    return {"_key": key, "name": key, "site_key": site, "location_type_key": "bed", "area_m2": 2.0, **extra}


@pytest.fixture
def db(database):
    for name in (col.SITES, col.LOCATIONS, col.LOCATION_TYPES, col.PLANT_INSTANCES, col.GARDEN_PLAN_AUDIT):
        database.collection(name).truncate()
    database.collection(col.LOCATION_TYPES).insert({"_key": "bed", "name": "Bed", "is_bed": True})
    for site, tenant in (("site_a", A), ("site_b", B)):
        database.collection(col.SITES).insert(
            {"_key": site, "tenant_key": tenant, "name": site, "type": "outdoor", "plan": {"plan_revision": 4}}
        )
    database.collection(col.LOCATIONS).insert(_bed("bed_a", "site_a"))
    database.collection(col.LOCATIONS).insert(_bed("bed_b", "site_b", soil_hazards=[CLUBROOT.model_dump(mode="json")]))
    return database


def _stored(db, key: str) -> dict[str, Any]:
    return db.collection(col.LOCATIONS).get(key)


def _add(entry: BedSoilHazard):
    return lambda stored: (*stored, entry)


class TestTheWrite:
    def test_it_writes_the_list_and_the_location_loads_it_back(self, db) -> None:
        repo = ArangoBedSoilHazardRepository(db)

        written = repo.change_soil_hazards("bed_a", tenant_key=A, change=_add(WHITE_ROT))

        assert written.status == "written" and written.entries == (WHITE_ROT,)
        assert _stored(db, "bed_a")["soil_hazards"] == [
            {"hazard": "white_rot", "confirmed_at": "2026-07-01", "source": "advisory_service"}
        ]
        location = ArangoSiteRepository(db).get_location_by_key("bed_a")
        assert location is not None and location.soil_hazards == [WHITE_ROT]

    def test_an_unchanged_list_writes_nothing(self, db) -> None:
        before = _stored(db, "bed_b")["_rev"]

        written = ArangoBedSoilHazardRepository(db).change_soil_hazards("bed_b", tenant_key=B, change=lambda s: s)

        assert written.status == "unchanged" and written.entries == (CLUBROOT,)
        assert _stored(db, "bed_b")["_rev"] == before

    @pytest.mark.parametrize("key", ["bed_b", "bed_gone"], ids=["foreign", "absent"])
    def test_a_foreign_and_an_absent_bed_are_the_same_answer_and_nothing_is_written(self, db, key: str) -> None:
        before = _stored(db, "bed_b")

        written = ArangoBedSoilHazardRepository(db).change_soil_hazards(key, tenant_key=A, change=_add(WHITE_ROT))

        assert written.status == "location_not_found"
        assert _stored(db, "bed_b") == before

    def test_an_empty_tenant_is_no_tenant(self, db) -> None:
        with pytest.raises(ValueError, match="tenant_key"):
            ArangoBedSoilHazardRepository(db).change_soil_hazards("bed_a", tenant_key="", change=_add(WHITE_ROT))

    def test_a_concurrent_write_to_the_same_bed_conflicts_instead_of_being_lost(self, db) -> None:
        """The other request commits between this write's read and its write: this one must not overwrite it."""
        repo = ArangoBedSoilHazardRepository(db)

        def change_while_another_request_commits(stored):
            with stream_transaction(db, write=(col.LOCATIONS,), entity="location") as other:
                other.collection(col.LOCATIONS).update(
                    {"_key": "bed_a", "soil_hazards": [CLUBROOT.model_dump(mode="json")]}
                )
            return (*stored, WHITE_ROT)

        with pytest.raises(WriteConflictError):
            repo.change_soil_hazards("bed_a", tenant_key=A, change=change_while_another_request_commits)

        assert _stored(db, "bed_a")["soil_hazards"] == [CLUBROOT.model_dump(mode="json")]


class TestTheServiceOverTheRealRepositories:
    def _service(self, db) -> BedSoilHazardService:
        return BedSoilHazardService(
            ArangoSiteRepository(db),
            ArangoLocationTypeRepository(db),
            ArangoPlantInstanceRepository(db),
            ArangoBedSoilHazardRepository(db),
            YamlSoilHazardKnowledgeSource(),
        )

    def _loss(self, db, key: str, tenant: str, bed: str, *, confirmed: bool) -> None:
        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": key,
                "tenant_key": tenant,
                "instance_id": key.upper(),
                "species_key": "sp_kohl",
                "location_key": bed,
                "planted_on": "2026-04-01",
                "removed_on": "2026-07-01",
                "termination_type": "died",
                "termination_cause": "disease",
                "failure_cause_class": "disease_soil",
                "failure_pathogen": "clubroot",
                "failure_pathogen_confirmed": confirmed,
                "failure_pathogen_source": "lab_test" if confirmed else None,
            }
        )

    def test_the_offer_is_made_and_its_acceptance_records_the_loss(self, db) -> None:
        self._loss(db, "kohl_a", A, "bed_a", confirmed=True)
        service = self._service(db)
        plant = ArangoPlantInstanceRepository(db).get_by_key("kohl_a")
        assert plant is not None

        offer = service.follow_up_for_loss(plant, tenant_key=A)
        assert (
            offer is not None
            and offer.hazard is SoilHazard.CLUBROOT
            and _stored(db, "bed_a").get("soil_hazards") is None
        )

        outcome = service.take_over_loss("bed_a", tenant_key=A, plant_key="kohl_a")
        assert outcome.changed is True
        (entry,) = outcome.entries

        assert (entry.hazard, entry.confirmed_at, entry.hosts[0].name) == (
            SoilHazard.CLUBROOT,
            date(2026, 7, 1),
            "Brassicaceae",
        )
        assert _stored(db, "bed_a")["soil_hazards"] == [
            {"hazard": "clubroot", "confirmed_at": "2026-07-01", "source": "lab_test"}
        ]

    def test_another_tenants_bed_is_neither_read_nor_written(self, db) -> None:
        before = _stored(db, "bed_b")
        service = self._service(db)

        with pytest.raises(NotFoundError):
            service.record(
                "bed_b",
                tenant_key=A,
                hazard=SoilHazard.WHITE_ROT,
                confirmed_at=date(2026, 7, 1),
                source=PathogenConfirmationSource.LAB_TEST,
            )
        with pytest.raises(NotFoundError):
            service.remove("bed_b", SoilHazard.CLUBROOT, tenant_key=A, user_key="u_a")

        assert _stored(db, "bed_b") == before
        assert db.collection(col.GARDEN_PLAN_AUDIT).count() == 0

    def test_juglone_at_an_area_and_hydroponics_from_the_room_through_the_real_site_reads(self, db) -> None:
        """O3/O5: the parent chain is read with ``ArangoSiteRepository.get_location_by_key``, within the site."""
        locations = db.collection(col.LOCATIONS)
        locations.insert({**_bed("garden_a", "site_a"), "location_type_key": "garden"})
        locations.insert({**_bed("room_a", "site_a"), "location_type_key": "greenhouse", "irrigation_system": "hydro"})
        locations.insert({**_bed("bed_in_room", "site_a"), "parent_location_key": "room_a"})
        # Review S1 (REQ-053 v1.61): a location without a bed type ("zone" is no seeded bed type here) under the
        # hydroponic room is refused; a soil bed (type "bed", own irrigation ``manual``) under it takes an entry.
        locations.insert(
            {**_bed("zone_in_room", "site_a"), "location_type_key": "zone", "parent_location_key": "room_a"}
        )
        # A corrupt parent key into another tenant's site: the chain ends there instead of reading it.
        locations.insert({**_bed("bed_foreign_parent", "site_a"), "parent_location_key": "room_b"})
        locations.insert({**_bed("room_b", "site_b"), "location_type_key": "greenhouse", "irrigation_system": "nft"})
        service = self._service(db)

        recorded = service.record(
            "garden_a",
            tenant_key=A,
            hazard=SoilHazard.JUGLONE,
            confirmed_at=date(2019, 3, 1),
            source=PathogenConfirmationSource.CLEAR_SYMPTOMS,
        )
        assert recorded.changed is True
        with pytest.raises(PlanError) as refused:
            service.record(
                "zone_in_room",
                tenant_key=A,
                hazard=SoilHazard.JUGLONE,
                confirmed_at=date(2019, 3, 1),
                source=PathogenConfirmationSource.CLEAR_SYMPTOMS,
            )
        assert refused.value.error_code == "soil_hazard.hydroponic"
        assert service.record(
            "bed_in_room",
            tenant_key=A,
            hazard=SoilHazard.CLUBROOT,
            confirmed_at=date(2026, 7, 1),
            source=PathogenConfirmationSource.LAB_TEST,
        ).changed
        assert service.record(
            "bed_foreign_parent",
            tenant_key=A,
            hazard=SoilHazard.CLUBROOT,
            confirmed_at=date(2026, 7, 1),
            source=PathogenConfirmationSource.LAB_TEST,
        ).changed


class TestTheRemovalAndItsAuditRow:
    """#2888 O6: the entry goes and its ``garden_plan_audit`` row is written in one transaction."""

    def test_the_removal_writes_the_row_with_bed_hazard_confirmation_and_the_lead(self, db) -> None:
        at = datetime(2026, 11, 28, 9, 30, tzinfo=UTC)

        removal = ArangoBedSoilHazardRepository(db).remove_soil_hazard(
            "bed_b", SoilHazard.CLUBROOT, tenant_key=B, user_key="u_lead", at=at
        )

        assert removal.status == "removed" and removal.removed == CLUBROOT
        assert _stored(db, "bed_b")["soil_hazards"] == []
        (row,) = list(db.collection(col.GARDEN_PLAN_AUDIT).all())
        assert {k: row[k] for k in ("tenant_key", "site_key", "revision", "user_key", "op", "entity", "key")} == {
            "tenant_key": B,
            "site_key": "site_b",
            "revision": 4,
            "user_key": "u_lead",
            "op": "delete",
            "entity": "soil_hazard",
            "key": "bed_b",
        }
        assert row["summary"] == "clubroot confirmed 2025-06-01"
        assert datetime.fromisoformat(row["at"]) == at

    def test_the_row_is_listed_in_the_plan_change_log(self, db) -> None:
        from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository

        ArangoBedSoilHazardRepository(db).remove_soil_hazard(
            "bed_b", SoilHazard.CLUBROOT, tenant_key=B, user_key="u_lead", at=datetime.now(UTC)
        )

        (entry,) = ArangoGardenPlanRepository(db).list_audit("site_b", tenant_key=B, offset=0, limit=10)
        assert (entry.op, entry.entity, entry.key, entry.summary) == (
            "delete",
            "soil_hazard",
            "bed_b",
            "clubroot confirmed 2025-06-01",
        )

    @pytest.mark.parametrize(
        ("key", "tenant", "hazard", "status"),
        [
            ("bed_b", B, SoilHazard.WHITE_ROT, "not_held"),
            ("bed_b", A, SoilHazard.CLUBROOT, "location_not_found"),
            ("bed_gone", B, SoilHazard.CLUBROOT, "location_not_found"),
        ],
        ids=["not_held", "foreign", "absent"],
    )
    def test_a_removal_that_removes_nothing_writes_no_row(self, db, key, tenant, hazard, status) -> None:
        before = _stored(db, "bed_b")

        removal = ArangoBedSoilHazardRepository(db).remove_soil_hazard(
            key, hazard, tenant_key=tenant, user_key="u_lead", at=datetime.now(UTC)
        )

        assert removal.status == status
        assert _stored(db, "bed_b") == before and db.collection(col.GARDEN_PLAN_AUDIT).count() == 0


class TestAnEditKeepsThem:
    def test_put_location_rebuilds_the_bed_from_a_body_without_them_and_keeps_them(self, db) -> None:
        """``PUT /locations/{key}`` builds a new ``Location`` from ``LocationCreate`` (no ``soil_hazards``) - #2623."""
        body = LocationCreate(name="Kohlbeet neu", site_key="site_b", location_type_key="bed", area_m2=3.0)

        updated = SiteService(ArangoSiteRepository(db)).update_location(
            "bed_b", Location(**body.model_dump()), tenant_key=B
        )

        assert updated.name == "Kohlbeet neu" and updated.soil_hazards == [CLUBROOT]
        assert _stored(db, "bed_b")["soil_hazards"] == [CLUBROOT.model_dump(mode="json")]
