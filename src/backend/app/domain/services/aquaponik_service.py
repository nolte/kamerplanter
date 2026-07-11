"""REQ-026 Aquaponics service.

Coordinates the fish/plant loop: system + fish-stock lifecycle, immutable water
tests (with derived free ammonia), feeding recommendations, cycling detection,
nutrient-deficiency analysis and fish-health / safety evaluation.

The service owns the domain engines (:mod:`app.domain.engines.aquaponics_engine`)
and reuses the existing :class:`HydroSystemMonitor` (via the deficiency analyzer)
for grow-bed nutrient-strength grading. All reads/writes are tenant-scoped:
system ownership is verified against ``tenant_key`` before any child access,
preventing cross-tenant leakage (SEC-B4).
"""

from __future__ import annotations

from typing import Any

from app.common.enums import AquaponicSystemType, CyclingStatus
from app.common.exceptions import ResourceInUseError, ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.data_access.arango.aquaponik_repository import ArangoAquaponikRepository
from app.domain.engines.aquaponics_engine import (
    BiofilterManager,
    CyclingProgress,
    DeficiencyReport,
    FeedingRecommendation,
    FishHealthMonitor,
    HealthAlert,
    NitrogenCycleEngine,
    NutrientDeficiencyAnalyzer,
    StockingDensityCalculator,
    StockingValidation,
    WaterQualityEvaluation,
)
from app.domain.engines.aquaponics_engine import (
    FeedingRateCalculator as _FeedingRateCalculator,
)
from app.domain.models.aquaponik import (
    AquaponicSystem,
    FishFeedingEvent,
    FishSpecies,
    FishStock,
    SupplementationEvent,
    WaterTest,
)


