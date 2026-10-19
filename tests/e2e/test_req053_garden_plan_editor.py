"""E2E baseline of the REQ-053 garden plan editor (WP 2.9, issue #2370; spec pin REQ-053 v1.4).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md, GP-ACC from the coverage matrix):
  TC-053-002  ->  draw a bed with the rectangle tool, snap to 2,0 x 1,0 m      (GP-ACC-002)
  TC-053-003  ->  drag a bed: grid snap, Alt without snap, Esc cancels          (GP-ACC-006)
  TC-053-004  ->  undo / redo of a move by keyboard                             (GP-ACC-007)
  TC-053-005  ->  move a bed by keyboard only, live-region announcement         (GP-ACC-008)
  TC-053-006  ->  planting positions follow a moved and rotated bed             (GP-ACC-005)
  TC-053-007  ->  save status, Ctrl+S, leave dialog (cancel / discard)          (UC-02/GP-UX-003)
  TC-053-008  ->  conflict with a second browser session, "Neu laden"           (GP-ACC-011)
  TC-053-009  ->  "Als Liste": all objects reachable, keyboard, axe             (GP-ACC-032)
  TC-053-014  ->  tent 1,2 x 1,2 m with 9 slots in the same plan view           (GP-ACC-036)
                  partial: see the test's docstring

Not automated here, on purpose (no skip, no xfail — there is nothing to run):
  TC-053-001  the editor of WP 2.1-2.8 has no boundary tool and does not mount on a
              plan without content (the route shows an empty state instead), so the
              boundary cannot be drawn in the browser.

Preconditions are self-provisioned through the application's own API, one fresh
site per test with a UUID-derived name (`_garden_plan_helpers.py`): no test reads
or mutates a plan another test or xdist worker touches. All cases are desktop
cases (TC-REQ-053 "Gerät: Desktop") and carry ``requires_desktop``.

Positions are model metres (x right, y up); every rect's ``origin`` is its
lower-left corner. The plan grid is 10 cm throughout.
"""

from __future__ import annotations

import math

import pytest
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from ._a11y_helpers import format_violations, run_axe
from ._garden_plan_helpers import (
    BedSpec,
    ObjectSpec,
    ProvisionedGarden,
    circle,
    polyline,
    provision_garden,
    read_plan,
    rect,
    stored_origin,
)
from .pages.garden_plan_page import GardenPlanPage

pytestmark = pytest.mark.requires_desktop

#: The bed most cases work on: 2 x 1 m, centred in the 10 x 10 m garden, so it
#: stays inside the visible canvas at 100 % zoom (the zoom centres on the plan).
BED_NAME = "Beet 1"
BED_ORIGIN = (4.0, 4.5)
SAVED = "Gespeichert"


def _dirty(count: int) -> str:
    return f"Ungespeicherte Änderungen ({count})"


@pytest.fixture
def plan(browser: WebDriver, base_url: str) -> GardenPlanPage:
    return GardenPlanPage(browser, base_url)


def _garden_with_one_bed(base_url: str, seed: dict, purpose: str) -> ProvisionedGarden:
    return provision_garden(
        base_url,
        seed,
        purpose=purpose,
        beds=(BedSpec(BED_NAME, rect(*BED_ORIGIN, 2.0, 1.0)),),
    )


# ── TC-053-002 ──────────────────────────────────────────────────────────────


