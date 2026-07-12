"""REQ-047 AC-26 / AC-29 — overwintering-materializer upgrade paths.

* AC-29 — a plant whose lifecycle has already terminated (monocarpic/biennial past
  its flowering/senescence phase, or any harvested/died/cancelled instance) gets no
  *new* overwintering profile at the next ``pre_winter`` transition.
* AC-26 — a potted (container) plant that would overwinter in-situ in a bed (yellow,
  path A) is escalated to the relocation path B (its root ball freezes in a pot).

The tests wire the real :class:`OverwinteringMaterializer` /
:class:`OverwinteringProfileService` over in-memory fakes so the whole derivation
runs end-to-end.
"""

from datetime import date

from app.common.enums import (
    FrostTolerance,
    HardinessRating,
    SiteType,
    TerminationType,
    WinterAction,
)
from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Site
from app.domain.models.species import Species
from app.domain.services.overwintering_materializer import OverwinteringMaterializer
from app.domain.services.overwintering_profile_service import OverwinteringProfileService

TENANT = "tenant-anna"


class FakeOverwinteringRepo(IOverwinteringProfileRepository):
    def __init__(self) -> None:
        self.store: dict[str, OverwinteringProfile] = {}
        self._seq = 0

    def get_profile_by_key(self, key):
        return self.store.get(key)

    def get_profile_by_plant_key(self, plant_key):
        return next((p for p in self.store.values() if p.plant_key == plant_key), None)

    def get_profile_by_run_key(self, run_key):
        return next((p for p in self.store.values() if p.planting_run_key == run_key), None)

    def create_profile(self, profile):
        self._seq += 1
        key = f"ow-{self._seq}"
        stored = profile.model_copy(update={"key": key})
        self.store[key] = stored
        return stored

    def update_profile(self, key, profile):
        stored = profile.model_copy(update={"key": key})
        self.store[key] = stored
        return stored

    def delete_profile(self, key):
        return self.store.pop(key, None) is not None

    def list_by_tenant(self, tenant_key, offset=0, limit=50):
        items = [p for p in self.store.values() if p.tenant_key == tenant_key]
        return items[offset : offset + limit], len(items)

    def create_subject_edge(self, profile_key, *, plant_key=None, planting_run_key=None):
        pass

    def create_winter_quarter_edge(self, profile_key, location_key):
        pass


class FakePlantRepo:
    def __init__(self) -> None:
        self.store: dict[str, PlantInstance] = {}

    def seed(self, plant: PlantInstance) -> PlantInstance:
        self.store[plant.key or ""] = plant
        return plant

    def get_by_key(self, key):
        return self.store.get(key)


class FakeSpeciesRepo:
    def __init__(self, species: Species) -> None:
        self._species = species

    def get_by_key(self, key):
        return self._species


def _species(frost: FrostTolerance = FrostTolerance.MODERATE, zones: list[str] | None = None) -> Species:
    return Species(scientific_name="Salvia officinalis", frost_sensitivity=frost, hardiness_zones=zones or [])


def _site() -> Site:
    return Site(key="site-out", tenant_key=TENANT, name="Bed", type=SiteType.OUTDOOR, climate_zone="")


def _plant(
    *,
    key: str = "plant-1",
    container_volume_liters: float | None = None,
    termination_type: TerminationType | None = None,
) -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key=TENANT,
        instance_id="i1",
        species_key="species-1",
        planted_on=date(2024, 1, 1),
        site_key="site-out",
        plant_name="p",
        container_volume_liters=container_volume_liters,
        termination_type=termination_type,
    )


def _materializer(species: Species) -> tuple[OverwinteringMaterializer, FakeOverwinteringRepo, FakePlantRepo]:
    ow_repo = FakeOverwinteringRepo()
    plant_repo = FakePlantRepo()
    species_repo = FakeSpeciesRepo(species)
    ow_service = OverwinteringProfileService(
        ow_repo,
        plant_repo=plant_repo,
        species_repo=species_repo,
    )
    materializer = OverwinteringMaterializer(ow_service, ow_repo, species_repo)
    return materializer, ow_repo, plant_repo


class TestAc29TerminatedPlant:
    def test_terminated_plant_without_profile_is_not_materialized(self) -> None:
        materializer, ow_repo, plant_repo = _materializer(_species())
        plant = plant_repo.seed(_plant(termination_type=TerminationType.SENESCED))

        result = materializer.materialize(plant, _site())

        assert result is None
        assert ow_repo.get_profile_by_plant_key(plant.key) is None

    def test_harvested_plant_without_profile_is_not_materialized(self) -> None:
        materializer, ow_repo, _plant_repo_ = _materializer(_species())
        plant = _plant(termination_type=TerminationType.HARVESTED)

        assert materializer.materialize(plant, _site()) is None
        assert ow_repo.get_profile_by_plant_key(plant.key) is None

    def test_alive_plant_still_materializes(self) -> None:
        materializer, ow_repo, plant_repo = _materializer(_species())
        plant = plant_repo.seed(_plant(termination_type=None))

        result = materializer.materialize(plant, _site())

        assert result is not None
        assert ow_repo.get_profile_by_plant_key(plant.key) is not None

    def test_terminated_plant_with_existing_profile_keeps_it(self) -> None:
        materializer, ow_repo, plant_repo = _materializer(_species())
        plant = plant_repo.seed(_plant(termination_type=TerminationType.SENESCED))
        existing = ow_repo.create_profile(
            OverwinteringProfile(
                plant_key=plant.key,
                hardiness_rating=HardinessRating.NEEDS_PROTECTION,
                winter_action=WinterAction.MULCH,
                winter_action_month=10,
                auto_generated=True,
                tenant_key=TENANT,
            )
        )

        result = materializer.materialize(plant, _site())

        # The guard only blocks *new* materialisation; an existing profile is kept
        # (provenance may be back-filled).
        assert result is not None
        assert result.plant_key == existing.plant_key


class TestAc26ContainerEscalation:
    def test_potted_yellow_plant_escalates_to_path_b(self) -> None:
        materializer, _ow_repo, plant_repo = _materializer(_species(FrostTolerance.MODERATE))
        plant = plant_repo.seed(_plant(container_volume_liters=15.0))

        result = materializer.materialize(plant, _site())

        assert result is not None
        assert result.derived_path == "B"
        assert result.winter_action == WinterAction.MOVE_INDOORS

    def test_bed_yellow_plant_stays_path_a(self) -> None:
        materializer, _ow_repo, plant_repo = _materializer(_species(FrostTolerance.MODERATE))
        plant = plant_repo.seed(_plant(container_volume_liters=None))

        result = materializer.materialize(plant, _site())

        assert result is not None
        assert result.derived_path == "A"
        assert result.winter_action in {WinterAction.MULCH, WinterAction.FLEECE, WinterAction.EARTH_UP}
