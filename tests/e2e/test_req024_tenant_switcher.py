"""E2E tests for REQ-024 — Tenant Switcher.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-024.md):
  TC-REQ-024-019  ->  TC-024-008  Tenant-Switcher zeigt alle Tenants mit Rolle und Typ-Icon
  TC-REQ-024-020  ->  TC-024-008  Dropdown zeigt Tenant-Namen
  TC-REQ-024-021  ->  TC-024-008  Dropdown oeffnet sich mit Tenant-Liste
  TC-REQ-024-022  ->  TC-024-008  Aktiver Tenant ist hervorgehoben
  TC-REQ-024-023  ->  TC-024-008  Dropdown hat 'Organisation erstellen' Eintrag
  TC-REQ-024-024  ->  TC-024-008  'Organisation erstellen' navigiert zu /tenants/create
  TC-REQ-024-025  ->  TC-024-009  Tenant wechseln -- URL und Daten aktualisieren sich
  TC-REQ-024-026  ->  TC-024-010  Tenant-Switcher persistiert letzten aktiven Tenant
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import LoginPage, TenantSwitcherPage

pytestmark = pytest.mark.requires_auth


# -- Demo credentials ---------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.local"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures -----------------------------------------------------------------


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


# -- TC-024-008: Tenant Switcher displays tenants -----------------------------


class TestTenantSwitcherDisplay:
    """Tenant Switcher display and interaction (Spec: TC-024-008 to TC-024-011)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_switcher_shows_active_tenant_name(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-019: Active tenant name is displayed in the App Bar.

        Spec: TC-024-008 -- Tenant-Switcher zeigt alle Tenants mit Rolle und Typ-Icon.
        """
        _ensure_logged_in(login_page)
        screenshot(
            "TC-REQ-024-019_dashboard-with-switcher",
            "Dashboard showing tenant switcher in app bar",
        )

        name = switcher.get_active_tenant_name()
        assert name, (
            "TC-REQ-024-019 FAIL: Expected active tenant name to be displayed"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_switcher_opens_dropdown_with_tenants(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-021: Clicking the switcher opens a dropdown with tenant list.

        Spec: TC-024-008 -- Tenant-Switcher Dropdown oeffnet sich.
        """
        _ensure_logged_in(login_page)
        switcher.open_menu()
        screenshot(
            "TC-REQ-024-021_switcher-dropdown-open",
            "Tenant switcher dropdown opened",
        )

        assert switcher.is_menu_open(), (
            "TC-REQ-024-021 FAIL: Expected tenant switcher dropdown to be open"
        )

        tenant_count = switcher.get_tenant_count()
        assert tenant_count >= 1, (
            f"TC-REQ-024-021 FAIL: Expected at least 1 tenant, got: {tenant_count}"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_switcher_shows_tenant_names(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-020: Dropdown shows tenant names.

        Spec: TC-024-008 -- Tenant-Switcher zeigt Tenant-Namen.
        """
        _ensure_logged_in(login_page)
        switcher.open_menu()

        names = switcher.get_tenant_names()
        screenshot(
            "TC-REQ-024-020_switcher-tenant-names",
            "Tenant names in switcher dropdown",
        )

        assert len(names) >= 1, (
            f"TC-REQ-024-020 FAIL: Expected at least 1 tenant name, got: {names}"
        )
        for name in names:
            assert name, "TC-REQ-024-020 FAIL: Expected each tenant entry to have a non-empty name"

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_switcher_highlights_active_tenant(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-022: Active tenant is highlighted with selected state and check icon.

        Spec: TC-024-008 -- Aktiver Tenant ist hervorgehoben.
        """
        _ensure_logged_in(login_page)
        switcher.open_menu()
        screenshot(
            "TC-REQ-024-022_switcher-active-highlight",
            "Active tenant highlighted in switcher",
        )

        selected = switcher.get_selected_tenant_name()
        assert selected, (
            "TC-REQ-024-022 FAIL: Expected one tenant to be marked as selected"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_switcher_has_create_organization_item(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-023: Dropdown has a 'Create organization' item at the bottom.

        Spec: TC-024-008 -- Dropdown hat 'Organisation erstellen' Eintrag.
        """
        _ensure_logged_in(login_page)
        switcher.open_menu()

        assert switcher.has_create_org_item(), (
            "TC-REQ-024-023 FAIL: Expected 'Create organization' menu item in switcher"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_switcher_create_org_navigates_to_create_page(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-024: Clicking 'Create organization' navigates to /tenants/create.

        Spec: TC-024-008 -- 'Organisation erstellen' navigiert zu /tenants/create.
        """
        _ensure_logged_in(login_page)
        switcher.open_menu()
        screenshot(
            "TC-REQ-024-024_before-create-org-click",
            "Switcher before clicking create organization",
        )

        switcher.click_create_organization()
        switcher.wait_for_url_contains("/tenants/create")
        screenshot(
            "TC-REQ-024-024_after-create-org-click",
            "After clicking create organization in switcher",
        )

        current_url = switcher.driver.current_url
        assert "/tenants/create" in current_url, (
            f"TC-REQ-024-024 FAIL: Expected /tenants/create, got: {current_url}"
        )


# -- TC-024-009: Tenant switching ---------------------------------------------


class TestTenantSwitching:
    """Switching between tenants (Spec: TC-024-009, TC-024-010)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_switch_tenant_updates_active_name(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-025: Switching tenant updates the active tenant name.

        Spec: TC-024-009 -- Tenant wechseln -- URL und Daten aktualisieren sich.
        """
        _ensure_logged_in(login_page)
        switcher.open_menu()

        names = switcher.get_tenant_names()
        if len(names) < 2:
            pytest.skip("Need at least 2 tenants to test switching")

        current_active = switcher.get_selected_tenant_name()
        target = next(n for n in names if n != current_active)

        screenshot(
            "TC-REQ-024-025_before-tenant-switch",
            f"Before switching from '{current_active}' to '{target}'",
        )

        switcher.switch_to_tenant(target)

        switcher.wait_for_element(
            switcher.TRIGGER_BUTTON_ALT, timeout=20
        )
        screenshot(
            "TC-REQ-024-025_after-tenant-switch",
            f"After switching to '{target}'",
        )

        new_active = switcher.get_active_tenant_name()
        assert new_active == target, (
            f"TC-REQ-024-025 FAIL: Expected active tenant '{target}', got: '{new_active}'"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_tenant_persists_after_reload(
        self,
        login_page: LoginPage,
        switcher: TenantSwitcherPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-026: Selected tenant persists after browser reload.

        Spec: TC-024-010 -- Tenant-Switcher persistiert letzten aktiven Tenant nach Reload.
        """
        _ensure_logged_in(login_page)

        active_before = switcher.get_active_tenant_name()
        screenshot(
            "TC-REQ-024-026_before-reload",
            f"Active tenant before reload: '{active_before}'",
        )

        switcher.driver.refresh()
        switcher.wait_for_element(
            switcher.TRIGGER_BUTTON_ALT, timeout=20
        )
        screenshot(
            "TC-REQ-024-026_after-reload",
            "After page reload",
        )

        active_after = switcher.get_active_tenant_name()
        assert active_after == active_before, (
            f"TC-REQ-024-026 FAIL: Expected tenant '{active_before}' to persist, got: '{active_after}'"
        )
