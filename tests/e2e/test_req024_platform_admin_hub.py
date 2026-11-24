"""E2E tests for the platform admin hub ``/admin/platform`` (F-12, issue #2935).

Spec-TC Mapping (test -> spec/e2e-testcases/TC-REQ-023.md, Abschnitt 12):
  test_sidebar_entry_opens_the_hub     ->  TC-023-050  Platform-Admin-Panel sichtbar und ladbar
  test_member_sees_no_sidebar_entry    ->  TC-023-051  Nicht-Platform-Admin hat keinen Zugang
  test_member_is_refused_at_the_hub    ->  TC-023-051  Nicht-Platform-Admin hat keinen Zugang
  test_admin_page_back_link_returns_to_the_hub  ->  TC-023-080  Admin-Seiten führen zurück
  test_settings_page_has_no_platform_tab        ->  TC-023-081  Einstellungen ohne Plattform-Tab

Full mode only: the admin pages and the member/admin split exist there (in light
mode the sole operator is the platform admin). Accounts are chosen the way the
rest of the suite chooses them: ``@pytest.mark.platform_admin`` switches the
session browser to the seeded platform admin, no marker keeps it on the demo
member (``ensure_authenticated`` in ``conftest.py``). Neither class carries
``requires_auth`` — that marker makes ``ensure_authenticated`` skip the account
switch, which would leave each test on whichever account the previous test on
this worker had.

The platform administration used to be the *platform* tab of the account
settings page; it is now its own page, reached from a sidebar entry only
platform admins see.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.account_settings_page import AccountSettingsPage
from .pages.dashboard_page import DashboardPage
from .pages.platform_admin_page import PlatformAdminPage

SIDEBAR_SETTINGS_ENTRY = (By.CSS_SELECTOR, "[data-testid='nav-settings']")
# F-11 (#2935): the settings page has groups instead of tabs; the group entries
# are rendered on desktop (side navigation) and phone (group list) alike.
SETTINGS_PLATFORM_GROUP = (By.CSS_SELECTOR, "[data-testid='settings-group-platform']")
SETTINGS_ACCOUNT_GROUP = (By.CSS_SELECTOR, "[data-testid='settings-group-account']")


@pytest.fixture(autouse=True)
def _full_mode_only(app_mode: str) -> None:
    """Skip outside full mode — light mode has no member/admin split and no admin pages."""
    if app_mode != "full":
        pytest.skip("platform admin hub E2E needs full mode (accounts, admin pages)")


def _require_account(browser: WebDriver, expected: str) -> None:
    """Fail unless ``ensure_authenticated`` put the browser on *expected* ("admin"/"demo").

    The switch is the fixture's job; this only refuses to run a case as the wrong
    user, which would pass the member case as an admin or the admin case as a
    member without testing either.
    """
    actual = getattr(browser, "_kp_account", "demo")
    assert actual == expected, (
        f"Expected the session on the {expected!r} account, it is on {actual!r}"
    )


@pytest.fixture
def hub(browser: WebDriver, base_url: str) -> PlatformAdminPage:
    return PlatformAdminPage(browser, base_url)


@pytest.fixture
def dashboard(browser: WebDriver, base_url: str) -> DashboardPage:
    return DashboardPage(browser, base_url)


@pytest.fixture
def account_settings(browser: WebDriver, base_url: str) -> AccountSettingsPage:
    return AccountSettingsPage(browser, base_url)


@pytest.mark.platform_admin
class TestPlatformAdminHub:
    """A platform admin reaches the hub from the sidebar and it loads (F-12 acceptance-1, -3, -4)."""

    @pytest.fixture(autouse=True)
    def _as_platform_admin(self, browser: WebDriver) -> None:
        _require_account(browser, "admin")

    def test_sidebar_entry_opens_the_hub(
        self,
        dashboard: DashboardPage,
        hub: PlatformAdminPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-050: Platform-Admin-Panel sichtbar und ladbar — via the sidebar entry.

        Spec: TC-023-050 -- the panel opens and loads its statistics and tables.
        """
        dashboard.open()
        assert hub.has_nav_entry(), "Expected the platform admin sidebar entry for a platform admin"

        hub.open_via_sidebar()
        screenshot("F-12_hub-via-sidebar", "Platform admin hub opened from the sidebar")

        assert hub.driver.current_url.rstrip("/").endswith(PlatformAdminPage.PATH), (
            f"Expected the hub URL, got {hub.driver.current_url}"
        )
        assert hub.has_loaded_admin_data(), (
            "Expected the hub to load the admin data (statistics, tenant and user tables)"
        )

    def test_admin_page_back_link_returns_to_the_hub(
        self,
        hub: PlatformAdminPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-080: Admin-Seiten führen zur Plattform-Verwaltung zurück.

        Spec: TC-023-080 -- hub -> plans page -> back arrow lands on the hub again.
        """
        hub.open()
        hub.open_plans_and_return()
        screenshot("F-12_back-link-to-hub", "Plans page back link returned to the hub")

        assert hub.driver.current_url.rstrip("/").endswith(PlatformAdminPage.PATH), (
            f"Expected the back link to lead to the hub, got {hub.driver.current_url}"
        )

    def test_settings_page_has_no_platform_tab(
        self,
        account_settings: AccountSettingsPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-081: Kontoeinstellungen enthalten keine Plattform-Verwaltung mehr.

        Spec: TC-023-081 -- the old #platform address opens the settings without a platform entry.
        """
        account_settings.open_path("/settings#platform", SETTINGS_ACCOUNT_GROUP)
        account_settings.wait_for_element_visible(SETTINGS_ACCOUNT_GROUP)
        screenshot("F-12_settings-without-platform-tab", "Settings page after the move")

        assert account_settings.is_absent_within(SETTINGS_PLATFORM_GROUP), (
            "Expected no platform group on the settings page, also for a platform admin"
        )


class TestPlatformAdminHubRefusal:
    """A member who is not a platform admin neither sees nor reaches the hub (F-12 acceptance-2).

    No marker on purpose: ``ensure_authenticated`` then switches the session to
    the demo member, an ordinary tenant member without the platform attribute.
    """

    @pytest.fixture(autouse=True)
    def _as_member(self, browser: WebDriver) -> None:
        _require_account(browser, "demo")

    def test_member_sees_no_sidebar_entry(
        self,
        dashboard: DashboardPage,
        hub: PlatformAdminPage,
    ) -> None:
        """TC-023-051: Nicht-Platform-Admin hat keinen Zugang — no sidebar entry.

        Spec: TC-023-051 -- the admin panel is not offered to an ordinary member.
        """
        dashboard.open()
        hub.ensure_sidebar_open()
        # Anchor first: the settings entry beside it is rendered, so the absence
        # below is read off a mounted sidebar, not off one that is still empty.
        hub.wait_for_element_visible(SIDEBAR_SETTINGS_ENTRY)
        assert hub.is_absent_within(PlatformAdminPage.NAV_ENTRY), (
            "Expected no platform admin sidebar entry for an ordinary member"
        )

    def test_member_is_refused_at_the_hub(
        self,
        hub: PlatformAdminPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-023-051: Nicht-Platform-Admin hat keinen Zugang — the route refuses.

        Spec: TC-023-051 -- opening the address directly grants no access and no data.
        """
        state = hub.open_expecting_refusal()
        screenshot("F-12_hub-refused", "Platform admin hub refused for a member")

        hub.require_branch(state, "refused", "platform admin hub (non-admin)")
