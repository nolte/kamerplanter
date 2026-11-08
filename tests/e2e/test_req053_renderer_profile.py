"""Renderer frame-time measurement for D-01 (REQ-053 GP-NFR-033/034, WP 9.6, issue #2746).

Spec-TC mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md; derived from GP-NFR-033/034 and D-01):
  TC-053-083  ->  drag and zoom frame time on the "large" class and on a plan of 3 000 visible objects,
                  profile Desktop (no throttling, 16 ms) and Mobile (390 x 844, CPU 4x, 33 ms)

What each case does, in this order (zoom first: a drag selects a bed, and on a phone the selection's sheet can
cover the canvas the wheel needs):

1. open the plan at its fit view and count what the renderer drew (``rendered_census``) - the arrangement check:
   every bed is drawn, and the synthetic case on the desktop really shows >= 3 000 objects (on the phone it
   cannot: the fit there is below the marker LOD, the count is recorded as it is);
2. throttle the CPU (mobile) and sample the idle frame cadence (the refresh interval the gaps come in);
3. Ctrl + wheel, 10 notches in (crossing the marker LOD threshold), count again, 10 notches out - frame time of
   each half; the zoom level must have changed both ways;
4. drag the bed nearest the canvas centre 60 px out and back to a small net offset in 30 paced pointer moves -
   frame time; the bed must have moved and the editor must report the unsaved move, which is then undone.

The bounds are **advisory**, like the INP profile of WP 8.29: a p95 over the profile's budget (GP-NFR-033/034) or
over D-01's 16 ms while dragging is reported - ``warnings.warn``, the JUnit properties ``renderer_*``, the table
in the test output and the JSON record (``renderer_record`` property and ``renderer-profile-<case>-<profile>.json``
next to the screenshots or in ``E2E_RENDERER_REPORT_DIR``) - and does not fail the test. What fails: a broken
measurement (no probe, no frame, no cadence) and an arrangement that is not what it claims (missing beds, a
synthetic plan below 3 000 visible objects, a zoom that did not zoom, a drag that did not move). The report and
the Go/No-Go for WP 9.7 are written from the records by ``tests/e2e/_renderer_report.py``.

Preconditions are self-provisioned through the API, one site per case and module (``_renderer_plans``); the
measurement saves nothing, so the profiles of a case share the site.
"""

from __future__ import annotations

import json
import os
import uuid
import warnings
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from ._frame_budget import (
    D01_DRAG_FRAME_MS,
    LAPTOP_FRAME_BUDGET_MS,
    PHONE_FRAME_BUDGET_MS,
    frame_bound,
)
from ._inp_probe import (
    CPU_SLOWDOWN,
    InpProbe,
    Measurement,
    set_cpu_slowdown,
    summary_table,
)
from ._renderer_plans import LARGE, SYNTHETIC_3000, MeasuredPlan, provision_grid_plan
from ._renderer_report import (
    D01_VISIBLE_OBJECTS,
    RECORD_FILE_PREFIX,
    RECORD_PROPERTY,
    RECORD_SCHEMA,
)
from .pages.field_mode_page import set_phone_viewport
from .pages.garden_plan_page import GardenPlanPage

# The module sets its own viewports (desktop window, phone 390 x 844): a mobile/tablet device run would only
# measure the same thing in a second emulation.
pytestmark = pytest.mark.requires_desktop

#: Every record of this run carries it; the report reads one run only (older runs' records never mix in).
#: ``--dist=loadfile`` keeps the module on one worker, so one import is one run.
RUN_ID = os.environ.get("E2E_RENDERER_RUN_ID") or uuid.uuid4().hex[:12]
#: The desktop profile's window (outer size); the record keeps the inner viewport and the canvas it gave.
DESKTOP_WINDOW = (1920, 1080)

#: Opening a plan of 5 000 plants: one large ``GET /plan`` (GP-NFR-031) and its first render.
OPEN_TIMEOUT_S = 90

