"""Sowing calendar engine — calculates time bars for species sowing/harvest/bloom phases."""

from __future__ import annotations

from datetime import date, timedelta

from pydantic import BaseModel, model_validator

from app.common.enums import FrostTolerance, PlantTrait

# ── Default frost dates (Central Europe) ──────────────────────────────

DEFAULT_LAST_FROST = date(2026, 5, 15)
DEFAULT_EISHEILIGE = date(2026, 5, 15)


# ── Pydantic models ──────────────────────────────────────────────────


class FrostConfig(BaseModel):
    last_frost_date: date = DEFAULT_LAST_FROST
    first_frost_date: date | None = None
    eisheilige_date: date = DEFAULT_EISHEILIGE


class SowingBar(BaseModel):
    phase: str  # indoor_sowing | outdoor_planting | growth | harvest | flowering
    color: str
    start_date: date
    end_date: date
    label: str = ""
    from_year: int | None = None


class SowingCalendarEntry(BaseModel):
    species_key: str
    species_name: str
    common_name: str = ""
    link_species_key: str = ""
    plant_category: str | None = None
    bars: list[SowingBar] = []


# ── Growing period — one self-contained sowing-to-harvest timeline ───


class GrowingPeriodData(BaseModel):
    label: str = ""
    sowing_indoor_weeks_before_last_frost: int | None = None
    sowing_outdoor_after_last_frost_days: int | None = None
    direct_sow_months: list[int] = []
    growth_months: list[int] = []
    harvest_months: list[int] = []
    bloom_months: list[int] = []
    harvest_from_year: int | None = None
    bloom_from_year: int | None = None


# ── Species data passed into the engine ───────────────────────────────


class SpeciesData(BaseModel):
    key: str
    scientific_name: str
    common_names: list[str] = []
    traits: list[PlantTrait] = []
    allows_harvest: bool = True
    frost_sensitivity: FrostTolerance | None = None
    plant_category: str | None = None
    # ── Explicit growing periods (preferred) ──
    growing_periods: list[GrowingPeriodData] = []
    # ── Legacy flat fields — auto-converted to single period ──
    sowing_indoor_weeks_before_last_frost: int | None = None
    sowing_outdoor_after_last_frost_days: int | None = None
    direct_sow_months: list[int] = []
    harvest_months: list[int] = []
    bloom_months: list[int] = []
    harvest_from_year: int | None = None
    bloom_from_year: int | None = None

    @model_validator(mode="after")
    def auto_create_periods(self) -> SpeciesData:
        """If no explicit growing_periods, create one from legacy flat fields."""
        if self.growing_periods:
            return self
        has_data = (
            self.sowing_indoor_weeks_before_last_frost is not None
            or self.sowing_outdoor_after_last_frost_days is not None
            or self.direct_sow_months
            or self.harvest_months
            or self.bloom_months
        )
        if has_data:
            self.growing_periods = [
                GrowingPeriodData(
                    sowing_indoor_weeks_before_last_frost=self.sowing_indoor_weeks_before_last_frost,
                    sowing_outdoor_after_last_frost_days=self.sowing_outdoor_after_last_frost_days,
                    direct_sow_months=self.direct_sow_months,
                    harvest_months=self.harvest_months,
                    bloom_months=self.bloom_months,
                    harvest_from_year=self.harvest_from_year,
                    bloom_from_year=self.bloom_from_year,
                )
            ]
        return self


# ── Engine ────────────────────────────────────────────────────────────


PHASE_COLORS: dict[str, str] = {
    "indoor_sowing": "#FDD835",
    "outdoor_planting": "#66BB6A",
    "growth": "#42A5F5",
    "harvest": "#FFA726",
    "flowering": "#EC407A",
}

# Lifecycle phase colors — used when displaying PlantingRun timelines
LIFECYCLE_PHASE_COLORS: dict[str, str] = {
    "germination": "#FDD835",
    "seedling": "#66BB6A",
    "vegetative": "#42A5F5",
    "flowering": "#EC407A",
    "harvest": "#FFA726",
    "flushing": "#AB47BC",
    "ripening": "#FFA726",
}


