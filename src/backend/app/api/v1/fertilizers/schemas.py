from datetime import date, datetime

from pydantic import BaseModel, Field

# ── Fertilizer schemas ──────────────────────────────────────────────

class FertilizerCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=200)
    brand: str = Field(default="", max_length=200)
    fertilizer_type: str
    is_organic: bool = False
    tank_safe: bool = True
    recommended_application: str = "any"
    npk_ratio: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ec_contribution_per_ml: float = Field(default=0.0, ge=0)
    mixing_priority: int = Field(default=50, ge=1, le=100)
    ph_effect: str = "neutral"
    bioavailability: str = "immediate"
    shelf_life_days: int | None = Field(default=None, ge=1)
    storage_temp_min: float | None = None
    storage_temp_max: float | None = None
    notes: str | None = None


class FertilizerUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=200)
    brand: str | None = None
    fertilizer_type: str | None = None
    is_organic: bool | None = None
    tank_safe: bool | None = None
    recommended_application: str | None = None
    npk_ratio: tuple[float, float, float] | None = None
    ec_contribution_per_ml: float | None = Field(default=None, ge=0)
    mixing_priority: int | None = Field(default=None, ge=1, le=100)
    ph_effect: str | None = None
    bioavailability: str | None = None
    shelf_life_days: int | None = Field(default=None, ge=1)
    storage_temp_min: float | None = None
    storage_temp_max: float | None = None
    notes: str | None = None


class FertilizerResponse(BaseModel):
    key: str
    product_name: str
    brand: str
    fertilizer_type: str
    is_organic: bool
    tank_safe: bool
    recommended_application: str
    npk_ratio: tuple[float, float, float]
    ec_contribution_per_ml: float
    mixing_priority: int
    ph_effect: str
    bioavailability: str
    shelf_life_days: int | None
    storage_temp_min: float | None
    storage_temp_max: float | None
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Stock schemas ───────────────────────────────────────────────────

class StockCreate(BaseModel):
    current_volume_ml: float = Field(ge=0)
    purchase_date: date | None = None
    expiry_date: date | None = None
    batch_number: str = ""
    cost_per_liter: float | None = Field(default=None, ge=0)


class StockUpdate(BaseModel):
    current_volume_ml: float | None = Field(default=None, ge=0)
    expiry_date: date | None = None
    batch_number: str | None = None
    cost_per_liter: float | None = Field(default=None, ge=0)


class StockResponse(BaseModel):
    key: str
    fertilizer_key: str
    current_volume_ml: float
    purchase_date: date | None
    expiry_date: date | None
    batch_number: str
    cost_per_liter: float | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Incompatibility schemas ─────────────────────────────────────────

class IncompatibilityCreate(BaseModel):
    other_key: str
    reason: str = ""
    severity: str = "warning"


class IncompatibilityResponse(BaseModel):
    fertilizer_key: str
    product_name: str | None
    reason: str
    severity: str
