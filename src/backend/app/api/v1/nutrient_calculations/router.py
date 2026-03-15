from fastapi import APIRouter, Depends

from app.api.v1.nutrient_calculations.schemas import (
    CalMagCorrectionResponse,
    EcBudgetRequest,
    EcBudgetResponse,
    EcSegmentResponse,
    EffectiveWaterProfileResponse,
    FlushingRequest,
    MixingProtocolRequest,
    MixingSafetyRequest,
    RunoffRequest,
    WaterMixRequest,
    WaterMixResponse,
    WaterMixReverseRequest,
    WaterMixReverseResponse,
    WaterSourceWarningResponse,
)
from app.common.dependencies import get_fertilizer_service
from app.common.enums import PhaseName, SubstrateType
from app.domain.engines.ec_budget_engine import (
    EcBudgetCalculator,
    EcBudgetFertilizerInput,
    EcBudgetInput,
)
from app.domain.engines.nutrient_engine import (
    FlushingProtocol,
    MixingSafetyValidator,
    NutrientSolutionCalculator,
    RunoffAnalyzer,
)
from app.domain.engines.water_mix_engine import WaterMixCalculator, WaterSourceValidator
from app.domain.models.site import RoWaterProfile, TapWaterProfile
from app.domain.services.fertilizer_service import FertilizerService

router = APIRouter(prefix="/nutrient-calculations", tags=["nutrient-calculations"])


