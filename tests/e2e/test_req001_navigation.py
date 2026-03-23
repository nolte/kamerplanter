"""E2E tests for REQ-001 — Navigation and Routing (TC-001 to TC-005).

In light mode the sidebar shows only top-level sections (Dashboard,
Pflanzeninstanzen, Aufgabenwarteschlange …).  The Stammdaten sub-pages
(Botanical Families, Species, Companion Planting, Crop Rotation) are
accessible via direct URL — so these tests navigate directly instead of
clicking sidebar links.
"""

from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BasePage


@pytest.fixture
def page(browser: WebDriver, base_url: str) -> BasePage:
    return BasePage(browser, base_url)


class TestNavigationAndRouting:
    """TC-REQ-001-001 to TC-REQ-001-005: Navigation and routing."""

    def test_navigate_to_botanical_families(
        self, page: BasePage, browser: WebDriver
    ) -> None:
        """TC-REQ-001-001: Navigate to Botanical Families list."""
        page.navigate("/stammdaten/botanical-families")
        page.wait_for_element((By.CSS_SELECTOR, "[data-testid='page-title']"))

        assert "/stammdaten/botanical-families" in browser.current_url, (
            f"URL should contain /stammdaten/botanical-families, got {browser.current_url}"
        )
        title = page.get_page_title()
        assert "Botanische Familien" in title, f"Expected 'Botanische Familien', got '{title}'"

    def test_navigate_to_species(
        self, page: BasePage, browser: WebDriver
    ) -> None:
        """TC-REQ-001-002: Navigate to Species list."""
        page.navigate("/stammdaten/species")
        page.wait_for_element((By.CSS_SELECTOR, "[data-testid='page-title']"))

        assert "/stammdaten/species" in browser.current_url
        title = page.get_page_title()
        assert "Arten" in title, f"Expected 'Arten', got '{title}'"

    def test_navigate_to_companion_planting(
        self, page: BasePage, browser: WebDriver
    ) -> None:
        """TC-REQ-001-003: Navigate to Companion Planting page."""
        page.navigate("/stammdaten/companion-planting")
        page.wait_for_element((By.CSS_SELECTOR, "[data-testid='page-title']"))

        assert "/stammdaten/companion-planting" in browser.current_url
        title = page.get_page_title()
        assert "Mischkultur" in title, f"Expected 'Mischkultur', got '{title}'"

    def test_navigate_to_crop_rotation(
        self, page: BasePage, browser: WebDriver
    ) -> None:
        """TC-REQ-001-004: Navigate to Crop Rotation page."""
        page.navigate("/stammdaten/crop-rotation")
        page.wait_for_element((By.CSS_SELECTOR, "[data-testid='page-title']"))

        assert "/stammdaten/crop-rotation" in browser.current_url
        title = page.get_page_title()
        assert "Fruchtfolge" in title, f"Expected 'Fruchtfolge', got '{title}'"

    def test_nonexistent_route_shows_not_found(
        self, page: BasePage, browser: WebDriver
    ) -> None:
        """TC-REQ-001-005: Direct URL access to non-existent route shows 404."""
        import time

        page.navigate("/stammdaten/nonexistent")
        time.sleep(2)  # Wait for lazy-loaded NotFoundPage to render

        body = browser.find_element(By.TAG_NAME, "body").text
        assert any(
            text in body for text in ["Seite nicht gefunden", "nicht gefunden", "404", "Not Found"]
        ), f"Expected 'not found' text, got: {body[:200]}"
