"""Bind a species to its default phase sequence — the runtime half of the seed rule.

Why this exists (#1006)
=======================

``seed_data.link_indoor_species_to_phase_sequence`` gives every seeded species a
``HAS_PHASE_SEQUENCE`` edge. Nothing did the same for a species minted at runtime:
``SpeciesService.create_species`` (identify → create, REQ-048) and the CSV
``ImportService`` both wrote the species and stopped. A plant created for such a
species then resolved no initial phase, and — before the ``else`` branch added to
``PlantInstanceService.create_plant`` — was stored with ``current_phase_key: null``
and an "initial" history entry pointing at nothing. That is what plant
``DRACA-0616-OWL`` looked like two months after planting.

Binding at species-creation time is the fix at the right end: the phase machine has
something to run against from the first plant onwards, rather than every consumer
having to cope with an unbound species.

The classifier is shared, not re-derived
----------------------------------------

The target sequence comes from :func:`~app.domain.engines.phase_sequence_resolver.resolve_phase_sequence_name`
— the same pure classifier the seed and the rebind migrations use. A second rule here
would drift from the seed within one release; the whole point of the engine living in
``domain/engines`` is that all three callers reach it.

Layering: this is a service (BACKEND.md §2.1) — it calls an engine and repositories
through their interfaces, and nothing calls it from an engine.
"""

from __future__ import annotations

import structlog

from app.domain.engines.cycle_resolver import resolve_effective_cycle
from app.domain.engines.phase_sequence_resolver import (
    INDOOR_DEFAULT_SEQUENCE,
    resolve_phase_sequence_name,
)
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.models.species import Species

logger = structlog.get_logger()

#: Page size for the sequence lookup. Mirrors the seed linker's 500 — the catalogue
#: holds ~21 sequences, and both sides must see the same set or they bind differently.
_SEQUENCE_PAGE = 500


def _enum_value(value: object) -> str | None:
    """Return ``value.value`` for an enum, the string itself, or ``None``."""
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


class PhaseSequenceBinder:
    """Give a species the phase sequence the seed would have given it."""

    def __init__(
        self,
        phase_seq_repo: IPhaseSequenceRepository,
        phase_repo: IPhaseRepository | None = None,
    ) -> None:
        self._phase_seq_repo = phase_seq_repo
        self._phase_repo = phase_repo

    def bind_default(self, species: Species) -> str | None:
        """Bind ``species`` to its resolved sequence. Returns the sequence name, or ``None``.

        ``None`` means nothing was bound, for one of three reasons, each logged:

        * the species already carries a binding (idempotent — a re-run is a no-op, and
          an explicit/precise binding is never overridden);
        * the species has no key yet;
        * not even ``indoor_default`` is seeded, so there is nothing to bind to.

        Never raises: a master-data gap must not fail the species write that triggered
        it. The caller keeps its species; the warning is the record.
        """
        species_key = species.key or ""
        if not species_key:
            return None

        try:
            if self._phase_seq_repo.get_sequence_by_species(species_key) is not None:
                return None

            sequences, _ = self._phase_seq_repo.get_all_sequences(0, _SEQUENCE_PAGE)
            key_by_name = {s.name: (s.key or "") for s in sequences}

            lifecycle = None
            if self._phase_repo is not None:
                lifecycle = self._phase_repo.get_lifecycle_by_species(species_key)

            # Bind on the EFFECTIVE (cultivation-aware) cycle through the one SSOT
            # cascade, exactly as the seed linker does (ADR-006 E1).
            effective_cycle = resolve_effective_cycle(None, lifecycle) if lifecycle is not None else None
            target_name = resolve_phase_sequence_name(
                species.scientific_name,
                cycle_type=_enum_value(effective_cycle),
                flowering_strategy=_enum_value(lifecycle.flowering_strategy) if lifecycle is not None else None,
                photosynthesis_type=_enum_value(species.photosynthesis_type),
                photoperiod_type=_enum_value(lifecycle.photoperiod_type) if lifecycle is not None else None,
                growth_habit=_enum_value(species.growth_habit),
            )

            resolved_name = target_name or INDOOR_DEFAULT_SEQUENCE
            target_key = key_by_name.get(resolved_name, "")
            if not target_key and target_name:
                # The resolver picked a cohort sequence that is not seeded — a seed-data
                # defect, not a routine fallback (issue #949). Say so, then fall back.
                logger.warning(
                    "phase_sequence_target_not_seeded",
                    species_key=species_key,
                    scientific_name=species.scientific_name,
                    target_sequence=target_name,
                    falling_back_to=INDOOR_DEFAULT_SEQUENCE,
                )
                resolved_name = INDOOR_DEFAULT_SEQUENCE
                target_key = key_by_name.get(INDOOR_DEFAULT_SEQUENCE, "")

            if not target_key:
                logger.warning(
                    "phase_sequence_binding_skipped",
                    species_key=species_key,
                    scientific_name=species.scientific_name,
                    reason="indoor_default sequence is not seeded",
                )
                return None

            self._phase_seq_repo.set_species_sequence(species_key, target_key)
            logger.info(
                "species_bound_to_phase_sequence",
                species_key=species_key,
                scientific_name=species.scientific_name,
                sequence=resolved_name,
            )
        except Exception as exc:  # noqa: BLE001 - binding must never fail the species write
            logger.warning(
                "phase_sequence_binding_failed",
                species_key=species_key,
                scientific_name=species.scientific_name,
                error=str(exc),
            )
            return None
        return resolved_name
