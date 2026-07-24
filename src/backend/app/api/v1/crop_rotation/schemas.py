from pydantic import BaseModel


class RotationSuccessorSet(BaseModel):
    from_family_key: str
    to_family_key: str
    wait_years: int = 3
    benefit_score: float = 0.0
    benefit_reason: str = ""


class RotationSuccessorResponse(BaseModel):
    family_key: str
    name: str | None = None
    # German family common name (e.g. "Nachtschattengewächse") passed through from
    # the family vertex so the UI can lead with a layperson-facing name and keep
    # the scientific family name as secondary context (REQ-567/A). Empty when the
    # family has no curated common name.
    common_name_de: str = ""
    common_name_en: str = ""
    # Raw rotation-category code (e.g. "legume"); the UI maps it to a translated,
    # plain-language label so no raw code ever reaches the screen (REQ-567/A).
    rotation_category: str = ""
    wait_years: int = 1
    benefit_score: float = 0.0
    benefit_reason: str = ""


class RotationSuccessorCreatedResponse(BaseModel):
    """Acknowledgement returned after a rotation-successor edge is written."""

    status: str