@pytest.mark.smoke
def test_tc_053_002_draw_bed_with_rectangle_tool_snaps_to_2_by_1(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot, screenshot_dir
) -> None:
    """TC-053-002 — draw a bed with the rectangle tool; it snaps to 2,0 x 1,0 m (GP-ACC-002).

    Precondition (API): a 10 x 10 m garden with a 10 cm grid and no bed.
    The drag runs from (3.03, 6.02) to (5.04, 6.98) at 100 % zoom: only the
    grid snap turns that into the 2,0 x 1,0 m bed at (3,0 | 6,0). Breaks if the
    snap is off (2,01 x 0,96), the bed is not created, the panel shows other
    dimensions, the save does not reach the server, or the reload loses it.

    Spec deviation, not asserted: the panel shows no area ("Fläche 2,0 m²") and
    the plan draws no status badge on the bed.
    """
    garden = provision_garden(base_url, e2e_seed_data, purpose="tc002")
    plan.open(garden.site_key)
    plan.zoom_to(100)
    screenshot("053_002_01_plan_without_beds", "Plan mit Gartengrenze, noch ohne Beet")

    plan.choose_tool(plan.TOOL_BED)
    live: dict[str, bool] = {}

    def _while_dragging() -> None:
        live["ghost"] = plan.is_ghost_shown()
        live["dimension"] = plan.is_dimension_shown()
        # Viewport-only: a full-page capture would scroll under the held button.
        plan.take_screenshot("053_002_02_while_drawing", screenshot_dir)

    plan.draw_rect((3.03, 6.02), (5.04, 6.98), during=_while_dragging)
    assert live == {"ghost": True, "dimension": True}, (
        f"TC-053-002: while dragging, the outline preview and the live dimensions must "
        f"show; observed {live}"
    )

    plan.wait_for_pending(1, "TC-053-002: the drawn bed is one unsaved change")
    plan.wait_for_panel_field("width", 2.0, "TC-053-002: snapped width")
    plan.wait_for_panel_field("length", 1.0, "TC-053-002: snapped length")
    assert (plan.panel_field("x"), plan.panel_field("y")) == (3.0, 6.0), (
        "TC-053-002: the snapped corner must lie on the 10 cm grid at (3.0, 6.0), got "
        f"({plan.panel_field('x')}, {plan.panel_field('y')})"
    )
    assert plan.panel_name() == BED_NAME, (
        f"TC-053-002: the new bed should be named {BED_NAME!r}, the panel shows "
        f"{plan.panel_name()!r}"
    )
    screenshot("053_002_03_bed_drawn", "Beet gezeichnet, Eigenschaftenpanel 2,0 x 1,0 m")

    plan.save_with_button()
    plan.wait_for_status_text(SAVED, "TC-053-002: after saving")
    stored = read_plan(base_url, e2e_seed_data, garden.site_key)["locations"]
    assert [loc["name"] for loc in stored] == [BED_NAME], (
        f"TC-053-002: exactly one stored bed {BED_NAME!r} expected, got "
        f"{[loc['name'] for loc in stored]}"
    )
    geometry = stored[0]["geometry"]
    assert (geometry["origin"], geometry["width_m"], geometry["length_m"]) == (
        [3.0, 6.0],
        2.0,
        1.0,
    ), f"TC-053-002: stored geometry differs from the drawn one: {geometry}"

    plan.reload(garden.site_key)
    bed_key = stored[0]["key"]
    width, height = plan.shape_size_m(bed_key)
    assert math.isclose(width / height, 2.0, abs_tol=1e-6), (
        f"TC-053-002: the bed must be drawn at 2 : 1 after the reload, drawn {width} x {height}"
    )
    assert plan.shape_origin_m(bed_key) == (3.0, 6.0), (
        f"TC-053-002: after the reload the bed is drawn at {plan.shape_origin_m(bed_key)}"
    )
    screenshot("053_002_04_after_reload", "Nach dem Neuladen: Beet unverändert vorhanden")


# ── TC-053-003 ──────────────────────────────────────────────────────────────