class AquaponikService:
    """Business logic for REQ-026 aquaponic systems."""

    def __init__(
        self,
        repo: ArangoAquaponikRepository,
        nitrogen_engine: NitrogenCycleEngine | None = None,
        feeding_calculator: _FeedingRateCalculator | None = None,
        stocking_calculator: StockingDensityCalculator | None = None,
        deficiency_analyzer: NutrientDeficiencyAnalyzer | None = None,
        biofilter_manager: BiofilterManager | None = None,
        health_monitor: FishHealthMonitor | None = None,
    ) -> None:
        self._repo = repo
        self._nitrogen = nitrogen_engine or NitrogenCycleEngine()
        self._feeding = feeding_calculator or _FeedingRateCalculator()
        self._stocking = stocking_calculator or StockingDensityCalculator()
        self._deficiency = deficiency_analyzer or NutrientDeficiencyAnalyzer()
        self._biofilter = biofilter_manager or BiofilterManager(self._feeding)
        self._health = health_monitor or FishHealthMonitor(self._nitrogen)

    # ── FishSpecies (global) ────────────────────────────────────────────

    def list_species(self, temperature_zone: str | None = None, feed_type: str | None = None) -> list[FishSpecies]:
        return self._repo.list_species(temperature_zone, feed_type)

    def get_species(self, key: str) -> FishSpecies:
        return self._repo.get_species_or_raise(key)

    def get_compatible_plants(self, key: str) -> dict[str, Any]:
        species = self._repo.get_species_or_raise(key)
        return {
            "fish_species_key": species.key,
            "fish_common_name_de": species.common_name_de,
            "temperature_zone": species.temperature_zone.value,
            "compatible": self._repo.get_compatible_plants(key, compatible=True),
            "incompatible": self._repo.get_compatible_plants(key, compatible=False),
        }

    def list_species_by_zone(self, zone: str) -> list[FishSpecies]:
        return self._repo.list_species(temperature_zone=zone)

    # ── AquaponicSystem CRUD ────────────────────────────────────────────

    def list_systems(self, tenant_key: str) -> list[AquaponicSystem]:
        return self._repo.list_systems(tenant_key)

    def get_system(self, key: str, tenant_key: str) -> AquaponicSystem:
        system = self._repo.get_or_raise(key)
        verify_tenant_ownership(system, tenant_key, "AquaponicSystem")
        return system

    def create_system(self, system: AquaponicSystem) -> AquaponicSystem:
        self._validate_system_config(system)
        return self._repo.create_system(system)

    def update_system(self, key: str, tenant_key: str, data: dict[str, Any]) -> AquaponicSystem:
        system = self.get_system(key, tenant_key)
        updated = system.model_copy(update=data)
        self._validate_system_config(updated)
        return self._repo.update(key, updated)

    def delete_system(self, key: str, tenant_key: str) -> None:
        self.get_system(key, tenant_key)
        stocks = self._repo.list_stocks(key, tenant_key)
        if any(stock.count > 0 for stock in stocks):
            raise ResourceInUseError(
                "AquaponicSystem", "system still holds a live fish stock (document mortality/harvest first)"
            )
        self._repo.delete_system(key)

    def set_cycling_status(self, key: str, tenant_key: str, status: CyclingStatus) -> AquaponicSystem:
        system = self.get_system(key, tenant_key)
        updated = system.model_copy(update={"cycling_status": status})
        return self._repo.update(key, updated)

    def _validate_system_config(self, system: AquaponicSystem) -> None:
        if system.system_type != AquaponicSystemType.MEDIA_BED and system.biofilter_type is None:
            raise ValidationError(
                "DWC/NFT/Hybrid/Wicking-Bed benötigen einen separaten Biofilter (biofilter_type). "
                "Nur Media-Bed hat einen integrierten Biofilter."
            )
        if system.has_clarifier and system.clarifier_type is None:
            raise ValidationError("Clarifier-Typ muss angegeben werden, wenn has_clarifier=true.")
        if system.ph_target_min > system.ph_target_max:
            raise ValidationError("ph_target_min darf nicht größer als ph_target_max sein.")

    # ── FishStock ───────────────────────────────────────────────────────

    def list_stocks(self, system_key: str, tenant_key: str) -> list[FishStock]:
        self.get_system(system_key, tenant_key)
        return self._repo.list_stocks(system_key, tenant_key)

    def get_stock(self, system_key: str, stock_key: str, tenant_key: str) -> FishStock:
        self.get_system(system_key, tenant_key)
        stock = self._repo.get_stock_or_raise(stock_key)
        verify_tenant_ownership(stock, tenant_key, "FishStock")
        if stock.system_key != system_key:
            raise ValidationError("FishStock gehört nicht zu diesem System.")
        return stock

    def create_stock(self, system_key: str, tenant_key: str, stock: FishStock) -> FishStock:
        self.get_system(system_key, tenant_key)
        # Species must exist (also validates the reference is resolvable).
        self._repo.get_species_or_raise(stock.species_key)
        stock.system_key = system_key
        stock.tenant_key = tenant_key
        if stock.initial_count == 0:
            stock.initial_count = stock.count
        return self._repo.create_stock(stock)

    def update_stock(self, system_key: str, stock_key: str, tenant_key: str, data: dict[str, Any]) -> FishStock:
        stock = self.get_stock(system_key, stock_key, tenant_key)
        updated = stock.model_copy(update=data)
        return self._repo.update_stock(stock_key, updated)

    def delete_stock(self, system_key: str, stock_key: str, tenant_key: str) -> None:
        stock = self.get_stock(system_key, stock_key, tenant_key)
        if stock.count > 0:
            raise ResourceInUseError("FishStock", "stock still holds fish (document mortality or harvest first)")
        self._repo.delete_stock(stock_key)

    def record_mortality(self, system_key: str, stock_key: str, tenant_key: str, deaths: int) -> FishStock:
        if deaths <= 0:
            raise ValidationError("Mortalitätseintrag muss > 0 sein.")
        stock = self.get_stock(system_key, stock_key, tenant_key)
        if deaths > stock.count:
            raise ValidationError("Mehr Verluste als vorhandene Fische.")
        updated = stock.model_copy(
            update={
                "count": stock.count - deaths,
                "mortality_count": stock.mortality_count + deaths,
            }
        )
        return self._repo.update_stock(stock_key, updated)

    def get_biomass_history(self, system_key: str, stock_key: str, tenant_key: str) -> dict[str, Any]:
        stock = self.get_stock(system_key, stock_key, tenant_key)
        return {
            "stock_key": stock.key,
            "current_biomass_kg": stock.total_biomass_kg,
            "count": stock.count,
            "avg_weight_g": stock.avg_weight_g,
            "last_weighed_at": stock.last_weighed_at,
        }

    def get_mortality_rate(self, system_key: str, stock_key: str, tenant_key: str) -> dict[str, Any]:
        stock = self.get_stock(system_key, stock_key, tenant_key)
        rate = self._health.calculate_mortality_rate(stock)
        return {
            "stock_key": stock.key,
            "mortality_count": stock.mortality_count,
            "initial_count": stock.initial_count,
            "mortality_rate": rate,
            "mortality_rate_percent": round(rate * 100, 2),
        }

    # ── WaterTest ───────────────────────────────────────────────────────

    def record_water_test(self, system_key: str, tenant_key: str, water_test: WaterTest) -> WaterTest:
        self.get_system(system_key, tenant_key)
        water_test.system_key = system_key
        water_test.tenant_key = tenant_key
        water_test.free_ammonia_mgl = self._nitrogen.calculate_free_ammonia(
            water_test.ammonia_tan_mgl, water_test.ph, water_test.temperature_c
        )
        return self._repo.create_water_test(water_test)

    def list_water_tests(self, system_key: str, tenant_key: str, offset: int = 0, limit: int = 50) -> list[WaterTest]:
        self.get_system(system_key, tenant_key)
        return self._repo.list_water_tests(system_key, tenant_key, offset, limit)

    def get_water_quality_status(self, system_key: str, tenant_key: str) -> list[WaterQualityEvaluation]:
        self.get_system(system_key, tenant_key)
        latest = self._repo.get_latest_water_test(system_key)
        if latest is None:
            return []
        species = self._primary_species(system_key, tenant_key)
        return self._nitrogen.evaluate_water_quality(latest, species)

    def get_nitrogen_cycle_chart(self, system_key: str, tenant_key: str, limit: int = 60) -> list[dict[str, Any]]:
        self.get_system(system_key, tenant_key)
        tests = self._repo.list_water_tests(system_key, tenant_key, offset=0, limit=limit)
        return [
            {
                "tested_at": t.tested_at,
                "ammonia_tan_mgl": t.ammonia_tan_mgl,
                "free_ammonia_mgl": t.free_ammonia_mgl,
                "nitrite_mgl": t.nitrite_mgl,
                "nitrate_mgl": t.nitrate_mgl,
                "ph": t.ph,
                "temperature_c": t.temperature_c,
            }
            for t in reversed(tests)
        ]

    def get_cycling_progress(self, system_key: str, tenant_key: str) -> CyclingProgress:
        self.get_system(system_key, tenant_key)
        tests = self._repo.list_water_tests(system_key, tenant_key, offset=0, limit=30)
        return self._nitrogen.detect_cycling_phase(tests)

    # ── Feeding ─────────────────────────────────────────────────────────

    def record_feeding(
        self, system_key: str, stock_key: str, tenant_key: str, feeding: FishFeedingEvent
    ) -> FishFeedingEvent:
        self.get_stock(system_key, stock_key, tenant_key)
        feeding.system_key = system_key
        feeding.stock_key = stock_key
        feeding.tenant_key = tenant_key
        return self._repo.create_feeding(feeding)

    def list_feedings(
        self, system_key: str, tenant_key: str, offset: int = 0, limit: int = 50
    ) -> list[FishFeedingEvent]:
        self.get_system(system_key, tenant_key)
        return self._repo.list_feedings(system_key, tenant_key, offset, limit)

    def get_feeding_recommendation(self, system_key: str, tenant_key: str) -> FeedingRecommendation:
        system = self.get_system(system_key, tenant_key)
        stocks = self._repo.list_stocks(system_key, tenant_key)
        if not stocks:
            raise ValidationError("Kein Fischbestand — keine Fütterungsempfehlung möglich.")
        species = self._repo.get_species_or_raise(stocks[0].species_key)
        biomass = sum(s.total_biomass_kg for s in stocks)
        latest = self._repo.get_latest_water_test(system_key)
        temp = latest.temperature_c if latest else species.temperature_optimal_min_c
        return self._feeding.calculate_daily_feed(biomass, temp, species, system.cycling_status)

    def get_fcr_analysis(self, system_key: str, tenant_key: str) -> dict[str, Any]:
        self.get_system(system_key, tenant_key)
        stocks = self._repo.list_stocks(system_key, tenant_key)
        feedings = self._repo.list_feedings(system_key, tenant_key, offset=0, limit=500)
        total_feed_g = sum(f.amount_g for f in feedings)
        biomass_gain_kg = sum(
            max(0.0, (s.count * s.avg_weight_g - s.initial_count * s.avg_weight_g)) / 1000 for s in stocks
        )
        fcr = round(total_feed_g / 1000 / biomass_gain_kg, 2) if biomass_gain_kg > 0 else None
        return {
            "total_feed_kg": round(total_feed_g / 1000, 3),
            "biomass_gain_kg": round(biomass_gain_kg, 3),
            "fcr": fcr,
            "feeding_count": len(feedings),
        }

    # ── Supplementation & deficiency ────────────────────────────────────

    def record_supplementation(
        self, system_key: str, tenant_key: str, event: SupplementationEvent
    ) -> SupplementationEvent:
        self.get_system(system_key, tenant_key)
        event.system_key = system_key
        event.tenant_key = tenant_key
        return self._repo.create_supplementation(event)

    def list_supplementations(
        self, system_key: str, tenant_key: str, offset: int = 0, limit: int = 50
    ) -> list[SupplementationEvent]:
        self.get_system(system_key, tenant_key)
        return self._repo.list_supplementations(system_key, tenant_key, offset, limit)

    def get_deficiency_check(self, system_key: str, tenant_key: str) -> DeficiencyReport:
        system = self.get_system(system_key, tenant_key)
        latest = self._repo.get_latest_water_test(system_key)
        if latest is None:
            raise ValidationError("Kein Wassertest vorhanden — Defizit-Analyse nicht möglich.")
        return self._deficiency.analyze(latest, system)

    # ── Safety, alerts & health ─────────────────────────────────────────

    def get_safety_status(self, system_key: str, tenant_key: str) -> dict[str, Any]:
        system = self.get_system(system_key, tenant_key)
        latest = self._repo.get_latest_water_test(system_key)
        species = self._primary_species(system_key, tenant_key)
        stocks = self._repo.list_stocks(system_key, tenant_key)

        water_quality: list[WaterQualityEvaluation] = []
        if latest is not None:
            water_quality = self._nitrogen.evaluate_water_quality(latest, species)
            alkalinity = (
                self._nitrogen.check_alkalinity_crash_risk(latest.kh_dh, system.daily_feed_target_g)
                if latest.kh_dh is not None
                else None
            )
            if alkalinity is not None:
                water_quality.append(alkalinity)

        stocking: StockingValidation | None = None
        if stocks and species is not None:
            stocking = self._stocking.validate_stocking(stocks[0], system.total_volume_liters, species, system)

        return {
            "system_key": system.key,
            "cycling_status": system.cycling_status.value,
            "water_quality": [e.model_dump() for e in water_quality],
            "stocking": stocking.model_dump() if stocking else None,
        }

    def get_alerts(self, system_key: str, tenant_key: str) -> list[WaterQualityEvaluation]:
        evaluations = self.get_water_quality_status(system_key, tenant_key)
        order = {"critical": 0, "warning": 1, "info": 2, "ok": 3}
        actionable = [e for e in evaluations if e.severity in ("critical", "warning")]
        return sorted(actionable, key=lambda e: order.get(e.severity, 3))

    def get_fish_health(self, system_key: str, tenant_key: str) -> list[HealthAlert]:
        self.get_system(system_key, tenant_key)
        stocks = self._repo.list_stocks(system_key, tenant_key)
        if not stocks:
            return []
        feedings = self._repo.list_feedings(system_key, tenant_key, offset=0, limit=20)
        tests = self._repo.list_water_tests(system_key, tenant_key, offset=0, limit=5)
        species = self._primary_species(system_key, tenant_key)
        alerts: list[HealthAlert] = []
        for stock in stocks:
            stock_feedings = [f for f in feedings if f.stock_key == stock.key]
            alerts.extend(self._health.evaluate_fish_health(stock, stock_feedings, tests, species))
        return alerts

    # ── Helpers ─────────────────────────────────────────────────────────

    def _primary_species(self, system_key: str, tenant_key: str) -> FishSpecies | None:
        stocks = self._repo.list_stocks(system_key, tenant_key)
        if not stocks:
            return None
        return self._repo.get_species(stocks[0].species_key)
