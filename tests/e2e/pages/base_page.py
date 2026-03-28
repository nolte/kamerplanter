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
        """Scroll an element into view and click it, falling back to JS click."""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        try:
            element.click()
        except (ElementNotInteractableException, ElementClickInterceptedException):
            self.driver.execute_script("arguments[0].click();", element)

    def clear_and_fill(self, element: WebElement, value: str) -> None:
        """Reliably clear an input element and type a new value.

        Uses JavaScript to clear the field value and dispatch native input/change
        events so that React controlled components pick up the change.  This
        works around ``InvalidElementStateException`` and ``Keys.CONTROL + "a"``
        failures in headless Chrome via Selenium Grid (Remote WebDriver).
        """
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
        element.send_keys(value)

    # ── Screenshots ───────────────────────────────────────────────────────

    def take_screenshot(self, name: str, output_dir: Path) -> Path:
        """Save a PNG screenshot and return the file path."""
        filepath = output_dir / f"{name}.png"
        self.driver.save_screenshot(str(filepath))
        return filepath
