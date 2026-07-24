from pydantic import BaseModel, Field


class PestRiskSet(BaseModel):
    a_family_key: str
    b_family_key: str
    shared_pests: list[str] = Field(default_factory=list)
    shared_diseases: list[str] = Field(default_factory=list)
    risk_level: str = "medium"


class FamilyCompatibleSet(BaseModel):
    a_family_key: str
    b_family_key: str
    benefit_type: str = ""
    compatibility_score: float = 0.0
    notes: str = ""


class FamilyIncompatibleSet(BaseModel):
    a_family_key: str
    b_family_key: str
    reason: str = ""
    severity: str = "moderate"


class FamilyRelationshipCreatedResponse(BaseModel):
    """Acknowledgement returned after a family-relationship edge is written."""

    status: str


class FamilyPestRiskResponse(BaseModel):
    """A family sharing pest/disease risk with the queried family."""

    family_key: str
    name: str | None = None
    shared_pests: list[str] = Field(default_factory=list)
    shared_diseases: list[str] = Field(default_factory=list)
    risk_level: str = "low"


class FamilyCompatibleResponse(BaseModel):
    """A family that is a beneficial companion of the queried family."""

    family_key: str
    name: str | None = None
    benefit_type: str = ""
    compatibility_score: float = 0.0
    notes: str = ""


class FamilyIncompatibleResponse(BaseModel):
    """A family that is an incompatible neighbour of the queried family."""

    family_key: str
    name: str | None = None
    reason: str = ""
    severity: str = "moderate"
