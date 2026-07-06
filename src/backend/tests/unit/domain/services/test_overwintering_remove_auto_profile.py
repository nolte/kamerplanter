"""REQ-047 §3.4 — ``OverwinteringProfileService.remove_auto_profile_for_plant``.

Removing a plant's auto-generated overwintering profile (when it is moved off an
outdoor/greenhouse site) is deliberately conservative: it only deletes a profile
that exists, belongs to the tenant, was auto-generated and has NOT been manually
overridden. Everything else is a silent, idempotent no-op.
"""

from app.common.enums import HardinessRating, WinterAction
from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.services.overwintering_profile_service import OverwinteringProfileService

TENANT = "tenant-anna"
FOREIGN = "tenant-bob"


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


def _service() -> tuple[OverwinteringProfileService, FakeOverwinteringRepo]:
    repo = FakeOverwinteringRepo()
    return OverwinteringProfileService(repo), repo


def _profile(
    plant_key: str = "plant-1",
    *,
    auto_generated: bool = True,
    user_overridden: bool = False,
    tenant: str = TENANT,
) -> OverwinteringProfile:
    return OverwinteringProfile(
        plant_key=plant_key,
        hardiness_rating=HardinessRating.NEEDS_PROTECTION,
        winter_action=WinterAction.MULCH,
        winter_action_month=10,
        auto_generated=auto_generated,
        user_overridden=user_overridden,
        tenant_key=tenant,
    )


class TestRemoveAutoProfileForPlant:
    def test_removes_auto_generated_profile(self) -> None:
        service, repo = _service()
        repo.create_profile(_profile())

        assert service.remove_auto_profile_for_plant("plant-1", TENANT) is True
        assert repo.get_profile_by_plant_key("plant-1") is None

    def test_keeps_user_overridden_profile(self) -> None:
        service, repo = _service()
        repo.create_profile(_profile(user_overridden=True))

        assert service.remove_auto_profile_for_plant("plant-1", TENANT) is False
        assert repo.get_profile_by_plant_key("plant-1") is not None

    def test_keeps_manually_created_profile(self) -> None:
        service, repo = _service()
        repo.create_profile(_profile(auto_generated=False))

        assert service.remove_auto_profile_for_plant("plant-1", TENANT) is False
        assert repo.get_profile_by_plant_key("plant-1") is not None

    def test_no_profile_is_noop(self) -> None:
        service, _ = _service()

        assert service.remove_auto_profile_for_plant("plant-1", TENANT) is False

    def test_foreign_tenant_profile_is_never_touched(self) -> None:
        service, repo = _service()
        repo.create_profile(_profile(tenant=FOREIGN))

        assert service.remove_auto_profile_for_plant("plant-1", TENANT) is False
        assert repo.get_profile_by_plant_key("plant-1") is not None
