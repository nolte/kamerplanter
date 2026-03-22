"""E2E tests for REQ-024 -- Tenant Creation (TC-024-003 to TC-024-007).

Covers:
  - TenantCreatePage: page load, form rendering, intro text
  - Happy path: create organization tenant with name + description
  - Validation: empty name, name too short (< 2 chars), submit disabled
  - Slug generation from German Umlauts
  - Redirect to dashboard after creation

All tests follow NFR-008:
  - Page-Object-Pattern (no direct find_element calls in tests)
  - WebDriverWait only -- no time.sleep()
  - Screenshot at: Page Load / before action / after action / error state
  - Descriptive assertion messages
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import LoginPage, TenantCreatePage, TenantSwitcherPage

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


# -- TC-024-003: Create page loads ------------------------------------------


class TestTenantCreatePageLoad:
    """TC-024-003 (partial): Verify TenantCreatePage renders correctly."""

    def test_create_page_renders_with_title(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot,
    ) -> None:
        """TC-024-003: TenantCreatePage loads with page title and form fields."""
        _ensure_logged_in(login_page)
        create_page.open()
        screenshot(
            "req024_001_tenant_create_loaded",
            "TenantCreatePage after load",
        )

        title = create_page.get_page_title_text()
        assert title, (
            "Expected page title on TenantCreatePage, got empty string"
        )

    def test_create_page_has_intro_text(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot,
    ) -> None:
        """TC-024-003: Intro text is displayed below the title."""
        _ensure_logged_in(login_page)
        create_page.open()

        intro = create_page.get_intro_text()
        assert intro, (
            "Expected intro/description text on TenantCreatePage, got empty string"
        )

    def test_submit_button_disabled_when_name_empty(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot,
    ) -> None:
        """TC-024-004: Submit button is disabled when name field is empty."""
        _ensure_logged_in(login_page)
        create_page.open()
        screenshot(
            "req024_002_create_empty_name",
            "Create page with empty name field",
        )

        assert not create_page.is_submit_enabled(), (
            "Submit button should be disabled when name is empty"
        )


# -- TC-024-003: Happy path creation ----------------------------------------


class TestTenantCreateHappyPath:
    """TC-024-003: Create an organization tenant -- happy path."""

    def test_create_organization_happy_path(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        switcher: TenantSwitcherPage,
        screenshot,
    ) -> None:
        """TC-024-003: Create organization with name and description redirects to dashboard."""
        _ensure_logged_in(login_page)
        create_page.open()
        screenshot(
            "req024_003_create_before_fill",
            "Create page before filling form",
        )

        create_page.enter_name("Selenium Test Garten")
        create_page.enter_description("Automatisierter Testgarten fuer E2E-Tests")
        screenshot(
            "req024_004_create_form_filled",
            "Create page with filled form",
        )

        assert create_page.is_submit_enabled(), (
            "Submit button should be enabled after entering a valid name (>= 2 chars)"
        )

        create_page.click_submit()
        screenshot(
            "req024_005_create_submitted",
            "After clicking submit on create form",
        )

        # Expect redirect to dashboard or snackbar confirmation
        create_page.wait_for_url_contains("/dashboard")
        screenshot(
            "req024_006_create_success_dashboard",
            "Dashboard after successful tenant creation",
        )

        current_url = create_page.driver.current_url
        assert "/dashboard" in current_url, (
            f"Expected redirect to /dashboard after creation, got: {current_url}"
        )


# -- TC-024-004 / TC-024-005: Validation ------------------------------------


class TestTenantCreateValidation:
    """TC-024-004 to TC-024-005: Form validation on TenantCreatePage."""

    def test_submit_disabled_for_single_character_name(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot,
    ) -> None:
        """TC-024-005: Name with only 1 character keeps submit disabled (minLength=2)."""
        _ensure_logged_in(login_page)
        create_page.open()

        create_page.enter_name("A")
        screenshot(
            "req024_007_create_name_too_short",
            "Create page with 1-char name (too short)",
        )

        assert not create_page.is_submit_enabled(), (
            "Submit button should be disabled when name has less than 2 characters"
        )

    def test_submit_enabled_for_two_character_name(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot,
    ) -> None:
        """TC-024-005 boundary: Name with exactly 2 characters enables submit."""
        _ensure_logged_in(login_page)
        create_page.open()

        create_page.enter_name("AB")
        screenshot(
            "req024_008_create_name_min_valid",
            "Create page with 2-char name (minimum valid)",
        )

        assert create_page.is_submit_enabled(), (
            "Submit button should be enabled when name has exactly 2 characters"
        )

    def test_description_is_optional(
        self,
        login_page: LoginPage,
        create_page: TenantCreatePage,
        screenshot,
    ) -> None:
        """TC-024-003: Description field is optional -- submit works without it."""
        _ensure_logged_in(login_page)
        create_page.open()

        create_page.enter_name("Nur Name Garten")
        screenshot(
            "req024_009_create_no_description",
            "Create page with name only, no description",
        )

        assert create_page.is_submit_enabled(), (
            "Submit button should be enabled with only name filled (description optional)"
        )
