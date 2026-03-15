from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.services.tank_service import TankService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def service(mock_repo, mock_engine):
    return TankService(mock_repo, mock_engine)


class TestGetActiveNutrientPlans:
    def test_returns_plans(self, service, mock_repo):
        mock_repo.get_by_key.return_value = MagicMock(key="t1")
        mock_repo.get_active_nutrient_plans.return_value = [
            {
                "run_key": "run1",
                "run_name": "Tomato Run",
                "run_status": "active",
                "plan_key": "plan1",
                "plan_name": "Plagron Terra",
                "current_phase": "vegetative",
                "plant_count": 4,
                "current_phase_entry": {
                    "phase_name": "vegetative",
                    "delivery_channels": [],
                },
                "all_phase_entries": [],
                "fertilizers": [
                    {
                        "key": "f1",
                        "product_name": "Terra Grow",
                        "brand": "Plagron",
                        "fertilizer_type": "base",
                        "npk_ratio": [3, 1, 3],
                        "ec_contribution_per_ml": 0.08,
                        "mixing_priority": 10,
                    },
                ],
                "watering_schedule": {"mode": "interval", "interval_days": 2},
                "water_mix_ratio_ro_percent": 50,
            },
        ]

        result = service.get_active_nutrient_plans("t1")

        assert len(result) == 1
        assert result[0]["run_key"] == "run1"
        assert result[0]["plan_name"] == "Plagron Terra"
        assert result[0]["current_phase"] == "vegetative"
        assert len(result[0]["fertilizers"]) == 1
        assert result[0]["fertilizers"][0]["product_name"] == "Terra Grow"
        mock_repo.get_active_nutrient_plans.assert_called_once_with("t1")

    def test_empty_when_no_runs(self, service, mock_repo):
        mock_repo.get_by_key.return_value = MagicMock(key="t1")
        mock_repo.get_active_nutrient_plans.return_value = []

        result = service.get_active_nutrient_plans("t1")

        assert result == []

    def test_tank_not_found_raises(self, service, mock_repo):
        mock_repo.get_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.get_active_nutrient_plans("nonexistent")

    def test_multiple_runs(self, service, mock_repo):
        mock_repo.get_by_key.return_value = MagicMock(key="t1")
        mock_repo.get_active_nutrient_plans.return_value = [
            {
                "run_key": "run1",
                "run_name": "Tomato Run",
                "run_status": "active",
                "plan_key": "plan1",
                "plan_name": "Plagron Terra",
                "current_phase": "flowering",
                "plant_count": 4,
                "fertilizers": [],
            },
            {
                "run_key": "run2",
                "run_name": "Basil Run",
                "run_status": "active",
                "plan_key": "plan2",
                "plan_name": "Gardol Indoor",
                "current_phase": "vegetative",
                "plant_count": 6,
                "fertilizers": [],
            },
        ]

        result = service.get_active_nutrient_plans("t1")

        assert len(result) == 2
        assert result[0]["run_name"] == "Tomato Run"
        assert result[1]["run_name"] == "Basil Run"
