"""REQ-053 WP 10.11 (#2832, W-016) - the tent rules a location carries, through the service.

* ``adjacency_factor``: a PATCH writes it (and ``null`` clears it), a changed factor re-derives the neighbourhood,
  and the adjacency recompute takes the location's factor over the site's.
* ``lighting``: written whole and cleared with ``null``; nothing reads it (prepared, inert by design).
* the light-schedule hint of the summary: only for a tent or shelf level, only with two or more plants, and it
  comes and goes with the photoperiods of the plants' phases.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.common.enums import PhotoperiodSource, SlotRole, TenantRole
from app.common.exceptions import NotFoundError
from app.domain.interfaces.graph_repository import AdjacencySync
from app.domain.models.garden_plan import BedCounters, LocationPatch
from app.domain.models.site import LocationLighting, Slot
from app.domain.models.tent_hint import HINT_PHOTOPERIOD_CONFLICT, HINT_PHOTOPERIOD_UNKNOWN, PlantPhotoperiod
from app.domain.services.adjacency_service import AdjacencyService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    USER,
    FakeObjects,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)


@pytest.fixture
def world():
    site = make_site()
    sites = FakeSites(site)
    repo = FakePlanRepo(sites)
    repo.locations["tent"] = make_location("tent", name="Zelt", geometry=rect(1, 1, 1.2, 1.2), location_type_key="tent")
    repo.locations["bed"] = make_location("bed", name="Beet", geometry=rect(4, 1, 2, 1))
    repo.dispatched = []
    service = GardenResourceService(
        sites, repo, FakeObjects(repo), GardenPlanService(sites, repo), dispatch_adjacency=repo.dispatched.append
    )
    return service, repo


def _patch(service: GardenResourceService, key: str, **fields):
    return service.patch_location(
        key, tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER, patch=LocationPatch(**fields)
    )


class TestAdjacencyFactorPatch:
    def test_a_patch_writes_the_factor_and_asks_for_the_recompute(self, world) -> None:
        service, repo = world

        stored, _ = _patch(service, "tent", adjacency_factor=2.5)

        assert stored.adjacency_factor == 2.5
        assert repo.field_updates[-1] == ("tent", {"adjacency_factor": 2.5})
        assert repo.dispatched == ["tent"]

    def test_null_clears_it_back_to_the_site_factor(self, world) -> None:
        service, repo = world
        repo.locations["tent"] = repo.locations["tent"].model_copy(update={"adjacency_factor": 2.5})

        stored, _ = _patch(service, "tent", adjacency_factor=None)

        assert stored.adjacency_factor is None
        assert repo.dispatched == ["tent"]

    def test_an_unchanged_factor_writes_nothing_and_recomputes_nothing(self, world) -> None:
        service, repo = world
        repo.locations["tent"] = repo.locations["tent"].model_copy(update={"adjacency_factor": 2.5})

        _patch(service, "tent", adjacency_factor=2.5)

        assert repo.field_updates == []
        assert repo.dispatched == []

    def test_another_field_does_not_recompute(self, world) -> None:
        service, repo = world

        _patch(service, "tent", notes="Neue Lampe")

        assert repo.dispatched == []

    @pytest.mark.parametrize("value", [0, -1, 10.01, float("inf"), float("nan")])
    def test_the_site_field_bounds_hold_for_the_location(self, value: float) -> None:
        with pytest.raises(ValidationError):
            LocationPatch(adjacency_factor=value)

    def test_the_upper_bound_itself_is_allowed(self) -> None:
        assert LocationPatch(adjacency_factor=10.0).adjacency_factor == 10.0

    def test_a_foreign_location_is_404_and_writes_nothing(self) -> None:
        site = make_site(tenant=OTHER_TENANT)
        sites = FakeSites(site)
        repo = FakePlanRepo(sites)
        repo.locations["tent"] = make_location("tent", location_type_key="tent")
        service = GardenResourceService(sites, repo, FakeObjects(repo), GardenPlanService(sites, repo))

        with pytest.raises(NotFoundError):
            _patch(service, "tent", adjacency_factor=2.0)
        assert repo.field_updates == []


class TestLightingPatch:
    def test_a_patch_writes_the_lighting_whole(self, world) -> None:
        service, repo = world
        repo.locations["tent"] = repo.locations["tent"].model_copy(
            update={"lighting": LocationLighting(lamp_height_cm=180, canopy_distance_cm=40)}
        )

        stored, _ = _patch(service, "tent", lighting={"lamp_height_cm": 170})

        assert stored.lighting is not None
        assert stored.lighting.lamp_height_cm == 170
        assert stored.lighting.canopy_distance_cm is None
        # Replaced whole: the dropped canopy distance is neither merged back nor stored as ``null``.
        assert repo.field_updates[-1] == ("tent", {"lighting": {"lamp_height_cm": 170.0}})
        assert repo.dispatched == []

    def test_null_clears_it(self, world) -> None:
        service, repo = world
        repo.locations["tent"] = repo.locations["tent"].model_copy(
            update={"lighting": LocationLighting(lamp_height_cm=180)}
        )

        stored, _ = _patch(service, "tent", lighting=None)

        assert stored.lighting is None

    @pytest.mark.parametrize(
        "lighting",
        [
            {"lamp_height_cm": 0},
            {"lamp_height_cm": 1000.5},
            {"canopy_distance_cm": -1},
            {"lamp_height_cm": 50, "canopy_distance_cm": 60},
            {"lamp_height_cm": 50, "colour": "red"},
            {"fixture_geometry": {"kind": "point", "origin": [0.1, 0.1]}},
        ],
    )
    def test_physically_impossible_lighting_is_refused(self, lighting: dict) -> None:
        with pytest.raises(ValidationError):
            LocationPatch(lighting=lighting)

    def test_an_empty_object_is_stored_as_nothing(self, world) -> None:
        service, repo = world
        repo.locations["tent"] = repo.locations["tent"].model_copy(
            update={"lighting": LocationLighting(lamp_height_cm=180)}
        )

        stored, _ = _patch(service, "tent", lighting={})

        assert stored.lighting is None


class _Graph:
    def __init__(self) -> None:
        self.pairs: list[tuple[str, str, float]] = []

    def sync_derived_adjacency(self, slot_keys, pairs):
        self.pairs = list(pairs)
        return AdjacencySync(created=len(pairs), updated=0, removed=0)


class TestRecomputeTakesTheLocationFactor:
    """Two points 50 cm apart with no species: spacing 30 cm, so the factor alone decides (1.5 -> 45 cm, 2 -> 60)."""

    def _service(self, location_factor: float | None) -> tuple[AdjacencyService, _Graph]:
        sites = FakeSites(make_site())
        repo = FakePlanRepo(sites)
        repo.locations["tent"] = make_location(
            "tent", geometry=rect(1, 1, 2, 1), location_type_key="tent", adjacency_factor=location_factor
        )
        for key, x in (("s1", 0.2), ("s2", 0.7)):
            repo.slots.append(
                Slot(
                    _key=key,
                    slot_id=f"TENT_{key.upper()}",
                    location_key="tent",
                    slot_role=SlotRole.POSITION,
                    geometry={"kind": "point", "origin": [x, 0.5]},
                )
            )
        graph = _Graph()
        return AdjacencyService(sites, repo, graph), graph

    def test_without_its_own_factor_the_site_factor_leaves_them_apart(self) -> None:
        service, graph = self._service(None)

        result = service.recompute("tent", tenant_key=TENANT)

        assert result.pairs == 0

    def test_the_location_factor_makes_them_neighbours(self) -> None:
        service, graph = self._service(2.0)

        result = service.recompute("tent", tenant_key=TENANT)

        assert result.pairs == 1
        assert graph.pairs == [("s1", "s2", 50.0)]


def _tent_summary(service: GardenResourceService, repo: FakePlanRepo, plants: list[PlantPhotoperiod]):
    repo.counters["tent"] = BedCounters(active_plant_count=len(plants))
    repo.photoperiods["tent"] = plants
    return service.get_summary("tent", tenant_key=TENANT)


def _plant(
    key: str, phase: str | None, hours: float | None, code: str | None = None, *, source: PhotoperiodSource | None
) -> PlantPhotoperiod:
    return PlantPhotoperiod(
        plant_key=key,
        phase_name=phase,
        photoperiod_hours=hours,
        phase_code=code,
        display_name=f"Plant {key}",
        photoperiod_source=source,
    )


def _sourced(key: str, phase: str | None, hours: float, code: str | None = None) -> PlantPhotoperiod:
    """A plant whose phase profile states its hours from a Steckbrief or a person's entry (#2857)."""
    return _plant(key, phase, hours, code, source=PhotoperiodSource.SOURCED)


