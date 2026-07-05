"""REQ-047 §3.3 — the season state machine (pure logic, no I/O).

:class:`SeasonStateEngine` computes the next :class:`SeasonPhase` from the current
state and the prepared :class:`SeasonSignal`. It is deterministic and does no
database/HTTP access, so the whole state logic is unit-testable in isolation.

Invariants (REQ-047 §3.3):

* Directed cycle ``growing → pre_winter → winter_dormancy → pre_spring → growing``;
  the engine only ever advances along this cycle, so a warm winter day can never
  push a plant *back* out of ``winter_dormancy`` — there simply is no backward
  edge (oscillation protection / no backward transition within a ``season_year``).
* A live/climatological transition needs ``signal_threshold_days`` consecutive
  signal days in the same direction (``consecutive_signal_days``); a single
  outlier day never flips the phase. On the calendar tier the month window decides
  immediately.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.common.enums import SeasonPhase, SeasonTriggerTier
from app.config.settings import settings
from app.domain.services.season_signal_resolver import SeasonSignal

#: Look-ahead window (days) for the live frost forecast — matches the resolver.
_LIVE_FORECAST_WINDOW_DAYS = 7

#: Directed season cycle.
_NEXT_PHASE: dict[SeasonPhase, SeasonPhase] = {
    SeasonPhase.GROWING: SeasonPhase.PRE_WINTER,
    SeasonPhase.PRE_WINTER: SeasonPhase.WINTER_DORMANCY,
    SeasonPhase.WINTER_DORMANCY: SeasonPhase.PRE_SPRING,
    SeasonPhase.PRE_SPRING: SeasonPhase.GROWING,
}

#: Calendar month windows per hemisphere for each advance condition.
#: ``pre_winter`` = single onset month, ``winter`` = dormancy months,
#: ``pre_spring`` = single reactivation month, ``growing`` = active months.
_CALENDAR_WINDOWS: dict[str, dict[str, set[int]]] = {
    "north": {
        "pre_winter": {10},
        "winter": {11, 12, 1, 2},
        "pre_spring": {3},
        "growing": {4, 5, 6, 7, 8, 9},
    },
    "south": {
        "pre_winter": {4},
        "winter": {5, 6, 7, 8},
        "pre_spring": {9},
        "growing": {10, 11, 12, 1, 2, 3},
    },
}

#: Months considered "after the coldest month" of the winter, per hemisphere —
#: guards the ``winter_dormancy → pre_spring`` transition against a warm mid-winter
#: day (REQ-047 §3.3).
_AFTER_COLDEST_MONTHS: dict[str, set[int]] = {
    "north": {2, 3, 4, 5, 6},
    "south": {8, 9, 10, 11, 12},
}


@dataclass(frozen=True)
class SeasonStateTransition:
    """Outcome of one engine evaluation."""

    changed: bool
    from_phase: SeasonPhase
    to_phase: SeasonPhase
    season_year: int | None
    consecutive_signal_days: int
    reason_i18n_key: str


def _doy(month: int, day: int) -> int:
    """Day-of-year (1..365) in a canonical non-leap year for ``MM-DD`` maths."""
    return date(2001, month, day).timetuple().tm_yday


def _parse_md(md: str | None) -> int | None:
    """Parse ``MM-DD`` into a canonical day-of-year, or ``None``."""
    if not md:
        return None
    try:
        month_str, day_str = md.split("-")
        return _doy(int(month_str), int(day_str))
    except (ValueError, IndexError) as exc:  # noqa: F841 — guards ruff-format tuple-except trap
        return None


def _gap_before(on_doy: int, target_doy: int) -> int:
    """Days from ``on_doy`` until ``target_doy`` (wrapping, 0..364)."""
    return (target_doy - on_doy) % 365


def _gap_after(on_doy: int, target_doy: int) -> int:
    """Days since ``target_doy`` up to ``on_doy`` (wrapping, 0..364)."""
    return (on_doy - target_doy) % 365


def _in_wrapped(x: int, start: int, end: int) -> bool:
    """Whether ``x`` lies in the (possibly year-wrapping) interval ``[start, end]``."""
    if start <= end:
        return start <= x <= end
    return x >= start or x <= end


class SeasonStateEngine:
    """Compute the next season phase from the current state and signal."""

    def __init__(
        self,
        *,
        pre_winter_temp_c: float | None = None,
        frost_temp_c: float | None = None,
        spring_temp_c: float | None = None,
        signal_threshold_days: int | None = None,
    ) -> None:
        self._pre_winter_temp_c = (
            pre_winter_temp_c if pre_winter_temp_c is not None else settings.season_pre_winter_temp_c
        )
        self._frost_temp_c = frost_temp_c if frost_temp_c is not None else settings.season_frost_temp_c
        self._spring_temp_c = spring_temp_c if spring_temp_c is not None else settings.season_spring_temp_c
        self._threshold_days = (
            signal_threshold_days if signal_threshold_days is not None else settings.season_signal_threshold_days
        )

    def next_phase(self, state, signal: SeasonSignal, on_date: date) -> SeasonStateTransition:  # noqa: ANN001 — SeasonState (avoid import cycle)
        """Return the transition for ``state`` given ``signal`` on ``on_date``."""
        phase: SeasonPhase = state.phase

        if signal.tier == SeasonTriggerTier.CALENDAR:
            met = self._calendar_advance_met(phase, signal, on_date)
            immediate = True
        elif signal.tier == SeasonTriggerTier.LIVE and signal.min_temp_c is not None:
            met = self._live_advance_met(phase, signal, on_date)
            immediate = False
        else:  # climatological — date-based on the estimated frost termini
            met = self._climatological_advance_met(phase, signal, on_date)
            immediate = False

        if not met:
            # Condition absent → reset the hysteresis counter, keep the phase.
            return SeasonStateTransition(
                changed=False,
                from_phase=phase,
                to_phase=phase,
                season_year=state.season_year,
                consecutive_signal_days=0,
                reason_i18n_key=signal.reason_i18n_key,
            )

        if immediate:
            do_transition = True
            new_counter = 0
        else:
            counter = state.consecutive_signal_days + 1
            do_transition = counter >= self._threshold_days
            new_counter = 0 if do_transition else counter

        if not do_transition:
            return SeasonStateTransition(
                changed=False,
                from_phase=phase,
                to_phase=phase,
                season_year=state.season_year,
                consecutive_signal_days=new_counter,
                reason_i18n_key=signal.reason_i18n_key,
            )

        next_phase = _NEXT_PHASE[phase]
        season_year = self._resolve_season_year(phase, next_phase, state.season_year, signal, on_date)
        return SeasonStateTransition(
            changed=True,
            from_phase=phase,
            to_phase=next_phase,
            season_year=season_year,
            consecutive_signal_days=0,
            reason_i18n_key=signal.reason_i18n_key,
        )

    # ── season_year bookkeeping ─────────────────────────────────────────

    @staticmethod
    def _resolve_season_year(
        phase: SeasonPhase,
        next_phase: SeasonPhase,
        current_year: int | None,
        signal: SeasonSignal,
        on_date: date,
    ) -> int | None:
        """Set the season year on the entry into winter, release it on exit."""
        if phase == SeasonPhase.GROWING and next_phase == SeasonPhase.PRE_WINTER:
            # Winter 2026/27 is tracked as 2026 — the year the autumn onset falls in.
            return on_date.year
        if phase == SeasonPhase.PRE_SPRING and next_phase == SeasonPhase.GROWING:
            return None
        return current_year

    # ── Advance-condition predicates ────────────────────────────────────

    def _live_advance_met(self, phase: SeasonPhase, signal: SeasonSignal, on_date: date) -> bool:
        min_temp = signal.min_temp_c
        assert min_temp is not None  # guarded by the caller
        frost_soon = self._frost_within_window(signal, on_date)

        if phase == SeasonPhase.GROWING:
            return min_temp <= self._pre_winter_temp_c or frost_soon
        if phase == SeasonPhase.PRE_WINTER:
            return min_temp <= self._frost_temp_c or frost_soon
        if phase == SeasonPhase.WINTER_DORMANCY:
            after_coldest = on_date.month in _AFTER_COLDEST_MONTHS[signal.hemisphere]
            return min_temp > self._spring_temp_c and after_coldest
        # PRE_SPRING → growing: last frost passed and no imminent frost.
        last_doy = _parse_md(signal.estimated_last_frost_md)
        if last_doy is not None:
            last_frost_passed = _gap_after(_doy(on_date.month, on_date.day), last_doy) <= 45
        else:
            last_frost_passed = min_temp > self._spring_temp_c
        return last_frost_passed and not frost_soon

    def _climatological_advance_met(self, phase: SeasonPhase, signal: SeasonSignal, on_date: date) -> bool:
        first_doy = _parse_md(signal.estimated_first_frost_md)
        last_doy = _parse_md(signal.estimated_last_frost_md)
        on_doy = _doy(on_date.month, on_date.day)

        if phase == SeasonPhase.GROWING:
            return first_doy is not None and _gap_before(on_doy, first_doy) <= 14
        if phase == SeasonPhase.PRE_WINTER:
            if first_doy is None:
                return False
            end = last_doy if last_doy is not None else (first_doy + 120) % 365
            return _in_wrapped(on_doy, first_doy, end)
        if phase == SeasonPhase.WINTER_DORMANCY:
            return last_doy is not None and _gap_before(on_doy, last_doy) <= 30
        # PRE_SPRING → growing
        return last_doy is not None and _gap_after(on_doy, last_doy) <= 45

    @staticmethod
    def _calendar_advance_met(phase: SeasonPhase, signal: SeasonSignal, on_date: date) -> bool:
        windows = _CALENDAR_WINDOWS[signal.hemisphere]
        month = on_date.month
        if phase == SeasonPhase.GROWING:
            return month in windows["pre_winter"]
        if phase == SeasonPhase.PRE_WINTER:
            return month in windows["winter"]
        if phase == SeasonPhase.WINTER_DORMANCY:
            return month in windows["pre_spring"]
        return month in windows["growing"]

    @staticmethod
    def _frost_within_window(signal: SeasonSignal, on_date: date) -> bool:
        frost_date = signal.forecast_first_frost_date
        if frost_date is None:
            return False
        return 0 <= (frost_date - on_date).days <= _LIVE_FORECAST_WINDOW_DAYS
