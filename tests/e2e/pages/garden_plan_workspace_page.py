"""Page object for the plan editor's workspace of wave 10 (REQ-053 §17.3, §9.8; WP 10.2-10.8, E2E WP 10.13).

The workspace parts the wave-10 cases drive on top of :class:`GardenPlanPage`: the route tabs with their URL state
(``?tab=``), the side panel's state rule (GP-UX-068), the layout of the three widths (GP-UX-069), the object
properties of windows and lamps (GP-FR-180), the window suggestion (GP-FR-181) and the indoor plan (GP-FR-182/183).

Every hook is a ``data-testid`` registered in UI-NFR-022 §2.5.1 (v1.9-v1.16) - none is guessed, none is renamed
(G-W10 a). Activation follows `e2e-test-stability` §C: keyboard wherever the control offers it (a tab, a table row, a
switch, the selected object's Escape), a dispatched ``mousedown`` pair for a MUI ``Select`` (it opens on mousedown
only in MUI 9), a coordinate-free click on ``click``-activated buttons, and trusted pointer input only for the one
spatial gesture - setting the points of a line on the canvas, guarded by ``elementFromPoint``.

Every state-changing helper reads its effect back (``aria-selected``, the URL, ``aria-expanded``, the pending-change
count of the save bar, the dialog leaving the DOM) and fails loudly when it never arrives (`test-falsifiability` T4).
Readers fail loudly on a missing structure instead of answering an empty default (T3).
"""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import parse_qs, urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.mouse_button import MouseButton
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from .base_page import DEFAULT_TIMEOUT
from .bed_care_page import choose_from_native_select, native_select_values
from .field_mode_page import FieldModePage
from .garden_plan_page import GardenPlanPage, ScreenPoint


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


#: The bounding rect of the first *displayed* match of a CSS selector, or ``null`` when none is displayed.
_DISPLAYED_RECT = """
var nodes = document.querySelectorAll(arguments[0]);
for (var i = 0; i < nodes.length; i++) {
  var r = nodes[i].getBoundingClientRect();
  var style = window.getComputedStyle(nodes[i]);
  if (r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none') {
    return {left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height};
  }
}
return null;
"""

#: Every displayed control of the header bar with its vertical extent: ``[label, top, bottom]``.
_HEADER_CONTROLS = """
var bar = arguments[0];
var out = [];
bar.querySelectorAll('button, a, [role="tab"], [role="status"], input:not([type="hidden"])').forEach(function (el) {
  var r = el.getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) { return; }
  if (window.getComputedStyle(el).visibility === 'hidden') { return; }
  var name = el.getAttribute('data-testid') || el.getAttribute('aria-label') || el.textContent.trim().slice(0, 30);
  out.push([name, r.top, r.bottom]);
});
return out;
"""

#: Every displayed button of a container with its size: ``[label, width, height]``.
_BUTTON_SIZES = """
var root = arguments[0];
var out = [];
root.querySelectorAll('button, [role="button"]').forEach(function (el) {
  var r = el.getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) { return; }
  var name = el.getAttribute('data-testid') || el.getAttribute('aria-label') || el.textContent.trim().slice(0, 30);
  out.push([name, r.width, r.height]);
});
return out;
"""

#: Every displayed button of a container with its box: ``[label, left, top, right, bottom]``.
_BUTTON_RECTS = """
var root = arguments[0];
var out = [];
root.querySelectorAll('button, [role="button"]').forEach(function (el) {
  var r = el.getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) { return; }
  var name = el.getAttribute('data-testid') || el.getAttribute('aria-label') || el.textContent.trim().slice(0, 30);
  out.push([name, r.left, r.top, r.right, r.bottom]);
});
return out;
"""

#: Whether the centre of the first displayed match is the element itself (or inside it): nothing lies over it.
_UNCOVERED = """
var nodes = document.querySelectorAll(arguments[0]);
for (var i = 0; i < nodes.length; i++) {
  var r = nodes[i].getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) { continue; }
  var hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
  return !!hit && nodes[i].contains(hit);
}
return null;
"""

#: The WAI-ARIA "Tabs" wiring of the side panel's tab list (GP-UX-068): per tab its state and its tab panel's link.
_PANEL_TAB_WIRING = """
var list = arguments[0];
return Array.from(list.querySelectorAll('[role="tab"]')).map(function (tab) {
  var panelId = tab.getAttribute('aria-controls');
  var panel = panelId ? document.getElementById(panelId) : null;
  return {
    testid: tab.getAttribute('data-testid'),
    id: tab.id,
    selected: tab.getAttribute('aria-selected'),
    tabindex: tab.getAttribute('tabindex'),
    controls: panelId,
    panelRole: panel ? panel.getAttribute('role') : null,
    panelLabelledBy: panel ? panel.getAttribute('aria-labelledby') : null
  };
});
"""


