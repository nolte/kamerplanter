"""REQ-053 WP 10.11 (#2832, W-016) - the tent rules against a real ArangoDB.

What no double decides, measured here:

* the photoperiod read: a legacy growth phase reaches its requirement profile directly, a phase-sequence entry through
  the growth phase of the same name in the species' lifecycle; a phase without a profile is unknown; a plant placed
  only through a slot counts; another tenant's, a removed and another location's plant do not;
* the photoperiod read is anchored at the location's slots, carries each plant's phase code and name, and leaves an
  ambiguous or missing name bridge unknown while a legacy phase id still wins;
* the summary's hint appears with two photoperiods and disappears once they agree; a young plant takes no part, and
  a shelf level counts only with its own lamp;
* ``layout_type_flags`` reads ``supports_layout`` and lets ``is_bed`` imply it;
* a location's own ``adjacency_factor`` decides the derived neighbourhood of its slots;
* ``lighting`` is stored replaced whole, without the ``null`` keys of the PATCH, and ``null`` removes it.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.enums import TenantRole
from app.data_access.arango import collections as col
from app.data_access.arango.garden_object_repository import ArangoGardenObjectRepository
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.graph_repository import ArangoGraphRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.garden_plan import LocationPatch
from app.domain.models.tent_hint import HINT_PHOTOPERIOD_CONFLICT, PhaseLabel
from app.domain.services.adjacency_service import AdjacencyService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("location_tent_rules")
A, B = "ten_a", "ten_b"

_DOCUMENTS = (
    col.SITES,
    col.LOCATIONS,
    col.SLOTS,
    col.LOCATION_TYPES,
    col.PLANT_INSTANCES,
    col.PLANTING_RUNS,
    col.SPECIES,
    col.LIFECYCLE_CONFIGS,
    col.GROWTH_PHASES,
    col.REQUIREMENT_PROFILES,
    col.PHASE_SEQUENCE_ENTRIES,
    col.PHASE_DEFINITIONS,
    col.TASKS,
    col.CARE_EVENTS,
    col.WATERING_EVENTS,
)
_EDGES = (
    col.HAS_LIFECYCLE,
    col.CONSISTS_OF,
    col.REQUIRES_PROFILE,
    col.ADJACENT_TO,
    col.RUN_PLANNED_AT,
    col.TENANT_HAS_ACCESS,
)
_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _DOCUMENTS:
        db.create_collection(name)
    for name in _EDGES:
        db.create_collection(name, edge=True)
    yield db
    system.delete_database(TEST_DATABASE)
    client.close()


def _location(key: str, site: str, type_key: str, **fields) -> dict:
    return {
        "_key": key,
        "site_key": site,
        "name": key,
        "location_type_key": type_key,
        "area_m2": 1.44,
        "depth": 0,
        "path": key,
        "geometry": {"kind": "rect", "origin": [1, 1], "width_m": 1.2, "length_m": 1.2, "rotation_deg": 0},
        **fields,
    }


def _phase(db, key: str, name: str, lifecycle: str, *, hours: float | None) -> None:
    db.collection(col.GROWTH_PHASES).insert(
        {"_key": key, "name": name, "display_name": name.title(), "lifecycle_key": lifecycle}
    )
    db.collection(col.CONSISTS_OF).insert(
        {"_from": f"{col.LIFECYCLE_CONFIGS}/{lifecycle}", "_to": f"{col.GROWTH_PHASES}/{key}"}
    )
    if hours is not None:
        db.collection(col.REQUIREMENT_PROFILES).insert(
            {"_key": f"rp_{key}", "phase_key": key, "photoperiod_hours": hours}
        )
        db.collection(col.REQUIRES_PROFILE).insert(
            {"_from": f"{col.GROWTH_PHASES}/{key}", "_to": f"{col.REQUIREMENT_PROFILES}/rp_{key}"}
        )


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    for key, supports, is_bed in (("tent", True, False), ("bed", None, True), ("room", False, False)):
        doc = {"_key": key, "name": key, "is_bed": is_bed}
        if supports is not None:
            doc["supports_layout"] = supports
        database.collection(col.LOCATION_TYPES).insert(doc)
    for key, tenant in (("site_a", A), ("site_b", B)):
        database.collection(col.SITES).insert(
            {
                "_key": key,
                "tenant_key": tenant,
                "name": key,
                "type": "indoor",
                "total_area_m2": 0.0,
                "timezone": "UTC",
                "plan": {"boundary": _BOUNDARY, "plan_revision": 1, "north_angle_deg": 0.0},
            }
        )
    database.collection(col.LOCATIONS).insert(_location("tent", "site_a", "tent"))
    database.collection(col.LOCATIONS).insert(_location("tent_2", "site_a", "tent"))
    # Cannabis: a legacy lifecycle - vegetative (18 h), flowering (12 h) and a seedling without a profile.
    database.collection(col.SPECIES).insert({"_key": "sp_cannabis", "scientific_name": "Cannabis sativa"})
    database.collection(col.LIFECYCLE_CONFIGS).insert({"_key": "lc_cannabis", "species_key": "sp_cannabis"})
    database.collection(col.HAS_LIFECYCLE).insert(
        {"_from": f"{col.SPECIES}/sp_cannabis", "_to": f"{col.LIFECYCLE_CONFIGS}/lc_cannabis"}
    )
    _phase(database, "gp_veg", "vegetative", "lc_cannabis", hours=18.0)
    _phase(database, "gp_flower", "flowering", "lc_cannabis", hours=12.0)
    _phase(database, "gp_seedling", "seedling", "lc_cannabis", hours=None)
    # A phase-sequence entry "flowering" of a sequence-driven plant of the same species.
    database.collection(col.PHASE_DEFINITIONS).insert({"_key": "pd_flowering", "name": "flowering"})
    database.collection(col.PHASE_SEQUENCE_ENTRIES).insert(
        {"_key": "pse_flowering", "phase_definition_key": "pd_flowering", "sequence_order": 3}
    )
    return database


def _plant(db, key: str, *, phase: str | None, tenant: str = A, location: str | None = "tent", **fields) -> None:
    db.collection(col.PLANT_INSTANCES).insert(
        {
            "_key": key,
            "tenant_key": tenant,
            "instance_id": key.upper(),
            "species_key": "sp_cannabis",
            "location_key": location,
            "current_phase_key": phase,
            "removed_on": None,
            **fields,
        }
    )


@pytest.fixture
def repo(db) -> ArangoGardenPlanRepository:
    return ArangoGardenPlanRepository(db)


@pytest.fixture
def service(db, repo) -> GardenResourceService:
    sites = ArangoSiteRepository(db)
    return GardenResourceService(sites, repo, ArangoGardenObjectRepository(db), GardenPlanService(sites, repo))


class TestPhotoperiodRead:
    def test_both_phase_key_spaces_reach_the_profile_and_a_missing_one_is_unknown(self, db, repo) -> None:
        _plant(db, "p_legacy", phase="gp_veg")
        _plant(db, "p_sequence", phase="pse_flowering")
        _plant(db, "p_seedling", phase="gp_seedling")
        _plant(db, "p_nophase", phase=None)

        rows = {row.plant_key: row for row in repo.load_location_photoperiods("tent", tenant_key=A)}

        assert {key: row.photoperiod_hours for key, row in rows.items()} == {
            "p_legacy": 18.0,
            "p_sequence": 12.0,
            "p_seedling": None,
            "p_nophase": None,
        }
        assert rows["p_legacy"].phase_name == "Vegetative"

    def test_a_plant_placed_through_a_slot_counts(self, db, repo) -> None:
        db.collection(col.SLOTS).insert({"_key": "s1", "slot_id": "TENT_1", "location_key": "tent"})
        _plant(db, "p_slot", phase="gp_flower", location=None, slot_key="s1")

        assert [row.plant_key for row in repo.load_location_photoperiods("tent", tenant_key=A)] == ["p_slot"]

    def test_foreign_removed_and_elsewhere_plants_are_not_read(self, db, repo) -> None:
        _plant(db, "p_own", phase="gp_veg")
        _plant(db, "p_foreign", phase="gp_flower", tenant=B)
        _plant(db, "p_removed", phase="gp_flower", removed_on="2026-10-01")
        _plant(db, "p_elsewhere", phase="gp_flower", location="tent_2")

        assert [row.plant_key for row in repo.load_location_photoperiods("tent", tenant_key=A)] == ["p_own"]

    def test_a_plant_in_a_slot_of_another_location_is_not_read(self, db, repo) -> None:
        db.collection(col.SLOTS).insert({"_key": "s_other", "slot_id": "TENT2_1", "location_key": "tent_2"})
        _plant(db, "p_other_slot", phase="gp_flower", location=None, slot_key="s_other")
        _plant(db, "p_here", phase="gp_veg")

        assert [row.plant_key for row in repo.load_location_photoperiods("tent", tenant_key=A)] == ["p_here"]

    def test_each_plant_carries_its_phase_code_and_its_name(self, db, repo) -> None:
        _plant(db, "p_named", phase="pse_flowering", plant_name="Gelato #3")
        _plant(db, "p_unnamed", phase="gp_seedling")

        rows = {row.plant_key: row for row in repo.load_location_photoperiods("tent", tenant_key=A)}

        assert (rows["p_named"].phase_code, rows["p_named"].display_name) == ("flowering", "Gelato #3")
        assert (rows["p_unnamed"].phase_code, rows["p_unnamed"].display_name) == ("seedling", "P_UNNAMED")

    def test_each_plant_carries_its_phase_with_both_display_names(self, db, repo) -> None:
        """#2889: a sequence entry carries its definition's English and German name, a legacy growth phase its own
        (English only - it has no German field); no phase, no label. Nothing is resolved by language here."""
        db.collection(col.PHASE_DEFINITIONS).update(
            {"_key": "pd_flowering", "display_name": "Flowering", "display_name_de": "Blüte"}
        )
        _plant(db, "p_sequence", phase="pse_flowering")
        _plant(db, "p_legacy", phase="gp_veg")
        _plant(db, "p_nophase", phase=None)

        rows = {row.plant_key: row for row in repo.load_location_photoperiods("tent", tenant_key=A)}

        assert rows["p_sequence"].phase_label == PhaseLabel("flowering", "Flowering", "Blüte")
        assert rows["p_legacy"].phase_label == PhaseLabel("vegetative", "Vegetative", "")
        assert rows["p_nophase"].phase_label is None

    def test_an_ambiguous_name_bridge_is_unknown_and_the_legacy_id_still_wins(self, db, repo) -> None:
        """Two growth phases named ``flowering`` in the species' lifecycles: the sequence plant is not guessed."""
        db.collection(col.LIFECYCLE_CONFIGS).insert({"_key": "lc_cannabis_auto", "species_key": "sp_cannabis"})
        db.collection(col.HAS_LIFECYCLE).insert(
            {"_from": f"{col.SPECIES}/sp_cannabis", "_to": f"{col.LIFECYCLE_CONFIGS}/lc_cannabis_auto"}
        )
        _phase(db, "gp_flower_auto", "flowering", "lc_cannabis_auto", hours=18.0)
        _plant(db, "p_sequence", phase="pse_flowering")
        _plant(db, "p_legacy", phase="gp_flower")

        rows = {row.plant_key: row for row in repo.load_location_photoperiods("tent", tenant_key=A)}

        assert rows["p_sequence"].photoperiod_hours is None
        assert rows["p_legacy"].photoperiod_hours == 12.0

    def test_a_sequence_phase_without_a_growth_phase_of_its_name_is_unknown(self, db, repo) -> None:
        db.collection(col.PHASE_DEFINITIONS).insert({"_key": "pd_ripening", "name": "ripening"})
        db.collection(col.PHASE_SEQUENCE_ENTRIES).insert(
            {"_key": "pse_ripening", "phase_definition_key": "pd_ripening", "sequence_order": 4}
        )
        _plant(db, "p_ripening", phase="pse_ripening")

        (row,) = repo.load_location_photoperiods("tent", tenant_key=A)

        assert (row.phase_code, row.photoperiod_hours) == ("ripening", None)

    def test_an_empty_tenant_is_refused(self, repo) -> None:
        with pytest.raises(ValueError):
            repo.load_location_photoperiods("tent", tenant_key="")


