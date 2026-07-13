"""Cross-keyspace resolution of a plant's phase key (#579).

A phase key on a :class:`~app.domain.models.plant_instance.PlantInstance` (or a
phase-history entry) can live in one of two key-spaces:

1. **PhaseSequenceEntry** (``phase_sequence_entries`` — the current model driving
   plant creation, the timeline and the transition dialog). The entry carries its
   own ``sequence_order``/``is_terminal`` and references a
   :class:`~app.domain.models.phase_sequence.PhaseDefinition` for the human name.
2. **GrowthPhase** (legacy ``growth_phases`` — the LifecycleConfig model still
   used by species that predate the PhaseSequence migration).

Before #579 the transition engine resolved phase keys *only* against
``growth_phases`` (:meth:`IPhaseRepository.get_phase_by_key`), so every transition
of a PhaseSequence-driven species failed with ``Target phase '…' not found``. This
resolver normalises both key-spaces onto one :class:`ResolvedPhase`, trying the
PhaseSequenceEntry space first (authoritative for sequence-driven species, mirrors
``PlantInstanceService._valid_phase_keys``) and falling back to the legacy
GrowthPhase space only for genuine LifecycleConfig species.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository


@dataclass(frozen=True)
class ResolvedPhase:
    """A phase normalised across both key-spaces.

    ``source`` records which key-space the phase came from so callers can pick the
    right cycle-restart metadata: PhaseSequence phases carry ``sequence_key`` (the
    owning :class:`~app.domain.models.phase_sequence.PhaseSequence`), legacy phases
    carry ``lifecycle_key`` (the owning
    :class:`~app.domain.models.lifecycle.LifecycleConfig`).
    """

    key: str
    name: str
    sequence_order: int
    is_terminal: bool
    source: str  # "phase_sequence" | "growth_phase"
    sequence_key: str | None = None
    lifecycle_key: str | None = None


class PhaseKeyResolver:
    """Resolve a phase key to a :class:`ResolvedPhase` across both key-spaces."""

    def __init__(
        self,
        phase_repo: IPhaseRepository,
        phase_seq_repo: IPhaseSequenceRepository | None = None,
    ) -> None:
        self._phase_repo = phase_repo
        self._phase_seq_repo = phase_seq_repo

    def resolve(self, phase_key: str | None) -> ResolvedPhase | None:
        """Return the normalised phase for ``phase_key``, or ``None`` if unknown.

        Resolution order mirrors ``PlantInstanceService._valid_phase_keys``: the
        PhaseSequenceEntry key-space is authoritative, the legacy GrowthPhase
        key-space is the fallback. A key found in neither returns ``None`` — the
        caller decides whether that is a hard error (an invalid transition target)
        or a benign miss (an unset current phase).
        """
        if not phase_key:
            return None

        # 1. PhaseSequenceEntry key-space (authoritative for sequence-driven species).
        if self._phase_seq_repo is not None:
            entry = self._phase_seq_repo.get_entry_by_key(phase_key)
            if entry is not None:
                defn = self._phase_seq_repo.get_definition_by_key(entry.phase_definition_key)
                return ResolvedPhase(
                    key=entry.key or phase_key,
                    name=defn.name if defn else "",
                    sequence_order=entry.sequence_order,
                    is_terminal=entry.is_terminal,
                    source="phase_sequence",
                    sequence_key=entry.phase_sequence_key or None,
                )

        # 2. Legacy GrowthPhase key-space (LifecycleConfig species).
        phase = self._phase_repo.get_phase_by_key(phase_key)
        if phase is not None:
            return ResolvedPhase(
                key=phase.key or phase_key,
                name=phase.name,
                sequence_order=phase.sequence_order,
                is_terminal=phase.is_terminal,
                source="growth_phase",
                lifecycle_key=phase.lifecycle_key or None,
            )

        return None

    def resolve_name(self, phase_key: str | None) -> str:
        """Resolve a phase key to its human phase name (empty string when unknown)."""
        resolved = self.resolve(phase_key)
        return resolved.name if resolved else ""

    def is_known(self, phase_key: str | None) -> bool:
        """Return ``True`` when ``phase_key`` resolves in either key-space.

        Guardrail used to detect a dangling ``current_phase_key`` (a plant pointing
        at a PhaseSequenceEntry key that no longer exists after a sequence
        regeneration, #579 error #2).
        """
        return self.resolve(phase_key) is not None
