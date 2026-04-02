"""E2E tests for REQ-001 — Navigation and Routing.

In light mode the sidebar shows only top-level sections (Dashboard,
Pflanzeninstanzen, Aufgabenwarteschlange ...).  The Stammdaten sub-pages
(Botanical Families, Species, Companion Planting, Crop Rotation) are
accessible via direct URL — so these tests navigate directly instead of
clicking sidebar links.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-001  ->  TC-001-001  Botanische Familienliste wird vollstaendig geladen
  TC-REQ-001-002  ->  TC-001-019  Species-Liste laden und Grundspalten pruefen
  TC-REQ-001-003  ->  TC-001-030  Species-Detailseite — Mischkultur-Tab (Seite navigieren)
  TC-REQ-001-004  ->  TC-001-050  Fruchtfolge-Seite oeffnen
  TC-REQ-001-005  ->  TC-001-068, TC-001-069  Ungueltige URL — nicht gefunden
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BasePage


@pytest.fixture
def page(browser: WebDriver, base_url: str) -> BasePage:
    return BasePage(browser, base_url)


class TestNavigationAndRouting:
    """Navigation and routing (Spec: TC-001-001, TC-001-019, TC-001-030, TC-001-050, TC-001-068)."""

    @pytest.mark.smoke
    def test_navigate_to_botanical_families(
        self, page: BasePage, browser: WebDriver, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-001: Navigate to Botanical Families list.

        Spec: TC-001-001 -- Botanische Familienliste wird vollstaendig geladen und angezeigt.
        """
        page.navigate("/stammdaten/botanical-families")
        page.wait_for_element((By.CSS_SELECTOR, "[data-testid='page-title']"))
        screenshot("TC-REQ-001-001_families-page", "Botanical families page after navigation")

        assert "/stammdaten/botanical-families" in browser.current_url, (
            f"TC-REQ-001-001 FAIL: URL should contain /stammdaten/botanical-families, got {browser.current_url}"
        )
        title = page.get_page_title()
        assert "Botanische Familien" in title, (
            f"TC-REQ-001-001 FAIL: Expected 'Botanische Familien', got '{title}'"
        )

    @pytest.mark.smoke
    def test_navigate_to_species(
        self, page: BasePage, browser: WebDriver, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-002: Navigate to Species list.

        Spec: TC-001-019 -- Species-Liste laden und Grundspalten pruefen.
        """
        page.navigate("/stammdaten/species")
        page.wait_for_element((By.CSS_SELECTOR, "[data-testid='page-title']"))
        screenshot("TC-REQ-001-002_species-page", "Species page after navigation")

        assert "/stammdaten/species" in browser.current_url, (
            f"TC-REQ-001-002 FAIL: URL should contain /stammdaten/species, got {browser.current_url}"
        )
        title = page.get_page_title()
        assert "Arten" in title, (
            f"TC-REQ-001-002 FAIL: Expected 'Arten', got '{title}'"
        )

    @pytest.mark.smoke
    def test_navigate_to_companion_planting(
        self, page: BasePage, browser: WebDriver, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-003: Navigate to Companion Planting page.

        Spec: TC-001-030 -- Mischkultur-Seite navigieren.
        """
        page.navigate("/stammdaten/companion-planting")
        page.wait_for_element((By.CSS_SELECTOR, "[data-testid='page-title']"))
        screenshot("TC-REQ-001-003_companion-page", "Companion planting page after navigation")

        assert "/stammdaten/companion-planting" in browser.current_url, (
            f"TC-REQ-001-003 FAIL: URL should contain /stammdaten/companion-planting, got {browser.current_url}"
        )
        title = page.get_page_title()
        assert "Mischkultur" in title, (
            f"TC-REQ-001-003 FAIL: Expected 'Mischkultur', got '{title}'"
        )

    @pytest.mark.smoke
    def test_navigate_to_crop_rotation(
        self, page: BasePage, browser: WebDriver, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-004: Navigate to Crop Rotation page.

        Spec: TC-001-050 -- Fruchtfolge-Seite oeffnen.
        """
        page.navigate("/stammdaten/crop-rotation")
        page.wait_for_element((By.CSS_SELECTOR, "[data-testid='page-title']"))
        screenshot("TC-REQ-001-004_rotation-page", "Crop rotation page after navigation")

        assert "/stammdaten/crop-rotation" in browser.current_url, (
            f"TC-REQ-001-004 FAIL: URL should contain /stammdaten/crop-rotation, got {browser.current_url}"
        )
        title = page.get_page_title()
        assert "Fruchtfolge" in title, (
            f"TC-REQ-001-004 FAIL: Expected 'Fruchtfolge', got '{title}'"
        )

    @pytest.mark.smoke
    def test_nonexistent_route_shows_not_found(
        self, page: BasePage, browser: WebDriver, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-005: Direct URL access to non-existent route shows 404.

        Spec: TC-001-068, TC-001-069 -- Ungueltige URL zeigt Fehlermeldung.
        """
        page.navigate("/stammdaten/nonexistent")
        page.wait_for_loading_complete()
        screenshot("TC-REQ-001-005_not-found", "Not found page for non-existent route")

        body = browser.find_element(By.TAG_NAME, "body").text
        assert any(
            text in body for text in ["Seite nicht gefunden", "nicht gefunden", "404", "Not Found"]
        ), f"TC-REQ-001-005 FAIL: Expected 'not found' text, got: {body[:200]}"
