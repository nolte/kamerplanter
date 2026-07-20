from app.common.types import CultivarKey, FamilyKey, SpeciesKey
from app.domain.engines.companion_planting_engine import CompanionPlantingEngine
from app.domain.interfaces.graph_repository import IGraphRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.species import Cultivar, Species


class SpeciesService:
    def __init__(self, species_repo: ISpeciesRepository, graph_repo: IGraphRepository) -> None:
        self._repo = species_repo
        self._graph = graph_repo

    def list_species(self, offset: int = 0, limit: int = 50) -> tuple[list[Species], int]:
        return self._repo.get_all(offset, limit)

    def get_species(self, key: SpeciesKey) -> Species:
        species = self._repo.get_or_raise(key)
        return species

    def create_species(self, species: Species) -> Species:
        # Idempotent create (REQ-048 Stufe 1 / R5): when a species with the same
        # canonical dedup key already exists — even if it only differs by the
        # hybrid marker (× vs x), casing or whitespace — return that existing
        # record instead of raising or inserting a duplicate. This is the
        # operator-confirmed resolution: the identify→create path must never
        # accumulate normalization duplicates. The dedup is an atomic UPSERT on
        # scientific_name_normalized (SEC-003), so the check-then-insert window is
        # closed server-side.
        return self._repo.upsert_by_normalized_scientific_name(species)

    def update_species(self, key: SpeciesKey, species: Species) -> Species:
        existing = self.get_species(key)
        # The representative reference image is owned by the acquisition
        # pipeline (REQ-029-A §4), not the edit form — preserve it on update.
        species.representative_image_url = existing.representative_image_url
        species.representative_image_attribution = existing.representative_image_attribution
        species.representative_image_license = existing.representative_image_license
        # The provenance marker is server-managed (REQ-001/REQ-011) and never
        # submitted by the edit form — preserve it so a full-replace update never
        # resets an enriched/tenant record back to the 'system' default.
        species.origin = existing.origin
        # cultivation_flexible is master data (seed lifecycle_overrides, ADR-006 E6),
        # not an edit-form field — preserve it so a full-replace update never resets
        # the facultative-cultivation capability flag to its default.
        species.cultivation_flexible = existing.cultivation_flexible
        return self._repo.update(key, species)

    def delete_species(self, key: SpeciesKey) -> bool:
        self.get_species(key)
        return self._repo.delete(key)

    def search_species(self, name: str | None = None, family_key: FamilyKey | None = None) -> list[Species]:
        return self._repo.search(name=name, family_key=family_key)

    def list_cultivars(self, species_key: SpeciesKey) -> list[Cultivar]:
        self.get_species(species_key)
        return self._repo.get_cultivars(species_key)

    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        self.get_species(cultivar.species_key)
        return self._repo.create_cultivar(cultivar)

    def get_cultivar(self, key: CultivarKey) -> Cultivar:
        return self._repo.get_cultivar_or_raise(key)

    def update_cultivar(self, key: CultivarKey, cultivar: Cultivar) -> Cultivar:
        existing = self.get_cultivar(key)
        # Preserve the server-managed provenance marker across a full-replace
        # update (the edit form never submits it).
        cultivar.origin = existing.origin
        return self._repo.update_cultivar(key, cultivar)

    def delete_cultivar(self, key: CultivarKey) -> bool:
        self.get_cultivar(key)
        return self._repo.delete_cultivar(key)

    def get_compatible_species(self, species_key: SpeciesKey) -> list[dict]:
        self.get_species(species_key)
        raw = self._graph.get_compatible_species(species_key)
        # Pass the full common_names list straight through from the graph vertex —
        # it is already loaded on the species document (no extra query). The
        # presentation layer derives the layperson-facing display name from it
        # (first entry = German common name by seed convention, REQ-567/A).
        return [
            {
                "species_key": item["species"].get("_key", ""),
                "scientific_name": item["species"].get("scientific_name"),
                "common_names": item["species"].get("common_names", []),
                "score": item.get("score", 0.0),
            }
            for item in raw
        ]

    def get_incompatible_species(self, species_key: SpeciesKey) -> list[dict]:
        self.get_species(species_key)
        raw = self._graph.get_incompatible_species(species_key)
        return [
            {
                "species_key": item["species"].get("_key", ""),
                "scientific_name": item["species"].get("scientific_name"),
                "common_names": item["species"].get("common_names", []),
                "reason": item.get("reason", ""),
            }
            for item in raw
        ]

    def get_companion_counts(self) -> dict[str, dict[str, int]]:
        # Whole-catalogue aggregate: per-species compatible/incompatible companion
        # counts computed in a single batch AQL (no N+1). Companion edges are
        # global reference data, so no tenant scoping applies.
        return self._graph.get_companion_counts()

    def get_companion_recommendations(self, species_key: SpeciesKey) -> dict:
        self.get_species(species_key)
        engine = CompanionPlantingEngine(self._graph, None, self._repo)  # type: ignore[arg-type]
        return engine.get_companion_recommendations(species_key)