def test_tc_053_003_drag_snaps_to_grid_alt_does_not_esc_cancels(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot, screenshot_dir
) -> None:
    """TC-053-003 — drag a bed 23 cm: with the grid it lands 20 cm on, with Alt 23 cm (GP-ACC-006).

    At 100 % zoom one screen pixel is exactly 1 cm, so a 23 px drag is a 0,23 m
    pointer move. Breaks if the move does not snap (4,23 without Alt), Alt still
    snaps (4,2 with Alt), Esc does not cancel a drag in progress, or no ghost /
    live dimension is shown while dragging.

    Spec deviation, not asserted: a snap guide line is only drawn by the draw
    tools, not while moving.
    """
    garden = _garden_with_one_bed(base_url, e2e_seed_data, "tc003")
    bed = garden.bed_key(BED_NAME)
    plan.open(garden.site_key)
    plan.zoom_to(100)
    plan.focus_canvas()
    screenshot("053_003_01_bed_before_drag", "Beet 1 an x = 4,0 m vor dem Ziehen")

    live: dict[str, bool] = {}

    def _while_dragging() -> None:
        live["ghost"] = plan.is_ghost_shown()
        live["dimension"] = plan.is_dimension_shown()
        # Viewport-only: a full-page capture would scroll under the held button.
        plan.take_screenshot("053_003_02_while_dragging", screenshot_dir)

    plan.drag_object_by(bed, 23, during=_while_dragging)
    assert live == {"ghost": True, "dimension": True}, (
        f"TC-053-003: while dragging, ghost and live dimensions must show; observed {live}"
    )
    plan.wait_for_panel_field("x", 4.2, "TC-053-003: a 0,23 m drag snaps to 0,20 m")
    assert plan.panel_field("y") == BED_ORIGIN[1], "TC-053-003: a horizontal drag keeps y"
    plan.wait_for_pending(1, "TC-053-003: the drag is one unsaved change")
    screenshot("053_003_03_snapped", "Ohne Alt: x = 4,2 m (Raster)")

    plan.undo_with_button()
    plan.wait_for_panel_field("x", BED_ORIGIN[0], "TC-053-003: undo puts the bed back")

    plan.drag_object_by(bed, 23, alt=True)
    plan.wait_for_panel_field("x", 4.23, "TC-053-003: with Alt the drag does not snap")
    screenshot("053_003_04_alt_no_snap", "Mit Alt: x = 4,23 m (kein Einrasten)")

    pending = plan.pending_count()

    def _escape_mid_drag() -> None:
        plan.press(Keys.ESCAPE)

    plan.drag_object_by(bed, 50, during=_escape_mid_drag)
    plan.wait_for_panel_field("x", 4.23, "TC-053-003: Esc during the drag")
    assert plan.shape_origin_m(bed) == (4.23, BED_ORIGIN[1]), (
        f"TC-053-003: after Esc the bed must stay where it was, drawn at {plan.shape_origin_m(bed)}"
    )
    assert plan.pending_count() == pending, (
        f"TC-053-003: a cancelled drag must not add a change ({pending} -> {plan.pending_count()})"
    )
    assert plan.save_status_text() == _dirty(pending), (
        f"TC-053-003: the header must still show unsaved changes, reads {plan.save_status_text()!r}"
    )
    screenshot("053_003_05_esc_cancelled", "Esc während des Ziehens: Beet bleibt stehen")


# ── TC-053-004 ──────────────────────────────────────────────────────────────


