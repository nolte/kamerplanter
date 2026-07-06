"""REQ-047 §3.4 — eager overwintering-profile sync on the plant instance service.

An overwintering profile is materialised **eagerly** the moment a plant instance
is placed on (or moved onto) an outdoor/greenhouse site, instead of only lazily at
the ``growing → pre_winter`` season transition. Moving a plant that carries a
purely auto-generated profile back indoors (or dropping its site) removes that
profile again — but a manually overridden profile is always kept.

These tests wire the *real* :class:`OverwinteringMaterializer` /
:class:`OverwinteringProfileService` over in-memory fakes so the full derivation
path is exercised end-to-end, plus a few :class:`MagicMock`-based tests that assert
the precise call / no-call contract (no site change, unwired collaborators).
"""

from datetime import date
from unittest.mock import MagicMock

from app.common.enums import FrostTolerance, HardinessRating, SiteType, WinterAction
from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Site
from app.domain.models.species import Species
from app.domain.services.overwintering_materializer import OverwinteringMaterializer
from app.domain.services.overwintering_profile_service import OverwinteringProfileService
from app.domain.services.plant_instance_service import PlantInstanceService

TENANT = "tenant-anna"
FOREIGN = "tenant-bob"


# ── Fakes ────────────────────────────────────────────────────────────────


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
    """Minimal plant repository fake with a distinct 'DB' snapshot.

    ``get_or_raise`` returns the *persisted* snapshot (deep copy) so the service can
    read the pre-update site_key even after the caller mutated the plant in memory.
    """

    def __init__(self) -> None:
        self.store: dict[str, PlantInstance] = {}
        self.db_state: dict[str, PlantInstance] = {}
        self._seq = 0

    def seed(self, plant: PlantInstance) -> PlantInstance:
        self.store[plant.key or ""] = plant
        self.db_state[plant.key or ""] = plant.model_copy(deep=True)
        return plant

    def create(self, plant: PlantInstance) -> PlantInstance:
        self._seq += 1
        if not plant.key:
            plant.key = f"plant-{self._seq}"
        self.store[plant.key] = plant
        self.db_state[plant.key] = plant.model_copy(deep=True)
        return plant

    def get_by_key(self, key):
        return self.store.get(key)

    def get_or_raise(self, key):
        return self.db_state[key]

    def update(self, key, plant):
        self.store[key] = plant
        self.db_state[key] = plant.model_copy(deep=True)
        return plant


class FakeSiteRepo:
    def __init__(self, sites: dict[str, Site]) -> None:
        self.sites = sites

    def get_site_by_key(self, key):
        return self.sites.get(key)

    def get_slot_by_key(self, key):
        return None

    def update_slot(self, key, slot):
        return slot


class FakeSpeciesRepo:
    def __init__(self, species: Species) -> None:
        self._species = species

    def get_by_key(self, key):
        return self._species


# ── Builders ─────────────────────────────────────────────────────────────


def _species(frost: FrostTolerance = FrostTolerance.MODERATE, zones: list[str] | None = None) -> Species:
    return Species(scientific_name="Salvia officinalis", frost_sensitivity=frost, hardiness_zones=zones or [])


def _site(key: str, site_type: SiteType, tenant: str = TENANT) -> Site:
    return Site(key=key, tenant_key=tenant, name=key, type=site_type, climate_zone="")


def _plant(site_key: str | None, *, key: str | None = None, tenant: str = TENANT, name: str = "p") -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key=tenant,
        instance_id="i1",
        species_key="species-1",
        planted_on=date(2024, 1, 1),
        site_key=site_key,
        plant_name=name,
    )


def _auto_profile(plant_key: str, *, user_overridden: bool = False, tenant: str = TENANT) -> OverwinteringProfile:
    return OverwinteringProfile(
        plant_key=plant_key,
        hardiness_rating=HardinessRating.NEEDS_PROTECTION,
        winter_action=WinterAction.MULCH,
        winter_action_month=10,
        auto_generated=True,
        user_overridden=user_overridden,
        tenant_key=tenant,
    )


