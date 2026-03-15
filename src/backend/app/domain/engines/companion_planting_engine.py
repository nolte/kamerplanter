from typing import TYPE_CHECKING

from app.common.exceptions import CompanionConflictError

if TYPE_CHECKING:
    from app.domain.interfaces.graph_repository import IGraphRepository
    from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
    from app.domain.interfaces.species_repository import ISpeciesRepository


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

    def check_compatibility(self, species_key: str, slot_key: str) -> tuple[bool, list[str], list[str]]:
        """Check companion planting compatibility for a species in a slot.
        Checks neighbors in adjacent slots.
        Returns (compatible, warnings, benefits).
        """
        warnings: list[str] = []
        benefits: list[str] = []

        # Get adjacent slots
        adjacent = self._graph_repo.get_adjacent_slots(slot_key)

        incompatible = self._graph_repo.get_incompatible_species(species_key)
        incompatible_keys = {item["species"].get("_key", "") for item in incompatible}

        compatible = self._graph_repo.get_compatible_species(species_key)
        compatible_map = {item["species"].get("_key", ""): item.get("score", 0) for item in compatible}

        for adj in adjacent:
            adj_slot = adj.get("slot", adj.get("vertex", {}))
            adj_slot_key = adj_slot.get("_key", "")
            if not adj_slot_key:
                continue
            active_plants = self._plant_repo.get_active_by_slot(adj_slot_key)
            for plant in active_plants:
                if plant.species_key in incompatible_keys:
                    species = self._species_repo.get_by_key(plant.species_key)
                    name = species.scientific_name if species else plant.species_key
                    warnings.append(f"Incompatible neighbor: {name} in slot {adj_slot_key}")
                elif plant.species_key in compatible_map:
                    species = self._species_repo.get_by_key(plant.species_key)
                    name = species.scientific_name if species else plant.species_key
                    benefits.append(f"Compatible neighbor: {name} (score: {compatible_map[plant.species_key]})")

        return len(warnings) == 0, warnings, benefits

    def check_or_raise(self, species_key: str, slot_key: str) -> list[str]:
        """Check compatibility and raise on conflict. Returns benefits."""
        compatible, warnings, benefits = self.check_compatibility(species_key, slot_key)
        if not compatible and warnings:
            raise CompanionConflictError(species_key, f"neighbors in slot {slot_key}")
        return benefits

    def get_companion_recommendations(self, species_key: str) -> dict:
        """Get companion planting recommendations with family-level fallback.

        Returns species-level matches first. If none found, falls back to
        family-level compatibility with score * 0.8 discount.
        """
        # 1. Species-level matches
        compatible = self._graph_repo.get_compatible_species(species_key)
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
            fam_species = self._graph_repo.get_species_by_family(fam_key)
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
