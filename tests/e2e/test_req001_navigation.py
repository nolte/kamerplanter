"""E2E tests for REQ-001 — Navigation and Routing (TC-001 to TC-005)."""

from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BasePage


@pytest.fixture
def page(browser: WebDriver, base_url: str) -> BasePage:
    return BasePage(browser, base_url)


class TestNavigationAndRouting:
    """TC-REQ-001-001 to TC-REQ-001-005: Sidebar navigation and routing."""

    def test_navigate_to_botanical_families_via_sidebar(
        self, page: BasePage, browser: WebDriver
    ) -> None:
        """TC-REQ-001-001: Navigate to Botanical Families list via sidebar."""
        page.navigate("/")
        sidebar_item = page.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='nav-/stammdaten/botanical-families']")
        )
        sidebar_item.click()
        page.wait_for_url_contains("/stammdaten/botanical-families")

        assert "/stammdaten/botanical-families" in browser.current_url, (
            f"URL should contain /stammdaten/botanical-families, got {browser.current_url}"
        )
        title = page.get_page_title()
        assert "Botanische Familien" in title, f"Expected 'Botanische Familien', got '{title}'"

    def test_navigate_to_species_via_sidebar(
        self, page: BasePage, browser: WebDriver
    ) -> None:
        """TC-REQ-001-002: Navigate to Species list via sidebar."""
        page.navigate("/")
        sidebar_item = page.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='nav-/stammdaten/species']")
        )
        sidebar_item.click()
        page.wait_for_url_contains("/stammdaten/species")

        assert "/stammdaten/species" in browser.current_url
        title = page.get_page_title()
        assert "Arten" in title, f"Expected 'Arten', got '{title}'"

    def test_navigate_to_companion_planting_via_sidebar(
        self, page: BasePage, browser: WebDriver
    ) -> None:
        """TC-REQ-001-003: Navigate to Companion Planting page via sidebar."""
        page.navigate("/")
        sidebar_item = page.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='nav-/stammdaten/companion-planting']")
        )
        sidebar_item.click()
        page.wait_for_url_contains("/stammdaten/companion-planting")

        assert "/stammdaten/companion-planting" in browser.current_url
        title = page.get_page_title()
        assert "Mischkultur" in title, f"Expected 'Mischkultur', got '{title}'"

    def test_navigate_to_crop_rotation_via_sidebar(
        self, page: BasePage, browser: WebDriver
    ) -> None:
        """TC-REQ-001-004: Navigate to Crop Rotation page via sidebar."""
        page.navigate("/")
        sidebar_item = page.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='nav-/stammdaten/crop-rotation']")
        )
        sidebar_item.click()
        page.wait_for_url_contains("/stammdaten/crop-rotation")

        assert "/stammdaten/crop-rotation" in browser.current_url
        title = page.get_page_title()
        assert "Fruchtfolge" in title, f"Expected 'Fruchtfolge', got '{title}'"

    def test_nonexistent_route_shows_not_found(
        self, page: BasePage, browser: WebDriver
    ) -> None:
        """TC-REQ-001-005: Direct URL access to non-existent route shows 404."""
        page.navigate("/stammdaten/nonexistent")

        # Look for "not found" text
        body = browser.find_element(By.TAG_NAME, "body").text
        assert any(
            text in body for text in ["Seite nicht gefunden", "nicht gefunden", "404"]
        ), f"Expected 'not found' text, got: {body[:200]}"
