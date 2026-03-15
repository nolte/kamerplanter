"""Tests for SowingCalendarEngine."""

from datetime import date, timedelta

import pytest

from app.common.enums import FrostTolerance
from app.domain.engines.sowing_calendar_engine import (
    FrostConfig,
    GrowingPeriodData,
    SowingCalendarEngine,
    SpeciesData,
    _split_into_periods,
)


@pytest.fixture
def engine():
    return SowingCalendarEngine()


@pytest.fixture
def frost_config():
    return FrostConfig(
        last_frost_date=date(2026, 5, 15),
        eisheilige_date=date(2026, 5, 15),
    )


def _make_species(**overrides) -> SpeciesData:
    defaults = {
        "key": "sp1",
        "scientific_name": "Capsicum annuum",
        "common_names": ["Paprika"],
    }
    defaults.update(overrides)
    return SpeciesData(**defaults)


class TestSplitIntoPeriods:
    def test_contiguous_months(self):
        assert _split_into_periods([3, 4, 5, 6]) == [(3, 6)]

    def test_split_months(self):
        assert _split_into_periods([3, 4, 5, 6, 9, 10]) == [(3, 6), (9, 10)]

    def test_single_month(self):
        assert _split_into_periods([7]) == [(7, 7)]

    def test_empty(self):
        assert _split_into_periods([]) == []

    def test_non_contiguous(self):
        assert _split_into_periods([1, 3, 5]) == [(1, 1), (3, 3), (5, 5)]

    def test_wrap_around(self):
        """Year-crossing months: [8,9,10,11,12,1,2,3] -> single wrap-around period."""
        assert _split_into_periods([8, 9, 10, 11, 12, 1, 2, 3]) == [(8, 3)]

    def test_wrap_around_with_gap(self):
        """[1,2,3,8,9,10,11,12] same as above — order doesn't matter."""
        assert _split_into_periods([1, 2, 3, 8, 9, 10, 11, 12]) == [(8, 3)]

    def test_wrap_around_plus_middle(self):
        """Wrap-around + separate middle period."""
        assert _split_into_periods([1, 2, 6, 7, 11, 12]) == [(11, 2), (6, 7)]

    def test_no_wrap_when_no_month_1(self):
        """No month 1 -> no wrap-around detection."""
        assert _split_into_periods([3, 4, 11, 12]) == [(3, 4), (11, 12)]

    def test_no_wrap_when_no_month_12(self):
        """No month 12 -> no wrap-around detection."""
        assert _split_into_periods([1, 2, 9, 10]) == [(1, 2), (9, 10)]


class TestAutoCreatePeriods:
    """SpeciesData auto-converts legacy flat fields to a single GrowingPeriod."""

    def test_flat_fields_create_single_period(self):
        sp = _make_species(
            sowing_indoor_weeks_before_last_frost=8,
            harvest_months=[7, 8],
        )
        assert len(sp.growing_periods) == 1
        assert sp.growing_periods[0].sowing_indoor_weeks_before_last_frost == 8
        assert sp.growing_periods[0].harvest_months == [7, 8]

    def test_explicit_periods_not_overwritten(self):
        sp = _make_species(
            growing_periods=[
                GrowingPeriodData(label="A", direct_sow_months=[3, 4]),
                GrowingPeriodData(label="B", direct_sow_months=[9, 10]),
            ],
            direct_sow_months=[1, 2],  # legacy — should be ignored
        )
        assert len(sp.growing_periods) == 2
        assert sp.growing_periods[0].label == "A"

    def test_no_data_no_periods(self):
        sp = _make_species()
        assert sp.growing_periods == []


