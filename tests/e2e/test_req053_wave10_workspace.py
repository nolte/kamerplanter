"""E2E of REQ-053 wave 10 part A - editor workspace, three widths, object properties, indoor plan (WP 10.13, #2834).

Spec pin REQ-053 v1.16 (§17.3 editor workspace, §9.8 indoor floor plan). Spec-TC Mapping (test TC ->
spec/e2e-testcases/TC-REQ-053.md, section 14):
  TC-053-098  ->  tabs Plan / Liste / Beete keep their state in ``?tab=``: deep link, browser Back to      (AC-7, AC-12,
                  the previous tab, a bed-list row opens "Plan" with the bed selected, ``?tab=xyz``        GP-UX-064)
                  shows "Plan", field mode has no tab bar
  TC-053-099  ->  a tab switch keeps the unsaved move, the selection and the zoom, without the leave       (AC-8, AC-16,
                  dialog; leaving the route still asks                                                      GP-UX-065)
  TC-053-100  ->  side panel: no reserved width, switch with aria-expanded/aria-controls, the state rule    (AC-4 part,
                  of GP-UX-068 step by step, layer switches with visible text, panel tabs by keyboard       AC-5, AC-6,
                  (WAI-ARIA tabs), selection group only with a selection                                    AC-17)
  TC-053-101  ->  desktop 1366 x 768: canvas >= 60 % of the viewport height, one header bar on one line,   (AC-1, AC-3,
                  vertical tool rail left of the canvas, zoom inside the canvas, panel docked beside it     AC-5, AC-14)
  TC-053-102  ->  tablet 820 x 1180 (md): rail left, the panel docked beside the canvas - zoom controls    (GP-UX-069)
                  and a selected bed stay uncovered (#2885),
                  no horizontal scrolling - the layout of md only, not the 1024 x 768 criterion (TC-053-103)
  TC-053-103  ->  1024 x 768 (lg, AC-2): every top-level tool of GP-UX-001 and its sub-menu entries, every   (GP-UX-001,
                  panel tab and every overflow entry reachable inside the viewport, no horizontal scrolling  GP-UX-069)
  TC-053-104  ->  phone 390 x 844 (planning mode): TouchBar and tool bar below the canvas, undo/redo in     (AC-9,
                  the TouchBar, tabs and panel switch in the overflow (entries >= 48 px with text), every   AC-15 part)
                  bar button >= 48 x 48 px, the selection opens a bottom sheet above the bars
  TC-053-105  ->  window and lamp properties edited and saved, the "off site" switch on (lamp) and refused  (GP-FR-180,
                  off (a box that sticks out), the object legend in the tab "Ebenen"                         §9.5)
  TC-053-106  ->  indoor plan without content: empty state with data-plan-kind="indoor" (garden one as     (GP-FR-182,
                  counter-check), "Grundriss zeichnen", a window drawn as a line, its derived direction,    GP-UX-049,
                  stored                                                                                    GP-FR-180)
  TC-053-107  ->  "Aus Fenster vorschlagen": preview, cancel changes nothing, confirm changes only the     (GP-FR-181,
                  sun window                                                                                 G-W10 c)
  TC-053-108  ->  indoor tab and list "Pflanzplätze" with tent and shelf (not the room), no frost layer;   (GP-FR-183,
                  the garden keeps "Beete" and its frost layer                                               GP-FR-182)

Breakpoints are the app theme's own (``theme/tokens.ts``): md = 768 px, lg = 1024 px - so 1024 x 768 is already lg
(docked panel), and the tablet case uses the suite's tablet size 820 x 1180, which is md (drawer).

Device: every case carries ``requires_desktop`` and runs on the desktop profile. The three width cases put the
browser at exactly their width themselves (``set_phone_viewport`` resizes and reads ``innerWidth``/``innerHeight``
back; under the mobile/tablet profiles a CDP emulation would pin another size, so they do not run there). They
first store the user's dismissal of the light-mode warning banner (``dismiss_light_mode_warning``): the banner shows
only in light mode on a non-private host and would be measured as part of the editor's height otherwise.

Testids (AC-10, GP-UX-070): the suite reaches the reworked editor only through the ``data-testid`` the earlier waves
already used (``garden-plan-canvas``, ``garden-plan-svg``, ``garden-plan-toolbar``, ``bed-list-section`` …) via
the migrated page objects; a renamed id breaks these cases, as it breaks the wave 2-9 suites that use them.

Preconditions are self-provisioned through the application's own API, one fresh site per test with a UUID-derived
name (`_garden_plan_helpers.py`): sites (garden and indoor), plan boundaries, beds/tents/shelves/rooms and garden
objects through ``plan/batch`` exactly as the editor saves them, the tent's sun facts through ``PATCH /locations``
as the bed dialog sends them. No shared fixture is mutated; nothing global is touched.

Waits are anchored on state - ``aria-selected`` of a tab and the URL, ``data-variant``/``data-tab`` of the side panel,
``aria-expanded`` of its switch, the save bar's pending-change count (emptied only by a fulfilled save), a dialog
leaving the DOM - never on time. Every absence is asserted after a positive anchor of the same render, every saved
outcome is read back from the server.
"""

from __future__ import annotations

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from ._garden_plan_helpers import (
    BedSpec,
    ObjectSpec,
    create_site,
    patch_location,
    polyline,
    provision_garden,
    read_plan,
    rect,
    stored_object,
    tenant_location,
)
from .pages.field_mode_page import set_phone_viewport
from .pages.garden_plan_workspace_page import WorkspacePlanPage

pytestmark = pytest.mark.requires_desktop

DIRTY_ONE = "Ungespeicherte Änderungen (1)"
#: Touch targets of UI-NFR-001 R-011 / GP-UX-008 (half a pixel for sub-pixel layout).
MIN_TARGET_PX = 47.5
#: The indoor flat of every indoor case: 6 x 4 m, north up (``north_angle_deg`` 0).
FLAT = rect(0.0, 0.0, 6.0, 4.0)
#: A window on the inside of the south wall: a line 2 m long, 10 cm wide, 5-15 cm from the wall (inside the outline,
#: so it is no containment violation); the outline tells its outside - south, azimuth 180°.
SOUTH_WINDOW = polyline([(1.0, 0.1), (3.0, 0.1)], 0.1)


@pytest.fixture
def plan(browser: WebDriver, base_url: str) -> WorkspacePlanPage:
    return WorkspacePlanPage(browser, base_url)


def _sun_facts(location: dict) -> tuple[str, dict, dict]:
    """``(sun_exposure, sun_profile, the other site conditions)`` of a stored location."""
    conditions = dict(location.get("site_conditions") or {})
    profile = dict(conditions.pop("sun_profile", None) or {})
    return location.get("sun_exposure"), profile, conditions


# ── TC-053-098 ──────────────────────────────────────────────────────────────


