"""E2E tests for REQ-024 — Tenant Creation.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-024.md):
  TC-REQ-024-001  ->  TC-024-003  Organisations-Tenant erfolgreich erstellen -- Happy Path
  TC-REQ-024-002  ->  TC-024-003  TenantCreatePage laedt mit Titel und Formularfeldern
  TC-REQ-024-003  ->  TC-024-003  Einleitungstext wird angezeigt
  TC-REQ-024-004  ->  TC-024-004  Tenant erstellen -- Pflichtfeld 'Name' leer
  TC-REQ-024-005  ->  TC-024-005  Tenant erstellen -- Name zu kurz (1 Zeichen)
  TC-REQ-024-006  ->  TC-024-005  Tenant erstellen -- Name mit 2 Zeichen (Minimalgrenze)
  TC-REQ-024-007  ->  TC-024-003  Beschreibung ist optional
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import LoginPage, TenantCreatePage, TenantSwitcherPage

pytestmark = pytest.mark.requires_auth


# -- Demo credentials ---------------------------------------------------------
DEMO_EMAIL = "demo@kamerplanter.example"
DEMO_PASSWORD = "demo-passwort-2024"


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def login_page(browser: WebDriver, base_url: str) -> LoginPage:
    """Return a LoginPage bound to the test browser."""
    return LoginPage(browser, base_url)


@pytest.fixture
def create_page(browser: WebDriver, base_url: str) -> TenantCreatePage:
    """Return a TenantCreatePage bound to the test browser."""
    return TenantCreatePage(browser, base_url)


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


# -- TC-024-003: Create page loads --------------------------------------------


class TestTenantCreatePageLoad:
    """TenantCreatePage renders correctly (Spec: TC-024-003, TC-024-004)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_create_page_renders_with_title(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-002: TenantCreatePage loads with page title and form fields.

        Spec: TC-024-003 -- Organisations-Tenant erfolgreich erstellen -- Seitenstruktur.
        """
        _ensure_logged_in(login_page)
        create_page.open()
        screenshot(
            "TC-REQ-024-002_tenant-create-loaded",
            "TenantCreatePage after load",
        )

        title = create_page.get_page_title_text()
        assert title, (
            "TC-REQ-024-002 FAIL: Expected page title on TenantCreatePage"
        )

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_create_page_has_intro_text(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-003: Intro text is displayed below the title.

        Spec: TC-024-003 -- Organisations-Tenant erstellen -- Einleitungstext.
        """
        _ensure_logged_in(login_page)
        create_page.open()

        intro = create_page.get_intro_text()
        assert intro, (
            "TC-REQ-024-003 FAIL: Expected intro text on TenantCreatePage"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_submit_button_disabled_when_name_empty(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-004: Submit button is disabled when name field is empty.

        Spec: TC-024-004 -- Tenant erstellen -- Pflichtfeld 'Name' leer gelassen.
        """
        _ensure_logged_in(login_page)
        create_page.open()
        screenshot(
            "TC-REQ-024-004_create-empty-name",
            "Create page with empty name field",
        )

        assert not create_page.is_submit_enabled(), (
            "TC-REQ-024-004 FAIL: Submit button should be disabled when name is empty"
        )


# -- TC-024-003: Happy path creation ------------------------------------------


class TestTenantCreateHappyPath:
    """Create an organization tenant -- happy path (Spec: TC-024-003)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_create_organization_happy_path(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        switcher: TenantSwitcherPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-001: Create organization with name and description redirects to dashboard.

        Spec: TC-024-003 -- Organisations-Tenant erfolgreich erstellen -- Happy Path.
        """
        _ensure_logged_in(login_page)
        create_page.open()
        screenshot(
            "TC-REQ-024-001_create-before-fill",
            "Create page before filling form",
        )

        create_page.enter_name("Selenium Test Garten")
        create_page.enter_description("Automatisierter Testgarten fuer E2E-Tests")
        screenshot(
            "TC-REQ-024-001_create-form-filled",
            "Create page with filled form",
        )

        assert create_page.is_submit_enabled(), (
            "TC-REQ-024-001 FAIL: Submit button should be enabled after entering a valid name"
        )

        create_page.click_submit()
        screenshot(
            "TC-REQ-024-001_create-submitted",
            "After clicking submit on create form",
        )

        create_page.wait_for_url_contains("/dashboard")
        screenshot(
            "TC-REQ-024-001_create-success-dashboard",
            "Dashboard after successful tenant creation",
        )

        current_url = create_page.driver.current_url
        assert "/dashboard" in current_url, (
            f"TC-REQ-024-001 FAIL: Expected redirect to /dashboard, got: {current_url}"
        )


# -- TC-024-004 / TC-024-005: Validation --------------------------------------


class TestTenantCreateValidation:
    """Form validation on TenantCreatePage (Spec: TC-024-004, TC-024-005)."""

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_submit_disabled_for_single_character_name(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-005: Name with only 1 character keeps submit disabled (minLength=2).

        Spec: TC-024-005 -- Tenant erstellen -- Name zu kurz (1 Zeichen).
        """
        _ensure_logged_in(login_page)
        create_page.open()

        create_page.enter_name("A")
        screenshot(
            "TC-REQ-024-005_create-name-too-short",
            "Create page with 1-char name (too short)",
        )

        assert not create_page.is_submit_enabled(), (
            "TC-REQ-024-005 FAIL: Submit button should be disabled when name < 2 characters"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_submit_enabled_for_two_character_name(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-006: Name with exactly 2 characters enables submit.

        Spec: TC-024-005 -- Tenant erstellen -- Minimalgrenze 2 Zeichen.
        """
        _ensure_logged_in(login_page)
        create_page.open()

        create_page.enter_name("AB")
        screenshot(
            "TC-REQ-024-006_create-name-min-valid",
            "Create page with 2-char name (minimum valid)",
        )

        assert create_page.is_submit_enabled(), (
            "TC-REQ-024-006 FAIL: Submit button should be enabled when name has exactly 2 characters"
        )

    @pytest.mark.core_crud
    @pytest.mark.requires_auth
    def test_description_is_optional(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-024-007: Description field is optional -- submit works without it.

        Spec: TC-024-003 -- Beschreibung ist optional.
        """
        _ensure_logged_in(login_page)
        create_page.open()

        create_page.enter_name("Nur Name Garten")
        screenshot(
            "TC-REQ-024-007_create-no-description",
            "Create page with name only, no description",
        )

        assert create_page.is_submit_enabled(), (
            "TC-REQ-024-007 FAIL: Submit button should be enabled with only name filled"
        )