class TestCalculateBars:
    def test_indoor_sowing_bar(self, engine, frost_config):
        sp = _make_species(sowing_indoor_weeks_before_last_frost=10)
        bars = engine.calculate_bars(sp, frost_config, 2026)

        indoor_bars = [b for b in bars if b.phase == "indoor_sowing"]
        assert len(indoor_bars) == 1
        bar = indoor_bars[0]
        assert bar.start_date == date(2026, 3, 6)
        assert bar.end_date == date(2026, 5, 14)

    def test_outdoor_planting_bar(self, engine, frost_config):
        sp = _make_species(sowing_outdoor_after_last_frost_days=0)
        bars = engine.calculate_bars(sp, frost_config, 2026)

        outdoor_bars = [b for b in bars if b.phase == "outdoor_planting"]
        assert len(outdoor_bars) == 1
        assert outdoor_bars[0].start_date == date(2026, 5, 15)
        assert outdoor_bars[0].end_date == date(2026, 5, 28)

    def test_eisheiligen_delay_for_sensitive(self, engine):
        frost_config = FrostConfig(
            last_frost_date=date(2026, 5, 1),
            eisheilige_date=date(2026, 5, 15),
        )
        sp = _make_species(
            sowing_outdoor_after_last_frost_days=0,
            frost_sensitivity=FrostTolerance.SENSITIVE,
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        outdoor_bars = [b for b in bars if b.phase == "outdoor_planting"]
        assert len(outdoor_bars) == 1
        assert outdoor_bars[0].start_date == date(2026, 5, 16)

    def test_no_eisheiligen_delay_for_hardy(self, engine):
        frost_config = FrostConfig(
            last_frost_date=date(2026, 5, 1),
            eisheilige_date=date(2026, 5, 15),
        )
        sp = _make_species(
            sowing_outdoor_after_last_frost_days=0,
            frost_sensitivity=FrostTolerance.HARDY,
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        outdoor_bars = [b for b in bars if b.phase == "outdoor_planting"]
        assert len(outdoor_bars) == 1
        assert outdoor_bars[0].start_date == date(2026, 5, 1)

    def test_harvest_months(self, engine, frost_config):
        sp = _make_species(harvest_months=[7, 8, 9])
        bars = engine.calculate_bars(sp, frost_config, 2026)
        harvest_bars = [b for b in bars if b.phase == "harvest"]
        assert len(harvest_bars) == 1
        assert harvest_bars[0].start_date == date(2026, 7, 1)
        assert harvest_bars[0].end_date == date(2026, 9, 30)

    def test_ornamental_uses_flowering(self, engine, frost_config):
        sp = _make_species(
            allows_harvest=False,
            bloom_months=[5, 6, 7],
            harvest_months=[8, 9],
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        flowering_bars = [b for b in bars if b.phase == "flowering"]
        harvest_bars = [b for b in bars if b.phase == "harvest"]
        assert len(flowering_bars) == 1
        assert len(harvest_bars) == 0

    def test_growth_bar_fills_gap(self, engine, frost_config):
        sp = _make_species(
            sowing_outdoor_after_last_frost_days=0,
            harvest_months=[8, 9],
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        growth_bars = [b for b in bars if b.phase == "growth"]
        assert len(growth_bars) == 1
        assert growth_bars[0].start_date == date(2026, 5, 29)
        assert growth_bars[0].end_date == date(2026, 7, 31)

    def test_no_bars_without_data(self, engine, frost_config):
        sp = _make_species()
        bars = engine.calculate_bars(sp, frost_config, 2026)
        assert bars == []

    def test_direct_sow_months(self, engine, frost_config):
        sp = _make_species(direct_sow_months=[3, 4, 5])
        bars = engine.calculate_bars(sp, frost_config, 2026)
        outdoor_bars = [b for b in bars if b.phase == "outdoor_planting"]
        assert len(outdoor_bars) == 1
        assert outdoor_bars[0].start_date == date(2026, 3, 1)
        assert outdoor_bars[0].end_date == date(2026, 5, 31)

    def test_split_harvest_months(self, engine, frost_config):
        sp = _make_species(harvest_months=[6, 7, 10, 11])
        bars = engine.calculate_bars(sp, frost_config, 2026)
        harvest_bars = [b for b in bars if b.phase == "harvest"]
        assert len(harvest_bars) == 2

    def test_growth_bar_indoor_only_no_outdoor(self, engine, frost_config):
        """Knollensellerie case: indoor sowing + harvest but no outdoor planting."""
        sp = _make_species(
            scientific_name="Apium graveolens var. rapaceum",
            common_names=["Knollensellerie"],
            sowing_indoor_weeks_before_last_frost=11,
            sowing_outdoor_after_last_frost_days=None,
            harvest_months=[9, 10, 11],
            frost_sensitivity=FrostTolerance.MODERATE,
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        indoor_bars = [b for b in bars if b.phase == "indoor_sowing"]
        growth_bars = [b for b in bars if b.phase == "growth"]
        harvest_bars = [b for b in bars if b.phase == "harvest"]

        assert len(indoor_bars) == 1
        assert len(harvest_bars) == 1
        assert len(growth_bars) == 1
        assert growth_bars[0].start_date == indoor_bars[0].end_date + timedelta(days=1)
        assert growth_bars[0].end_date == harvest_bars[0].start_date - timedelta(days=1)

    def test_direct_sow_months_preferred_over_outdoor_days(self, engine, frost_config):
        sp = _make_species(
            sowing_outdoor_after_last_frost_days=0,
            direct_sow_months=[5, 6],
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        outdoor_bars = [b for b in bars if b.phase == "outdoor_planting"]
        assert len(outdoor_bars) == 1
        assert outdoor_bars[0].start_date == date(2026, 5, 1)
        assert outdoor_bars[0].end_date == date(2026, 6, 30)

    def test_no_growth_bar_when_contiguous(self, engine, frost_config):
        """§5.2: Phases contiguous — no growth bar needed."""
        sp = _make_species(direct_sow_months=[5, 6], harvest_months=[7, 8, 9])
        bars = engine.calculate_bars(sp, frost_config, 2026)
        growth_bars = [b for b in bars if b.phase == "growth"]
        assert len(growth_bars) == 0

    def test_growth_bar_fills_indoor_to_outdoor_gap(self, engine, frost_config):
        """§5.2: Lavender — growth bar fills gap between indoor end and outdoor start."""
        sp = _make_species(
            sowing_indoor_weeks_before_last_frost=8,
            sowing_outdoor_after_last_frost_days=14,
            bloom_months=[6, 7, 8],
            allows_harvest=False,
            frost_sensitivity=FrostTolerance.HARDY,
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        indoor_bars = [b for b in bars if b.phase == "indoor_sowing"]
        outdoor_bars = [b for b in bars if b.phase == "outdoor_planting"]
        growth_bars = [b for b in bars if b.phase == "growth"]

        assert len(indoor_bars) == 1
        assert len(outdoor_bars) == 1
        assert len(growth_bars) == 1
        assert growth_bars[0].start_date == indoor_bars[0].end_date + timedelta(days=1)
        assert growth_bars[0].end_date == outdoor_bars[0].start_date - timedelta(days=1)

    def test_no_growth_bar_when_indoor_outdoor_contiguous(self, engine, frost_config):
        sp = _make_species(
            sowing_indoor_weeks_before_last_frost=8,
            sowing_outdoor_after_last_frost_days=0,
            harvest_months=[8, 9],
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        growth_bars = [b for b in bars if b.phase == "growth"]
        assert len(growth_bars) == 1
        outdoor_bars = [b for b in bars if b.phase == "outdoor_planting"]
        harvest_bars = [b for b in bars if b.phase == "harvest"]
        assert growth_bars[0].start_date == outdoor_bars[0].end_date + timedelta(days=1)
        assert growth_bars[0].end_date == harvest_bars[0].start_date - timedelta(days=1)

    def test_outdoor_clipped_to_after_indoor(self, engine, frost_config):
        """§5.1: Parsley — outdoor clipped to start after indoor ends."""
        sp = _make_species(
            sowing_indoor_weeks_before_last_frost=9,
            direct_sow_months=[3, 4, 5, 6, 7],
            harvest_months=[5, 6, 7, 8, 9, 10, 11],
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        indoor_bars = [b for b in bars if b.phase == "indoor_sowing"]
        outdoor_bars = [b for b in bars if b.phase == "outdoor_planting"]

        assert len(indoor_bars) == 1
        assert len(outdoor_bars) == 1
        assert outdoor_bars[0].start_date == indoor_bars[0].end_date + timedelta(days=1)
        assert outdoor_bars[0].end_date == date(2026, 7, 31)

    def test_outdoor_period_fully_covered_by_indoor_is_skipped(self, engine, frost_config):
        sp = _make_species(
            sowing_indoor_weeks_before_last_frost=10,
            direct_sow_months=[3, 4, 7, 8],
            harvest_months=[9, 10],
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        outdoor_bars = [b for b in bars if b.phase == "outdoor_planting"]
        assert len(outdoor_bars) == 1
        assert outdoor_bars[0].start_date == date(2026, 7, 1)

    def test_bloom_pause_separate_bars(self, engine, frost_config):
        sp = _make_species(
            allows_harvest=False,
            bloom_months=[3, 4, 5, 6, 9, 10],
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        flowering_bars = [b for b in bars if b.phase == "flowering"]
        assert len(flowering_bars) == 2
        assert flowering_bars[0].end_date == date(2026, 6, 30)
        assert flowering_bars[1].start_date == date(2026, 9, 1)

    def test_wrap_around_harvest_single_bar(self, engine, frost_config):
        """Wrap-around harvest months clipped at year end."""
        sp = _make_species(
            direct_sow_months=[5, 6],
            harvest_months=[10, 11, 12, 1, 2],
        )
        bars = engine.calculate_bars(sp, frost_config, 2026)
        harvest_bars = [b for b in bars if b.phase == "harvest"]
        assert len(harvest_bars) == 1
        assert harvest_bars[0].start_date == date(2026, 10, 1)
        assert harvest_bars[0].end_date == date(2026, 12, 31)


class TestBuildCalendar:
    def test_sorts_by_earliest_bar(self, engine, frost_config):
        sp_late = _make_species(
            key="late",
            scientific_name="Beta vulgaris",
            common_names=["Rote Bete"],
            harvest_months=[9, 10],
        )
        sp_early = _make_species(
            key="early",
            scientific_name="Lactuca sativa",
            common_names=["Salat"],
            direct_sow_months=[3, 4],
        )
        entries = engine.build_calendar([sp_late, sp_early], frost_config, 2026)
        assert len(entries) == 2
        assert entries[0].species_key == "early"
        assert entries[1].species_key == "late"

    def test_skips_species_without_bars(self, engine, frost_config):
        sp_empty = _make_species(key="empty", scientific_name="Genus species")
        sp_with = _make_species(key="with", scientific_name="Genus species2", harvest_months=[7])
        entries = engine.build_calendar([sp_empty, sp_with], frost_config, 2026)
        assert len(entries) == 1
        assert entries[0].species_key == "with"

    def test_explicit_periods_separate_rows(self, engine, frost_config):
        """Species with explicit growing_periods produce one row per period."""
        sp = _make_species(
            key="wheat",
            scientific_name="Triticum aestivum",
            common_names=["Weizen"],
            growing_periods=[
                GrowingPeriodData(label="Sommerweizen", direct_sow_months=[3, 4], harvest_months=[7, 8]),
                GrowingPeriodData(label="Winterweizen", direct_sow_months=[10, 11], harvest_months=[6, 7]),
            ],
        )
        entries = engine.build_calendar([sp], frost_config, 2026)
        assert len(entries) == 2
        # Winterweizen sorts first (growth bar from Jan 1)
        assert entries[0].species_key == "wheat_1"
        assert entries[1].species_key == "wheat_0"
        # Both rows link back to the real species key
        assert entries[0].link_species_key == "wheat"
        assert entries[1].link_species_key == "wheat"
        assert "Winterweizen" in entries[0].common_name
        assert "Sommerweizen" in entries[1].common_name

    def test_year_crossing_period_growth_before_harvest(self, engine, frost_config):
        """Year-crossing period (sow autumn, harvest next summer) shows growth from Jan 1."""
        sp = _make_species(
            key="ww",
            scientific_name="Triticum aestivum",
            common_names=["Winterweizen"],
            growing_periods=[
                GrowingPeriodData(label="Winterweizen", direct_sow_months=[10, 11], harvest_months=[6, 7]),
            ],
        )
        entries = engine.build_calendar([sp], frost_config, 2026)
        assert len(entries) == 1
        bars = {b.phase: b for b in entries[0].bars}
        assert "growth" in bars
        assert bars["growth"].start_date == date(2026, 1, 1)
        assert bars["growth"].end_date == date(2026, 5, 31)
        assert "harvest" in bars
        assert bars["harvest"].start_date == date(2026, 6, 1)
        assert "outdoor_planting" in bars
        assert bars["outdoor_planting"].start_date == date(2026, 10, 1)

    def test_period_label_fallback_to_season(self, engine, frost_config):
        """Without explicit labels, season is derived from sowing months."""
        sp = _make_species(
            key="sp",
            scientific_name="Genus species",
            common_names=["Test"],
            growing_periods=[
                GrowingPeriodData(direct_sow_months=[3, 4], harvest_months=[7, 8]),
                GrowingPeriodData(direct_sow_months=[9, 10], harvest_months=[12, 1]),
            ],
        )
        entries = engine.build_calendar([sp], frost_config, 2026)
        assert len(entries) == 2
        assert "spring" in entries[0].common_name
        assert "autumn" in entries[1].common_name

    def test_single_period_no_suffix(self, engine, frost_config):
        """Species with one period does not get a label suffix."""
        sp = _make_species(
            key="tomato",
            scientific_name="Solanum lycopersicum",
            common_names=["Tomate"],
            harvest_months=[7, 8, 9],
        )
        entries = engine.build_calendar([sp], frost_config, 2026)
        assert len(entries) == 1
        assert entries[0].common_name == "Tomate"
        assert entries[0].species_key == "tomato"
        assert entries[0].link_species_key == "tomato"

    def test_porree_explicit_periods(self, engine, frost_config):
        """Porree: two explicit periods with independent harvest."""
        sp = _make_species(
            key="leek",
            scientific_name="Allium porrum",
            common_names=["Porree"],
            growing_periods=[
                GrowingPeriodData(
                    label="Sommerporree",
                    direct_sow_months=[2, 3],
                    harvest_months=[8, 9, 10, 11],
                ),
                GrowingPeriodData(
                    label="Winterporree",
                    direct_sow_months=[5, 6],
                    harvest_months=[12, 1, 2, 3],
                ),
            ],
        )
        entries = engine.build_calendar([sp], frost_config, 2026)
        assert len(entries) == 2

        # Sommerporree
        summer = entries[0]
        assert "Sommerporree" in summer.common_name
        harvest_bars = [b for b in summer.bars if b.phase == "harvest"]
        assert len(harvest_bars) == 1
        assert harvest_bars[0].start_date == date(2026, 8, 1)
        assert harvest_bars[0].end_date == date(2026, 11, 30)

        # Winterporree — harvest wraps year, clipped at Dec 31
        winter = entries[1]
        assert "Winterporree" in winter.common_name
        harvest_bars = [b for b in winter.bars if b.phase == "harvest"]
        assert len(harvest_bars) == 1
        assert harvest_bars[0].start_date == date(2026, 12, 1)
        assert harvest_bars[0].end_date == date(2026, 12, 31)

    def test_period_with_indoor_sowing(self, engine, frost_config):
        """Each period can independently have indoor sowing."""
        sp = _make_species(
            key="sp",
            scientific_name="Genus species",
            common_names=["Test"],
            growing_periods=[
                GrowingPeriodData(
                    label="Frühjahr",
                    sowing_indoor_weeks_before_last_frost=8,
                    harvest_months=[7, 8],
                ),
                GrowingPeriodData(
                    label="Herbst",
                    direct_sow_months=[8, 9],
                    harvest_months=[11, 12],
                ),
            ],
        )
        entries = engine.build_calendar([sp], frost_config, 2026)
        assert len(entries) == 2

        spring_indoor = [b for b in entries[0].bars if b.phase == "indoor_sowing"]
        assert len(spring_indoor) == 1

        autumn_indoor = [b for b in entries[1].bars if b.phase == "indoor_sowing"]
        assert len(autumn_indoor) == 0

    def test_defaults_frost_config(self, engine):
        frost_config = FrostConfig()
        sp = _make_species(sowing_indoor_weeks_before_last_frost=8)
        entries = engine.build_calendar([sp], frost_config, 2026)
        assert len(entries) == 1

    def test_from_year_on_harvest_bar(self, engine, frost_config):
        """Harvest bars carry from_year when set on the period."""
        sp = _make_species(
            growing_periods=[
                GrowingPeriodData(
                    direct_sow_months=[3, 4, 5],
                    harvest_months=[7, 8, 9],
                    harvest_from_year=2,
                )
            ],
        )
        entries = engine.build_calendar([sp], frost_config, 2026)
        harvest_bars = [b for b in entries[0].bars if b.phase == "harvest"]
        assert len(harvest_bars) == 1
        assert harvest_bars[0].from_year == 2

    def test_from_year_on_bloom_bar_ornamental(self, engine, frost_config):
        """Bloom bars for ornamentals carry from_year."""
        sp = _make_species(
            allows_harvest=False,
            growing_periods=[
                GrowingPeriodData(
                    direct_sow_months=[3, 4],
                    bloom_months=[6, 7],
                    bloom_from_year=2,
                )
            ],
        )
        entries = engine.build_calendar([sp], frost_config, 2026)
        bloom_bars = [b for b in entries[0].bars if b.phase == "flowering"]
        assert len(bloom_bars) == 1
        assert bloom_bars[0].from_year == 2

    def test_from_year_none_by_default(self, engine, frost_config):
        """Bars have from_year=None when not set."""
        sp = _make_species(
            growing_periods=[
                GrowingPeriodData(
                    direct_sow_months=[3, 4],
                    harvest_months=[7, 8],
                )
            ],
        )
        entries = engine.build_calendar([sp], frost_config, 2026)
        for b in entries[0].bars:
            assert b.from_year is None

    def test_from_year_legacy_flat_fields(self, engine, frost_config):
        """Legacy flat bloom_from_year is passed through auto-created period."""
        sp = _make_species(
            direct_sow_months=[3, 4, 5],
            bloom_months=[5, 6, 7],
            bloom_from_year=2,
            allows_harvest=False,
        )
        entries = engine.build_calendar([sp], frost_config, 2026)
        bloom_bars = [b for b in entries[0].bars if b.phase == "flowering"]
        assert len(bloom_bars) >= 1
        assert bloom_bars[0].from_year == 2
