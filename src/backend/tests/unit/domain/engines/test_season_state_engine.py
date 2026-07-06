"""REQ-047 §3.3 — unit tests for the SeasonStateEngine (pure state logic).

Covers every directed transition (live / climatological / calendar tiers), the
hysteresis threshold, the oscillation / no-backward-within-season_year guard and
the season_year bookkeeping.
"""

from datetime import date

from app.common.enums import SeasonPhase, SeasonTriggerTier
from app.domain.engines.season_state_engine import SeasonStateEngine
from app.domain.models.season_state import SeasonState
from app.domain.services.season_signal_resolver import SeasonSignal

# Fixed thresholds so the tests do not depend on env overrides.
ENGINE = SeasonStateEngine(
    pre_winter_temp_c=5.0,
    frost_temp_c=2.0,
    spring_temp_c=10.0,
    signal_threshold_days=3,
)


def _state(phase: SeasonPhase = SeasonPhase.GROWING, **overrides) -> SeasonState:
    data = {"site_key": "s1", "tenant_key": "t1", "phase": phase}
    data.update(overrides)
    return SeasonState(**data)


def _live(
    min_temp_c: float, *, hemisphere: str = "north", frost_date: date | None = None, last_md: str | None = None
) -> SeasonSignal:
    return SeasonSignal(
        tier=SeasonTriggerTier.LIVE,
        min_temp_c=min_temp_c,
        forecast_first_frost_date=frost_date,
        estimated_first_frost_md=None,
        estimated_last_frost_md=last_md,
        reason_i18n_key="pages.season.trigger.liveTemp",
        hemisphere=hemisphere,
    )


def _clim(first_md: str | None, last_md: str | None, *, hemisphere: str = "north") -> SeasonSignal:
    return SeasonSignal(
        tier=SeasonTriggerTier.CLIMATOLOGICAL,
        min_temp_c=None,
        forecast_first_frost_date=None,
        estimated_first_frost_md=first_md,
        estimated_last_frost_md=last_md,
        reason_i18n_key="pages.season.trigger.climateEstimate",
        hemisphere=hemisphere,
    )


def _calendar(*, hemisphere: str = "north") -> SeasonSignal:
    return SeasonSignal(
        tier=SeasonTriggerTier.CALENDAR,
        min_temp_c=None,
        forecast_first_frost_date=None,
        estimated_first_frost_md=None,
        estimated_last_frost_md=None,
        reason_i18n_key="pages.season.trigger.calendar",
        hemisphere=hemisphere,
    )


def _apply(state: SeasonState, signal: SeasonSignal, on_date: date):
    """Run one engine evaluation and fold the result back into the state."""
    transition = ENGINE.next_phase(state, signal, on_date)
    state.consecutive_signal_days = transition.consecutive_signal_days
    state.season_year = transition.season_year
    if transition.changed:
        state.phase = transition.to_phase
    return transition


class TestLiveHysteresis:
    def test_growing_to_pre_winter_needs_three_consecutive_cold_days(self) -> None:
        state = _state()
        signal = _live(4.0)  # <= pre_winter_temp_c
        on = date(2026, 10, 1)

        t1 = _apply(state, signal, on)
        assert not t1.changed and state.consecutive_signal_days == 1
        t2 = _apply(state, signal, date(2026, 10, 2))
        assert not t2.changed and state.consecutive_signal_days == 2
        t3 = _apply(state, signal, date(2026, 10, 3))
        assert t3.changed
        assert state.phase == SeasonPhase.PRE_WINTER
        assert state.consecutive_signal_days == 0

    def test_single_warm_day_resets_the_counter(self) -> None:
        state = _state(consecutive_signal_days=2)
        # A warm day does not satisfy the growing→pre_winter cold condition.
        t = _apply(state, _live(15.0), date(2026, 10, 5))
        assert not t.changed
        assert state.phase == SeasonPhase.GROWING
        assert state.consecutive_signal_days == 0

    def test_frost_forecast_triggers_pre_winter_regardless_of_month(self) -> None:
        state = _state(consecutive_signal_days=2)
        # Even a mild min temp advances when frost is forecast within 7 days.
        signal = _live(8.0, frost_date=date(2026, 9, 20))
        t = _apply(state, signal, date(2026, 9, 15))
        assert t.changed and state.phase == SeasonPhase.PRE_WINTER

    def test_pre_winter_to_dormancy_on_frost(self) -> None:
        state = _state(SeasonPhase.PRE_WINTER, season_year=2026)
        signal = _live(1.0)  # <= frost_temp_c
        for day in (10, 11, 12):
            _apply(state, signal, date(2026, 11, day))
        assert state.phase == SeasonPhase.WINTER_DORMANCY


class TestNoBackwardTransition:
    def test_warm_december_day_does_not_leave_dormancy(self) -> None:
        state = _state(SeasonPhase.WINTER_DORMANCY, season_year=2026)
        # A warm day in December: spring guard "after coldest month" is False.
        for day in (10, 11, 12):
            t = _apply(state, _live(15.0), date(2026, 12, day))
            assert not t.changed
        assert state.phase == SeasonPhase.WINTER_DORMANCY

    def test_dormancy_to_pre_spring_only_after_coldest_month(self) -> None:
        state = _state(SeasonPhase.WINTER_DORMANCY, season_year=2026)
        signal = _live(12.0, last_md="04-20")  # warm, after coldest month (March)
        for day in (10, 11, 12):
            _apply(state, signal, date(2027, 3, day))
        assert state.phase == SeasonPhase.PRE_SPRING