class TestSummaryHint:
    def test_the_conflict_appears_and_disappears(self, db, service) -> None:
        _plant(db, "p1", phase="gp_veg")
        _plant(db, "p2", phase="pse_flowering")

        view = service.get_summary("tent", tenant_key=A)

        assert [hint.code for hint in view.tent_hints] == [HINT_PHOTOPERIOD_CONFLICT]
        assert view.supports_layout is True

        db.collection(col.PLANT_INSTANCES).update({"_key": "p1", "current_phase_key": "gp_flower"})

        assert service.get_summary("tent", tenant_key=A).tent_hints == []

    def test_a_young_plant_takes_no_part(self, db, service) -> None:
        _plant(db, "p1", phase="gp_flower")
        _plant(db, "p2", phase="gp_veg")
        db.collection(col.GROWTH_PHASES).update({"_key": "gp_veg", "name": "seedling"})

        assert service.get_summary("tent", tenant_key=A).tent_hints == []

    def test_a_shelf_level_counts_only_with_its_own_lamp(self, db, service) -> None:
        db.collection(col.LOCATION_TYPES).insert({"_key": "shelf", "name": "shelf", "supports_layout": True})
        db.collection(col.LOCATIONS).insert(_location("shelf_lit", "site_a", "shelf", lighting={"lamp_height_cm": 40}))
        db.collection(col.LOCATIONS).insert(_location("shelf_dark", "site_a", "shelf"))
        for location in ("shelf_lit", "shelf_dark"):
            _plant(db, f"{location}_1", phase="gp_veg", location=location)
            _plant(db, f"{location}_2", phase="gp_flower", location=location)

        assert [h.code for h in service.get_summary("shelf_lit", tenant_key=A).tent_hints] == [
            HINT_PHOTOPERIOD_CONFLICT
        ]
        assert service.get_summary("shelf_dark", tenant_key=A).tent_hints == []


