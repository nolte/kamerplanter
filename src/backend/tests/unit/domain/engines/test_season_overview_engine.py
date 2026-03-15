"""Tests for SeasonOverviewEngine."""

from datetime import date
from unittest.mock import patch

import pytest

from app.domain.engines.season_overview_engine import (
    SeasonOverviewEngine,
    TaskEvent,
)
from app.domain.engines.sowing_calendar_engine import (
    SowingBar,
    SowingCalendarEntry,
)


@pytest.fixture
def engine():
    return SeasonOverviewEngine()


def _make_entry(species_key: str, bars: list[SowingBar]) -> SowingCalendarEntry:
    return SowingCalendarEntry(
        species_key=species_key,
        species_name=f"Species {species_key}",
        bars=bars,
    )


class TestBuildOverview:
    def test_produces_12_months(self, engine):
        overview = engine.build_overview([], [], "site1", "Garden", 2026)
        assert len(overview.months) == 12
        assert overview.months[0].month == 1
        assert overview.months[11].month == 12

    def test_counts_sowing_entries(self, engine):
        entry = _make_entry(
            "sp1",
            [
                SowingBar(
                    phase="outdoor_planting",
                    color="#66BB6A",
                    start_date=date(2026, 3, 1),
                    end_date=date(2026, 4, 30),
                ),
            ],
        )
        overview = engine.build_overview([entry], [], "s1", "G", 2026)
        assert overview.months[2].sowing_count == 1  # March
        assert overview.months[3].sowing_count == 1  # April
        assert overview.months[4].sowing_count == 0  # May

    def test_counts_harvest_entries(self, engine):
        entry = _make_entry(
            "sp1",
            [
                SowingBar(phase="harvest", color="#FFA726", start_date=date(2026, 7, 1), end_date=date(2026, 9, 30)),
            ],
        )
        overview = engine.build_overview([entry], [], "s1", "G", 2026)
        assert overview.months[6].harvest_count == 1  # July
        assert overview.months[7].harvest_count == 1  # August
        assert overview.months[8].harvest_count == 1  # September
        assert overview.months[9].harvest_count == 0  # October

    def test_task_counts_and_top3(self, engine):
        tasks = [
            TaskEvent(month=5, title="Mulchen", priority=3),
            TaskEvent(month=5, title="Gießen", priority=1),
            TaskEvent(month=5, title="Düngen", priority=5),
            TaskEvent(month=5, title="Jäten", priority=2),
        ]
        overview = engine.build_overview([], tasks, "s1", "G", 2026)
        may = overview.months[4]
        assert may.task_count == 4
        assert may.top_tasks == ["Düngen", "Mulchen", "Jäten"]

    @patch("app.domain.engines.season_overview_engine.date")
    def test_is_current_month(self, mock_date, engine):
        mock_date.today.return_value = date(2026, 3, 15)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        overview = engine.build_overview([], [], "s1", "G", 2026)
        assert overview.months[2].is_current is True  # March
        assert overview.months[0].is_current is False

    def test_site_info_propagated(self, engine):
        overview = engine.build_overview([], [], "site42", "Mein Garten", 2026)
        assert overview.site_key == "site42"
        assert overview.site_name == "Mein Garten"
        assert overview.year == 2026

    def test_counts_bloom_entries_separately(self, engine):
        entry = _make_entry(
            "sp1",
            [
                SowingBar(phase="flowering", color="#EC407A", start_date=date(2026, 3, 1), end_date=date(2026, 5, 31)),
            ],
        )
        overview = engine.build_overview([entry], [], "s1", "G", 2026)
        # Bloom should NOT count as harvest
        assert overview.months[2].harvest_count == 0  # March
        assert overview.months[2].bloom_count == 1  # March
        assert overview.months[3].bloom_count == 1  # April
        assert overview.months[4].bloom_count == 1  # May
        assert overview.months[5].bloom_count == 0  # June

    def test_empty_inputs(self, engine):
        overview = engine.build_overview([], [], "", "", 2026)
        assert len(overview.months) == 12
        assert all(m.sowing_count == 0 for m in overview.months)
        assert all(m.harvest_count == 0 for m in overview.months)
        assert all(m.bloom_count == 0 for m in overview.months)

    def test_counts_lifecycle_germination_as_sowing(self, engine):
        entry = _make_entry(
            "run1",
            [
                SowingBar(
                    phase="germination", color="#FDD835", start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)
                ),
            ],
        )
        overview = engine.build_overview([entry], [], "s1", "G", 2026)
        assert overview.months[1].sowing_count == 1  # Feb
        assert overview.months[1].harvest_count == 0

    def test_counts_lifecycle_seedling_as_sowing(self, engine):
        entry = _make_entry(
            "run1",
            [
                SowingBar(phase="seedling", color="#66BB6A", start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)),
            ],
        )
        overview = engine.build_overview([entry], [], "s1", "G", 2026)
        assert overview.months[2].sowing_count == 1  # March

    def test_lifecycle_vegetative_not_counted(self, engine):
        entry = _make_entry(
            "run1",
            [
                SowingBar(phase="vegetative", color="#42A5F5", start_date=date(2026, 4, 1), end_date=date(2026, 6, 30)),
            ],
        )
        overview = engine.build_overview([entry], [], "s1", "G", 2026)
        assert overview.months[3].sowing_count == 0  # April
        assert overview.months[3].harvest_count == 0
        assert overview.months[3].bloom_count == 0

    def test_full_lifecycle_run(self, engine):
        """A complete PlantingRun lifecycle should count correctly."""
        entry = _make_entry(
            "run1",
            [
                SowingBar(
                    phase="germination", color="#FDD835", start_date=date(2026, 2, 1), end_date=date(2026, 2, 14)
                ),
                SowingBar(phase="seedling", color="#66BB6A", start_date=date(2026, 2, 15), end_date=date(2026, 3, 15)),
                SowingBar(
                    phase="vegetative", color="#42A5F5", start_date=date(2026, 3, 16), end_date=date(2026, 5, 31)
                ),
                SowingBar(phase="flowering", color="#EC407A", start_date=date(2026, 6, 1), end_date=date(2026, 7, 31)),
                SowingBar(phase="harvest", color="#FFA726", start_date=date(2026, 8, 1), end_date=date(2026, 9, 30)),
            ],
        )
        overview = engine.build_overview([entry], [], "s1", "G", 2026)
        # Feb: germination + seedling
        assert overview.months[1].sowing_count == 2
        # March: seedling + vegetative (seedling counts, vegetative doesn't)
        assert overview.months[2].sowing_count == 1
        # June: flowering
        assert overview.months[5].bloom_count == 1
        assert overview.months[5].harvest_count == 0
        # August: harvest
        assert overview.months[7].harvest_count == 1
        assert overview.months[7].bloom_count == 0
