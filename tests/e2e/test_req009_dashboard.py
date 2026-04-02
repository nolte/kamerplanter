"""E2E tests for REQ-009 — Dashboard page and quick actions.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-009.md):
  TC-REQ-009-001  ->  TC-009-001  Dashboard-Seite aufrufen
  TC-REQ-009-002  ->  TC-009-001  Begrüssungstext sichtbar
  TC-REQ-009-003  ->  TC-009-001  Schnellaktionen-Kacheln vorhanden (6 Stück)
  TC-REQ-009-004  ->  TC-009-001  Schnellaktion navigiert zur Zielseite
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import DashboardPage


@pytest.fixture
def dashboard(browser: WebDriver, base_url: str) -> DashboardPage:
    return DashboardPage(browser, base_url)


class TestDashboardPage:
    """Dashboard page load and quick actions (Spec: TC-009-001, TC-009-002)."""

    @pytest.mark.smoke
    def test_dashboard_loads(
        self, dashboard: DashboardPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-009-001: Dashboard page loads and shows page title.

        Spec: TC-009-001 -- Dashboard-Seite aufrufen (authentifizierter Nutzer).
        """
        dashboard.open()
        screenshot("TC-REQ-009-001_dashboard-loaded", "Dashboard page after initial load — title and quick actions visible")

        title = dashboard.get_page_title()
        assert title, (
            "TC-REQ-009-001 FAIL: Page title should not be empty"
        )

    @pytest.mark.smoke
    def test_welcome_message_visible(
        self, dashboard: DashboardPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-009-002: Welcome text is displayed on the dashboard.

        Spec: TC-009-001 -- Begrüssungstext 'Willkommen bei Kamerplanter' ist sichtbar.
        """
        dashboard.open()
        welcome = dashboard.get_welcome_text()
        screenshot("TC-REQ-009-002_welcome-message", f"Dashboard welcome message: '{welcome}'")

        assert welcome, (
            "TC-REQ-009-002 FAIL: Welcome message should be visible on the dashboard"
        )

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_quick_actions_present(
        self, dashboard: DashboardPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-009-003: All quick-action cards are rendered.

        Spec: TC-009-001 -- Abschnitt 'Schnellaktionen' mit mindestens 6 Kacheln.
        """
        dashboard.open()
        actions = dashboard.get_quick_actions()
        screenshot("TC-REQ-009-003_quick-actions", f"Dashboard quick actions — {len(actions)} cards found")

        assert len(actions) >= 6, (
            f"TC-REQ-009-003 FAIL: Expected at least 6 quick actions, got {len(actions)}: {actions}"
        )

    @pytest.mark.core_crud
    def test_quick_action_navigates(
        self, dashboard: DashboardPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-009-004: Clicking a quick-action card navigates to the target page.

        Spec: TC-009-001 -- Schnellaktion-Kacheln fuehren zur jeweiligen Zielseite.
        """
        dashboard.open()
        screenshot("TC-REQ-009-004_before-click", "Dashboard before clicking quick-action card")

        dashboard.click_quick_action("/stammdaten/botanical-families")
        dashboard.wait_for_url_contains("/stammdaten/botanical-families")
        screenshot("TC-REQ-009-004_after-click", "Target page after quick-action navigation")

        assert "/stammdaten/botanical-families" in dashboard.driver.current_url, (
            f"TC-REQ-009-004 FAIL: Expected URL to contain '/stammdaten/botanical-families', "
            f"got '{dashboard.driver.current_url}'"
        )