@router.post("/mixing-protocol")
def mixing_protocol(
    body: MixingProtocolRequest,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    fertilizers = []
    for key in body.fertilizer_keys:
        fert = service.get_fertilizer(key)
        fertilizers.append(fert)

    substrate = SubstrateType(body.substrate_type)
    calculator = NutrientSolutionCalculator()
    return calculator.calculate(
        target_volume_liters=body.target_volume_liters,
        target_ec_ms=body.target_ec_ms,
        target_ph=body.target_ph,
        base_water_ec=body.base_water_ec,
        base_water_ph=body.base_water_ph,
        fertilizers=fertilizers,
        substrate_type=substrate,
    )


@router.post("/flushing")
def flushing_protocol(body: FlushingRequest):
    substrate = SubstrateType(body.substrate_type)
    protocol = FlushingProtocol()
    return protocol.generate(
        current_ec_ms=body.current_ec_ms,
        days_until_harvest=body.days_until_harvest,
        substrate_type=substrate,
    )


@router.post("/runoff")
def runoff_analysis(body: RunoffRequest):
    analyzer = RunoffAnalyzer()
    return analyzer.analyze(
        input_ec_ms=body.input_ec_ms,
        runoff_ec_ms=body.runoff_ec_ms,
        input_ph=body.input_ph,
        runoff_ph=body.runoff_ph,
        input_volume_liters=body.input_volume_liters,
        runoff_volume_liters=body.runoff_volume_liters,
    )


@router.post("/mixing-safety")
def mixing_safety(
    body: MixingSafetyRequest,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    fertilizers = []
    for key in body.fertilizer_keys:
        fert = service.get_fertilizer(key)
        fertilizers.append(fert)

    validator = MixingSafetyValidator()
    return validator.validate_combination(fertilizers)


@router.post("/water-mix", response_model=WaterMixResponse)
def water_mix(body: WaterMixRequest):
    tap = TapWaterProfile(
        ec_ms=body.tap_profile.ec_ms,
        ph=body.tap_profile.ph,
        alkalinity_ppm=body.tap_profile.alkalinity_ppm,
        gh_ppm=body.tap_profile.gh_ppm,
        calcium_ppm=body.tap_profile.calcium_ppm,
        magnesium_ppm=body.tap_profile.magnesium_ppm,
        chlorine_ppm=body.tap_profile.chlorine_ppm,
        chloramine_ppm=body.tap_profile.chloramine_ppm,
        measurement_date=body.tap_profile.measurement_date,
    )
    ro = RoWaterProfile(ec_ms=body.ro_profile.ec_ms, ph=body.ro_profile.ph)

    calculator = WaterMixCalculator()
    effective = calculator.calculate_effective_water(tap, ro, body.ro_percent)

    calmag = None
    if body.target_ca_ppm > 0 or body.target_mg_ppm > 0:
        correction = calculator.suggest_calmag_correction(
            effective,
            body.target_ca_ppm,
            body.target_mg_ppm,
        )
        calmag = CalMagCorrectionResponse(
            calcium_deficit_ppm=correction.calcium_deficit_ppm,
            magnesium_deficit_ppm=correction.magnesium_deficit_ppm,
            ca_mg_ratio=correction.ca_mg_ratio,
            ca_mg_ratio_warning=correction.ca_mg_ratio_warning,
            needs_correction=correction.needs_correction,
        )

    validator = WaterSourceValidator()
    warnings = validator.validate_all(tap, ro)

    return WaterMixResponse(
        effective_profile=EffectiveWaterProfileResponse(**effective.model_dump()),
        calmag_correction=calmag,
        warnings=[WaterSourceWarningResponse(code=w.code, message=w.message, severity=w.severity) for w in warnings],
    )


@router.post("/water-mix/reverse", response_model=WaterMixReverseResponse)
def water_mix_reverse(body: WaterMixReverseRequest):
    tap = TapWaterProfile(
        ec_ms=body.tap_profile.ec_ms,
        ph=body.tap_profile.ph,
        alkalinity_ppm=body.tap_profile.alkalinity_ppm,
        gh_ppm=body.tap_profile.gh_ppm,
        calcium_ppm=body.tap_profile.calcium_ppm,
        magnesium_ppm=body.tap_profile.magnesium_ppm,
        chlorine_ppm=body.tap_profile.chlorine_ppm,
        chloramine_ppm=body.tap_profile.chloramine_ppm,
        measurement_date=body.tap_profile.measurement_date,
    )
    ro = RoWaterProfile(ec_ms=body.ro_profile.ec_ms, ph=body.ro_profile.ph)

    calculator = WaterMixCalculator()
    ro_percent = calculator.calculate_ro_percent_for_target(tap, ro, body.target_base_ec_ms)
    effective = calculator.calculate_effective_water(tap, ro, ro_percent)

    return WaterMixReverseResponse(
        ro_percent=ro_percent,
        effective_profile=EffectiveWaterProfileResponse(**effective.model_dump()),
    )


@router.post("/ec-budget", response_model=EcBudgetResponse)
def ec_budget(
    body: EcBudgetRequest,
    service: FertilizerService = Depends(get_fertilizer_service),
):
    substrate = SubstrateType(body.substrate)
    phase = PhaseName(body.phase)

    # Resolve fertilizer keys → domain models
    fert_inputs: list[EcBudgetFertilizerInput] = []
    recipe_map: dict[str, float] = {}

    for fert_req in body.fertilizer_keys:
        fert = service.get_fertilizer(fert_req.key)
        fert_inputs.append(
            EcBudgetFertilizerInput(
                key=fert_req.key,
                product_name=fert.product_name,
                ec_contribution_per_ml=fert.ec_contribution_per_ml,
                ec_contribution_uncertain=fert.ec_contribution_uncertain,
                max_dose_ml_per_liter=fert.max_dose_ml_per_liter,
                fertilizer_type=fert.fertilizer_type,
            )
        )
        if fert_req.recipe_ml_per_liter is not None:
            recipe_map[fert_req.key] = fert_req.recipe_ml_per_liter

    # Resolve CalMag EC if provided
    calmag_ec_per_ml = 0.0
    if body.calmag_key:
        calmag_fert = service.get_fertilizer(body.calmag_key)
        calmag_ec_per_ml = calmag_fert.ec_contribution_per_ml

    # Resolve Silicate EC if provided
    silicate_ec_per_ml = 0.0
    if body.silicate_key:
        silicate_fert = service.get_fertilizer(body.silicate_key)
        silicate_ec_per_ml = silicate_fert.ec_contribution_per_ml

    inp = EcBudgetInput(
        base_water_ec=body.base_water_ec,
        target_ec=body.target_ec,
        alkalinity_ppm=body.alkalinity_ppm,
        substrate=substrate,
        phase=phase,
        volume_liters=body.volume_liters,
        fertilizers=fert_inputs,
        recipe_ml_per_liter=recipe_map,
        calmag_key=body.calmag_key,
        calmag_dose_ml_per_liter=body.calmag_dose_ml_per_liter,
        calmag_ec_per_ml=calmag_ec_per_ml,
        silicate_key=body.silicate_key,
        silicate_dose_ml_per_liter=body.silicate_dose_ml_per_liter,
        silicate_ec_per_ml=silicate_ec_per_ml,
        substrate_cycles_used=body.substrate_cycles_used,
        measured_ec=body.measured_ec,
        measured_temp_celsius=body.measured_temp_celsius,
    )

    calculator = EcBudgetCalculator()
    result = calculator.calculate(inp)

    return EcBudgetResponse(
        ec_mix=result.ec_mix,
        ec_net=result.ec_net,
        ec_silicate=result.ec_silicate,
        ec_calmag=result.ec_calmag,
        ec_fertilizers=result.ec_fertilizers,
        ec_ph_reserve=result.ec_ph_reserve,
        ec_final=result.ec_final,
        ec_max=result.ec_max,
        ec_target=result.ec_target,
        ec_at_25_corrected=result.ec_at_25_corrected,
        tolerance=result.tolerance,
        valid=result.valid,
        living_soil_bypass=result.living_soil_bypass,
        segments=[EcSegmentResponse(**s.model_dump()) for s in result.segments],
        warnings=result.warnings,
        dosage_table=result.dosage_table,
        dosage_instructions=result.dosage_instructions,
    )
