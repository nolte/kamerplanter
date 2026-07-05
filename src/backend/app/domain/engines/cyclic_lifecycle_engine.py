"""Cyclic / perennial lifecycle decisions (REQ-003 D1/D4/D6/D10).

A pure-logic engine that decides, for cyclic (perennial) and bounded-cyclic
(biennial / monocarpic) lifecycles:

* whether the seasonal cycle restarts after the terminal phase or terminates
  (biennial `max_seasons`, monocarpic `flowering_strategy`),
* the maturity stage across the productive life (juvenile → productive →
  declining), which drives the D4 juvenile-skip of reproductive phases,
* the monocarpic terminal behaviour (D6) — and, for pup-based monocarps (D10),
  the mother is terminal while continuation happens through **new** clonal plant
  instances (a propagation/lineage concern, REQ-017), not a cycle restart.

No persistence: callers pass the season number, plant age and current phase.
"""

from __future__ import annotations

from app.common.enums import CycleType, FloweringStrategy, GrowthDeterminacy, MaturityStage
from app.domain.engines.phase_role_map import core_phase, is_productive_phase
from app.domain.models.lifecycle import LifecycleConfig

# Core reproductive phases after which a monocarpic plant enters terminal
# senescence (extended phase names are normalised via the D8 map).
_REPRODUCTIVE_TERMINAL = frozenset({"flowering", "fruit_development", "ripening"})


class CyclicLifecycleEngine:
    """Seasonal-cycle, maturity and terminal-behaviour decisions."""

    def is_monocarpic(self, lifecycle: LifecycleConfig) -> bool:
        """D6/D10: flowers once then dies (agave, bromeliad, many bamboos)."""
        return lifecycle.flowering_strategy == FloweringStrategy.MONOCARPIC

    def is_monocarpic_terminal(self, lifecycle: LifecycleConfig, current_phase_name: str) -> bool:
        """D10: whether a monocarpic plant has just entered its terminal reproductive
        phase (``flowering`` / ``fruit_development`` / ``ripening``).

        This is the single decision point at which continuation happens through a
        clonal pup (a **new** plant instance, REQ-017) rather than a seasonal cycle
        restart — the mother lives on, senescent, until it dies. Pure: the caller
        passes the (D8-normalised) current phase name; the side effect of spawning
        and linking the pup belongs to the service layer (NFR-001)."""
        return self.is_monocarpic(lifecycle) and core_phase(current_phase_name) in _REPRODUCTIVE_TERMINAL

    def effective_max_seasons(self, lifecycle: LifecycleConfig) -> int | None:
        """Season bound: explicit ``max_seasons``, else 2 for biennials, else None."""
        if lifecycle.max_seasons is not None:
            return lifecycle.max_seasons
        if lifecycle.cycle_type == CycleType.BIENNIAL:
            return 2
        return None

    def get_maturity_stage(self, lifecycle: LifecycleConfig, plant_age_years: int) -> MaturityStage:
        """D4: juvenile below ``first_bearing_year``, declining past the productive span."""
        first = lifecycle.first_bearing_year
        if first is not None and plant_age_years < first:
            return MaturityStage.JUVENILE
        productive = lifecycle.expected_productive_years
        if first is not None and productive is not None and plant_age_years > first + productive:
            return MaturityStage.DECLINING
        return MaturityStage.PRODUCTIVE

    def skips_reproductive_phases(self, lifecycle: LifecycleConfig, plant_age_years: int) -> bool:
        """D4 juvenile-skip: a juvenile perennial skips flowering/fruit/ripening."""
        return self.get_maturity_stage(lifecycle, plant_age_years) == MaturityStage.JUVENILE

    def stays_in_productive_phase(self, lifecycle: LifecycleConfig, current_phase_name: str) -> bool:
        """E4: whether an auto-advance out of the current phase must be suppressed.

        The state machine stays single-current-phase. For an ``indeterminate``
        species (tomato, pepper, cucumber, many house plants) the productive phase
        (``fruiting`` / ``flowering_fruit`` / ``flowering``) is a **stable, recurring**
        phase in which vegetative growth, flowering and fruit set run *concurrently*
        as attributes of that one phase — harvest is continuous, without a phase
        change. So once such a plant has reached its productive phase, a time/gdd
        trigger that would otherwise advance it onward (fruit_development → ripening
        → terminal) is suppressed; it simply keeps producing.

        ``determinate`` (and the default ``None``) species follow the linear path and
        are never suppressed. The decision is pure — the caller passes the current
        phase name (extended names are normalised via the D8 role map).
        """
        if lifecycle.growth_determinacy != GrowthDeterminacy.INDETERMINATE:
            return False
        return is_productive_phase(current_phase_name)

    def should_restart_cycle(
        self,
        lifecycle: LifecycleConfig,
        current_season_number: int,
        current_phase_name: str,
    ) -> tuple[bool, str]:
        """Whether the seasonal cycle restarts after the terminal phase.

        Returns ``(should_restart, reason)``. Bounded (biennial / ``max_seasons``)
        and monocarpic lifecycles terminate instead of restarting (D1/D6/D10).
        """
        max_seasons = self.effective_max_seasons(lifecycle)
        if max_seasons is not None and current_season_number >= max_seasons:
            return False, f"Terminal lifecycle: last season {current_season_number}/{max_seasons} reached"
        if self.is_monocarpic(lifecycle) and core_phase(current_phase_name) in _REPRODUCTIVE_TERMINAL:
            return False, "Monocarpic: flowers once, terminal senescence after seed set"
        if lifecycle.cycle_type == CycleType.PERENNIAL:
            return True, f"Seasonal restart: season {current_season_number + 1}"
        return False, "Non-cyclic lifecycle (annual) — no restart"
