"""Tests for survival-rate / failure-cause aggregation (REQ-003 G1).

``get_survival_stats`` turns the repository's raw aggregation into a survival
model: ``survived`` counts concluded instances (``terminated``) that were NOT an
unplanned ``died`` loss, ``survival_rate`` is ``survived / terminated`` over
concluded instances, the termination-type/cause breakdowns are mapped onto their
enums, and the
loss-by-phase counts are merged by resolved phase *name* (per-lifecycle phase
keys of the same canonical phase are summed) and sorted most-affected first.
Tenant isolation is verified by pinning the tenant_key handed to the repo and
rejecting the empty-tenant sentinel.
"""

from unittest.mock import MagicMock

import pytest

from app.common.enums import TerminationCause, TerminationType
from app.common.exceptions import ValidationError
from app.domain.services.plant_instance_service import PlantInstanceService


def _phase(name: str) -> MagicMock:
    phase = MagicMock()
    phase.name = name
    return phase


class TestSurvivalStats:
    def setup_method(self) -> None:
        self.plant_repo = MagicMock()
        self.site_repo = MagicMock()
        self.rotation = MagicMock()
        self.companion = MagicMock()
        self.phase_repo = MagicMock()

    def _service(self) -> PlantInstanceService:
        return PlantInstanceService(
            self.plant_repo,
            self.site_repo,
            self.rotation,
            self.companion,
            phase_repo=self.phase_repo,
        )

    def test_aggregates_rate_breakdowns_and_merges_phase_by_name(self) -> None:
        self.plant_repo.get_survival_stats.return_value = {
            "total": 10,
            "terminated": 6,
            "died": 4,
            "by_type": [
                {"value": "harvested", "count": 1},
                {"value": "senesced", "count": 1},
                {"value": "died", "count": 4},
            ],
            "by_cause": [
                {"value": "pest", "count": 3},
                {"value": "frost", "count": 1},
            ],
            # Two distinct phase keys resolve to the same canonical name → merged.
            "by_phase": [
                {"value": "ph-veg-basil", "count": 1},
                {"value": "ph-veg-tomato", "count": 2},
                {"value": "ph-flower", "count": 1},
            ],
        }
        self.phase_repo.get_phase_by_key.side_effect = lambda key: {
            "ph-veg-basil": _phase("vegetative"),
            "ph-veg-tomato": _phase("vegetative"),
            "ph-flower": _phase("flowering"),
        }[key]

        stats = self._service().get_survival_stats("t-1")

        assert stats.total == 10
        assert stats.terminated == 6
        assert stats.active == 4  # total - terminated
        assert stats.died == 4
        assert stats.survived == 2  # terminated - died (concluded, not died)
        assert stats.survival_rate == 0.3333  # survived / terminated = 2 / 6

        type_counts = {c.termination_type: c.count for c in stats.by_termination_type}
        assert type_counts == {
            TerminationType.HARVESTED: 1,
            TerminationType.SENESCED: 1,
            TerminationType.DIED: 4,
        }

        cause_counts = {c.termination_cause: c.count for c in stats.by_termination_cause}
        assert cause_counts == {TerminationCause.PEST: 3, TerminationCause.FROST: 1}

        # Merged by name and sorted most-affected first.
        assert [(p.phase_name, p.count) for p in stats.loss_by_phase] == [
            ("vegetative", 3),
            ("flowering", 1),
        ]

    def test_empty_tenant_has_zero_rate_and_empty_breakdowns(self) -> None:
        self.plant_repo.get_survival_stats.return_value = {
            "total": 0,
            "terminated": 0,
            "died": 0,
            "by_type": [],
            "by_cause": [],
            "by_phase": [],
        }

        stats = self._service().get_survival_stats("t-1")

        assert stats.total == 0
        assert stats.survival_rate == 0.0  # no division-by-zero
        assert stats.by_termination_type == []
        assert stats.loss_by_phase == []

    def test_unresolved_phase_key_falls_back_to_empty_name(self) -> None:
        self.plant_repo.get_survival_stats.return_value = {
            "total": 2,
            "terminated": 1,
            "died": 1,
            "by_type": [{"value": "died", "count": 1}],
            "by_cause": [{"value": "unknown", "count": 1}],
            "by_phase": [{"value": "ph-gone", "count": 1}],
        }
        self.phase_repo.get_phase_by_key.return_value = None  # phase no longer exists

        stats = self._service().get_survival_stats("t-1")

        assert len(stats.loss_by_phase) == 1
        assert stats.loss_by_phase[0].phase_name == ""
        assert stats.loss_by_phase[0].count == 1

    def test_passes_tenant_key_through_to_repository(self) -> None:
        self.plant_repo.get_survival_stats.return_value = {
            "total": 0,
            "terminated": 0,
            "died": 0,
            "by_type": [],
            "by_cause": [],
            "by_phase": [],
        }

        self._service().get_survival_stats("tenant-xyz")

        self.plant_repo.get_survival_stats.assert_called_once_with("tenant-xyz")

    def test_empty_tenant_key_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._service().get_survival_stats("")
        self.plant_repo.get_survival_stats.assert_not_called()
