from pydantic import BaseModel, Field


class FavoriteCreateRequest(BaseModel):
    target_key: str = Field(min_length=1)
    source: str = "manual"


class FavoriteResponse(BaseModel):
    key: str
    target_key: str
    target_type: str
    source: str
    cascade_from_key: str | None = None
    favorited_at: str


class NutrientPlanFertilizerInfo(BaseModel):
    key: str
    product_name: str
    brand: str | None = None


class NutrientPlanMatchResponse(BaseModel):
    plan_key: str
    name: str
    description: str | None = None
    substrate_type: str | None = None
    fertilizer_count: int = 0
    fertilizers: list[NutrientPlanFertilizerInfo] = []