def test_tc_053_004_undo_and_redo_a_move_by_keyboard(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-004 — Ctrl+Z puts a moved bed back, Ctrl+Shift+Z moves it again (GP-ACC-007).

    Breaks if either shortcut does nothing, the pending count does not follow,
    or the undo/redo buttons do not mirror the history.

    Spec deviation: after the undo the header reads "Gespeichert", not
    "Ungespeicherte Änderungen (0)" — the count of zero is asserted, the wording
    is recorded in the PR.
    """
    garden = _garden_with_one_bed(base_url, e2e_seed_data, "tc004")
    bed = garden.bed_key(BED_NAME)
    plan.open(garden.site_key)
    plan.zoom_to(100)
    assert not plan.is_undo_enabled(), "TC-053-004: a freshly loaded plan has nothing to undo"
    screenshot("053_004_01_loaded", "Plan geladen, Rückgängig inaktiv")

    plan.drag_object_by(bed, 50)
    plan.wait_for_shape_origin(bed, (4.5, BED_ORIGIN[1]), "TC-053-004: moved by 0,5 m")
    plan.wait_for_status_text(_dirty(1), "TC-053-004: after the move")
    assert plan.is_undo_enabled() and not plan.is_redo_enabled(), (
        "TC-053-004: after one action undo is available and redo is not"
    )
    screenshot("053_004_02_moved", "Beet verschoben, Ungespeicherte Änderungen (1)")

    plan.focus_canvas()
    plan.press(Keys.CONTROL, "z")
    plan.wait_for_shape_origin(bed, BED_ORIGIN, "TC-053-004: Ctrl+Z")
    plan.wait_for_pending(0, "TC-053-004: Ctrl+Z removes the unsaved change")
    assert not plan.is_undo_enabled() and plan.is_redo_enabled(), (
        "TC-053-004: with the history undone, undo is inactive and redo active"
    )
    screenshot("053_004_03_undone", "Nach Strg+Z: Beet an der ursprünglichen Position")

    plan.press(Keys.CONTROL, Keys.SHIFT, "z")
    plan.wait_for_shape_origin(bed, (4.5, BED_ORIGIN[1]), "TC-053-004: Ctrl+Shift+Z")
    plan.wait_for_status_text(_dirty(1), "TC-053-004: after the redo")
    assert plan.is_undo_enabled() and not plan.is_redo_enabled(), (
        "TC-053-004: after the redo, undo is active and redo inactive again"
    )
    screenshot("053_004_04_redone", "Nach Strg+Umschalt+Z: Beet wieder verschoben")


# ── TC-053-005 ──────────────────────────────────────────────────────────────


def test_tc_053_005_move_bed_with_keyboard_only_and_hear_the_position(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-005 — reach, select and move a bed with the keyboard alone (GP-ACC-008).

    Tab reaches the bed (visible focus), Enter selects it, three Arrow-Right
    move it 3 grid steps (0,3 m), Shift+Arrow-Down 10 steps (1,0 m) down, the
    polite live region names the new coordinate, Esc drops the selection. No
    pointer input at all.

    Not covered: step 4 ("R rotates by 15°") — the editor has no R shortcut yet
    (WP 2.1-2.8); recorded in the PR instead of being asserted or skipped.
    """
    garden = _garden_with_one_bed(base_url, e2e_seed_data, "tc005")
    bed = garden.bed_key(BED_NAME)
    plan.open(garden.site_key)

    plan.tab_to_object(bed)
    assert plan.object_has_visible_focus(bed), (
        "TC-053-005: the bed reached by Tab must show a visible focus (:focus-visible)"
    )
    plan.press(Keys.ENTER)
    plan.wait_for_selected(bed, True, "TC-053-005: Enter selects the focused bed")
    screenshot("053_005_01_selected_by_keyboard", "Beet per Tab erreicht und mit Enter gewählt")

    for _ in range(3):
        plan.press(Keys.ARROW_RIGHT)
    plan.wait_for_panel_field("x", 4.3, "TC-053-005: three Arrow-Right = 3 grid steps")
    said = plan.wait_for_announcement(
        f"{BED_NAME} verschoben nach x 4,3 m", "TC-053-005: announcement after Arrow-Right"
    )
    assert "y 4,5 m" in said, f"TC-053-005: the announcement must carry the coordinate: {said!r}"
    screenshot("053_005_02_moved_right", "Drei Rasterschritte nach rechts, Ansage x 4,3 m")

    plan.press(Keys.SHIFT, Keys.ARROW_DOWN)
    plan.wait_for_panel_field("y", 3.5, "TC-053-005: Shift+Arrow-Down = 10 grid steps down")
    plan.wait_for_announcement("y 3,5 m", "TC-053-005: announcement after Shift+Arrow-Down")
    plan.wait_for_pending(4, "TC-053-005: four keyboard moves, four unsaved changes")
    screenshot("053_005_03_moved_down", "Zehn Rasterschritte nach unten, Ansage y 3,5 m")

    plan.press(Keys.ESCAPE)
    plan.wait_for_selected(bed, False, "TC-053-005: Esc drops the selection")
    plan.wait_for_panel_empty("TC-053-005: the panel returns to its empty state after Esc")
    assert plan.save_status_text() == _dirty(4), (
        f"TC-053-005: the moves stay unsaved, header reads {plan.save_status_text()!r}"
    )
    screenshot("053_005_04_escaped", "Esc: Auswahl aufgehoben, Änderungen bleiben ungespeichert")


# ── TC-053-006 ──────────────────────────────────────────────────────────────

#: 12 planting positions in two rows of six, bed frame (origin = bed corner).
_ROW_SLOTS = tuple((x, y) for y in (0.3, 0.7) for x in (0.2, 0.5, 0.8, 1.1, 1.4, 1.7))


def _in_plan(origin: tuple[float, float], rotation_deg: float, local: tuple[float, float]):
    """A bed-frame point in plan coordinates (rotation CCW about the bed origin)."""
    rad = math.radians(rotation_deg)
    x, y = local
    return (
        round(origin[0] + x * math.cos(rad) - y * math.sin(rad), 3),
        round(origin[1] + x * math.sin(rad) + y * math.cos(rad), 3),
    )


def test_tc_053_006_planting_positions_follow_a_moved_and_rotated_bed(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-006 — move a bed with 12 positions by 1 m and rotate it 90°; they move along (GP-ACC-005).

    The positions are read from the drawn markers before the change (positive
    control: the reader sees all 12 where the bed frame puts them) and after it
    (the fixed defect #2381: they stayed behind). Breaks if any position loses its place
    relative to the bed frame.

    Not covered: step 4 (bed view ``bed-plan-tab``) — there is no bed detail page
    yet (WP 2.1-2.8).
    """
    origin = (3.0, 4.0)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc006",
        beds=(BedSpec(BED_NAME, rect(*origin, 2.0, 1.0), slots=_ROW_SLOTS),),
    )
    bed = garden.bed_key(BED_NAME)
    plan.open(garden.site_key)

    before = sorted(plan.marker_centres(bed))
    expected_before = sorted(_in_plan(origin, 0.0, s) for s in _ROW_SLOTS)
    assert before == expected_before, (
        f"TC-053-006 precondition: the 12 positions must be drawn inside the bed frame; "
        f"drawn {before}, expected {expected_before}"
    )
    screenshot("053_006_01_bed_with_positions", "Beet mit 12 Pflanzpositionen")

    plan.select_with_keyboard(bed)
    plan.press(Keys.SHIFT, Keys.ARROW_RIGHT)
    moved = (origin[0] + 1.0, origin[1])
    plan.wait_for_panel_field("x", moved[0], "TC-053-006: Shift+Arrow-Right moves 1 m")
    plan.set_panel_field("rotation", 90.0)
    plan.wait_for_pending(2, "TC-053-006: move and rotation are two unsaved changes")
    screenshot("053_006_02_moved_and_rotated", "Beet um 1 m verschoben und um 90° gedreht")

    after = sorted(plan.marker_centres(bed))
    expected_after = sorted(_in_plan(moved, 90.0, s) for s in _ROW_SLOTS)
    assert after == expected_after, (
        f"TC-053-006: the 12 positions did not move and turn with the bed (#2381); drawn "
        f"{after}, expected {expected_after}"
    )

    plan.save_with_button()
    plan.reload(garden.site_key)
    stored = sorted(plan.marker_centres(bed))
    assert stored == expected_after, (
        f"TC-053-006: after saving and reloading the positions must sit in the moved, "
        f"rotated frame; drawn {stored}, expected {expected_after}"
    )


# ── TC-053-007 ──────────────────────────────────────────────────────────────


def test_tc_053_007_save_status_ctrl_s_and_leave_dialog(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-007 — no auto-save; Ctrl+S saves; leaving with changes asks first (UC-02, GP-UX-003).

    Breaks if a move is saved without being asked, Ctrl+S does not reach the
    server, the main navigation leaves without the dialog, "Abbrechen" loses
    the change, or "Verwerfen"/confirm does not discard it.

    Not asserted: the transient "Speichern …" between the two states — it lasts
    one request and is not durably observable.
    """
    garden = _garden_with_one_bed(base_url, e2e_seed_data, "tc007")
    bed = garden.bed_key(BED_NAME)
    plan.open(garden.site_key)

    plan.select_with_keyboard(bed)
    plan.press(Keys.ARROW_RIGHT)
    plan.wait_for_status_text(_dirty(1), "TC-053-007: a move leaves one unsaved change")
    assert stored_origin(read_plan(base_url, e2e_seed_data, garden.site_key), bed) == BED_ORIGIN, (
        "TC-053-007: there is no auto-save, the server must still hold the old position"
    )
    screenshot("053_007_01_unsaved", "Ungespeicherte Änderungen (1), noch nichts gespeichert")

    plan.press(Keys.CONTROL, "s")
    plan.wait_for_pending(0, "TC-053-007: Ctrl+S saves")
    plan.wait_for_status_text(SAVED, "TC-053-007: after Ctrl+S")
    saved = (4.1, BED_ORIGIN[1])
    assert stored_origin(read_plan(base_url, e2e_seed_data, garden.site_key), bed) == saved, (
        "TC-053-007: after Ctrl+S the server must hold the moved position"
    )
    screenshot("053_007_02_saved", "Nach Strg+S: Gespeichert")

    plan.press(Keys.ARROW_RIGHT)
    plan.wait_for_pending(1, "TC-053-007: the second move")
    plan.click_main_nav("/dashboard")
    plan.wait_for_leave_dialog("TC-053-007: leaving with an unsaved change")
    assert "/plan" in plan.driver.current_url, "TC-053-007: the dialog must hold the navigation"
    screenshot("053_007_03_leave_dialog", "Verlassen-Dialog bei ungespeicherter Änderung")

    plan.cancel_leaving()
    plan.wait_for_pending(1, "TC-053-007: 'Abbrechen' keeps the change")
    assert "/plan" in plan.driver.current_url, "TC-053-007: 'Abbrechen' stays in the plan"
    plan.wait_for_shape_origin(bed, (4.2, BED_ORIGIN[1]), "TC-053-007: change kept")
    screenshot("053_007_04_cancelled", "Abbrechen: im Plan geblieben, Änderung erhalten")

    plan.click_main_nav("/dashboard")
    plan.wait_for_leave_dialog("TC-053-007: leaving again")
    plan.confirm_leaving()
    plan.wait_for_url_contains("/dashboard")
    plan.open(garden.site_key)
    plan.wait_for_shape_origin(bed, saved, "TC-053-007: reopened plan shows the saved state")
    assert plan.pending_count() == 0, "TC-053-007: the discarded change must be gone"
    assert stored_origin(read_plan(base_url, e2e_seed_data, garden.site_key), bed) == saved, (
        "TC-053-007: discarding must not have saved the second move"
    )
    screenshot("053_007_05_reopened", "Wieder geöffnet: zuletzt gespeicherter Stand")


# ── TC-053-008 ──────────────────────────────────────────────────────────────


@pytest.fixture
def second_plan(request: pytest.FixtureRequest, device_profile: dict, base_url: str, browser):
    """Session B: a second, independent browser on the same tenant.

    Built by the same ``start_browser_session`` the ``browser`` fixture uses, so
    both sessions are configured identically (locale, modules, full-mode login).
    Requesting ``browser`` first orders A's session before B's.
    """
    from ._session_health import quit_driver
    from .conftest import start_browser_session

    driver = start_browser_session(request, device_profile)
    try:
        yield GardenPlanPage(driver, base_url)
    finally:
        quit_driver(driver)


def test_tc_053_008_conflict_with_a_second_session_offers_reload(
    plan: GardenPlanPage,
    second_plan: GardenPlanPage,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
    screenshot_dir,
) -> None:
    """TC-053-008 — B saves after A: conflict dialog; "Neu laden" shows A's state (GP-ACC-011).

    A and B open the same plan at the same revision. B moves bed "Beet B" twice
    (undo stack not empty), A moves "Beet A" and saves, then B saves. Breaks if
    B's save silently overwrites A's, the dialog lacks either action, or the
    reload keeps B's change or B's undo history.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc008",
        beds=(
            BedSpec("Beet A", rect(2.0, 2.0, 2.0, 1.0)),
            BedSpec("Beet B", rect(6.0, 6.0, 2.0, 1.0)),
        ),
    )
    bed_a, bed_b = garden.bed_key("Beet A"), garden.bed_key("Beet B")
    plan.open(garden.site_key)
    second_plan.open(garden.site_key)

    second_plan.select_with_keyboard(bed_b)
    second_plan.press(Keys.ARROW_RIGHT)
    second_plan.press(Keys.ARROW_RIGHT)
    second_plan.wait_for_pending(2, "TC-053-008: session B has two unsaved moves")
    assert second_plan.is_undo_enabled(), "TC-053-008: session B's undo stack is not empty"

    plan.select_with_keyboard(bed_a)
    plan.press(Keys.ARROW_UP)
    plan.save_with_button()
    a_saved = (2.0, 2.1)
    assert stored_origin(read_plan(base_url, e2e_seed_data, garden.site_key), bed_a) == a_saved, (
        "TC-053-008: session A's save must be on the server before B saves"
    )
    screenshot("053_008_01_session_a_saved", "Sitzung A: Beet A verschoben und gespeichert")

    second_plan.click_save_expecting_refusal()
    second_plan.wait_for_conflict_dialog("TC-053-008: session B saves on an outdated revision")
    second_plan.wait_for_status_text(
        "Konflikt – Plan wurde zwischenzeitlich geändert", "TC-053-008: B's header"
    )
    actions = (
        second_plan.conflict_button_text(second_plan.CONFLICT_RELOAD),
        second_plan.conflict_button_text(second_plan.CONFLICT_DOWNLOAD),
    )
    assert actions == ("Neu laden", "Meine Änderungen als Kopie behalten (JSON herunterladen)"), (
        f"TC-053-008: the dialog must offer reload and the JSON copy, offers {actions}"
    )
    # The `screenshot` fixture captures session A; B's checkpoints go next to them.
    second_plan.take_screenshot("053_008_02_session_b_conflict_dialog", screenshot_dir)

    second_plan.reload_after_conflict()
    second_plan.wait_for_shape_origin(bed_a, a_saved, "TC-053-008: B now shows A's move")
    second_plan.wait_for_shape_origin(bed_b, (6.0, 6.0), "TC-053-008: B's own moves are gone")
    assert not second_plan.is_undo_enabled(), (
        "TC-053-008: after the reload B's undo history is empty (Rückgängig inaktiv)"
    )
    assert second_plan.save_status_text() == SAVED, (
        f"TC-053-008: B is clean after the reload, header reads {second_plan.save_status_text()!r}"
    )
    stored = read_plan(base_url, e2e_seed_data, garden.site_key)
    assert stored_origin(stored, bed_b) == (6.0, 6.0), (
        "TC-053-008: B's refused save must not have reached the server"
    )
    second_plan.take_screenshot("053_008_03_session_b_reloaded", screenshot_dir)


# ── TC-053-009 ──────────────────────────────────────────────────────────────


def test_tc_053_009_list_view_reaches_every_object_and_passes_axe(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-009 — "Als Liste" lists every object, works by keyboard, axe finds nothing (GP-ACC-032).

    Plan: boundary, three beds, a path and a tree. Breaks if an object is
    missing from the list or lacks name/type/position/size, Tab cannot reach the
    list, arrow keys do not walk it, a list selection does not mark the object
    on the plan (or the reverse), or axe-core reports a WCAG 2.x A/AA violation
    in the editor in either view.
    """
    beds = (
        BedSpec("Beet Nord", rect(1.0, 7.0, 2.0, 1.0)),
        BedSpec("Beet Mitte", rect(4.0, 4.5, 2.0, 1.0)),
        BedSpec("Beet Süd", rect(1.0, 2.0, 3.0, 1.0)),
    )
    objects = (
        ObjectSpec("Weg", "path", polyline([(0.5, 0.5), (9.5, 0.5)], 0.6)),
        ObjectSpec("Apfelbaum", "tree", circle(8.0, 8.0, 1.0)),
    )
    garden = provision_garden(base_url, e2e_seed_data, purpose="tc009", beds=beds, objects=objects)
    plan.open(garden.site_key)
    editor = "[data-testid='garden-plan-editor']"
    plan_violations = run_axe(plan.driver, context=editor)
    screenshot("053_009_01_plan_view", "Kartenansicht vor dem Wechsel zur Liste")

    plan.show_list()
    expected = {**garden.beds, **garden.objects}
    listed = plan.list_keys()
    assert sorted(listed) == sorted(expected.values()), (
        f"TC-053-009: the list must hold exactly the five objects; lists {listed}, "
        f"expected {sorted(expected.values())}"
    )
    rows = {name: plan.list_row_text(key) for name, key in expected.items()}
    for name, text in rows.items():
        assert text.startswith(name) and " · x " in text and " m" in text, (
            f"TC-053-009: row of {name!r} must carry name, type, position and size: {text!r}"
        )
    assert "Beet · x 4 m, y 4,5 m · 2 × 1 m" in rows["Beet Mitte"], (
        f"TC-053-009: a bed row reads type, position and size: {rows['Beet Mitte']!r}"
    )
    assert "Baum" in rows["Apfelbaum"] and "Ø 2 m" in rows["Apfelbaum"], (
        f"TC-053-009: the tree row reads its type and crown size: {rows['Apfelbaum']!r}"
    )
    screenshot("053_009_02_list_view", "Ansicht „Als Liste“ mit allen fünf Objekten")

    first = plan.tab_into_list()
    plan.press(Keys.ARROW_DOWN)
    second = plan.active_list_key()
    assert second is not None and second != first, (
        f"TC-053-009: Arrow-Down must move the focus to the next row ({first} -> {second})"
    )
    plan.press(Keys.ENTER)
    plan.poll().until(lambda _d: plan.is_row_selected(second))
    plan.wait_for_element(plan.LIST_DETAILS)
    list_violations = run_axe(plan.driver, context=editor)
    screenshot("053_009_03_row_selected", "Listeneintrag per Tastatur gewählt, Details offen")

    plan.show_plan()
    plan.wait_for_selected(second, True, "TC-053-009: the list selection marks the plan object")

    other = next(key for key in garden.beds.values() if key != second)
    plan.select_with_keyboard(other)
    plan.show_list()
    assert plan.is_row_selected(other) and not plan.is_row_selected(second), (
        "TC-053-009: a selection on the plan marks its row in the list (and only that row)"
    )
    screenshot("053_009_04_selection_round_trip", "Auswahl auf dem Plan spiegelt sich in der Liste")

    report = (
        "TC-053-009: axe-core (WCAG 2.x A/AA) must report no violation in the editor.\n"
        f"Plan view:\n{format_violations(plan_violations)}\n"
        f"List view:\n{format_violations(list_violations)}"
    )
    assert not (plan_violations or list_violations), report


# ── TC-053-014 ──────────────────────────────────────────────────────────────

#: 3 x 3 positions of the 1,2 x 1,2 m tent, bed frame.
_TENT_SLOTS = tuple((x, y) for y in (0.2, 0.6, 1.0) for x in (0.2, 0.6, 1.0))


def test_tc_053_014_tent_is_drawn_like_an_outdoor_bed_with_its_9_positions(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-014 (partial) — a 1,2 x 1,2 m tent with 9 positions in the same view as a bed (GP-ACC-036).

    Precondition (API): an indoor site with a tent and 9 positions (3 x 3) — in
    production migration data (M1) — and an outdoor site with a raised bed and
    positions for comparison. Asserted: the tent is drawn as a 1,2 x 1,2 m
    frame with its 9 positions on the 3 x 3 grid, and it is the same kind of
    plan object with the same properties-panel hook set as the outdoor bed (no
    tent special path).

    Not covered, because the UI of WP 2.1-2.8 does not have it: the bed detail
    page (``bed-detail-page``, ``bed-plan-tab``, tabs Pflanzung/Pflege/Boden/
    Historie) and dragging a planting position (slots are selectable, not
    movable, in the editor). Recorded in the PR.
    """
    tent_origin = (1.0, 1.0)
    tent_site = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc014-tent",
        site_type="indoor",
        boundary=rect(0.0, 0.0, 4.0, 3.0),
        beds=(BedSpec("Zelt", rect(*tent_origin, 1.2, 1.2), "tent", _TENT_SLOTS),),
    )
    outdoor_site = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc014-bed",
        beds=(BedSpec(BED_NAME, rect(*BED_ORIGIN, 2.0, 1.0), slots=_TENT_SLOTS),),
    )
    tent = tent_site.bed_key("Zelt")
    outdoor_bed = outdoor_site.bed_key(BED_NAME)

    plan.open(tent_site.site_key)
    width, length = plan.shape_size_m(tent)
    assert (round(width, 3), round(length, 3)) == (1.2, 1.2), (
        f"TC-053-014: the tent frame must be 1,2 x 1,2 m, drawn {width} x {length}"
    )
    drawn = sorted(plan.marker_centres(tent))
    expected = sorted(_in_plan(tent_origin, 0.0, s) for s in _TENT_SLOTS)
    assert drawn == expected, (
        f"TC-053-014: the 9 positions must sit on the 3 x 3 grid in the tent; drawn {drawn}, "
        f"expected {expected}"
    )
    tent_kind = plan.object_kind(tent)
    plan.select_with_keyboard(tent)
    tent_hooks = plan.panel_testids()
    screenshot("053_014_01_tent_selected", "Zelt 1,2 x 1,2 m mit 9 Positionen, ausgewählt")

    plan.open(outdoor_site.site_key)
    bed_kind = plan.object_kind(outdoor_bed)
    plan.select_with_keyboard(outdoor_bed)
    bed_hooks = plan.panel_testids()
    screenshot("053_014_02_outdoor_bed_selected", "Outdoor-Beet zum Vergleich, ausgewählt")

    assert tent_kind == bed_kind == "location", (
        f"TC-053-014: tent and bed must be the same plan object kind ({tent_kind!r} vs "
        f"{bed_kind!r})"
    )
    assert tent_hooks == bed_hooks, (
        "TC-053-014: tent and outdoor bed must show the same properties panel (same "
        f"data-testid set); only tent: {sorted(tent_hooks - bed_hooks)}, only bed: "
        f"{sorted(bed_hooks - tent_hooks)}"
    )
