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
    score: float
