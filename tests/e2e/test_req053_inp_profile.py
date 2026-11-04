"""INP measurement profile of the garden plan (REQ-053 GP-NFR-071, WP 8.29, issue #2672).

Spec-TC mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md; the profile is derived from GP-NFR-071):
  TC-053-060  ->  select, drag start, zoom: INP of each interaction on the planning editor (desktop)
  TC-053-060  ->  pinch zoom: frame time of a two-finger pinch on a 390 x 844 phone
  TC-053-060  ->  field mode, CPU 4x: INP of the first taps on the low-end profile

The bounds are **advisory**, like Lighthouse today (INP <= 200 ms, pinch frame <= 33 ms): a value over a bound is
reported (``warnings.warn``, JUnit properties ``inp_*``, the table in the test output and the JSON next to the
screenshots) and does not fail the test. What does fail: a broken measurement (no probe, no Event Timing API, no
frame recorded) and an arrangement that did not reach the state it measures (the bed was not selected, the zoom
level did not change). The instrument and its limits are described in ``_inp_probe.py``.

Preconditions are self-provisioned through the application's API, one fresh site per test (``_garden_plan_helpers``).
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.remote.webdriver import WebDriver

from ._garden_plan_helpers import BedSpec, bed_rect, provision_garden
from ._inp_probe import (
    CPU_SLOWDOWN,
    InpProbe,
    Measurement,
    report_json,
    set_cpu_slowdown,
    summary_table,
)
from .pages.field_mode_page import FieldModePage, set_phone_viewport
from .pages.garden_plan_page import GardenPlanPage

BED_NAME = "Beet 1"

#: A second finger within 50 ms of the first is ignored as a wet-finger artefact (GP-UX-041): the pinch waits.
SECOND_FINGER_DELAY_S = 0.12


def _report(results: list[Measurement], screenshot_dir: Path, record_property, label: str) -> None:
    """Print the table, store the JSON next to the screenshots, record the values, warn on a bound."""
    print("\n" + summary_table(results))  # noqa: T201 - the measurement report is the test's output
    (screenshot_dir / f"inp-profile-{label}.json").write_text(
        report_json(results), encoding="utf-8"
    )
    for item in results:
        record_property(f"inp_{label}_{item.name}_ms", item.inp_text())
        if item.frame_p95_ms is not None:
            record_property(f"inp_{label}_{item.name}_frame_p95_ms", f"{item.frame_p95_ms:.1f}")
        for over in item.exceeded():
            warnings.warn(f"GP-NFR-071 (advisory) {label}/{item.name}: {over}", stacklevel=2)


def _one_bed(base_url: str, seed: dict, purpose: str):
    garden = provision_garden(
        base_url, seed, purpose=purpose, beds=(BedSpec(BED_NAME, bed_rect(2.0, 1.0)),)
    )
    return garden, garden.bed_key(BED_NAME)


@pytest.mark.requires_desktop
def test_gp_nfr_071_inp_of_select_drag_start_and_zoom(
    browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot_dir: Path, record_property
) -> None:
    """TC-053-060 — INP of selecting a bed, starting a drag and zooming (pointer, wheel and button) on the editor.

    Each scenario resets the probe, runs one scripted gesture, waits for the state it is meant to produce and
    reads the worst interaction back. Breaks (loudly) if the probe is missing, if the bed was not selected, if
    the drag did not move the bed or if the zoom level did not change; an INP above 200 ms is a warning.
    """
    garden, bed = _one_bed(base_url, e2e_seed_data, "inp-desktop")
    plan = GardenPlanPage(browser, base_url).open(garden.site_key)
    probe = InpProbe(browser)
    results: list[Measurement] = []

    # select: a real click on the bed
    probe.install()
    plan.scroll_into_view(plan.wait_for_element(plan.SVG))
    centre = plan.object_centre(bed)
    plan._require_hit(centre, bed, "INP profile: selecting the bed")  # noqa: SLF001 - the page object's own guard
    ActionChains(browser).move_by_offset(
        0, 0
    ).perform()  # anchor the pointer origin in the viewport
    builder = ActionBuilder(browser)
    builder.pointer_action.move_to_location(round(centre.x), round(centre.y))
    builder.pointer_action.click()
    builder.perform()
    plan.wait_for_selected(bed, True, "INP profile: select by click")
    results.append(probe.read("select"))

    # drag start: press, first moves, release (the move itself is the editor's own work)
    probe.reset()
    before = plan.shape_origin_m(bed)
    plan.drag_object_by(bed, 60, 0)
    after = plan.shape_origin_m(bed)
    assert after != before, f"INP profile: the drag did not move the bed ({before} -> {after})"
    results.append(probe.read("drag_start"))

    # zoom by the toolbar button
    probe.reset()
    start_zoom = plan.zoom_percent()
    plan.wait_and_click(plan.ZOOM_IN)
    plan.poll().until(lambda _d: plan.zoom_percent() != start_zoom)
    results.append(probe.read("zoom_button"))

    # zoom by Ctrl + wheel about the pointer
    probe.reset()
    zoomed = plan.zoom_percent()
    canvas = plan.wait_for_element(plan.SVG)
    plan.scroll_into_view(canvas)
    ActionChains(browser).key_down(Keys.CONTROL).scroll_from_origin(
        ScrollOrigin.from_element(canvas), 0, -240
    ).key_up(Keys.CONTROL).perform()
    plan.poll().until(lambda _d: plan.zoom_percent() != zoomed)
    results.append(probe.read("zoom_wheel"))

    _report(results, screenshot_dir, record_property, "desktop")
    assert [item.name for item in results] == ["select", "drag_start", "zoom_button", "zoom_wheel"]


@pytest.mark.requires_desktop
def test_gp_nfr_071_pinch_zoom_frame_time_on_a_phone(
    browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot_dir: Path, record_property
) -> None:
    """TC-053-060 — Frame time while two fingers spread on the planning editor at 390 x 844 (advisory: p95 <= 33 ms).

    The pinch is a W3C two-pointer touch gesture; the zoom level must change, otherwise the gesture did not
    reach the editor and the frame times would describe nothing. A page that records no frame fails.
    """
    garden, _bed = _one_bed(base_url, e2e_seed_data, "inp-pinch")
    set_phone_viewport(browser, 390, 844)
    plan = GardenPlanPage(browser, base_url).open_in_planning_mode(garden.site_key)
    probe = InpProbe(browser)
    probe.install()
    before = plan.px_per_m()
    svg = plan.wait_for_element(plan.SVG)
    plan.scroll_into_view(svg)
    # A point of the plan that is inside the viewport and not covered by another surface (the panel, the sheet):
    # scan the visible part of the canvas top-down until both fingers' start points and their end points hit it.
    spot = browser.execute_script(
        "var c = arguments[0], r = c.getBoundingClientRect();"
        "var left = Math.max(r.left, 0), right = Math.min(r.right, window.innerWidth);"
        "var top = Math.max(r.top, 0), bottom = Math.min(r.bottom, window.innerHeight);"
        "var cx = (left + right) / 2;"
        "for (var y = top + 10; y < bottom - 10; y += 10) {"
        "  var ok = [cx - 110, cx - 20, cx + 20, cx + 110].every(function (x) {"
        "    var el = document.elementFromPoint(x, y); return el && c.contains(el); });"
        "  if (ok) return [cx, y]; }"
        "return null;",
        plan.wait_for_element(plan.CANVAS),
    )
    assert spot, "INP profile: no free point on the canvas for a two-finger pinch at this viewport"
    cx, cy = round(spot[0]), round(spot[1])

    probe.start_frames()
    actions = ActionBuilder(browser)
    first = actions.add_pointer_input(interaction.POINTER_TOUCH, "finger1")
    second = actions.add_pointer_input(interaction.POINTER_TOUCH, "finger2")
    # Both devices advance tick by tick: finger 1 lands first, finger 2 follows after the wet-finger window.
    first.create_pointer_move(x=cx - 20, y=cy, origin="viewport")
    second.create_pointer_move(x=cx + 20, y=cy, origin="viewport")
    first.create_pointer_down()
    second.create_pause(0)
    first.create_pause(SECOND_FINGER_DELAY_S)
    second.create_pause(SECOND_FINGER_DELAY_S)
    first.create_pause(0)
    second.create_pointer_down()
    for step in range(1, 7):
        first.create_pointer_move(x=cx - 20 - step * 12, y=cy, origin="viewport")
        second.create_pointer_move(x=cx + 20 + step * 12, y=cy, origin="viewport")
    first.create_pointer_up(0)
    second.create_pointer_up(0)
    actions.perform()
    probe.stop_frames()

    plan.poll().until(lambda _d: plan.px_per_m() != before)
    after = plan.px_per_m()
    assert after > before, (
        f"INP profile: the pinch did not zoom in ({before:.1f} -> {after:.1f} px/m)"
    )
    result = probe.read("pinch_zoom", expect_frames=True)
    _report([result], screenshot_dir, record_property, "pinch")


def test_gp_nfr_071_field_mode_on_the_low_end_profile(
    browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot_dir: Path, record_property
) -> None:
    """TC-053-060 — INP of the first taps in field mode with the CPU throttled 4x (the low-end Android profile).

    When the browser takes no CDP throttling command the profile cannot be reproduced: that is a **named gap**,
    reported in the output and as a property, and the same taps are measured un-throttled so the report is not
    empty. The taps are real WebDriver clicks: the bed row opens its sheet.
    """
    garden, bed = _one_bed(base_url, e2e_seed_data, "inp-field")
    set_phone_viewport(browser, 390, 844)
    field = FieldModePage(browser, base_url)
    field.open(garden.site_key)
    probe = InpProbe(browser)
    probe.install()
    # Throttle only now: the page load and the content waits run at full speed, the measured tap does not.
    throttled = set_cpu_slowdown(browser, CPU_SLOWDOWN)
    try:
        field.tap_bed(bed)
        result = probe.read("field_tap_bed", cpu_slowdown=CPU_SLOWDOWN if throttled else 1)
        if not throttled:
            result.notes.append(
                "named gap: this browser took no CPU throttling command; measured un-throttled"
            )
            record_property("inp_field_cpu_throttle", "unavailable")
            warnings.warn(
                "GP-NFR-071: CPU 4x throttling is not available in this browser session (named gap)",
                stacklevel=2,
            )
        _report([result], screenshot_dir, record_property, "field")
    finally:
        if throttled and not set_cpu_slowdown(browser, 1):
            warnings.warn(
                "GP-NFR-071: the CPU throttle could not be reset after the field-mode scenario",
                stacklevel=2,
            )