@pytest.mark.smoke
def test_tc_053_098_tabs_keep_their_state_in_the_url_deep_link_back_and_row(
    plan: WorkspacePlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-098 - tabs Plan / Liste / Beete in ``?tab=``: deep link, Back, row -> Plan, unknown value, field mode.

    Breaks if a deep link opens another tab, a switch does not write the URL, Back does not return to the previous
    tab (or asks about unsaved changes), the bed-list row does not open "Plan" with that bed selected, ``?tab=xyz``
    shows anything but "Plan", or field mode shows the tab bar (AC-7, AC-12, GP-UX-064).
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc098",
        beds=(
            BedSpec("Beet A", rect(1.0, 4.5, 2.0, 1.0)),
            BedSpec("Beet B", rect(6.0, 4.5, 2.0, 1.0)),
        ),
    )
    bed_a, bed_b = garden.bed_key("Beet A"), garden.bed_key("Beet B")

    plan.open_deep_link(garden.site_key, "tab=beds", "beds")
    plan.wait_for_tab_content("beds", "TC-053-098: the deep link ?tab=beds")
    plan.wait_for_bed_list_keys({bed_a, bed_b}, "TC-053-098: the bed list behind the deep link")
    assert not plan.is_any_displayed(plan.CANVAS), (
        "TC-053-098: behind the tab 'Beete' the canvas must be hidden"
    )
    screenshot("053_098_01_deep_link_beds", "Deep-Link ?tab=beds: Tab „Beete“ aktiv, Beetliste")

    plan.open_tab("list")
    plan.wait_for_tab("list", "TC-053-098: switching to 'Liste'")
    plan.wait_for_tab_content("list", "TC-053-098: the list tab")
    assert plan.url_tab_param() == "list", (
        f"TC-053-098: the URL should say tab=list: {plan.driver.current_url}"
    )
    plan.open_tab("plan")
    plan.wait_for_tab("plan", "TC-053-098: switching to 'Plan'")
    plan.wait_for_tab_content("plan", "TC-053-098: the plan tab")
    assert plan.url_tab_param() == "plan", (
        f"TC-053-098: the URL should say tab=plan: {plan.driver.current_url}"
    )

    plan.go_back_to_tab("list", "TC-053-098: Back from 'Plan'")
    plan.wait_for_tab_content("list", "TC-053-098: Back shows the list again")
    assert not plan.is_any_displayed(plan.LEAVE_DIALOG), (
        "TC-053-098: Back between tabs must not ask about unsaved changes"
    )
    plan.go_back_to_tab("beds", "TC-053-098: Back from 'Liste'")
    plan.wait_for_bed_list_keys({bed_a, bed_b}, "TC-053-098: Back returns to the bed list")
    screenshot("053_098_02_back_to_beds", "Zweimal „Zurück“: wieder Tab „Beete“")

    plan.activate_bed_list_row(bed_b)
    plan.wait_for_tab("plan", "TC-053-098: a bed-list row opens 'Plan'")
    plan.wait_for_selected(bed_b, True, "TC-053-098: the row's bed is selected on the plan")
    assert not plan.is_selected(bed_a), (
        "TC-053-098: only the row's bed may be selected, Beet A is too"
    )
    screenshot("053_098_03_row_to_plan", "Zeile Beet B gewählt: Tab „Plan“, Beet B ausgewählt")

    plan.open_deep_link(garden.site_key, "tab=xyz", "plan")
    plan.wait_for_tab_content("plan", "TC-053-098: ?tab=xyz")
    assert plan.url_tab_param() == "xyz", (
        f"TC-053-098: the unknown value stays in the URL and shows 'Plan': {plan.driver.current_url}"
    )
    screenshot("053_098_04_unknown_tab", "?tab=xyz: Tab „Plan“")

    plan.open_field_mode_with_tab(garden.site_key)
    assert not plan.tab_bar_present(), (
        "TC-053-098: field mode must not show the tab bar, even with ?tab=beds"
    )
    screenshot("053_098_05_field_mode", "?mode=field&tab=beds: Feldmodus ohne Tab-Leiste")


# ── TC-053-099 ──────────────────────────────────────────────────────────────


