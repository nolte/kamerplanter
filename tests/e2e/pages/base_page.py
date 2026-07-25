"""Base page object with common helpers for all pages."""

from __future__ import annotations

import time
from pathlib import Path

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DEFAULT_TIMEOUT = 15

# ── Dialog scoping ────────────────────────────────────────────────────────
# A MUI Dialog's paper carries ``role="dialog"`` -- but so does a *temporary*
# MUI Drawer's paper. Below the `md` breakpoint (900px, i.e. BOTH the mobile
# and the tablet profile) the Sidebar renders as `variant="temporary"` with
# `ModalProps={{ keepMounted: true }}`, so its paper is portalled to
# ``document.body`` at app mount and stays in the DOM with
# ``visibility: hidden`` while the drawer is closed.
#
# An unscoped ``div[role='dialog']`` therefore resolves to that invisible
# drawer paper FIRST (document order), and ``visibility_of_element_located``
# -- which uses ``find_element``, i.e. first match only -- never becomes true.
# CSS selector *lists* are no protection either: they also match in document
# order, so a ``[data-testid='x'], div[role='dialog']`` fallback chain still
# picks the drawer.
#
# Always scope dialog lookups to the MuiDialog subtree (or, better, to the
# dialog's own data-testid). The Drawer root is ``.MuiDrawer-root`` and never
# carries ``.MuiDialog-root``, so this scoping is exact.
DIALOG_SELECTOR = ".MuiDialog-root [role='dialog']"
DIALOG_XPATH = "//*[contains(@class, 'MuiDialog-root')]//*[@role='dialog']"