class SowingCalendarEngine:
    """Builds sowing calendar entries for a list of species."""

    def calculate_bars(
        self,
        sp: SpeciesData,
        frost_config: FrostConfig,
        year: int,
    ) -> list[SowingBar]:
        """Calculate bars for the first growing period (backward compat)."""
        if not sp.growing_periods:
            return []
        return self._calculate_period_bars(
            sp.growing_periods[0],
            frost_config,
            year,
            is_ornamental=PlantTrait.ORNAMENTAL in sp.traits or not sp.allows_harvest,
            frost_sensitivity=sp.frost_sensitivity,
        )

    def _calculate_period_bars(
        self,
        period: GrowingPeriodData,
        frost_config: FrostConfig,
        year: int,
        *,
        is_ornamental: bool = False,
        frost_sensitivity: FrostTolerance | None = None,
    ) -> list[SowingBar]:
        bars: list[SowingBar] = []
        last_frost = frost_config.last_frost_date.replace(year=year)
        eisheilige = frost_config.eisheilige_date.replace(year=year)

        # 1. Indoor sowing (Voranzucht)
        if period.sowing_indoor_weeks_before_last_frost is not None:
            indoor_start = last_frost - timedelta(weeks=period.sowing_indoor_weeks_before_last_frost)
            indoor_end = last_frost - timedelta(days=1)
            if indoor_start.year == year or indoor_end.year == year:
                bars.append(
                    SowingBar(
                        phase="indoor_sowing",
                        color=PHASE_COLORS["indoor_sowing"],
                        start_date=max(indoor_start, date(year, 1, 1)),
                        end_date=indoor_end,
                        label="indoor_sowing",
                    )
                )

        # 2. Outdoor planting — direct_sow_months preferred, fallback to days-after-frost.
        #    When indoor sowing exists, clip outdoor start to after indoor end (§5.1).
        indoor_end_date = bars[-1].end_date if bars and bars[-1].phase == "indoor_sowing" else None
        if period.direct_sow_months:
            for period_start, period_end in _split_into_periods(period.direct_sow_months):
                ds, de = _period_dates(year, period_start, period_end)
                if indoor_end_date and ds <= indoor_end_date:
                    ds = indoor_end_date + timedelta(days=1)
                if ds > de:
                    continue
                bars.append(
                    SowingBar(
                        phase="outdoor_planting",
                        color=PHASE_COLORS["outdoor_planting"],
                        start_date=ds,
                        end_date=de,
                        label="direct_sow",
                    )
                )
        elif period.sowing_outdoor_after_last_frost_days is not None:
            outdoor_start = last_frost + timedelta(days=period.sowing_outdoor_after_last_frost_days)
            if frost_sensitivity == FrostTolerance.SENSITIVE:
                outdoor_start = max(outdoor_start, eisheilige + timedelta(days=1))
            outdoor_planting_end = outdoor_start + timedelta(days=13)
            bars.append(
                SowingBar(
                    phase="outdoor_planting",
                    color=PHASE_COLORS["outdoor_planting"],
                    start_date=outdoor_start,
                    end_date=outdoor_planting_end,
                    label="outdoor_planting",
                )
            )

        # 3. Harvest or Flowering months
        #    Clip terminal bars: harvest/bloom cannot start before planting/indoor ends (§5.3).
        #    Exception: year-crossing periods where harvest is before planting.
        sowing_bars = [b for b in bars if b.phase in ("indoor_sowing", "outdoor_planting")]
        latest_sowing_end = max(b.end_date for b in sowing_bars) if sowing_bars else None

        terminal_months = period.bloom_months if (is_ornamental and period.bloom_months) else period.harvest_months
        terminal_phase = "flowering" if (is_ornamental and period.bloom_months) else "harvest"
        terminal_from_year = (
            period.bloom_from_year if (is_ornamental and period.bloom_months) else period.harvest_from_year
        )

        if terminal_months:
            for period_start, period_end in _split_into_periods(terminal_months):
                ds, de = _period_dates(year, period_start, period_end)
                # Clip: terminal bar must not start before sowing ends,
                # unless it's a year-crossing period (terminal entirely before sowing).
                if latest_sowing_end and ds <= latest_sowing_end:
                    if de <= latest_sowing_end:
                        # Year-crossing: terminal is entirely before sowing — keep as-is
                        pass
                    else:
                        ds = latest_sowing_end + timedelta(days=1)
                if ds > de:
                    continue
                bars.append(
                    SowingBar(
                        phase=terminal_phase,
                        color=PHASE_COLORS[terminal_phase],
                        start_date=ds,
                        end_date=de,
                        label=terminal_phase,
                        from_year=terminal_from_year,
                    )
                )

        # 4. Growth bars — explicit growth_months preferred, otherwise gap-fill (§5.2)
        if period.growth_months:
            # 4-explicit: user-defined growth months
            for period_start, period_end in _split_into_periods(period.growth_months):
                ds, de = _period_dates(year, period_start, period_end)
                bars.append(
                    SowingBar(
                        phase="growth",
                        color=PHASE_COLORS["growth"],
                        start_date=ds,
                        end_date=de,
                        label="growth",
                    )
                )
        else:
            # 4-auto: per-sow-bar gap-fill with date precision.
            # For each sowing bar, find the nearest future terminal or sowing
            # bar and fill the gap with growth.  For year-crossing scenarios
            # (e.g. sow Oct → harvest Jun), also fill from Jan 1 to the
            # earliest "prior" terminal.
            indoor_bars = [b for b in bars if b.phase == "indoor_sowing"]
            planting_bars = [b for b in bars if b.phase == "outdoor_planting"]
            terminal_bars = [b for b in bars if b.phase in ("harvest", "flowering")]

            # 4a. Gap between indoor sowing end and outdoor planting start
            if indoor_bars and planting_bars:
                indoor_end = max(b.end_date for b in indoor_bars)
                outdoor_start = min(b.start_date for b in planting_bars)
                if outdoor_start > indoor_end + timedelta(days=1):
                    bars.append(
                        SowingBar(
                            phase="growth",
                            color=PHASE_COLORS["growth"],
                            start_date=indoor_end + timedelta(days=1),
                            end_date=outdoor_start - timedelta(days=1),
                            label="growth",
                        )
                    )

            # 4b. Per sowing bar: fill gap to nearest future terminal
            source_bars = planting_bars or indoor_bars
            if source_bars and terminal_bars:
                for sb in source_bars:
                    future_terminals = [b for b in terminal_bars if b.start_date > sb.end_date]
                    if future_terminals:
                        nearest = min(future_terminals, key=lambda b: b.start_date)
                        # Don't fill past another sowing bar
                        other_sow_before = [
                            s
                            for s in source_bars
                            if s is not sb and s.start_date > sb.end_date and s.start_date < nearest.start_date
                        ]
                        end_limit = (
                            min(s.start_date for s in other_sow_before) - timedelta(days=1)
                            if other_sow_before
                            else nearest.start_date - timedelta(days=1)
                        )
                        growth_start = sb.end_date + timedelta(days=1)
                        if growth_start <= end_limit:
                            bars.append(
                                SowingBar(
                                    phase="growth",
                                    color=PHASE_COLORS["growth"],
                                    start_date=growth_start,
                                    end_date=end_limit,
                                    label="growth",
                                )
                            )
                    else:
                        # No future terminal — year-crossing scenario.
                        # Fill growth from sow end to Dec 31.
                        growth_start = sb.end_date + timedelta(days=1)
                        year_end = date(year, 12, 31)
                        if growth_start <= year_end:
                            bars.append(
                                SowingBar(
                                    phase="growth",
                                    color=PHASE_COLORS["growth"],
                                    start_date=growth_start,
                                    end_date=year_end,
                                    label="growth",
                                )
                            )

            # 4c. Year-crossing: fill Jan 1 to earliest terminal that is
            #     before all sowing bars (i.e. the "wrapped" terminal).
            if source_bars and terminal_bars:
                earliest_source = min(b.start_date for b in source_bars)
                prior_terminals = [b for b in terminal_bars if b.end_date < earliest_source]
                if prior_terminals:
                    earliest_terminal = min(b.start_date for b in prior_terminals)
                    if earliest_terminal > date(year, 1, 1):
                        bars.append(
                            SowingBar(
                                phase="growth",
                                color=PHASE_COLORS["growth"],
                                start_date=date(year, 1, 1),
                                end_date=earliest_terminal - timedelta(days=1),
                                label="growth",
                            )
                        )

            # 4-fallback: No sowing bars but terminal bars exist (indoor ornamentals).
            # Fill all non-terminal months with growth.
            if not sowing_bars and terminal_bars:
                terminal_months_set: set[int] = set()
                for tb in terminal_bars:
                    sm = tb.start_date.month
                    em = tb.end_date.month
                    if sm <= em:
                        terminal_months_set.update(range(sm, em + 1))
                    else:
                        terminal_months_set.update(range(sm, 13))
                        terminal_months_set.update(range(1, em + 1))
                growth_months_list = sorted(m for m in range(1, 13) if m not in terminal_months_set)
                if growth_months_list:
                    for ps, pe in _split_into_periods(growth_months_list):
                        ds, de = _period_dates(year, ps, pe)
                        bars.append(
                            SowingBar(
                                phase="growth",
                                color=PHASE_COLORS["growth"],
                                start_date=ds,
                                end_date=de,
                                label="growth",
                            )
                        )

        return bars

    def build_calendar(
        self,
        species_list: list[SpeciesData],
        frost_config: FrostConfig,
        year: int,
    ) -> list[SowingCalendarEntry]:
        entries: list[SowingCalendarEntry] = []
        for sp in species_list:
            if not sp.growing_periods:
                continue
            common = sp.common_names[0] if sp.common_names else ""
            is_ornamental = PlantTrait.ORNAMENTAL in sp.traits or not sp.allows_harvest

            for i, period in enumerate(sp.growing_periods):
                bars = self._calculate_period_bars(
                    period,
                    frost_config,
                    year,
                    is_ornamental=is_ornamental,
                    frost_sensitivity=sp.frost_sensitivity,
                )
                if not bars:
                    continue

                if len(sp.growing_periods) > 1:
                    suffix = period.label or _season_label(period)
                    label = f"{common} ({suffix})" if common else f"{sp.scientific_name} ({suffix})"
                    species_key = f"{sp.key}_{i}"
                else:
                    label = common
                    species_key = sp.key

                entries.append(
                    SowingCalendarEntry(
                        species_key=species_key,
                        species_name=sp.scientific_name,
                        common_name=label,
                        link_species_key=sp.key,
                        plant_category=sp.plant_category,
                        bars=bars,
                    )
                )

        entries.sort(key=lambda e: min(b.start_date for b in e.bars) if e.bars else date.max)
        return entries