def test_tc_053_099_tab_switch_keeps_the_unsaved_move_selection_and_zoom(
    plan: WorkspacePlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-099 - Plan -> Liste -> Beete -> Plan keeps the unsaved move, the selection and the zoom; no dialog.

    Breaks if a tab switch asks about unsaved changes, drops the pending move, the selection or the zoom level, or
    if leaving the route no longer asks (AC-8, AC-16, GP-UX-065). The viewport's pan is a vitest matter.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc099",
        beds=(BedSpec("Beet A", rect(4.0, 4.5, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet A")
    plan.open(garden.site_key)
    zoom_before = plan.zoom_percent()

    plan.select_with_keyboard(bed)
    plan.press(Keys.ARROW_RIGHT)
    plan.wait_for_panel_field("x", 4.1, "TC-053-099: one grid step to the right")
    plan.wait_for_pending(1, "TC-053-099: the move is one unsaved change")
    screenshot("053_099_01_moved", "Beet A um einen Rasterschritt verschoben, ungespeichert")

    for tab in ("list", "beds", "plan"):
        plan.open_tab(tab)
        plan.wait_for_tab(tab, f"TC-053-099: switching to {tab!r}")
        plan.wait_for_tab_content(tab, f"TC-053-099: the tab {tab!r}")
        assert not plan.is_any_displayed(plan.LEAVE_DIALOG), (
            f"TC-053-099: switching to {tab!r} must not ask about unsaved changes"
        )
        assert plan.save_status_text() == DIRTY_ONE, (
            f"TC-053-099: after switching to {tab!r} the header should read {DIRTY_ONE!r}, "
            f"it reads {plan.save_status_text()!r}"
        )
        if tab == "beds":
            screenshot("053_099_02_beds_tab", "Tab „Beete“: Änderung weiter ungespeichert")

    assert plan.is_selected(bed), "TC-053-099: back on 'Plan' Beet A must still be selected"
    assert plan.zoom_percent() == zoom_before, (
        f"TC-053-099: the zoom changed over the tab switches: {zoom_before} % -> {plan.zoom_percent()} %"
    )
    plan.wait_for_shape_origin(bed, (4.1, 4.5), "TC-053-099: the bed stays at the moved position")
    screenshot(
        "053_099_03_back_on_plan", "Zurück auf „Plan“: Auswahl, Zoom und Verschiebung unverändert"
    )

    plan.click_main_nav("/dashboard")
    plan.wait_for_leave_dialog("TC-053-099: leaving the route with an unsaved change asks")
    screenshot("053_099_04_leave_dialog", "Verlassen der Route: Ungespeichert-Dialog")
    plan.cancel_leaving()
    plan.wait_for_pending(1, "TC-053-099: 'Abbrechen' keeps the change")


# ── TC-053-100 ──────────────────────────────────────────────────────────────


def test_tc_053_100_side_panel_state_rule_switch_and_keyboard_tabs(
    plan: WorkspacePlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-100 - the side panel's state rule (GP-UX-068) step by step on the docked panel (>= lg).

    Breaks if the collapsed panel reserves width or renders, the switch lacks ``aria-expanded``/``aria-controls`` or
    names another element, a selection does not open "Eigenschaften", a deselect closes a panel the user opened (or
    leaves open one the selection opened), the first user open is not "Ansicht", a reopen forgets the last tab, the
    layer switches have no visible text, the tabs break the WAI-ARIA pattern or the keyboard, or the selection group
    renders without a selection (AC-4 part, AC-5, AC-6, AC-17).
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc100",
        beds=(BedSpec("Beet A", rect(4.0, 4.5, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet A")
    plan.open(garden.site_key)

    plan.wait_for_element_visible(plan.TOOLBAR)
    assert plan.side_panel_state() is None, (
        f"TC-053-100: without a selection the panel is collapsed, it is {plan.side_panel_state()}"
    )
    expanded, controls = plan.panel_toggle_aria()
    assert expanded == "false" and controls, (
        f"TC-053-100: the collapsed switch should carry aria-expanded=false and aria-controls: {expanded!r}, {controls!r}"
    )
    assert not plan.is_present(plan.SELECTION_GROUP), (
        "TC-053-100: no selection, yet the selection group renders"
    )
    header, area = (
        plan.rect_of(plan.HEADER_BAR, "header bar"),
        plan.rect_of(plan.CANVAS_AREA, "canvas area"),
    )
    assert header["right"] - area["right"] <= 2, (
        f"TC-053-100: the collapsed panel must reserve no width - the canvas area ends at {area['right']:.0f} px, "
        f"the header bar at {header['right']:.0f} px"
    )
    screenshot("053_100_01_collapsed", "Ohne Auswahl: kein Seitenpanel, Zeichenfläche bis zum Rand")

    plan.select_with_keyboard(bed)
    plan.wait_for_side_panel(
        ("docked", "properties"), "TC-053-100: a new selection opens 'Eigenschaften'"
    )
    expanded, controls = plan.panel_toggle_aria()
    assert expanded == "true", (
        f"TC-053-100: the open panel's switch should say aria-expanded=true: {expanded!r}"
    )
    assert controls == plan.side_panel_id(), (
        f"TC-053-100: aria-controls {controls!r} must name the panel on screen ({plan.side_panel_id()!r})"
    )
    plan.wait_for_element_visible(plan.SELECTION_GROUP)
    screenshot("053_100_02_selected", "Auswahl: Panel auf „Eigenschaften“, Auswahlgruppe sichtbar")

    plan.deselect_with_escape(bed)
    plan.wait_for_side_panel(
        None, "TC-053-100: the selection opened the panel, the deselect closes it"
    )
    assert not plan.is_present(plan.SELECTION_GROUP), (
        "TC-053-100: the selection group outlived the selection"
    )

    plan.click_panel_toggle()
    plan.wait_for_side_panel(
        ("docked", "view"), "TC-053-100: the first open without a selection shows 'Ansicht'"
    )
    plan.choose_side_panel_tab("layers")
    texts = plan.layer_toggle_texts()
    unlabelled = sorted(testid for testid, text in texts.items() if not text)
    assert not unlabelled, (
        f"TC-053-100: layer switches without visible text: {unlabelled} (all: {texts})"
    )
    # The legend lists what the switched-on layers draw; it renders once a layer is on (``ZoneLegend``).
    plan.set_layer("zones", True)
    plan.wait_for_element_visible(plan.LAYER_LEGEND)
    screenshot(
        "053_100_03_layers",
        "Vom Nutzer geöffnet: Tab „Ebenen“ mit beschrifteten Schaltern und Legende",
    )

    plan.select_with_keyboard(bed)
    plan.wait_for_side_panel(
        ("docked", "properties"), "TC-053-100: a selection switches to 'Eigenschaften'"
    )
    plan.deselect_with_escape(bed)
    plan.wait_for_element_visible(plan.PANEL_EMPTY)
    assert plan.side_panel_state() == ("docked", "properties"), (
        f"TC-053-100: the user opened the panel, a deselect must not close it: {plan.side_panel_state()}"
    )
    screenshot("053_100_04_user_panel_stays", "Vom Nutzer geöffnet: bleibt nach dem Abwählen offen")

    plan.click_panel_toggle()
    plan.wait_for_side_panel(None, "TC-053-100: the switch closes the panel")
    plan.click_panel_toggle()
    plan.wait_for_side_panel(
        ("docked", "layers"), "TC-053-100: reopened without a selection: the last used tab"
    )

    wiring = plan.panel_tab_wiring()
    selected = [tab["testid"] for tab in wiring if tab["selected"] == "true"]
    stops = [tab["testid"] for tab in wiring if tab["tabindex"] == "0"]
    assert selected == ["garden-plan-side-panel-tab-layers"] == stops, (
        f"TC-053-100: exactly the active tab is selected and a tab stop; selected {selected}, stops {stops}"
    )
    broken = [
        tab["testid"]
        for tab in wiring
        if not tab["controls"]
        or tab["panelRole"] != "tabpanel"
        or tab["panelLabelledBy"] != tab["id"]
    ]
    assert len(wiring) == 4 and not broken, (
        f"TC-053-100: WAI-ARIA tab wiring broken for {broken}: {wiring}"
    )

    # Manual activation (#2887): an arrow moves the focus only, Enter activates the focused tab.
    plan.press_on_active_panel_tab(Keys.ARROW_RIGHT)
    assert plan.focused_testid() == "garden-plan-side-panel-tab-zones", (
        f"TC-053-100: Arrow-Right moves the focus to the next tab, focus is on {plan.focused_testid()!r}"
    )
    assert plan.side_panel_state() == ("docked", "layers"), (
        f"TC-053-100: an arrow alone activates no tab: {plan.side_panel_state()}"
    )
    plan.press(Keys.ENTER)
    plan.wait_for_side_panel(("docked", "zones"), "TC-053-100: Enter activates the focused tab")
    plan.press_on_active_panel_tab(Keys.HOME)
    plan.press(Keys.ENTER)
    plan.wait_for_side_panel(
        ("docked", "properties"), "TC-053-100: Home + Enter selects the first tab"
    )
    plan.press_on_active_panel_tab(Keys.END)
    plan.press(Keys.ENTER)
    plan.wait_for_side_panel(("docked", "zones"), "TC-053-100: End + Enter selects the last tab")
    screenshot("053_100_05_keyboard_tabs", "Panel-Tabs per Tastatur: Ende → „Zonen“")


# ── TC-053-101 ──────────────────────────────────────────────────────────────


def test_tc_053_101_desktop_1366_canvas_height_one_header_rail_left_panel_docked(
    plan: WorkspacePlanPage,
    browser: WebDriver,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
    record_property,
) -> None:
    """TC-053-101 - at 1366 x 768 the canvas is >= 60 % of the viewport height in the real app shell.

    Breaks if the canvas is lower than 60 % of the viewport (460.8 px), there is not exactly one header bar or its
    controls wrap, the tools are not a vertical rail left of the canvas, a TouchBar shows, the zoom control lies outside
    the canvas, the collapsed panel reserves width, the page scrolls sideways, or the selection's panel is not docked
    beside the canvas inside the viewport (AC-1, AC-3, AC-5, AC-14 part, GP-UX-069). The measured height is recorded as
    ``canvas_height_px``.
    """
    width, height = set_phone_viewport(browser, 1366, 768)
    plan.dismiss_light_mode_warning()
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc101",
        beds=(BedSpec("Beet A", rect(4.0, 4.5, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet A")
    plan.open(garden.site_key)

    plan.wait_for_element_visible(plan.TOOLBAR)
    assert plan.side_panel_state() is None, (
        f"TC-053-101: no selection, yet the panel is {plan.side_panel_state()}"
    )
    canvas = plan.rect_of(plan.CANVAS, "canvas")
    record_property(
        "canvas_height_px", f"{canvas['height']:.1f} of {height} ({canvas['height'] / height:.1%})"
    )
    assert canvas["height"] >= 0.6 * height, (
        f"TC-053-101 (AC-1): the canvas is {canvas['height']:.1f} px high, "
        f"{canvas['height'] / height:.1%} of the {width} x {height} viewport - at least 60 % ({0.6 * height:.1f} px)"
    )
    assert plan.header_bar_count() == 1, (
        f"TC-053-101 (AC-3): {plan.header_bar_count()} header bars on screen"
    )
    controls = plan.header_controls()
    assert plan.on_one_line(controls), f"TC-053-101 (AC-1): the header bar wraps: {controls}"

    assert plan.toolbar_orientation() == "vertical", (
        "TC-053-101 (AC-3): the tools should be a vertical rail"
    )
    rail, area = (
        plan.rect_of(plan.TOOLBAR, "tool rail"),
        plan.rect_of(plan.CANVAS_AREA, "canvas area"),
    )
    assert rail["right"] <= area["left"] + 1, (
        f"TC-053-101: the rail {rail} should stand left of the canvas {area}"
    )
    assert not plan.is_any_displayed(plan.TOUCHBAR), (
        "TC-053-101: a fine pointer at 1366 px shows no TouchBar"
    )
    zoom = plan.rect_of(plan.ZOOM_OVERLAY, "zoom overlay")
    inside = (
        zoom["left"] >= canvas["left"] - 1
        and zoom["right"] <= canvas["right"] + 1
        and zoom["top"] >= canvas["top"] - 1
        and zoom["bottom"] <= canvas["bottom"] + 1
    )
    assert inside, (
        f"TC-053-101 (AC-14): the zoom control {zoom} must lie inside the canvas {canvas}"
    )
    header = plan.rect_of(plan.HEADER_BAR, "header bar")
    assert header["right"] - area["right"] <= 2, (
        f"TC-053-101 (AC-5): the collapsed panel reserves width: canvas area ends at {area['right']:.0f}, "
        f"header bar at {header['right']:.0f}"
    )
    assert plan.horizontal_overflow_px() <= 0, (
        f"TC-053-101: the page scrolls sideways by {plan.horizontal_overflow_px()} px"
    )
    screenshot(
        "053_101_01_desktop_no_selection",
        "1366 × 768 ohne Auswahl: Zeichenfläche ≥ 60 %, eine Kopfleiste",
    )

    plan.select_with_keyboard(bed)
    plan.wait_for_side_panel(("docked", "properties"), "TC-053-101: the selection docks the panel")
    panel, area = (
        plan.rect_of(plan.SIDE_PANEL, "side panel"),
        plan.rect_of(plan.CANVAS_AREA, "canvas area"),
    )
    assert panel["left"] >= area["right"] - 1 and panel["right"] <= width + 0.5, (
        f"TC-053-101: the docked panel {panel} should stand right of the canvas area {area}, inside {width} px"
    )
    assert plan.horizontal_overflow_px() <= 0, (
        f"TC-053-101: with the docked panel the page scrolls sideways by {plan.horizontal_overflow_px()} px"
    )
    screenshot("053_101_02_desktop_docked_panel", "1366 × 768 mit Auswahl: Panel angedockt rechts")


# ── TC-053-102 ──────────────────────────────────────────────────────────────


def test_tc_053_102_tablet_820_panel_docks_beside_the_canvas(
    plan: WorkspacePlanPage, browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-102 - at 820 x 1180 (md, the theme's 768-1023 px) the rail stays left and the panel docks beside the canvas.

    Breaks if the rail is not vertical left of the canvas, the header bar wraps, the panel opens in another form than
    docked, the panel overlaps the canvas area or the zoom controls (WCAG 2.2 SC 2.4.11, #2885), a bed on the plan's
    right edge that the selection docks the panel beside is left outside the visible canvas, or the page scrolls
    sideways (GP-UX-069, GP-UX-068). The md layout only - the 1024 x 768 criterion is TC-053-103.
    """
    set_phone_viewport(browser, 820, 1180)
    plan.dismiss_light_mode_warning()
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc102",
        beds=(
            BedSpec("Beet A", rect(4.0, 4.5, 2.0, 1.0)),
            # On the right edge: the canvas that the docked panel narrows cuts it off unless the view pans.
            BedSpec("Beet B", rect(8.8, 4.5, 1.0, 1.0)),
        ),
    )
    plan.open(garden.site_key)

    assert plan.toolbar_orientation() == "vertical", (
        "TC-053-102: from md up the tools are a vertical rail"
    )
    rail, before = (
        plan.rect_of(plan.TOOLBAR, "tool rail"),
        plan.rect_of(plan.CANVAS_AREA, "canvas area"),
    )
    assert rail["right"] <= before["left"] + 1, (
        f"TC-053-102: the rail {rail} should stand left of {before}"
    )
    controls = plan.header_controls()
    assert plan.on_one_line(controls), f"TC-053-102: the header bar wraps at 820 px: {controls}"
    assert plan.side_panel_state() is None, (
        f"TC-053-102: the panel should start collapsed: {plan.side_panel_state()}"
    )
    # Read now, asserted at the end: the panel is checked even when the page scrolls sideways.
    overflow_collapsed = plan.horizontal_overflow_px()
    screenshot("053_102_01_tablet_collapsed", "820 × 1180: Werkzeuge links, Panel eingeklappt")

    plan.open_side_panel_by_switch()
    plan.wait_for_side_panel(
        ("docked", "view"), "TC-053-102: at md the panel docks beside the canvas"
    )
    panel, after, zoom = (
        plan.rect_of(plan.SIDE_PANEL, "side panel"),
        plan.rect_of(plan.CANVAS_AREA, "canvas area"),
        plan.rect_of(plan.ZOOM_OVERLAY, "zoom overlay"),
    )
    assert panel["left"] >= after["right"] - 1, (
        f"TC-053-102: the panel {panel} must stand right of the canvas area {after}, not over it (#2885)"
    )
    assert after["width"] < before["width"], (
        f"TC-053-102: the canvas should give the panel its width: {before['width']:.0f} -> {after['width']:.0f}"
    )
    assert (
        after["left"] <= zoom["left"] and zoom["right"] <= min(after["right"], panel["left"]) + 1
    ), (
        f"TC-053-102: the zoom controls {zoom} must lie inside the visible canvas area {after}, left of {panel}"
    )
    overflow_docked = plan.horizontal_overflow_px()
    screenshot("053_102_02_tablet_docked", "820 × 1180: Panel neben der Zeichenfläche, Zoom frei")

    # A selection opens the panel and the plan keeps its fit: the bed on the right edge must pan into view.
    plan.close_side_panel()
    bed_b = garden.bed_key("Beet B")
    plan.select_with_keyboard(bed_b)
    plan.wait_for_side_panel(
        ("docked", "properties"), "TC-053-102: the selection opens the panel on its properties"
    )
    area = plan.rect_of(plan.CANVAS_AREA, "canvas area")
    try:
        plan.poll().until(
            lambda _d: (
                (box := plan.rect_of(plan.object_locator(bed_b), "Beet B"))["left"]
                >= area["left"] - 1
                and box["right"] <= area["right"] + 1
            )
        )
    except TimeoutException as exc:
        raise AssertionError(
            f"TC-053-102: the selected bed {plan.rect_of(plan.object_locator(bed_b), 'Beet B')} should pan "
            f"into the visible canvas area {area} left of the docked panel (#2885)"
        ) from exc
    screenshot(
        "053_102_03_tablet_selection", "820 × 1180: ausgewähltes Beet am rechten Rand im Bild"
    )
    assert overflow_collapsed <= 0 and overflow_docked <= 0, (
        f"TC-053-102: the page scrolls sideways at 820 px - by {overflow_collapsed} px with the panel collapsed, "
        f"by {overflow_docked} px with the panel docked (header bar: {controls})"
    )


# ── TC-053-103 ──────────────────────────────────────────────────────────────

#: The top-level tools of GP-UX-001 since REQ-053 v1.19 (#2868: narrowed to the tools that exist) plus Bereich and
#: Messen from GP-UX-071 (#2913; Pflanze setzen and Text/Label are still to come), and the tools whose rail button
#: opens a sub-menu.
GP_UX_001_TOOLS = ("select", "pan", "area", "bed", "garden_object", "measure")
TOOLS_WITH_MENU = ("area", "bed", "garden_object")
PANEL_TABS = ("properties", "view", "layers", "zones")


def test_tc_053_103_every_editor_function_reachable_at_1024(
    plan: WorkspacePlanPage, browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-103 - at 1024 x 768 every editor function is reachable without horizontal scrolling (AC-2).

    Breaks if a top-level tool of GP-UX-001 is missing from the rail or lies outside the viewport, a tool sub-menu
    does not open or an entry of it lies outside the viewport, a panel tab cannot be chosen, an overflow entry lies
    outside the viewport or is lower than 48 px, or the page scrolls sideways at any of these steps (AC-2,
    GP-UX-001, GP-UX-069). 1024 px is the theme's lg: the panel docks beside the canvas.
    """
    width, height = set_phone_viewport(browser, 1024, 768)
    plan.dismiss_light_mode_warning()
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc103",
        beds=(BedSpec("Beet A", rect(4.0, 4.5, 2.0, 1.0)),),
    )
    plan.open(garden.site_key)
    plan.wait_for_element_visible(plan.TOOLBAR)
    overflow: dict[str, int] = {"start": plan.horizontal_overflow_px()}

    def inside(box: dict[str, float]) -> bool:
        return (
            box["left"] >= -1
            and box["right"] <= width + 1
            and box["top"] >= -1
            and box["bottom"] <= height + 1
        )

    for tool in GP_UX_001_TOOLS:
        button = plan.rect_of(plan.tool_locator(tool), f"tool {tool}")
        assert inside(button), (
            f"TC-053-103 (AC-2): the tool {tool!r} {button} lies outside the {width} x {height} viewport"
        )
    screenshot(
        "053_103_01_rail_1024", "1024 × 768: Werkzeug-Leiste mit allen Werkzeugen aus GP-UX-001"
    )

    for tool in TOOLS_WITH_MENU:
        entries = plan.menu_entry_rects(
            plan.tool_locator(f"{tool}-menu"),
            f"garden-plan-tool-{tool}-submenu",
            f"the sub-menu of {tool!r}",
        )
        outside = [entry for entry in entries if not (inside(entry) and entry["in_menu"])]
        assert not outside, (
            f"TC-053-103 (AC-2): entries of the {tool!r} sub-menu cannot be reached in the viewport: {outside}"
        )
        overflow[f"menu {tool}"] = plan.horizontal_overflow_px()

    plan.open_side_panel_by_switch()
    for tab in PANEL_TABS:
        plan.choose_side_panel_tab(tab)
        panel = plan.rect_of(plan.SIDE_PANEL, "side panel")
        assert panel["right"] <= width + 1, (
            f"TC-053-103 (AC-2): with the tab {tab!r} the panel {panel} reaches past the viewport"
        )
        overflow[f"tab {tab}"] = plan.horizontal_overflow_px()
    screenshot("053_103_02_panel_1024", "1024 × 768: Panel angedockt, alle Tabs erreichbar")

    entries = plan.menu_entry_rects(plan.OVERFLOW, "garden-plan-overflow-menu", "the overflow menu")
    # AC-2 asks for "erreichbar": an entry reached by scrolling inside the menu counts, a cut-off one does not
    # (the menu is bounded by the viewport and scrolls; at 768 px height its last entries are scrolled into it).
    outside = [entry for entry in entries if not (inside(entry) and entry["in_menu"])]
    assert not outside, (
        f"TC-053-103 (AC-2): overflow entries cannot be reached in the viewport: {outside}"
    )
    low = [entry for entry in entries if entry["height"] < 48 - 0.5]
    assert not low, f"TC-053-103 (AC-2): overflow entries lower than 48 px: {low}"
    overflow["overflow menu"] = plan.horizontal_overflow_px()

    scrolled = {step: px for step, px in overflow.items() if px > 0}
    assert not scrolled, f"TC-053-103 (AC-2): the page scrolls sideways at 1024 px: {scrolled}"


def test_tc_053_103_measure_tool_measures_a_known_distance(
    plan: WorkspacePlanPage, browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-103 step 5 - the rail's measure tool measures a known polyline and stores nothing (GP-UX-071).

    Breaks if the measure tool is not on the rail or does not become active, if a click does not set a snapped
    point, if a segment or the total is measured wrong or not shown as text (the status the screen reader hears
    and the overlay on the canvas), if Enter does not finish it, if Esc does not clear it, or if measuring leaves a
    change to save (it is transient: no plan operation).
    """
    set_phone_viewport(browser, 1024, 768)
    plan.dismiss_light_mode_warning()
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc103m",
        beds=(BedSpec("Beet A", rect(4.0, 4.5, 2.0, 1.0)),),
    )
    plan.open(garden.site_key)
    plan.wait_for_element_visible(plan.TOOLBAR)
    plan.choose_tool(plan.TOOL_MEASURE)

    # 3 m along x, then 2 m along y: 5 m in two segments, away from the bed and the boundary (no object snap).
    plan.click_plan_point(1.0, 1.0, "measure start")
    plan.wait_for_measure_status("Startpunkt gesetzt", "TC-053-103 measure: after the first click")
    plan.click_plan_point(4.0, 1.0, "measure second point")
    plan.click_plan_point(4.0, 3.0, "measure third point")
    status = plan.wait_for_measure_status("5,00 m", "TC-053-103 measure: two segments")
    assert "2 Abschnitte" in status, (
        f"TC-053-103 measure: the status should count 2 segments: {status!r}"
    )
    segments, total = plan.measure_texts()
    assert segments == ["3,00 m", "2,00 m"], (
        f"TC-053-103 measure: segment lengths on the canvas: {segments}"
    )
    assert total == "Gesamt 5,00 m", f"TC-053-103 measure: total on the canvas: {total!r}"

    plan.focus_canvas()
    plan.press(Keys.ENTER)
    plan.wait_for_measure_status("Messung fertig: 5,00 m", "TC-053-103 measure: Enter finishes")
    screenshot("053_103_03_measure", "1024 × 768: Messen, 3 m + 2 m = 5 m")
    assert plan.pending_count() == 0, "TC-053-103 measure: measuring must leave nothing to save"

    plan.press(Keys.ESCAPE)
    plan.poll().until(lambda d: not d.find_elements(*plan.MEASURE_TOTAL))
    plan.wait_for_measure_status("Klicke auf den Startpunkt", "TC-053-103 measure: Esc clears")


def test_tc_053_103_area_parents_a_bed_drawn_inside_it(
    plan: WorkspacePlanPage, browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-103 step 6 - the rail's area tool draws an area that parents the bed drawn inside it (GP-UX-071).

    Breaks if the area tool is not on the rail or does not become active, if its type choice with the parent rule is
    missing, if the drawn rectangle is not stored as a location of the chosen area type that the read model marks
    ``is_area``, if a bed drawn inside it afterwards does not get the area as ``parent_location_key``, or if the bed
    that was on the plan before (outside the area) changes its parent.
    """
    set_phone_viewport(browser, 1024, 768)
    plan.dismiss_light_mode_warning()
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc103a",
        beds=(BedSpec("Beet A", rect(4.0, 4.5, 2.0, 1.0)),),
    )
    plan.open(garden.site_key)
    plan.wait_for_element_visible(plan.TOOLBAR)
    before = {
        loc["key"]: loc for loc in read_plan(base_url, e2e_seed_data, garden.site_key)["locations"]
    }

    plan.choose_tool(plan.TOOL_AREA)
    plan.choose_new_area_type("garden")
    helper = plan.new_area_type_rule()
    assert "danach ganz in diesem Bereich" in helper, (
        f"TC-053-103 area: the type choice should name the parent rule, it reads {helper!r}"
    )
    plan.draw_rect((0.5, 0.5), (3.5, 3.5))
    plan.wait_for_pending(1, "TC-053-103 area: drawing the area")
    area_key = plan.selected_keys()
    assert len(area_key) == 1, f"TC-053-103 area: the new area should be selected, got {area_key}"
    (area_temp,) = area_key

    plan.choose_tool(plan.TOOL_BED)
    plan.draw_rect((1.0, 1.0), (2.0, 2.0), start_on=area_temp)
    plan.wait_for_pending(2, "TC-053-103 area: drawing the bed inside the area")
    screenshot("053_103_04_area", "1024 × 768: Bereich mit einem Beet darin")
    plan.save_with_button()

    stored = read_plan(base_url, e2e_seed_data, garden.site_key)
    new = [loc for loc in stored["locations"] if loc["key"] not in before]
    areas = [loc for loc in new if loc.get("is_area") is True]
    beds = [loc for loc in new if loc.get("is_area") is not True]
    assert len(areas) == 1 and len(beds) == 1, (
        f"TC-053-103 area: expected one new area and one new bed: {new}"
    )
    assert areas[0]["location_type_key"] == "garden", f"TC-053-103 area: area type {areas[0]}"
    assert "garden" in stored.get("area_type_keys", []), (
        "TC-053-103 area: the read model names the area types"
    )
    assert beds[0].get("parent_location_key") == areas[0]["key"], (
        f"TC-053-103 area: the bed drawn inside the area should hang below it: {beds[0]} / {areas[0]}"
    )
    old_bed = garden.bed_key("Beet A")
    after = {loc["key"]: loc for loc in stored["locations"]}
    assert after[old_bed].get("parent_location_key") == before[old_bed].get(
        "parent_location_key"
    ), "TC-053-103 area: the bed that was there before keeps its parent"


# ── TC-053-104 ──────────────────────────────────────────────────────────────


def test_tc_053_104_phone_390_touchbar_bars_below_overflow_and_bottom_sheet(
    plan: WorkspacePlanPage, browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-104 - at 390 x 844 (planning mode) TouchBar and tool bar sit below the canvas, the panel is a sheet.

    Breaks if the TouchBar or the horizontal tool bar is missing or not below the canvas, undo/redo are not in the
    TouchBar, the header bar wraps or still shows the tabs or the panel switch inline, an overflow entry for them is
    missing, lower than 48 px or without text, a bar button is smaller than 48 x 48 px, the selection does not open a
    bottom sheet above the bars, or the page scrolls sideways (AC-9, AC-15 part, GP-UX-063/069). #2904: also breaks if
    the overflow's tooltip stays on screen after its menu closed or covers the sheet's close button, the selection
    group wraps or a selection action (delete above all) lies outside the viewport, or the rotation step - moved into
    the overflow below md - is missing there.
    """
    set_phone_viewport(browser, 390, 844)
    plan.dismiss_light_mode_warning()
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc104",
        beds=(BedSpec("Beet A", rect(4.0, 4.5, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet A")
    plan.open_in_planning_mode(garden.site_key)

    plan.wait_for_element_visible(plan.TOUCHBAR)
    assert plan.toolbar_orientation() == "horizontal", (
        "TC-053-104: below md the tool bar is horizontal"
    )
    area = plan.rect_of(plan.CANVAS_AREA, "canvas area")
    for locator, name in ((plan.TOUCHBAR, "TouchBar"), (plan.TOOLBAR, "tool bar")):
        bar = plan.rect_of(locator, name)
        assert bar["top"] >= area["bottom"] - 1, (
            f"TC-053-104: the {name} {bar} should sit below the canvas {area}"
        )
    assert plan.touchbar_holds("garden-plan-undo") and plan.touchbar_holds("garden-plan-redo"), (
        "TC-053-104: undo and redo belong in the TouchBar below md"
    )
    controls = plan.header_controls()
    assert plan.on_one_line(controls), f"TC-053-104: the header bar wraps at 390 px: {controls}"
    assert not plan.is_any_displayed(plan.TABS) and not plan.is_any_displayed(plan.PANEL_TOGGLE), (
        "TC-053-104 (AC-15): below md the tabs and the panel switch belong in the overflow, not the header bar"
    )
    sizes = plan.button_sizes(plan.TOUCHBAR) + plan.button_sizes(plan.TOOLBAR)
    small = [(name, round(w, 1), round(h, 1)) for name, w, h in sizes if min(w, h) < MIN_TARGET_PX]
    assert not small, f"TC-053-104 (AC-9): touch targets below 48 x 48 px: {small}"
    assert plan.horizontal_overflow_px() <= 0, (
        f"TC-053-104: the page scrolls sideways by {plan.horizontal_overflow_px()} px"
    )
    screenshot(
        "053_104_01_phone_bars", "390 × 844: TouchBar und Werkzeug-Leiste unten, Kopfleiste kompakt"
    )

    entries = plan.inspect_overflow(
        (
            "garden-plan-menu-tab-plan",
            "garden-plan-menu-tab-list",
            "garden-plan-menu-tab-beds",
            "garden-plan-menu-panel",
        ),
        then_choose="garden-plan-menu-tab-list",
        during=lambda: screenshot(
            "053_104_02_phone_overflow", "390 × 844: Überlauf mit Tabs und Panel-Umschalter"
        ),
    )
    short = {
        entry: found for entry, found in entries.items() if found[0] < MIN_TARGET_PX or not found[1]
    }
    assert not short, (
        f"TC-053-104 (AC-15): overflow entries lower than 48 px or without text: {short}"
    )
    plan.wait_for_tab("list", "TC-053-104: the overflow entry 'Liste' opens the list")
    plan.wait_for_no_tooltip("TC-053-104 (#2904): after the overflow menu closed")
    plan.wait_for_tab_content("list", "TC-053-104: the list tab on the phone")
    plan.open_tab("plan")
    plan.wait_for_tab_content("plan", "TC-053-104: back to the plan through the overflow")

    plan.select_with_keyboard(bed)
    plan.wait_for_side_panel(
        ("sheet", "properties"), "TC-053-104: below md the selection opens a bottom sheet"
    )
    sheet, bars = (
        plan.rect_of(plan.SIDE_PANEL, "bottom sheet"),
        plan.rect_of(plan.TOUCHBAR, "TouchBar"),
    )
    assert sheet["bottom"] <= bars["top"] + 1, (
        f"TC-053-104: the sheet {sheet} should lie above the bars {bars}"
    )
    assert plan.horizontal_overflow_px() <= 0, (
        f"TC-053-104: with the sheet the page scrolls sideways by {plan.horizontal_overflow_px()} px"
    )

    # #2904: every selection action fully inside the viewport, in one row - without scrolling the page to it.
    width, height = plan.viewport_size()
    actions = plan.button_rects(plan.SELECTION_GROUP)
    names = [name for name, _ in actions]
    assert "garden-plan-delete-button" in names and "garden-plan-align-button" in names, (
        f"TC-053-104 (#2904): the selection group should hold align and delete: {names}"
    )
    outside = [
        (name, box)
        for name, box in actions
        if box["left"] < -1
        or box["right"] > width + 1
        or box["top"] < -1
        or box["bottom"] > height + 1
    ]
    assert not outside, (
        f"TC-053-104 (#2904): selection actions outside the {width} x {height} viewport: {outside}"
    )
    delete = plan.rect_of(plan.DELETE_BUTTON, "the delete button")
    assert delete["top"] >= 0 and delete["bottom"] <= height + 1, (
        f"TC-053-104 (#2904): 'Löschen' {delete} is cut off by the bottom edge ({height} px)"
    )
    rows = [(name, box["top"], box["bottom"]) for name, box in actions]
    assert plan.on_one_line(rows), f"TC-053-104 (#2904): the selection group wraps: {rows}"
    screenshot(
        "053_104_03_phone_sheet", "390 × 844: Auswahl öffnet das Bottom Sheet über den Leisten"
    )

    # The rotation step is in the overflow below md (never dropped); choosing it leaves no tooltip over the sheet.
    steps = plan.inspect_overflow(
        ("garden-plan-angle-15", "garden-plan-angle-45", "garden-plan-angle-90"),
        then_choose="garden-plan-angle-45",
    )
    short = {
        entry: found for entry, found in steps.items() if found[0] < MIN_TARGET_PX or not found[1]
    }
    assert not short, (
        f"TC-053-104 (#2904): rotation step entries lower than 48 px or without text: {short}"
    )
    plan.wait_for_no_tooltip("TC-053-104 (#2904): after choosing the rotation step")
    assert plan.is_uncovered(plan.SIDE_PANEL_CLOSE, "the sheet's close button"), (
        "TC-053-104 (#2904): something lies over the bottom sheet's close button after the overflow closed"
    )


# ── TC-053-105 ──────────────────────────────────────────────────────────────


def test_tc_053_105_window_and_lamp_properties_saved_off_site_switch_and_legend(
    plan: WorkspacePlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-105 - window and lamp properties are edited in the panel and stored; "off site" on and refused off.

    Breaks if the window's derived direction is not "Süd, 180°", an edit is not exactly one unsaved change, the saved
    props differ from what was entered, the lamp's ``off_site`` is not stored, switching off the box that sticks out of
    the outline is not refused (or becomes a change), or the object legend misses a class on the plan (GP-FR-180, §9.5).
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc105",
        site_type="indoor",
        boundary=FLAT,
        objects=(
            ObjectSpec("Südfenster", "window", SOUTH_WINDOW),
            ObjectSpec(
                "Deckenleuchte",
                "lamp",
                rect(4.0, 1.5, 0.6, 0.6),
                props={"kind": "ceiling", "height_m": 2.5},
            ),
            # Sticks out of the flat at the top right corner: allowed only as scenery outside the outline.
            ObjectSpec("Balkonkasten", "furniture", rect(5.5, 3.6, 1.0, 0.6), off_site=True),
        ),
    )
    window, lamp, box = (garden.objects[n] for n in ("Südfenster", "Deckenleuchte", "Balkonkasten"))
    plan.open(garden.site_key)

    plan.select_with_keyboard(window)
    plan.wait_for_object_props("window", "TC-053-105: the window's properties")
    available, text = plan.window_orientation()
    assert available == "true" and "Süd, 180°" in text, (
        f"TC-053-105: the window should show the derived direction 'Süd, 180°': {available!r}, {text!r}"
    )
    plan.commit_prop_number(plan.WINDOW_SILL, "0,9")
    plan.choose_prop_select(plan.WINDOW_GLAZING, "double")
    screenshot(
        "053_105_01_window_props", "Fenster: Brüstungshöhe 0,9 m, Doppelverglasung, Richtung Süd"
    )

    plan.select_with_keyboard(lamp)
    plan.wait_for_object_props("lamp", "TC-053-105: the lamp's properties")
    plan.choose_prop_select(plan.LAMP_KIND, "grow_light")
    plan.commit_prop_number(plan.LAMP_HEIGHT, "1,8")
    plan.commit_prop_number(plan.LAMP_PPFD, "400")
    assert not plan.off_site_checked(), (
        "TC-053-105: the lamp starts inside the outline (off site off)"
    )
    pending = plan.pending_count()
    plan.press_off_site_switch()
    plan.wait_for_pending(pending + 1, "TC-053-105: switching 'off site' on is one unsaved change")
    assert plan.off_site_checked(), "TC-053-105: the lamp's 'off site' switch should be on now"
    screenshot("053_105_02_lamp_props", "Lampe: Pflanzenlampe, 1,8 m, 400 µmol/m²/s, außerhalb an")

    plan.save_with_button()
    stored = read_plan(base_url, e2e_seed_data, garden.site_key)
    window_props = stored_object(stored, window)["props"]
    assert (window_props.get("sill_height_m"), window_props.get("glazing")) == (0.9, "double"), (
        f"TC-053-105: the stored window props should carry 0.9 m and double glazing: {window_props}"
    )
    stored_lamp = stored_object(stored, lamp)
    lamp_props = stored_lamp["props"]
    assert (lamp_props.get("kind"), lamp_props.get("height_m"), lamp_props.get("ppfd_ref")) == (
        "grow_light",
        1.8,
        400.0,
    ), f"TC-053-105: the stored lamp props should be grow_light / 1.8 m / 400: {lamp_props}"
    assert stored_lamp.get("off_site") is True, (
        f"TC-053-105: the lamp should be stored off site: {stored_lamp}"
    )

    plan.select_with_keyboard(box)
    plan.wait_for_object_props("furniture", "TC-053-105: the box's properties")
    assert plan.off_site_checked(), "TC-053-105: the box was arranged off site"
    plan.press_off_site_switch()
    plan.wait_for_element_visible(plan.OFF_SITE_ERROR)
    refusal = plan.text_of(plan.OFF_SITE_ERROR)
    assert "ragt" in refusal, f"TC-053-105: the refusal should say the box sticks out: {refusal!r}"
    assert plan.off_site_checked(), "TC-053-105: the refused switch must stay on"
    assert plan.pending_count() == 0, "TC-053-105: a refused switch is no unsaved change"
    screenshot(
        "053_105_03_off_site_refused", "Balkonkasten: Ausschalten abgelehnt, ragt über die Grenze"
    )

    legend = plan.object_legend_types()
    assert {"window", "lamp", "furniture"} <= legend and "door" not in legend, (
        f"TC-053-105: the object legend should list window, lamp and furniture (and no door): {sorted(legend)}"
    )
    assert (
        stored_object(read_plan(base_url, e2e_seed_data, garden.site_key), box).get("off_site")
        is True
    ), "TC-053-105: the refused switch must leave the stored box off site"
    screenshot("053_105_04_object_legend", "Tab „Ebenen“: Objekt-Legende mit Fenster, Lampe, Möbel")


# ── TC-053-106 ──────────────────────────────────────────────────────────────


def test_tc_053_106_indoor_empty_state_draw_the_flat_and_a_window(
    plan: WorkspacePlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-106 - the indoor empty state, "Grundriss zeichnen", a window drawn as a line and stored.

    Breaks if the indoor empty state is not marked ``data-plan-kind="indoor"`` (the garden one being the counter-check),
    misses its text or actions or offers "Erstes Beet anlegen", the drawing does not open the editor with the tab
    "Pflanzplätze", the drawn window is not one unsaved change with the derived direction "Süd, 180°" by convention,
    or the stored plan does not hold exactly that window line (GP-FR-182, GP-UX-049, GP-FR-180).
    """
    garden_key, _ = create_site(
        base_url, e2e_seed_data, purpose="tc106-garden", site_type="outdoor"
    )
    indoor_key, _ = create_site(base_url, e2e_seed_data, purpose="tc106-indoor", site_type="indoor")

    plan.open_empty_plan(garden_key)
    assert plan.empty_plan_kind() == "garden", (
        "TC-053-106: an outdoor site shows the garden empty state"
    )
    plan.wait_for_element_visible(plan.EMPTY_ADD_BED)
    assert not plan.is_present(plan.EMPTY_DRAW), (
        "TC-053-106: the garden empty state offers no 'Grundriss zeichnen'"
    )
    screenshot("053_106_01_garden_empty", "Garten ohne Plan: „Erstes Beet anlegen“")

    plan.open_empty_plan(indoor_key)
    assert plan.empty_plan_kind() == "indoor", (
        "TC-053-106: an indoor site shows the indoor empty state"
    )
    plan.wait_for_element_visible(plan.EMPTY_DRAW)
    plan.wait_for_element_visible(plan.EMPTY_UNDERLAY)
    text = plan.text_of(plan.EMPTY)
    assert "Zeichne die Umrisse deiner Wohnung oder lade ein Foto als Vorlage" in text, (
        f"TC-053-106: the indoor empty state should explain the flat: {text!r}"
    )
    assert not plan.is_present(plan.EMPTY_ADD_BED), (
        "TC-053-106: the indoor empty state offers no 'Erstes Beet'"
    )
    screenshot(
        "053_106_02_indoor_empty", "Wohnung ohne Plan: Grundriss zeichnen oder Foto als Vorlage"
    )

    plan.start_drawing_from_empty_state()
    assert plan.tab_label("beds") == "Pflanzplätze", (
        f"TC-053-106: the indoor bed tab should read 'Pflanzplätze': {plan.tab_label('beds')!r}"
    )
    plan.choose_tool(plan.TOOL_OBJECT)
    plan.choose_new_object_type("window")
    plan.choose_draw_shape("polyline")
    # Right to left: with no outline the outside is left of the drawing direction - south.
    plan.click_plan_point(6.0, 5.0, "TC-053-106: first point of the window")
    plan.click_plan_point(3.0, 5.0, "TC-053-106: second point of the window")
    plan.finish_drawing()
    drawn = plan.selected_keys()
    assert len(drawn) == 1, f"TC-053-106: the drawn window should be the one selection: {drawn}"
    plan.wait_for_object_props("window", "TC-053-106: the drawn window's properties")
    available, text = plan.window_orientation()
    assert available == "true" and "Süd, 180°" in text, (
        f"TC-053-106: the drawn window should face 'Süd, 180°': {available!r}, {text!r}"
    )
    plan.wait_for_element_visible(plan.WINDOW_CONVENTION)
    screenshot(
        "053_106_03_window_drawn",
        "Fenster als Linie gezeichnet: Süd, Außenseite aus der Zeichenrichtung",
    )

    plan.save_with_button()
    objects = read_plan(base_url, e2e_seed_data, indoor_key).get("garden_objects") or []
    assert [o.get("object_type") for o in objects] == ["window"], (
        f"TC-053-106: the stored plan should hold exactly the drawn window: {objects}"
    )
    geometry = objects[0].get("geometry") or {}
    points = [tuple(float(c) for c in point) for point in geometry.get("points") or []]
    expected = [(6.0, 5.0), (3.0, 5.0)]
    close = len(points) == 2 and all(
        abs(p[0] - e[0]) <= 0.03 and abs(p[1] - e[1]) <= 0.03
        for p, e in zip(points, expected, strict=True)
    )
    assert geometry.get("kind") == "polyline" and close, (
        f"TC-053-106: the window should be stored as the line {expected}: {geometry}"
    )


# ── TC-053-107 ──────────────────────────────────────────────────────────────


def test_tc_053_107_window_suggestion_cancel_changes_nothing_confirm_only_the_sun_window(
    plan: WorkspacePlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-107 - "Aus Fenster vorschlagen": preview, cancel writes nothing, confirm writes only ``sun_window``.

    Breaks if the preview does not suggest "Mittags" from the south window (or lists another window or direction),
    misses the northern-hemisphere caveat of a site without GPS, a cancel leaves a pending change or a stored change,
    a confirm is saved without the user's save (it must be one pending change), or the save changes anything of the
    tent's sun facts but the sun window (GP-FR-181, G-W10 c "nie automatisch überschreiben").
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc107",
        site_type="indoor",
        boundary=FLAT,
        beds=(BedSpec("Zelt A", rect(1.0, 0.4, 1.2, 1.2), location_type_key="tent"),),
        objects=(ObjectSpec("Südfenster", "window", SOUTH_WINDOW),),
    )
    tent, window = garden.bed_key("Zelt A"), garden.objects["Südfenster"]
    patch_location(
        base_url,
        e2e_seed_data,
        tent,
        {
            "sun_exposure": "partial_shade",
            "site_conditions": {
                "sun_profile": {"direct_sun_hours_summer": 4.0, "foliage_shade_in_summer": False}
            },
        },
    )
    exposure, profile, others = _sun_facts(tenant_location(base_url, e2e_seed_data, tent))
    assert (exposure, profile.get("sun_window"), profile.get("direct_sun_hours_summer")) == (
        "partial_shade",
        "unknown",
        4.0,
    ), (
        f"TC-053-107: precondition - the tent should be partial shade, 4 h, no sun window: {exposure}, {profile}"
    )

    plan.open(garden.site_key)
    plan.select_with_keyboard(tent)
    plan.open_window_suggestion()
    assert plan.suggested_sun_window() == "midday", (
        f"TC-053-107: a south window suggests 'midday', the preview says {plan.suggested_sun_window()!r}"
    )
    shown = plan.suggestion_text()
    assert "Vorschlag: Mittags" in shown and "Eingetragen ist: Unbekannt" in shown, (
        f"TC-053-107: the preview should name the suggestion and the stored value: {shown!r}"
    )
    assert plan.suggested_windows() == {window: "south"}, (
        f"TC-053-107: the preview should list exactly the south window: {plan.suggested_windows()}"
    )
    assert "hemisphere_assumed" in plan.suggestion_hints(), (
        f"TC-053-107: a site without GPS must say the northern hemisphere is assumed: {plan.suggestion_hints()}"
    )
    screenshot(
        "053_107_01_preview", "Vorschau: Vorschlag Mittags, Südfenster, Hinweis Nordhalbkugel"
    )

    plan.cancel_window_suggestion()
    assert plan.pending_count() == 0, (
        "TC-053-107: cancelling the suggestion must leave no unsaved change"
    )
    assert _sun_facts(tenant_location(base_url, e2e_seed_data, tent)) == (
        exposure,
        profile,
        others,
    ), "TC-053-107: cancelling the suggestion must not change the stored tent"

    plan.open_window_suggestion()
    plan.apply_window_suggestion()
    assert plan.save_status_text() == DIRTY_ONE, (
        f"TC-053-107: the confirmed suggestion is an unsaved change until saved: {plan.save_status_text()!r}"
    )
    screenshot("053_107_02_applied_unsaved", "Übernommen: eine ungespeicherte Änderung")
    plan.save_with_button()

    after_exposure, after_profile, after_others = _sun_facts(
        tenant_location(base_url, e2e_seed_data, tent)
    )
    expected_profile = {**profile, "sun_window": "midday", "source": "manual"}
    assert (after_exposure, after_profile, after_others) == (exposure, expected_profile, others), (
        f"TC-053-107: only the sun window may change - before {exposure}, {profile}, {others}; "
        f"after {after_exposure}, {after_profile}, {after_others}"
    )


# ── TC-053-108 ──────────────────────────────────────────────────────────────


def test_tc_053_108_indoor_planting_spots_tab_and_list_without_frost_layer(
    plan: WorkspacePlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-108 - the indoor tab and list "Pflanzplätze" hold tent and shelf, not the room; no frost layer.

    Breaks if the indoor tab is not named "Pflanzplätze" (or its URL value is not ``beds``), the list's heading
    differs, the list misses the tent or the shelf or shows the room, the indoor layers offer frost (or lose the sun
    layer), or the garden counter-check loses "Beete" or its frost layer (GP-FR-183, GP-FR-182, AC-13 part).
    """
    indoor = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc108-indoor",
        site_type="indoor",
        boundary=FLAT,
        beds=(
            BedSpec("Zelt A", rect(0.5, 0.5, 1.2, 1.2), location_type_key="tent"),
            BedSpec("Regal B", rect(2.5, 0.5, 1.2, 0.4), location_type_key="shelf"),
            BedSpec("Wohnzimmer", rect(3.5, 1.5, 2.0, 2.0), location_type_key="room"),
        ),
    )
    tent, shelf = indoor.bed_key("Zelt A"), indoor.bed_key("Regal B")
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc108-garden",
        beds=(BedSpec("Hochbeet 1", rect(4.0, 4.5, 2.0, 1.0)),),
    )

    plan.open(indoor.site_key)
    assert plan.tab_label("beds") == "Pflanzplätze", (
        f"TC-053-108: the indoor bed tab should read 'Pflanzplätze': {plan.tab_label('beds')!r}"
    )
    plan.open_tab("beds")
    plan.wait_for_tab("beds", "TC-053-108: the tab 'Pflanzplätze'")
    assert plan.url_tab_param() == "beds", (
        f"TC-053-108: the URL value stays 'beds': {plan.driver.current_url}"
    )
    plan.wait_for_bed_list_keys(
        {tent, shelf}, "TC-053-108: the planting spots are the tent and the shelf"
    )
    assert plan.bed_list_heading() == "Pflanzplätze", (
        f"TC-053-108: the list should be titled 'Pflanzplätze': {plan.bed_list_heading()!r}"
    )
    screenshot(
        "053_108_01_planting_spots", "Indoor: Tab und Liste „Pflanzplätze“ mit Zelt und Regal"
    )

    plan.open_tab("plan")
    plan.wait_for_tab_content("plan", "TC-053-108: back on the plan")
    plan.open_side_panel_tab("layers")
    indoor_layers = set(plan.layer_toggle_texts())
    assert (
        "garden-plan-layer-sun" in indoor_layers and "garden-plan-layer-frost" not in indoor_layers
    ), f"TC-053-108: indoor offers the sun layer but no frost layer: {sorted(indoor_layers)}"
    screenshot("053_108_02_indoor_layers", "Indoor: Tab „Ebenen“ ohne Frost")

    plan.open(garden.site_key)
    assert plan.tab_label("beds") == "Beete", (
        f"TC-053-108: the garden keeps the tab 'Beete': {plan.tab_label('beds')!r}"
    )
    plan.open_side_panel_tab("layers")
    garden_layers = set(plan.layer_toggle_texts())
    assert "garden-plan-layer-frost" in garden_layers, (
        f"TC-053-108: the garden counter-check should offer the frost layer: {sorted(garden_layers)}"
    )
    screenshot("053_108_03_garden_layers", "Garten zum Vergleich: Tab „Beete“, Ebene „Frost“")
