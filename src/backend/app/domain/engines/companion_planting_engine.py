"""Companion-planting compatibility (REQ-028) and the one per-pair rule every reader of it shares.

:func:`judge_neighbour` is **the** decision for one species next to another: an ``incompatible_with`` edge wins,
else a ``compatible_with`` edge with its score, else the relation is unknown. The engine's
:meth:`CompanionPlantingEngine.check_compatibility`, the planting dialog
(:meth:`~app.domain.services.bed_rotation_service.BedRotationService.validate_planting`) and the plan's companion
overlay (:mod:`~app.domain.services.companion_overlay_service`, GP-FR-134) all call it, so a neighbour cannot be
"compatible" in one view and "incompatible" in another. :func:`strongest_verdict` folds several verdicts (several
species in one slot, both directions of a pair) with the same precedence.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

from app.common.exceptions import CompanionConflictError
from app.domain.interfaces.graph_repository import IGraphRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.species_repository import ISpeciesRepository

CompanionStatus = Literal["compatible", "incompatible", "unknown"]

#: Precedence of the statuses: a lower rank wins when verdicts are folded, and orders a list strongest first.
COMPANION_STATUS_RANK: dict[CompanionStatus, int] = {"incompatible": 0, "compatible": 1, "unknown": 2}


@dataclass(frozen=True)
class CompanionVerdict:
    """The relation of one species to a neighbour; ``score`` only for ``compatible`` (as the edge stores it)."""

    status: CompanionStatus
    score: Any = None


UNKNOWN_VERDICT = CompanionVerdict("unknown")


def judge_neighbour(
    other_species_key: str,
    incompatible_keys: Collection[str],
    compatible_scores: Mapping[str, Any],
) -> CompanionVerdict:
    """The per-pair rule: how the anchor species, whose edges are given, relates to ``other_species_key``.

    ``incompatible_keys`` are the anchor's ``incompatible_with`` neighbours, ``compatible_scores`` its
    ``compatible_with`` neighbours with the edge score. An incompatible edge wins over a compatible one between the
    same two species; no edge at all is ``unknown`` - nothing is assumed (E-10).
    """
    if other_species_key in incompatible_keys:
        return CompanionVerdict("incompatible")
    if other_species_key in compatible_scores:
        return CompanionVerdict("compatible", compatible_scores[other_species_key])
    return UNKNOWN_VERDICT


def strongest_verdict(verdicts: Iterable[CompanionVerdict]) -> CompanionVerdict:
    """Fold verdicts with the precedence of :func:`judge_neighbour`.

    Incompatible wins, else the best compatible, else unknown. Of several compatible verdicts the highest score is
    kept (a missing score ranks below any number); on a tie the first one stays.
    """
    best = UNKNOWN_VERDICT
    for verdict in verdicts:
        rank, best_rank = COMPANION_STATUS_RANK[verdict.status], COMPANION_STATUS_RANK[best.status]
        stronger = rank < best_rank
        better_score = rank == best_rank and verdict.status == "compatible" and _higher(verdict.score, best.score)
        if stronger or better_score:
            best = verdict
    return best


def _higher(score: Any, than: Any) -> bool:
    return _score_key(score) > _score_key(than)


def _score_key(score: Any) -> float:
    return float(score) if isinstance(score, int | float) else float("-inf")


class CompanionPlantingEngine:
    """Evaluates companion planting compatibility."""

    def __init__(
        self,
        graph_repo: IGraphRepository,
        plant_repo: IPlantInstanceRepository,
        species_repo: ISpeciesRepository,
    ) -> None:
        self._graph_repo = graph_repo
        self._plant_repo = plant_repo
        self._species_repo = species_repo

    def check_compatibility(
        self,
        species_key: str,
        slot_key: str,
        *,
        tenant_key: str,
    ) -> tuple[bool, list[str], list[str]]:
        """Check companion planting compatibility for a species in a slot.

        Checks neighbors in adjacent slots.
        Returns (compatible, warnings, benefits).

        ``tenant_key`` is required and keyword-only (#927): the neighbour lookup
        is a tenant-scoped repository read, and the warnings it produces name the
        species growing next door. Reading that unscoped would put another
        tenant's crop into this tenant's warning text.
        """
        warnings: list[str] = []
        benefits: list[str] = []

        # Get adjacent slots
        adjacent = self._graph_repo.get_adjacent_slots(slot_key)

        incompatible = self._graph_repo.get_incompatible_species(species_key, tenant_key=tenant_key)
        incompatible_keys = {item["species"].get("_key", "") for item in incompatible}

        compatible = self._graph_repo.get_compatible_species(species_key, tenant_key=tenant_key)
        compatible_map = {item["species"].get("_key", ""): item.get("score", 0) for item in compatible}

        for adj in adjacent:
            adj_slot = adj.get("slot", adj.get("vertex", {}))
            adj_slot_key = adj_slot.get("_key", "")
            if not adj_slot_key:
                continue
            active_plants = self._plant_repo.get_active_by_slot(adj_slot_key, tenant_key=tenant_key)
            for plant in active_plants:
                verdict = judge_neighbour(plant.species_key, incompatible_keys, compatible_map)
                if verdict.status == "incompatible":
                    species = self._species_repo.get_by_key(plant.species_key)
                    name = species.scientific_name if species else plant.species_key
                    warnings.append(f"Incompatible neighbor: {name} in slot {adj_slot_key}")
                elif verdict.status == "compatible":
                    species = self._species_repo.get_by_key(plant.species_key)
                    name = species.scientific_name if species else plant.species_key
                    benefits.append(f"Compatible neighbor: {name} (score: {verdict.score})")

        return len(warnings) == 0, warnings, benefits

    def check_or_raise(self, species_key: str, slot_key: str, *, tenant_key: str) -> list[str]:
        """Check compatibility and raise on conflict. Returns benefits."""
        compatible, warnings, benefits = self.check_compatibility(species_key, slot_key, tenant_key=tenant_key)
        if not compatible and warnings:
            raise CompanionConflictError(species_key, f"neighbors in slot {slot_key}")
        return benefits

    def get_companion_recommendations(self, species_key: str, *, tenant_key: str | None) -> dict:
        """Get companion planting recommendations with family-level fallback.

        Returns species-level matches first. If none found, falls back to
        family-level compatibility with score * 0.8 discount. Both levels list
        only species ``tenant_key`` can see (MT-054); ``None`` is the system context.
        """
        # 1. Species-level matches
        compatible = self._graph_repo.get_compatible_species(species_key, tenant_key=tenant_key)
        if compatible:
            return {
                "matches": [
                    {
                        "species_key": c["species"].get("_key", ""),
                        "scientific_name": c["species"].get("scientific_name"),
                        "score": c.get("score", 0.0),
                        "match_level": "species",
                    }
                    for c in compatible
                ],
                "match_level": "species",
            }

        # 2. Family-level fallback
        species = self._species_repo.get_by_key(species_key)
        if not species or not species.family_key:
            return {"matches": [], "match_level": "species"}

        family_compat = self._graph_repo.get_family_compatible(species.family_key)
        matches = []
        for fc in family_compat:
            fam_key = fc["family"].get("_key", "")
            fam_species = self._graph_repo.get_species_by_family(fam_key, tenant_key=tenant_key)
            for s in fam_species:
                if s.get("_key") != species_key:
                    matches.append(
                        {
                            "species_key": s["_key"],
                            "scientific_name": s.get("scientific_name"),
                            "score": round(fc.get("compatibility_score", 0) * 0.8, 2),
                            "match_level": "family",
                            "benefit_type": fc.get("benefit_type", ""),
                        }
                    )

        return {"matches": matches, "match_level": "family" if matches else "species"}
