"""Tests for NutrientPlanService.get_water_mix_recommendations_batch().

Uses MagicMock objects for domain models to avoid import-chain issues
with forward references (WateringSchedule) on Python 3.13.
"""

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.site import RoWaterProfile, SiteWaterConfig, TapWaterProfile


def _make_tap(**kwargs) -> TapWaterProfile:
    defaults = {
        "ec_ms": 0.4,
        "ph": 7.5,
        "alkalinity_ppm": 120,
        "gh_ppm": 200,
        "calcium_ppm": 60,
        "magnesium_ppm": 15,
        "chlorine_ppm": 0.3,
        "chloramine_ppm": 0.1,
    }
    defaults.update(kwargs)
    return TapWaterProfile(**defaults)


def _make_ro(**kwargs) -> RoWaterProfile:
    defaults = {"ec_ms": 0.02, "ph": 6.5}
    defaults.update(kwargs)
    return RoWaterProfile(**defaults)


def _make_plan_mock(key: str = "plan1", name: str = "Test Plan", tenant_key: str = "t1"):
    plan = MagicMock()
    plan.key = key
    plan.name = name
    plan.tenant_key = tenant_key
    plan.recommended_substrate_type = None
    return plan


def _make_site_mock(
    key: str = "site1",
    name: str = "Test Site",
    has_ro: bool = True,
    tenant_key: str = "t1",
):
    site = MagicMock()
    site.key = key
    site.name = name
    site.tenant_key = tenant_key
    if has_ro:
        site.water_config = SiteWaterConfig(
            has_ro_system=True,
            tap_water_profile=_make_tap(),
            ro_water_profile=_make_ro(),
        )
    else:
        site.water_config = None
    return site


def _make_entry_mock(
    sequence_order: int,
    phase_name_value: str = "vegetative",
    target_ec: float | None = 1.2,
    calcium_ppm: float | None = 60.0,
    magnesium_ppm: float | None = 15.0,
):
    entry = MagicMock()
    entry.sequence_order = sequence_order
    entry.phase_name.value = phase_name_value
    entry.calcium_ppm = calcium_ppm
    entry.magnesium_ppm = magnesium_ppm

    if target_ec is not None and target_ec > 0:
        channel = MagicMock()
        channel.target_ec_ms = target_ec
        entry.delivery_channels = [channel]
    elif target_ec == 0.0:
        channel = MagicMock()
        channel.target_ec_ms = 0.0
        entry.delivery_channels = [channel]
    else:
        entry.delivery_channels = []

    return entry


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_fert_repo():
    return MagicMock()


@pytest.fixture
def mock_validator():
    return MagicMock()


@pytest.fixture
def mock_site_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo, mock_fert_repo, mock_validator, mock_site_repo):
    # Import with patching to avoid WateringSchedule forward ref issue
    from app.domain.services.nutrient_plan_service import NutrientPlanService

    return NutrientPlanService(mock_repo, mock_fert_repo, mock_validator, mock_site_repo)