class WorkspacePlanPage(GardenPlanPage):
    """The garden or indoor plan as the wave-10 workspace shows it."""

    TAB_PREFIX = "garden-plan-tab-"
    PLAN_TABS = ("plan", "list", "beds")

    TOOLBAR = _tid("garden-plan-toolbar")
    TOUCHBAR = _tid("garden-plan-touchbar")
    CANVAS_AREA = _tid("garden-plan-canvas-area")
    ZOOM_OVERLAY = _tid("garden-plan-zoom-overlay")
    SELECTION_GROUP = _tid("garden-plan-selection-group")
    DELETE_BUTTON = _tid("garden-plan-delete-button")
    TOOLTIP = (By.CSS_SELECTOR, "[role='tooltip']")
    SIDE_PANEL_TABLIST = _tid("garden-plan-side-panel-tabs")
    SIDE_PANEL_CLOSE = _tid("garden-plan-panel-close")
    LAYER_TOGGLES = _tid("garden-plan-layer-toggles")
    LAYER_LEGEND = _tid("garden-plan-layer-legend")

    # ── Bed list in the tab "Beete" / "Pflanzplätze" (GP-FR-042, GP-FR-183) ──
    BED_LIST_SECTION = _tid("bed-list-section")
    BED_LIST_HEADING = (By.CSS_SELECTOR, "[data-testid='bed-list-section'] #bed-list-heading")
    BED_LIST_LINKS = (
        By.CSS_SELECTOR,
        "[data-testid='bed-list-section'] [data-testid^='bed-list-link-']",
    )

    # ── Drawing a garden object (GP-FR-180) ────────────────────────────
    TOOL_OBJECT = _tid("garden-plan-tool-garden_object")
    NEW_OBJECT_TYPE = "garden-plan-new-object-type"
    DRAW_FINISH = _tid("garden-plan-draw-finish")

    # ── Area tool (GP-UX-071, #2913) ───────────────────────────────────
    TOOL_AREA = _tid("garden-plan-tool-area")
    NEW_AREA_TYPE = "garden-plan-new-area-type"
    NEW_AREA_TYPE_RULE = _tid("garden-plan-new-area-type-rule")

    # ── Plant tool "Pflanze setzen" (GP-UX-071, #2913) ─────────────────
    TOOL_PLANT = _tid("garden-plan-tool-plant")
    PLANT_STATUS = _tid("garden-plan-plant-status")
    PLANT_DIALOG = _tid("garden-plan-plant-dialog")
    PLANT_DIALOG_TITLE = (By.CSS_SELECTOR, "[data-testid='garden-plan-plant-dialog'] h2")
    PLANT_DIALOG_SPECIES = (
        By.CSS_SELECTOR,
        "[data-testid='garden-plan-plant-dialog-species'] input",
    )
    PLANT_DIALOG_SUBMIT = _tid("garden-plan-plant-dialog-submit")
    PLANT_OPTIONS = (By.CSS_SELECTOR, "li[role='option']")

    # ── Measure tool (GP-UX-071, #2913) ────────────────────────────────
    TOOL_MEASURE = _tid("garden-plan-tool-measure")
    MEASURE_STATUS = _tid("garden-plan-measure-status")
    MEASURE_TOTAL = _tid("garden-plan-measure-total")
    MEASURE_SEGMENTS = _tid("garden-plan-measure-segment")

    # ── Object properties (WP 10.6) ────────────────────────────────────
    OBJECT_PROPS = _tid("garden-plan-panel-object-props")
    WINDOW_SILL = _tid("garden-plan-panel-window-sill-height")
    WINDOW_GLAZING = "garden-plan-panel-window-glazing"
    WINDOW_ORIENTATION = _tid("garden-plan-panel-window-orientation")
    WINDOW_CONVENTION = _tid("garden-plan-panel-window-orientation-convention")
    LAMP_KIND = "garden-plan-panel-lamp-kind"
    LAMP_HEIGHT = _tid("garden-plan-panel-lamp-height")
    LAMP_PPFD = _tid("garden-plan-panel-lamp-ppfd")
    OFF_SITE_SWITCH = _tid("garden-plan-panel-off-site-switch")
    OFF_SITE_ERROR = _tid("garden-plan-panel-off-site-error")
    OBJECT_LEGEND = _tid("garden-plan-legend-objects")

    # ── Window suggestion (WP 10.7) ────────────────────────────────────
    SUGGEST = _tid("garden-plan-panel-window-suggest")
    SUGGEST_DIALOG = _tid("garden-plan-window-suggestion-dialog")
    SUGGEST_VALUE = _tid("garden-plan-window-suggestion-value")
    SUGGEST_WINDOWS = _tid("garden-plan-window-suggestion-windows")
    SUGGEST_HINTS = _tid("garden-plan-window-suggestion-hints")
    SUGGEST_APPLY = _tid("garden-plan-window-suggestion-apply")
    SUGGEST_CANCEL = _tid("garden-plan-window-suggestion-cancel")

    # ── Navigation ─────────────────────────────────────────────────────

    def open_deep_link(self, site_key: str, query: str, expected_tab: str) -> WorkspacePlanPage:
        """Open the plan with the query string *query* (``tab=beds``) and wait until *expected_tab* is the open tab.

        The tab is read from the URL and - while the tabs stand in the header bar - from ``aria-selected`` of
        its tab; a route that settled on another tab fails loudly with what it shows.
        """
        self.navigate(f"{self.PATH.format(key=site_key)}?{query}")
        self.wait_for_content(self.HEADER_BAR, f"plan of site {site_key} with ?{query}")
        self.wait_for_tab(expected_tab, f"deep link ?{query}")
        return self

    #: Where the app shell keeps the user's dismissal of the light-mode warning (``layouts/MainLayout.tsx``).
    LIGHT_MODE_WARNING_DISMISSED_KEY = "kp-light-mode-warning-dismissed"

    def dismiss_light_mode_warning(self) -> None:
        """Store the user's own dismissal of the light-mode warning banner, as its close button does.

        The banner shows only in light mode on a non-private host (the E2E stack's ``frontend`` host) and stands
        between the breadcrumbs and the app bar; a layout measurement of the editor would otherwise measure the
        banner too. The value is the one the banner's ``onClose`` writes to ``localStorage``; it takes effect on the
        next page load and is read back here.
        """
        self.driver.execute_script(
            "window.localStorage.setItem(arguments[0], 'true');",
            self.LIGHT_MODE_WARNING_DISMISSED_KEY,
        )
        stored = self.driver.execute_script(
            "return window.localStorage.getItem(arguments[0]);",
            self.LIGHT_MODE_WARNING_DISMISSED_KEY,
        )
        if stored != "true":
            raise AssertionError(f"the light-mode warning dismissal was not stored: {stored!r}")

    def open_empty_plan(self, site_key: str) -> WorkspacePlanPage:
        """Open the plan of a site without plan content and return once its empty state rendered (GP-UX-049)."""
        self.navigate(self.PATH.format(key=site_key))
        self.wait_for_content(self.EMPTY, f"empty plan of site {site_key}")
        return self

    def open_field_mode_with_tab(self, site_key: str) -> WorkspacePlanPage:
        """Open ``?mode=field&tab=beds``: field mode, where ``tab`` has no effect (AC-12); waits for its bed list."""
        self.navigate(f"{self.PATH.format(key=site_key)}?mode=field&tab=beds")
        self.wait_for_content(
            FieldModePage.ROOT, f"field mode of site {site_key}", require_no_skeleton=False
        )
        self.wait_for_content(FieldModePage.BED_LIST, f"field-mode bed list of site {site_key}")
        return self

    def tab_bar_present(self) -> bool:
        """Whether the route shows a tab bar at all (``garden-plan-tabs``); an instantaneous read after a settle."""
        return self.is_present(self.TABS)

    def selected_inline_tab(self) -> str:
        """The tab whose header-bar tab carries ``aria-selected="true"``; loud when no tab is selected."""
        for name in self.PLAN_TABS:
            for element in self.driver.find_elements(*_tid(f"{self.TAB_PREFIX}{name}")):
                if element.get_attribute("aria-selected") == "true":
                    return name
        raise AssertionError("no plan tab carries aria-selected='true' in the header bar")

    def wait_for_tab(self, name: str, what: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until *name* is the open tab: in the URL and, while the tabs are inline, by ``aria-selected``."""

        def _open(_d: object) -> bool:
            if self.current_tab() != name:
                return False
            if self._inline(_tid(f"{self.TAB_PREFIX}{name}")):
                return self.selected_inline_tab() == name
            return True

        try:
            self.poll(timeout).until(_open)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: expected the tab {name!r}, the URL is {self.driver.current_url!r}"
            ) from exc

    def url_tab_param(self) -> str | None:
        """The raw ``tab`` query value (``None`` when the URL has none) - unlike ``current_tab`` not normalised."""
        values = parse_qs(urlparse(self.driver.current_url).query).get("tab")
        return values[0] if values else None

    def go_back_to_tab(self, name: str, what: str) -> None:
        """The browser's "Back" and wait until it shows the tab *name* (GP-UX-064: every switch is an entry)."""
        self.driver.back()
        self.wait_for_tab(name, what)

    def wait_for_tab_content(self, name: str, what: str) -> None:
        """The visible content of the tab *name*: the canvas (plan), the list (list) or the bed list (beds)."""
        target = {"plan": self.CANVAS, "list": self.LIST, "beds": self.BED_LIST_SECTION}[name]
        try:
            self.wait_for_element_visible(target)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the content of the tab {name!r} is not on screen"
            ) from exc

    # ── Bed list (tab "Beete" / "Pflanzplätze") ────────────────────────

    def bed_list_keys(self) -> set[str]:
        """The location keys the displayed bed list links to (table or cards, whichever is on screen)."""
        prefix = "bed-list-link-"
        return {
            (link.get_attribute("data-testid") or "")[len(prefix) :]
            for link in self.driver.find_elements(*self.BED_LIST_LINKS)
            if link.is_displayed()
        }

    def wait_for_bed_list_keys(self, expected: set[str], what: str, timeout: int = 15) -> None:
        """Wait until the bed list shows exactly *expected* (never satisfied by a list that has not loaded yet)."""
        if not expected:
            raise AssertionError(
                f"{what}: an empty expectation cannot tell a loaded list from a loading one"
            )
        try:
            self.poll(timeout).until(lambda _d: self.bed_list_keys() == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the bed list shows {sorted(self.bed_list_keys())}, expected {sorted(expected)}"
            ) from exc

    def bed_list_heading(self) -> str:
        return " ".join((self.wait_for_element_visible(self.BED_LIST_HEADING).text or "").split())

    def activate_bed_list_row(self, bed_key: str) -> None:
        """Choose the row of *bed_key* with the keyboard (focus + Enter: the row's own key handler, no coordinates)."""
        link = self.wait_for_element_visible(_tid(f"bed-list-link-{bed_key}"))
        row = self.driver.execute_script(
            "return arguments[0].closest(\"[data-testid='data-table-row']\");", link
        )
        if row is None:
            raise AssertionError(f"the bed list link of {bed_key} sits in no data-table-row")
        self.driver.execute_script("arguments[0].focus();", row)
        if not self.driver.execute_script("return document.activeElement === arguments[0];", row):
            raise AssertionError(f"the bed list row of {bed_key} did not take the keyboard focus")
        self.press(Keys.ENTER)

    # ── Side panel (GP-UX-068) ─────────────────────────────────────────

    def side_panel_state(self) -> tuple[str, str] | None:
        """``(variant, tab)`` of the side panel on screen, ``None`` while it is collapsed (then it is not rendered)."""
        for element in self.driver.find_elements(*self.SIDE_PANEL):
            if element.is_displayed():
                variant = element.get_attribute("data-variant")
                tab = element.get_attribute("data-tab")
                if not variant or not tab:
                    raise AssertionError(
                        f"the side panel carries no data-variant/data-tab: {variant!r}/{tab!r}"
                    )
                return variant, tab
        return None

    def wait_for_side_panel(
        self, expected: tuple[str, str] | None, what: str, timeout: int = DEFAULT_TIMEOUT
    ) -> None:
        """Wait until :meth:`side_panel_state` is *expected* (``None`` = collapsed)."""
        try:
            self.poll(timeout).until(lambda _d: self.side_panel_state() == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the side panel should be {expected}, it is {self.side_panel_state()}"
            ) from exc

    def side_panel_id(self) -> str:
        """The DOM ``id`` of the side panel on screen - what the switch's ``aria-controls`` must name (AC-5)."""
        for element in self.driver.find_elements(*self.SIDE_PANEL):
            if element.is_displayed():
                panel_id = element.get_attribute("id")
                if not panel_id:
                    raise AssertionError("the side panel on screen carries no id")
                return panel_id
        raise AssertionError("side_panel_id(): the side panel is collapsed")

    def panel_toggle_aria(self) -> tuple[str | None, str | None]:
        """``(aria-expanded, aria-controls)`` of the panel switch in the header bar; loud when it is not inline."""
        if not self._inline(self.PANEL_TOGGLE):
            raise AssertionError(
                "the panel switch is not in the header bar (it moved into the overflow)"
            )
        toggle = self.wait_for_element(self.PANEL_TOGGLE)
        return toggle.get_attribute("aria-expanded"), toggle.get_attribute("aria-controls")

    def click_panel_toggle(self) -> None:
        """Press the header bar's panel switch and wait until its ``aria-expanded`` flipped."""
        before, _ = self.panel_toggle_aria()
        self.click_coordinate_free(self.wait_for_element_clickable(self.PANEL_TOGGLE))
        try:
            self.poll().until(lambda _d: self.panel_toggle_aria()[0] != before)
        except TimeoutException as exc:
            raise AssertionError(
                f"the panel switch was pressed but aria-expanded stayed {before!r}"
            ) from exc

    def open_panel_from_overflow(self) -> None:
        """The overflow entry "Seitenpanel ein-/ausblenden" (narrow bar, GP-UX-063 step 3); waits for the panel."""
        self._click_overflow_entry(_tid("garden-plan-menu-panel"), "the side panel entry")
        try:
            self.poll().until(lambda _d: self.side_panel_state() is not None)
        except TimeoutException as exc:
            raise AssertionError("the side panel did not open from its overflow entry") from exc

    def open_side_panel_by_switch(self) -> None:
        """Open the collapsed panel by its switch - inline in the header bar, else its overflow entry."""
        if self.side_panel_state() is not None:
            raise AssertionError(f"the side panel is already open: {self.side_panel_state()}")
        if self._inline(self.PANEL_TOGGLE):
            self.click_panel_toggle()
        else:
            self.open_panel_from_overflow()

    def close_side_panel(self) -> None:
        """The panel's own close button; waits until the panel is collapsed (not rendered)."""
        self.click_coordinate_free(self.wait_for_element_clickable(self.SIDE_PANEL_CLOSE))
        self.wait_for_side_panel(None, "closing the side panel by its button")

    def tool_locator(self, tool: str) -> tuple[str, str]:
        """The rail button of the top-level tool *tool* (``select``, ``pan``, ``bed``, ``garden_object``, ``measure``)."""
        return _tid(f"garden-plan-tool-{tool}")

    def measure_status(self) -> str:
        """The measure tool's status text (``role="status"``): the next step and the measured total."""
        return (
            self.wait_for_element(self.MEASURE_STATUS).get_attribute("textContent") or ""
        ).strip()

    def wait_for_measure_status(
        self, fragment: str, what: str, timeout: int = DEFAULT_TIMEOUT
    ) -> str:
        """Wait until the measure status contains *fragment*; loud with the last text otherwise."""
        try:
            self.poll(timeout).until(lambda _d: fragment in self.measure_status())
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the measure status should contain {fragment!r}, reads {self.measure_status()!r}"
            ) from exc
        return self.measure_status()

    def measure_texts(self) -> tuple[list[str], str]:
        """The segment lengths and the total the measure overlay draws on the canvas."""
        segments = [
            (node.get_attribute("textContent") or "").strip()
            for node in self.driver.find_elements(*self.MEASURE_SEGMENTS)
        ]
        total = (
            self.wait_for_element(self.MEASURE_TOTAL).get_attribute("textContent") or ""
        ).strip()
        return segments, total

    # An entry the menu's paper has scrolled out of sight is reachable when the paper is a scroll container the user
    # can scroll (``overflow-y`` auto/scroll): the entry is scrolled into the paper the way a wheel or a finger would,
    # then its rect is read. ``in_menu`` says whether it then lies inside the paper's visible box. A paper that cannot
    # scroll leaves a cut-off entry outside it (``in_menu`` false); a paper that grows past the viewport leaves the
    # entry outside the viewport - either way the caller's check fails (AC-2: reachable, not merely present).
    _MENU_ENTRY_RECTS = """
        var menu = document.querySelector(arguments[0]);
        if (!menu) return null;
        var paper = menu.querySelector('.MuiPaper-root') || menu;
        var style = getComputedStyle(paper);
        if (style.transform !== 'none' || style.opacity !== '1') return null;
        var scrollable = /(auto|scroll)/.test(style.overflowY);
        var entries = Array.from(menu.querySelectorAll("[role^='menuitem']")).map(function (item) {
            var p = paper.getBoundingClientRect();
            var r = item.getBoundingClientRect();
            var scrolled = false;
            if (scrollable && (r.bottom > p.bottom + 1 || r.top < p.top - 1)) {
                paper.scrollTop += r.bottom > p.bottom ? r.bottom - p.bottom : r.top - p.top;
                r = item.getBoundingClientRect();
                scrolled = true;
            }
            return {testid: item.getAttribute('data-testid') || '', text: (item.textContent || '').trim(),
                    left: r.left, right: r.right, top: r.top, bottom: r.bottom, height: r.height,
                    scrolled: scrolled, in_menu: r.top >= p.top - 1 && r.bottom <= p.bottom + 1};
        });
        paper.scrollTop = 0;
        return entries;
    """

    def menu_entry_rects(self, trigger: tuple[str, str], menu_testid: str, what: str) -> list[dict]:
        """Open the menu behind *trigger*, read the rect of every entry once the menu stands still, close it by Escape.

        The rects are read after the ``Grow`` transition (transform ``none``, opacity 1); a scale that is still
        running would report a shrunken entry. An entry outside the visible part of a scrolling menu is scrolled into
        it first (``scrolled``); ``in_menu`` tells whether it is then visible inside the menu (see
        ``_MENU_ENTRY_RECTS``). Loud when the menu does not open, has no entry, or does not close.
        """
        selector = f"[data-testid='{menu_testid}']"
        self._open_menu(trigger, (By.CSS_SELECTOR, selector), what)
        try:
            entries = self.poll().until(
                lambda d: d.execute_script(self._MENU_ENTRY_RECTS, selector) or None
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the menu shows no entry, or it never stood still"
            ) from exc
        self.press(Keys.ESCAPE)
        self.wait_for_element_hidden((By.CSS_SELECTOR, f"{selector} [role^='menuitem']"))
        return entries

    def choose_side_panel_tab(self, tab: str) -> None:
        """Pick the panel tab *tab* in the open panel (no opening: the state rule is what the caller observes)."""
        state = self.side_panel_state()
        if state is None:
            raise AssertionError(f"choose_side_panel_tab({tab!r}): the side panel is collapsed")
        locator = _tid(f"garden-plan-side-panel-tab-{tab}")
        self.click_coordinate_free(self.wait_for_element_clickable(locator))
        self.wait_for_side_panel((state[0], tab), f"choosing the panel tab {tab!r}")

    def panel_tab_wiring(self) -> list[dict]:
        """The WAI-ARIA wiring of every panel tab (see ``_PANEL_TAB_WIRING``); loud when the tab list is missing."""
        wiring = self.driver.execute_script(
            _PANEL_TAB_WIRING, self.wait_for_element(self.SIDE_PANEL_TABLIST)
        )
        if not wiring:
            raise AssertionError("the side panel's tab list holds no role='tab'")
        return list(wiring)

    def press_on_active_panel_tab(self, key: str) -> None:
        """Focus the selected panel tab and press *key* (arrow, Home, End) - the keyboard path of the tab list.

        The tabs activate manually (#2887): an arrow, Home or End only moves the focus; Enter or Space on the focused
        tab (``press``) activates it.
        """
        state = self.side_panel_state()
        if state is None:
            raise AssertionError("press_on_active_panel_tab(): the side panel is collapsed")
        active = self.wait_for_element(_tid(f"garden-plan-side-panel-tab-{state[1]}"))
        self.driver.execute_script("arguments[0].focus();", active)
        if not self.driver.execute_script(
            "return document.activeElement === arguments[0];", active
        ):
            raise AssertionError(f"the panel tab {state[1]!r} did not take the keyboard focus")
        self.press(key)

    def focused_testid(self) -> str | None:
        return self.driver.execute_script(
            "var a = document.activeElement; return a ? a.getAttribute('data-testid') : null;"
        )

    def deselect_with_escape(self, key: str) -> None:
        """Clear the selection of *key* with Escape **on that object** (focused first; no blind Escape on the body)."""
        node = self.wait_for_object(key)
        self.driver.execute_script("arguments[0].focus();", node)
        if not self.driver.execute_script("return document.activeElement === arguments[0];", node):
            raise AssertionError(
                f"plan object {key!r} did not take the keyboard focus before Escape"
            )
        self.press(Keys.ESCAPE)
        self.wait_for_selected(key, False, f"Escape on plan object {key!r}")

    def layer_toggle_texts(self) -> dict[str, str]:
        """``{layer test id: visible text}`` of the layer switches in the open "layers" tab; loud without switches."""
        group = self.wait_for_element_visible(self.LAYER_TOGGLES)
        texts = {
            (toggle.get_attribute("data-testid") or ""): " ".join((toggle.text or "").split())
            for toggle in group.find_elements(
                By.CSS_SELECTOR, "[data-testid^='garden-plan-layer-']"
            )
            if toggle.is_displayed()
        }
        if not texts:
            raise AssertionError("the layers tab shows no layer switch")
        return texts

    # ── Layout (GP-UX-063/067/069) ─────────────────────────────────────

    def rect_of(self, locator: tuple[str, str], what: str) -> dict[str, float]:
        """The bounding rect of the first displayed match of *locator*; loud when none is displayed."""
        if locator[0] != By.CSS_SELECTOR:
            raise AssertionError(f"rect_of() takes a CSS locator, got {locator!r}")
        self.wait_for_element_visible(locator)
        rect = self.driver.execute_script(_DISPLAYED_RECT, locator[1])
        if rect is None:
            raise AssertionError(f"{what}: {locator[1]} is not displayed")
        return {k: float(v) for k, v in rect.items()}

    def viewport_size(self) -> tuple[int, int]:
        inner = self.driver.execute_script("return [window.innerWidth, window.innerHeight];")
        return int(inner[0]), int(inner[1])

    def horizontal_overflow_px(self) -> int:
        """How far the page is wider than its viewport (0 = no horizontal scrolling)."""
        return int(
            self.driver.execute_script(
                "var d = document.documentElement;"
                "return Math.max(d.scrollWidth, document.body.scrollWidth) - d.clientWidth;"
            )
        )

    def header_bar_count(self) -> int:
        return sum(
            1 for element in self.driver.find_elements(*self.HEADER_BAR) if element.is_displayed()
        )

    def header_controls(self) -> list[tuple[str, float, float]]:
        """Every displayed control of the header bar as ``(name, top, bottom)``; loud when there is none."""
        controls = self.driver.execute_script(
            _HEADER_CONTROLS, self.wait_for_element_visible(self.HEADER_BAR)
        )
        if not controls:
            raise AssertionError("the header bar shows no control at all")
        return [(str(name), float(top), float(bottom)) for name, top, bottom in controls]

    @staticmethod
    def on_one_line(controls: list[tuple[str, float, float]]) -> bool:
        """All controls share one horizontal band: the lowest top lies above the highest bottom."""
        return max(top for _, top, _ in controls) < min(bottom for _, _, bottom in controls)

    def button_sizes(self, locator: tuple[str, str]) -> list[tuple[str, float, float]]:
        """``(name, width, height)`` of every displayed button inside *locator*; loud when it holds none."""
        sizes = self.driver.execute_script(_BUTTON_SIZES, self.wait_for_element_visible(locator))
        if not sizes:
            raise AssertionError(f"{locator[1]} holds no displayed button")
        return [(str(name), float(w), float(h)) for name, w, h in sizes]

    def button_rects(self, locator: tuple[str, str]) -> list[tuple[str, dict[str, float]]]:
        """``(name, box)`` of every displayed button inside *locator*; loud when it holds none."""
        rects = self.driver.execute_script(_BUTTON_RECTS, self.wait_for_element_visible(locator))
        if not rects:
            raise AssertionError(f"{locator[1]} holds no displayed button")
        return [
            (
                str(name),
                {
                    "left": float(left),
                    "top": float(top),
                    "right": float(right),
                    "bottom": float(bottom),
                },
            )
            for name, left, top, right, bottom in rects
        ]

    def is_uncovered(self, locator: tuple[str, str], what: str) -> bool:
        """Whether nothing (a tooltip, a menu) lies over the centre of the displayed *locator*; loud when absent."""
        if locator[0] != By.CSS_SELECTOR:
            raise AssertionError(f"is_uncovered() takes a CSS locator, got {locator!r}")
        self.wait_for_element_visible(locator)
        found = self.driver.execute_script(_UNCOVERED, locator[1])
        if found is None:
            raise AssertionError(f"{what}: {locator[1]} is not displayed")
        return bool(found)

    def wait_for_no_tooltip(self, what: str) -> None:
        """Wait until no tooltip is displayed (a closing one fades out); loud when one stays (#2904)."""
        try:
            self.poll().until(
                lambda d: (
                    not any(element.is_displayed() for element in d.find_elements(*self.TOOLTIP))
                )
            )
        except TimeoutException as exc:
            texts = [
                " ".join((element.text or "").split())
                for element in self.driver.find_elements(*self.TOOLTIP)
                if element.is_displayed()
            ]
            raise AssertionError(f"{what}: a tooltip stays on screen: {texts}") from exc

    def touchbar_holds(self, testid: str) -> bool:
        """Whether the displayed ``TouchBar`` holds a displayed control *testid* (undo/redo below md, GP-UX-052)."""
        bar = self.wait_for_element_visible(self.TOUCHBAR)
        return any(
            element.is_displayed()
            for element in bar.find_elements(By.CSS_SELECTOR, f"[data-testid='{testid}']")
        )

    def toolbar_orientation(self) -> str:
        value = self.wait_for_element_visible(self.TOOLBAR).get_attribute("data-orientation")
        if value not in ("vertical", "horizontal"):
            raise AssertionError(f"the tool bar carries no orientation: {value!r}")
        return value

    def inspect_overflow(
        self,
        entries: tuple[str, ...],
        *,
        then_choose: str,
        during: Callable[[], None] | None = None,
    ) -> dict[str, tuple[float, str]]:
        """Open the overflow "⋮", read ``{entry: (height px, text)}`` of *entries*, then choose *then_choose*.

        Ends by choosing an entry - the menu's own way out - instead of a dismissal key. Loud when an entry is
        missing; *during* runs while the menu is open (a screenshot checkpoint).
        """
        self._open_menu(self.OVERFLOW, self.OVERFLOW_MENU, "the overflow menu")
        found: dict[str, tuple[float, str]] = {}
        for entry in entries:
            selector = f"[data-testid='garden-plan-overflow-menu'] [data-testid='{entry}']"
            try:
                item = self.wait_for_element_visible((By.CSS_SELECTOR, selector))
            except TimeoutException as exc:
                raise AssertionError(f"the overflow has no entry {entry!r}") from exc
            # The layout height (``offsetHeight``), not the rendered rect: the menu opens with a ``Grow`` transition,
            # whose scale transform makes ``getBoundingClientRect`` read a growing height while it runs.
            height = float(self.driver.execute_script("return arguments[0].offsetHeight;", item))
            found[entry] = (height, " ".join((item.text or "").split()))
        if during is not None:
            during()
        chosen = self.wait_for_element_clickable(
            (
                By.CSS_SELECTOR,
                f"[data-testid='garden-plan-overflow-menu'] [data-testid='{then_choose}']",
            )
        )
        self.click_menu_option(chosen)
        self.wait_for_element_hidden(self.OVERFLOW_MENU)
        return found

    # ── Drawing a garden object ────────────────────────────────────────

    def start_drawing_from_empty_state(self) -> None:
        """The indoor empty state's "Grundriss zeichnen": the editor mounts on the default area of an empty plan."""
        self.wait_and_click(self.EMPTY_DRAW)
        self.wait_for_content(self.EDITOR, "the editor after 'Grundriss zeichnen'")
        self.wait_for_element(self.SVG)

    def choose_new_object_type(self, object_type: str) -> None:
        """Pick the type of the next drawn object in its Select (opens on mousedown); read back on the input."""
        choose_from_native_select(self, self.NEW_OBJECT_TYPE, object_type)

    def choose_new_area_type(self, area_type: str) -> None:
        """Pick the type of the next drawn area in its Select (opens on mousedown); read back on the input."""
        choose_from_native_select(self, self.NEW_AREA_TYPE, area_type)

    def new_area_type_rule(self) -> str:
        """The parent rule beside the area type choice (GP-UX-071), whitespace-normalised."""
        return self.text_of(self.NEW_AREA_TYPE_RULE)

    def choose_draw_shape(self, shape: str) -> None:
        self.choose_tool(_tid(f"garden-plan-shape-{shape}"))

    def click_plan_point(self, x_m: float, y_m: float, what: str) -> None:
        """One trusted pointer press and release on the empty plan surface at model point (*x_m*, *y_m*)."""
        self._bring_canvas_into_view()
        point: ScreenPoint = self.to_screen(x_m, y_m)
        self._require_hit(point, None, what)
        builder = ActionBuilder(self.driver)
        builder.pointer_action.move_to_location(round(point.x), round(point.y))
        builder.pointer_action.pointer_down(MouseButton.LEFT)
        builder.pointer_action.pointer_up(MouseButton.LEFT)
        builder.perform()

    def click_plan_position(self, x_m: float, y_m: float, what: str) -> None:
        """One trusted pointer press and release at model point (*x_m*, *y_m*) on the plan, whatever is drawn there.

        The plant tool's target is a planting-spot marker, which the editor draws as a decorative path: the guard
        checks only that the point lies on the plan (``elementFromPoint`` inside the SVG), not which object it is.
        """
        self._bring_canvas_into_view()
        point: ScreenPoint = self.to_screen(x_m, y_m)
        inside = self.driver.execute_script(
            "var el = document.elementFromPoint(arguments[0], arguments[1]); return !!el && arguments[2].contains(el);",
            point.x,
            point.y,
            self.wait_for_element(self.SVG),
        )
        if not inside:
            raise AssertionError(
                f"{what}: the point ({point.x:.1f}, {point.y:.1f}) is not on the plan"
            )
        builder = ActionBuilder(self.driver)
        builder.pointer_action.move_to_location(round(point.x), round(point.y))
        builder.pointer_action.pointer_down(MouseButton.LEFT)
        builder.pointer_action.pointer_up(MouseButton.LEFT)
        builder.perform()

    def plant_status(self) -> str:
        """The plant tool's status text (``role="status"``): what a click does."""
        return self.text_of(self.PLANT_STATUS)

    def wait_for_plant_dialog(self, what: str) -> str:
        """The plant dialog is open; its title (bed and spot)."""
        try:
            self.wait_for_element_visible(self.PLANT_DIALOG)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the plant dialog did not open") from exc
        return self.text_of(self.PLANT_DIALOG_TITLE)

    def choose_plant_species(self, scientific_name: str) -> str:
        """Type the scientific name into the dialog's species picker and pick exactly that species' option."""
        field = self.wait_for_element(self.PLANT_DIALOG_SPECIES)
        self.clear_and_fill(field, scientific_name)
        suffix = f"({scientific_name})"

        def _option():
            for option in self.driver.find_elements(*self.PLANT_OPTIONS):
                if suffix in " ".join((option.get_attribute("textContent") or "").split()):
                    return option
            return False

        try:
            option = self.poll().until(lambda _d: _option())
        except TimeoutException as exc:
            rendered = [
                o.get_attribute("textContent")
                for o in self.driver.find_elements(*self.PLANT_OPTIONS)
            ]
            raise AssertionError(
                f"the plant dialog offers no option for {scientific_name!r}; options: {rendered}"
            ) from exc
        self.click_menu_option(option)
        self.poll().until(lambda _d: (field.get_attribute("value") or "").endswith(suffix))
        return field.get_attribute("value") or ""

    def submit_plant_dialog(self, what: str) -> None:
        """Press "Pflanze setzen" once it is enabled (the slot check ran); waits until the dialog is gone."""
        try:
            self.poll().until(lambda d: d.find_element(*self.PLANT_DIALOG_SUBMIT).is_enabled())
        except TimeoutException as exc:
            raise AssertionError(f"{what}: 'Pflanze setzen' stays disabled") from exc
        self.wait_and_click_coordinate_free(self.PLANT_DIALOG_SUBMIT)
        try:
            self.poll().until(lambda d: not d.find_elements(*self.PLANT_DIALOG))
        except TimeoutException as exc:
            errors = [
                (e.get_attribute("textContent") or "").strip()
                for e in self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "[data-testid^='garden-plan-plant-dialog-'][role='alert'], [data-testid='garden-plan-plant-dialog-blocked']",
                )
            ]
            raise AssertionError(
                f"{what}: the plant dialog did not close; it says {errors}"
            ) from exc

    def finish_drawing(self) -> None:
        """ "Fertig" of a point-by-point shape; waits until the new object is one unsaved change."""
        before = self.pending_count()
        self.wait_and_click_coordinate_free(self.DRAW_FINISH)
        self.wait_for_pending(before + 1, "finishing the drawn shape")

    def selected_keys(self) -> set[str]:
        """The plan objects drawn as selected (``aria-pressed="true"``)."""
        return {
            node.get_attribute("data-plan-key")
            for node in self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='garden-plan-svg'] [data-plan-key][role='button'][aria-pressed='true']",
            )
        }

    # ── Object properties (GP-FR-180) ──────────────────────────────────

    def wait_for_object_props(self, object_type: str, what: str) -> None:
        """The properties tab shows the fields of a *object_type* object (``data-object-type``)."""
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='garden-plan-panel-object-props'][data-object-type='{object_type}']",
        )
        try:
            self.wait_for_element_visible(locator)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the panel shows no {object_type} properties") from exc

    def commit_prop_number(self, locator: tuple[str, str], text: str) -> None:
        """Type *text* into a numeric property field and commit it with Enter: exactly one more unsaved change."""
        before = self.pending_count()
        field = self.wait_for_element_clickable(locator)
        self.clear_and_fill(field, text)
        field.send_keys(Keys.ENTER)
        self.wait_for_pending(before + 1, f"committing {text!r} in {locator[1]}")

    def choose_prop_select(self, testid: str, value: str) -> None:
        """Pick *value* in a property Select (opens on mousedown): exactly one more unsaved change."""
        before = self.pending_count()
        choose_from_native_select(self, testid, value)
        self.wait_for_pending(before + 1, f"choosing {value!r} in {testid}")

    def window_orientation(self) -> tuple[str, str]:
        """``(data-available, visible text)`` of the window's derived orientation."""
        element = self.wait_for_element_visible(self.WINDOW_ORIENTATION)
        return element.get_attribute("data-available") or "", " ".join((element.text or "").split())

    def off_site_checked(self) -> bool:
        return bool(self.wait_for_element(self.OFF_SITE_SWITCH).is_selected())

    def press_off_site_switch(self) -> None:
        """Space on the focused switch input (a checkbox: Space is its key) - the caller reads the effect."""
        switch = self.wait_for_element(self.OFF_SITE_SWITCH)
        self.driver.execute_script("arguments[0].focus();", switch)
        if not self.driver.execute_script(
            "return document.activeElement === arguments[0];", switch
        ):
            raise AssertionError("the off-site switch did not take the keyboard focus")
        self.press(Keys.SPACE)

    def object_legend_types(self) -> set[str]:
        """The object classes the legend in the "layers" tab lists (``garden-plan-legend-object-<type>``)."""
        self.open_side_panel_tab("layers")
        legend = self.wait_for_element_visible(self.OBJECT_LEGEND)
        prefix = "garden-plan-legend-object-"
        types = {
            (entry.get_attribute("data-testid") or "")[len(prefix) :]
            for entry in legend.find_elements(By.CSS_SELECTOR, f"[data-testid^='{prefix}']")
        }
        if not types:
            raise AssertionError("the object legend lists no object class")
        return types

    # ── Window suggestion (GP-FR-181) ──────────────────────────────────

    def open_window_suggestion(self) -> None:
        """ "Aus Fenster vorschlagen" in the sun section of the selected location; waits for the preview dialog."""
        self.wait_and_click_coordinate_free(self.SUGGEST)
        self.wait_for_element_visible(self.SUGGEST_DIALOG)

    def suggested_sun_window(self) -> str:
        value = self.wait_for_element_visible(self.SUGGEST_VALUE).get_attribute("data-sun-window")
        if not value:
            raise AssertionError("the suggestion carries no data-sun-window")
        return value

    def suggestion_text(self) -> str:
        return " ".join((self.wait_for_element_visible(self.SUGGEST_VALUE).text or "").split())

    def suggested_windows(self) -> dict[str, str]:
        """``{window key: data-orientation}`` of the windows the preview lists; loud when it lists none."""
        prefix = "garden-plan-window-suggestion-window-"
        listing = self.wait_for_element_visible(self.SUGGEST_WINDOWS)
        found = {
            (row.get_attribute("data-testid") or "")[len(prefix) :]: row.get_attribute(
                "data-orientation"
            )
            or ""
            for row in listing.find_elements(By.CSS_SELECTOR, f"[data-testid^='{prefix}']")
        }
        if not found:
            raise AssertionError("the suggestion preview lists no window")
        return found

    def suggestion_hints(self) -> set[str]:
        hints = self.wait_for_element_visible(self.SUGGEST_HINTS)
        found = {
            item.get_attribute("data-hint") or ""
            for item in hints.find_elements(By.CSS_SELECTOR, "[data-hint]")
        }
        if not found:
            raise AssertionError("the suggestion preview shows a hint list without hints")
        return found

    def cancel_window_suggestion(self) -> None:
        self.wait_and_click_coordinate_free(self.SUGGEST_CANCEL)
        self.wait_for_element_hidden(self.SUGGEST_DIALOG)

    def apply_window_suggestion(self) -> None:
        """ "Übernehmen": the dialog closes and the sun window is one more unsaved change (never saved on its own)."""
        before = self.pending_count()
        self.wait_and_click_coordinate_free(self.SUGGEST_APPLY)
        self.wait_for_element_hidden(self.SUGGEST_DIALOG)
        self.wait_for_pending(before + 1, "applying the window suggestion")

    # ── Tasks on garden objects (R-7.2, W-008; WP 10.10, E2E WP 10.14) ─

    OBJECT_TASKS = _tid("garden-plan-panel-object-tasks")
    OBJECT_TASKS_EMPTY = _tid("garden-plan-panel-object-tasks-empty")
    OBJECT_TASKS_LIST = _tid("garden-plan-panel-object-tasks-list")
    OBJECT_TASKS_ERROR = _tid("garden-plan-panel-object-tasks-error")
    OBJECT_TASK_ADD = _tid("garden-plan-panel-object-task-add")
    OBJECT_TASK_ROW_PREFIX = "garden-plan-panel-object-task-"
    TASK_DIALOG = _tid("care-task-dialog")
    TASK_DIALOG_TITLE = (By.CSS_SELECTOR, "[data-testid='care-task-dialog'] h2")
    TASK_NAME = _tid("care-task-name")
    TASK_SUBMIT = _tid("care-task-submit")
    TASK_OBJECT_HINT = _tid("care-task-object-hint")
    TASK_SCOPE_BED = _tid("care-task-scope-bed")
    TASK_SCOPE_PLANTS = _tid("care-task-scope-plants")

    def wait_for_object_tasks(self, object_type: str, what: str) -> str:
        """Wait until the "Aufgaben" section of a *object_type* object finished loading: ``"empty"`` or ``"list"``.

        The section renders at once with a loading line; settled is the empty text or the list - an error surface
        is a loud failure with its text, never read as "no task".
        """
        section = (
            By.CSS_SELECTOR,
            f"[data-testid='garden-plan-panel-object-tasks'][data-object-type='{object_type}']",
        )
        try:
            self.wait_for_element_visible(section)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the panel shows no task section for a {object_type}"
            ) from exc

        def _settled(_d: object) -> str | bool:
            if self.is_present(self.OBJECT_TASKS_ERROR):
                return "error"
            if self.is_present(self.OBJECT_TASKS_LIST):
                return "list"
            if self.is_present(self.OBJECT_TASKS_EMPTY):
                return "empty"
            return False

        try:
            state = self.poll().until(_settled)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the task section never finished loading") from exc
        if state == "error":
            text = " ".join((self.wait_for_element(self.OBJECT_TASKS_ERROR).text or "").split())
            raise AssertionError(f"{what}: the task section shows an error: {text!r}")
        return str(state)

    def has_object_tasks_section(self) -> bool:
        """Whether the panel holds a task section now (read after the object's properties anchored)."""
        return self.is_present(self.OBJECT_TASKS)

    def object_task_rows(self) -> dict[str, str]:
        """``{task key: visible text}`` of the rows the section lists; loud when the list is not shown."""
        listing = self.wait_for_element_visible(self.OBJECT_TASKS_LIST)
        rows = {}
        for row in listing.find_elements(
            By.CSS_SELECTOR, f"li[data-testid^='{self.OBJECT_TASK_ROW_PREFIX}']"
        ):
            key = (row.get_attribute("data-testid") or "")[len(self.OBJECT_TASK_ROW_PREFIX) :]
            rows[key] = " ".join((row.get_attribute("textContent") or "").split())
        if not rows:
            raise AssertionError("the object's task list is shown without a row")
        return rows

    def open_object_task_dialog(self) -> None:
        """ "Aufgabe anlegen" in the section: waits for the task dialog bound to a garden object."""
        self.wait_and_click_coordinate_free(self.OBJECT_TASK_ADD)
        dialog = self.wait_for_element_visible(self.TASK_DIALOG)
        target = dialog.get_attribute("data-target")
        if target != "garden_object":
            raise AssertionError(
                f"the task dialog opened for {target!r}, not for the garden object"
            )

    def task_dialog_title(self) -> str:
        return " ".join((self.wait_for_element_visible(self.TASK_DIALOG_TITLE).text or "").split())

    def task_dialog_categories(self) -> list[str]:
        """The category values the open task dialog offers, in the order shown."""
        return native_select_values(self, "care-task-category")

    def task_dialog_has_scope_choice(self) -> bool:
        """Whether the open task dialog offers "Gilt für" (bed / every plant); read after the dialog settled."""
        self.wait_for_element_visible(self.TASK_DIALOG)
        return self.is_present(self.TASK_SCOPE_BED) or self.is_present(self.TASK_SCOPE_PLANTS)

    def task_dialog_object_hint(self) -> str:
        return " ".join((self.wait_for_element_visible(self.TASK_OBJECT_HINT).text or "").split())

    def submit_object_task(self, category: str, name: str, what: str) -> str:
        """Pick *category*, type *name*, submit; return the key of the row the section then lists for *name*.

        The dialog closes only on a fulfilled create, and the section reloads its list after it: the new row is the
        proof the server accepted the task.
        """
        choose_from_native_select(self, "care-task-category", category)
        field = self.wait_for_element_clickable(self.TASK_NAME)
        self.clear_and_fill(field, name)
        self.poll().until(lambda _d: (field.get_attribute("value") or "") == name)
        self.wait_and_click_coordinate_free(self.TASK_SUBMIT)
        try:
            self.wait_for_element_hidden(self.TASK_DIALOG)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the task dialog did not close after the submit") from exc

        def _row(_d: object) -> str | bool:
            if not self.is_present(self.OBJECT_TASKS_LIST):
                return False
            for key, text in self.object_task_rows().items():
                if name in text:
                    return key
            return False

        try:
            return str(self.poll().until(_row))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the section lists no task named {name!r} after the create"
            ) from exc


__all__ = ["WorkspacePlanPage"]
