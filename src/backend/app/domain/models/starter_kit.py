from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import SiteType, StarterKitDifficulty


class StarterKit(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    kit_id: str
    name_i18n: dict[str, str] = Field(default_factory=dict)
    description_i18n: dict[str, str] = Field(default_factory=dict)
    difficulty: StarterKitDifficulty = StarterKitDifficulty.BEGINNER
    icon: str = ""
    plant_count_suggestion: int = Field(default=3, ge=1, le=50)
    site_type: SiteType = SiteType.INDOOR
    species_keys: list[str] = Field(default_factory=list)
    cultivar_keys: list[str] = Field(default_factory=list)
    toxicity_warning: bool = False
    workflow_template_keys: list[str] = Field(default_factory=list)
    includes_nutrient_plan: bool = False
    nutrient_plan_keys: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    sort_order: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