#: 60 px out in 15 moves, back to +2 px in 15: the gesture is long enough for a frame time, and the net move lands
#: clear of every neighbour - the gaps across are 0.8 m ("large") and 0.3 m (synthetic); +2 px is at most 0.29 m
#: on the phone fit of "large" (~7 px/m) and ~0.13 m on that of the synthetic plan (~15 px/m). Not 0: a drag that
#: returns to its start leaves no move, and the effect check ("the bed moved") would have nothing to read.
#: Snapping runs on every move but the last; the last move and the release hold Alt (snap bypass, GP-FR-154), or
#: the object snap would pull the small offset back onto the column the bed was aligned with.
DRAG_WAYPOINTS = [(4 * k, 0) for k in range(1, 16)] + [
    (round(60 - k * 58 / 15), 0) for k in range(1, 16)
]
DRAG_STEP_MS = 16
#: Ten notches of 120 px: x 6 in zoom (``WHEEL_ZOOM_PER_PX`` 0.0015), from the fit across the marker LOD.
ZOOM_NOTCHES = 10
WHEEL_DELTA = 120
WHEEL_INTERVAL_MS = 40


@dataclass(frozen=True)
class Profile:
    name: str
    cpu: int
    budget_ms: float
    phone: bool


PROFILES = {
    "desktop": Profile("desktop", 1, LAPTOP_FRAME_BUDGET_MS, phone=False),
    "mobile": Profile("mobile", CPU_SLOWDOWN, PHONE_FRAME_BUDGET_MS, phone=True),
}


@pytest.fixture(scope="module", params=[LARGE, SYNTHETIC_3000], ids=lambda spec: spec.name)
def measured_plan(
    request: pytest.FixtureRequest, base_url: str, e2e_seed_data: dict
) -> MeasuredPlan:
    """The case's plan, seeded once per module and case **before** the test's browser exists.

    Module scope is what orders it: pytest sets up higher-scoped fixtures before function-scoped ones (the
    ``browser`` and the autouse ``screenshot`` fixture), so the minutes of seeding never run while a Grid
    session sits idle (the Grid drops a session after 300 s without a command - the first run lost
    ``large-desktop`` that way). The profiles of a case share it; the measurement saves nothing.
    """
    return provision_grid_plan(base_url, e2e_seed_data, request.param)


def _report_dir(screenshot_dir: Path) -> Path:
    configured = os.environ.get("E2E_RENDERER_REPORT_DIR")
    target = Path(configured) if configured else screenshot_dir
    target.mkdir(parents=True, exist_ok=True)
    return target


def _wait_for_all_beds(plan: GardenPlanPage, beds: int) -> dict[str, int]:
    """The fit view shows the whole plan: wait until every bed is drawn; the census of that moment."""
    try:
        plan.poll(OPEN_TIMEOUT_S).until(lambda _d: plan.rendered_census()["beds"] >= beds)
    except TimeoutException as exc:
        raise AssertionError(
            f"the fit view should draw all {beds} beds, it draws {plan.rendered_census()}"
        ) from exc
    return plan.rendered_census()


def _zoom_half(
    plan: GardenPlanPage, probe: InpProbe, name: str, direction: int, **read
) -> tuple[Measurement, float]:
    """One measured half of the zoom gesture; loud when the zoom level did not move in *direction*."""
    before = plan.px_per_m()
    at = plan.canvas_centre()
    probe.reset()
    probe.start_frames()
    plan.wheel_zoom(at, [-direction * WHEEL_DELTA] * ZOOM_NOTCHES, interval_ms=WHEEL_INTERVAL_MS)

    def moved(_d) -> bool:
        now = plan.px_per_m()
        return now > before * 1.5 if direction > 0 else now < before / 1.5

    try:
        plan.poll().until(moved)
    except TimeoutException as exc:
        probe.stop_frames()
        raise AssertionError(
            f"renderer profile: the {name} gesture did not zoom ({before:.1f} -> {plan.px_per_m():.1f} px/m)"
        ) from exc
    return probe.read_gesture(name, **read), plan.px_per_m()


