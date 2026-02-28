from app.domain.models.starter_kit import StarterKit


class OnboardingEngine:
    """Pure domain logic for onboarding wizard."""

    def validate_kit_application(
        self,
        kit: StarterKit,
        site_name: str,
        plant_count: int,
    ) -> list[str]:
        """Validate that kit application inputs are sensible."""
        errors: list[str] = []
        if not site_name or not site_name.strip():
            errors.append("Site name is required")
        if plant_count < 1:
            errors.append("At least one plant must be created")
        if plant_count > kit.plant_count_suggestion * 3:
            errors.append(
                f"Plant count ({plant_count}) exceeds 3x the suggestion ({kit.plant_count_suggestion})"
            )
        if not kit.species_keys:
            errors.append("Kit has no species configured")
        return errors

    def build_entity_plan(
        self,
        kit: StarterKit,
        site_name: str,
        plant_count: int,
    ) -> dict:
        """Build a plan of entities to create from a kit.

        Returns a dict describing what will be created.
        """
        species_per_plant = len(kit.species_keys)
        if species_per_plant == 0:
            return {"site": site_name, "locations": 0, "plants": 0, "species_keys": []}

        plants_per_species = max(1, plant_count // species_per_plant)
        remainder = plant_count % species_per_plant

        plant_assignments: list[dict[str, str | int]] = []
        for i, species_key in enumerate(kit.species_keys):
            count = plants_per_species + (1 if i < remainder else 0)
            plant_assignments.append({"species_key": species_key, "count": count})

        return {
            "site_name": site_name,
            "site_type": kit.site_type.value,
            "location_count": 1,
            "plant_assignments": plant_assignments,
            "total_plants": plant_count,
            "species_keys": kit.species_keys,
            "cultivar_keys": kit.cultivar_keys,
            "workflow_template_keys": kit.workflow_template_keys,
            "includes_nutrient_plan": kit.includes_nutrient_plan,
        }
