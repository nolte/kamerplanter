"""ADR-006 E1 — the single source of truth for a plant's effective cycle.

Before #565 Phase 2 the annual-vs-perennial decision was 100 % species-fixed:
``LifecycleConfig.cycle_type`` (botanical) with an optional species-level
``cultivation_cycle_type`` (practised). #541 showed that this is often a
per-instance cultivation decision of the grower (an overwintered tomato grown
perennial, a strawberry grown as an annual), so Phase 2 adds a per-instance
override (``PlantInstance.cultivation_cycle_type``).

To keep that from drifting across the many consumers (phase restart, the REQ-047
season-state coupling, the auto-transition restart gate, the dashboard/timeline
display), EVERY consumer resolves the effective cycle through this ONE function.
The cascade — most specific wins — is:

    instance.cultivation_cycle_type          # per-instance grower decision (E1)
      → species cultivation_cycle_type       # species cultivation practice (#297)
        → species botanical cycle_type       # species botanical lifespan (#297)
          → phase_sequence.cycle_type        # Weg-B template fallback (no LifecycleConfig)

The botanical ``cycle_type`` stays species-fixed (#297 is not broken); only the
*practised* axis becomes instance-overridable. Returns ``None`` only when no
source at all is known (neither a LifecycleConfig nor a PhaseSequence).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.enums import CycleType
    from app.domain.models.lifecycle import LifecycleConfig
    from app.domain.models.phase_sequence import PhaseSequence
    from app.domain.models.plant_instance import PlantInstance


def resolve_effective_cycle(
    instance: PlantInstance | None,
    lifecycle: LifecycleConfig | None,
    phase_sequence: PhaseSequence | None = None,
) -> CycleType | None:
    """Resolve a plant's effective cultivation cycle (ADR-006 E1 cascade).

    See the module docstring for the full priority. ``instance`` may be ``None``
    when a consumer only knows the species (e.g. a species-grouped timeline); the
    cascade then starts at the species tier. ``phase_sequence`` is the Weg-B
    fallback used only when there is no ``LifecycleConfig``.
    """
    if instance is not None and instance.cultivation_cycle_type is not None:
        return instance.cultivation_cycle_type
    if lifecycle is not None:
        if lifecycle.cultivation_cycle_type is not None:
            return lifecycle.cultivation_cycle_type
        return lifecycle.cycle_type
    if phase_sequence is not None:
        return phase_sequence.cycle_type
    return None
