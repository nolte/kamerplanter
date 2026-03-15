from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.common.enums import SiteType, StarterKitDifficulty


class StarterKitResponse(BaseModel):
    key: str
    kit_id: str
    name_i18n: dict[str, str]
    description_i18n: dict[str, str]
    difficulty: StarterKitDifficulty
    icon: str
    plant_count_suggestion: int
    site_type: SiteType
    species_keys: list[str]
    cultivar_keys: list[str]
    toxicity_warning: bool
    workflow_template_keys: list[str]
    includes_nutrient_plan: bool
    tags: list[str]
    sort_order: int


class ApplyKitRequest(BaseModel):
    site_name: str = Field(min_length=1, max_length=200)
    plant_count: int = Field(default=3, ge=1, le=50)