def test_layout_type_flags_read_supports_layout_and_beds(repo) -> None:
    assert repo.layout_type_flags(["tent", "bed", "room", "unknown"]) == {"tent": True, "bed": True, "room": False}
    assert repo.layout_type_flags([]) == {}


class TestLocationFactorDecidesTheNeighbourhood:
    """Two points 50 cm apart, no species: spacing 30 cm, so 1.5 (site) gives 45 cm and 2.0 gives 60 cm."""

    def _slots(self, db) -> None:
        for key, x in (("s1", 0.2), ("s2", 0.7)):
            db.collection(col.SLOTS).insert(
                {
                    "_key": key,
                    "slot_id": f"TENT_{key.upper()}",
                    "location_key": "tent",
                    "slot_role": "position",
                    "geometry": {"kind": "point", "origin": [x, 0.5]},
                    "archived_at": None,
                }
            )

    def test_the_patched_factor_links_slots_the_site_factor_keeps_apart(self, db, repo, service) -> None:
        self._slots(db)
        adjacency = AdjacencyService(ArangoSiteRepository(db), repo, ArangoGraphRepository(db))

        assert adjacency.recompute("tent", tenant_key=A).pairs == 0

        service.patch_location(
            "tent", tenant_key=A, user_key="u1", role=TenantRole.GROWER, patch=LocationPatch(adjacency_factor=2.0)
        )
        result = adjacency.recompute("tent", tenant_key=A)

        assert result.pairs == 1
        assert {(e["_from"], e["_to"]) for e in db.collection(col.ADJACENT_TO).all()} == {
            (f"{col.SLOTS}/s1", f"{col.SLOTS}/s2"),
            (f"{col.SLOTS}/s2", f"{col.SLOTS}/s1"),
        }


