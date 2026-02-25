"""E2E tests for the Dashboard page — REQ-009."""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import DashboardPage


@pytest.fixture
def dashboard(browser: WebDriver, base_url: str) -> DashboardPage:
    return DashboardPage(browser, base_url)


class TestDashboard:
    """Dashboard page loads and displays quick actions."""

    def test_dashboard_loads(self, dashboard: DashboardPage) -> None:
        """Page loads successfully and shows a welcome message."""
        dashboard.open()
        title = dashboard.get_page_title()
        assert title, "Page title should not be empty"

    def test_welcome_message_visible(self, dashboard: DashboardPage) -> None:
        """Welcome text is displayed on the dashboard."""
        dashboard.open()
        welcome = dashboard.get_welcome_text()
        assert welcome, "Welcome message should be visible"

    def test_quick_actions_present(self, dashboard: DashboardPage) -> None:
        """All 6 quick-action cards are rendered."""
        dashboard.open()
        actions = dashboard.get_quick_actions()
        assert len(actions) == 6, f"Expected 6 quick actions, got {len(actions)}"

    def test_quick_action_navigates(self, dashboard: DashboardPage) -> None:
        """Clicking a quick-action card navigates to the target page."""
        dashboard.open()
        dashboard.click_quick_action("/stammdaten/botanical-families")
        dashboard.wait_for_url_contains("/stammdaten/botanical-families")
        assert "/stammdaten/botanical-families" in dashboard.driver.current_url
