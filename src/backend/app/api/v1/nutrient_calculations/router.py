from fastapi import APIRouter, Depends

from app.api.v1.nutrient_calculations.schemas import (
    AreaDosingItemResponse,
    AreaDosingRequest,
    AreaDosingResponse,
    CalMagCorrectionResponse,
    EcBudgetRequest,
    EcBudgetResponse,
    EcSegmentResponse,
    EffectiveWaterProfileResponse,
    FlushingRequest,
    MixingProtocolDosage,
    MixingProtocolRequest,
    MixingProtocolResponse,
    MixingSafetyRequest,
    PhAdjustmentResponse,
    RunoffRequest,
    WaterMixRequest,
    WaterMixResponse,
    WaterMixReverseRequest,
    WaterMixReverseResponse,
    WaterSourceWarningResponse,
)
from app.common.auth import get_current_tenant
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
    RunoffAnalyzer,
    _ph_adjustment,
)
from app.domain.engines.water_mix_engine import WaterMixCalculator, WaterSourceValidator
from app.domain.models.site import RoWaterProfile, TapWaterProfile
from app.domain.models.tenant_context import TenantContext
from app.domain.services.fertilizer_service import FertilizerService

router = APIRouter(prefix="/nutrient-calculations", tags=["nutrient-calculations"])


@router.post("/mixing-protocol", response_model=MixingProtocolResponse)
def mixing_protocol(
    body: MixingProtocolRequest,
    service: FertilizerService = Depends(get_fertilizer_service),
) -> MixingProtocolResponse:
    """Compute a mixing protocol via the canonical EC-budget pipeline (REQ-004-A).

    DOM-5 fix: this endpoint now runs the REQ-004-A-compliant EcBudgetCalculator
    (pH reserve + pre-deductions), so ml/L doses are lower than the legacy
    NutrientSolutionCalculator (which ignored the pH reserve and overshot the
    target EC after pH correction). The legacy response shape is preserved and
    additively extended with ``ec_net``, ``ec_ph_reserve`` and ``valid``.
    """
    substrate = SubstrateType(body.substrate_type)
    phase = PhaseName(body.phase)

    fert_inputs: list[EcBudgetFertilizerInput] = []
    for key in body.fertilizer_keys:
        fert = service.get_fertilizer(key)
        fert_inputs.append(
            EcBudgetFertilizerInput(
                key=key,
                product_name=fert.product_name,
                ec_contribution_per_ml=fert.ec_contribution_per_ml,
                ec_contribution_uncertain=fert.ec_contribution_uncertain,
                max_dose_ml_per_liter=fert.max_dose_ml_per_liter,
                fertilizer_type=fert.fertilizer_type,
            )
        )

    inp = EcBudgetInput(
        base_water_ec=body.base_water_ec,
        target_ec=body.target_ec_ms,
        alkalinity_ppm=body.alkalinity_ppm,
        substrate=substrate,
        phase=phase,
        volume_liters=body.target_volume_liters,
        fertilizers=fert_inputs,
        recipe_ml_per_liter=body.recipe_ml_per_liter or {},
    )

    result = EcBudgetCalculator().calculate(inp)

    dosages = [
        MixingProtocolDosage(
            fertilizer_key=row.get("key"),
            product_name=row.get("product_name", ""),
            ml_per_liter=row.get("ml_per_liter", 0.0),
            total_ml=row.get("total_ml", 0.0),
            ec_contribution=row.get("ec_contribution", 0.0),
        )
        for row in result.dosage_table
    ]
    ph_adj = _ph_adjustment(body.base_water_ph, body.target_ph)

    return MixingProtocolResponse(
        dosages=dosages,
        calculated_ec=result.ec_final,
        ph_adjustment=PhAdjustmentResponse(**ph_adj),
        warnings=result.warnings,
        instructions=result.dosage_instructions,
        ec_net=result.ec_net,
        ec_ph_reserve=result.ec_ph_reserve,
        valid=result.valid,
    )


@router.post("/area-dosing", response_model=AreaDosingResponse)
def area_dosing(
    body: AreaDosingRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: FertilizerService = Depends(get_fertilizer_service),
) -> AreaDosingResponse:
    """Compute per-area organic fertilizer amounts (REQ-004 W-013, AP-11).

    Area is taken from an explicit ``area_m2`` (override) or resolved from
    ``location_key`` (Location.area_m2, scoped to the caller's tenant). Solid
    amendments are dosed g/m² and L/m² instead of ml/L.
    """
    result = service.calculate_area_dosage(
        fertilizer_keys=body.fertilizer_keys,
        area_m2=body.area_m2,
        location_key=body.location_key,
        demand_level=body.demand_level,
        tenant_key=ctx.tenant_key,
    )
    return AreaDosingResponse(
        area_m2=result.area_m2,
        items=[AreaDosingItemResponse(**item.model_dump()) for item in result.items],
        warnings=result.warnings,
        instructions=result.instructions,
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
