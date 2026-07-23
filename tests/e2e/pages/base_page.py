"""Base page object with common helpers for all pages."""

from __future__ import annotations

import time
from pathlib import Path

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DEFAULT_TIMEOUT = 15


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
        """Click an open dropdown option by its stable data-value (i18n-independent)."""
        selectors = []
        if field_name:
            selectors.append(f"[data-testid='form-option-{field_name}-{value}']")
        selectors.append(f"li[role='option'][data-value='{value}']")
        for selector in selectors:
            locator = (By.CSS_SELECTOR, selector)
            if self.is_present(locator):
                self.scroll_and_click(self.wait_for_element_clickable(locator))
                self.close_mui_dropdown()
                return
        raise AssertionError(f"Option with value '{value}' not found in the open dropdown")

    def choose_select_value(self, field_name: str, value: str) -> None:
        """Open a FormSelectField and pick the option with the given value."""
        self.open_select(field_name)
        self.select_option_by_value(value, field_name)

    def get_row_cell_text(self, row: WebElement, col_id: str) -> str:
        """Return a DataTable row cell's text addressed by column id (not position)."""
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        return cells[0].text if cells else ""

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
