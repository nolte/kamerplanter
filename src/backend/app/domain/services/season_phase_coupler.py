"""ADR-006 E3 — couple the REQ-047 season state to the REQ-003 growth phase.

Before #565 the two yearly cycles ran decoupled: the (site-wide) season state
switched only the *care* mode (``dormancy_care_activator``) and the overwintering
materialisation, never the biological growth phase — while the growth-phase cycle
restart (REQ-003) was never driven at all. This coupler closes that gap: on the
season transition into ``winter_dormancy`` the affected plants' growth phase is
driven to ``dormancy``, and on ``pre_spring`` the perennial cycle is restarted at
its restart anchor.

Instance gating (ADR-006 E3) is deliberately CONSERVATIVE here: the central
``resolve_effective_cycle`` cascade (Phase 2 / E1) does not exist yet, so an
instance is treated as perennial only when its species' *practised* cycle
(``LifecycleConfig.cultivation_cycle_type`` → botanical ``cycle_type``, else the
PhaseSequence ``cycle_type``) is perennial. An annual instance at a perennial site
is therefore NOT forced into dormancy/restart — the annual user intent wins, exactly
as E3 requires — without pre-empting the Phase-2 instance override.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.common.enums import CycleType, TransitionTrigger
from app.common.exceptions import PhaseTransitionError

if TYPE_CHECKING:
    from app.domain.interfaces.phase_repository import IPhaseRepository
    from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
    from app.domain.models.plant_instance import PlantInstance
    from app.domain.services.phase_service import PhaseService

logger = structlog.get_logger(__name__)

_DORMANCY_PHASE = "dormancy"


class SeasonPhaseCoupler:
    """Drive the growth phase from the season state (perennials only)."""

    def __init__(
        self,
        phase_service: PhaseService,
        lifecycle_repo: IPhaseRepository,
        phase_seq_repo: IPhaseSequenceRepository | None = None,
    ) -> None:
        self._phase_service = phase_service
        self._lifecycle_repo = lifecycle_repo
        self._phase_seq_repo = phase_seq_repo

    # ── Season-driven growth-phase effects ──────────────────────────────

    def enter_dormancy(self, plant: PlantInstance) -> bool:
        """On ``winter_dormancy``: drive an effectively-perennial plant to ``dormancy``.

        Returns ``True`` when the growth phase was moved. A plant that is not
        effectively perennial, has no ``dormancy`` phase (e.g. an evergreen), or is
        already dormant is left untouched (returns ``False``).
        """
        if not self._is_effective_perennial(plant):
            return False
        target = self._phase_service.find_phase_key_by_name(plant.species_key, _DORMANCY_PHASE)
        if target is None:
            return False
        return self._transition(plant, target, "season_winter_dormancy")

    def restart_cycle(self, plant: PlantInstance) -> bool:
        """On ``pre_spring``: restart an effectively-perennial plant's cycle.

        Transitions to the species' cycle-restart anchor (sprouting/vegetative, E4),
        which the transition engine records as a perennial cycle restart (cycle number
        increments). Returns ``True`` when the restart fired.
        """
        if not self._is_effective_perennial(plant):
            return False
        target = self._phase_service.resolve_cycle_restart_phase_key(plant.species_key)
        if target is None:
            return False
        return self._transition(plant, target, "season_cycle_restart")

    # ── Internals ───────────────────────────────────────────────────────

    def _is_effective_perennial(self, plant: PlantInstance) -> bool:
        """Conservative E3 gate — see the module docstring."""
        if not plant.species_key:
            return False
        lifecycle = self._lifecycle_repo.get_lifecycle_by_species(plant.species_key)
        if lifecycle is not None:
            effective = lifecycle.cultivation_cycle_type or lifecycle.cycle_type
            return effective == CycleType.PERENNIAL
        if self._phase_seq_repo is not None:
            seq = self._phase_seq_repo.get_sequence_by_species(plant.species_key)
            if seq is not None:
                return seq.cycle_type == CycleType.PERENNIAL
        return False

    def _transition(self, plant: PlantInstance, target_phase_key: str, reason: str) -> bool:
        """Best-effort growth-phase transition; a benign engine refusal is swallowed."""
        if not plant.key or not plant.current_phase_key:
            return False
        if plant.current_phase_key == target_phase_key:
            return False  # idempotent — already in the target phase
        try:
            # force=True: the season signal is authoritative for perennials, so it may
            # jump forward into dormancy or backward on a restart regardless of an
            # explicit transition rule; the restart is still recorded as a cycle restart.
            self._phase_service.transition_phase(
                plant.key, target_phase_key, reason=reason, force=True, trigger=TransitionTrigger.AUTO
            )
            logger.info("season_phase_coupled", plant_key=plant.key, to_phase=target_phase_key, reason=reason)
            return True
        except PhaseTransitionError as exc:
            # e.g. "Already in phase" on a same-order target — season coupling is
            # best-effort and must never abort the site evaluation.
            logger.info("season_phase_couple_skipped", plant_key=plant.key, reason=reason, detail=str(exc))
            return False
