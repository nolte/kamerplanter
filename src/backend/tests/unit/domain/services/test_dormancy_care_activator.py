"""REQ-047 §3.5 — unit tests for the DormancyCareActivator.

Covers the K4 winter-protection guard: a winter-hardy plant (ampel green, no
overwintering profile) must not be switched into dormancy-care mode, while a
frost-tender plant with a profile is.
"""

from app.common.enums import CareStyleType, HardinessRating, WinterAction
from app.domain.models.care_reminder import CareProfile
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.services.dormancy_care_activator import DormancyCareActivator


class _FakeCareRepo:
    def __init__(self, profile: CareProfile | None) -> None:
        self._profile = profile
        self.updated: CareProfile | None = None

    def get_profile_by_plant_key(self, plant_key: str) -> CareProfile | None:
        return self._profile

    def update_profile(self, key: str, profile: CareProfile) -> CareProfile:
        self.updated = profile
        return profile


def _care() -> CareProfile:
    return CareProfile(care_style=CareStyleType.OUTDOOR_PERENNIAL, plant_key="p1")


def _owp() -> OverwinteringProfile:
    return OverwinteringProfile(
        plant_key="p1",
        hardiness_rating=HardinessRating.NEEDS_PROTECTION,
        winter_action=WinterAction.MULCH,
        winter_action_month=10,
        winter_watering="reduced",
    )


class TestDormancyGuard:
    def test_hardy_plant_without_profile_not_activated(self) -> None:
        """K4 — no overwintering profile (green) → no dormancy-care mode, and the
        CareProfile is never written."""
        repo = _FakeCareRepo(_care())
        activator = DormancyCareActivator(repo)

        result = activator.activate("p1", None)

        assert result is None
        assert repo.updated is None

    def test_protected_plant_activates_mode(self) -> None:
        repo = _FakeCareRepo(_care())
        activator = DormancyCareActivator(repo)

        result = activator.activate("p1", _owp())

        assert result is not None
        assert result.dormancy_care_mode is True
        assert repo.updated is not None
        assert repo.updated.dormancy_care_mode is True

    def test_deactivate_clears_mode(self) -> None:
        care = _care()
        care.dormancy_care_mode = True
        repo = _FakeCareRepo(care)
        activator = DormancyCareActivator(repo)

        result = activator.deactivate("p1")

        assert result is not None
        assert result.dormancy_care_mode is False