def _real_service(
    sites: dict[str, Site],
    *,
    frost: FrostTolerance = FrostTolerance.MODERATE,
    zones: list[str] | None = None,
) -> tuple[PlantInstanceService, FakeOverwinteringRepo, FakePlantRepo]:
    ow_repo = FakeOverwinteringRepo()
    plant_repo = FakePlantRepo()
    site_repo = FakeSiteRepo(sites)
    species_repo = FakeSpeciesRepo(_species(frost, zones))

    ow_service = OverwinteringProfileService(
        ow_repo,
        site_repo=site_repo,
        plant_repo=plant_repo,
        species_repo=species_repo,
    )
    materializer = OverwinteringMaterializer(ow_service, ow_repo, species_repo)

    service = PlantInstanceService(
        plant_repo,
        site_repo,
        MagicMock(),  # rotation
        MagicMock(),  # companion
        overwintering_materializer=materializer,
        overwintering_service=ow_service,
    )
    return service, ow_repo, plant_repo


def _mock_service() -> tuple[PlantInstanceService, MagicMock, MagicMock, FakePlantRepo, FakeSiteRepo]:
    plant_repo = FakePlantRepo()
    site_repo = FakeSiteRepo(
        {
            "site-out": _site("site-out", SiteType.OUTDOOR),
            "site-in": _site("site-in", SiteType.INDOOR),
        }
    )
    materializer = MagicMock()
    ow_service = MagicMock()
    service = PlantInstanceService(
        plant_repo,
        site_repo,
        MagicMock(),
        MagicMock(),
        overwintering_materializer=materializer,
        overwintering_service=ow_service,
    )
    return service, materializer, ow_service, plant_repo, site_repo


# ── create_plant: eager materialisation ─────────────────────────────────


class TestCreateEagerMaterialisation:
    def test_outdoor_yellow_ampel_materialises_profile(self) -> None:
        service, ow_repo, _ = _real_service({"site-out": _site("site-out", SiteType.OUTDOOR)})

        created = service.create_plant(_plant("site-out"))

        profile = ow_repo.get_profile_by_plant_key(created.key)
        assert profile is not None
        assert profile.auto_generated is True
        assert profile.hardiness_rating == HardinessRating.NEEDS_PROTECTION

    def test_greenhouse_materialises_profile(self) -> None:
        service, ow_repo, _ = _real_service({"site-gh": _site("site-gh", SiteType.GREENHOUSE)})

        created = service.create_plant(_plant("site-gh"))

        assert ow_repo.get_profile_by_plant_key(created.key) is not None

    def test_balcony_materialises_profile(self) -> None:
        # REQ-047 §3.4 — a balcony is a frost-exposed outdoor location, so the eager
        # trigger materialises a profile there just like outdoor/greenhouse.
        service, ow_repo, _ = _real_service({"site-bal": _site("site-bal", SiteType.BALCONY)})

        created = service.create_plant(_plant("site-bal"))

        assert ow_repo.get_profile_by_plant_key(created.key) is not None

    def test_outdoor_green_ampel_hardy_species_creates_no_profile(self) -> None:
        # A winter-hardy species (ampel green) never gets a profile (AC-9).
        service, ow_repo, _ = _real_service(
            {"site-out": _site("site-out", SiteType.OUTDOOR)},
            frost=FrostTolerance.HARDY,
        )

        created = service.create_plant(_plant("site-out"))

        assert ow_repo.get_profile_by_plant_key(created.key) is None

    def test_indoor_site_creates_no_profile_even_when_yellow(self) -> None:
        service, ow_repo, _ = _real_service({"site-in": _site("site-in", SiteType.INDOOR)})

        created = service.create_plant(_plant("site-in"))

        assert ow_repo.get_profile_by_plant_key(created.key) is None

    def test_no_site_key_creates_no_profile_and_does_not_crash(self) -> None:
        service, ow_repo, _ = _real_service({})

        created = service.create_plant(_plant(None))

        assert created.key is not None
        assert ow_repo.get_profile_by_plant_key(created.key) is None

    def test_indoor_site_does_not_call_materialiser(self) -> None:
        service, materializer, _ow_service, _pr, _sr = _mock_service()

        service.create_plant(_plant("site-in"))

        materializer.materialize.assert_not_called()

    def test_foreign_tenant_site_is_not_materialised(self) -> None:
        # Fail-safe tenant guard: a site owned by another tenant must not derive a
        # profile even if it is outdoor.
        service, materializer, _ow_service, _pr, _sr = _mock_service()
        service._site_repo.sites["site-foreign"] = _site("site-foreign", SiteType.OUTDOOR, tenant=FOREIGN)

        service.create_plant(_plant("site-foreign"))

        materializer.materialize.assert_not_called()