class TestGetWaterMixRecommendationsBatch:
    """Tests for the batch water mix recommendation method."""

    def test_returns_recommendations_for_all_entries_with_target_ec(
        self,
        service,
        mock_repo,
        mock_site_repo,
    ):
        """Should return one recommendation per entry that has target EC."""
        plan = _make_plan_mock()
        entries = [
            _make_entry_mock(1, target_ec=1.0),
            _make_entry_mock(2, target_ec=1.4, phase_name_value="flowering"),
        ]
        site = _make_site_mock()

        mock_repo.get_by_key.return_value = plan
        mock_repo.get_phase_entries.return_value = entries
        mock_site_repo.get_site_by_key.return_value = site

        result = service.get_water_mix_recommendations_batch(
            tenant_key="t1",
            plan_key="plan1",
            site_key="site1",
        )

        assert len(result["recommendations"]) == 2
        assert result["plan_name"] == "Test Plan"
        assert result["plan_key"] == "plan1"
        assert result["site_name"] == "Test Site"
        assert result["site_key"] == "site1"

        # Check individual recommendations
        rec_1 = result["recommendations"][0]
        assert rec_1["sequence_order"] == 1
        assert rec_1["phase_name"] == "vegetative"
        assert rec_1["recommendation"]["target_ec_ms"] == 1.0

        rec_2 = result["recommendations"][1]
        assert rec_2["sequence_order"] == 2
        assert rec_2["phase_name"] == "flowering"
        assert rec_2["recommendation"]["target_ec_ms"] == 1.4

    def test_entries_without_target_ec_inherit_from_neighbour(self, service, mock_repo, mock_site_repo):
        """Entries with no target EC inherit from the nearest neighbour."""
        plan = _make_plan_mock()
        entries = [
            _make_entry_mock(1, target_ec=1.2),
            _make_entry_mock(2, target_ec=None),  # No channels — inherits from seq 1
            _make_entry_mock(3, target_ec=0.0),  # Zero target EC — inherits from seq 2→1
        ]
        site = _make_site_mock()

        mock_repo.get_by_key.return_value = plan
        mock_repo.get_phase_entries.return_value = entries
        mock_site_repo.get_site_by_key.return_value = site

        result = service.get_water_mix_recommendations_batch(
            tenant_key="t1",
            plan_key="plan1",
            site_key="site1",
        )

        # All 3 entries get recommendations (seq 2 + 3 inherit EC 1.2 from seq 1)
        assert len(result["recommendations"]) == 3
        assert result["recommendations"][0]["sequence_order"] == 1
        assert result["recommendations"][0]["recommendation"]["target_ec_ms"] == 1.2
        assert result["recommendations"][1]["sequence_order"] == 2
        assert result["recommendations"][1]["recommendation"]["target_ec_ms"] == 1.2
        assert result["recommendations"][2]["sequence_order"] == 3
        assert result["recommendations"][2]["recommendation"]["target_ec_ms"] == 1.2

    def test_empty_list_when_no_ro_system(self, service, mock_repo, mock_site_repo):
        """Should return empty recommendations list (not error) when site has no RO."""
        plan = _make_plan_mock()
        site = _make_site_mock(has_ro=False)

        mock_repo.get_by_key.return_value = plan
        mock_site_repo.get_site_by_key.return_value = site

        result = service.get_water_mix_recommendations_batch(
            tenant_key="t1",
            plan_key="plan1",
            site_key="site1",
        )

        assert result["recommendations"] == []
        assert result["site_name"] == "Test Site"
        assert result["plan_name"] == "Test Plan"

    def test_raises_not_found_for_missing_plan(self, service, mock_repo, mock_site_repo):
        """Should raise NotFoundError when plan does not exist."""
        mock_repo.get_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.get_water_mix_recommendations_batch(
                tenant_key="t1",
                plan_key="missing",
                site_key="site1",
            )

    def test_raises_not_found_for_missing_site(self, service, mock_repo, mock_site_repo):
        """Should raise NotFoundError when site does not exist."""
        plan = _make_plan_mock()
        mock_repo.get_by_key.return_value = plan
        mock_site_repo.get_site_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.get_water_mix_recommendations_batch(
                tenant_key="t1",
                plan_key="plan1",
                site_key="missing",
            )

    def test_raises_not_found_for_wrong_tenant_site(self, service, mock_repo, mock_site_repo):
        """Should raise NotFoundError when site belongs to different tenant."""
        plan = _make_plan_mock()
        site = _make_site_mock(tenant_key="other-tenant")

        mock_repo.get_by_key.return_value = plan
        mock_site_repo.get_site_by_key.return_value = site

        with pytest.raises(NotFoundError):
            service.get_water_mix_recommendations_batch(
                tenant_key="t1",
                plan_key="plan1",
                site_key="site1",
            )

    def test_raises_validation_error_without_site_repo(self, mock_repo, mock_fert_repo, mock_validator):
        """Should raise ValidationError if site_repo is not configured."""
        from app.domain.services.nutrient_plan_service import NutrientPlanService

        svc = NutrientPlanService(mock_repo, mock_fert_repo, mock_validator, site_repo=None)

        with pytest.raises(ValidationError, match="Site repository not configured"):
            svc.get_water_mix_recommendations_batch(
                tenant_key="t1",
                plan_key="plan1",
                site_key="site1",
            )

    def test_substrate_type_override_used(self, service, mock_repo, mock_site_repo):
        """Substrate type override should be applied to all recommendations."""
        plan = _make_plan_mock()
        entries = [_make_entry_mock(1, target_ec=1.2)]
        site = _make_site_mock()

        mock_repo.get_by_key.return_value = plan
        mock_repo.get_phase_entries.return_value = entries
        mock_site_repo.get_site_by_key.return_value = site

        result = service.get_water_mix_recommendations_batch(
            tenant_key="t1",
            plan_key="plan1",
            site_key="site1",
            substrate_type_override="hydro_solution",
        )

        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0]["recommendation"]["substrate_type"] == "hydro_solution"

    def test_empty_entries_returns_empty_recommendations(self, service, mock_repo, mock_site_repo):
        """Plan with no entries should return empty recommendations list."""
        plan = _make_plan_mock()
        site = _make_site_mock()

        mock_repo.get_by_key.return_value = plan
        mock_repo.get_phase_entries.return_value = []
        mock_site_repo.get_site_by_key.return_value = site

        result = service.get_water_mix_recommendations_batch(
            tenant_key="t1",
            plan_key="plan1",
            site_key="site1",
        )

        assert result["recommendations"] == []

    def test_calmag_correction_included_in_batch(self, service, mock_repo, mock_site_repo):
        """Entries with Ca/Mg targets should include CalMag correction."""
        plan = _make_plan_mock()
        entries = [_make_entry_mock(1, target_ec=1.2, calcium_ppm=80.0, magnesium_ppm=20.0)]
        site = _make_site_mock()

        mock_repo.get_by_key.return_value = plan
        mock_repo.get_phase_entries.return_value = entries
        mock_site_repo.get_site_by_key.return_value = site

        result = service.get_water_mix_recommendations_batch(
            tenant_key="t1",
            plan_key="plan1",
            site_key="site1",
        )

        rec = result["recommendations"][0]["recommendation"]
        assert rec["calmag_correction"] is not None

    def test_loads_plan_entries_site_only_once(self, service, mock_repo, mock_site_repo):
        """Should load plan, entries, and site exactly once (not per entry)."""
        plan = _make_plan_mock()
        entries = [
            _make_entry_mock(1, target_ec=1.0),
            _make_entry_mock(2, target_ec=1.2),
            _make_entry_mock(3, target_ec=1.4),
        ]
        site = _make_site_mock()

        mock_repo.get_by_key.return_value = plan
        mock_repo.get_phase_entries.return_value = entries
        mock_site_repo.get_site_by_key.return_value = site

        service.get_water_mix_recommendations_batch(
            tenant_key="t1",
            plan_key="plan1",
            site_key="site1",
        )

        # Plan loaded once (via get_plan which calls get_by_key)
        mock_repo.get_by_key.assert_called_once_with("plan1")
        # Entries loaded once
        mock_repo.get_phase_entries.assert_called_once_with("plan1")
        # Site loaded once
        mock_site_repo.get_site_by_key.assert_called_once_with("site1")
