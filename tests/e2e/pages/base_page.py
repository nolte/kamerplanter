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

    # ── Interactions ─────────────────────────────────────────────────────

    def close_mui_dropdown(self, timeout: int = 5) -> None:
        """Close any open MUI Select dropdown and wait until it is removed from the DOM."""
        from selenium.common.exceptions import NoSuchElementException, TimeoutException
        from selenium.webdriver.common.keys import Keys

        if not self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']"):
            return  # Already closed

        # Dropdown is open — close it via Escape
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        try:
            # Wait until ALL option elements are gone from the DOM
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "li[role='option']")) == 0
            )
        except TimeoutException:
            pass

    def scroll_and_click(self, element: WebElement) -> None:
        """Scroll an element into view and click it, falling back to JS click.

        Tolerates StaleElementReferenceException on the scroll/click path:
        on stale, we cannot re-find the element here (no locator), so the
        caller must use ``click_locator_with_retry`` for stale-prone paths.
        """
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            element.click()
        except (ElementNotInteractableException, ElementClickInterceptedException):
            self.driver.execute_script("arguments[0].click();", element)
        except StaleElementReferenceException:
            # Element was re-rendered between scrollIntoView and click.
            # Re-raise so the caller (click_locator_with_retry) can re-find
            # the element and retry.
            raise

    def click_locator_with_retry(
        self,
        locator: tuple[str, str],
        timeout: int = DEFAULT_TIMEOUT,
        attempts: int = 3,
    ) -> None:
        """Click an element resolved from *locator*, retrying on stale references.

        React re-renders frequently invalidate elements between the moment
        ``wait_for_element_clickable`` resolves them and the moment
        ``element.click()`` fires.  This helper re-resolves the locator on
        each attempt so a single re-render does not abort the test.
        """
        for attempt in range(attempts):
            try:
                btn = self.wait_for_element_clickable(locator, timeout=timeout)
                self.scroll_and_click(btn)
                return
            except StaleElementReferenceException:
                if attempt == attempts - 1:
                    raise
                time.sleep(0.25)

    def clear_and_fill(self, element: WebElement, value: str) -> None:
        """Reliably clear an input element and type a new value.

        Robust against React-controlled inputs that restore defaults from
        state and against MUI inputs where ``Ctrl+A`` is intercepted by the
        component (e.g. number-fields with stepper buttons).

        Strategy:

        1. **Focus** the element (click → JS focus fallback).
        2. **Per-character backspace from end**: ``End`` then ``Backspace``
           N times where N is the current value length.  More deterministic
           than ``Ctrl+A`` because it never accidentally selects parent
           content and always drives React's ``onChange`` per character.
        3. **JS native setter + input/change events** as a belt-and-braces
           fallback for any default that races back in.
        4. **Re-verify**; if non-empty, repeat the backspace loop once more.
        5. ``send_keys(value)`` to type the desired value.
        """
        from selenium.webdriver.common.keys import Keys

        # Stage 1 — focus
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].focus();", element)

        # Stage 2 — backspace from end, character by character
        def _backspace_clear(el: WebElement) -> None:
            current = el.get_attribute("value") or ""
            if not current:
                return
            try:
                el.send_keys(Keys.END)
            except Exception:
                pass
            # Cap the loop to avoid infinite loops if get_attribute lies.
            for _ in range(min(len(current) + 2, 256)):
                el.send_keys(Keys.BACKSPACE)
                if not (el.get_attribute("value") or ""):
                    break

        _backspace_clear(element)
        time.sleep(0.05)

        # Stage 3 — JS native setter as fallback (handles defaults restored
        # from React state between stage 2 and stage 5)
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
        time.sleep(0.1)

        # Stage 4 — re-verify; one more backspace round if a default snapped back
        if (element.get_attribute("value") or ""):
            _backspace_clear(element)

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

    # ── Dialog & form helpers (stable lookups across UI refactors) ─────────
    #
    # The frontend exposes three stable conventions:
    #   1. Every open MUI Dialog renders ``div[role="dialog"]``.
    #   2. Form action buttons share ``data-testid="form-submit-button"`` and
    #      ``data-testid="form-cancel-button"`` (see FormActions.tsx).
    #   3. Form-field wrappers use ``data-testid="form-field-<name>"``.
    #
    # Use the helpers below instead of pinning to component-specific
    # ``data-testid="*-create-dialog"`` so tests survive future renames.

    OPEN_DIALOG = (By.CSS_SELECTOR, "div[role='dialog'], div[role='alertdialog']")
    FORM_SUBMIT_BUTTON = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL_BUTTON = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    def wait_for_dialog_open(
        self,
        testid: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> WebElement:
        """Wait until a MUI Dialog is visible.

        Without ``testid`` this matches *any* open dialog via the ARIA
        ``role="dialog"`` attribute, which MUI renders on every open Dialog
        regardless of component-specific testids.  Pass ``testid`` to lock
        onto a specific dialog when more than one might be open.
        """
        if testid:
            locator = (By.CSS_SELECTOR, f"[data-testid='{testid}']")
        else:
            locator = self.OPEN_DIALOG
        return self.wait_for_element_visible(locator, timeout)

    def wait_for_dialog_closed(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until no open MUI Dialog is visible (matches any role)."""
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.OPEN_DIALOG)
        )

    def is_dialog_open(self, testid: str | None = None) -> bool:
        """Return True if a dialog (any, or matching testid) is currently visible."""
        if testid:
            els = self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{testid}']")
        else:
            els = self.driver.find_elements(*self.OPEN_DIALOG)
        return any(el.is_displayed() for el in els)

    def click_form_submit(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Click the FormActions submit button (``form-submit-button``)."""
        self.click_locator_with_retry(self.FORM_SUBMIT_BUTTON, timeout=timeout)

    def click_form_cancel(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Click the FormActions cancel button (``form-cancel-button``)."""
        self.click_locator_with_retry(self.FORM_CANCEL_BUTTON, timeout=timeout)

    def find_form_field_input(self, field_name: str) -> WebElement:
        """Find the actual input/textarea/select inside a ``form-field-<name>``.

        Mirrors the FormTextField/FormNumberField wrapper convention.
        Falls back to a direct ``name`` attribute lookup if the wrapper is
        absent (e.g. legacy fields).
        """
        wrapper = self.driver.find_elements(
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}']",
        )
        if wrapper:
            inputs = wrapper[0].find_elements(
                By.CSS_SELECTOR, "input, textarea, [role='combobox']"
            )
            if inputs:
                return inputs[0]
        # Fallback: direct name attribute on input
        return self.driver.find_element(
            By.CSS_SELECTOR, f"input[name='{field_name}'], textarea[name='{field_name}']"
        )

    def fill_form_field(self, field_name: str, value: str) -> None:
        """Fill a form field identified by ``data-testid='form-field-<name>'``."""
        self.clear_and_fill(self.find_form_field_input(field_name), value)

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
