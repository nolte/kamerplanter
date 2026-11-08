"""Interaction measurement for the REQ-053 INP profile (GP-NFR-071, WP 8.29).

What is measured, and with which instrument
-------------------------------------------
* **INP** (Interaction to Next Paint) of one scripted interaction: a ``PerformanceObserver`` of type ``event``
  (``durationThreshold`` 16 ms, the floor the Event Timing API allows) collects every event entry that carries an
  ``interactionId``; the duration of an interaction is the longest entry of its id (input delay + processing +
  presentation, rounded by the browser to 8 ms). A scenario's value is the **worst** interaction of the scenario -
  the INP of a session with fewer than 50 interactions is the maximum (web-vitals definition, p98 rule).
  An interaction below the 16 ms floor does not show up at all and is reported as ``< 16``: a pass, not a gap.
* **Frame time** of a gesture: a ``requestAnimationFrame`` loop records the gap between frames while the
  gesture runs (pinch-zoom probe).
* **Frame time of a drag and a zoom gesture** on a large plan (GP-NFR-033/034, the renderer measurement D-01 of
  WP 9.6): the same loop, read through :meth:`InpProbe.read_gesture` against a budget of 16 ms (laptop) or 33 ms
  (phone). A ``requestAnimationFrame`` gap is a whole number of display refreshes - at 60 Hz an idle page already
  reads 16.7 ms - so the bound is judged with a tolerance of a tenth of the page's own idle refresh interval
  (:meth:`InpProbe.frame_cadence_ms`): 16.7 ms is "one refresh, no frame dropped" and within 16 ms, 33.3 ms is one
  dropped frame and over it.
* **CPU 4x throttling** (the low-end Android profile) through the CDP command ``Emulation.setCPUThrottlingRate``.
  Selenium's ``Remote`` driver has no ``execute_cdp_cmd``; chromedriver (behind the Grid too) serves the command at
  ``/session/<id>/goog/cdp/execute``, which is registered here. When the browser refuses it the profile is
  reported as **not available** (a named gap), never silently measured un-throttled.

The thresholds are **advisory** like Lighthouse today (the CI score is a report, not a gate): a value over the
bound is reported (``warnings.warn`` and the ``inp_*`` properties of the JUnit XML), it does not fail the test.
A *broken measurement* (the probe is missing, no interaction produced any entry and no frame was recorded) does.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any

from selenium.webdriver.remote.webdriver import WebDriver

#: GP-NFR-071.
INP_BUDGET_MS = 200
FRAME_BUDGET_MS = 33
#: GP-NFR-033/034: one frame at 60 fps on a mid-range laptop, two on a mid-range phone.
LAPTOP_FRAME_BUDGET_MS = 16
PHONE_FRAME_BUDGET_MS = 33
#: The share of the idle refresh interval a frame gap may exceed its budget by (see the module docstring).
VSYNC_TOLERANCE = 0.1
#: Event Timing reports nothing shorter than this.
INP_FLOOR_MS = 16
CPU_SLOWDOWN = 4

_INSTALL = """
if (window.__kpInp && window.__kpInp.observer) { window.__kpInp.reset(); return true; }
const probe = { interactions: new Map(), frames: [], rafId: 0, last: 0, observer: null };
probe.consume = function (entries) {
  for (const e of entries) {
    if (!e.interactionId) continue;
    const seen = probe.interactions.get(e.interactionId);
    if (!seen || e.duration > seen.duration) {
      probe.interactions.set(e.interactionId, { name: e.name, duration: e.duration });
    }
  }
};
probe.observer = new PerformanceObserver((list) => probe.consume(list.getEntries()));
probe.observer.observe({ type: 'event', durationThreshold: 16, buffered: false });
probe.reset = function () {
  probe.consume(probe.observer.takeRecords());
  probe.interactions.clear();
  probe.frames = [];
};
probe.startFrames = function () {
  probe.frames = [];
  probe.last = 0;
  const tick = (t) => {
    if (probe.last) probe.frames.push(t - probe.last);
    probe.last = t;
    probe.rafId = requestAnimationFrame(tick);
  };
  probe.rafId = requestAnimationFrame(tick);
};
probe.stopFrames = function () { cancelAnimationFrame(probe.rafId); };
probe.cadence = function (ms, done) {
  const gaps = [];
  let last = 0;
  const started = performance.now();
  const tick = (t) => {
    if (last) gaps.push(t - last);
    last = t;
    if (t - started < ms) requestAnimationFrame(tick); else done(gaps);
  };
  requestAnimationFrame(tick);
};
window.__kpInp = probe;
return true;
"""

_SETTLE = """
const done = arguments[arguments.length - 1];
requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(done, 80)));
"""

_CADENCE = """
const done = arguments[arguments.length - 1];
const p = window.__kpInp;
if (!p || !p.cadence) { done(null); return; }
p.cadence(arguments[0], done);
"""

_READ = """
const p = window.__kpInp;
if (!p) return null;
p.consume(p.observer.takeRecords());
return {
  interactions: Array.from(p.interactions.values()),
  frames: p.frames.slice(),
  supported: PerformanceObserver.supportedEntryTypes.includes('event'),
};
"""


@dataclass
class Measurement:
    """One scenario's result."""

    name: str
    #: Worst interaction in ms, ``None`` when no interaction crossed the 16 ms floor.
    inp_ms: float | None = None
    interactions: int = 0
    frame_p95_ms: float | None = None
    frame_max_ms: float | None = None
    frames: int = 0
    cpu_slowdown: int = 1
    notes: list[str] = field(default_factory=list)
    #: The frame budget of a gesture (GP-NFR-033/034); ``None`` = :data:`FRAME_BUDGET_MS` (GP-NFR-071).
    frame_budget_ms: float | None = None
    #: The page's idle ``requestAnimationFrame`` interval; ``None`` = not measured, the bound has no tolerance.
    vsync_ms: float | None = None

    def inp_text(self) -> str:
        return f"< {INP_FLOOR_MS}" if self.inp_ms is None else f"{self.inp_ms:.0f}"

    def frame_budget(self) -> float:
        return FRAME_BUDGET_MS if self.frame_budget_ms is None else self.frame_budget_ms

    def frame_bound(self) -> float:
        """The value the frame p95 is held against: the budget plus the refresh tolerance."""
        tolerance = 0.0 if self.vsync_ms is None else VSYNC_TOLERANCE * self.vsync_ms
        return self.frame_budget() + tolerance

    def exceeded(self) -> list[str]:
        """The advisory bounds this scenario is over (empty = within)."""
        over: list[str] = []
        if self.inp_ms is not None and self.inp_ms > INP_BUDGET_MS:
            over.append(f"INP {self.inp_ms:.0f} ms > {INP_BUDGET_MS} ms")
        if self.frame_p95_ms is not None and self.frame_p95_ms > self.frame_bound():
            budget = f"{self.frame_budget():g} ms"
            if self.vsync_ms is not None:
                budget += f" (+ {VSYNC_TOLERANCE:.0%} of the {self.vsync_ms:.1f} ms refresh)"
            over.append(f"frame p95 {self.frame_p95_ms:.1f} ms > {budget}")
        return over

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "inp_ms": self.inp_ms,
            "interactions": self.interactions,
            "frame_p95_ms": self.frame_p95_ms,
            "frame_max_ms": self.frame_max_ms,
            "frames": self.frames,
            "cpu_slowdown": self.cpu_slowdown,
            "frame_budget_ms": self.frame_budget(),
            "vsync_ms": self.vsync_ms,
            "exceeded": self.exceeded(),
            "notes": self.notes,
        }


