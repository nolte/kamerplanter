"""Browser-free self-test of the INP measurement helpers (WP 8.29, GP-NFR-071; gesture frame time WP 9.6).

The in-page observers need a real browser; what is testable here is the Python side: how a reading becomes a
``Measurement``, which bounds are reported as exceeded, that a broken probe is loud and that an unavailable CPU
throttle is reported as unavailable instead of pretending.
"""

from __future__ import annotations

import pytest

from tests.e2e._inp_probe import (
    FRAME_BUDGET_MS,
    INP_BUDGET_MS,
    LAPTOP_FRAME_BUDGET_MS,
    PHONE_FRAME_BUDGET_MS,
    InpProbe,
    set_cpu_slowdown,
    summary_table,
)


class _Driver:
    def __init__(self, reading):
        self.reading = reading
        self.command_executor = type("Executor", (), {"_commands": {}})()

    def execute_script(self, _script):
        return self.reading

    def execute_async_script(self, _script):
        return None


def _reading(durations=(), frames=(), supported=True):
    return {
        "interactions": [{"name": "pointerup", "duration": d} for d in durations],
        "frames": list(frames),
        "supported": supported,
    }


def test_the_worst_interaction_is_the_scenario_value() -> None:
    result = InpProbe(_Driver(_reading(durations=[24, 96, 40]))).read("select")
    assert (result.inp_ms, result.interactions) == (96, 3)
    assert result.exceeded() == []


def test_no_interaction_above_the_floor_is_a_pass_not_a_gap() -> None:
    result = InpProbe(_Driver(_reading())).read("zoom")
    assert result.inp_ms is None and result.inp_text() == "< 16" and result.exceeded() == []


def test_a_value_over_the_bound_is_reported_not_raised() -> None:
    result = InpProbe(_Driver(_reading(durations=[INP_BUDGET_MS + 8]))).read("drag_start")
    assert result.exceeded() == [f"INP {INP_BUDGET_MS + 8:.0f} ms > {INP_BUDGET_MS} ms"]


def test_frame_p95_and_the_bound() -> None:
    frames = [16.0] * 95 + [50.0] * 5  # nearest rank: the 95th of 100 values is still 16
    result = InpProbe(_Driver(_reading(frames=frames))).read("pinch", expect_frames=True)
    assert result.frame_p95_ms == 16.0 and result.frame_max_ms == 50.0
    assert result.exceeded() == []
    worse = InpProbe(_Driver(_reading(frames=[16.0] * 94 + [50.0] * 6))).read("pinch")
    assert worse.frame_p95_ms == 50.0
    assert worse.exceeded() == [f"frame p95 50.0 ms > {FRAME_BUDGET_MS} ms"]


@pytest.mark.parametrize(
    ("reading", "message"),
    [
        (None, "probe is gone"),
        (_reading(supported=False), "no Event Timing API"),
    ],
)
def test_a_broken_probe_is_loud(reading, message) -> None:
    with pytest.raises(AssertionError, match=message):
        InpProbe(_Driver(reading)).read("select")


def test_a_pinch_without_a_single_frame_is_loud() -> None:
    with pytest.raises(AssertionError, match="recorded no frame"):
        InpProbe(_Driver(_reading())).read("pinch", expect_frames=True)


def test_a_browser_that_takes_no_cdp_command_is_reported_unavailable() -> None:
    class _NoCdp(_Driver):
        def execute(self, *_args):
            raise RuntimeError("unknown command")

    assert set_cpu_slowdown(_NoCdp(None), 4) is False


def test_the_table_lists_every_scenario() -> None:
    first = InpProbe(_Driver(_reading(durations=[120]))).read("select", cpu_slowdown=4)
    second = InpProbe(_Driver(_reading())).read("zoom")
    table = summary_table([first, second])
    assert "select" in table and "zoom" in table and "120" in table and "< 16" in table


# ── Gesture frame time (WP 9.6, GP-NFR-033/034) ─────────────────────────────


class _GestureDriver(_Driver):
    """Answers the cadence sampler with *cadence* and every other async script (the settle) with ``None``."""

    def __init__(self, reading, cadence=None):
        super().__init__(reading)
        self.cadence = cadence
        self.scripts: list[str] = []

    def execute_script(self, script):
        self.scripts.append(script)
        return self.reading

    def execute_async_script(self, script, *_args):
        return self.cadence if "cadence" in script else None


def test_a_60hz_frame_is_within_the_laptop_budget_with_the_refresh_tolerance() -> None:
    # An idle 60 Hz page reads 16.7 ms per frame: that is "no frame dropped", within 16 ms.
    driver = _GestureDriver(_reading(frames=[16.7] * 60))
    result = InpProbe(driver).read_gesture("drag", budget_ms=LAPTOP_FRAME_BUDGET_MS, vsync_ms=16.7)
    assert result.frame_p95_ms == 16.7 and result.exceeded() == []
    assert result.as_dict()["frame_budget_ms"] == LAPTOP_FRAME_BUDGET_MS
    assert any("stopFrames" in script for script in driver.scripts), (
        "the frame loop was not stopped"
    )


def test_one_dropped_frame_per_gesture_frame_is_over_the_laptop_budget() -> None:
    result = InpProbe(_GestureDriver(_reading(frames=[33.3] * 60))).read_gesture(
        "drag", budget_ms=LAPTOP_FRAME_BUDGET_MS, vsync_ms=16.7
    )
    assert result.exceeded() == ["frame p95 33.3 ms > 16 ms (+ 10% of the 16.7 ms refresh)"]
    # ... and still within the phone's two frames.
    phone = InpProbe(_GestureDriver(_reading(frames=[33.3] * 60))).read_gesture(
        "drag", budget_ms=PHONE_FRAME_BUDGET_MS, vsync_ms=16.7
    )
    assert phone.exceeded() == []


def test_without_a_cadence_the_bound_has_no_tolerance() -> None:
    result = InpProbe(_GestureDriver(_reading(frames=[16.7] * 60))).read_gesture(
        "zoom_in", budget_ms=LAPTOP_FRAME_BUDGET_MS, vsync_ms=None
    )
    assert result.frame_bound() == LAPTOP_FRAME_BUDGET_MS
    assert result.exceeded() == ["frame p95 16.7 ms > 16 ms"]


def test_a_gesture_without_a_frame_is_loud() -> None:
    with pytest.raises(AssertionError, match="recorded no frame"):
        InpProbe(_GestureDriver(_reading())).read_gesture(
            "drag", budget_ms=LAPTOP_FRAME_BUDGET_MS, vsync_ms=16.7
        )


def test_the_cadence_is_the_median_idle_gap() -> None:
    probe = InpProbe(_GestureDriver(_reading(), cadence=[16.6, 16.7, 50.0, 16.7, 16.8, 16.7]))
    assert probe.frame_cadence_ms() == 16.7


@pytest.mark.parametrize(
    ("cadence", "message"), [(None, "no cadence sampler"), ([16.7] * 4, "no frame cadence")]
)
def test_a_page_that_does_not_animate_has_no_cadence(cadence, message) -> None:
    with pytest.raises(AssertionError, match=message):
        InpProbe(_GestureDriver(_reading(), cadence=cadence)).frame_cadence_ms()
