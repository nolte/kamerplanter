"""Unit tests for the REQ-047 ↔ REQ-003 coupling (ADR-006 E3, #565 WP-3).

Verifies that the season state drives the biological growth phase — dormancy on
``winter_dormancy``, cycle restart on ``pre_spring`` — but ONLY for effectively
perennial plants (conservative instance gate on the species' practised cycle), so an
annual instance is never forced into dormancy/restart.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from app.common.enums import CycleType, TransitionTrigger
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.models.phase_sequence import PhaseSequence
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.season_phase_coupler import SeasonPhaseCoupler


def _plant(
    current_phase_key: str = "e-flowering",
    cultivation_cycle_type: CycleType | None = None,
) -> PlantInstance:
    return PlantInstance(
        _key="plant-1",
        tenant_key="t1",
        instance_id="i1",
        species_key="sp-1",
        planted_on=date(2026, 1, 1),
        current_phase_key=current_phase_key,
        cultivation_cycle_type=cultivation_cycle_type,
    )


def _lifecycle_repo(lc: LifecycleConfig | None) -> MagicMock:
    repo = MagicMock()
    repo.get_lifecycle_by_species.return_value = lc
    return repo


def _seq_repo(seq: PhaseSequence | None) -> MagicMock:
    repo = MagicMock()
    repo.get_sequence_by_species.return_value = seq
    return repo


def _perennial_lc() -> LifecycleConfig:
    return LifecycleConfig(species_key="sp-1", cycle_type=CycleType.PERENNIAL)


class TestEnterDormancy:
    def test_perennial_is_driven_to_dormancy(self) -> None:
        phase_service = MagicMock()
        phase_service.find_phase_key_by_role.return_value = "e-dormancy"
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(_perennial_lc()))

        assert coupler.enter_dormancy(_plant()) is True
        phase_service.transition_phase.assert_called_once_with(
            "plant-1", "e-dormancy", reason="season_winter_dormancy", force=True, trigger=TransitionTrigger.AUTO
        )

    def test_role_typed_rest_phase_is_coupled(self) -> None:
        """#677 / NCT-2: a #616 fine-typed rest phase (e.g. ``winter_rest`` on a
        ``cam_succulent_rest`` sequence) is resolved by ROLE, not the literal ``dormancy``."""
        phase_service = MagicMock()
        # No literal ``dormancy`` phase exists — only the role-typed ``winter_rest``.
        phase_service.find_phase_key_by_role.return_value = "e-winter-rest"
        phase_service.find_phase_key_by_name.return_value = None
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(_perennial_lc()))

        assert coupler.enter_dormancy(_plant()) is True
        phase_service.find_phase_key_by_role.assert_called_once_with("sp-1", "dormancy")
        phase_service.transition_phase.assert_called_once_with(
            "plant-1", "e-winter-rest", reason="season_winter_dormancy", force=True, trigger=TransitionTrigger.AUTO
        )

    def test_legacy_literal_dormancy_fallback(self) -> None:
        """Legacy sequences without a role-typed rest phase fall back to the literal
        ``dormancy`` name lookup."""
        phase_service = MagicMock()
        phase_service.find_phase_key_by_role.return_value = None  # no role-typed rest phase
        phase_service.find_phase_key_by_name.return_value = "e-dormancy"
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(_perennial_lc()))

        assert coupler.enter_dormancy(_plant()) is True
        phase_service.find_phase_key_by_name.assert_called_once_with("sp-1", "dormancy")
        phase_service.transition_phase.assert_called_once_with(
            "plant-1", "e-dormancy", reason="season_winter_dormancy", force=True, trigger=TransitionTrigger.AUTO
        )

    def test_annual_instance_is_not_forced_into_dormancy(self) -> None:
        """E3: an annual (cultivation_cycle_type) instance keeps its linear cycle."""
        phase_service = MagicMock()
        annual = LifecycleConfig(
            species_key="sp-1", cycle_type=CycleType.PERENNIAL, cultivation_cycle_type=CycleType.ANNUAL
        )
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(annual))

        assert coupler.enter_dormancy(_plant()) is False
        phase_service.transition_phase.assert_not_called()

    def test_evergreen_without_dormancy_phase_is_untouched(self) -> None:
        phase_service = MagicMock()
        phase_service.find_phase_key_by_role.return_value = None  # no rest-role phase
        phase_service.find_phase_key_by_name.return_value = None  # no literal dormancy phase
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(_perennial_lc()))

        assert coupler.enter_dormancy(_plant()) is False
        phase_service.transition_phase.assert_not_called()

    def test_already_dormant_is_idempotent(self) -> None:
        phase_service = MagicMock()
        phase_service.find_phase_key_by_role.return_value = "e-dormancy"
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(_perennial_lc()))

        assert coupler.enter_dormancy(_plant(current_phase_key="e-dormancy")) is False
        phase_service.transition_phase.assert_not_called()


class TestRestartCycle:
    def test_perennial_restarts_at_anchor(self) -> None:
        phase_service = MagicMock()
        phase_service.resolve_cycle_restart_phase_key.return_value = "e-sprouting"
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(_perennial_lc()))

        assert coupler.restart_cycle(_plant(current_phase_key="e-dormancy")) is True
        phase_service.transition_phase.assert_called_once_with(
            "plant-1", "e-sprouting", reason="season_cycle_restart", force=True, trigger=TransitionTrigger.AUTO
        )

    def test_annual_instance_is_not_restarted(self) -> None:
        phase_service = MagicMock()
        annual = LifecycleConfig(
            species_key="sp-1", cycle_type=CycleType.PERENNIAL, cultivation_cycle_type=CycleType.ANNUAL
        )
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(annual))

        assert coupler.restart_cycle(_plant(current_phase_key="e-dormancy")) is False
        phase_service.transition_phase.assert_not_called()

    def test_no_lifecycle_falls_back_to_sequence_cycle_type(self) -> None:
        """Species without a LifecycleConfig gate on the PhaseSequence cycle_type."""
        phase_service = MagicMock()
        phase_service.resolve_cycle_restart_phase_key.return_value = "e-sprouting"
        seq = PhaseSequence(_key="seq-1", name="perennial_runner", cycle_type=CycleType.PERENNIAL)
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(None), _seq_repo(seq))

        assert coupler.restart_cycle(_plant(current_phase_key="e-dormancy")) is True


class TestInstanceOverride:
    """ADR-006 E1 — the per-instance cultivation_cycle_type override drives the gate
    via resolve_effective_cycle, beating the species cycle in both directions."""

    def test_annual_override_on_perennial_species_is_not_driven_to_dormancy(self) -> None:
        phase_service = MagicMock()
        phase_service.find_phase_key_by_name.return_value = "e-dormancy"
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(_perennial_lc()))

        plant = _plant(cultivation_cycle_type=CycleType.ANNUAL)
        assert coupler.enter_dormancy(plant) is False
        phase_service.transition_phase.assert_not_called()

    def test_annual_override_on_perennial_species_is_not_restarted(self) -> None:
        phase_service = MagicMock()
        phase_service.resolve_cycle_restart_phase_key.return_value = "e-sprouting"
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(_perennial_lc()))

        plant = _plant(current_phase_key="e-dormancy", cultivation_cycle_type=CycleType.ANNUAL)
        assert coupler.restart_cycle(plant) is False
        phase_service.transition_phase.assert_not_called()

    def test_perennial_override_on_annual_species_is_driven_to_dormancy(self) -> None:
        phase_service = MagicMock()
        phase_service.find_phase_key_by_role.return_value = "e-dormancy"
        annual = LifecycleConfig(species_key="sp-1", cycle_type=CycleType.ANNUAL)
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(annual))

        plant = _plant(cultivation_cycle_type=CycleType.PERENNIAL)
        assert coupler.enter_dormancy(plant) is True
        phase_service.transition_phase.assert_called_once()

    def test_perennial_override_on_annual_species_is_restarted(self) -> None:
        phase_service = MagicMock()
        phase_service.resolve_cycle_restart_phase_key.return_value = "e-sprouting"
        annual = LifecycleConfig(species_key="sp-1", cycle_type=CycleType.ANNUAL)
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(annual))

        plant = _plant(current_phase_key="e-dormancy", cultivation_cycle_type=CycleType.PERENNIAL)
        assert coupler.restart_cycle(plant) is True
        phase_service.transition_phase.assert_called_once()


class TestReclassifiedTenderPerennial:
    """ADR-006 E1 negative proof for the tomato-cohort reclassification.

    A tender perennial is seeded with a SPECIES-level botanical ``cycle_type=perennial`` and
    a SPECIES-level ``cultivation_cycle_type=annual`` (no per-instance override). The season
    coupler must still treat it as an annual — ``_is_effective_perennial`` is False — so the
    reclassification (which activates ``grown_as_annual``) never drags it into dormancy or a
    seasonal restart.
    """

    @staticmethod
    def _tender_perennial_lc() -> LifecycleConfig:
        return LifecycleConfig(
            species_key="sp-1",
            cycle_type=CycleType.PERENNIAL,
            cultivation_cycle_type=CycleType.ANNUAL,
        )

    def test_effective_cycle_is_annual_not_perennial(self) -> None:
        coupler = SeasonPhaseCoupler(MagicMock(), _lifecycle_repo(self._tender_perennial_lc()))
        assert coupler._is_effective_perennial(_plant()) is False

    def test_not_driven_to_dormancy(self) -> None:
        phase_service = MagicMock()
        phase_service.find_phase_key_by_name.return_value = "e-dormancy"
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(self._tender_perennial_lc()))

        assert coupler.enter_dormancy(_plant()) is False
        phase_service.transition_phase.assert_not_called()

    def test_not_restarted(self) -> None:
        phase_service = MagicMock()
        phase_service.resolve_cycle_restart_phase_key.return_value = "e-sprouting"
        coupler = SeasonPhaseCoupler(phase_service, _lifecycle_repo(self._tender_perennial_lc()))

        assert coupler.restart_cycle(_plant(current_phase_key="e-dormancy")) is False
        phase_service.transition_phase.assert_not_called()
