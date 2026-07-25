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

    def close_mui_dropdown(self, timeout: int = 5) -> None:
        """Close any open MUI Select dropdown and wait until it is removed from the DOM."""
        from selenium.common.exceptions import TimeoutException
        from selenium.webdriver.common.keys import Keys

        if not self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']"):
            return  # Already closed

        # After an option click MUI closes the popover on its own — give the
        # close animation a moment before touching the keyboard. Sending
        # Escape while the popover is mid-close delivers the key to the
        # surrounding dialog and closes THAT instead (races on slow machines,
        # e.g. CI runners).
        try:
            WebDriverWait(self.driver, 2).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "li[role='option']")) == 0
            )
            return
        except TimeoutException:
            pass

        # Dropdown is genuinely open (opened without selecting) — close it via Escape
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        try:
            # Wait until ALL option elements are gone from the DOM
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "li[role='option']")) == 0
            )
        except TimeoutException:
            pass

    def scroll_and_click(self, element: WebElement) -> None:
        """Scroll an element into view and click it, falling back to JS click."""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        try:
            element.click()
        except (ElementNotInteractableException, ElementClickInterceptedException):
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

    def open_select(self, field_name: str) -> None:
        """Open a FormSelectField dropdown via a stable trigger selector.

        Prefers the ARIA `[role='combobox']` display (stable across MUI versions);
        falls back to the legacy `.MuiSelect-select` class for non-FormSelectField
        selects that don't expose the combobox role.
        """
        for selector in (
            f"[data-testid='form-field-{field_name}'] [role='combobox']",
            f"[data-testid='form-field-{field_name}'] .MuiSelect-select",
        ):
            els = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if els:
                self.scroll_and_click(els[0])
                return
        raise AssertionError(f"Select trigger for field '{field_name}' not found")

    def select_option_by_value(self, value: str, field_name: str | None = None) -> None:
        """Click an open dropdown option by its stable data-value (i18n-independent).

        Waits briefly (bounded) for each candidate selector to become
        clickable rather than gating on an instant ``is_present`` check --
        the MUI popover open animation can still be in flight when this runs,
        so an unwaited check can miss an option that renders a beat later.
        """
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
            self.scroll_and_click(el)
            self.close_mui_dropdown()
            return
        raise AssertionError(f"Option with value '{value}' not found in the open dropdown")

    def choose_select_value(self, field_name: str, value: str) -> None:
        """Open a FormSelectField and pick the option with the given value.

        Retries once, re-opening the select, if the listbox never appeared or
        the option click didn't register on the first attempt -- a bounded
        guard against the MUI popover animation racing the option lookup
        (observed as a one-off timeout on an otherwise-passing code path,
        TC-006-J077).
        """
        self.open_select(field_name)
        try:
            self.select_option_by_value(value, field_name)
            return
        except AssertionError:
            pass
        self.close_mui_dropdown()
        self.open_select(field_name)
        self.select_option_by_value(value, field_name)

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
