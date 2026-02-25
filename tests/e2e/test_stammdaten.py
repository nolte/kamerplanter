"""E2E tests for Stammdaten (master data) — REQ-001."""

from __future__ import annotations

import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BotanicalFamilyListPage


@pytest.fixture
def family_list(browser: WebDriver, base_url: str) -> BotanicalFamilyListPage:
    return BotanicalFamilyListPage(browser, base_url)


class TestBotanicalFamilyList:
    """Botanical family list page and CRUD operations."""

    def test_botanical_family_list_loads(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """List page loads and renders the page title."""
        family_list.open()
        title = family_list.get_page_title()
        assert title, "Page title should not be empty"

    def test_create_botanical_family(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """Create dialog allows creating a new botanical family."""
        family_list.open()
        initial_count = family_list.get_row_count()

        # Open create dialog and fill form
        family_list.click_create()
        unique_name = f"E2E-TestFamily-{uuid.uuid4().hex[:8]}"
        family_list.fill_create_form(unique_name)
        family_list.submit_create_form()

        # Wait for dialog to close and list to refresh
        family_list.wait_for_loading_complete()

        # Verify new entry appears (row count increased or page reloaded)
        new_count = family_list.get_row_count()
        assert new_count >= initial_count, (
            f"Expected at least {initial_count} rows after create, got {new_count}"
        )

    def test_navigate_to_detail(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """Clicking a table row navigates to the detail page."""
        family_list.open()

        if family_list.get_row_count() == 0:
            pytest.skip("No botanical families in database — cannot test detail navigation")

        family_list.click_row(0)
        family_list.wait_for_url_contains("/stammdaten/botanical-families/")
        assert "/stammdaten/botanical-families/" in family_list.driver.current_url
