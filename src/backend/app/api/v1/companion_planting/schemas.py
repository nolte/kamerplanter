from pydantic import BaseModel


class CompatibilitySet(BaseModel):
    from_species_key: str
    to_species_key: str
    score: float = 1.0


class IncompatibilitySet(BaseModel):
    from_species_key: str
    to_species_key: str
    reason: str = ""


class CompatibleSpeciesResponse(BaseModel):
    species_key: str
    scientific_name: str | None = None
    # Full language-mixed common-name list from the species document (DE first by
    # seed convention). Passed through verbatim so the UI can render a
    # layperson-facing name with the scientific name as secondary context.
    common_names: list[str] = []
    score: float


class IncompatibleSpeciesResponse(BaseModel):
    species_key: str
    scientific_name: str | None = None
    common_names: list[str] = []
    reason: str = ""


class SpeciesCompanionCounts(BaseModel):
    compatible: int = 0
    incompatible: int = 0
