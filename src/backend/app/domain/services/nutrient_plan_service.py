from app.common.exceptions import NotFoundError
from app.common.types import FertilizerKey, NutrientPlanKey, NutrientPlanPhaseEntryKey
from app.domain.engines.nutrient_plan_engine import NutrientPlanValidator
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.interfaces.nutrient_plan_repository import INutrientPlanRepository
from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry


class NutrientPlanService:
    def __init__(
        self,
        repo: INutrientPlanRepository,
        fert_repo: IFertilizerRepository,
        validator: NutrientPlanValidator,
    ) -> None:
        self._repo = repo
        self._fert_repo = fert_repo
        self._validator = validator

    # ── Plan CRUD ────────────────────────────────────────────────────

    def list_plans(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None,
    ) -> tuple[list[NutrientPlan], int]:
        return self._repo.get_all(offset, limit, filters)

    def get_plan(self, key: NutrientPlanKey) -> NutrientPlan:
        plan = self._repo.get_by_key(key)
        if plan is None:
            raise NotFoundError("NutrientPlan", key)
        return plan

    def create_plan(self, plan: NutrientPlan) -> NutrientPlan:
        return self._repo.create(plan)

    def update_plan(self, key: NutrientPlanKey, data: dict) -> NutrientPlan:
        existing = self.get_plan(key)
        allowed_fields = {
            "name", "description", "recommended_substrate_type",
            "author", "is_template", "version", "tags",
        }
        for field, value in data.items():
            if field in allowed_fields:
                setattr(existing, field, value)
        return self._repo.update(key, existing)

    def delete_plan(self, key: NutrientPlanKey) -> bool:
        self.get_plan(key)
        return self._repo.delete(key)

    # ── Phase entries ────────────────────────────────────────────────

    def create_phase_entry(self, plan_key: NutrientPlanKey, entry: NutrientPlanPhaseEntry) -> NutrientPlanPhaseEntry:
        self.get_plan(plan_key)
        entry.plan_key = plan_key
        return self._repo.create_phase_entry(entry)

    def get_phase_entries(self, plan_key: NutrientPlanKey) -> list[NutrientPlanPhaseEntry]:
        self.get_plan(plan_key)
        return self._repo.get_phase_entries(plan_key)

    def update_phase_entry(self, key: NutrientPlanPhaseEntryKey, data: dict) -> NutrientPlanPhaseEntry:
        existing = self._repo.get_phase_entry_by_key(key)
        if existing is None:
            raise NotFoundError("NutrientPlanPhaseEntry", key)
        allowed_fields = {
            "phase_name", "sequence_order", "week_start", "week_end",
            "npk_ratio", "target_ec_ms", "target_ph", "calcium_ppm",
            "magnesium_ppm", "feeding_frequency_per_week",
            "volume_per_feeding_liters", "notes", "fertilizer_dosages",
        }
        for field, value in data.items():
            if field in allowed_fields:
                setattr(existing, field, value)
        return self._repo.update_phase_entry(key, existing)

    def delete_phase_entry(self, key: NutrientPlanPhaseEntryKey) -> bool:
        existing = self._repo.get_phase_entry_by_key(key)
        if existing is None:
            raise NotFoundError("NutrientPlanPhaseEntry", key)
        return self._repo.delete_phase_entry(key)

    # ── Fertilizer assignment ────────────────────────────────────────

    def add_fertilizer_to_entry(
        self, entry_key: NutrientPlanPhaseEntryKey, fertilizer_key: FertilizerKey,
        ml_per_liter: float, optional: bool = False,
    ) -> dict:
        entry = self._repo.get_phase_entry_by_key(entry_key)
        if entry is None:
            raise NotFoundError("NutrientPlanPhaseEntry", entry_key)
        fert = self._fert_repo.get_by_key(fertilizer_key)
        if fert is None:
            raise NotFoundError("Fertilizer", fertilizer_key)
        return self._repo.add_fertilizer_to_entry(entry_key, fertilizer_key, ml_per_liter, optional)

    def remove_fertilizer_from_entry(
        self, entry_key: NutrientPlanPhaseEntryKey, fertilizer_key: FertilizerKey,
    ) -> bool:
        return self._repo.remove_fertilizer_from_entry(entry_key, fertilizer_key)

    # ── Plant assignment ─────────────────────────────────────────────

    def assign_to_plant(self, plant_key: str, plan_key: NutrientPlanKey, assigned_by: str = "") -> dict:
        self.get_plan(plan_key)
        return self._repo.assign_to_plant(plant_key, plan_key, assigned_by)

    def get_plant_plan(self, plant_key: str) -> NutrientPlan | None:
        return self._repo.get_plant_plan(plant_key)

    def remove_plant_plan(self, plant_key: str) -> bool:
        return self._repo.remove_plant_plan(plant_key)

    # ── Clone ────────────────────────────────────────────────────────

    def clone_plan(self, source_key: NutrientPlanKey, new_name: str, author: str = "") -> NutrientPlan:
        self.get_plan(source_key)
        return self._repo.clone(source_key, new_name, author)

    # ── Validation ───────────────────────────────────────────────────

    def validate_plan(self, plan_key: NutrientPlanKey) -> dict:
        self.get_plan(plan_key)
        entries = self._repo.get_phase_entries(plan_key)

        completeness = self._validator.validate_completeness(entries)

        # EC budget check per entry
        ec_results = []
        for entry in entries:
            # Load fertilizers referenced in dosages
            ferts: dict[str, object] = {}
            for dosage in entry.fertilizer_dosages:
                fert = self._fert_repo.get_by_key(dosage.fertilizer_key)
                if fert is not None:
                    ferts[dosage.fertilizer_key] = fert
            ec_result = self._validator.validate_ec_budget(entry, ferts)  # type: ignore[arg-type]
            ec_result["entry_key"] = entry.key
            ec_result["phase_name"] = entry.phase_name.value
            ec_results.append(ec_result)

        all_ec_valid = all(r["valid"] for r in ec_results)

        return {
            "completeness": completeness,
            "ec_budgets": ec_results,
            "valid": completeness["complete"] and all_ec_valid,
        }

    # ── Current dosages ──────────────────────────────────────────────

    def get_current_dosages(self, plant_key: str, current_phase: str, current_week: int) -> dict | None:
        plan = self._repo.get_plant_plan(plant_key)
        if plan is None:
            return None
        if plan.key is None:
            return None

        entries = self._repo.get_phase_entries(plan.key)
        # Find matching entry for current phase and week
        for entry in entries:
            if (
                entry.phase_name.value == current_phase
                and entry.week_start <= current_week <= entry.week_end
            ):
                # Sort dosages by fertilizer mixing priority
                dosages_with_priority = []
                for dosage in entry.fertilizer_dosages:
                    fert = self._fert_repo.get_by_key(dosage.fertilizer_key)
                    priority = fert.mixing_priority if fert else 50
                    dosages_with_priority.append({
                        "fertilizer_key": dosage.fertilizer_key,
                        "product_name": fert.product_name if fert else "Unknown",
                        "ml_per_liter": dosage.ml_per_liter,
                        "optional": dosage.optional,
                        "mixing_priority": priority,
                    })
                dosages_with_priority.sort(key=lambda d: d["mixing_priority"])

                return {
                    "plan_key": plan.key,
                    "plan_name": plan.name,
                    "entry_key": entry.key,
                    "phase_name": entry.phase_name.value,
                    "target_ec_ms": entry.target_ec_ms,
                    "target_ph": entry.target_ph,
                    "dosages": dosages_with_priority,
                }

        return None
