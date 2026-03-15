from app.common.exceptions import NotFoundError
from app.common.types import FertilizerKey, NutrientPlanKey, NutrientPlanPhaseEntryKey
from app.domain.engines.delivery_channel_engine import DeliveryChannelValidator
from app.domain.engines.nutrient_plan_engine import NutrientPlanValidator, resolve_effective_entry
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.interfaces.nutrient_plan_repository import INutrientPlanRepository
from app.domain.models.nutrient_plan import DeliveryChannel, NutrientPlan, NutrientPlanPhaseEntry


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
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
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
            "name",
            "description",
            "recommended_substrate_type",
            "author",
            "is_template",
            "version",
            "tags",
            "watering_schedule",
            "water_mix_ratio_ro_percent",
            "cycle_restart_from_sequence",
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
            "phase_name",
            "sequence_order",
            "week_start",
            "week_end",
            "npk_ratio",
            "calcium_ppm",
            "magnesium_ppm",
            "notes",
            "delivery_channels",
            "is_recurring",
            "watering_schedule_override",
            "water_mix_ratio_ro_percent",
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

    # ── Channel fertilizer assignment ─────────────────────────────────

    def add_fertilizer_to_channel(
        self,
        entry_key: NutrientPlanPhaseEntryKey,
        channel_id: str,
        fertilizer_key: FertilizerKey,
        ml_per_liter: float,
        optional: bool = False,
    ) -> dict:
        entry = self._repo.get_phase_entry_by_key(entry_key)
        if entry is None:
            raise NotFoundError("NutrientPlanPhaseEntry", entry_key)
        # Validate channel exists
        channel_ids = [ch.channel_id for ch in entry.delivery_channels]
        if channel_id not in channel_ids:
            raise NotFoundError("DeliveryChannel", channel_id)
        fert = self._fert_repo.get_by_key(fertilizer_key)
        if fert is None:
            raise NotFoundError("Fertilizer", fertilizer_key)
        return self._repo.add_fertilizer_to_channel(
            entry_key,
            channel_id,
            fertilizer_key,
            ml_per_liter,
            optional,
        )

    def remove_fertilizer_from_channel(
        self,
        entry_key: NutrientPlanPhaseEntryKey,
        channel_id: str,
        fertilizer_key: FertilizerKey,
    ) -> bool:
        return self._repo.remove_fertilizer_from_channel(
            entry_key,
            channel_id,
            fertilizer_key,
        )

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

        # Channel validation for entries with delivery channels
        channel_validator = DeliveryChannelValidator()
        channel_validations: list[dict] = []
        all_channels_valid = True

        # EC budget per entry — aggregate from channel dosages
        ec_budgets: list[dict] = []

        for entry in entries:
            # Load fertilizers for all channels in this entry
            ferts: dict[str, object] = {}
            if entry.delivery_channels:
                for ch in entry.delivery_channels:
                    for dosage in ch.fertilizer_dosages:
                        if dosage.fertilizer_key not in ferts:
                            fert = self._fert_repo.get_by_key(dosage.fertilizer_key)
                            if fert is not None:
                                ferts[dosage.fertilizer_key] = fert

            # Calculate EC budget for this entry
            calculated_ec = 0.0
            for ch in entry.delivery_channels or []:
                for dosage in ch.fertilizer_dosages:
                    fert = ferts.get(dosage.fertilizer_key)
                    if fert is not None:
                        ec_per_ml = getattr(fert, "ec_contribution_per_ml", 0.0)
                        calculated_ec += dosage.ml_per_liter * ec_per_ml

            # Use the first channel's target_ec as reference, or 0
            target_ec = 0.0
            for ch in entry.delivery_channels or []:
                if ch.target_ec_ms is not None:
                    target_ec = ch.target_ec_ms
                    break

            delta = calculated_ec - target_ec
            ec_valid = target_ec == 0 or abs(delta) < 0.5
            ec_budgets.append(
                {
                    "entry_key": entry.key,
                    "phase_name": entry.phase_name.value,
                    "valid": ec_valid,
                    "target_ec": target_ec,
                    "calculated_ec": round(calculated_ec, 3),
                    "delta": round(delta, 3),
                    "message": "OK" if ec_valid else f"EC delta {delta:+.2f} exceeds tolerance",
                }
            )

            # Channel validation
            if entry.delivery_channels:
                ch_result = channel_validator.validate_channels(
                    entry.delivery_channels,
                    ferts,  # type: ignore[arg-type]
                )
                if not ch_result["valid"]:
                    all_channels_valid = False
                channel_validations.append(
                    {
                        "entry_key": entry.key,
                        "phase_name": entry.phase_name.value,
                        **ch_result,
                    }
                )

        return {
            "completeness": completeness,
            "ec_budgets": ec_budgets,
            "channel_validations": channel_validations,
            "valid": completeness["complete"] and all_channels_valid,
        }

    # ── Current dosages ──────────────────────────────────────────────

    def get_current_dosages(self, plant_key: str, current_phase: str, current_week: int) -> dict | None:
        plan = self._repo.get_plant_plan(plant_key)
        if plan is None:
            return None
        if plan.key is None:
            return None

        entries = self._repo.get_phase_entries(plan.key)
        entry = resolve_effective_entry(
            entries,
            current_phase,
            current_week,
            plan.cycle_restart_from_sequence,
        )
        if entry is None:
            return None

        channels_data = self._build_channels_data(entry.delivery_channels)
        return {
            "plan_key": plan.key,
            "plan_name": plan.name,
            "entry_key": entry.key,
            "phase_name": entry.phase_name.value,
            "channels": channels_data,
        }

    def get_active_channels_for_plan(
        self,
        plan_key: str,
        current_phase: str,
        current_week: int,
    ) -> list[dict]:
        """Return active delivery channels with enriched dosage data.

        Works for any entity that has a nutrient plan assigned (plant or run).
        Returns only enabled channels from the effective phase entry.
        """
        plan = self._repo.get_by_key(plan_key)
        if plan is None or plan.key is None:
            return []

        entries = self._repo.get_phase_entries(plan.key)
        entry = resolve_effective_entry(
            entries,
            current_phase,
            current_week,
            plan.cycle_restart_from_sequence,
        )
        if entry is None:
            return []

        channels_data = self._build_channels_data(entry.delivery_channels)
        # Augment with plan context
        for ch in channels_data:
            ch["plan_key"] = plan.key
            ch["plan_name"] = plan.name
            ch["entry_key"] = entry.key
            ch["phase_name"] = entry.phase_name.value
            ch["week_start"] = entry.week_start
            ch["week_end"] = entry.week_end
        return channels_data

    def _build_channels_data(self, channels: list[DeliveryChannel]) -> list[dict]:
        """Build enriched channel data with fertilizer names and mixing priorities."""
        result = []
        for ch in channels:
            dosages_with_priority = []
            for dosage in ch.fertilizer_dosages:
                fert = self._fert_repo.get_by_key(dosage.fertilizer_key)
                priority = fert.mixing_priority if fert else 50
                dosages_with_priority.append(
                    {
                        "fertilizer_key": dosage.fertilizer_key,
                        "product_name": fert.product_name if fert else "Unknown",
                        "ml_per_liter": dosage.ml_per_liter,
                        "optional": dosage.optional,
                        "mixing_priority": priority,
                    }
                )
            dosages_with_priority.sort(key=lambda d: d["mixing_priority"])
            result.append(
                {
                    "channel_id": ch.channel_id,
                    "label": ch.label,
                    "application_method": ch.application_method.value,
                    "target_ec_ms": ch.target_ec_ms,
                    "target_ph": ch.target_ph,
                    "dosages": dosages_with_priority,
                }
            )
        return result