class TestSpringColdSnapGuard:
    """K2 — the live growing→pre_winter entry is bound to the autumn window, so a
    spring cold snap right after ``→ growing`` cannot re-trigger dormancy."""

    def test_cold_spring_nights_do_not_reenter_winter(self) -> None:
        state = _state(SeasonPhase.GROWING, season_year=None)
        signal = _live(3.0)  # <= pre_winter_temp_c, but it is spring
        for day in (10, 11, 12, 13, 14):
            t = _apply(state, signal, date(2027, 4, day))  # April = spring, not autumn
            assert not t.changed
        assert state.phase == SeasonPhase.GROWING

    def test_cool_may_nights_do_not_reenter_winter(self) -> None:
        state = _state(SeasonPhase.GROWING, season_year=None)
        signal = _live(4.0)
        for day in (1, 2, 3, 4):
            t = _apply(state, signal, date(2027, 5, day))
            assert not t.changed
        assert state.phase == SeasonPhase.GROWING

    def test_autumn_cold_still_enters_winter(self) -> None:
        # The guard must not block the legitimate autumn entry.
        state = _state(SeasonPhase.GROWING, season_year=None)
        signal = _live(3.0)
        for day in (1, 2, 3):
            _apply(state, signal, date(2026, 9, day))  # September = autumn window
        assert state.phase == SeasonPhase.PRE_WINTER


class TestLateSpringRelease:
    """K3 — the pre_spring→growing release has no tight 45-day cap, so a cold year
    whose dormancy→pre_spring transition fires late still reaches growing."""

    def test_release_after_last_frost_even_in_june(self) -> None:
        state = _state(SeasonPhase.PRE_SPRING, season_year=2026)
        # Warm, no imminent frost, last frost was 20 April → June is > 45 days later.
        signal = _live(12.0, last_md="04-20")
        for day in (10, 11, 12):
            _apply(state, signal, date(2027, 6, day))
        assert state.phase == SeasonPhase.GROWING

    def test_climatological_release_after_last_frost_even_late(self) -> None:
        state = _state(SeasonPhase.PRE_SPRING, season_year=2026)
        signal = _clim("10-15", "04-20")
        for day in (5, 6, 7):
            _apply(state, signal, date(2027, 6, day))
        assert state.phase == SeasonPhase.GROWING


class TestSeasonYearBookkeeping:
    def test_season_year_set_on_winter_entry_and_released_on_spring_exit(self) -> None:
        # Calendar tier advances immediately, making the full cycle easy to drive.
        state = _state()
        _apply(state, _calendar(), date(2026, 10, 15))  # growing → pre_winter
        assert state.phase == SeasonPhase.PRE_WINTER
        assert state.season_year == 2026

        _apply(state, _calendar(), date(2026, 11, 15))  # pre_winter → winter_dormancy
        assert state.phase == SeasonPhase.WINTER_DORMANCY
        assert state.season_year == 2026

        _apply(state, _calendar(), date(2027, 3, 15))  # winter_dormancy → pre_spring
        assert state.phase == SeasonPhase.PRE_SPRING
        assert state.season_year == 2026

        _apply(state, _calendar(), date(2027, 4, 15))  # pre_spring → growing
        assert state.phase == SeasonPhase.GROWING
        assert state.season_year is None


class TestCalendarTier:
    def test_calendar_is_immediate_no_hysteresis(self) -> None:
        state = _state()
        t = ENGINE.next_phase(state, _calendar(), date(2026, 10, 15))
        assert t.changed and t.to_phase == SeasonPhase.PRE_WINTER

    def test_southern_hemisphere_shifted_months(self) -> None:
        state = _state()
        # Southern winter onset is April (month 4).
        t = ENGINE.next_phase(state, _calendar(hemisphere="south"), date(2026, 4, 15))
        assert t.changed and t.to_phase == SeasonPhase.PRE_WINTER
        # October is a growing month in the south — no onset.
        t2 = ENGINE.next_phase(state, _calendar(hemisphere="south"), date(2026, 10, 15))
        assert not t2.changed


class TestClimatologicalTier:
    def test_full_cycle_from_site_frost_dates(self) -> None:
        state = _state()
        signal = _clim("10-15", "04-20")

        # growing → pre_winter within 14 days before first frost.
        for day in (2, 3, 4):
            _apply(state, signal, date(2026, 10, day))
        assert state.phase == SeasonPhase.PRE_WINTER

        # pre_winter → winter_dormancy once inside the winter window.
        for day in (1, 2, 3):
            _apply(state, signal, date(2026, 11, day))
        assert state.phase == SeasonPhase.WINTER_DORMANCY

        # winter_dormancy → pre_spring within 30 days before last frost.
        for day in (1, 2, 3):
            _apply(state, signal, date(2027, 4, day))
        assert state.phase == SeasonPhase.PRE_SPRING

        # pre_spring → growing after last frost.
        for day in (21, 22, 23):
            _apply(state, signal, date(2027, 4, day))
        assert state.phase == SeasonPhase.GROWING

    def test_no_transition_when_far_from_frost(self) -> None:
        state = _state()
        t = _apply(state, _clim("10-15", "04-20"), date(2026, 7, 1))
        assert not t.changed
        assert state.consecutive_signal_days == 0
