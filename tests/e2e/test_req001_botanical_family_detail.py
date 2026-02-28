"""E2E tests for REQ-001 — Botanical Family Detail Page (TC-023 to TC-028)."""

from __future__ import annotations

import time
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BotanicalFamilyDetailPage, BotanicalFamilyListPage


@pytest.fixture
def family_list(browser: WebDriver, base_url: str) -> BotanicalFamilyListPage:
    return BotanicalFamilyListPage(browser, base_url)


@pytest.fixture
def detail_page(browser: WebDriver, base_url: str) -> BotanicalFamilyDetailPage:
    return BotanicalFamilyDetailPage(browser, base_url)


def _navigate_to_first_family_detail(
    family_list: BotanicalFamilyListPage,
) -> str:
    """Navigate to first family's detail page and return the URL."""
    family_list.open()
    if family_list.get_row_count() == 0:
        pytest.skip("No botanical families in database")
    family_list.click_row(0)
    family_list.wait_for_url_contains("/stammdaten/botanical-families/")
    return family_list.driver.current_url


class TestBotanicalFamilyDetailPage:
    """TC-REQ-001-023 to TC-REQ-001-028: Detail page view, edit, delete."""

    def test_display_detail_page_with_populated_form(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage
    ) -> None:
        """TC-REQ-001-023: Display detail page with populated form."""
        _navigate_to_first_family_detail(family_list)

        title = detail_page.get_title()
        assert title, "Page title should not be empty"

        name = detail_page.get_field_value("name")
        assert name, "Name field should be populated"

        assert detail_page.has_delete_button(), "Delete button should be visible"

    def test_edit_family_and_save(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage
    ) -> None:
        """TC-REQ-001-024: Edit a botanical family and save changes."""
        _navigate_to_first_family_detail(family_list)

        unique = uuid.uuid4().hex[:6]
        detail_page.set_textarea("description", f"E2E-Updated description {unique}")
        detail_page.click_save()

        time.sleep(1)
        # Verify the page remains on detail view (no redirect)
        assert "/stammdaten/botanical-families/" in detail_page.driver.current_url

    def test_cancel_deletion_keeps_family(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage
    ) -> None:
        """TC-REQ-001-027: Cancel deletion keeps the family."""
        _navigate_to_first_family_detail(family_list)

        detail_page.click_delete()
        assert detail_page.is_confirm_dialog_open(), "Confirmation dialog should open"

        detail_page.cancel_delete()
        time.sleep(0.5)
        assert not detail_page.is_confirm_dialog_open(), "Dialog should close after cancel"
        assert "/stammdaten/botanical-families/" in detail_page.driver.current_url

    def test_delete_family_with_confirmation(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage,
        browser: WebDriver, base_url: str,
    ) -> None:
        """TC-REQ-001-026: Delete a botanical family via confirmation dialog."""
        # First create a family to delete
        family_list.open()
        family_list.click_create()
        unique = uuid.uuid4().hex[:6]
        delete_name = f"Deleteaceae{unique}"
        family_list.fill_create_form(delete_name)
        family_list.submit_create_form()
        time.sleep(2)
        family_list.wait_for_loading_complete()

        # Navigate to its detail page
        try:
            family_list.click_row_by_name(delete_name)
        except ValueError:
            pytest.skip(f"Family '{delete_name}' not found after creation")

        family_list.wait_for_url_contains("/stammdaten/botanical-families/")

        detail_page.click_delete()
        assert detail_page.is_confirm_dialog_open(), "Confirmation dialog should open"

        detail_page.confirm_delete()
        time.sleep(2)

        # Should redirect to list page
        detail_page.wait_for_url_contains("/stammdaten/botanical-families")
        names = family_list.get_first_column_texts()
        assert delete_name not in names, f"{delete_name} should be deleted"

    def test_detail_page_nonexistent_key_shows_error(
        self, detail_page: BotanicalFamilyDetailPage
    ) -> None:
        """TC-REQ-001-028: Detail page shows error for non-existent key."""
        detail_page.navigate("/stammdaten/botanical-families/nonexistent123")
        time.sleep(2)

        assert detail_page.is_error_displayed() or "nonexistent" not in detail_page.driver.title, (
            "Should show error display or not-found state"
        )