def _no_profile(key: str, phase: str | None) -> PlantPhotoperiod:
    """A plant whose current phase resolves no requirement profile."""
    return _plant(key, phase, None, source=None)


def _shelf(repo: FakePlanRepo, lighting: LocationLighting | None) -> None:
    repo.locations["shelf"] = make_location(
        "shelf", name="Regal", geometry=rect(1, 4, 1, 0.4), location_type_key="shelf", lighting=lighting
    )
    repo.layout_types["shelf"] = True
    repo.counters["shelf"] = BedCounters(active_plant_count=2)
    repo.photoperiods["shelf"] = [_sourced("p1", "Vegetative", 18), _sourced("p2", "Flowering", 12)]


class TestPhotoperiodHintInTheSummary:
    def test_a_tent_supports_a_layout_and_is_no_bed(self, world) -> None:
        service, repo = world

        view = _tent_summary(service, repo, [])

        assert view.supports_layout is True
        assert view.is_bed is False

    def test_different_photoperiods_raise_the_conflict_hint(self, world) -> None:
        service, repo = world

        view = _tent_summary(
            service,
            repo,
            [_sourced("p1", "Vegetative", 18), _sourced("p2", "Vegetative", 18), _sourced("p3", "Flowering", 12)],
        )

        (hint,) = view.tent_hints
        assert hint.code == HINT_PHOTOPERIOD_CONFLICT
        assert hint.severity == "warning"
        assert [(g.photoperiod_hours, g.plant_count, g.phase_names) for g in hint.groups] == [
            (18.0, 2, ("Vegetative",)),
            (12.0, 1, ("Flowering",)),
        ]

    def test_the_hint_disappears_once_the_photoperiods_agree(self, world) -> None:
        service, repo = world

        view = _tent_summary(service, repo, [_sourced("p1", "Flowering", 12), _sourced("p3", "Flowering", 12)])

        assert view.tent_hints == []

    def test_an_unknown_photoperiod_is_reported_never_assumed(self, world) -> None:
        service, repo = world

        view = _tent_summary(service, repo, [_sourced("p1", "Vegetative", 18), _no_profile("p2", "Seedling")])

        (hint,) = view.tent_hints
        assert hint.code == HINT_PHOTOPERIOD_UNKNOWN
        assert hint.severity == "info"
        assert hint.unknown_plant_count == 1

    def test_a_bed_never_reads_the_photoperiods(self, world) -> None:
        service, repo = world
        repo.counters["bed"] = BedCounters(active_plant_count=3)
        repo.photoperiods["bed"] = [_sourced("p1", "Vegetative", 18), _sourced("p2", "Flowering", 12)]

        view = service.get_summary("bed", tenant_key=TENANT)

        assert view.tent_hints == []
        assert repo.photoperiod_reads == []

    def test_a_single_plant_reads_nothing(self, world) -> None:
        service, repo = world

        view = _tent_summary(service, repo, [_sourced("p1", "Vegetative", 18)])

        assert view.tent_hints == []
        assert repo.photoperiod_reads == []

    def test_the_read_carries_the_callers_tenant(self, world) -> None:
        service, repo = world
        _tent_summary(service, repo, [_sourced("p1", "Vegetative", 18), _sourced("p2", "Flowering", 12)])

        assert repo.photoperiod_reads == ["tent"]
        assert repo.locations["tent"].site_key == SITE

    def test_young_plants_take_no_part(self, world) -> None:
        service, repo = world

        view = _tent_summary(
            service,
            repo,
            [_sourced("p1", "Flowering", 12, "flowering"), _sourced("p2", "Seedling", 18, "seedling")],
        )

        assert view.tent_hints == []

    def test_the_unknown_hint_names_the_plants(self, world) -> None:
        service, repo = world

        view = _tent_summary(service, repo, [_sourced("p1", "Vegetative", 18), _no_profile("p2", "Flowering")])

        (hint,) = view.tent_hints
        assert hint.unknown_plant_names == ("Plant p2",)

    def test_default_and_generated_hours_are_unknown_not_a_conflict(self, world) -> None:
        """#2857: hours nobody chose for the species (generator table, fallback) never make a conflict."""
        service, repo = world

        view = _tent_summary(
            service,
            repo,
            [
                _plant("p1", "Vegetative", 18, "vegetative", source=PhotoperiodSource.DEFAULT),
                _plant("p2", "Flowering", 12, "flowering", source=PhotoperiodSource.GENERATED),
                _plant("p3", "Flowering", 12, "flowering", source=None),
            ],
        )

        (hint,) = view.tent_hints
        assert (hint.code, hint.severity, hint.unknown_plant_count) == (HINT_PHOTOPERIOD_UNKNOWN, "info", 3)
        assert hint.groups == ()


class TestPhotoperiodHintOnAShelf:
    def test_a_shelf_level_with_its_own_lamp_gets_the_hint(self, world) -> None:
        service, repo = world
        _shelf(repo, LocationLighting(lamp_height_cm=40.0))

        view = service.get_summary("shelf", tenant_key=TENANT)

        assert [hint.code for hint in view.tent_hints] == [HINT_PHOTOPERIOD_CONFLICT]
        assert repo.photoperiod_reads == ["shelf"]

    def test_an_unlit_shelf_takes_its_light_from_the_day(self, world) -> None:
        service, repo = world
        _shelf(repo, None)

        view = service.get_summary("shelf", tenant_key=TENANT)

        assert view.tent_hints == []
        assert repo.photoperiod_reads == []

    def test_a_canopy_distance_alone_is_no_lamp(self, world) -> None:
        service, repo = world
        _shelf(repo, LocationLighting(canopy_distance_cm=20.0))

        view = service.get_summary("shelf", tenant_key=TENANT)

        assert view.tent_hints == []