class BasePage:
    """Shared helpers inherited by every page object."""

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    # ── Navigation ────────────────────────────────────────────────────────

    def navigate(self, path: str) -> None:
        """Navigate to *path* relative to the base URL."""
        self.driver.get(f"{self.base_url}{path}")

    # ── Waits ─────────────────────────────────────────────────────────────

    def wait_for_element(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> WebElement:
        """Wait until an element is present in the DOM and return it."""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def wait_for_element_visible(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> WebElement:
        """Wait until an element is visible and return it."""
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_for_element_clickable(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> WebElement:
        """Wait until an element is clickable and return it."""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )

    def wait_for_element_hidden(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> None:
        """Wait until an element is no longer visible (e.g. MUI Dialog fade-out)."""
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(locator)
        )

    def wait_for_loading_complete(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until all ``[data-testid='loading-skeleton']`` elements disappear."""
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
            )
        )

    def wait_for_url_contains(self, fragment: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the current URL contains *fragment*."""
        WebDriverWait(self.driver, timeout).until(EC.url_contains(fragment))

    # ── Queries ───────────────────────────────────────────────────────────

    def find_by_testid(self, testid: str) -> WebElement:
        """Shorthand for finding an element by its ``data-testid``."""
        return self.driver.find_element(By.CSS_SELECTOR, f"[data-testid='{testid}']")

    def find_all_by_testid(self, testid: str) -> list[WebElement]:
        """Return all elements matching the given ``data-testid``."""
        return self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{testid}']")

    def is_present(self, locator: tuple[str, str]) -> bool:
        """Return True if at least one element matching *locator* exists in the DOM."""
        return len(self.driver.find_elements(*locator)) > 0

    def get_text_stable(self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT) -> str:
        """Return text of *locator*, retrying on StaleElementReferenceException."""
        deadline = time.time() + timeout
        while True:
            try:
                el = self.wait_for_element_visible(locator, timeout=min(5, max(1, int(deadline - time.time()))))
                return el.text
            except StaleElementReferenceException:
                if time.time() >= deadline:
                    raise
                time.sleep(0.2)

    def get_page_title(self) -> str:
        """Return the text content of the ``[data-testid='page-title']`` element."""
        return self.get_text_stable((By.CSS_SELECTOR, "[data-testid='page-title']"))

    def is_error_displayed(self) -> bool:
        """Check whether ``[data-testid='error-display']`` is visible."""
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='error-display']"
        )
        return len(elements) > 0 and elements[0].is_displayed()

    def has_alert_notification(self) -> bool:
        """Check whether any ``[role='alert']`` notification is present (e.g. an error snackbar)."""
        return len(self.driver.find_elements(By.CSS_SELECTOR, "[role='alert']")) > 0

    def get_body_text(self) -> str:
        """Return the full text content of the page body (for keyword assertions)."""
        return self.driver.find_element(By.TAG_NAME, "body").text

    # ── Interactions ─────────────────────────────────────────────────────

    OPTIONS = (By.CSS_SELECTOR, "li[role='option']")
    LISTBOX = (By.CSS_SELECTOR, "[role='listbox']")

    def _wait_options_gone(self, timeout: float) -> bool:
        """Wait (bounded) until no ``li[role='option']`` is left; return the outcome."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*self.OPTIONS)) == 0
            )
            return True
        except TimeoutException:
            return False

    def close_mui_dropdown(self, timeout: int = 5) -> None:
        """Close any open MUI Select dropdown, or fail loudly if it stays open.

        Fails loudly by design: an open popover is a full-screen click-away
        overlay, so returning while it is still up pushes the failure onto the
        *next* interaction, which then reports "button not clickable" for a
        cause that is nowhere near it (observed in
        ``FAILURE_test_ended_cycle_spawns_no_new_instance.png``). The previous
        ``except TimeoutException: pass`` swallowed exactly that.

        The Escape key goes to the listbox rather than to ``<body>``: a blind
        body-level Escape is delivered to whatever modal currently has focus,
        so it closes the *surrounding dialog* when the popover happens to have
        closed itself in the meantime.
        """
        from selenium.webdriver.common.keys import Keys

        if not self.driver.find_elements(*self.OPTIONS):
            return  # Already closed

        # After an option click MUI closes the popover on its own — give the
        # close a bounded moment before touching the keyboard at all.
        if self._wait_options_gone(2):
            return

        # Dropdown is genuinely open (opened without selecting) — close it via
        # Escape on the menu itself, which is where MUI's key handler sits.
        target = next(iter(self.driver.find_elements(*self.LISTBOX)), None)
        if target is None:
            target = next(iter(self.driver.find_elements(*self.OPTIONS)), None)
        if target is None:
            return  # raced to closed between the two lookups
        try:
            target.send_keys(Keys.ESCAPE)
        except (
            ElementNotInteractableException,
            StaleElementReferenceException,
        ):
            self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)

        if not self._wait_options_gone(timeout):
            raise AssertionError(
                f"MUI dropdown did not close within {timeout}s — "
                f"{len(self.driver.find_elements(*self.OPTIONS))} option(s) are "
                "still in the DOM. Its click-away overlay will intercept every "
                "following click."
            )

    #: Controls whose menu/popover opens on ``mousedown`` rather than on
    #: ``click``: the MUI Select display div (``[role='combobox']`` since v5,
    #: ``.MuiSelect-select`` as the legacy class hook).
    MENU_TRIGGER_CSS = "[role='combobox'], .MuiSelect-select"

    def opens_on_mousedown(self, element: WebElement) -> bool:
        """Return True if *element* is a control that opens on ``mousedown``."""
        return bool(
            self.driver.execute_script(
                "return arguments[0].matches(arguments[1]);",
                element,
                self.MENU_TRIGGER_CSS,
            )
        )

    def dispatch_menu_trigger_open(self, element: WebElement) -> None:
        """Dispatch a ``mousedown``/``mouseup`` pair straight onto a menu trigger.

        MUI opens a Select **only** from its ``onMouseDown`` handler -- there is
        no ``onClick`` opener. A JS ``element.click()`` dispatches a lone
        ``click`` event, so it can never open one; it merely *reports* success.
        This sends the pair a real pointer would.

        Deliberately dispatched on the element rather than through
        ``ActionChains``: ActionChains is coordinate-based and, unlike
        ``WebElement.click()``, performs no interactability hit-test, so under
        an overlay it silently delivers the events to the overlay -- the same
        class of silent-success defect this replaces. Also deliberately without
        a trailing ``click``: MUI has already opened the menu on ``mousedown``,
        and a bubbling ``click`` can be read as a click-away.
        """
        self.driver.execute_script(
            "var el = arguments[0];"
            "['mousedown', 'mouseup'].forEach(function (type) {"
            "  el.dispatchEvent(new MouseEvent(type, {"
            "    bubbles: true, cancelable: true, view: window, button: 0,"
            "  }));"
            "});",
            element,
        )

    def scroll_and_click(self, element: WebElement) -> None:
        """Scroll an element into view and click it, with a sound JS fallback.

        The fallback is chosen by target: a bare JS ``click()`` is fine for
        buttons and links, but is a *silent no-op* on a MUI Select trigger
        (which opens on ``mousedown``), so those get an explicit
        mousedown/mouseup pair instead — see
        :meth:`dispatch_menu_trigger_open`.
        """
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        try:
            element.click()
        except (ElementNotInteractableException, ElementClickInterceptedException):
            if self.opens_on_mousedown(element):
                self.dispatch_menu_trigger_open(element)
            else:
                self.driver.execute_script("arguments[0].click();", element)

    def wait_and_click(self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until *locator* is clickable, scroll it into view, then click it.

        The scroll step is not cosmetic: below the `sm` breakpoint MUI dialogs
        render ``fullScreen``, so a form's action row is the last child of a
        scrolling ``DialogContent`` and sits *below the fold*.
        ``element_to_be_clickable`` is satisfied by a displayed+enabled element
        regardless of whether it is inside the viewport, so a naked ``.click()``
        on such a button raises ``ElementNotInteractableException`` (or, once
        ChromeDriver's own scroll puts it under the fixed AppBar,
        ``ElementClickInterceptedException``).

        Use this for every submit/cancel-style action; ``scroll_and_click``
        stays available for callers that already hold the element.
        """
        self.scroll_and_click(self.wait_for_element_clickable(locator, timeout=timeout))

    # ── Robust form-select / table helpers (prefer dedicated testids) ──────
    # These replace brittle `.MuiSelect-select` clicks, i18n-fragile
    # `contains(text(), label)` option XPaths, and position-based `cells[N]`
    # access with the dedicated data-testids emitted by FormSelectField and
    # DataTable. They fall back to the legacy selectors so page objects can be
    # migrated incrementally.

    #: Trigger sub-selectors probed inside a select container, in order: the
    #: ARIA display (stable across MUI versions), then the legacy class hook.
    SELECT_TRIGGER_SUBSELECTORS = ("[role='combobox']", ".MuiSelect-select")

    def is_select_open(self, trigger: WebElement) -> bool:
        """Return True while *trigger*'s dropdown is open.

        Keyed on the trigger's own ``aria-expanded`` (durable, and true even for
        a menu that legitimately renders zero options), with the rendered
        listbox as a second signal for triggers that don't carry the attribute
        or that went stale on the re-render the open caused.
        """
        if self._aria_expanded(trigger) == "true":
            return True
        return len(self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")) > 0

    @staticmethod
    def _aria_expanded(trigger: WebElement) -> str:
        """Return *trigger*'s ``aria-expanded``, or ``'<stale>'`` if it unmounted."""
        try:
            return trigger.get_attribute("aria-expanded") or ""
        except StaleElementReferenceException:
            return "<stale>"

    #: Reads the geometry of the open menu's paper -- the element `Popover`
    #: repositions and `Grow` scales. Resolved from the first option's own
    #: ``.MuiPaper-root`` ancestor rather than from a guessed paper selector,
    #: so it can never pick up the always-mounted temporary-drawer paper.
    _MENU_RECT_SCRIPT = (
        "var opt = document.querySelector(\"li[role='option']\");"
        "if (!opt) { return null; }"
        "var paper = opt.closest('.MuiPaper-root') || opt;"
        "var r = paper.getBoundingClientRect();"
        "return [Math.round(r.top), Math.round(r.left), Math.round(r.height)];"
    )

    def _wait_for_menu_position_stable(self, timeout: int = 5) -> None:
        """Wait until the open menu's paper stopped moving, or fail loudly.

        `Popover` clamps a menu that does not fit below its anchor *upward*,
        and it does so while `Grow` is still running — i.e. **after** Selenium
        already considers the options clickable. A click issued in that window
        lands on whichever option slid into those coordinates, which is how a
        requested ``FREQ=WEEKLY`` ended up selecting ``FREQ=MONTHLY`` on the
        mobile profile (852 px viewport, five options, the last field of a long
        page). Desktop never saw it because at 1080 px the menu fits below the
        anchor and its position is final from the first frame.

        Two consecutive identical geometry readings are the durable signal that
        the reposition-and-grow settled. Complements — and does not depend on —
        the harness-level ``--force-prefers-reduced-motion``.
        """
        last: list[list[int] | None] = [None]

        def _stable(driver: WebDriver) -> bool:
            current = driver.execute_script(self._MENU_RECT_SCRIPT)
            if current is None:
                return True  # menu gone / no options — nothing to stabilise
            previous, last[0] = last[0], current
            return current == previous

        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.1).until(_stable)
        except TimeoutException as exc:
            raise AssertionError(
                f"The open dropdown never stopped moving within {timeout}s "
                f"(last [top, left, height] = {last[0]}). Clicking an option "
                "while the popover is still being repositioned selects the "
                "wrong entry."
            ) from exc

    def _settle_listbox(self, timeout: int = 2) -> None:
        """Wait until an opened dropdown's options render *and* stopped moving.

        ``aria-expanded`` can be observed a beat before the portalled menu's
        ``li[role='option']`` nodes are queryable, which would make an
        immediately following ``find_elements`` return ``[]``. A Select whose
        option list is legitimately empty is not an error condition -- it stays
        open with zero options, so callers that require options assert on them
        and this returns without a geometry check.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*self.OPTIONS)) > 0
            )
        except TimeoutException:
            return
        self._wait_for_menu_position_stable()

    def _wait_until_select_open(self, trigger: WebElement, timeout: int = 5) -> bool:
        """Wait (bounded) until *trigger*'s dropdown is open; return the outcome."""
        try:
            WebDriverWait(self.driver, timeout).until(lambda _d: self.is_select_open(trigger))
            return True
        except TimeoutException:
            return False

    def open_select(self, field_name: str) -> None:
        """Open a FormSelectField dropdown and verify that it actually opened."""
        self.open_select_in(
            f"[data-testid='form-field-{field_name}']", f"field '{field_name}'"
        )

    def open_select_by_testid(self, testid: str) -> None:
        """Open a MUI Select addressed by the data-testid on its TextField root.

        MUI spreads ``...other`` onto the **root** ``FormControl`` (label +
        input + helper text), not onto the ``[role='combobox']`` display div, so
        a click on the root's centre can land on the label or the helper text —
        a silent no-op, because the ``<p>`` is a descendant of the clicked root
        and Chrome therefore raises no interception. Resolve the combobox first.
        """
        self.open_select_in(f"[data-testid='{testid}']", f"select '{testid}'")

    def open_select_in(self, container: str, what: str) -> None:
        """Open the MUI Select inside *container*, or fail loudly.

        Fails loudly by design: a helper that reports success without having
        opened anything pushes the failure to a later, unrelated line (the
        option lookup) and hides the real cause.
        """
        trigger: WebElement | None = None
        for sub in self.SELECT_TRIGGER_SUBSELECTORS:
            locator = (By.CSS_SELECTOR, f"{container} {sub}")
            if self.driver.find_elements(*locator):
                trigger = self.wait_for_element_clickable(locator)
                break
        if trigger is None:
            raise AssertionError(f"Select trigger for {what} not found")

        self.scroll_and_click(trigger)
        if self._wait_until_select_open(trigger):
            self._settle_listbox()
            return
        # The click did not open the menu (e.g. it was swallowed while the
        # trigger was still moving). Retry with the explicit mousedown pair.
        self.dispatch_menu_trigger_open(trigger)
        if self._wait_until_select_open(trigger):
            self._settle_listbox()
            return
        raise AssertionError(
            f"Select for {what} did not open (aria-expanded stayed "
            f"{self._aria_expanded(trigger)!r} and no li[role='option'] appeared)"
        )

    #: The Select display div of the dropdown that is currently open. Captured
    #: *before* the option click so the resulting value can be read back even
    #: when the caller gave no field name.
    OPEN_SELECT_TRIGGER = (
        By.CSS_SELECTOR,
        "[role='combobox'][aria-expanded='true'], .MuiSelect-select[aria-expanded='true']",
    )

    #: Reads the committed value of a MUI Select: its hidden
    #: ``.MuiSelect-nativeInput`` inside the same ``.MuiInputBase-root``.
    _SELECT_VALUE_FROM_TRIGGER = (
        "var el = arguments[0];"
        "var base = el.closest('.MuiInputBase-root') || el.parentElement;"
        "var input = base ? base.querySelector('input, select, textarea') : null;"
        "return input ? input.value : null;"
    )
    _SELECT_VALUE_FROM_CONTAINER = (
        "var root = document.querySelector(arguments[0]);"
        "if (!root) { return null; }"
        "var input = root.querySelector('input, select, textarea');"
        "return input ? input.value : null;"
    )

    def select_option_by_value(self, value: str, field_name: str | None = None) -> None:
        """Click an open dropdown option by its data-value and verify the effect.

        Waits briefly (bounded) for each candidate selector to become
        clickable rather than gating on an instant ``is_present`` check --
        the MUI popover open animation can still be in flight when this runs,
        so an unwaited check can miss an option that renders a beat later.

        Reads the resulting Select value back and raises on a mismatch. Without
        that, this helper returned unconditionally after *dispatching* a click,
        so a click that landed on a neighbouring option (see
        :meth:`_wait_for_menu_position_stable`) was reported as a success --
        and the two-attempt retry in :meth:`choose_select_value` was inert,
        because nothing ever raised. The expectation is taken from the clicked
        option's own ``data-value``, not from *value*, because the option
        testid suffix and the value differ for the empty option
        (``form-option-<field>-none`` / ``-empty`` both commit ``''``).
        """
        trigger = next(iter(self.driver.find_elements(*self.OPEN_SELECT_TRIGGER)), None)
        selectors = []
        if field_name:
            selectors.append(f"[data-testid='form-option-{field_name}-{value}']")
        selectors.append(f"li[role='option'][data-value='{value}']")
        for selector in selectors:
            locator = (By.CSS_SELECTOR, selector)
            try:
                el = self.wait_for_element_clickable(locator, timeout=3)
            except TimeoutException:
                continue
            expected = el.get_attribute("data-value")
            self.scroll_and_click(el)
            self.close_mui_dropdown()
            self._verify_select_committed(trigger, expected, value, field_name)
            return
        raise AssertionError(f"Option with value '{value}' not found in the open dropdown")

    def _read_select_value(
        self, trigger: WebElement | None, field_name: str | None
    ) -> str | None:
        """Return the committed value of the Select that was just operated on."""
        if field_name:
            value = self.driver.execute_script(
                self._SELECT_VALUE_FROM_CONTAINER,
                f"[data-testid='form-field-{field_name}']",
            )
            if value is not None:
                return str(value)
        if trigger is None:
            return None
        try:
            value = self.driver.execute_script(self._SELECT_VALUE_FROM_TRIGGER, trigger)
        except StaleElementReferenceException:
            return None
        return None if value is None else str(value)

    def _verify_select_committed(
        self,
        trigger: WebElement | None,
        expected: str | None,
        requested: str,
        field_name: str | None,
    ) -> None:
        """Raise unless the clicked option actually became the Select's value."""
        what = f"field '{field_name}'" if field_name else "the open select"
        if expected is None:
            raise AssertionError(
                f"The option clicked for {what} (requested '{requested}') carries "
                "no data-value, so the selection cannot be verified. Address a "
                "MUI MenuItem rendered inside a Select."
            )
        actual = self._read_select_value(trigger, field_name)
        if actual is None:
            raise AssertionError(
                f"Cannot read back the value of {what} after selecting "
                f"'{requested}': no native input was found for it. Verifying the "
                "click is mandatory — an unverified option click silently "
                "selects a neighbouring entry when the popover is still moving."
            )
        # Multi-selects commit a comma-joined list.
        if actual != expected and expected not in actual.split(","):
            raise AssertionError(
                f"Selecting '{requested}' on {what} did not take effect: expected "
                f"the value {expected!r}, but the field holds {actual!r}. The "
                "click most likely landed on a neighbouring option."
            )

    def choose_select_value(self, field_name: str, value: str) -> None:
        """Open a FormSelectField and pick the option with the given value.

        Retries once, re-opening the select, if the listbox never appeared or
        the option click didn't register on the first attempt -- a bounded
        guard against the MUI popover animation racing the option lookup
        (observed as a one-off timeout on an otherwise-passing code path,
        TC-006-J077). The retry spans the *open* too: ``open_select`` verifies
        the dropdown really opened and raises when it did not, and
        ``select_option_by_value`` verifies the clicked option really became
        the value -- so this retry only became reachable once those two started
        raising, rather than reporting success unconditionally.
        """
        from contextlib import suppress

        last_error: AssertionError | None = None
        for _attempt in range(2):
            try:
                self.open_select(field_name)
                self.select_option_by_value(value, field_name)
                return
            except AssertionError as exc:
                last_error = exc
                # Recovery only: a stuck popover here is a *symptom* of the
                # failure being carried in `last_error`, which is the one worth
                # reporting. `close_mui_dropdown` stays loud for every other
                # caller.
                with suppress(AssertionError):
                    self.close_mui_dropdown()
        assert last_error is not None
        raise last_error

    def get_row_cell_text(self, row: WebElement, col_id: str) -> str:
        """Return a DataTable row cell's text addressed by column id (not position)."""
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        return cells[0].text if cells else ""

    # ── Layout-tolerant DataTable row access ──────────────────────────────
    # `DataTable` emits ``[data-testid='data-table-row']`` in BOTH layouts, but
    # only the desktop table renders ``<td data-testid='cell-<col_id>'>``. Below
    # the table's `mobileBreakpoint` it renders a `MobileCard` inside the same
    # row container, and `MobileCard` emits no per-cell testids at all -- there
    # is neither a ``<td>`` nor a ``cell-*`` to read. Position-based `cells[0]`
    # access is doubly wrong there: it yields `[]` on mobile, and on desktop it
    # picks whatever column happens to come first (a favourite star, a
    # conditionally prepended chip column, ...) rather than the identifying one.

    DATA_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    #: Container `DataTable` emits *only* in the mobile card layout.
    DATA_TABLE_CARDS = (By.CSS_SELECTOR, "[data-testid='data-table-cards']")

    def is_card_layout(self) -> bool:
        """Return True while a `DataTable` renders its mobile card layout.

        `DataTable` wraps the cards in ``[data-testid='data-table-cards']`` and
        renders that container in no other branch, so this is a durable signal
        -- no viewport arithmetic, no breakpoint duplication in the tests.
        """
        return len(self.driver.find_elements(*self.DATA_TABLE_CARDS)) > 0

    def require_table_layout(self, what: str) -> None:
        """Fail loudly when a column-position-based read is attempted on cards.

        Position-based readers (``cells[N]``) have no meaning in the card
        layout: `MobileCard` renders no ``<td>`` and no per-cell testid, so
        such a reader silently yields ``[]``/``""`` there -- and an assertion
        like "the deleted entry is no longer listed" then passes for the wrong
        reason. Callers that genuinely need column positions must be
        desktop-only; this guard turns the silent pass into a hard failure.
        """
        if self.is_card_layout():
            raise AssertionError(
                f"{what} reads DataTable cells by column position, but the mobile "
                "card layout is active (no <td> cells). Use a layout-tolerant "
                "reader (get_row_primary_text / get_row_text_fragments) or mark "
                "the test 'requires_desktop'."
            )

    def get_row_text_fragments(self, row: WebElement) -> list[str]:
        """Return a row's readable text fragments in *both* layouts.

        Desktop: one entry per ``<td>``. Mobile card layout: one entry per
        rendered text line of the card. Intended for membership assertions
        ("… is/is not listed"), which is what the positional ``get_row_texts``
        helpers were actually used for.
        """
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells:
            return [c.text for c in cells]
        return [line.strip() for line in (row.text or "").splitlines() if line.strip()]

    def get_all_row_text_fragments(self) -> list[list[str]]:
        """Return :meth:`get_row_text_fragments` for every visible DataTable row."""
        return [
            self.get_row_text_fragments(row)
            for row in self.driver.find_elements(*self.DATA_TABLE_ROWS)
        ]

    # `MobileCard` emits no per-field testid at all: its title is a
    # ``subtitle2`` Typography and its optional subtitle the ``caption``
    # Typography immediately following it inside the same header Box. The
    # `fields` grid also renders captions, so the subtitle is addressed as the
    # title's *sibling* rather than as "the first caption".
    CARD_TITLE_XPATH = ".//*[contains(@class, 'MuiTypography-subtitle2')]"
    CARD_SUBTITLE_XPATH = (
        ".//*[contains(@class, 'MuiTypography-subtitle2')]"
        "/following-sibling::*[contains(@class, 'MuiTypography-caption')]"
    )

    @staticmethod
    def _text_content(element: WebElement) -> str:
        """Return an element's ``textContent``, not its rendered text.

        `MobileCard` renders title and subtitle as ``<Typography noWrap>``
        (``overflow: hidden; text-overflow: ellipsis``), so the tail of a long
        value — e.g. the ``— watering`` suffix of a care-reminder task name —
        is not part of the element's *rendered* text and ``WebElement.text``
        drops it. ``textContent`` carries the full string.
        """
        return (element.get_attribute("textContent") or "").strip()

    def get_card_title(self, row: WebElement) -> str:
        """Return the `MobileCard` title of *row*, or ``''`` outside the card layout."""
        els = row.find_elements(By.XPATH, self.CARD_TITLE_XPATH)
        return self._text_content(els[0]) if els else ""

    def get_card_subtitle(self, row: WebElement) -> str:
        """Return the `MobileCard` subtitle of *row*, or ``''`` if it has none."""
        els = row.find_elements(By.XPATH, self.CARD_SUBTITLE_XPATH)
        return self._text_content(els[0]) if els else ""

    def get_row_chip_texts(self, row: WebElement) -> list[str]:
        """Return the chip labels of a row in DOM order (layout-tolerant).

        Both the desktop cells and `MobileCard`'s ``chips`` slot render the
        same MUI Chips in the same order, so an index into this list is stable
        across layouts -- unlike an index into the column list.
        """
        return [c.text for c in row.find_elements(By.CSS_SELECTOR, ".MuiChip-label")]

    #: MUI Chip palette suffixes, in the order they are probed.
    CHIP_COLORS = ("success", "warning", "error", "info", "secondary", "primary", "default")

    def get_column_chip_texts(self, col_id: str) -> list[str]:
        """Return the chip labels of column *col_id*, across all visible rows.

        Falls back to *every* chip of the row in the mobile card layout, where
        `MobileCard` renders the same chips the chip-carrying columns render,
        in the same order, but exposes no per-field testid to address them by.
        """
        texts: list[str] = []
        for row in self.driver.find_elements(*self.DATA_TABLE_ROWS):
            cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
            scope = cells[0] if cells else row
            texts.extend(c.text for c in scope.find_elements(By.CSS_SELECTOR, ".MuiChip-label"))
        return texts

    def get_column_chip_colors(self, col_id: str) -> list[str]:
        """Return the MUI palette name of column *col_id*'s chips, across all rows.

        Same layout fallback as :meth:`get_column_chip_texts`.
        """
        colors: list[str] = []
        for row in self.driver.find_elements(*self.DATA_TABLE_ROWS):
            cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
            colors.extend(self.get_row_chip_colors(cells[0] if cells else row))
        return colors

    def get_row_chip_colors(self, row: WebElement) -> list[str]:
        """Return the MUI palette name of each chip in a row, in DOM order.

        Reads MUI's ``MuiChip-color<Palette>`` class (e.g. ``MuiChip-colorSuccess``
        -> ``"success"``) and falls back to ``"default"``.
        """
        colors: list[str] = []
        for chip in row.find_elements(By.CSS_SELECTOR, ".MuiChip-root"):
            cls = chip.get_attribute("class") or ""
            colors.append(
                next(
                    (c for c in self.CHIP_COLORS if f"MuiChip-color{c.capitalize()}" in cls),
                    "default",
                )
            )
        return colors

    def get_row_primary_text(self, row: WebElement, col_id: str) -> str:
        """Return a row's identifying text, addressed by column id in both layouts.

        Reads ``[data-testid='cell-<col_id>']`` when the desktop table is
        rendered. In the mobile card layout it falls back to the card's first
        text line, which is the `MobileCard` ``title`` -- fed from the same
        field the identifying column renders on every page using this helper.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        if cells:
            return cells[0].text
        lines = [line.strip() for line in (row.text or "").splitlines() if line.strip()]
        return lines[0] if lines else ""

    def get_column_texts(self, col_id: str) -> list[str]:
        """Return the identifying text of every visible DataTable row."""
        return [
            self.get_row_primary_text(row, col_id)
            for row in self.driver.find_elements(*self.DATA_TABLE_ROWS)
        ]

    def find_row_by_text(self, needle: str) -> WebElement | None:
        """Return the first DataTable row whose rendered text contains *needle*.

        Layout-tolerant: matches against the row/card text rather than against
        a positional cell, so it behaves identically for the desktop table and
        the mobile card list.
        """
        for row in self.driver.find_elements(*self.DATA_TABLE_ROWS):
            if needle in (row.text or ""):
                return row
        return None

    def clear_and_fill(self, element: WebElement, value: str) -> None:
        """Reliably clear an input element and type a new value.

        Uses JavaScript to clear the field value and dispatch native input/change
        events so that React controlled components pick up the change.  After
        the JS clear, verifies the field is actually empty — if React restored
        the old value, falls back to Ctrl+A to select all before typing so
        the new value replaces whatever is in the field.
        """
        from selenium.webdriver.common.keys import Keys

        self.driver.execute_script(
            "var el = arguments[0];"
            "var proto = el.tagName === 'TEXTAREA'"
            "  ? window.HTMLTextAreaElement.prototype"
            "  : window.HTMLInputElement.prototype;"
            "var nativeInputValueSetter = Object.getOwnPropertyDescriptor(proto, 'value').set;"
            "nativeInputValueSetter.call(el, '');"
            "el.dispatchEvent(new Event('input', {bubbles: true}));"
            "el.dispatchEvent(new Event('change', {bubbles: true}));",
            element,
        )
        time.sleep(0.15)

        # Verify the field was actually cleared — React may have restored the
        # old value from state before send_keys runs.
        current = element.get_attribute("value") or ""
        if current:
            element.send_keys(Keys.CONTROL + "a")
            time.sleep(0.05)

        element.send_keys(value)

    # ── Sidebar navigation ─────────────────────────────────────────────────

    SIDEBAR_ROOT = (By.CSS_SELECTOR, "[data-testid='sidebar']")
    SIDEBAR_TOGGLE = (By.CSS_SELECTOR, "[data-testid='sidebar-toggle']")
    SIDEBAR_PAPER = (By.CSS_SELECTOR, "[data-testid='sidebar'] .MuiDrawer-paper")

    def is_sidebar_open(self) -> bool:
        """Return True if the sidebar drawer's paper is actually visible."""
        papers = self.driver.find_elements(*self.SIDEBAR_PAPER)
        return len(papers) > 0 and papers[0].is_displayed()

    def ensure_sidebar_open(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Open the sidebar drawer if it is closed, and wait until it is visible.

        Viewport-aware and idempotent. Below the `md` breakpoint (900px --
        i.e. BOTH the mobile and the tablet profile) the Sidebar renders as a
        *temporary* Drawer with ``ModalProps={{ keepMounted: true }}``, so its
        nav items stay in the DOM while the drawer is closed, merely hidden via
        ``visibility: hidden``. `uiSlice` seeds ``sidebarOpen`` from
        ``window.innerWidth >= 768``, so at 393px the drawer starts closed.

        Any assertion on nav-item *visibility* must therefore open the drawer
        first -- a presence-only wait on the sidebar stays green and masks the
        closed drawer. Returns immediately when the paper is already visible
        (desktop `persistent` variant, or the tablet width where the drawer
        starts open).

        No-ops when no sidebar is mounted at all (e.g. the login route, which
        renders outside `MainLayout`) -- "the sidebar is missing" is a distinct
        condition that the caller's own assertion reports.
        """
        if self.is_sidebar_open() or not self.is_present(self.SIDEBAR_ROOT):
            return
        toggle = self.wait_for_element_clickable(self.SIDEBAR_TOGGLE, timeout=timeout)
        self.scroll_and_click(toggle)
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.SIDEBAR_PAPER)
        )

    def navigate_via_sidebar(self, path: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Navigate by clicking a sidebar link, simulating real user behavior.

        Falls back to direct URL navigation if the sidebar item is not visible
        (e.g. hidden by expertise level).
        """
        locator = (By.CSS_SELECTOR, f"[data-testid='nav-{path}']")
        items = self.driver.find_elements(*locator)
        if items and items[0].is_displayed():
            self.scroll_and_click(items[0])
            WebDriverWait(self.driver, timeout).until(EC.url_contains(path))
        else:
            self.navigate(path)

    # ── Expertise level helpers ─────────────────────────────────────────────

    SHOW_ALL_FIELDS_TOGGLE = (By.CSS_SELECTOR, "[data-testid='show-all-fields-toggle']")

    def expand_all_fields(self, timeout: int = 5) -> None:
        """Click the 'Show all fields' toggle if present (for beginner mode)."""
        toggles = self.driver.find_elements(*self.SHOW_ALL_FIELDS_TOGGLE)
        if toggles and toggles[0].is_displayed():
            self.scroll_and_click(toggles[0])
            time.sleep(0.3)

    # ── Screenshots ───────────────────────────────────────────────────────

    def take_screenshot(self, name: str, output_dir: Path) -> Path:
        """Save a PNG screenshot and return the file path."""
        filepath = output_dir / f"{name}.png"
        self.driver.save_screenshot(str(filepath))
        return filepath
