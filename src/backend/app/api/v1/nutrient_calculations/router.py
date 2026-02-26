from fastapi import APIRouter, Depends

from app.api.v1.nutrient_calculations.schemas import (
    FlushingRequest,
    MixingProtocolRequest,
    MixingSafetyRequest,
    RunoffRequest,
)
from app.common.dependencies import get_fertilizer_service
from app.common.enums import SubstrateType
from app.domain.engines.nutrient_engine import (
    FlushingProtocol,
    MixingSafetyValidator,
    NutrientSolutionCalculator,
    RunoffAnalyzer,
)
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
