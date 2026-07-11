"""REQ-026 Aquaponics domain engines.

Pure, side-effect-free calculators and validators for the fish/plant loop:

* :class:`NitrogenCycleEngine` — free-ammonia (Emerson 1975), DO saturation
  (Benson & Krause 1984), species-specific water-quality grading and biofilter
  cycling detection.
* :class:`StockingDensityCalculator` — stocking density and fish/plant ratio.
* :class:`FeedingRateCalculator` — temperature-corrected feeding recommendation,
  TAN production and post-cycling/dormancy ramp-up schedules.
* :class:`NutrientDeficiencyAnalyzer` — Fe/K/Ca/Mg/Mn/Zn/B/PO4 deficiency check.
  Delegates the grow-bed nutrient-strength (EC) suitability to the existing
  :class:`~app.domain.engines.hydro_system_monitor.HydroSystemMonitor`.
* :class:`AquaponicsSafetyValidator` — blocks fish-toxic substances.
* :class:`BiofilterManager` — biofilter dimensioning, turnover, reactivation.
* :class:`FishHealthMonitor` — mortality-rate and feeding-refusal alerts.

All numeric constants and formulas trace to
``spec/req/REQ-026_Aquaponik-Management.md`` (§1/§3).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel

from app.common.enums import (
    AquaponicSystemType,
    CyclingStatus,
    FishFeedingResponse,
)
from app.domain.engines.hydro_system_monitor import HydroSystemMonitor
from app.domain.models.aquaponik import (
    AquaponicSystem,
    FishFeedingEvent,
    FishSpecies,
    FishStock,
    WaterTest,
)

Severity = Literal["ok", "info", "warning", "critical"]

#: Safe threshold for free (unionised) ammonia in mg/L (REQ-026 §1).
FREE_AMMONIA_SAFE_MGL = 0.02
#: Warning threshold — half of the critical limit.
FREE_AMMONIA_WARN_MGL = 0.01
#: Consecutive stable days required for ``cycling -> cycled`` (REQ-026 §1).
CYCLING_STABLE_DAYS_REQUIRED = 7
#: Grow-bed substrate mapping per system type (drives EC-suitability checks).
_SYSTEM_SUBSTRATE = {
    AquaponicSystemType.MEDIA_BED: "clay_pebbles",
    AquaponicSystemType.WICKING_BED: "clay_pebbles",
    AquaponicSystemType.DWC: "hydro_solution",
    AquaponicSystemType.NFT: "hydro_solution",
    AquaponicSystemType.HYBRID: "hydro_solution",
}


class WaterQualityEvaluation(BaseModel):
    """A single graded water-parameter finding."""

    parameter: str
    value: float
    limit: float
    severity: Severity
    message_de: str
    message_en: str


class CyclingProgress(BaseModel):
    """Biofilter cycling progress derived from the water-test history."""

    status: CyclingStatus
    progress_percent: float
    stable_days: int
    days_required: int
    estimated_completion: date | None
    phase_description_de: str
    phase_description_en: str


class StockingValidation(BaseModel):
    """Result of a stocking-density check."""

    current_density_kg_per_1000l: float
    max_density_kg_per_1000l: float
    utilization_percent: float
    status: Literal["ok", "warning", "overstocked"]
    fish_plant_ratio_g_feed_per_m2: float
    message_de: str


class FeedingRecommendation(BaseModel):
    """Temperature-corrected daily feeding recommendation."""

    recommended_g: float
    base_rate_percent: float
    temperature_factor: float
    cycling_factor: float
    species_name: str
    biomass_kg: float
    water_temp_c: float
    notes: list[str]


class RampUpSchedule(BaseModel):
    """Post-cycling / post-dormancy feeding ramp-up plan."""

    weeks: list[dict]
    target_daily_g: float
    reason: str


class DeficiencyFinding(BaseModel):
    """A single micro/macro-nutrient deficiency (or excess) finding."""

    nutrient: str
    value_ppm: float | None
    target_min_ppm: float
    target_max_ppm: float
    status: Literal["ok", "deficient", "excess", "unknown"]
    recommended_supplement: str
    message_de: str


class DeficiencyReport(BaseModel):
    """Aggregate deficiency analysis for a system."""

    findings: list[DeficiencyFinding]
    grow_bed_ec_status: str
    grow_bed_ec_message: str


class SafetyViolation(BaseModel):
    """A fish-safety rule violation (warn = advise, block = reject)."""

    violation_type: str
    severity: Literal["warning", "block"]
    message_de: str
    message_en: str


class BiofilterDimensioning(BaseModel):
    """Biofilter surface-area dimensioning recommendation."""

    required_surface_area_m2: float
    current_surface_area_m2: float | None
    status: Literal["sufficient", "marginal", "insufficient", "unknown"]
    daily_tan_production_g: float
    filter_capacity_g_tan_per_day: float


class HealthAlert(BaseModel):
    """A fish-health alert derived from mortality / feeding / water quality."""

    alert_type: str
    severity: Severity
    message_de: str
    message_en: str
    recommended_action: str


class NitrogenCycleEngine:
    """Nitrogen-cycle math and species-specific water-quality grading."""

    @staticmethod
    def calculate_free_ammonia(tan_mgl: float, ph: float, temp_c: float) -> float:
        """Free (unionised) ammonia from TAN, pH and temperature (Emerson 1975)."""
        t_kelvin = temp_c + 273.15
        pka = 0.09018 + 2729.92 / t_kelvin
        fraction_nh3 = 1.0 / (10 ** (pka - ph) + 1)
        return round(tan_mgl * fraction_nh3, 4)

    @staticmethod
    def calculate_do_saturation(temp_c: float) -> float:
        """Maximum DO saturation at ``temp_c`` (Benson & Krause 1984, mg/L)."""
        t = temp_c
        return round(14.6 - 0.3943 * t + 0.007714 * t**2 - 0.0000646 * t**3, 2)

    def evaluate_water_quality(
        self,
        water_test: WaterTest,
        fish_species: FishSpecies | None,
    ) -> list[WaterQualityEvaluation]:
        """Grade every water parameter against species-specific limits."""
        results: list[WaterQualityEvaluation] = []
        free_nh3 = water_test.free_ammonia_mgl or self.calculate_free_ammonia(
            water_test.ammonia_tan_mgl, water_test.ph, water_test.temperature_c
        )

        # Free ammonia — species-independent hard limit.
        if free_nh3 > FREE_AMMONIA_SAFE_MGL:
            results.append(
                WaterQualityEvaluation(
                    parameter="free_ammonia",
                    value=free_nh3,
                    limit=FREE_AMMONIA_SAFE_MGL,
                    severity="critical",
                    message_de=f"Freies Ammoniak {free_nh3} mg/L überschreitet den kritischen Grenzwert "
                    f"{FREE_AMMONIA_SAFE_MGL} mg/L — akute Lebensgefahr für Fische.",
                    message_en=f"Free ammonia {free_nh3} mg/L exceeds the critical limit "
                    f"{FREE_AMMONIA_SAFE_MGL} mg/L — acutely lethal to fish.",
                )
            )
        elif free_nh3 > FREE_AMMONIA_WARN_MGL:
            results.append(
                WaterQualityEvaluation(
                    parameter="free_ammonia",
                    value=free_nh3,
                    limit=FREE_AMMONIA_WARN_MGL,
                    severity="warning",
                    message_de=f"Freies Ammoniak {free_nh3} mg/L erhöht — Fütterung reduzieren.",
                    message_en=f"Free ammonia {free_nh3} mg/L elevated — reduce feeding.",
                )
            )

        if fish_species is None:
            return results

        # TAN, nitrite, nitrate against species maxima.
        for param, value, limit, de_name, en_name in (
            ("ammonia_tan", water_test.ammonia_tan_mgl, fish_species.max_tan_mgl, "Ammoniak (TAN)", "ammonia (TAN)"),
            ("nitrite", water_test.nitrite_mgl, fish_species.max_nitrite_mgl, "Nitrit", "nitrite"),
            ("nitrate", water_test.nitrate_mgl, fish_species.max_nitrate_mgl, "Nitrat", "nitrate"),
        ):
            if value > limit:
                results.append(
                    WaterQualityEvaluation(
                        parameter=param,
                        value=value,
                        limit=limit,
                        severity="critical" if param != "nitrate" else "warning",
                        message_de=f"{de_name} {value} mg/L überschreitet den Grenzwert für "
                        f"{fish_species.common_name_de} (max {limit} mg/L).",
                        message_en=f"{en_name} {value} mg/L exceeds the limit for "
                        f"{fish_species.common_name_en} (max {limit} mg/L).",
                    )
                )

        # pH against species tolerance band.
        if water_test.ph < fish_species.ph_min or water_test.ph > fish_species.ph_max:
            results.append(
                WaterQualityEvaluation(
                    parameter="ph",
                    value=water_test.ph,
                    limit=fish_species.ph_min if water_test.ph < fish_species.ph_min else fish_species.ph_max,
                    severity="warning",
                    message_de=f"pH {water_test.ph} liegt außerhalb des Toleranzbereichs "
                    f"{fish_species.ph_min}-{fish_species.ph_max} für {fish_species.common_name_de}.",
                    message_en=f"pH {water_test.ph} is outside the tolerance range "
                    f"{fish_species.ph_min}-{fish_species.ph_max} for {fish_species.common_name_en}.",
                )
            )

        # Temperature — layered lethal / stress / suboptimal.
        results.extend(self._evaluate_temperature(water_test.temperature_c, fish_species))

        # Dissolved oxygen — absolute species thresholds + saturation ratio.
        if water_test.dissolved_oxygen_mgl is not None:
            results.extend(
                self._evaluate_dissolved_oxygen(water_test.dissolved_oxygen_mgl, water_test.temperature_c, fish_species)
            )

        # Carbonate / general hardness.
        results.extend(self._evaluate_hardness(water_test))

        return results

    def _evaluate_temperature(self, temp_c: float, species: FishSpecies) -> list[WaterQualityEvaluation]:
        if temp_c < species.temperature_lethal_low_c or temp_c > species.temperature_lethal_high_c:
            severity: Severity = "critical"
            de = f"Wassertemperatur {temp_c}°C ist letal für {species.common_name_de}."
            en = f"Water temperature {temp_c}°C is lethal for {species.common_name_en}."
        elif temp_c < species.temperature_min_c or temp_c > species.temperature_max_c:
            severity = "warning"
            de = f"Wassertemperatur {temp_c}°C liegt im Stressbereich für {species.common_name_de}."
            en = f"Water temperature {temp_c}°C is in the stress range for {species.common_name_en}."
        elif temp_c < species.temperature_optimal_min_c or temp_c > species.temperature_optimal_max_c:
            severity = "info"
            de = f"Wassertemperatur {temp_c}°C ist suboptimal für {species.common_name_de}."
            en = f"Water temperature {temp_c}°C is suboptimal for {species.common_name_en}."
        else:
            return []
        return [
            WaterQualityEvaluation(
                parameter="temperature",
                value=temp_c,
                limit=species.temperature_optimal_max_c,
                severity=severity,
                message_de=de,
                message_en=en,
            )
        ]

    def _evaluate_dissolved_oxygen(
        self, do_mgl: float, temp_c: float, species: FishSpecies
    ) -> list[WaterQualityEvaluation]:
        results: list[WaterQualityEvaluation] = []
        if do_mgl < species.do_minimum_mgl:
            results.append(
                WaterQualityEvaluation(
                    parameter="dissolved_oxygen",
                    value=do_mgl,
                    limit=species.do_minimum_mgl,
                    severity="critical",
                    message_de=f"Gelöstsauerstoff {do_mgl} mg/L unter dem Überlebensminimum "
                    f"{species.do_minimum_mgl} mg/L für {species.common_name_de}.",
                    message_en=f"Dissolved oxygen {do_mgl} mg/L below survival minimum "
                    f"{species.do_minimum_mgl} mg/L for {species.common_name_en}.",
                )
            )
        elif do_mgl < species.do_stress_mgl:
            results.append(
                WaterQualityEvaluation(
                    parameter="dissolved_oxygen",
                    value=do_mgl,
                    limit=species.do_stress_mgl,
                    severity="warning",
                    message_de=f"Gelöstsauerstoff {do_mgl} mg/L unter der Stress-Schwelle "
                    f"{species.do_stress_mgl} mg/L — Belüftung erhöhen.",
                    message_en=f"Dissolved oxygen {do_mgl} mg/L below the stress threshold "
                    f"{species.do_stress_mgl} mg/L — increase aeration.",
                )
            )
        saturation = self.calculate_do_saturation(temp_c)
        if saturation > 0 and do_mgl < 0.7 * saturation:
            results.append(
                WaterQualityEvaluation(
                    parameter="do_saturation",
                    value=round(do_mgl / saturation * 100, 1),
                    limit=70.0,
                    severity="warning",
                    message_de=f"Sauerstoffsättigung unter 70% (Sättigung bei {temp_c}°C ≈ {saturation} mg/L).",
                    message_en=f"Oxygen saturation below 70% (saturation at {temp_c}°C ≈ {saturation} mg/L).",
                )
            )
        return results

    def _evaluate_hardness(self, water_test: WaterTest) -> list[WaterQualityEvaluation]:
        results: list[WaterQualityEvaluation] = []
        if water_test.kh_dh is not None and water_test.kh_dh < 4:
            results.append(
                WaterQualityEvaluation(
                    parameter="kh",
                    value=water_test.kh_dh,
                    limit=4.0,
                    severity="warning",
                    message_de=f"Karbonathärte {water_test.kh_dh}°dH unter 4°dH — pH-Crash-Gefahr, nachpuffern.",
                    message_en=f"Carbonate hardness {water_test.kh_dh}°dH below 4°dH — pH-crash risk, re-buffer.",
                )
            )
        if water_test.gh_dh is not None:
            if water_test.gh_dh < 4:
                results.append(
                    WaterQualityEvaluation(
                        parameter="gh",
                        value=water_test.gh_dh,
                        limit=4.0,
                        severity="warning",
                        message_de=f"Gesamthärte {water_test.gh_dh}°dH niedrig — Ca/Mg-Mangel möglich.",
                        message_en=f"General hardness {water_test.gh_dh}°dH low — Ca/Mg deficiency possible.",
                    )
                )
            elif water_test.gh_dh > 20:
                results.append(
                    WaterQualityEvaluation(
                        parameter="gh",
                        value=water_test.gh_dh,
                        limit=20.0,
                        severity="warning",
                        message_de=f"Gesamthärte {water_test.gh_dh}°dH hoch — Stress bei empfindlichen Arten.",
                        message_en=f"General hardness {water_test.gh_dh}°dH high — stress for sensitive species.",
                    )
                )
        return results

    def detect_cycling_phase(self, water_tests: list[WaterTest]) -> CyclingProgress:
        """Estimate biofilter cycling progress from the water-test history.

        ``water_tests`` may be in any order; they are sorted ascending by test
        time. ``stable_days`` counts the trailing run of tests that are stable
        (TAN < 0.25 mg/L and NO2 < 0.1 mg/L). ``cycled`` requires
        ``CYCLING_STABLE_DAYS_REQUIRED`` consecutive stable readings.
        """
        if not water_tests:
            return CyclingProgress(
                status=CyclingStatus.NEW,
                progress_percent=0.0,
                stable_days=0,
                days_required=CYCLING_STABLE_DAYS_REQUIRED,
                estimated_completion=None,
                phase_description_de="Noch keine Wassertests — Biofilter nicht eingefahren.",
                phase_description_en="No water tests yet — biofilter not cycled.",
            )
        ordered = sorted(water_tests, key=lambda t: t.tested_at or datetime.min.replace(tzinfo=UTC))
        stable_run = 0
        for test in reversed(ordered):
            if test.ammonia_tan_mgl < 0.25 and test.nitrite_mgl < 0.1:
                stable_run += 1
            else:
                break
        progress = min(stable_run / CYCLING_STABLE_DAYS_REQUIRED * 100, 100.0)

        latest = ordered[-1]
        has_activity = any(t.ammonia_tan_mgl > 0.5 for t in ordered)
        if stable_run >= CYCLING_STABLE_DAYS_REQUIRED:
            status = CyclingStatus.CYCLED
            de = "Cycling abgeschlossen — Biofilter stabil."
            en = "Cycling complete — biofilter stable."
        elif has_activity or latest.ammonia_tan_mgl > 0.5:
            status = CyclingStatus.CYCLING
            de = "Biofilter fährt ein — Ammoniak-/Nitrit-Spikes möglich."
            en = "Biofilter is cycling — ammonia/nitrite spikes possible."
        else:
            status = CyclingStatus.NEW
            de = "Biofilter frisch — noch keine Nitrifikation nachweisbar."
            en = "Biofilter fresh — no nitrification detected yet."

        estimated: date | None = None
        if status == CyclingStatus.CYCLING and latest.tested_at is not None:
            remaining = max(0, CYCLING_STABLE_DAYS_REQUIRED - stable_run)
            estimated = (latest.tested_at + timedelta(days=remaining)).date()

        return CyclingProgress(
            status=status,
            progress_percent=round(progress, 1),
            stable_days=stable_run,
            days_required=CYCLING_STABLE_DAYS_REQUIRED,
            estimated_completion=estimated,
            phase_description_de=de,
            phase_description_en=en,
        )

    def check_alkalinity_crash_risk(self, kh_dh: float, daily_feed_g: float) -> WaterQualityEvaluation | None:
        """Warn when carbonate hardness is too low for the active feeding load."""
        if kh_dh < 4 and daily_feed_g > 0:
            return WaterQualityEvaluation(
                parameter="kh",
                value=kh_dh,
                limit=4.0,
                severity="warning",
                message_de=f"Karbonathärte {kh_dh}°dH bei aktiver Fütterung — pH-Crash-Risiko, nachpuffern.",
                message_en=f"Carbonate hardness {kh_dh}°dH under active feeding — pH-crash risk, re-buffer.",
            )
        return None


class StockingDensityCalculator:
    """Stocking-density and fish/plant balance calculations."""

    FEED_PER_M2: dict[str, float] = {
        "media_bed": 80,
        "dwc": 100,
        "nft": 60,
        "hybrid": 90,
        "wicking_bed": 50,
    }

    def calculate_max_fish(self, tank_volume_l: float, species: FishSpecies) -> int:
        """Maximum fish count at market weight and the hobby stocking density."""
        avg_weight_g = species.market_weight_g or 200.0
        if avg_weight_g <= 0:
            return 0
        max_biomass_kg = tank_volume_l / 1000 * species.max_stocking_density_kg_per_1000l
        return int(max_biomass_kg * 1000 / avg_weight_g)

    def calculate_fish_plant_ratio(
        self, daily_feed_g: float, grow_area_m2: float, system_type: AquaponicSystemType
    ) -> float:
        """Feed per grow-bed area (g/m²/day)."""
        if grow_area_m2 <= 0:
            return 0.0
        return round(daily_feed_g / grow_area_m2, 1)

    def validate_stocking(
        self,
        fish_stock: FishStock,
        tank_volume_l: float,
        species: FishSpecies,
        system: AquaponicSystem,
    ) -> StockingValidation:
        density = round(fish_stock.total_biomass_kg / (tank_volume_l / 1000), 2) if tank_volume_l > 0 else 0.0
        max_density = species.max_stocking_density_kg_per_1000l
        utilization = round(density / max_density * 100, 1) if max_density > 0 else 0.0
        ratio = self.calculate_fish_plant_ratio(system.daily_feed_target_g, system.grow_area_m2, system.system_type)
        if utilization > 100:
            status: Literal["ok", "warning", "overstocked"] = "overstocked"
            message = (
                f"Besatzdichte {density} kg/1000L überschreitet das Maximum {max_density} kg/1000L "
                f"({utilization}%) — Besatz reduzieren."
            )
        elif utilization > 80:
            status = "warning"
            message = f"Besatzdichte {density} kg/1000L nahe Maximum ({utilization}%)."
        else:
            status = "ok"
            message = f"Besatzdichte {density} kg/1000L im sicheren Bereich ({utilization}%)."
        return StockingValidation(
            current_density_kg_per_1000l=density,
            max_density_kg_per_1000l=max_density,
            utilization_percent=utilization,
            status=status,
            fish_plant_ratio_g_feed_per_m2=ratio,
            message_de=message,
        )


class FeedingRateCalculator:
    """Temperature-corrected feeding recommendations and ramp-up schedules."""

    BASE_FEED_RATE: dict[str, float] = {
        "warmwater": 0.03,
        "temperate": 0.025,
        "coldwater": 0.02,
    }
    DEFAULT_PROTEIN_BY_FEED_TYPE: dict[str, float] = {
        "carnivore": 0.45,
        "omnivore": 0.32,
        "herbivore": 0.28,
    }
    CYCLING_FACTORS: dict[str, float] = {
        "new": 0.0,
        "cycling": 0.25,
        "dormant": 0.1,
        "cycled": 1.0,
    }

    def _temperature_factor(self, water_temp_c: float, species: FishSpecies) -> float:
        if water_temp_c >= species.temperature_max_c:
            return 0.0
        if water_temp_c < species.temperature_optimal_min_c:
            return round(2 ** ((water_temp_c - species.temperature_optimal_min_c) / 10), 3)
        if water_temp_c <= species.temperature_optimal_max_c:
            return 1.0
        span = species.temperature_max_c - species.temperature_optimal_max_c
        if span <= 0:
            return 0.0
        return round(max(0.0, 1 - (water_temp_c - species.temperature_optimal_max_c) / span), 3)

    def calculate_daily_feed(
        self,
        total_biomass_kg: float,
        water_temp_c: float,
        species: FishSpecies,
        cycling_status: CyclingStatus,
        fish_response: FishFeedingResponse | None = None,
    ) -> FeedingRecommendation:
        notes: list[str] = []
        base_rate = self.BASE_FEED_RATE[species.temperature_zone.value]
        temp_factor = self._temperature_factor(water_temp_c, species)
        cycling_factor = self.CYCLING_FACTORS.get(cycling_status.value, 1.0)

        if fish_response == FishFeedingResponse.REFUSED:
            notes.append("Fische verweigern das Futter — Fütterung aussetzen und Wasserwerte prüfen.")
            return FeedingRecommendation(
                recommended_g=0.0,
                base_rate_percent=round(base_rate * 100, 1),
                temperature_factor=temp_factor,
                cycling_factor=cycling_factor,
                species_name=species.common_name_de,
                biomass_kg=total_biomass_kg,
                water_temp_c=water_temp_c,
                notes=notes,
            )

        recommended = round(total_biomass_kg * 1000 * base_rate * temp_factor * cycling_factor, 2)

        if temp_factor == 0:
            notes.append(f"Wassertemperatur {water_temp_c}°C zu hoch — Fütterung stoppen.")
        elif temp_factor < 1:
            notes.append(
                f"Wassertemperatur {water_temp_c}°C außerhalb Optimum "
                f"({species.temperature_optimal_min_c}-{species.temperature_optimal_max_c}°C) — "
                f"Futtermenge um {round((1 - temp_factor) * 100)}% angepasst."
            )
        if cycling_status == CyclingStatus.CYCLED:
            notes.append("Biofilter eingefahren — volle Fütterung erlaubt.")
        elif cycling_status in (CyclingStatus.CYCLING, CyclingStatus.NEW):
            notes.append("Biofilter noch nicht eingefahren — reduzierte Fütterung (Ramp-up).")
        elif cycling_status == CyclingStatus.DORMANT:
            notes.append("Biofilter in Winterruhe — nur minimale Fütterung.")

        return FeedingRecommendation(
            recommended_g=recommended,
            base_rate_percent=round(base_rate * 100, 1),
            temperature_factor=temp_factor,
            cycling_factor=cycling_factor,
            species_name=species.common_name_de,
            biomass_kg=total_biomass_kg,
            water_temp_c=water_temp_c,
            notes=notes,
        )

    def calculate_tan_production(self, daily_feed_g: float, protein_percent: float = 32.0) -> float:
        """Estimated TAN production from feed amount and protein content (g/day)."""
        return round(daily_feed_g * (protein_percent / 100) * 0.092, 3)

    def calculate_ramp_up_schedule(
        self, target_feed_g: float, reason: str, water_temp_c: float = 25.0
    ) -> RampUpSchedule:
        """Temperature-dependent post-cycling / dormancy feeding ramp-up."""
        if water_temp_c < 15:
            return RampUpSchedule(weeks=[], target_daily_g=target_feed_g, reason=reason)
        base_weeks = 7
        duration = base_weeks if water_temp_c >= 20 else base_weeks * 2
        steps = [0.25, 0.5, 0.75, 1.0]
        per_step_weeks = max(1, duration // len(steps))
        weeks: list[dict] = []
        week_no = 1
        for pct in steps:
            for _ in range(per_step_weeks):
                weeks.append(
                    {
                        "week": week_no,
                        "percent": int(pct * 100),
                        "daily_g": round(target_feed_g * pct, 2),
                    }
                )
                week_no += 1
        return RampUpSchedule(weeks=weeks, target_daily_g=target_feed_g, reason=reason)


class NutrientDeficiencyAnalyzer:
    """Micro/macro-nutrient deficiency analysis for aquaponic water.

    Consumes :class:`HydroSystemMonitor` to grade the grow-bed nutrient
    strength (estimated EC) against the substrate's EC limits.
    """

    TARGETS: dict[str, tuple[float, float, str]] = {
        "iron": (2.0, 5.0, "Fe-DTPA (bis pH 7.5) oder Fe-EDDHA (bis pH 9.0)"),
        "potassium": (150.0, 300.0, "KOH oder K2CO3"),
        "calcium": (40.0, 120.0, "Ca(OH)2"),
        "magnesium": (15.0, 50.0, "MgSO4 (Bittersalz)"),
        "phosphate": (10.0, 60.0, "Monitoring — meist ausreichend durch Futter"),
    }

    def __init__(self, monitor: HydroSystemMonitor | None = None) -> None:
        self._monitor = monitor or HydroSystemMonitor()

    @staticmethod
    def _estimate_ec_ms(water_test: WaterTest) -> float:
        """Rough EC estimate (mS/cm) from measured dissolved ions (ppm/640)."""
        total_ppm = sum(
            value
            for value in (
                water_test.nitrate_mgl,
                water_test.potassium_ppm,
                water_test.calcium_ppm,
                water_test.magnesium_ppm,
                water_test.phosphate_ppm,
            )
            if value is not None
        )
        return round(total_ppm / 640, 3)

    def analyze(self, water_test: WaterTest, system: AquaponicSystem) -> DeficiencyReport:
        findings: list[DeficiencyFinding] = []
        values = {
            "iron": water_test.iron_ppm,
            "potassium": water_test.potassium_ppm,
            "calcium": water_test.calcium_ppm,
            "magnesium": water_test.magnesium_ppm,
            "phosphate": water_test.phosphate_ppm,
        }
        for nutrient, (target_min, target_max, supplement) in self.TARGETS.items():
            value = values[nutrient]
            if value is None:
                status: Literal["ok", "deficient", "excess", "unknown"] = "unknown"
                message = f"{nutrient}: kein Messwert vorhanden."
            elif value < target_min:
                status = "deficient"
                message = f"{nutrient} {value} ppm unter Zielbereich ({target_min}-{target_max}) — {supplement}."
            elif nutrient == "phosphate" and value > 80:
                status = "excess"
                message = f"Phosphat {value} ppm hoch (>80) — Teilwasserwechsel; reduziert Eisenverfügbarkeit."
            elif value > target_max:
                status = "excess"
                message = f"{nutrient} {value} ppm über Zielbereich ({target_min}-{target_max})."
            else:
                status = "ok"
                message = f"{nutrient} {value} ppm im Zielbereich."
            findings.append(
                DeficiencyFinding(
                    nutrient=nutrient,
                    value_ppm=value,
                    target_min_ppm=target_min,
                    target_max_ppm=target_max,
                    status=status,
                    recommended_supplement=supplement,
                    message_de=message,
                )
            )

        substrate = _SYSTEM_SUBSTRATE.get(system.system_type, "hydro_solution")
        estimated_ec = self._estimate_ec_ms(water_test)
        ec_ok, ec_message = self._monitor.validate_ec_for_substrate(estimated_ec, substrate)
        return DeficiencyReport(
            findings=findings,
            grow_bed_ec_status="ok" if ec_ok else "out_of_range",
            grow_bed_ec_message=f"Geschätzte Nährstoff-EC {estimated_ec} mS/cm ({substrate}): {ec_message}",
        )


class AquaponicsSafetyValidator:
    """Blocks fish-toxic substances and unsafe interventions."""

    def validate_fertilizer_safe(
        self, aquaponic_safe: bool, system_ph: float, is_fe_edta: bool = False
    ) -> SafetyViolation | None:
        if not aquaponic_safe:
            return SafetyViolation(
                violation_type="synthetic_fertilizer",
                severity="block",
                message_de="Dieser Dünger ist nicht fischsicher (aquaponic_safe=false) und darf nicht "
                "in Aquaponik-Systemen eingesetzt werden.",
                message_en="This fertilizer is not fish-safe (aquaponic_safe=false) and must not be "
                "used in aquaponic systems.",
            )
        if is_fe_edta and system_ph > 6.5:
            return SafetyViolation(
                violation_type="fe_edta_ph",
                severity="warning",
                message_de=f"Fe-EDTA ist bei pH {system_ph} (>6.5) instabil und wirkungslos — Fe-DTPA/Fe-EDDHA nutzen.",
                message_en=f"Fe-EDTA is unstable above pH 6.5 (pH {system_ph}) — use Fe-DTPA/Fe-EDDHA instead.",
            )
        return None

    def validate_no_chlorine(self, chlorine_ppm: float | None, chloramine_ppm: float | None) -> SafetyViolation | None:
        if chloramine_ppm is not None and chloramine_ppm > 0.003:
            return SafetyViolation(
                violation_type="chlorine",
                severity="block",
                message_de=f"Chloramin {chloramine_ppm} ppm — nicht durch Abstehen entfernbar, Aktivkohle nötig.",
                message_en=f"Chloramine {chloramine_ppm} ppm — not removable by standing, needs carbon filter.",
            )
        if chlorine_ppm is not None and chlorine_ppm > 0.003:
            return SafetyViolation(
                violation_type="chlorine",
                severity="warning",
                message_de=f"Freies Chlor {chlorine_ppm} ppm — Wasser 24-48h abstehen lassen oder Vitamin C.",
                message_en=f"Free chlorine {chlorine_ppm} ppm — let water stand 24-48h or add vitamin C.",
            )
        return None

    def validate_no_copper_pesticide(self, is_copper_based: bool) -> SafetyViolation | None:
        if is_copper_based:
            return SafetyViolation(
                violation_type="copper_pesticide",
                severity="block",
                message_de="Kupferbasierte Pflanzenschutzmittel sind in Aquaponik verboten (fischgiftig >0.1 ppm).",
                message_en="Copper-based pesticides are forbidden in aquaponics (fish-toxic above 0.1 ppm).",
            )
        return None

    def validate_water_change_rate(self, change_volume_l: float, system_volume_l: float) -> SafetyViolation | None:
        if system_volume_l <= 0:
            return None
        percent = change_volume_l / system_volume_l * 100
        if percent > 20:
            return SafetyViolation(
                violation_type="excessive_water_change",
                severity="warning",
                message_de=f"Wasserwechsel {round(percent, 1)}% (>20%) — Fischstress durch pH-/Temperaturschock.",
                message_en=f"Water change {round(percent, 1)}% (>20%) — fish stress from pH/temperature shock.",
            )
        return None

    def validate_temperature_compatibility(self, fish_species: FishSpecies, plant_zone: str) -> SafetyViolation | None:
        fish_zone = fish_species.temperature_zone.value
        if plant_zone and plant_zone != fish_zone:
            return SafetyViolation(
                violation_type="temperature_incompatible",
                severity="warning",
                message_de=f"Temperaturzone inkompatibel: Fisch {fish_zone} vs. Pflanze {plant_zone}.",
                message_en=f"Temperature zone incompatible: fish {fish_zone} vs. plant {plant_zone}.",
            )
        return None


class BiofilterManager:
    """Biofilter dimensioning, turnover and seasonal reactivation."""

    SSA_M2_PER_M3: dict[str, float] = {
        "media_bed_integrated": 300,
        "mbbr": 650,
        "trickle": 200,
        "fluidized_bed": 1000,
    }
    NITRIFICATION_RATE_G_PER_M2_PER_DAY = 0.5

    def __init__(self, feeding: FeedingRateCalculator | None = None) -> None:
        self._feeding = feeding or FeedingRateCalculator()

    @staticmethod
    def _temperature_factor(temp_c: float) -> float:
        if temp_c < 5:
            return 0.0
        if temp_c < 10:
            return 0.1
        return round(2 ** ((temp_c - 25) / 10), 3)

    def estimate_required_surface_area(
        self,
        daily_feed_g: float,
        temp_c: float,
        biofilter_type_value: str | None,
        biofilter_volume_liters: float | None,
        protein_percent: float = 32.0,
    ) -> BiofilterDimensioning:
        tan_production = self._feeding.calculate_tan_production(daily_feed_g, protein_percent)
        temp_factor = self._temperature_factor(temp_c)
        rate = self.NITRIFICATION_RATE_G_PER_M2_PER_DAY * temp_factor
        required_area = round(tan_production / rate, 2) if rate > 0 else 0.0

        current_area: float | None = None
        capacity = 0.0
        if biofilter_type_value and biofilter_volume_liters:
            ssa = self.SSA_M2_PER_M3.get(biofilter_type_value, 300)
            current_area = round(biofilter_volume_liters / 1000 * ssa, 2)
            capacity = round(current_area * rate, 3)

        if rate <= 0:
            status: Literal["sufficient", "marginal", "insufficient", "unknown"] = "unknown"
        elif current_area is None:
            status = "unknown"
        elif current_area >= required_area * 1.2:
            status = "sufficient"
        elif current_area >= required_area:
            status = "marginal"
        else:
            status = "insufficient"

        return BiofilterDimensioning(
            required_surface_area_m2=required_area,
            current_surface_area_m2=current_area,
            status=status,
            daily_tan_production_g=tan_production,
            filter_capacity_g_tan_per_day=capacity,
        )

    def calculate_turnover_rate(self, pump_flow_lph: float, system_volume_l: float) -> float:
        return round(pump_flow_lph / system_volume_l, 2) if system_volume_l > 0 else 0.0

    def seasonal_reactivation_plan(
        self, cycling_status: CyclingStatus, current_temp_c: float, target_feed_g: float
    ) -> RampUpSchedule | None:
        if cycling_status == CyclingStatus.DORMANT and current_temp_c > 15:
            return self._feeding.calculate_ramp_up_schedule(
                target_feed_g, reason="post_dormancy", water_temp_c=current_temp_c
            )
        return None


class FishHealthMonitor:
    """Fish-health alerts derived from mortality, feeding and water quality."""

    MORTALITY_RATE_WARNING = 0.02
    MORTALITY_RATE_CRITICAL = 0.05
    REFUSED_FEEDING_THRESHOLD = 2

    def __init__(self, nitrogen_engine: NitrogenCycleEngine | None = None) -> None:
        self._nitrogen = nitrogen_engine or NitrogenCycleEngine()

    def calculate_mortality_rate(self, fish_stock: FishStock, period_days: int = 7) -> float:
        """Cumulative mortality fraction relative to the initial stock."""
        if fish_stock.initial_count <= 0:
            return 0.0
        return round(fish_stock.mortality_count / fish_stock.initial_count, 4)

    def evaluate_fish_health(
        self,
        fish_stock: FishStock,
        recent_feedings: list[FishFeedingEvent],
        recent_water_tests: list[WaterTest],
        fish_species: FishSpecies | None,
    ) -> list[HealthAlert]:
        alerts: list[HealthAlert] = []

        rate = self.calculate_mortality_rate(fish_stock)
        if rate >= self.MORTALITY_RATE_CRITICAL:
            alerts.append(
                HealthAlert(
                    alert_type="mortality_rate",
                    severity="critical",
                    message_de=f"Mortalitätsrate {round(rate * 100, 1)}% kritisch (>5%).",
                    message_en=f"Mortality rate {round(rate * 100, 1)}% critical (>5%).",
                    recommended_action="Wasserwerte sofort prüfen, Futter stoppen, tote Fische entfernen.",
                )
            )
        elif rate >= self.MORTALITY_RATE_WARNING:
            alerts.append(
                HealthAlert(
                    alert_type="mortality_rate",
                    severity="warning",
                    message_de=f"Mortalitätsrate {round(rate * 100, 1)}% erhöht (>2%).",
                    message_en=f"Mortality rate {round(rate * 100, 1)}% elevated (>2%).",
                    recommended_action="Wasserqualität und Fressverhalten beobachten.",
                )
            )

        ordered = sorted(recent_feedings, key=lambda f: f.fed_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        refused_run = 0
        for feeding in ordered:
            if feeding.fish_response == FishFeedingResponse.REFUSED:
                refused_run += 1
            else:
                break
        if refused_run >= self.REFUSED_FEEDING_THRESHOLD:
            alerts.append(
                HealthAlert(
                    alert_type="feeding_refusal",
                    severity="warning",
                    message_de=f"{refused_run} aufeinanderfolgende Futterverweigerungen — Gesundheitsalarm.",
                    message_en=f"{refused_run} consecutive feeding refusals — health alert.",
                    recommended_action="Wasserwerte prüfen, auf Krankheitszeichen achten.",
                )
            )

        if recent_water_tests and fish_species is not None:
            latest = max(recent_water_tests, key=lambda t: t.tested_at or datetime.min.replace(tzinfo=UTC))
            for evaluation in self._nitrogen.evaluate_water_quality(latest, fish_species):
                if evaluation.severity == "critical":
                    alerts.append(
                        HealthAlert(
                            alert_type="water_quality",
                            severity="critical",
                            message_de=evaluation.message_de,
                            message_en=evaluation.message_en,
                            recommended_action="Sofort: Fütterung stoppen, Teilwasserwechsel, Belüftung erhöhen.",
                        )
                    )
        return alerts
