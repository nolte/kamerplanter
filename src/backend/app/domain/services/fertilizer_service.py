from pydantic import ValidationError as PydanticValidationError

from app.common.exceptions import NotFoundError, ValidationError
from app.common.types import FertilizerKey, FertilizerStockKey
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.models.fertilizer import Fertilizer, FertilizerStock


class FertilizerService:
    def __init__(self, repo: IFertilizerRepository) -> None:
        self._repo = repo

    # ── Fertilizer CRUD ──────────────────────────────────────────────

    def list_fertilizers(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
    ) -> tuple[list[Fertilizer], int]:
        return self._repo.get_all(offset, limit, filters)

    def get_fertilizer(self, key: FertilizerKey) -> Fertilizer:
        fert = self._repo.get_by_key(key)
        if fert is None:
            raise NotFoundError("Fertilizer", key)
        return fert

    def create_fertilizer(self, fertilizer: Fertilizer) -> Fertilizer:
        return self._repo.create(fertilizer)

    def update_fertilizer(self, key: FertilizerKey, data: dict) -> Fertilizer:
        existing = self.get_fertilizer(key)
        allowed_fields = {
            "product_name",
            "brand",
            "fertilizer_type",
            "is_organic",
            "tank_safe",
            "recommended_application",
            "npk_ratio",
            "ec_contribution_per_ml",
            "mixing_priority",
            "ph_effect",
            "bioavailability",
            "shelf_life_days",
            "storage_temp_min",
            "storage_temp_max",
            "notes",
        }
        merged = existing.model_dump()
        for field, value in data.items():
            if field in allowed_fields:
                merged[field] = value
        try:
            validated = Fertilizer.model_validate(merged)
        except PydanticValidationError as exc:
            raise ValidationError(
                message=str(exc.errors()[0]["msg"]),
                details=[
                    {"field": ".".join(str(loc) for loc in e["loc"]), "reason": e["msg"], "code": e["type"]}
                    for e in exc.errors()
                ],
            ) from exc
        return self._repo.update(key, validated)

    def delete_fertilizer(self, key: FertilizerKey) -> bool:
        self.get_fertilizer(key)  # ensure exists
        return self._repo.delete(key)

    # ── Stock CRUD ───────────────────────────────────────────────────

    def create_stock(self, fertilizer_key: FertilizerKey, stock: FertilizerStock) -> FertilizerStock:
        self.get_fertilizer(fertilizer_key)
        stock.fertilizer_key = fertilizer_key
        return self._repo.create_stock(stock)

    def get_stocks(self, fertilizer_key: FertilizerKey) -> list[FertilizerStock]:
        self.get_fertilizer(fertilizer_key)
        return self._repo.get_stocks(fertilizer_key)

    def update_stock(self, key: FertilizerStockKey, data: dict) -> FertilizerStock:
        # We need to find the stock first — stocks don't have a dedicated get
        # Use repository directly
        stocks_col = getattr(self._repo, "_db", None)
        if stocks_col is None:
            raise NotFoundError("FertilizerStock", key)
        stock = FertilizerStock(fertilizer_key="temp", current_volume_ml=0)
        allowed_fields = {"current_volume_ml", "expiry_date", "batch_number", "cost_per_liter"}
        for field, value in data.items():
            if field in allowed_fields:
                setattr(stock, field, value)
        return self._repo.update_stock(key, stock)

    def delete_stock(self, key: FertilizerStockKey) -> bool:
        return self._repo.delete_stock(key)

    # ── Incompatibility ──────────────────────────────────────────────

    def add_incompatibility(
        self,
        key_a: FertilizerKey,
        key_b: FertilizerKey,
        reason: str,
        severity: str,
    ) -> dict:
        self.get_fertilizer(key_a)
        self.get_fertilizer(key_b)
        return self._repo.add_incompatibility(key_a, key_b, reason, severity)

    def get_incompatibilities(self, key: FertilizerKey) -> list[dict]:
        self.get_fertilizer(key)
        return self._repo.get_incompatibilities(key)

    def remove_incompatibility(self, key_a: FertilizerKey, key_b: FertilizerKey) -> bool:
        return self._repo.remove_incompatibility(key_a, key_b)

    # ── Reverse lookup ─────────────────────────────────────────────────

    def get_nutrient_plan_usage(self, key: FertilizerKey) -> list[dict]:
        self.get_fertilizer(key)  # ensure exists
        return self._repo.get_nutrient_plan_usage(key)