def _measured_drag(
    plan: GardenPlanPage, probe: InpProbe, grab_inset_m: float | None, **read
) -> Measurement:
    bed = plan.bed_nearest_canvas_centre()
    before = plan.shape_origin_m(bed)
    probe.reset()
    probe.start_frames()
    plan.drag_object_along(
        bed, DRAG_WAYPOINTS, step_ms=DRAG_STEP_MS, alt_on_release=True, grab_inset_m=grab_inset_m
    )
    result = probe.read_gesture("drag", **read)
    try:
        plan.poll().until(lambda _d: plan.pending_count() > 0)
    except TimeoutException as exc:
        raise AssertionError(
            f"renderer profile: the drag of {bed!r} left no unsaved move ({plan.save_status_text()!r})"
        ) from exc
    after = plan.shape_origin_m(bed)
    assert after != before, (
        f"renderer profile: the drag did not move bed {bed!r} ({before} -> {after})"
    )
    return result


def _undo_the_drag(plan: GardenPlanPage) -> None:
    """Leave the plan as stored: no unsaved change, no leave prompt, nothing an auto-save could write.

    Ctrl+Z on the focused canvas rather than the toolbar button: the keyboard path exists on every viewport,
    the button may sit in an overflow menu on a phone. Verified through the pending count; nothing to do when
    no move is pending (the test failed before the drag, or the drag moved nothing).
    """
    if plan.pending_count() == 0:
        return
    plan.focus_canvas()
    plan.press(Keys.CONTROL, "z")
    plan.wait_for_pending(0, "renderer profile: undoing the measured drag")


def _publish(
    record: dict, results: list[Measurement], screenshot_dir: Path, record_property
) -> None:
    """Table, JSON record (property + sidecar), per-value properties, advisory warnings."""
    label = f"{record['case']}_{record['profile']}"
    print("\n" + summary_table(results))  # noqa: T201 - the measurement report is the test's output
    print(  # noqa: T201
        f"{label}: visible objects fit/zoomed = {record['census_fit']['visible_objects']}/"
        f"{record['census_zoomed']['visible_objects']}, vsync {record['vsync_ms']:.1f} ms, "
        f"throttle {record['throttle']}"
    )
    payload = json.dumps(record, sort_keys=True)
    record_property(RECORD_PROPERTY, payload)
    (
        _report_dir(screenshot_dir)
        / f"{RECORD_FILE_PREFIX}{record['case']}-{record['profile']}.json"
    ).write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    record_property(
        f"renderer_{label}_visible_objects", str(record["census_fit"]["visible_objects"])
    )
    for item in results:
        if item.frame_p95_ms is not None:
            record_property(
                f"renderer_{label}_{item.name}_frame_p95_ms", f"{item.frame_p95_ms:.1f}"
            )
        for over in item.exceeded():
            warnings.warn(f"GP-NFR-033/034 (advisory) {label}/{item.name}: {over}", stacklevel=2)
    drag = next(item for item in results if item.name == "drag")
    d01_bound = frame_bound(D01_DRAG_FRAME_MS, drag.vsync_ms)
    if drag.frame_p95_ms is not None and drag.frame_p95_ms > d01_bound:
        warnings.warn(
            f"D-01 (advisory) {label}: drag frame p95 {drag.frame_p95_ms:.1f} ms > {D01_DRAG_FRAME_MS:g} ms",
            stacklevel=2,
        )
    if record["case"] == "large":
        peak = max(
            record["census_fit"]["visible_objects"], record["census_zoomed"]["visible_objects"]
        )
        if peak > D01_VISIBLE_OBJECTS:
            warnings.warn(
                f"D-01 (advisory) {label}: {peak} visible objects > {D01_VISIBLE_OBJECTS}",
                stacklevel=2,
            )


