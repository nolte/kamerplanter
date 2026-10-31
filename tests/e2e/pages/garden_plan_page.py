"""Page object for the garden plan editor (REQ-053 WP 2.3-2.8, ``/standorte/sites/:key/plan``).

Every hook used here is a ``data-testid`` (or the renderer's ``data-plan-key``)
that exists in ``src/frontend/src/features/gardenPlanner/`` — none is guessed.

HOW THE CANVAS IS DRIVEN (`e2e-test-stability` §C)
-------------------------------------------------
Two input paths, chosen by what the gesture *is*:

* **Keyboard, wherever the product offers it.** Selecting an object
  (focus + Enter), moving it (arrows), undo/redo/save (Ctrl+Z / Ctrl+Shift+Z /
  Ctrl+S), the list view switch (Space) and the list rows (arrows + Enter) are
  coordinate-free and trusted, and they exercise the accessibility contract the
  editor promises (GP-ACC-008).
* **Real pointer input where the gesture is spatial** — drawing a rectangle and
  dragging a bed. A drag on a canvas has no coordinate-free equivalent, so it is
  W3C pointer actions (trusted ``pointerdown``/``pointermove``/``pointerup``)
  aimed at a model point converted through the SVG's own ``viewBox``. Before the
  press the target point is checked with ``elementFromPoint``: it must resolve to
  the intended plan object (or, for drawing, to the empty plan surface), and a
  miss fails loudly with the element stack at that point instead of dragging
  whatever happens to lie there.

Every state-changing helper reads its effect back (pending-change count, a panel
field, ``aria-pressed``) and fails loudly when the effect never arrives
(`e2e-test-stability` §D, `test-falsifiability` T4).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.mouse_button import MouseButton
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import DEFAULT_TIMEOUT, BasePage


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


@dataclass(frozen=True)
class ScreenPoint:
    """A point in CSS viewport pixels (what W3C pointer actions take)."""

    x: float
    y: float


class GardenPlanPage(BasePage):
    """The plan of one site: canvas, save bar, properties panel, list view, dialogs."""

    PATH = "/standorte/sites/{key}/plan"

    # ── Page and editor ────────────────────────────────────────────────
    PAGE = _tid("garden-plan-page")
    EDITOR = _tid("garden-plan-editor")
    CANVAS = _tid("garden-plan-canvas")
    SVG = _tid("garden-plan-svg")
    LIVE_REGION = _tid("garden-plan-live-region")

    # ── Save bar (WP 2.8) ──────────────────────────────────────────────
    SAVE_STATUS = _tid("garden-plan-save-status")
    SAVE_BUTTON = _tid("garden-plan-save")
    UNDO_BUTTON = _tid("garden-plan-undo")
    REDO_BUTTON = _tid("garden-plan-redo")

    # ── Toolbar and view bar (WP 2.4 / 2.5) ────────────────────────────
    TOOL_SELECT = _tid("garden-plan-tool-select")
    TOOL_BED = _tid("garden-plan-tool-bed")
    ZOOM_IN = _tid("garden-plan-zoom-in")
    ZOOM_OUT = _tid("garden-plan-zoom-out")
    ZOOM_LEVEL = _tid("garden-plan-zoom-level")

    # ── Gesture feedback (overlay) ─────────────────────────────────────
    GHOST = _tid("garden-plan-ghost")
    DIMENSION = _tid("garden-plan-dimension")

    # ── Properties panel (WP 2.6) ──────────────────────────────────────
    PANEL = _tid("garden-plan-panel")
    PANEL_EMPTY = _tid("garden-plan-panel-empty")
    PANEL_FORM = _tid("garden-plan-panel-form")
    PANEL_NAME = _tid("garden-plan-panel-name")

    # ── List view (WP 2.7) ─────────────────────────────────────────────
    VIEW_LIST_SWITCH = _tid("garden-plan-view-list")
    LIST = _tid("garden-plan-list")
    LIST_DETAILS = _tid("garden-plan-list-details")

    # ── Dialogs ────────────────────────────────────────────────────────
    CONFLICT_DIALOG = _tid("plan-conflict-dialog")
    CONFLICT_RELOAD = _tid("plan-conflict-reload")
    CONFLICT_DOWNLOAD = _tid("plan-conflict-download")
    # The route's UnsavedChangesGuard is a ConfirmDialog; a closed MUI Dialog
    # renders nothing, so while the guard is open it is the only one on the page.
    LEAVE_DIALOG = _tid("confirm-dialog")
    LEAVE_CANCEL = (
        By.CSS_SELECTOR,
        "[data-testid='confirm-dialog'] [data-testid='confirm-dialog-cancel']",
    )
    LEAVE_CONFIRM = (
        By.CSS_SELECTOR,
        "[data-testid='confirm-dialog'] [data-testid='confirm-dialog-confirm']",
    )

    # ── Wave 7 (WP 7.6-7.13): layers, zones, templates, arrange, auto-save ──
    INFO = _tid("garden-plan-info")
    NOTICE = _tid("garden-plan-notice")
    AUTOSAVE = _tid("garden-plan-autosave")
    AUTOSAVE_PAUSED = _tid("garden-plan-autosave-paused")
    WATERED_LAYER = _tid("garden-plan-watered-layer")
    ZONE_LAYER = _tid("garden-plan-zone-layer")
    LEGEND_WATERED = _tid("garden-plan-legend-watered")
    SNAP_MARKER = _tid("garden-plan-snap-marker")
    MINIMAP = _tid("garden-plan-minimap")
    MINIMAP_VIEWPORT = _tid("garden-plan-minimap-viewport")

    ZONES_OPEN = _tid("garden-plan-zones-open")
    ZONE_PANEL = _tid("garden-plan-zone-panel")
    ZONE_NEW = _tid("garden-plan-zone-new")
    ZONE_FORM = _tid("garden-plan-zone-form")
    ZONE_NAME = _tid("garden-plan-zone-name")
    ZONE_TAKE_SELECTION = _tid("garden-plan-zone-take-selection")
    ZONE_SAVE = _tid("garden-plan-zone-save")
    ZONE_STATUS = _tid("garden-plan-zone-status")
    ZONE_LAST_WATERING = _tid("garden-plan-zone-last-watering")
    ZONE_ALLOCATION_MARKER = _tid("garden-plan-zone-allocation-marker")
    ROUND_OPEN = _tid("garden-plan-zone-round-open")
    ROUND_DIALOG = _tid("garden-plan-round-dialog")
    ROUND_VOLUME = _tid("garden-plan-round-volume")
    ROUND_SUMMARY = _tid("garden-plan-round-summary")
    ROUND_MARKER = _tid("garden-plan-round-marker")
    ROUND_SUBMIT = _tid("garden-plan-round-submit")
    ROUND_RESULT = _tid("garden-plan-round-result")
    ROUND_RESULT_MARKER = _tid("garden-plan-round-result-marker")
    ROUND_DONE = _tid("garden-plan-round-done")
    PANEL_ZONE = _tid("garden-plan-panel-zone")
    PANEL_LAST_WATERED = _tid("garden-plan-panel-last-watered")

    TOOL_TEMPLATE = _tid("garden-plan-tool-template")
    TEMPLATE_PANEL = _tid("garden-plan-template-panel")
    TEMPLATE_HINT = _tid("garden-plan-template-hint")
    TEMPLATE_ROTATE = _tid("garden-plan-template-rotate")
    TEMPLATE_PLACE_CENTRE = _tid("garden-plan-template-place-center")

    ADD_WITH_DIMENSIONS = _tid("garden-plan-add-with-dimensions")
    ADD_DIALOG = _tid("garden-plan-add-dialog")
    ADD_STANDARD_SIZES = _tid("garden-plan-add-standard-sizes")
    ADD_BED_TYPE = _tid("garden-plan-add-bed-type")
    ADD_SUBMIT = _tid("garden-plan-add-submit")

    ALIGN_BUTTON = _tid("garden-plan-align-button")
    OVERFLOW = _tid("garden-plan-overflow")
    OVERFLOW_MENU = _tid("garden-plan-overflow-menu")
    MULTI_DIALOG = _tid("garden-plan-multi-dialog")
    MULTI_PREVIEW = _tid("garden-plan-multi-preview")
    MULTI_SUBMIT = _tid("garden-plan-multi-submit")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ─────────────────────────────────────────────────────

    def open(self, site_key: str) -> GardenPlanPage:
        """Open the plan of *site_key* and return once the **editor** rendered.

        The editor only mounts for a plan with content (boundary, bed or
        object); every caller provisions one, so the empty state or an error
        surface is a failure here, reported with what the route showed.
        """
        self.navigate(self.PATH.format(key=site_key))
        self.wait_for_content(self.EDITOR, f"garden plan editor of site {site_key}")
        self.wait_for_element(self.SVG)
        return self

    def reload(self, site_key: str) -> GardenPlanPage:
        """A full page load of the same plan — the read-back of what was stored."""
        if self.pending_count() != 0:
            raise AssertionError(
                "reload() with unsaved changes would open the browser's leave prompt; "
                f"save or undo first (status: {self.save_status_text()!r})"
            )
        return self.open(site_key)

    # ── Save bar ───────────────────────────────────────────────────────

    def pending_count(self) -> int:
        """Unsaved operations, from ``data-pending-count`` (the slice's ``pending.length``)."""
        raw = self.wait_for_element(self.SAVE_STATUS).get_attribute("data-pending-count")
        if raw is None or not raw.isdigit():
            raise AssertionError(f"save status carries no numeric data-pending-count: {raw!r}")
        return int(raw)

    def save_status_text(self) -> str:
        return (self.wait_for_element(self.SAVE_STATUS).get_attribute("textContent") or "").strip()

    def wait_for_pending(self, expected: int, what: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        try:
            self.poll(timeout).until(lambda _d: self.pending_count() == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: expected {expected} unsaved change(s), the save bar reports "
                f"{self.pending_count()} ({self.save_status_text()!r})"
            ) from exc

    def wait_for_status_text(
        self, expected: str, what: str, timeout: int = DEFAULT_TIMEOUT
    ) -> None:
        try:
            self.poll(timeout).until(lambda _d: self.save_status_text() == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: expected the save status {expected!r}, it reads "
                f"{self.save_status_text()!r}"
            ) from exc

    def save_with_button(self) -> None:
        """Click "Speichern" and return once the server accepted the batch.

        ``pending`` is emptied only by the fulfilled save (a 2xx), never
        optimistically, so ``pending == 0`` after ``> 0`` is a server-confirmed
        signal (`e2e-test-stability` §D).
        """
        before = self.pending_count()
        if before == 0:
            raise AssertionError("save_with_button(): nothing to save, the test arranged no change")
        self.wait_and_click(self.SAVE_BUTTON)
        self.wait_for_pending(0, f"saving {before} change(s) with the button")

    def click_save_expecting_refusal(self) -> None:
        """Click "Speichern" where the save is expected NOT to go through (conflict)."""
        if self.pending_count() == 0:
            raise AssertionError("click_save_expecting_refusal(): nothing to save")
        self.wait_and_click(self.SAVE_BUTTON)

    def is_undo_enabled(self) -> bool:
        return self.wait_for_element(self.UNDO_BUTTON).is_enabled()

    def is_redo_enabled(self) -> bool:
        return self.wait_for_element(self.REDO_BUTTON).is_enabled()

    def undo_with_button(self) -> None:
        before = self.pending_count()
        self.wait_and_click(self.UNDO_BUTTON)
        self.poll().until(lambda _d: self.pending_count() != before)

    # ── Keyboard ───────────────────────────────────────────────────────

    def _active_plan_key(self) -> str | None:
        return self.driver.execute_script(
            "var a = document.activeElement;"
            "return a && a.getAttribute ? a.getAttribute('data-plan-key') : null;"
        )

    def focus_canvas(self) -> None:
        """Put the keyboard focus on the canvas region (the editor's key target).

        ``focus()`` is the precondition of a keyboard flow, not the action under
        test; it moves no pointer. Verified, because a focus that did not land
        would send every following key to ``<body>``.
        """
        canvas = self.wait_for_element(self.CANVAS)
        self.driver.execute_script("arguments[0].focus();", canvas)
        focused = self.driver.execute_script(
            "return document.activeElement === arguments[0];", canvas
        )
        if not focused:
            raise AssertionError("the canvas region did not take the keyboard focus")

    def press(self, *keys: str) -> None:
        """Press *keys* as one chord on the focused element (modifiers first, released last)."""
        modifiers = [k for k in keys if k in (Keys.CONTROL, Keys.SHIFT, Keys.ALT, Keys.META)]
        plain = [k for k in keys if k not in modifiers]
        chain = ActionChains(self.driver)
        for modifier in modifiers:
            chain.key_down(modifier)
        for key in plain:
            chain.send_keys(key)
        for modifier in reversed(modifiers):
            chain.key_up(modifier)
        chain.perform()

    def tab_to_object(self, key: str) -> None:
        """Reach the plan object *key* with Tab (the roving tab stop) and PageDown.

        From the focused canvas region Tab lands on the plan's one tab stop
        (GP-NFR-068); PageDown walks object to object. Bounded by the number of
        object nodes, and fails loudly naming where the focus is instead.
        """
        self.wait_for_object(key)
        self.focus_canvas()
        self.press(Keys.TAB)
        nodes = len(self.driver.find_elements(By.CSS_SELECTOR, "[data-plan-key][role='button']"))
        for _ in range(nodes + 1):
            if self._active_plan_key() == key:
                return
            self.press(Keys.PAGE_DOWN)
        raise AssertionError(
            f"keyboard focus never reached plan object {key!r}; it is on "
            f"{self._active_plan_key()!r} after Tab and {nodes + 1} PageDown presses"
        )

    def object_has_visible_focus(self, key: str) -> bool:
        """``:focus-visible`` on the object — the focus ring the keyboard user sees."""
        node = self.wait_for_object(key)
        return bool(
            self.driver.execute_script(
                "return document.activeElement === arguments[0]"
                " && arguments[0].matches(':focus-visible');",
                node,
            )
        )

    def select_with_keyboard(self, key: str) -> None:
        """Tab to *key* and press Enter; return once the object is selected."""
        self.tab_to_object(key)
        self.press(Keys.ENTER)
        self.wait_for_selected(key, True, "selecting with Enter")

    # ── Plan objects ───────────────────────────────────────────────────

    def object_locator(self, key: str) -> tuple[str, str]:
        return (
            By.CSS_SELECTOR,
            f"[data-testid='garden-plan-svg'] [data-plan-key='{key}'][role='button']",
        )

    def wait_for_object(self, key: str):
        return self.wait_for_element(self.object_locator(key))

    def is_selected(self, key: str) -> bool:
        pressed = self.wait_for_object(key).get_attribute("aria-pressed")
        if pressed not in ("true", "false"):
            raise AssertionError(f"plan object {key!r} carries no aria-pressed: {pressed!r}")
        return pressed == "true"

    def wait_for_selected(self, key: str, selected: bool, what: str) -> None:
        try:
            self.poll().until(lambda _d: self.is_selected(key) is selected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: plan object {key!r} should be {'selected' if selected else 'unselected'}"
                f" (aria-pressed={self.wait_for_object(key).get_attribute('aria-pressed')!r})"
            ) from exc

    def object_kind(self, key: str) -> str:
        kind = self.wait_for_object(key).get_attribute("data-plan-kind")
        if not kind:
            raise AssertionError(f"plan object {key!r} carries no data-plan-kind")
        return kind

    def shape_size_m(self, key: str) -> tuple[float, float]:
        """Width and height of the object's drawn shape in metres (SVG user units).

        One user unit is one metre in this renderer, so ``getBBox`` of the shape
        is the drawn size; used for the "drawn at 2 : 1" check.
        """
        node = self.wait_for_object(key)
        box = self.driver.execute_script(
            "var s = arguments[0].querySelector('.gp-shape');"
            "if (!s) { return null; } var b = s.getBBox(); return [b.width, b.height];",
            node,
        )
        if not box:
            raise AssertionError(f"plan object {key!r} has no drawn shape (.gp-shape)")
        return float(box[0]), float(box[1])

    def shape_origin_m(self, key: str) -> tuple[float, float]:
        """Where the object is drawn: the lower-left corner of its shape, in model metres.

        Read from the rendered SVG (``getBBox``, user units = metres, y negated),
        so it is the position the user sees on the plan — independent of the
        selection and the panel. Rounded to the storage precision (1 mm).
        """
        node = self.wait_for_object(key)
        box = self.driver.execute_script(
            "var s = arguments[0].querySelector('.gp-shape');"
            "if (!s) { return null; } var b = s.getBBox(); return [b.x, b.y, b.height];",
            node,
        )
        if not box:
            raise AssertionError(f"plan object {key!r} has no drawn shape (.gp-shape)")
        return round(float(box[0]), 3), round(-(float(box[1]) + float(box[2])), 3)

    def wait_for_shape_origin(self, key: str, expected: tuple[float, float], what: str) -> None:
        def _at(_d) -> bool:
            x, y = self.shape_origin_m(key)
            return abs(x - expected[0]) < 1e-6 and abs(y - expected[1]) < 1e-6

        try:
            self.poll().until(_at)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: plan object {key!r} should be drawn at {expected}, it is drawn at "
                f"{self.shape_origin_m(key)}"
            ) from exc

    def marker_centres(self, location_key: str) -> list[tuple[float, float]]:
        """Plan positions (metres, y up) of the planting-position markers of a bed.

        The renderer draws a bed's markers as ONE decorative path,
        ``M{x-r} {-y}a…a…`` per marker (``data-plan-markers``); this parses it
        back. Loud when the group is missing — "no markers drawn" must not read
        as "zero positions".
        """
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='garden-plan-svg'] [data-plan-markers='{location_key}'] path",
        )
        try:
            self.poll().until(lambda d: d.find_elements(*locator))
        except TimeoutException as exc:
            raise AssertionError(
                f"no planting-position markers are drawn for bed {location_key!r} "
                "(group [data-plan-markers] missing — zoomed out below the LOD threshold?)"
            ) from exc
        centres: list[tuple[float, float]] = []
        for path in self.driver.find_elements(*locator):
            d = path.get_attribute("d") or ""
            for mx, my, r in re.findall(r"M(-?[\d.]+) (-?[\d.]+)a(-?[\d.]+)", d):
                centres.append((round(float(mx) + float(r), 3), round(-float(my), 3)))
        if not centres:
            raise AssertionError(f"marker path of bed {location_key!r} holds no marker: {d!r}")
        return centres

    # ── Pointer gestures ───────────────────────────────────────────────

    def px_per_m(self) -> float:
        """The current zoom: rendered SVG width over ``viewBox`` width."""
        ratio = self.driver.execute_script(
            "var s = arguments[0]; var vb = s.viewBox.baseVal;"
            "var r = s.getBoundingClientRect();"
            "return vb && vb.width ? r.width / vb.width : null;",
            self.wait_for_element(self.SVG),
        )
        if not ratio:
            raise AssertionError("the plan SVG has no usable viewBox")
        return float(ratio)

    def to_screen(self, x_m: float, y_m: float) -> ScreenPoint:
        """Model metres (y up) -> CSS viewport pixels, through the SVG's viewBox."""
        point = self.driver.execute_script(
            "var s = arguments[0]; var vb = s.viewBox.baseVal;"
            "var r = s.getBoundingClientRect(); var k = r.width / vb.width;"
            "return [r.left + (arguments[1] - vb.x) * k, r.top + (-arguments[2] - vb.y) * k];",
            self.wait_for_element(self.SVG),
            x_m,
            y_m,
        )
        return ScreenPoint(float(point[0]), float(point[1]))

    def object_centre(self, key: str) -> ScreenPoint:
        """The on-screen centre of the object's drawn shape (interior for a rect bed).

        The shape, not the ``<g>``: a selected object's group also holds its
        dimension text above the outline, which would pull the centre upward.
        """
        box = self.driver.execute_script(
            "var s = arguments[0].querySelector('.gp-shape');"
            "if (!s) { return null; } var r = s.getBoundingClientRect();"
            "return [r.left + r.width / 2, r.top + r.height / 2];",
            self.wait_for_object(key),
        )
        if not box:
            raise AssertionError(f"plan object {key!r} has no drawn shape (.gp-shape)")
        return ScreenPoint(float(box[0]), float(box[1]))

    def _require_hit(self, point: ScreenPoint, expected_key: str | None, what: str) -> None:
        """The `elementFromPoint` guard (`e2e-test-stability` §C).

        *expected_key* = the plan object the point must resolve to, ``None`` =
        it must resolve to the plan surface **outside** every plan object
        (drawing starts on empty ground). A miss fails loudly with the full
        element stack at the point.
        """
        found = self.driver.execute_script(
            "var x = arguments[0], y = arguments[1], svg = arguments[2];"
            "var el = document.elementFromPoint(x, y);"
            "if (!el) { return {inside: false, key: null, stack: []}; }"
            "var obj = el.closest('[data-plan-key]');"
            "var stack = document.elementsFromPoint(x, y).slice(0, 6).map(function (e) {"
            "  return e.tagName + (e.getAttribute('data-testid') ? '[' + e.getAttribute('data-testid')"
            "  + ']' : '') + (e.getAttribute('data-plan-key') ? '{' + e.getAttribute('data-plan-key')"
            "  + '}' : ''); });"
            "return {inside: svg.contains(el), key: obj ? obj.getAttribute('data-plan-key') : null,"
            " stack: stack};",
            point.x,
            point.y,
            self.wait_for_element(self.SVG),
        )
        ok = found["inside"] and found["key"] == expected_key
        if not ok:
            target = f"plan object {expected_key!r}" if expected_key else "empty plan surface"
            raise AssertionError(
                f"{what}: the point ({point.x:.1f}, {point.y:.1f}) does not hit the {target}; "
                f"elementFromPoint resolves to key={found['key']!r}, inside plan="
                f"{found['inside']}, stack={found['stack']}"
            )

    def pointer_drag(
        self,
        start: ScreenPoint,
        end: ScreenPoint,
        *,
        alt: bool = False,
        during: Callable[[], None] | None = None,
    ) -> None:
        """Press at *start*, move to *end* in three steps, run *during*, release.

        Two ``perform()`` calls on purpose: W3C input state survives between
        them, so *during* observes the gesture while the button is still down
        (ghost, live dimensions, an Escape that cancels).

        *during* must leave the layout alone: the release lands at the same
        viewport pixels, so a scroll in between (a full-page screenshot does
        that) would end the gesture on another model point. A scroll is
        detected and fails the gesture loudly — use a viewport-only capture
        (``take_screenshot``) for a mid-gesture checkpoint.
        """
        scroll_before = self._scroll_position()
        builder = ActionBuilder(self.driver)
        if alt:
            builder.key_action.key_down(Keys.ALT)
            builder.pointer_action.pause(0)
        builder.pointer_action.move_to_location(round(start.x), round(start.y))
        builder.pointer_action.pointer_down(MouseButton.LEFT)
        for fraction in (0.34, 0.67, 1.0):
            builder.pointer_action.move_to_location(
                round(start.x + (end.x - start.x) * fraction),
                round(start.y + (end.y - start.y) * fraction),
            )
        builder.perform()
        try:
            if during is not None:
                during()
        finally:
            finish = ActionBuilder(self.driver)
            finish.pointer_action.pointer_up(MouseButton.LEFT)
            if alt:
                finish.key_action.pause(0)
                finish.key_action.key_up(Keys.ALT)
            finish.perform()
        scroll_after = self._scroll_position()
        if scroll_after != scroll_before:
            raise AssertionError(
                f"the page scrolled during the gesture ({scroll_before} -> {scroll_after}), so "
                "the release landed on a different plan point than intended"
            )

    def _scroll_position(self) -> tuple[int, int]:
        x, y = self.driver.execute_script("return [window.scrollX, window.scrollY];")
        return int(x), int(y)

    def _bring_canvas_into_view(self) -> None:
        """Centre the canvas in the viewport before any coordinate is computed."""
        self.scroll_into_view(self.wait_for_element(self.CANVAS))

    def drag_object_by(
        self,
        key: str,
        dx_px: int,
        dy_px: int = 0,
        *,
        alt: bool = False,
        during: Callable[[], None] | None = None,
    ) -> None:
        """Drag plan object *key* by whole screen pixels (y down), from its centre."""
        self._bring_canvas_into_view()
        start = self.object_centre(key)
        self._require_hit(start, key, f"dragging {key!r}")
        end = ScreenPoint(start.x + dx_px, start.y + dy_px)
        self.pointer_drag(start, end, alt=alt, during=during)

    def draw_rect(
        self,
        corner_a: tuple[float, float],
        corner_b: tuple[float, float],
        *,
        during: Callable[[], None] | None = None,
    ) -> None:
        """Drag a rectangle between two model points with the active draw tool."""
        self._bring_canvas_into_view()
        start = self.to_screen(*corner_a)
        end = self.to_screen(*corner_b)
        self._require_hit(start, None, "starting a rectangle")
        self.pointer_drag(start, end, during=during)

    def is_ghost_shown(self) -> bool:
        return bool(self.driver.find_elements(*self.GHOST))

    def is_dimension_shown(self) -> bool:
        return any(
            (el.get_attribute("textContent") or "").strip()
            for el in self.driver.find_elements(*self.DIMENSION)
        )

    # ── Toolbar / zoom ─────────────────────────────────────────────────

    def choose_tool(self, locator: tuple[str, str]) -> None:
        """Pick a tool and verify the toggle reports it as pressed."""
        self.wait_and_click(locator)
        try:
            self.poll().until(
                lambda d: d.find_element(*locator).get_attribute("aria-pressed") == "true"
            )
        except TimeoutException as exc:
            raise AssertionError(f"tool {locator[1]} was clicked but is not active") from exc

    def zoom_percent(self) -> int:
        text = (self.wait_for_element(self.ZOOM_LEVEL).get_attribute("textContent") or "").strip()
        match = re.match(r"(\d+)\s*%", text)
        if not match:
            raise AssertionError(f"zoom level reads {text!r}, not 'N %'")
        return int(match.group(1))

    def zoom_to(self, percent: int) -> None:
        """Step the zoom buttons until the zoom level reads *percent* (100 % = 100 px/m)."""
        for _ in range(8):
            current = self.zoom_percent()
            if current == percent:
                return
            self.wait_and_click(self.ZOOM_IN if current < percent else self.ZOOM_OUT)
            self.poll().until(lambda _d, before=current: self.zoom_percent() != before)
        raise AssertionError(f"zoom never reached {percent} % (it reads {self.zoom_percent()} %)")

    # ── Properties panel ───────────────────────────────────────────────

    def _field_locator(self, field_id: str) -> tuple[str, str]:
        return _tid(f"garden-plan-panel-field-{field_id}")

    def panel_field(self, field_id: str) -> float:
        """A numeric panel field (x, y, width, length, rotation) as a float; loud if absent."""
        element = self.wait_for_element(self._field_locator(field_id))
        raw = element.get_attribute("value")
        try:
            return float((raw or "").replace(",", "."))
        except ValueError as exc:
            raise AssertionError(f"panel field {field_id!r} holds no number: {raw!r}") from exc

    def wait_for_panel_field(self, field_id: str, expected: float, what: str) -> None:
        try:
            self.poll().until(lambda _d: abs(self.panel_field(field_id) - expected) < 1e-6)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: panel field {field_id!r} should read {expected}, it reads "
                f"{self.panel_field(field_id)}"
            ) from exc

    def set_panel_field(self, field_id: str, value: float) -> None:
        """Type *value* into a panel field and commit it with Enter (one undo step)."""
        element = self.wait_for_element_clickable(self._field_locator(field_id))
        self.clear_and_fill(element, f"{value:g}")
        element.send_keys(Keys.ENTER)
        self.wait_for_panel_field(field_id, value, f"committing {field_id}={value}")

    def panel_name(self) -> str:
        return self.wait_for_element(self.PANEL_NAME).get_attribute("value") or ""

    def wait_for_panel_empty(self, what: str) -> None:
        self.wait_for_settled({"empty": self.PANEL_EMPTY}, what, require_no_skeleton=False)

    def panel_testids(self) -> set[str]:
        """Every ``data-testid`` inside the properties panel (the panel's hook set)."""
        panel = self.wait_for_element(self.PANEL)
        self.wait_for_element(self.PANEL_FORM)
        ids = self.driver.execute_script(
            "return Array.from(arguments[0].querySelectorAll('[data-testid]'))"
            ".map(function (e) { return e.getAttribute('data-testid'); });",
            panel,
        )
        if not ids:
            raise AssertionError("the properties panel holds no data-testid at all")
        return set(ids)

    # ── Live region ────────────────────────────────────────────────────

    def live_region_text(self) -> str:
        return (self.wait_for_element(self.LIVE_REGION).get_attribute("textContent") or "").strip()

    def wait_for_announcement(self, fragment: str, what: str) -> str:
        try:
            self.poll().until(lambda _d: fragment in self.live_region_text())
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the live region never said {fragment!r}; it says "
                f"{self.live_region_text()!r}"
            ) from exc
        return self.live_region_text()

    # ── List view ──────────────────────────────────────────────────────

    def _switch_list(self, on: bool) -> None:
        switch = self.wait_for_element(self.VIEW_LIST_SWITCH)
        if switch.is_selected() is on:
            raise AssertionError(f"list view switch is already {'on' if on else 'off'}")
        # A checkbox: Space on the focused input is the keyboard activation (§C).
        self.driver.execute_script("arguments[0].focus();", switch)
        self.press(Keys.SPACE)
        target = self.LIST if on else self.SVG
        self.wait_for_element(target)

    def show_list(self) -> None:
        self._switch_list(True)

    def show_plan(self) -> None:
        self._switch_list(False)

    def list_row_button(self, key: str):
        return self.wait_for_element(
            (By.CSS_SELECTOR, f"[data-testid='garden-plan-list'] button[data-list-key='{key}']")
        )

    def list_row_text(self, key: str) -> str:
        return " ".join((self.list_row_button(key).get_attribute("textContent") or "").split())

    def list_keys(self) -> list[str]:
        self.wait_for_element(self.LIST)
        return [
            el.get_attribute("data-list-key")
            for el in self.driver.find_elements(
                By.CSS_SELECTOR, "[data-testid='garden-plan-list'] button[data-list-key]"
            )
        ]

    def is_row_selected(self, key: str) -> bool:
        return self.list_row_button(key).get_attribute("aria-pressed") == "true"

    def active_list_key(self) -> str | None:
        return self.driver.execute_script(
            "var a = document.activeElement;"
            "return a && a.getAttribute ? a.getAttribute('data-list-key') : null;"
        )

    def tab_into_list(self, max_presses: int = 25) -> str:
        """Tab forward from the current focus until a list row has it; return its key.

        Reaching the list by Tab at all — without a focus trap on the way — is
        part of what TC-053-009 asserts, so this fails loudly when it never gets
        there.
        """
        for _ in range(max_presses):
            key = self.active_list_key()
            if key:
                return key
            self.press(Keys.TAB)
        raise AssertionError(f"Tab never reached a list row within {max_presses} presses")

    # ── Leaving the page ───────────────────────────────────────────────

    def click_main_nav(self, path: str) -> None:
        """Click the sidebar entry for *path* — a route change the guard can intercept."""
        self.ensure_sidebar_open()
        locator = (By.CSS_SELECTOR, f"[data-testid='nav-{path}']")
        items = [
            i
            for i in self.driver.find_elements(*locator)
            if self.is_displayed_in_scroll_container(i)
        ]
        if not items:
            raise AssertionError(f"main navigation entry 'nav-{path}' is not displayed")
        self.scroll_and_click(items[0])

    def wait_for_leave_dialog(self, what: str) -> None:
        self.wait_for_settled({"dialog": self.LEAVE_DIALOG}, what, require_no_skeleton=False)

    def cancel_leaving(self) -> None:
        self.wait_and_click(self.LEAVE_CANCEL)
        self.wait_for_element_hidden(self.LEAVE_DIALOG)

    def confirm_leaving(self) -> None:
        self.wait_and_click(self.LEAVE_CONFIRM)
        self.wait_for_element_hidden(self.LEAVE_DIALOG)

    # ── Conflict dialog ────────────────────────────────────────────────

    def wait_for_conflict_dialog(self, what: str) -> None:
        self.wait_for_settled({"conflict": self.CONFLICT_DIALOG}, what, require_no_skeleton=False)

    def conflict_button_text(self, locator: tuple[str, str]) -> str:
        return " ".join((self.wait_for_element(locator).get_attribute("textContent") or "").split())

    def reload_after_conflict(self) -> None:
        if self.pending_count() == 0:
            raise AssertionError("reload_after_conflict(): no unsaved changes to discard")
        self.wait_and_click(self.CONFLICT_RELOAD)
        self.wait_for_element_hidden(self.CONFLICT_DIALOG)
        # Only a fulfilled load replaces `pending`, so 0 after > 0 proves the
        # reload arrived (and not merely that the old editor is still mounted).
        self.wait_for_pending(0, "reloading after the conflict")
        self.wait_for_content(self.EDITOR, "plan editor after the conflict reload")
        self.wait_for_element(self.SVG)

    # ── Wave 7: generic reads ──────────────────────────────────────────

    def text_of(self, locator: tuple[str, str]) -> str:
        """Whitespace-normalised ``textContent`` of *locator*; waits for presence, loud when absent."""
        return " ".join((self.wait_for_element(locator).get_attribute("textContent") or "").split())

    def wait_for_text(self, locator: tuple[str, str], expected: str, what: str) -> str:
        """Wait until *locator* reads exactly *expected* (whitespace-normalised)."""
        try:
            self.poll().until(lambda _d: self.text_of(locator) == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: expected {locator[1]} to read {expected!r}, it reads {self.text_of(locator)!r}"
            ) from exc
        return expected

    def object_keys(self) -> list[str]:
        """Keys of every focusable bed and garden object drawn, in DOM order (the boundary left out).

        The SVG must be there; the boundary is a focusable plan object too, but
        never a copy, a selection target of Ctrl+A or a bed.
        """
        svg = self.wait_for_element(self.SVG)
        return self.driver.execute_script(
            "return Array.from(arguments[0].querySelectorAll(\"[data-plan-key][role='button']\"))"
            ".filter(function (e) { return e.getAttribute('data-plan-kind') !== 'boundary'; })"
            ".map(function (e) { return e.getAttribute('data-plan-key'); });",
            svg,
        )

    def select_all_with_keyboard(self, expected: set[str]) -> None:
        """Ctrl+A on the canvas selects every unlocked bed and object (GP-UX-037); verified per key."""
        if not expected:
            raise AssertionError(
                "select_all_with_keyboard(): name the objects that must end up selected"
            )
        self.focus_canvas()
        self.press(Keys.CONTROL, "a")
        for key in sorted(expected):
            self.wait_for_selected(key, True, "Ctrl+A")

    # ── Wave 7: layers (GP-FR-031) ─────────────────────────────────────

    def _layer_toggle(self, layer_id: str) -> tuple[str, str]:
        return _tid(f"garden-plan-layer-{layer_id}")

    def is_layer_on(self, layer_id: str) -> bool:
        pressed = self.wait_for_element(self._layer_toggle(layer_id)).get_attribute("aria-pressed")
        if pressed not in ("true", "false"):
            raise AssertionError(f"layer toggle {layer_id!r} carries no aria-pressed: {pressed!r}")
        return pressed == "true"

    def set_layer(self, layer_id: str, visible: bool) -> None:
        """Switch a layer with the keyboard (focus + Space on the toggle button) and verify it flipped."""
        if self.is_layer_on(layer_id) is visible:
            raise AssertionError(
                f"layer {layer_id!r} is already {'on' if visible else 'off'}; the test expected to switch it"
            )
        toggle = self.wait_for_element(self._layer_toggle(layer_id))
        self.driver.execute_script("arguments[0].focus();", toggle)
        self.press(Keys.SPACE)
        try:
            self.poll().until(lambda _d: self.is_layer_on(layer_id) is visible)
        except TimeoutException as exc:
            raise AssertionError(
                f"layer {layer_id!r} did not switch {'on' if visible else 'off'}"
            ) from exc

    def zone_layer_beds(self, zone_key: str) -> set[str]:
        """The beds the zone layer hatches for *zone_key*; loud when the layer is not drawn at all."""
        layer = self.wait_for_element(self.ZONE_LAYER)
        keys = self.driver.execute_script(
            "var zone = arguments[1];"
            "return Array.from(arguments[0].querySelectorAll('[data-zone-key]'))"
            ".filter(function (g) { return g.getAttribute('data-zone-key') === zone; })"
            ".map(function (g) { return g.getAttribute('data-zone-bed'); });",
            layer,
            zone_key,
        )
        return set(keys)

    def wait_for_zone_layer_beds(self, zone_key: str, expected: set[str], what: str) -> None:
        try:
            self.poll().until(lambda _d: self.zone_layer_beds(zone_key) == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the zone layer should hatch {sorted(expected)} for zone {zone_key!r}, it "
                f"hatches {sorted(self.zone_layer_beds(zone_key))}"
            ) from exc

    def watered_layer(self) -> dict[str, tuple[str, str]]:
        """Bed key -> (class, label) of the last-watered layer; loud when the layer is not drawn."""
        layer = self.wait_for_element(self.WATERED_LAYER)
        rows = self.driver.execute_script(
            "return Array.from(arguments[0].querySelectorAll('[data-watered-bed]')).map(function (g) {"
            "  var t = g.querySelector('text');"
            "  return [g.getAttribute('data-watered-bed'), g.getAttribute('data-watered-class'),"
            "          t ? t.textContent : null]; });",
            layer,
        )
        result: dict[str, tuple[str, str]] = {}
        for bed, klass, label in rows:
            if not klass or label is None:
                raise AssertionError(
                    f"last-watered entry of bed {bed!r} lacks its class or label: "
                    f"class={klass!r}, label={label!r} (zoomed below the label LOD?)"
                )
            result[bed] = (klass, " ".join(label.split()))
        return result

    def wait_for_watered_layer(self, expected: dict[str, tuple[str, str]], what: str) -> None:
        try:
            self.poll().until(lambda _d: self.watered_layer() == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the last-watered layer should draw {expected}, it draws {self.watered_layer()}"
            ) from exc

    # ── Wave 7: irrigation zones (GP-FR-110 / 117) ─────────────────────

    def open_zone_panel(self) -> None:
        """Open the zone panel (its own lazy chunk) and return once it rendered."""
        self.wait_and_click(self.ZONES_OPEN)
        self.wait_for_settled({"panel": self.ZONE_PANEL}, "zone panel", require_no_skeleton=False)
        expanded = self.wait_for_element(self.ZONES_OPEN).get_attribute("aria-expanded")
        if expanded != "true":
            raise AssertionError(
                f"the zone panel rendered, but its button says aria-expanded={expanded!r}"
            )

    def start_new_zone(self, name: str) -> None:
        self.wait_and_click(self.ZONE_NEW)
        self.wait_for_element(self.ZONE_FORM)
        self.clear_and_fill(self.wait_for_element_clickable(self.ZONE_NAME), name)

    def zone_form_beds(self) -> dict[str, bool]:
        """Bed key -> ticked, for every bed checkbox of the zone form; loud when the form lists none."""
        form = self.wait_for_element(self.ZONE_FORM)
        boxes = self.driver.execute_script(
            "return Array.from(arguments[0].querySelectorAll(\"input[data-testid^='garden-plan-zone-bed-']\"))"
            ".map(function (i) { return [i.getAttribute('data-testid'), i.checked]; });",
            form,
        )
        if not boxes:
            raise AssertionError("the zone form lists no bed checkbox at all")
        prefix = "garden-plan-zone-bed-"
        return {testid[len(prefix) :]: bool(checked) for testid, checked in boxes}

    def take_selection_into_zone(self, expected: set[str]) -> None:
        """'Auswahl vom Plan übernehmen' and verify exactly *expected* beds are ticked afterwards."""
        self.wait_and_click(self.ZONE_TAKE_SELECTION)
        try:
            self.poll().until(
                lambda _d: {k for k, on in self.zone_form_beds().items() if on} == expected
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"taking the plan selection should tick {sorted(expected)}, the form ticks "
                f"{sorted(k for k, on in self.zone_form_beds().items() if on)}"
            ) from exc

    def set_zone_bed(self, bed_key: str, ticked: bool) -> None:
        """Tick or untick a bed of the zone form with the keyboard (focus + Space on the checkbox)."""
        box = self.wait_for_element(_tid(f"garden-plan-zone-bed-{bed_key}"))
        if box.is_selected() is ticked:
            raise AssertionError(f"bed {bed_key!r} is already {'ticked' if ticked else 'unticked'}")
        self.driver.execute_script("arguments[0].focus();", box)
        self.press(Keys.SPACE)
        try:
            self.poll().until(lambda _d: self.zone_form_beds().get(bed_key) is ticked)
        except TimeoutException as exc:
            raise AssertionError(
                f"the checkbox of bed {bed_key!r} did not flip to {ticked}"
            ) from exc

    def save_zone(self) -> None:
        """'Zone speichern'; returns once the panel shows the stored zone's status.

        The status section only renders for a zone whose full record the zone
        endpoint returned after the write, so its presence is server-confirmed.
        """
        self.wait_and_click(self.ZONE_SAVE)
        self.wait_for_settled({"status": self.ZONE_STATUS}, "saved zone", require_no_skeleton=False)
        self.wait_for_element(self.ZONE_LAST_WATERING)

    def zone_row(self, zone_key: str) -> tuple[str, str]:
        return _tid(f"garden-plan-zone-row-{zone_key}")

    def open_zone(self, zone_key: str) -> None:
        """Open a zone from the list; return once its status has loaded."""
        self.wait_and_click(self.zone_row(zone_key))
        self.wait_for_element(self.ZONE_LAST_WATERING)

    def open_watering_round(self) -> None:
        self.wait_and_click(self.ROUND_OPEN)
        self.wait_for_element(self.ROUND_DIALOG)
        self.wait_for_element(self.ROUND_VOLUME)

    def choose_round_allocation(self, allocation: str) -> None:
        """Pick a radio of the round dialog with the keyboard and verify it is checked."""
        radio = self.wait_for_element(_tid(f"garden-plan-round-allocation-{allocation}"))
        if not radio.is_selected():
            self.driver.execute_script("arguments[0].focus();", radio)
            self.press(Keys.SPACE)
        try:
            self.poll().until(
                lambda d: d.find_element(
                    *_tid(f"garden-plan-round-allocation-{allocation}")
                ).is_selected()
            )
        except TimeoutException as exc:
            raise AssertionError(f"the allocation {allocation!r} is not checked") from exc

    def submit_watering_round(self, volume_liters: str, summary: str) -> list[str]:
        """Fill the total and the note, submit; return the per-bed share lines of the server's answer.

        The result view replaces the form only when the server answered the
        round (``setResult`` in the request's ``then``), so it is a durable signal.
        """
        self.clear_and_fill(self.wait_for_element_clickable(self.ROUND_VOLUME), volume_liters)
        self.clear_and_fill(self.wait_for_element_clickable(self.ROUND_SUMMARY), summary)
        self.wait_and_click(self.ROUND_SUBMIT)
        result = self.wait_for_settled(
            {"result": self.ROUND_RESULT}, "watering round answer", require_no_skeleton=False
        )
        lines = self.driver.execute_script(
            "return Array.from(arguments[0].querySelectorAll('li')).map(function (l) { return l.textContent; });",
            self.wait_for_element(result.locator),
        )
        if not lines:
            raise AssertionError("the round's result lists no bed share at all")
        return [" ".join(line.split()) for line in lines]

    def close_watering_round(self) -> None:
        self.wait_and_click(self.ROUND_DONE)
        self.wait_for_element_hidden(self.ROUND_DIALOG)

    # ── Wave 7: bed templates and standard sizes (GP-FR-044 / 045) ────

    def pick_template(self, template_key: str) -> None:
        """Open the template tool, choose *template_key* in its picker; verify the hint asks for placing."""
        self.choose_tool(self.TOOL_TEMPLATE)
        self.wait_for_element(self.TEMPLATE_PANEL)
        self.open_select_in("[data-testid='garden-plan-template-panel']", "template picker")
        self.select_option_by_value(template_key)

    def place_template_at_centre(self, placed_text: str) -> None:
        """'In die Bildmitte setzen'; returns once the editor reports the bed as created and saved.

        ``placed_text`` is shown only after the server placed the bed AND the
        plan was read again (``placeTemplateAt`` fulfilled with ``ok``).
        """
        button = self.wait_for_element(self.TEMPLATE_PLACE_CENTRE)
        if button.get_attribute("aria-disabled") == "true":
            raise AssertionError("'In die Bildmitte setzen' is disabled: no template picked")
        self.wait_and_click(self.TEMPLATE_PLACE_CENTRE)
        state = self.wait_for_settled(
            {"info": self.INFO, "notice": self.NOTICE},
            "placing a template",
            require_no_skeleton=False,
        )
        if state.branch != "info":
            raise AssertionError(f"placing the template was refused: {self.text_of(self.NOTICE)!r}")
        self.wait_for_text(self.INFO, placed_text, "placing a template")

    def open_add_with_dimensions(self) -> None:
        self.wait_and_click(self.ADD_WITH_DIMENSIONS)
        self.wait_for_element(self.ADD_DIALOG)

    def pick_standard_size(self, template_key: str) -> None:
        """Press a standard-size button of the dialog (its catalogue loads with the dialog)."""
        self.wait_for_settled(
            {"sizes": self.ADD_STANDARD_SIZES}, "standard sizes", require_no_skeleton=False
        )
        self.wait_and_click(_tid(f"garden-plan-add-standard-{template_key}"))

    def add_field(self, field_id: str) -> str:
        return (
            self.wait_for_element(_tid(f"garden-plan-add-{field_id}")).get_attribute("value") or ""
        )

    def set_add_field(self, field_id: str, value: str) -> None:
        element = self.wait_for_element_clickable(_tid(f"garden-plan-add-{field_id}"))
        self.clear_and_fill(element, value)
        if self.add_field(field_id) != value:
            raise AssertionError(
                f"add field {field_id!r} reads {self.add_field(field_id)!r}, not {value!r}"
            )

    def add_bed_type(self) -> str:
        """The committed value of the dialog's bed-type select (its hidden native input)."""
        return self.wait_for_element(self.ADD_BED_TYPE).get_attribute("value") or ""

    def submit_add_dialog(self) -> None:
        self.wait_and_click(self.ADD_SUBMIT)
        self.wait_for_element_hidden(self.ADD_DIALOG)

    # ── Wave 7: align / distribute, multi-duplicate (GP-FR-029 / 025) ─

    def _open_menu(self, trigger: tuple[str, str], opened: tuple[str, str], what: str) -> None:
        """Click a menu button and verify the menu opened (*opened* is present), or fail loudly."""
        self.wait_and_click(trigger)
        try:
            self.poll().until(lambda d: d.find_elements(*opened))
        except TimeoutException as exc:
            raise AssertionError(f"{what} did not open ({opened[1]} never appeared)") from exc

    def align(self, mode: str) -> None:
        """'Ausrichten' -> *mode* (left/right/top/bottom/centerH/centerV or distribute-<axis>)."""
        if not self.wait_for_element(self.ALIGN_BUTTON).is_enabled():
            raise AssertionError(
                "'Ausrichten' is disabled: fewer than two movable objects are selected"
            )
        item_id = mode if mode.startswith("distribute-") else f"align-{mode}"
        self._open_menu(self.ALIGN_BUTTON, _tid(f"garden-plan-{item_id}"), "the align menu")
        item = self.wait_for_element_clickable(_tid(f"garden-plan-{item_id}"))
        self.click_menu_option(item)
        self.wait_for_element_hidden(_tid(f"garden-plan-{item_id}"))

    def open_multi_duplicate(self) -> None:
        """'Mehr' -> 'Mehrfach duplizieren'; returns once the dialog shows its form."""
        self._open_menu(self.OVERFLOW, self.OVERFLOW_MENU, "the overflow menu")
        item = self.wait_for_element_clickable(
            (
                By.CSS_SELECTOR,
                "[data-testid='garden-plan-overflow-menu'] [data-testid='garden-plan-menu-multiDuplicate']",
            )
        )
        if item.get_attribute("aria-disabled") == "true":
            raise AssertionError("'Mehrfach duplizieren' is disabled: nothing is selected")
        self.click_menu_option(item)
        self.wait_for_element(self.MULTI_DIALOG)
        self.wait_for_element(_tid("garden-plan-multi-count"))

    def set_multi_field(self, field_id: str, value: str) -> None:
        element = self.wait_for_element_clickable(_tid(f"garden-plan-multi-{field_id}"))
        self.clear_and_fill(element, value)
        actual = element.get_attribute("value")
        if actual != value:
            raise AssertionError(
                f"multi-duplicate field {field_id!r} reads {actual!r}, not {value!r}"
            )

    def submit_multi_duplicate(self) -> None:
        self.wait_and_click(self.MULTI_SUBMIT)
        self.wait_for_element_hidden(self.MULTI_DIALOG)

    # ── Wave 7: snap marker, auto-save, mini-map (GP-FR-012, GP-UX-004/014) ─

    def snap_marker_kind(self) -> str | None:
        """The kind of the snap marker drawn right now (``corner``/``edge``/``grid``), ``None`` if none."""
        markers = self.driver.find_elements(*self.SNAP_MARKER)
        return markers[0].get_attribute("data-kind") if markers else None

    def is_autosave_on(self) -> bool:
        return self.wait_for_element(self.AUTOSAVE).is_selected()

    def enable_autosave(self) -> None:
        """Switch auto-save on with the keyboard (focus + Space on the switch input) and verify it."""
        if self.is_autosave_on():
            raise AssertionError(
                "auto-save is already on; a fresh browser session starts with it off"
            )
        switch = self.wait_for_element(self.AUTOSAVE)
        self.driver.execute_script("arguments[0].focus();", switch)
        self.press(Keys.SPACE)
        try:
            self.poll().until(lambda _d: self.is_autosave_on())
        except TimeoutException as exc:
            raise AssertionError("the auto-save switch did not turn on") from exc

    def minimap_viewport_centre(self) -> tuple[float, float]:
        """Centre of the viewport rectangle inside the 120 x 120 px mini-map drawing (its own pixels)."""
        rect = self.wait_for_element(self.MINIMAP_VIEWPORT)
        values = [rect.get_attribute(name) for name in ("x", "y", "width", "height")]
        try:
            x, y, w, h = (float(v) for v in values)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise AssertionError(
                f"mini-map viewport rectangle has no numeric geometry: {values}"
            ) from exc
        return round(x + w / 2, 1), round(y + h / 2, 1)

    def wait_for_minimap_shift_right(
        self, start: tuple[float, float], min_px: float, what: str
    ) -> None:
        """Wait until the viewport rectangle sits at least *min_px* right of *start* (a pan to the right)."""
        try:
            self.poll().until(lambda _d: self.minimap_viewport_centre()[0] - start[0] >= min_px)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the mini-map's viewport rectangle should move >= {min_px} px right; "
                f"{start} -> {self.minimap_viewport_centre()}"
            ) from exc

    def wait_for_minimap_centred(self, tolerance_px: float, what: str) -> None:
        """Wait until the viewport rectangle is centred in the 120 px drawing (within *tolerance_px*)."""
        middle = 120 / 2
        try:
            self.poll().until(
                lambda _d: all(
                    abs(c - middle) <= tolerance_px for c in self.minimap_viewport_centre()
                )
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the mini-map's viewport rectangle should be centred at ({middle}, {middle}), "
                f"its centre is {self.minimap_viewport_centre()}"
            ) from exc

    def click_minimap_centre(self) -> None:
        """Click the middle of the mini-map with a real pointer.

        The mini-map is a pointer-only shortcut (``role="img"``, out of the tab
        order, no keyboard path by design) and an inert target: its only
        children are an ``aria-hidden`` SVG drawing, so the descendant-tolerant
        native click cannot land on another control. Its ``onClick`` reads the
        event's coordinates, so a script click (``clientX = 0``) would jump to a
        wrong place - the native click is the only sound activation here; an
        interception raises instead of falling back.
        """
        minimap = self.wait_for_element_visible(self.MINIMAP)
        centre = self.driver.execute_script(
            "var r = arguments[0].getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2];",
            minimap,
        )
        hit = self.driver.execute_script(
            "var el = document.elementFromPoint(arguments[0], arguments[1]);"
            "return !!el && arguments[2].contains(el);",
            centre[0],
            centre[1],
            minimap,
        )
        if not hit:
            raise AssertionError(
                f"the centre of the mini-map {centre} is covered by another element"
            )
        minimap.click()

    # ── Wave 7 part B (WP 7.26): IO menu, season, export, import, snapshots ──
    #
    # The dialogs are the lazy chunks of ``io/`` and ``season/`` (``PlanIoMenu``);
    # every hook below is a ``data-testid`` of those files. Radios are switched with
    # the keyboard (focus + Space on the native input: MUI draws it at opacity 0
    # over the control, so it is the element that receives the activation, and
    # Space is its own activation key); a Select opens on mousedown only (MUI 9),
    # so it goes through ``dispatch_menu_trigger_open``.

    IO_MENU = _tid("garden-plan-io-menu")
    IO_EXPORT = _tid("garden-plan-io-export")
    IO_IMPORT = _tid("garden-plan-io-import")
    IO_SEASON = _tid("garden-plan-io-season")

    SEASON_DIALOG = _tid("plan-season-dialog")
    SEASON_YEAR = _tid("plan-season-year")
    SEASON_CHECK = _tid("plan-season-check")
    SEASON_CONFIRM = _tid("plan-season-confirm")
    SEASON_REPORT = _tid("plan-season-report")
    SEASON_DONE = _tid("plan-season-done")
    SEASON_FAILURE = _tid("plan-season-failure")
    #: The first action of a plan dialog is its close/cancel button (the dialogs give it no test id).
    SEASON_CLOSE = (
        By.CSS_SELECTOR,
        "[data-testid='plan-season-dialog'] .MuiDialogActions-root button:first-of-type",
    )

    EXPORT_DIALOG = _tid("plan-export-dialog")
    EXPORT_FORMAT_JSON = _tid("plan-export-format-json")
    EXPORT_SCOPE_HINT = _tid("plan-export-scope-hint")
    EXPORT_JSON_SUMMARY = _tid("plan-export-json-summary")
    EXPORT_DOWNLOAD = _tid("plan-export-download")
    EXPORT_ERROR = _tid("plan-export-error")

    IMPORT_WIZARD = _tid("plan-import-wizard")
    IMPORT_FILE = _tid("plan-import-file")
    IMPORT_FILE_ERROR = _tid("plan-import-file-error")
    IMPORT_REPORT = _tid("plan-import-report")
    IMPORT_OK = _tid("plan-import-ok")
    IMPORT_NEXT = _tid("plan-import-next")
    IMPORT_TARGET = _tid("plan-import-target")
    IMPORT_CHECK = _tid("plan-import-check")
    IMPORT_APPLY = _tid("plan-import-apply")
    IMPORT_DONE = _tid("plan-import-done")
    IMPORT_CLOSE = _tid("plan-import-close")
    IMPORT_FAILURE = _tid("plan-import-failure")
    IMPORT_SNAPSHOTS = _tid("plan-import-snapshots")

    SNAPSHOTS = _tid("plan-snapshots")
    SNAPSHOTS_EMPTY = _tid("plan-snapshots-empty")
    SNAPSHOTS_NOTICE = _tid("plan-snapshots-notice")
    SNAPSHOTS_CONFIRM_NAME = _tid("plan-snapshots-confirm-name")
    SNAPSHOTS_RESTORE = _tid("plan-snapshots-restore")
    SNAPSHOTS_FAILURE = _tid("plan-snapshots-failure")
    SNAPSHOTS_REPORT = (
        By.CSS_SELECTOR,
        "[data-testid='plan-snapshots'] [data-testid='plan-import-report']",
    )

    # ── Underlay (GP-FR-033) ───────────────────────────────────────────
    UNDERLAY_OPEN = _tid("garden-plan-underlay-open")
    UNDERLAY_DIALOG = _tid("garden-plan-underlay-dialog")
    UNDERLAY_FILE = _tid("underlay-file")
    UNDERLAY_IMAGE = (By.CSS_SELECTOR, "[data-testid='underlay-picture'] img")
    UNDERLAY_SCALE = _tid("underlay-scale")
    UNDERLAY_SAVE = _tid("underlay-save")
    UNDERLAY_ERROR = _tid("underlay-error")
    UNDERLAY_DRAWN = (By.CSS_SELECTOR, "[data-testid='garden-plan-svg'] [data-plan-underlay] image")

    # ── Plant-state and condition layers (GP-UX-061, GP-FR-169) ─────────
    ATTENTION_FILTER = _tid("garden-plan-attention-filter")
    LEGEND_PLANT_STATE = _tid("garden-plan-legend-plantState")
    SUN_LAYER = _tid("garden-plan-sun-layer")

    # ── Generic dialog plumbing ────────────────────────────────────────

    def _open_io_entry(self, entry: tuple[str, str], dialog: tuple[str, str], what: str) -> None:
        """'Export & Import' -> *entry*; return once *dialog* (a lazy chunk) is on screen."""
        self._open_menu(self.IO_MENU, entry, "the 'Export & Import' menu")
        item = self.wait_for_element(entry)
        if item.get_attribute("aria-disabled") == "true":
            reason = " ".join((item.get_attribute("textContent") or "").split())
            raise AssertionError(f"{what}: the menu entry is disabled ({reason!r})")
        self.click_menu_option(item)
        try:
            self.wait_for_element_visible(dialog)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the dialog {dialog[1]} did not open") from exc

    def _type_into(self, locator: tuple[str, str], text: str) -> None:
        """Replace the value of a controlled text input with *text* and verify the input holds it."""
        field = self.wait_for_element(locator)
        self.scroll_into_view(field)
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(text)
        try:
            self.poll().until(lambda _d: field.get_attribute("value") == text)
        except TimeoutException as exc:
            raise AssertionError(
                f"the input {locator[1]} should hold {text!r}, it holds {field.get_attribute('value')!r}"
            ) from exc

    def _choose_radio(self, locator: tuple[str, str]) -> None:
        """Check a native radio with the keyboard (focus + Space) and verify it is checked."""
        radio = self.wait_for_element(locator)
        if not radio.is_enabled():
            raise AssertionError(f"the radio {locator[1]} is disabled")
        self.driver.execute_script("arguments[0].focus();", radio)
        if not self.driver.execute_script("return document.activeElement === arguments[0];", radio):
            raise AssertionError(f"the radio {locator[1]} did not take the focus")
        self.press(Keys.SPACE)
        try:
            self.poll().until(lambda _d: radio.is_selected())
        except TimeoutException as exc:
            raise AssertionError(f"the radio {locator[1]} is not checked after Space") from exc

    def _unhide_file_input(self, locator: tuple[str, str]):
        """A ``hidden`` file input made sendable (the import page's pattern); the file is then sent, not clicked."""
        file_input = self.find_present(locator)
        self.driver.execute_script(
            "arguments[0].removeAttribute('hidden');"
            "arguments[0].style.display = 'block';"
            "arguments[0].style.width = '1px';"
            "arguments[0].style.height = '1px';"
            "arguments[0].style.opacity = '0.01';",
            file_input,
        )
        return file_input

    def _lines(self, css: str) -> list[str]:
        return [
            " ".join((el.get_attribute("textContent") or "").split())
            for el in self.driver.find_elements(By.CSS_SELECTOR, css)
        ]

    # ── New season (GP-FR-171) ─────────────────────────────────────────

    def open_new_season(self) -> None:
        self._open_io_entry(self.IO_SEASON, self.SEASON_DIALOG, "new season")

    def check_new_season(self, year: int) -> str:
        """Type the season *year*, press 'Prüfen'; return the report title once the server's dry run answered."""
        self._type_into(self.SEASON_YEAR, str(year))
        self.wait_and_click(self.SEASON_CHECK)
        title_css = "[data-testid='plan-season-report'] h3"

        def _report() -> str | bool:
            if self.is_present(self.SEASON_FAILURE):
                raise AssertionError(
                    f"new season check failed: {self.text_of(self.SEASON_FAILURE)!r}"
                )
            titles = self._lines(title_css)
            return titles[0] if titles and f"für {year}" in titles[0] else False

        try:
            return self.poll().until(lambda _d: _report())
        except TimeoutException as exc:
            raise AssertionError(f"the new-season report for {year} never appeared") from exc

    def season_report_text(self) -> str:
        return self.text_of(self.SEASON_REPORT)

    def season_report_rows(self) -> list[str]:
        """The per-bed lines of the report (``Beet A: 2 freie Slots``)."""
        return self._lines("[data-testid='plan-season-report'] li .MuiListItemText-primary")

    def confirm_new_season(self) -> str:
        """'Freie Slots anlegen'; return the success line once the server wrote the slots."""
        button = self.wait_for_element_clickable(self.SEASON_CONFIRM)
        self.scroll_and_click(button)

        def _done() -> str | bool:
            if self.is_present(self.SEASON_FAILURE):
                raise AssertionError(f"new season failed: {self.text_of(self.SEASON_FAILURE)!r}")
            return self.text_of(self.SEASON_DONE) if self.is_present(self.SEASON_DONE) else False

        try:
            return self.poll().until(lambda _d: _done())
        except TimeoutException as exc:
            raise AssertionError("the new season was never confirmed as written") from exc

    def close_new_season(self) -> None:
        self.wait_and_click(self.SEASON_CLOSE)
        self.wait_for_element_hidden(self.SEASON_DIALOG)

    # ── Plan selection by marquee (GP-UX-037) ──────────────────────────

    def marquee_select(
        self, corner_a: tuple[float, float], corner_b: tuple[float, float], expected: set[str]
    ) -> None:
        """Drag a selection frame between two model points on empty ground; verify exactly *expected* is selected.

        A frame selects the beds and objects fully inside it (``selectMachine``). Both corners
        are checked with ``elementFromPoint`` to lie on the empty plan surface, so the press
        starts a frame and not the drag of an object.
        """
        self.choose_tool(self.TOOL_SELECT)
        self._bring_canvas_into_view()
        start = self.to_screen(*corner_a)
        end = self.to_screen(*corner_b)
        self._require_hit(start, None, "starting the selection frame")
        self._require_hit(end, None, "ending the selection frame")
        self.pointer_drag(start, end)
        keys = self.object_keys()
        try:
            self.poll().until(lambda _d: {k for k in keys if self.is_selected(k)} == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"the selection frame should select exactly {sorted(expected)}, selected are "
                f"{sorted(k for k in keys if self.is_selected(k))}"
            ) from exc

    # ── Export (GP-UX-050, GP-FR-172) ──────────────────────────────────

    def open_export(self) -> None:
        self._open_io_entry(self.IO_EXPORT, self.EXPORT_DIALOG, "export")

    def choose_export_json(self) -> None:
        self.wait_and_click(self.EXPORT_FORMAT_JSON)
        try:
            self.poll().until(
                lambda d: (
                    d.find_element(*self.EXPORT_FORMAT_JSON).get_attribute("aria-pressed") == "true"
                )
            )
        except TimeoutException as exc:
            raise AssertionError("the export format 'JSON' did not become active") from exc

    def choose_export_scope(self, scope: str) -> None:
        self._choose_radio(_tid(f"plan-export-scope-{scope}"))

    def wait_for_export_summary(self, fragment: str, what: str) -> str:
        """Wait for the JSON preview (one export request per settled option) to contain *fragment*."""

        def _summary() -> str | bool:
            if self.is_present(self.EXPORT_ERROR):
                raise AssertionError(
                    f"{what}: the export dialog reports {self.text_of(self.EXPORT_ERROR)!r}"
                )
            if not self.is_present(self.EXPORT_JSON_SUMMARY):
                return False
            text = self.text_of(self.EXPORT_JSON_SUMMARY)
            return text if fragment in text else False

        try:
            return self.poll().until(lambda _d: _summary())
        except TimeoutException as exc:
            shown = (
                self.text_of(self.EXPORT_JSON_SUMMARY)
                if self.is_present(self.EXPORT_JSON_SUMMARY)
                else None
            )
            raise AssertionError(
                f"{what}: the preview should name {fragment!r}, it reads {shown!r}"
            ) from exc

    def download_export(self) -> None:
        """'Herunterladen'; the dialog closes only after the export request succeeded (``onClose`` in the try)."""
        self.wait_and_click(self.EXPORT_DOWNLOAD)
        try:
            self.wait_for_element_hidden(self.EXPORT_DIALOG)
        except TimeoutException as exc:
            error = self.text_of(self.EXPORT_ERROR) if self.is_present(self.EXPORT_ERROR) else None
            raise AssertionError(
                f"the export dialog did not close after the download (error: {error!r})"
            ) from exc

    # ── Import (GP-UX-051, GP-API-005) ─────────────────────────────────

    def open_import(self) -> None:
        self._open_io_entry(self.IO_IMPORT, self.IMPORT_WIZARD, "import")

    def choose_import_file(self, path: str) -> None:
        """Hand the backup file to the wizard; return once the server's check report is shown."""
        self._unhide_file_input(self.IMPORT_FILE).send_keys(path)

        def _report() -> bool:
            for failure in (self.IMPORT_FILE_ERROR, self.IMPORT_FAILURE):
                if self.is_present(failure):
                    raise AssertionError(
                        f"the import of {path!r} was refused: {self.text_of(failure)!r}"
                    )
            return self.is_present(self.IMPORT_REPORT)

        try:
            self.poll().until(lambda _d: _report())
        except TimeoutException as exc:
            raise AssertionError(f"no check report appeared for {path!r}") from exc

    def import_report_counts(self) -> list[str]:
        """The count lines of the check report (``Wird angelegt: 2 Standorte, ...``)."""
        return self._lines("[data-testid='plan-import-report'] > div:first-child > p")

    def import_next(self) -> None:
        self.wait_and_click(self.IMPORT_NEXT)
        self.wait_for_element(_tid("plan-import-mode-merge"))

    def choose_import_mode(self, mode: str) -> None:
        self._choose_radio(_tid(f"plan-import-mode-{mode}"))

    def choose_import_target(self, target: str) -> None:
        """Pick the import target in its Select (opens on mousedown); verified on the native input."""
        native = self.wait_for_element(self.IMPORT_TARGET)
        if native.get_attribute("value") == target:
            raise AssertionError(
                f"the import target is already {target!r}; the test expected to change it"
            )
        trigger = self.driver.execute_script(
            "return arguments[0].closest('.MuiInputBase-root').querySelector(\"[role='combobox']\");",
            native,
        )
        if trigger is None:
            raise AssertionError("the import target select has no combobox")
        self.dispatch_menu_trigger_open(trigger)
        self._settle_listbox()
        self.select_option_by_value(target)
        try:
            self.poll().until(lambda _d: native.get_attribute("value") == target)
        except TimeoutException as exc:
            raise AssertionError(f"the import target did not become {target!r}") from exc

    def target_hint(self) -> str:
        """The helper text under the target select (it explains what the target means)."""
        native = self.wait_for_element(self.IMPORT_TARGET)
        return (
            self.driver.execute_script(
                "var root = arguments[0].closest('.MuiFormControl-root');"
                "var help = root ? root.querySelector('.MuiFormHelperText-root') : null;"
                "return help ? help.textContent.replace(/\\s+/g, ' ').trim() : null;",
                native,
            )
            or ""
        )

    def recheck_import(self) -> None:
        """'Erneut prüfen' after a changed mode or target; return once the apply button replaced it."""
        self.wait_and_click(self.IMPORT_CHECK)

        def _checked() -> bool:
            if self.is_present(self.IMPORT_FAILURE):
                raise AssertionError(f"the re-check failed: {self.text_of(self.IMPORT_FAILURE)!r}")
            return self.is_present(self.IMPORT_APPLY)

        try:
            self.poll().until(lambda _d: _checked())
        except TimeoutException as exc:
            raise AssertionError("the import was never re-checked") from exc

    def apply_import(self) -> str:
        """Press the apply button; return the success line once the server wrote the import."""
        self.wait_and_click(self.IMPORT_APPLY)
        return self._wait_for_import_done("the import")

    def _wait_for_import_done(self, what: str) -> str:
        def _done() -> str | bool:
            for failure in (self.IMPORT_FAILURE, self.SNAPSHOTS_FAILURE):
                if self.is_present(failure):
                    raise AssertionError(f"{what} failed: {self.text_of(failure)!r}")
            return self.text_of(self.IMPORT_DONE) if self.is_present(self.IMPORT_DONE) else False

        try:
            return self.poll().until(lambda _d: _done())
        except TimeoutException as exc:
            raise AssertionError(f"{what} was never confirmed as written") from exc

    def close_import(self) -> None:
        self.wait_and_click(self.IMPORT_CLOSE)
        self.wait_for_element_hidden(self.IMPORT_WIZARD)

    # ── Snapshots (GP-FR-148/170) ──────────────────────────────────────

    def open_snapshots(self) -> None:
        """'Früheren Stand wiederherstellen …' in the import wizard; return once the list (or its empty note) loaded."""
        self.wait_and_click(self.IMPORT_SNAPSHOTS)
        self.wait_for_element(self.SNAPSHOTS)
        try:
            self.poll().until(
                lambda d: (
                    d.find_elements(
                        By.CSS_SELECTOR,
                        "[data-testid^='plan-snapshot-']:not([data-testid^='plan-snapshots'])",
                    )
                    or self.is_present(self.SNAPSHOTS_EMPTY)
                    or self.is_present(_tid("plan-snapshots-error"))
                )
            )
        except TimeoutException as exc:
            raise AssertionError("the list of earlier states never loaded") from exc
        if self.is_present(_tid("plan-snapshots-error")):
            raise AssertionError(
                f"the snapshot list failed: {self.text_of(_tid('plan-snapshots-error'))!r}"
            )

    def snapshot_rows(self) -> dict[str, str]:
        """audit key -> row text of every listed earlier state."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='plan-snapshot-']:not([data-testid^='plan-snapshots'])"
        )
        return {
            (row.get_attribute("data-testid") or "")[len("plan-snapshot-") :]: " ".join(
                (row.get_attribute("textContent") or "").split()
            )
            for row in rows
        }

    def choose_snapshot(self, audit_key: str) -> None:
        """Choose one earlier state; return once the server's dry-run report for it is shown."""
        self.wait_and_click(_tid(f"plan-snapshot-{audit_key}"))

        def _report() -> bool:
            if self.is_present(self.SNAPSHOTS_FAILURE):
                raise AssertionError(
                    f"checking the snapshot failed: {self.text_of(self.SNAPSHOTS_FAILURE)!r}"
                )
            return self.is_present(self.SNAPSHOTS_REPORT)

        try:
            self.poll().until(lambda _d: _report())
        except TimeoutException as exc:
            raise AssertionError(f"no restore report appeared for snapshot {audit_key!r}") from exc

    def snapshot_report_counts(self) -> list[str]:
        return self._lines(
            "[data-testid='plan-snapshots'] [data-testid='plan-import-report'] > div:first-child > p"
        )

    def is_restore_enabled(self) -> bool:
        return self.wait_for_element(self.SNAPSHOTS_RESTORE).is_enabled()

    def type_snapshot_confirm_name(self, name: str) -> None:
        self._type_into(self.SNAPSHOTS_CONFIRM_NAME, name)

    def restore_snapshot(self) -> str:
        """'Diesen Stand wiederherstellen'; return the success line once the server wrote it."""
        if not self.is_restore_enabled():
            raise AssertionError("'Diesen Stand wiederherstellen' is disabled")
        self.wait_and_click(self.SNAPSHOTS_RESTORE)
        return self._wait_for_import_done("the restore")

    # ── Underlay (GP-FR-033) ───────────────────────────────────────────

    def open_underlay(self) -> None:
        self.wait_and_click(self.UNDERLAY_OPEN)
        try:
            self.wait_for_element_visible(self.UNDERLAY_DIALOG)
        except TimeoutException as exc:
            raise AssertionError("the underlay dialog did not open") from exc

    def choose_underlay_picture(self, path: str) -> tuple[int, int]:
        """Hand the picture to the dialog; return its natural size once the browser decoded it."""
        self._unhide_file_input(self.UNDERLAY_FILE).send_keys(path)

        def _size():
            if self.is_present(self.UNDERLAY_ERROR):
                raise AssertionError(
                    f"the underlay dialog reports {self.text_of(self.UNDERLAY_ERROR)!r}"
                )
            images = self.driver.find_elements(*self.UNDERLAY_IMAGE)
            if not images:
                return False
            size = self.driver.execute_script(
                "var i = arguments[0]; return i.complete && i.naturalWidth > 0 ? [i.naturalWidth, i.naturalHeight] : null;",
                images[0],
            )
            return (int(size[0]), int(size[1])) if size else False

        try:
            return self.poll().until(lambda _d: _size())
        except TimeoutException as exc:
            raise AssertionError(f"the underlay picture {path!r} was never shown") from exc

    def underlay_field(self, field_id: str) -> str:
        return self.wait_for_element(_tid(f"underlay-{field_id}")).get_attribute("value") or ""

    def set_underlay_field(self, field_id: str, text: str) -> None:
        self._type_into(_tid(f"underlay-{field_id}"), text)

    def mark_underlay_point(self, which: str, fx: float, fy: float) -> tuple[float, float]:
        """Choose 'Punkt 1/2 setzen', click the picture at the fractions (*fx*, *fy*) of its box; the marked pixel.

        A real pointer click: the dialog turns the event's ``clientX/Y`` into a picture
        pixel (``toImagePoint``), so a script click (``clientX = 0``) would mark a wrong
        place. The point is checked with ``elementFromPoint`` to hit the picture itself.
        The marked pixel is read back from the dialog's own fields, which the click fills.
        """
        toggle = self.wait_for_element(_tid(f"underlay-mark-{which}"))
        if toggle.get_attribute("aria-pressed") != "true":
            self.scroll_and_click(toggle)
            self.poll().until(lambda _d: toggle.get_attribute("aria-pressed") == "true")
        image = self.wait_for_element(self.UNDERLAY_IMAGE)
        self.scroll_into_view(image)
        before = (self.underlay_field(f"{which}x"), self.underlay_field(f"{which}y"))
        point = self.driver.execute_script(
            "var r = arguments[0].getBoundingClientRect();"
            "return [r.left + r.width * arguments[1], r.top + r.height * arguments[2]];",
            image,
            fx,
            fy,
        )
        hit = self.driver.execute_script(
            "return document.elementFromPoint(arguments[0], arguments[1]) === arguments[2];",
            point[0],
            point[1],
            image,
        )
        if not hit:
            raise AssertionError(
                f"the point {point} on the underlay picture is covered by another element"
            )
        builder = ActionBuilder(self.driver)
        builder.pointer_action.move_to_location(round(point[0]), round(point[1]))
        builder.pointer_action.click()
        builder.perform()
        try:
            self.poll().until(
                lambda _d: (
                    (self.underlay_field(f"{which}x"), self.underlay_field(f"{which}y")) != before
                    and self.underlay_field(f"{which}x") != ""
                )
            )
        except TimeoutException as exc:
            raise AssertionError(f"the click on the picture did not mark point {which}") from exc
        return float(self.underlay_field(f"{which}x")), float(self.underlay_field(f"{which}y"))

    def save_underlay(self) -> None:
        """'Speichern'; the dialog closes only after the server stored picture and calibration."""
        self.wait_and_click(self.UNDERLAY_SAVE)
        try:
            self.wait_for_element_hidden(self.UNDERLAY_DIALOG, timeout=30)
        except TimeoutException as exc:
            error = (
                self.text_of(self.UNDERLAY_ERROR) if self.is_present(self.UNDERLAY_ERROR) else None
            )
            raise AssertionError(
                f"the underlay dialog did not close after saving (error: {error!r})"
            ) from exc

    def underlay_screen_distance_m(self, p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """The plan distance between two picture pixels as the editor draws them: screen px over px/m.

        Both pixels go through the drawn ``<image>``'s own screen matrix (``getScreenCTM``:
        the calibration's scale, the placement and the zoom together), so this is the
        measure a user takes on screen, not a recomputation of the formula.
        """
        image = self.wait_for_element(self.UNDERLAY_DRAWN)
        pixels = self.driver.execute_script(
            "var img = arguments[0], m = img.getScreenCTM(), svg = img.ownerSVGElement;"
            "if (!m) { return null; }"
            "function at(x, y) { var p = svg.createSVGPoint(); p.x = x; p.y = y;"
            "  p = p.matrixTransform(m); return [p.x, p.y]; }"
            "var a = at(arguments[1], arguments[2]), b = at(arguments[3], arguments[4]);"
            "return Math.hypot(b[0] - a[0], b[1] - a[1]);",
            image,
            p1[0],
            p1[1],
            p2[0],
            p2[1],
        )
        if pixels is None:
            raise AssertionError("the drawn underlay has no screen matrix (not rendered)")
        return float(pixels) / self.px_per_m()

    def is_underlay_drawn(self) -> bool:
        return self.is_present(self.UNDERLAY_DRAWN)

    # ── Plant-state layer and attention filter (GP-UX-061) ─────────────

    def layer_markers(self) -> dict[str, dict]:
        """plant key -> ``{"lifecycle": ..., "badges": [...]}`` of every marker the plant-state layer draws."""
        svg = self.wait_for_element(self.SVG)
        rows = self.driver.execute_script(
            "return Array.from(arguments[0].querySelectorAll(\"[data-plan-state-layer='true']\")).map(function (g) {"
            "  var ring = g.querySelector('[data-plan-lifecycle]');"
            "  return [g.getAttribute('data-plan-key'), ring ? ring.getAttribute('data-plan-lifecycle') : null,"
            "    Array.from(g.querySelectorAll('[data-plan-badge-reason]')).map(function (b) {"
            "      return b.getAttribute('data-plan-badge-reason'); })]; });",
            svg,
        )
        return {key: {"lifecycle": lifecycle, "badges": badges} for key, lifecycle, badges in rows}

    def wait_for_layer_markers(self, expected: dict[str, dict], what: str) -> None:
        try:
            self.poll().until(lambda _d: self.layer_markers() == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the plant-state layer should draw {expected}, it draws {self.layer_markers()}"
            ) from exc

    def is_attention_filter_usable(self) -> bool:
        return self.wait_for_element(self.ATTENTION_FILTER).get_attribute("aria-disabled") != "true"

    def is_attention_filter_on(self) -> bool:
        return self.wait_for_element(self.ATTENTION_FILTER).get_attribute("aria-pressed") == "true"

    def attention_filter_hint(self) -> str:
        """The hint the filter is described by (``aria-describedby``): why it is off, or what it does."""
        button = self.wait_for_element(self.ATTENTION_FILTER)
        hint_id = button.get_attribute("aria-describedby")
        if not hint_id:
            raise AssertionError("the attention filter carries no aria-describedby hint")
        return self.text_of((By.ID, hint_id))

    def set_attention_filter(self, on: bool) -> None:
        """Switch the filter with the keyboard (focus + Space) and verify ``aria-pressed`` flipped."""
        if self.is_attention_filter_on() is on:
            raise AssertionError(f"the attention filter is already {'on' if on else 'off'}")
        if not self.is_attention_filter_usable():
            raise AssertionError(
                f"the attention filter is disabled: {self.attention_filter_hint()!r}"
            )
        button = self.wait_for_element(self.ATTENTION_FILTER)
        self.driver.execute_script("arguments[0].focus();", button)
        self.press(Keys.SPACE)
        try:
            self.poll().until(lambda _d: self.is_attention_filter_on() is on)
        except TimeoutException as exc:
            raise AssertionError(
                f"the attention filter did not switch {'on' if on else 'off'}"
            ) from exc

    def sun_layer_beds(self) -> dict[str, str]:
        """bed key -> sun window the sun layer draws; loud when the layer is not drawn at all."""
        layer = self.wait_for_element(self.SUN_LAYER)
        return {
            g.get_attribute("data-condition-bed"): g.get_attribute("data-condition-value")
            for g in layer.find_elements(By.CSS_SELECTOR, "[data-condition-bed]")
        }

    def has_layer_toggle(self, layer_id: str) -> bool:
        """Whether the view bar lists a switch for *layer_id* (the underlay's only while the site has a picture)."""
        self.wait_for_element(self.SVG)
        return self.is_present(self._layer_toggle(layer_id))

    def wait_for_sun_layer(self, expected: dict[str, str], what: str) -> None:
        try:
            self.poll().until(lambda _d: self.sun_layer_beds() == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the sun layer should draw {expected}, it draws {self.sun_layer_beds()}"
            ) from exc

    def wait_for_object_keys(self, expected: set[str], what: str) -> None:
        """Wait until the editor draws exactly the beds and objects *expected* (the boundary left out)."""
        try:
            self.poll().until(lambda _d: set(self.object_keys()) == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the editor should draw {sorted(expected)}, it draws {sorted(self.object_keys())}"
            ) from exc
