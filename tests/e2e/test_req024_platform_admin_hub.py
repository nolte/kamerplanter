"""E2E tests for the platform admin hub ``/admin/platform`` (F-12, issue #2935).

Spec-TC Mapping (test -> spec/e2e-testcases/TC-REQ-023.md, Abschnitt 12):
  test_sidebar_entry_opens_the_hub     ->  TC-023-050  Platform-Admin-Panel sichtbar und ladbar
  test_member_sees_no_sidebar_entry    ->  TC-023-051  Nicht-Platform-Admin hat keinen Zugang
  test_member_is_refused_at_the_hub    ->  TC-023-051  Nicht-Platform-Admin hat keinen Zugang

The platform administration used to be the *platform* tab of the account
settings page (the location TC-023-050/051 still name). It is now its own page,
reached from a sidebar entry only platform admins see. The cases' intent — the
admin panel is visible and loads for a platform admin, and nobody else reaches
it or its data — is what these tests assert at the new location.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.dashboard_page import DashboardPage
from .pages.platform_admin_page import PlatformAdminPage

SIDEBAR_SETTINGS_ENTRY = (By.CSS_SELECTOR, "[data-testid='nav-settings']")


@pytest.fixture
def hub(browser: WebDriver, base_url: str) -> PlatformAdminPage:
    return PlatformAdminPage(browser, base_url)


@pytest.fixture
def dashboard(browser: WebDriver, base_url: str) -> DashboardPage:
    return DashboardPage(browser, base_url)


@pytest.mark.platform_admin
@pytest.mark.requires_auth
class TestPlatformAdminHub:
    """A platform admin reaches the hub from the sidebar and it loads (F-12 acceptance-1, -4)."""

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


@pytest.mark.requires_auth
class TestPlatformAdminHubRefusal:
    """A member who is not a platform admin neither sees nor reaches the hub (F-12 acceptance-2)."""

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
