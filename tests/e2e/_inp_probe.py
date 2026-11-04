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
window.__kpInp = probe;
return true;
"""

_SETTLE = """
const done = arguments[arguments.length - 1];
requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(done, 80)));
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

    def inp_text(self) -> str:
        return f"< {INP_FLOOR_MS}" if self.inp_ms is None else f"{self.inp_ms:.0f}"

    def exceeded(self) -> list[str]:
        """The advisory bounds this scenario is over (empty = within)."""
        over: list[str] = []
        if self.inp_ms is not None and self.inp_ms > INP_BUDGET_MS:
            over.append(f"INP {self.inp_ms:.0f} ms > {INP_BUDGET_MS} ms")
        if self.frame_p95_ms is not None and self.frame_p95_ms > FRAME_BUDGET_MS:
            over.append(f"frame p95 {self.frame_p95_ms:.1f} ms > {FRAME_BUDGET_MS} ms")
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
    "InpProbe",
    "Measurement",
    "report_json",
    "set_cpu_slowdown",
    "summary_table",
]
