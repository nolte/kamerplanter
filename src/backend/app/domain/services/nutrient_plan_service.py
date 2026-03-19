from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.common.types import FertilizerKey, NutrientPlanKey, NutrientPlanPhaseEntryKey
from app.domain.engines.delivery_channel_engine import DeliveryChannelValidator
from app.domain.engines.dosage_calculation_engine import (
    DosageCalculationEngine,
    DosageCalculationInput,
    DosageCalculationResult,
)
from app.domain.engines.nutrient_plan_engine import NutrientPlanValidator, resolve_effective_entry
from app.domain.engines.water_mix_engine import WaterMixCalculator
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.interfaces.nutrient_plan_repository import INutrientPlanRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import DeliveryChannel, NutrientPlan, NutrientPlanPhaseEntry
from app.domain.models.site import RoWaterProfile


class NutrientPlanService:
    def __init__(
        self,
        repo: INutrientPlanRepository,
        fert_repo: IFertilizerRepository,
        validator: NutrientPlanValidator,
        site_repo: ISiteRepository | None = None,
    ) -> None:
        self._repo = repo
        self._fert_repo = fert_repo
        self._validator = validator
        self._site_repo = site_repo
        self._water_calc = WaterMixCalculator()
        self._dosage_engine = DosageCalculationEngine()

    # ── Plan CRUD ────────────────────────────────────────────────────

    def list_plans(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        tenant_key: str = "",
    ) -> tuple[list[NutrientPlan], int]:
        return self._repo.get_all(offset, limit, filters, tenant_key=tenant_key)

    def get_plan(self, key: NutrientPlanKey, tenant_key: str = "") -> NutrientPlan:
        plan = self._repo.get_by_key(key)
        if plan is None:
            raise NotFoundError("NutrientPlan", key)
        if tenant_key:
            verify_tenant_ownership(plan, tenant_key, "NutrientPlan")
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
            "target_ec_ms",
            "target_calcium_ppm",
            "target_magnesium_ppm",
            "reference_base_ec",
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

    # ── Dosage calculation (REQ-004 §4b) ────────────────────────────

    def calculate_dosages(
        self,
        tenant_key: str,
        plan_key: NutrientPlanKey,
        sequence_order: int,
        site_key: str,
        volume_liters: float = 10.0,
        channel_id: str | None = None,
        ro_percent_override: int | None = None,
    ) -> DosageCalculationResult:
        """Calculate runtime dosages for a phase entry based on site water profile.

        Orchestrates the 3-stage pipeline:
        1. WaterMixCalculator -> effective water profile
        2. CalMag correction -> fill mineral gaps
        3. EC budget scaling -> scale dosages proportionally
        """
        if self._site_repo is None:
            raise ValidationError("Site repository not configured.")

        # Load plan with tenant isolation
        plan = self.get_plan(plan_key, tenant_key=tenant_key)

        # Find phase entry by sequence_order
        entries = self._repo.get_phase_entries(plan_key)
        entry = None
        for e in entries:
            if e.sequence_order == sequence_order:
                entry = e
                break
        if entry is None:
            raise NotFoundError("NutrientPlanPhaseEntry", f"sequence_order={sequence_order}")

        # Load site with tenant isolation
        site = self._site_repo.get_site_by_key(site_key)
        if site is None:
            raise NotFoundError("Site", site_key)
        if tenant_key and hasattr(site, "tenant_key") and site.tenant_key != tenant_key:
            raise NotFoundError("Site", site_key)

        # Extract water profiles; use RO defaults if system is enabled but no profile stored
        tap_water = None
        ro_water = None
        if site.water_config:
            tap_water = site.water_config.tap_water_profile
            if site.water_config.has_ro_system:
                ro_water = site.water_config.ro_water_profile or RoWaterProfile()

        # Load all fertilizer products referenced in the channel
        fertilizer_lookup = self._load_fertilizer_lookup(entry)

        # Find CalMag product
        calmag_product = self._find_calmag_product()

        # Determine substrate type
        substrate_type = ""
        if plan.recommended_substrate_type is not None:
            substrate_type = (
                plan.recommended_substrate_type.value
                if hasattr(plan.recommended_substrate_type, "value")
                else str(plan.recommended_substrate_type)
            )
        if not substrate_type:
            substrate_type = "coco"

        # Build input and run engine
        calc_input = DosageCalculationInput(
            phase_entry=entry,
            channel_id=channel_id,
            volume_liters=volume_liters,
            tap_water=tap_water,
            ro_water=ro_water,
            ro_percent_override=ro_percent_override,
            substrate_type=substrate_type,
            calmag_product=calmag_product,
            fertilizer_lookup=fertilizer_lookup,
        )

        return self._dosage_engine.calculate(calc_input)

    def _load_fertilizer_lookup(self, entry: NutrientPlanPhaseEntry) -> dict[str, Fertilizer]:
        """Load all fertilizer products referenced in a phase entry's channels."""
        lookup: dict[str, Fertilizer] = {}
        for ch in entry.delivery_channels:
            for dosage in ch.fertilizer_dosages:
                if dosage.fertilizer_key not in lookup:
                    fert = self._fert_repo.get_by_key(dosage.fertilizer_key)
                    if fert is not None:
                        lookup[dosage.fertilizer_key] = fert
        return lookup

    def _find_calmag_product(self) -> Fertilizer | None:
        """Find a CalMag supplement product in the fertilizer catalog."""
        # Search for supplement products with "CalMag" in the name
        ferts, _ = self._fert_repo.get_all(offset=0, limit=100, filters={"fertilizer_type": "supplement"})
        for fert in ferts:
            if "calmag" in fert.product_name.lower():
                return fert
        return None

    # ── Water mix recommendation ──────────────────────────────────────

    def get_water_mix_recommendation(
        self,
        tenant_key: str,
        plan_key: NutrientPlanKey,
        sequence_order: int,
        site_key: str,
        substrate_type_override: str | None = None,
    ) -> dict:
        """Calculate optimal RO/tap water mix ratio for a phase entry.

        Loads the nutrient plan, phase entry, and site water config, then
        delegates to WaterMixCalculator.recommend_mix_ratio().

        Raises ValidationError if the site has no RO system configured.
        """
        if self._site_repo is None:
            raise ValidationError("Site repository not configured.")

        # Load plan with tenant isolation
        plan = self.get_plan(plan_key, tenant_key=tenant_key)

        # Load entries and find matching sequence_order
        entries = self._repo.get_phase_entries(plan_key)
        entry = None
        for e in entries:
            if e.sequence_order == sequence_order:
                entry = e
                break
        if entry is None:
            raise NotFoundError("NutrientPlanPhaseEntry", f"sequence_order={sequence_order}")

        # Load site with tenant isolation
        site = self._site_repo.get_site_by_key(site_key)
        if site is None:
            raise NotFoundError("Site", site_key)
        if tenant_key and hasattr(site, "tenant_key") and site.tenant_key != tenant_key:
            raise NotFoundError("Site", site_key)

        # Validate RO system
        if site.water_config is None or not site.water_config.has_ro_system:
            raise ValidationError("Site does not have an RO system configured.")
        if site.water_config.tap_water_profile is None:
            raise ValidationError("Site does not have a tap water profile configured.")

        # Use stored RO profile or default values for a standard RO membrane
        ro = site.water_config.ro_water_profile or RoWaterProfile()

        # Determine target EC from delivery channels or entry
        target_ec = 0.0
        for ch in entry.delivery_channels or []:
            if ch.target_ec_ms is not None:
                target_ec = ch.target_ec_ms
                break

        if target_ec <= 0:
            raise ValidationError(
                "No target EC configured for this phase entry. Set target_ec_ms on a delivery channel."
            )

        # Determine substrate type
        substrate_type = substrate_type_override or ""
        if not substrate_type and plan.recommended_substrate_type is not None:
            substrate_type = (
                plan.recommended_substrate_type.value
                if hasattr(plan.recommended_substrate_type, "value")
                else str(plan.recommended_substrate_type)
            )
        if not substrate_type:
            substrate_type = "coco"  # sensible default

        # Target Ca/Mg from phase entry
        target_ca = entry.calcium_ppm or 0.0
        target_mg = entry.magnesium_ppm or 0.0

        phase_name_str = (
            entry.phase_name.value
            if hasattr(entry.phase_name, "value")
            else str(entry.phase_name)
        )
        recommendation = self._water_calc.recommend_mix_ratio(
            tap=site.water_config.tap_water_profile,
            ro=ro,
            target_ec_ms=target_ec,
            substrate_type=substrate_type,
            target_ca_ppm=target_ca,
            target_mg_ppm=target_mg,
            phase_name=phase_name_str,
        )

        return {
            "recommendation": recommendation.model_dump(),
            "plan_name": plan.name,
            "plan_key": plan.key,
            "phase_name": entry.phase_name.value,
            "sequence_order": entry.sequence_order,
            "site_name": site.name,
            "site_key": site.key,
        }

    def get_water_mix_recommendations_batch(
        self,
        tenant_key: str,
        plan_key: NutrientPlanKey,
        site_key: str,
        substrate_type_override: str | None = None,
    ) -> dict:
        """Calculate optimal RO/tap water mix ratio for ALL phase entries of a plan.

        Loads plan, entries, and site once, then iterates all entries that have
        delivery channels with a target EC > 0. Entries without target EC are
        silently skipped.

        Returns empty recommendations list if the site has no RO system.
        """
        if self._site_repo is None:
            raise ValidationError("Site repository not configured.")

        # Load plan with tenant isolation
        plan = self.get_plan(plan_key, tenant_key=tenant_key)

        # Load site with tenant isolation
        site = self._site_repo.get_site_by_key(site_key)
        if site is None:
            raise NotFoundError("Site", site_key)
        if tenant_key and hasattr(site, "tenant_key") and site.tenant_key != tenant_key:
            raise NotFoundError("Site", site_key)

        # If no RO system or no tap water profile, return empty recommendations
        if (
            site.water_config is None
            or not site.water_config.has_ro_system
            or site.water_config.tap_water_profile is None
        ):
            return {
                "recommendations": [],
                "site_name": site.name,
                "site_key": site.key,
                "plan_name": plan.name,
                "plan_key": plan.key,
            }

        tap = site.water_config.tap_water_profile
        # Use stored RO profile or default values for a standard RO membrane
        ro = site.water_config.ro_water_profile or RoWaterProfile()

        # Determine substrate type once
        substrate_type = substrate_type_override or ""
        if not substrate_type and plan.recommended_substrate_type is not None:
            substrate_type = (
                plan.recommended_substrate_type.value
                if hasattr(plan.recommended_substrate_type, "value")
                else str(plan.recommended_substrate_type)
            )
        if not substrate_type:
            substrate_type = "coco"

        # Load all entries once
        entries = self._repo.get_phase_entries(plan_key)

        # Build target EC per entry; entries without explicit EC inherit from
        # the nearest neighbour (by sequence_order) so every phase gets a
        # water-mix recommendation.
        def _extract_target_ec(entry) -> float:  # noqa: ANN001
            for ch in entry.delivery_channels or []:
                if ch.target_ec_ms is not None and ch.target_ec_ms > 0:
                    return ch.target_ec_ms
            return 0.0

        sorted_entries = sorted(entries, key=lambda e: e.sequence_order)
        entry_ecs: dict[int, float] = {}
        for e in sorted_entries:
            ec = _extract_target_ec(e)
            if ec > 0:
                entry_ecs[e.sequence_order] = ec

        # Fill gaps: propagate from nearest neighbour with a known EC
        if entry_ecs:
            known_seqs = sorted(entry_ecs.keys())
            for e in sorted_entries:
                if e.sequence_order in entry_ecs:
                    continue
                # Find closest sequence_order that has a target EC
                closest = min(known_seqs, key=lambda s: abs(s - e.sequence_order))
                entry_ecs[e.sequence_order] = entry_ecs[closest]

        recommendations: list[dict] = []
        for entry in sorted_entries:
            target_ec = entry_ecs.get(entry.sequence_order, 0.0)
            if target_ec <= 0:
                continue

            target_ca = entry.calcium_ppm or 0.0
            target_mg = entry.magnesium_ppm or 0.0

            phase_name_str = (
                entry.phase_name.value
                if hasattr(entry.phase_name, "value")
                else str(entry.phase_name)
            )
            recommendation = self._water_calc.recommend_mix_ratio(
                tap=tap,
                ro=ro,
                target_ec_ms=target_ec,
                substrate_type=substrate_type,
                target_ca_ppm=target_ca,
                target_mg_ppm=target_mg,
                phase_name=phase_name_str,
            )

            recommendations.append(
                {
                    "recommendation": recommendation.model_dump(),
                    "plan_name": plan.name,
                    "plan_key": plan.key,
                    "phase_name": entry.phase_name.value,
                    "sequence_order": entry.sequence_order,
                    "site_name": site.name,
                    "site_key": site.key,
                }
            )

        return {
            "recommendations": recommendations,
            "site_name": site.name,
            "site_key": site.key,
            "plan_name": plan.name,
            "plan_key": plan.key,
        }
