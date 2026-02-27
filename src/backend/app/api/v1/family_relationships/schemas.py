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