# ── Helpers ──────────────────────────────────────────────────────────


def _month_end(year: int, month: int) -> date:
    """Last day of the given month."""
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _period_dates(year: int, period_start: int, period_end: int) -> tuple[date, date]:
    """Convert a period tuple to (start_date, end_date).

    Wrap-around periods (start > end, e.g. (8, 3)) are clipped at year end.
    """
    ds = date(year, period_start, 1)
    de = _month_end(year, period_end) if period_end >= period_start else date(year, 12, 31)
    return ds, de


def _season_label(period: GrowingPeriodData) -> str:
    """Derive a season label from a period's earliest sowing month."""
    if period.direct_sow_months:
        start_month = min(period.direct_sow_months)
    elif period.sowing_indoor_weeks_before_last_frost is not None:
        return "spring"
    else:
        return ""
    if start_month <= 4:
        return "spring"
    if start_month <= 8:
        return "summer"
    return "autumn"


def _split_into_periods(months: list[int]) -> list[tuple[int, int]]:
    """Split a list of months into contiguous period tuples.

    Detects circular wrap-around: [8, 9, 10, 11, 12, 1, 2, 3] -> [(8, 3)]
    where start > end indicates the period crosses the year boundary.

    Non-wrapping: [3, 4, 5, 6, 9, 10] -> [(3, 6), (9, 10)]
    """
    if not months:
        return []
    sorted_months = sorted(set(months))
    periods: list[tuple[int, int]] = []
    start = sorted_months[0]
    prev = sorted_months[0]
    for m in sorted_months[1:]:
        if m == prev + 1:
            prev = m
        else:
            periods.append((start, prev))
            start = m
            prev = m
    periods.append((start, prev))

    # Detect circular wrap-around: first group includes month 1,
    # last group includes month 12 -> merge into one wrap-around period.
    if len(periods) >= 2 and periods[0][0] == 1 and periods[-1][1] == 12:
        wrap_period = (periods[-1][0], periods[0][1])
        periods = [wrap_period] + periods[1:-1]

    return periods
