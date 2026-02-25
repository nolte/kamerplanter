from app.common.exceptions import CompanionConflictError
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
        incompatible_keys = {item.get("vertex", {}).get("_key", "") for item in incompatible}

        compatible = self._graph_repo.get_compatible_species(species_key)
        compatible_map = {
            item.get("vertex", {}).get("_key", ""): item.get("edge", {}).get("score", 0)
            for item in compatible
        }

        for adj in adjacent:
            adj_slot_key = adj.get("vertex", {}).get("_key", "")
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
