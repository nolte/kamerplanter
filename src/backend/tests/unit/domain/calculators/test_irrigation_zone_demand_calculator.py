"""REQ-053 WP 7.5 (#2471) - the zone demand calculator: net litres, gross only with a sourced efficiency (E-10)."""

from __future__ import annotations

import pytest

from app.common.enums import IrrigationSystem, IrrigationZoneType
from app.domain.calculators.irrigation_zone_demand_calculator import (
    DEFAULT_APPLICATION_EFFICIENCY,
    BedDemand,
    days_of_supply,
    effective_efficiency,
    irrigation_system_differs,
    net_liters,
    zone_demand,
)

BEDS = [BedDemand("b1", net_demand_mm=3.0, area_m2=6.0), BedDemand("b2", net_demand_mm=2.5, area_m2=2.0)]


class TestNetLiters:
    def test_one_millimetre_over_one_square_metre_is_one_litre(self) -> None:
        assert net_liters(BedDemand("b", 1.0, 1.0)) == 1.0
        assert net_liters(BEDS[0]) == 18.0

    def test_no_depth_or_no_area_is_no_demand(self) -> None:
        assert net_liters(BedDemand("b", -0.4, 5.0)) == 0.0
        assert net_liters(BedDemand("b", 2.0, 0.0)) == 0.0


class TestEfficiency:
    def test_only_drip_has_a_default_and_every_other_type_is_unknown(self) -> None:
        assert DEFAULT_APPLICATION_EFFICIENCY[IrrigationZoneType.DRIP] == 0.88
        assert {t for t, v in DEFAULT_APPLICATION_EFFICIENCY.items() if v is None} == {
            IrrigationZoneType.MANUAL,
            IrrigationZoneType.SPRINKLER,
            IrrigationZoneType.SOAKER_HOSE,
            IrrigationZoneType.SUB_IRRIGATION,
        }
        assert set(DEFAULT_APPLICATION_EFFICIENCY) == set(IrrigationZoneType)  # a new type must be decided here

    @pytest.mark.parametrize("zone_type", list(IrrigationZoneType))
    def test_a_value_set_on_the_zone_wins_for_every_type(self, zone_type) -> None:
        found = effective_efficiency(zone_type, 0.7)
        assert (found.value, found.source) == (0.7, "zone")


class TestZoneDemand:
    @pytest.mark.parametrize(
        ("zone_type", "stored", "gross", "source"),
        [
            (IrrigationZoneType.DRIP, None, round(23.0 / 0.88, 2), "type_default"),
            (IrrigationZoneType.DRIP, 0.9, round(23.0 / 0.9, 2), "zone"),
            (IrrigationZoneType.SPRINKLER, None, None, None),
            (IrrigationZoneType.MANUAL, None, None, None),
            (IrrigationZoneType.SOAKER_HOSE, None, None, None),
            (IrrigationZoneType.SUB_IRRIGATION, None, None, None),
            (IrrigationZoneType.SPRINKLER, 0.75, round(23.0 / 0.75, 2), "zone"),
        ],
    )
    def test_gross_exists_only_with_a_known_efficiency(self, zone_type, stored, gross, source) -> None:
        demand = zone_demand(zone_type, stored, BEDS)

        assert demand.net_liters == 23.0 and demand.bed_count == 2
        assert (demand.gross_liters, demand.efficiency.source) == (gross, source)

    def test_a_zone_without_beds_has_no_litres(self) -> None:
        demand = zone_demand(IrrigationZoneType.DRIP, None, [])

        assert (demand.net_liters, demand.bed_count) == (0.0, 0)


class TestWaterSourceReserve:
    def test_whole_days_the_source_lasts(self) -> None:
        assert days_of_supply(200.0, 45.0) == 4

    @pytest.mark.parametrize(("capacity", "daily"), [(None, 10.0), (0.0, 10.0), (200.0, 0.0)])
    def test_no_hint_without_a_capacity_or_a_demand(self, capacity, daily) -> None:
        assert days_of_supply(capacity, daily) is None


class TestSystemConflict:
    @pytest.mark.parametrize(
        ("zone_type", "bed", "differs"),
        [
            (IrrigationZoneType.DRIP, IrrigationSystem.MANUAL, True),
            (IrrigationZoneType.MANUAL, IrrigationSystem.DRIP, True),
            (IrrigationZoneType.DRIP, IrrigationSystem.DRIP, False),
            (IrrigationZoneType.MANUAL, IrrigationSystem.MANUAL, False),
            (IrrigationZoneType.SPRINKLER, IrrigationSystem.DRIP, False),
            (IrrigationZoneType.DRIP, IrrigationSystem.HYDRO, False),
            (IrrigationZoneType.SOAKER_HOSE, IrrigationSystem.NFT, False),
        ],
    )
    def test_a_hint_needs_both_values_to_be_shared_ones_and_to_differ(self, zone_type, bed, differs) -> None:
        assert irrigation_system_differs(zone_type, bed) is differs
