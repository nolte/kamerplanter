"""REQ-047 §3.2/§3.6 — SeasonStateService transition side-effect wiring (C2).

The season transition is the primary trigger for the winter/spring reminders:
entering ``pre_winter`` materialises the profile *and* creates the winter tasks;
entering ``pre_spring`` clears dormancy-care *and* creates the spring_uncover task.
"""

from datetime import date
from unittest.mock import MagicMock

from app.common.enums import SeasonPhase, SiteType
from app.domain.engines.season_state_engine import SeasonStateTransition
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Site
from app.domain.services.season_state_service import SeasonStateService


def _plant(key: str = "plant-1") -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key="tenant-1",
        instance_id="i1",
        species_key="species-1",
        planted_on=date(2024, 1, 1),
        site_key="site-1",
    )


def _site() -> Site:
    return Site(key="site-1", tenant_key="tenant-1", name="Garden", type=SiteType.OUTDOOR)


def _transition(to_phase: SeasonPhase) -> SeasonStateTransition:
    return SeasonStateTransition(
        changed=True,
        from_phase=SeasonPhase.GROWING,
        to_phase=to_phase,
        season_year=2026,
        consecutive_signal_days=0,
        reason_i18n_key="pages.season.trigger.frostForecast",
    )


def _service(care_service: MagicMock, materializer: MagicMock, dormancy: MagicMock) -> SeasonStateService:
    plant_repo = MagicMock()
    plant_repo.find_by_field.return_value = [_plant()]
    overwintering_repo = MagicMock()
    overwintering_repo.get_profile_by_plant_key.return_value = None
    return SeasonStateService(
        MagicMock(),  # repo
        MagicMock(),  # resolver
        MagicMock(),  # engine
        materializer,
        dormancy,
        care_service,
        overwintering_repo,
        plant_repo,
        MagicMock(),  # site_repo
    )


class TestApplySideEffects:
    def test_pre_winter_materialises_and_creates_winter_tasks(self) -> None:
        care_service = MagicMock()
        materializer = MagicMock()
        service = _service(care_service, materializer, MagicMock())

        service._apply_side_effects(_site(), _transition(SeasonPhase.PRE_WINTER))

        materializer.materialize.assert_called_once()
        care_service.ensure_seasonal_winter_tasks.assert_called_once_with("plant-1", SeasonPhase.PRE_WINTER)

    def test_pre_spring_leaves_dormancy_and_creates_spring_task(self) -> None:
        care_service = MagicMock()
        dormancy = MagicMock()
        service = _service(care_service, MagicMock(), dormancy)

        service._apply_side_effects(_site(), _transition(SeasonPhase.PRE_SPRING))

        dormancy.deactivate.assert_called_once_with("plant-1")
        care_service.ensure_seasonal_winter_tasks.assert_called_once_with("plant-1", SeasonPhase.PRE_SPRING)

    def test_growing_leaves_dormancy_without_winter_tasks(self) -> None:
        care_service = MagicMock()
        dormancy = MagicMock()
        service = _service(care_service, MagicMock(), dormancy)

        service._apply_side_effects(_site(), _transition(SeasonPhase.GROWING))

        dormancy.deactivate.assert_called_once_with("plant-1")
        care_service.ensure_seasonal_winter_tasks.assert_not_called()

    def test_dormancy_reuses_persisted_profile_without_double_read(self) -> None:
        """K4/efficiency — the persisted profile is loaded once and reused; the
        shared-template resolver is only consulted when there is no per-instance
        profile."""
        care_service = MagicMock()
        dormancy = MagicMock()
        service = _service(care_service, MagicMock(), dormancy)
        persisted = MagicMock(key="ow-1", dormancy_care_active=False)
        service._overwintering_repo.get_profile_by_plant_key.return_value = persisted

        service._apply_side_effects(_site(), _transition(SeasonPhase.WINTER_DORMANCY))

        dormancy.activate.assert_called_once()
        # The persisted profile was reused, so the public template resolver was not.
        care_service.resolve_overwintering_profile.assert_not_called()
