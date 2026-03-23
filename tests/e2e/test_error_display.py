"""E2E tests for error display — NFR-006."""

from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BasePage


@pytest.fixture
def page(browser: WebDriver, base_url: str) -> BasePage:
    return BasePage(browser, base_url)


class TestErrorDisplay:
    """Error pages and error display component."""

    def test_404_page(self, page: BasePage) -> None:
        """Navigating to an unknown route shows the NotFound page."""
        page.navigate("/this-route-does-not-exist-e2e-test")
        el = page.wait_for_element(
            (By.CSS_SELECTOR, "[data-testid='error-page']")
        )
        assert el.is_displayed(), "Error page should be visible"

        # The page title or body should indicate a 404 state
        page_text = el.text
        assert "404" in page_text, (
            "Page should display 404 text"
        )

    def test_nonexistent_entity(self, page: BasePage) -> None:
        """Accessing a non-existent entity shows an error display."""
        page.navigate("/pflanzen/plant-instances/nonexistent-key-e2e-12345")
        # Either ErrorDisplay or NotFound should appear
        page.wait_for_element(
            (
                By.CSS_SELECTOR,
                "[data-testid='error-display'], [data-testid='error-page']",
            )
        )
        error_elements = page.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='error-display']"
        )
        not_found_elements = page.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='error-page']"
        )
        assert (
            len(error_elements) > 0 or len(not_found_elements) > 0
        ), "Either error display or not-found page should appear"
