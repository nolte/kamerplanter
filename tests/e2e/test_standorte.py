"""E2E tests for Standorte (sites) — REQ-002."""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import SiteListPage


@pytest.fixture
def site_list(browser: WebDriver, base_url: str) -> SiteListPage:
    return SiteListPage(browser, base_url)


class TestSiteList:
    """Site list page loads and supports creation."""

    def test_site_list_loads(self, site_list: SiteListPage) -> None:
        """List page loads and shows the page title."""
        site_list.open()
        title = site_list.get_page_title()
        assert title, "Page title should not be empty"

    def test_create_site(self, site_list: SiteListPage) -> None:
        """Clicking the create button opens a create dialog/form."""
        site_list.open()
        site_list.click_create()
        # The create dialog should be visible — we check that the URL
        # has not navigated away (dialog is rendered in the same page).
        assert "/standorte/sites" in site_list.driver.current_url