# ── update_plant: move sync ─────────────────────────────────────────────


class TestUpdateMoveSync:
    def test_move_indoor_to_outdoor_materialises_profile(self) -> None:
        sites = {
            "site-in": _site("site-in", SiteType.INDOOR),
            "site-out": _site("site-out", SiteType.OUTDOOR),
        }
        service, ow_repo, plant_repo = _real_service(sites)
        plant = plant_repo.seed(_plant("site-in", key="plant-1"))

        moved = plant.model_copy(update={"site_key": "site-out"})
        service.update_plant("plant-1", moved)

        assert ow_repo.get_profile_by_plant_key("plant-1") is not None

    def test_move_outdoor_to_indoor_removes_auto_profile(self) -> None:
        sites = {
            "site-out": _site("site-out", SiteType.OUTDOOR),
            "site-in": _site("site-in", SiteType.INDOOR),
        }
        service, ow_repo, plant_repo = _real_service(sites)
        plant_repo.seed(_plant("site-out", key="plant-1"))
        ow_repo.create_profile(_auto_profile("plant-1"))
        assert ow_repo.get_profile_by_plant_key("plant-1") is not None

        moved = _plant("site-in", key="plant-1")
        service.update_plant("plant-1", moved)

        assert ow_repo.get_profile_by_plant_key("plant-1") is None

    def test_move_outdoor_to_indoor_keeps_user_overridden_profile(self) -> None:
        sites = {
            "site-out": _site("site-out", SiteType.OUTDOOR),
            "site-in": _site("site-in", SiteType.INDOOR),
        }
        service, ow_repo, plant_repo = _real_service(sites)
        plant_repo.seed(_plant("site-out", key="plant-1"))
        ow_repo.create_profile(_auto_profile("plant-1", user_overridden=True))

        moved = _plant("site-in", key="plant-1")
        service.update_plant("plant-1", moved)

        assert ow_repo.get_profile_by_plant_key("plant-1") is not None

    def test_move_outdoor_to_no_site_removes_auto_profile(self) -> None:
        service, ow_repo, plant_repo = _real_service({"site-out": _site("site-out", SiteType.OUTDOOR)})
        plant_repo.seed(_plant("site-out", key="plant-1"))
        ow_repo.create_profile(_auto_profile("plant-1"))

        moved = _plant(None, key="plant-1")
        service.update_plant("plant-1", moved)

        assert ow_repo.get_profile_by_plant_key("plant-1") is None

    def test_field_only_update_neither_materialises_nor_removes(self) -> None:
        service, materializer, ow_service, plant_repo, _sr = _mock_service()
        plant_repo.seed(_plant("site-out", key="plant-1", name="old"))

        renamed = _plant("site-out", key="plant-1", name="new")
        service.update_plant("plant-1", renamed)

        materializer.materialize.assert_not_called()
        ow_service.remove_auto_profile_for_plant.assert_not_called()


# ── Robustness: unwired collaborators ───────────────────────────────────


class TestWithoutOverwinteringCollaborators:
    def _plain_service(self) -> tuple[PlantInstanceService, FakePlantRepo]:
        plant_repo = FakePlantRepo()
        site_repo = FakeSiteRepo({"site-out": _site("site-out", SiteType.OUTDOOR)})
        service = PlantInstanceService(plant_repo, site_repo, MagicMock(), MagicMock())
        return service, plant_repo

    def test_create_without_materialiser_does_not_crash(self) -> None:
        service, _ = self._plain_service()

        created = service.create_plant(_plant("site-out"))

        assert created.key is not None

    def test_update_without_collaborators_does_not_crash(self) -> None:
        service, plant_repo = self._plain_service()
        plant_repo.seed(_plant("site-out", key="plant-1"))

        moved = _plant("site-in", key="plant-1")
        result = service.update_plant("plant-1", moved)

        assert result.site_key == "site-in"
