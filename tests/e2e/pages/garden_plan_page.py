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