class InpProbe:
    """Installs the in-page observers and reads them back around one scripted gesture."""

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver

    def install(self) -> None:
        """Install (or reset) the observers on the current document; a navigation drops them."""
        ok = self.driver.execute_script(_INSTALL)
        if not ok:
            raise AssertionError("the INP probe could not be installed on the page")

    def reset(self) -> None:
        self.install()

    def start_frames(self) -> None:
        self.driver.execute_script("window.__kpInp.startFrames();")

    def stop_frames(self) -> None:
        self.driver.execute_script("window.__kpInp.stopFrames();")

    def read(self, name: str, *, cpu_slowdown: int = 1, expect_frames: bool = False) -> Measurement:
        """The scenario's result; raises when the measurement itself is broken."""
        # Event Timing entries are dispatched after the next presentation: let two frames and a task pass first.
        self.driver.execute_async_script(_SETTLE)
        data = self.driver.execute_script(_READ)
        if data is None:
            raise AssertionError(f"{name}: the INP probe is gone (the page navigated mid-scenario)")
        if not data["supported"]:
            raise AssertionError(
                f"{name}: this browser has no Event Timing API; INP cannot be measured"
            )
        durations = [float(item["duration"]) for item in data["interactions"]]
        frames = [float(gap) for gap in data["frames"]]
        result = Measurement(
            name=name,
            inp_ms=max(durations) if durations else None,
            interactions=len(durations),
            frames=len(frames),
            cpu_slowdown=cpu_slowdown,
        )
        if frames:
            ordered = sorted(frames)
            result.frame_p95_ms = ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]
            result.frame_max_ms = ordered[-1]
        if expect_frames and not frames:
            raise AssertionError(f"{name}: the frame probe recorded no frame")
        return result

    def frame_cadence_ms(self, sample_ms: int = 600) -> float:
        """The median ``requestAnimationFrame`` gap of the idle page: the refresh interval the gaps come in.

        Raises when the page produced fewer than five frames in *sample_ms* - a frame time measured on a page
        that does not animate would describe nothing.
        """
        gaps = self.driver.execute_async_script(_CADENCE, sample_ms)
        if gaps is None:
            raise AssertionError("the frame probe is gone or not installed (no cadence sampler)")
        ordered = sorted(float(gap) for gap in gaps)
        if len(ordered) < 5:
            raise AssertionError(
                f"the idle page produced {len(ordered)} frames in {sample_ms} ms; no frame cadence"
            )
        return ordered[len(ordered) // 2]

    def read_gesture(
        self, name: str, *, budget_ms: float, vsync_ms: float | None, cpu_slowdown: int = 1
    ) -> Measurement:
        """The frame time of the gesture since :meth:`start_frames`, held against *budget_ms* (GP-NFR-033/034).

        Lets the trailing render of the gesture land first (two frames and a task, the same settle as
        :meth:`read`), then stops the frame loop. A gesture that recorded no frame is a broken measurement and
        raises.
        """
        self.driver.execute_async_script(_SETTLE)
        self.stop_frames()
        result = self.read(name, cpu_slowdown=cpu_slowdown, expect_frames=True)
        result.frame_budget_ms = float(budget_ms)
        result.vsync_ms = vsync_ms
        return result


# ── CPU throttling ─────────────────────────────────────────────────────────


def _register_cdp(driver: WebDriver) -> None:
    commands = getattr(driver.command_executor, "_commands", None)
    if commands is not None and "executeCdpCommand" not in commands:
        commands["executeCdpCommand"] = ("POST", "/session/$sessionId/goog/cdp/execute")


def set_cpu_slowdown(driver: WebDriver, rate: int) -> bool:
    """Throttle the page's CPU by *rate* (1 = off). ``False`` when the browser takes no CDP command."""
    try:
        driver.execute_cdp_cmd("Emulation.setCPUThrottlingRate", {"rate": rate})  # type: ignore[attr-defined]
        return True
    except AttributeError:
        pass
    except Exception:  # noqa: BLE001 - a Grid that proxies no CDP: fall through to the raw command
        pass
    try:
        _register_cdp(driver)
        driver.execute(
            "executeCdpCommand",
            {"cmd": "Emulation.setCPUThrottlingRate", "params": {"rate": rate}},
        )
        return True
    except Exception:  # noqa: BLE001 - the named gap: the caller reports it
        return False


def summary_table(results: list[Measurement]) -> str:
    """A fixed-width text table for the test log and the PR report."""
    lines = [
        f"{'scenario':<34} {'cpu':>4} {'INP ms':>8} {'n':>3} {'frame p95':>10} {'frame max':>10}",
    ]
    for item in results:
        p95 = "-" if item.frame_p95_ms is None else f"{item.frame_p95_ms:.1f}"
        mx = "-" if item.frame_max_ms is None else f"{item.frame_max_ms:.1f}"
        lines.append(
            f"{item.name:<34} {item.cpu_slowdown:>3}x {item.inp_text():>8} {item.interactions:>3} "
            f"{p95:>10} {mx:>10}"
        )
    return "\n".join(lines)


def report_json(results: list[Measurement]) -> str:
    return json.dumps([item.as_dict() for item in results], indent=2, sort_keys=True)


__all__ = [
    "CPU_SLOWDOWN",
    "FRAME_BUDGET_MS",
    "INP_BUDGET_MS",
    "INP_FLOOR_MS",
    "LAPTOP_FRAME_BUDGET_MS",
    "PHONE_FRAME_BUDGET_MS",
    "VSYNC_TOLERANCE",
    "InpProbe",
    "Measurement",
    "report_json",
    "set_cpu_slowdown",
    "summary_table",
]