class TestLightingIsStoredWhole:
    def test_replaced_whole_without_null_keys_and_removed_by_null(self, db, service) -> None:
        patch = LocationPatch(lighting={"lamp_height_cm": 180, "canopy_distance_cm": 40})
        service.patch_location("tent", tenant_key=A, user_key="u1", role=TenantRole.GROWER, patch=patch)

        service.patch_location(
            "tent",
            tenant_key=A,
            user_key="u1",
            role=TenantRole.GROWER,
            patch=LocationPatch(lighting={"lamp_height_cm": 170}),
        )

        assert db.collection(col.LOCATIONS).get("tent")["lighting"] == {"lamp_height_cm": 170.0}

        service.patch_location(
            "tent", tenant_key=A, user_key="u1", role=TenantRole.GROWER, patch=LocationPatch(lighting=None)
        )

        assert "lighting" not in db.collection(col.LOCATIONS).get("tent")

    def test_a_foreign_tenant_cannot_write_it(self, db, service) -> None:
        from app.common.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            service.patch_location(
                "tent",
                tenant_key=B,
                user_key="u1",
                role=TenantRole.GROWER,
                patch=LocationPatch(lighting={"lamp_height_cm": 170}),
            )
        assert "lighting" not in db.collection(col.LOCATIONS).get("tent")
