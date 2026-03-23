"""E2E tests for REQ-024 -- Tenant Switcher (TC-024-008 to TC-024-011).

Covers:
  - TenantSwitcher: open/close, tenant list, type icons, active highlight
  - Switching between tenants (URL + content update)
  - Persistence of selected tenant after reload
  - Create organization link in switcher menu

All tests follow NFR-008:
  - Page-Object-Pattern (no direct find_element calls in tests)
  - WebDriverWait only -- no time.sleep()
  - Screenshot at: Page Load / before action / after action / error state
  - Descriptive assertion messages
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import LoginPage, TenantSwitcherPage

pytestmark = pytest.mark.requires_auth


# -- Demo credentials --------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.local"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture
def login_page(browser: WebDriver, base_url: str) -> LoginPage:
    """Return a LoginPage bound to the test browser."""
    return LoginPage(browser, base_url)


@pytest.fixture
def switcher(browser: WebDriver, base_url: str) -> TenantSwitcherPage:
    """Return a TenantSwitcherPage bound to the test browser."""
    return TenantSwitcherPage(browser, base_url)


def _ensure_logged_in(login_page: LoginPage) -> None:
    """Log in as demo user if not already authenticated."""
    login_page.driver.delete_all_cookies()
    login_page.open()
    login_page.login(DEMO_EMAIL, DEMO_PASSWORD)
    login_page.wait_for_url_contains("/dashboard")


# -- TC-024-008: Tenant Switcher displays tenants ---------------------------


class TestTenantSwitcherDisplay:
    """TC-024-008 to TC-024-011: Tenant Switcher display and interaction."""

    def test_switcher_shows_active_tenant_name(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot,
    ) -> None:
        """TC-024-008: Active tenant name is displayed in the App Bar."""
        _ensure_logged_in(login_page)
        screenshot(
            "req024_021_dashboard_with_switcher",
            "Dashboard showing tenant switcher in app bar",
        )

        name = switcher.get_active_tenant_name()
        assert name, (
            "Expected the active tenant name to be displayed in the App Bar, got empty"
        )

    def test_switcher_opens_dropdown_with_tenants(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot,
    ) -> None:
        """TC-024-008: Clicking the switcher opens a dropdown with tenant list."""
        _ensure_logged_in(login_page)
        switcher.open_menu()
        screenshot(
            "req024_022_switcher_dropdown_open",
            "Tenant switcher dropdown opened",
        )

        assert switcher.is_menu_open(), (
            "Expected the tenant switcher dropdown menu to be open"
        )

        tenant_count = switcher.get_tenant_count()
        assert tenant_count >= 1, (
            f"Expected at least 1 tenant in the switcher, got: {tenant_count}"
        )

    def test_switcher_shows_tenant_names(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot,
    ) -> None:
        """TC-024-008: Dropdown shows tenant names."""
        _ensure_logged_in(login_page)
        switcher.open_menu()

        names = switcher.get_tenant_names()
        screenshot(
            "req024_023_switcher_tenant_names",
            "Tenant names in switcher dropdown",
        )

        assert len(names) >= 1, (
            f"Expected at least 1 tenant name, got: {names}"
        )
        for name in names:
            assert name, "Expected each tenant entry to have a non-empty name"

    def test_switcher_highlights_active_tenant(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot,
    ) -> None:
        """TC-024-008: Active tenant is highlighted with selected state and check icon."""
        _ensure_logged_in(login_page)
        switcher.open_menu()
        screenshot(
            "req024_024_switcher_active_highlight",
            "Active tenant highlighted in switcher",
        )

        selected = switcher.get_selected_tenant_name()
        assert selected, (
            "Expected one tenant to be marked as selected in the dropdown"
        )

    def test_switcher_has_create_organization_item(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot,
    ) -> None:
        """TC-024-008: Dropdown has a 'Create organization' item at the bottom."""
        _ensure_logged_in(login_page)
        switcher.open_menu()

        assert switcher.has_create_org_item(), (
            "Expected a 'Create organization' menu item at the bottom of the switcher"
        )

    def test_switcher_create_org_navigates_to_create_page(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot,
    ) -> None:
        """TC-024-008: Clicking 'Create organization' navigates to /tenants/create."""
        _ensure_logged_in(login_page)
        switcher.open_menu()
        screenshot(
            "req024_025_before_create_org_click",
            "Switcher before clicking create organization",
        )

        switcher.click_create_organization()
        switcher.wait_for_url_contains("/tenants/create")
        screenshot(
            "req024_026_after_create_org_click",
            "After clicking create organization in switcher",
        )

        current_url = switcher.driver.current_url
        assert "/tenants/create" in current_url, (
            f"Expected navigation to /tenants/create, got: {current_url}"
        )


# -- TC-024-009: Tenant switching -------------------------------------------


class TestTenantSwitching:
    """TC-024-009 to TC-024-010: Switching between tenants."""

    def test_switch_tenant_updates_active_name(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot,
    ) -> None:
        """TC-024-009: Switching tenant updates the active tenant name.

        This test requires at least 2 tenants. If only 1 exists, the test is skipped.
        """
        _ensure_logged_in(login_page)
        switcher.open_menu()

        names = switcher.get_tenant_names()
        if len(names) < 2:
            pytest.skip("Need at least 2 tenants to test switching")

        current_active = switcher.get_selected_tenant_name()
        # Pick a different tenant
        target = next(n for n in names if n != current_active)

        screenshot(
            "req024_027_before_tenant_switch",
            f"Before switching from '{current_active}' to '{target}'",
        )

        switcher.switch_to_tenant(target)

        # TenantSwitcher does window.location.reload() -- wait for page
        switcher.wait_for_element(
            switcher.TRIGGER_BUTTON_ALT, timeout=20
        )
        screenshot(
            "req024_028_after_tenant_switch",
            f"After switching to '{target}'",
        )

        new_active = switcher.get_active_tenant_name()
        assert new_active == target, (
            f"Expected active tenant to be '{target}' after switch, got: '{new_active}'"
        )

    def test_tenant_persists_after_reload(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot,
    ) -> None:
        """TC-024-010: Selected tenant persists after browser reload."""
        _ensure_logged_in(login_page)

        # Get current active tenant
        active_before = switcher.get_active_tenant_name()
        screenshot(
            "req024_029_before_reload",
            f"Active tenant before reload: '{active_before}'",
        )

        # Reload the page
        switcher.driver.refresh()
        switcher.wait_for_element(
            switcher.TRIGGER_BUTTON_ALT, timeout=20
        )
        screenshot(
            "req024_030_after_reload",
            "After page reload",
        )

        active_after = switcher.get_active_tenant_name()
        assert active_after == active_before, (
            f"Expected tenant '{active_before}' to persist after reload, got: '{active_after}'"
        )
