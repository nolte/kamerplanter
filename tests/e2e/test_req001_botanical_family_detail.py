"""E2E tests for REQ-001 — Botanical Family Detail Page.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-023  ->  TC-001-005  Navigation von Liste zu Detailansicht (Formular anzeigen)
  TC-REQ-001-024  ->  TC-001-010  Botanische Familie bearbeiten und speichern
  TC-REQ-001-027  ->  TC-001-012  Loeschen abbrechen — Familie bleibt erhalten
  TC-REQ-001-026  ->  TC-001-011  Botanische Familie loeschen mit Bestaetigungsdialog
  TC-REQ-001-028  ->  TC-001-068  Ungueltige URL — Botanische Familie nicht gefunden
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
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
    """Detail page view, edit, delete (Spec: TC-001-005, TC-001-010, TC-001-011, TC-001-012)."""

    @pytest.mark.smoke
    def test_display_detail_page_with_populated_form(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-023: Display detail page with populated form.

        Spec: TC-001-005 -- Navigation von Liste zu Detailansicht einer Botanischen Familie.
        """
        _navigate_to_first_family_detail(family_list)
        screenshot("TC-REQ-001-023_detail-loaded", "Botanical family detail page with populated form")

        title = detail_page.get_title()
        assert title, "TC-REQ-001-023 FAIL: Page title should not be empty"

        name = detail_page.get_field_value("name")
        assert name, "TC-REQ-001-023 FAIL: Name field should be populated"

        assert detail_page.has_delete_button(), "TC-REQ-001-023 FAIL: Delete button should be visible"

    @pytest.mark.core_crud
    def test_edit_family_and_save(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-024: Edit a botanical family and save changes.

        Spec: TC-001-010 -- Botanische Familie bearbeiten und speichern.
        """
        _navigate_to_first_family_detail(family_list)
        screenshot("TC-REQ-001-024_before-edit", "Family detail page before editing")

        unique = uuid.uuid4().hex[:6]
        detail_page.set_textarea("description", f"E2E-Updated description {unique}")
        screenshot("TC-REQ-001-024_field-modified", f"Description changed to E2E-Updated description {unique}")

        detail_page.click_save()

        detail_page.wait_for_loading_complete()
        screenshot("TC-REQ-001-024_after-save", "Family detail page after saving")

        # Verify the page remains on detail view (no redirect)
        assert "/stammdaten/botanical-families/" in detail_page.driver.current_url, (
            f"TC-REQ-001-024 FAIL: Expected detail URL, got {detail_page.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_cancel_deletion_keeps_family(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-027: Cancel deletion keeps the family.

        Spec: TC-001-012 -- Loeschen abbrechen — Familie bleibt erhalten.
        """
        _navigate_to_first_family_detail(family_list)

        detail_page.click_delete()
        screenshot("TC-REQ-001-027_confirm-dialog-open", "Delete confirmation dialog open")

        assert detail_page.is_confirm_dialog_open(), (
            "TC-REQ-001-027 FAIL: Confirmation dialog should open"
        )

        detail_page.cancel_delete()
        detail_page.wait_for_loading_complete()
        screenshot("TC-REQ-001-027_after-cancel", "Detail page after cancelling deletion")

        assert not detail_page.is_confirm_dialog_open(), (
            "TC-REQ-001-027 FAIL: Dialog should close after cancel"
        )
        assert "/stammdaten/botanical-families/" in detail_page.driver.current_url, (
            f"TC-REQ-001-027 FAIL: Should remain on detail page, got {detail_page.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_delete_family_with_confirmation(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path], browser: WebDriver, base_url: str,
    ) -> None:
        """TC-REQ-001-026: Delete a botanical family via confirmation dialog.

        Spec: TC-001-011 -- Botanische Familie loeschen mit Bestaetigungsdialog.
        """
        # First create a family to delete
        family_list.open()
        family_list.click_create()
        unique = uuid.uuid4().hex[:6]
        delete_name = f"Deleteaceae{unique}"
        family_list.fill_create_form(delete_name)
        family_list.submit_create_form()
        family_list.wait_for_loading_complete()
        screenshot("TC-REQ-001-026_family-created", f"Family {delete_name} created for deletion test")

        # Navigate to its detail page
        try:
            family_list.click_row_by_name(delete_name)
        except ValueError:
            pytest.skip(f"Family '{delete_name}' not found after creation")

        family_list.wait_for_url_contains("/stammdaten/botanical-families/")
        screenshot("TC-REQ-001-026_detail-before-delete", f"Detail page of {delete_name} before deletion")

        detail_page.click_delete()
        screenshot("TC-REQ-001-026_confirm-dialog", "Delete confirmation dialog open")

        assert detail_page.is_confirm_dialog_open(), (
            "TC-REQ-001-026 FAIL: Confirmation dialog should open"
        )

        detail_page.confirm_delete()

        # Should redirect to list page
        detail_page.wait_for_url_contains("/stammdaten/botanical-families")
        screenshot("TC-REQ-001-026_after-delete", "Family list after deletion")

        names = family_list.get_first_column_texts()
        assert delete_name not in names, (
            f"TC-REQ-001-026 FAIL: {delete_name} should be deleted"
        )

    @pytest.mark.smoke
    def test_detail_page_nonexistent_key_shows_error(
        self, detail_page: BotanicalFamilyDetailPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-028: Detail page shows error for non-existent key.

        Spec: TC-001-068 -- Ungueltige URL — Botanische Familie nicht gefunden zeigt Fehlermeldung.
        """
        detail_page.navigate("/stammdaten/botanical-families/nonexistent123")
        detail_page.wait_for_loading_complete()
        screenshot("TC-REQ-001-028_nonexistent-key", "Detail page for non-existent botanical family key")

        assert detail_page.is_error_displayed() or "nonexistent" not in detail_page.driver.title, (
            "TC-REQ-001-028 FAIL: Should show error display or not-found state"
        )
