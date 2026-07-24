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


class CompanionEdgeCreatedResponse(BaseModel):
    """Acknowledgement returned after a companion edge is written."""

    status: str


class CompanionRecommendationMatch(BaseModel):
    """One recommended companion species (species- or family-level match)."""

    species_key: str
    scientific_name: str | None = None
    score: float
    match_level: str
    # Only present on family-level fallback matches (species-level matches omit it).
    benefit_type: str | None = None


class CompanionRecommendationsResponse(BaseModel):
    """Companion recommendations with the level at which they were resolved."""

    matches: list[CompanionRecommendationMatch]
    match_level: str
