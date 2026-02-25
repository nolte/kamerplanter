from fastapi import APIRouter

from app.api.v1.calculations.schemas import (
    GDDRequest,
    GDDResponse,
    PhotoperiodTransitionRequest,
    SlotCapacityRequest,
    SlotCapacityResponse,
    VPDRequest,
    VPDResponse,
)
from app.domain.calculators.gdd_calculator import calculate_accumulated_gdd
from app.domain.calculators.photoperiod_calculator import calculate_dli, calculate_transition_schedule
from app.domain.calculators.slot_capacity_calculator import (
    calculate_max_capacity,
    calculate_optimal_range,
    calculate_plants_per_m2,
)
from app.domain.calculators.vpd_calculator import calculate_vpd, classify_vpd

router = APIRouter(prefix="/calculations", tags=["calculations"])

@router.post("/vpd", response_model=VPDResponse)
def calc_vpd(body: VPDRequest):
    vpd = calculate_vpd(body.temp_c, body.humidity_percent)
    status, recommendation = classify_vpd(vpd, body.phase)
    return VPDResponse(vpd_kpa=round(vpd, 4), status=status, recommendation=recommendation)

@router.post("/gdd", response_model=GDDResponse)
def calc_gdd(body: GDDRequest):
    gdd = calculate_accumulated_gdd(body.daily_temps, body.base_temp_c)
    return GDDResponse(accumulated_gdd=round(gdd, 2), days_counted=len(body.daily_temps))

@router.post("/photoperiod-transition")
def calc_photoperiod(body: PhotoperiodTransitionRequest):
    schedule = calculate_transition_schedule(body.current_hours, body.target_hours, body.transition_days)
    for entry in schedule:
        entry["dli"] = round(calculate_dli(body.ppfd, entry["photoperiod_hours"]), 2)
    return {"schedule": schedule}

@router.post("/slot-capacity", response_model=SlotCapacityResponse)
def calc_slot_capacity(body: SlotCapacityRequest):
    max_cap = calculate_max_capacity(body.area_m2, body.plant_spacing_cm)
    opt_range = calculate_optimal_range(body.area_m2, body.plant_spacing_cm)
    ppm2 = calculate_plants_per_m2(body.plant_spacing_cm)
    return SlotCapacityResponse(max_capacity=max_cap, optimal_range=opt_range, plants_per_m2=round(ppm2, 2))