@pytest.mark.parametrize("profile", sorted(PROFILES))
def test_gp_nfr_033_034_renderer_frame_time_for_d01(
    measured_plan: MeasuredPlan,
    profile: str,
    request: pytest.FixtureRequest,
    browser: WebDriver,
    base_url: str,
    screenshot_dir: Path,
    record_property,
) -> None:
    """TC-053-083 — Drag and zoom frame time (p95) of the SVG renderer on a large plan, per profile (D-01).

    Advisory against 16 ms (desktop) / 33 ms (mobile, CPU 4x) and D-01's 16 ms while dragging; the values and the
    visible-object count go to the JSON record the report generator reads. Fails only on a broken measurement or
    an arrangement that is not what the case claims.
    """
    measured = measured_plan
    case = measured.spec.name
    setup = PROFILES[profile]
    if setup.phone:
        set_phone_viewport(browser, 390, 844)
        plan = GardenPlanPage(browser, base_url).open_in_planning_mode(
            measured.garden.site_key, timeout=OPEN_TIMEOUT_S
        )
    else:
        browser.set_window_size(*DESKTOP_WINDOW)
        plan = GardenPlanPage(browser, base_url).open(
            measured.garden.site_key, timeout=OPEN_TIMEOUT_S
        )
    viewport = [int(v) for v in browser.execute_script("return [innerWidth, innerHeight];")]
    census_fit = _wait_for_all_beds(plan, measured.stored_beds)
    px_fit = plan.px_per_m()
    canvas_px = list(plan.svg_size_px())
    if case == SYNTHETIC_3000.name and not setup.phone:
        assert census_fit["visible_objects"] >= D01_VISIBLE_OBJECTS, (
            f"TC-053-083: the synthetic plan should show >= {D01_VISIBLE_OBJECTS} objects at the desktop fit "
            f"({px_fit:.1f} px/m), the renderer drew {census_fit} - the case would not measure D-01's load"
        )
    plan.take_screenshot(f"053_083_{case}_{profile}_01_fit", screenshot_dir)

    probe = InpProbe(browser)
    probe.install()
    throttle = "off"
    if setup.cpu > 1:
        # Throttle only now: the page load and the content waits ran at full speed, the gestures do not.
        throttle = "applied" if set_cpu_slowdown(browser, setup.cpu) else "unavailable"
        if throttle == "unavailable":
            record_property(f"renderer_{case}_{profile}_cpu_throttle", "unavailable")
            warnings.warn(
                "GP-NFR-033: CPU 4x throttling is not available in this browser session (named gap); "
                "the mobile profile is measured un-throttled",
                stacklevel=2,
            )
    cpu = setup.cpu if throttle == "applied" else 1
    # Whatever fails after the drag, the unsaved move is taken back (published first: a refused undo must not
    # cost the measurement).
    try:
        try:
            vsync = probe.frame_cadence_ms()
            read = {"budget_ms": setup.budget_ms, "vsync_ms": vsync, "cpu_slowdown": cpu}
            zoom_in, px_zoomed = _zoom_half(plan, probe, "zoom_in", +1, **read)
            census_zoomed = plan.rendered_census()
            zoom_out, _px = _zoom_half(plan, probe, "zoom_out", -1, **read)
            # A bed packed with plant markers is pressed in its plant-free edge strip (half its width inside).
            strip = measured.spec.drag_strip_m
            drag = _measured_drag(plan, probe, strip / 2 if strip else None, **read)
        finally:
            if throttle == "applied" and not set_cpu_slowdown(browser, 1):
                warnings.warn("GP-NFR-033: the CPU throttle could not be reset", stacklevel=2)
        plan.take_screenshot(f"053_083_{case}_{profile}_02_after", screenshot_dir)

        results = [zoom_in, zoom_out, drag]
        if throttle == "unavailable":
            for item in results:
                item.notes.append(
                    "named gap: no CPU throttling in this session; measured un-throttled"
                )
        record = {
            "schema": RECORD_SCHEMA,
            "case": case,
            "profile": profile,
            "cpu_slowdown": cpu,
            "throttle": throttle,
            "viewport": viewport,
            "canvas_px": canvas_px,
            "run_id": RUN_ID,
            "budget_ms": setup.budget_ms,
            "vsync_ms": vsync,
            "plan": measured.as_dict(),
            "census_fit": census_fit,
            "census_zoomed": census_zoomed,
            "px_per_m_fit": round(px_fit, 2),
            "px_per_m_zoomed": round(px_zoomed, 2),
            "gestures": [item.as_dict() for item in results],
            "recorded_at": datetime.now(UTC).isoformat(),
            "nodeid": request.node.nodeid,
        }
        _publish(record, results, screenshot_dir, record_property)
    finally:
        _undo_the_drag(plan)
    assert [item.name for item in results] == ["zoom_in", "zoom_out", "drag"] and all(
        item.frames > 0 for item in results
    ), f"TC-053-083: every gesture of {case}/{profile} carries a frame time: {results}"
