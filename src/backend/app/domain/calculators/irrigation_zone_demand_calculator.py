"""What an irrigation zone needs today, and what its water source can give (REQ-053 GP-FR-113/119, W-017; WP 7.5).

Pure: every input is an argument, nothing is read.

**Net litres.** One millimetre over one square metre is one litre, so a bed's net litres are the ``net_demand_mm``
that REQ-037 computed for the run standing in it (``irrigation_demands``, effective rain already deducted) times the
area the demand was computed for (the bed's ``area_m2`` at the time, stored on the demand). The zone's net litres
are the sum over its beds.

**Gross litres need an efficiency (E-10, #2466 item 4).** Gross = net / ``application_efficiency``. A value the user
set on the zone wins. Without one only **drip** has a default - 0.88, the design value of Howell 2003 / Alberta
Agdex 563-1 (``spec/analysis/agrobiology-thresholds-req-053.md`` R-005, status *corrected*). Every other type has
none: no source gives a design value for it (sprinkler 0.75 is only a 70-90 % range, manual 0.8 has no source), so
the efficiency is *unknown* and no gross value is made up.

**No W-017 cap (#2466 item 5).** The usable-water-capacity x substrate-volume ceiling for planter, raised bed and tent
has no sourced values; nothing here caps the single dose.

**Zone type vs bed system (GP-FR-119, #2466 item 3).** The two value sets differ (zone: manual, drip, sprinkler,
soaker_hose, sub_irrigation; bed: manual, drip, hydro, mist, nft, ebb_flow); only ``manual`` and ``drip`` occur in
both. A hint arises only when the zone's type and the bed's system are both such shared values and differ - the zone
wins for demand and consumption, the hint just says the bed is equipped otherwise.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal

from app.common.enums import IrrigationSystem, IrrigationZoneType

#: The one type with a sourced default (R-005); every other type maps to "unknown", not to a guess.
DEFAULT_APPLICATION_EFFICIENCY: Mapping[IrrigationZoneType, float | None] = {
    IrrigationZoneType.DRIP: 0.88,
    IrrigationZoneType.MANUAL: None,
    IrrigationZoneType.SPRINKLER: None,
    IrrigationZoneType.SOAKER_HOSE: None,
    IrrigationZoneType.SUB_IRRIGATION: None,
}

#: Values both ``IrrigationZoneType`` and ``IrrigationSystem`` carry.
SHARED_IRRIGATION_VALUES: frozenset[str] = frozenset({IrrigationZoneType.MANUAL.value, IrrigationZoneType.DRIP.value})

type EfficiencySource = Literal["zone", "type_default"]


@dataclass(frozen=True)
class BedDemand:
    """The demand REQ-037 computed for the run in one bed: depth in mm over the area it was computed for."""

    location_key: str
    net_demand_mm: float
    area_m2: float


@dataclass(frozen=True)
class Efficiency:
    """The application efficiency in force, and where it comes from; ``value is None`` = unknown."""

    value: float | None
    source: EfficiencySource | None


@dataclass(frozen=True)
class ZoneDemand:
    """A zone's litres for one day: net always, gross only with a known efficiency."""

    net_liters: float
    gross_liters: float | None
    efficiency: Efficiency
    bed_count: int


def net_liters(demand: BedDemand) -> float:
    """``net_demand_mm`` x ``area_m2`` (1 mm over 1 m² = 1 L); a negative depth is no demand."""
    return max(demand.net_demand_mm, 0.0) * max(demand.area_m2, 0.0)


def effective_efficiency(irrigation_type: IrrigationZoneType, stored: float | None) -> Efficiency:
    """The zone's own value if set, else the sourced default of the type, else unknown (E-10)."""
    if stored is not None:
        return Efficiency(stored, "zone")
    default = DEFAULT_APPLICATION_EFFICIENCY.get(irrigation_type)
    return Efficiency(default, "type_default") if default is not None else Efficiency(None, None)


def zone_demand(
    irrigation_type: IrrigationZoneType, application_efficiency: float | None, beds: Iterable[BedDemand]
) -> ZoneDemand:
    """Sum the beds' net litres and divide by the efficiency when one is known."""
    demands = list(beds)
    net = round(sum(net_liters(demand) for demand in demands), 2)
    efficiency = effective_efficiency(irrigation_type, application_efficiency)
    gross = round(net / efficiency.value, 2) if efficiency.value else None
    return ZoneDemand(net_liters=net, gross_liters=gross, efficiency=efficiency, bed_count=len(demands))


def days_of_supply(capacity_liters: float | None, daily_liters: float) -> int | None:
    """Whole days a water source of ``capacity_liters`` lasts at ``daily_liters``; ``None`` without both values."""
    if capacity_liters is None or capacity_liters <= 0 or daily_liters <= 0:
        return None
    return math.floor(capacity_liters / daily_liters)


def irrigation_system_differs(zone_type: IrrigationZoneType, bed_system: IrrigationSystem) -> bool:
    """Whether the bed's own system contradicts the zone's type, judged on the values both sets share only."""
    return (
        zone_type.value in SHARED_IRRIGATION_VALUES
        and bed_system.value in SHARED_IRRIGATION_VALUES
        and zone_type.value != bed_system.value
    )
