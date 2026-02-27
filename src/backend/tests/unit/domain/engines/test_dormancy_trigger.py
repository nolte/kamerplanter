from unittest.mock import MagicMock

from app.domain.engines.dormancy_trigger import DormancyTrigger
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.models.species import Species


def _make_lifecycle(dormancy_required: bool = True, critical_day_length: float | None = 10.0) -> LifecycleConfig:
    lc = MagicMock(spec=LifecycleConfig)
    lc.dormancy_required = dormancy_required
    lc.critical_day_length_hours = critical_day_length
    lc.key = "lc1"
    return lc


def _make_species(base_temp: float = 5.0) -> Species:
    return Species(scientific_name="Test sp", genus="Test", base_temp=base_temp, _key="sp1")


class TestDormancyTriggerConsecutive:
    def setup_method(self):
        self.phase_repo = MagicMock()
        self.species_repo = MagicMock()
        self.trigger = DormancyTrigger(self.phase_repo, self.species_repo)

    def test_seven_consecutive_cold_days(self):
        """7 consecutive cold days should trigger dormancy."""
        self.phase_repo.get_lifecycle_by_species.return_value = _make_lifecycle()
        self.species_repo.get_by_key.return_value = _make_species(base_temp=5.0)

        observations = [{"temperature_c": 2.0, "day_length_hours": 8.0} for _ in range(7)]

        triggered, reason = self.trigger.should_trigger_dormancy_consecutive("sp1", observations, 7)
        assert triggered is True
        assert "consecutive days" in reason

    def test_six_cold_one_warm(self):
        """6 cold + 1 warm should NOT trigger."""
        self.phase_repo.get_lifecycle_by_species.return_value = _make_lifecycle()
        self.species_repo.get_by_key.return_value = _make_species(base_temp=5.0)

        observations = [{"temperature_c": 2.0, "day_length_hours": 8.0} for _ in range(6)]
        observations.append({"temperature_c": 10.0, "day_length_hours": 14.0})

        triggered, reason = self.trigger.should_trigger_dormancy_consecutive("sp1", observations, 7)
        assert triggered is False

    def test_too_few_observations(self):
        """Fewer observations than required should NOT trigger."""
        self.phase_repo.get_lifecycle_by_species.return_value = _make_lifecycle()
        self.species_repo.get_by_key.return_value = _make_species(base_temp=5.0)

        observations = [{"temperature_c": 2.0, "day_length_hours": 8.0} for _ in range(5)]

        triggered, reason = self.trigger.should_trigger_dormancy_consecutive("sp1", observations, 7)
        assert triggered is False
        assert "Not enough observations" in reason

    def test_dormancy_not_required(self):
        """Species not requiring dormancy should always return False."""
        self.phase_repo.get_lifecycle_by_species.return_value = _make_lifecycle(dormancy_required=False)
        self.species_repo.get_by_key.return_value = _make_species()

        observations = [{"temperature_c": -5.0, "day_length_hours": 6.0} for _ in range(7)]

        triggered, reason = self.trigger.should_trigger_dormancy_consecutive("sp1", observations, 7)
        assert triggered is False
        assert "not required" in reason

    def test_photoperiod_only_trigger(self):
        """Short day length alone should trigger if below critical threshold."""
        self.phase_repo.get_lifecycle_by_species.return_value = _make_lifecycle(critical_day_length=10.0)
        self.species_repo.get_by_key.return_value = _make_species(base_temp=5.0)

        # Temperature above base but day length below critical
        observations = [{"temperature_c": 8.0, "day_length_hours": 8.0} for _ in range(7)]

        triggered, reason = self.trigger.should_trigger_dormancy_consecutive("sp1", observations, 7)
        assert triggered is True

    def test_no_lifecycle(self):
        """Missing lifecycle should return False."""
        self.phase_repo.get_lifecycle_by_species.return_value = None

        triggered, reason = self.trigger.should_trigger_dormancy_consecutive("sp1", [], 7)
        assert triggered is False

    def test_uses_last_n_observations(self):
        """Should only check the last N observations, ignoring earlier warm days."""
        self.phase_repo.get_lifecycle_by_species.return_value = _make_lifecycle()
        self.species_repo.get_by_key.return_value = _make_species(base_temp=5.0)

        # 3 warm days + 7 cold days
        observations = [{"temperature_c": 20.0, "day_length_hours": 14.0} for _ in range(3)]
        observations.extend([{"temperature_c": 2.0, "day_length_hours": 8.0} for _ in range(7)])

        triggered, reason = self.trigger.should_trigger_dormancy_consecutive("sp1", observations, 7)
        assert triggered is True
