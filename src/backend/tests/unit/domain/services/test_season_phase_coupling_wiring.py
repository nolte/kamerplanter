"""The SeasonState transition drives the growth-phase coupler (ADR-006 E3, #565 WP-3).

Verifies that ``SeasonStateService._apply_side_effects`` invokes the injected
:class:`SeasonPhaseCoupler` — ``enter_dormancy`` on ``winter_dormancy`` and
``restart_cycle`` on ``pre_spring`` — so the two yearly cycles (REQ-047 season +
REQ-003 growth phase) are coupled, not run independently.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.common.enums import SeasonPhase
from app.domain.engines.season_state_engine import SeasonStateTransition
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Site
from app.domain.services.season_state_service import SeasonStateService


def _plant() -> PlantInstance:
    return PlantInstance(
        _key="plant-1",
        tenant_key="t1",
        instance_id="i1",
        species_key="sp-1",
        planted_on=date(2026, 1, 1),
        site_key="site-1",
    )


def _service_with_coupler() -> tuple[SeasonStateService, MagicMock]:
    coupler = MagicMock()
    plant_repo = MagicMock()
    plant_repo.find_by_field.return_value = [_plant()]
    service = SeasonStateService(
        MagicMock(),  # repo
        MagicMock(),  # resolver
        MagicMock(),  # engine
        MagicMock(),  # materializer
        MagicMock(),  # dormancy_activator
        MagicMock(),  # care_service
        MagicMock(),  # overwintering_repo
        plant_repo,
        MagicMock(),  # site_repo
        coupler,
    )
    return service, coupler


def _transition(to_phase: SeasonPhase) -> SeasonStateTransition:
    return SeasonStateTransition(
        changed=True,
        from_phase=SeasonPhase.GROWING,
        to_phase=to_phase,
        season_year=2026,
        consecutive_signal_days=0,
        reason_i18n_key="x",
    )


def _site() -> Site:
    return Site(_key="site-1", tenant_key="t1", name="Garden", type="outdoor")


def test_winter_dormancy_calls_enter_dormancy() -> None:
    service, coupler = _service_with_coupler()
    service._apply_side_effects(_site(), _transition(SeasonPhase.WINTER_DORMANCY))
    coupler.enter_dormancy.assert_called_once()
    assert coupler.enter_dormancy.call_args.args[0].key == "plant-1"
    coupler.restart_cycle.assert_not_called()


def test_pre_spring_calls_restart_cycle() -> None:
    service, coupler = _service_with_coupler()
    service._apply_side_effects(_site(), _transition(SeasonPhase.PRE_SPRING))
    coupler.restart_cycle.assert_called_once()
    assert coupler.restart_cycle.call_args.args[0].key == "plant-1"


@pytest.mark.parametrize("phase", [SeasonPhase.PRE_WINTER, SeasonPhase.GROWING])
def test_other_phases_do_not_drive_growth_phase(phase: SeasonPhase) -> None:
    service, coupler = _service_with_coupler()
    service._apply_side_effects(_site(), _transition(phase))
    coupler.enter_dormancy.assert_not_called()
    coupler.restart_cycle.assert_not_called()


def test_coupler_failure_does_not_abort_evaluation() -> None:
    """A failing coupler is swallowed by the per-plant _safe guard (AC-18)."""
    service, coupler = _service_with_coupler()
    coupler.enter_dormancy.side_effect = RuntimeError("boom")
    # Must not raise.
    service._apply_side_effects(_site(), _transition(SeasonPhase.WINTER_DORMANCY))
    coupler.enter_dormancy.assert_called_once()
