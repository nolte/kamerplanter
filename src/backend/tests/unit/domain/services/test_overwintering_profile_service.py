import pytest

from app.common.enums import FrostTolerance, HardinessRating, WinterAction
from app.common.exceptions import ValidationError, WinterPathViolationError
from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.services.overwintering_profile_service import OverwinteringProfileService


class FakeOverwinteringRepo(IOverwinteringProfileRepository):
    def __init__(self) -> None:
        self.store: dict[str, OverwinteringProfile] = {}
        self.edges: list[tuple] = []
        self._seq = 0

    def get_profile_by_key(self, key):
        return self.store.get(key)

    def get_profile_by_plant_key(self, plant_key):
        return next((p for p in self.store.values() if p.plant_key == plant_key), None)

    def get_profile_by_run_key(self, run_key):
        return next((p for p in self.store.values() if p.planting_run_key == run_key), None)

    def create_profile(self, profile):
        self._seq += 1
        key = f"ow{self._seq}"
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
        self.edges.append(("subject", profile_key, plant_key, planting_run_key))

    def create_winter_quarter_edge(self, profile_key, location_key):
        self.edges.append(("winter_quarter", profile_key, location_key))


TENANT = "tenant_anna"


@pytest.fixture
def service() -> OverwinteringProfileService:
    return OverwinteringProfileService(FakeOverwinteringRepo())


def _profile(**overrides) -> OverwinteringProfile:
    data = {
        "plant_key": "p1",
        "hardiness_rating": HardinessRating.HARDY,
        "winter_action": WinterAction.NONE,
        "winter_action_month": 10,
    }
    data.update(overrides)
    return OverwinteringProfile(**data)


class TestCreateD5:
    def test_valid_profile_created(self, service) -> None:
        created = service.create_profile(_profile(), TENANT)
        assert created.key
        assert created.tenant_key == TENANT

    def test_d5_contradiction_rejected(self, service) -> None:
        # path A rating (hardy) with a path B action (move_indoors) → 422
        bad = _profile(winter_action=WinterAction.MOVE_INDOORS)
        with pytest.raises(WinterPathViolationError):
            service.create_profile(bad, TENANT)

    def test_requires_exactly_one_subject(self, service) -> None:
        with pytest.raises(ValidationError):
            service.create_profile(_profile(plant_key=None, planting_run_key=None), TENANT)
        with pytest.raises(ValidationError):
            service.create_profile(_profile(plant_key="p1", planting_run_key="r1"), TENANT)

    def test_subject_edge_wired(self, service) -> None:
        created = service.create_profile(_profile(), TENANT)
        repo = service._repo
        assert ("subject", created.key, "p1", None) in repo.edges


class TestUpdateD5:
    def test_update_rejects_d5_contradiction(self, service) -> None:
        created = service.create_profile(_profile(), TENANT)
        with pytest.raises(WinterPathViolationError):
            service.update_profile(created.key, TENANT, {"winter_action": WinterAction.DIG_STORE})


class TestAutoGenerate:
    def test_red_species_relocated(self, service) -> None:
        profile = service.auto_generate_profile(TENANT, plant_key="p1", frost_sensitivity=FrostTolerance.SENSITIVE)
        assert profile.auto_generated is True
        assert profile.hardiness_rating == HardinessRating.FROST_FREE
        assert profile.winter_action == WinterAction.MOVE_INDOORS

    def test_green_species_in_situ(self, service) -> None:
        profile = service.auto_generate_profile(
            TENANT, plant_key="p1", frost_sensitivity=FrostTolerance.VERY_HARDY, species_zone="6a", site_zone="7a"
        )
        assert profile.hardiness_rating == HardinessRating.HARDY
        assert profile.winter_action == WinterAction.NONE


class TestHardinessOverview:
    def test_aggregates_counts_and_red_list(self, service) -> None:
        service.create_profile(_profile(plant_key="p1"), TENANT)  # green
        service.create_profile(
            _profile(
                plant_key="p2", hardiness_rating=HardinessRating.NEEDS_PROTECTION, winter_action=WinterAction.FLEECE
            ),
            TENANT,
        )  # yellow
        service.create_profile(
            _profile(
                plant_key="p3", hardiness_rating=HardinessRating.FROST_FREE, winter_action=WinterAction.MOVE_INDOORS
            ),
            TENANT,
        )  # red
        service.create_profile(
            _profile(
                plant_key="p4", hardiness_rating=HardinessRating.DIG_AND_STORE, winter_action=WinterAction.DIG_STORE
            ),
            TENANT,
        )  # red

        overview = service.get_hardiness_overview(TENANT)
        assert overview.green == 1
        assert overview.yellow == 1
        assert overview.red == 2
        assert overview.total == 4
        assert {e.plant_key for e in overview.red_plants} == {"p3", "p4"}

    def test_overview_is_tenant_scoped(self, service) -> None:
        service.create_profile(_profile(plant_key="p1"), TENANT)
        service.create_profile(_profile(plant_key="p2"), "other_tenant")
        overview = service.get_hardiness_overview(TENANT)
        assert overview.total == 1
