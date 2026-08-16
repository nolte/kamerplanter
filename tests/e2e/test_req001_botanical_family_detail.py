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
    # Asserted, not skipped. The seed ships 18 botanical families and they are
    # global reference data, so an empty catalogue is a broken stack, not a
    # reason to report a neutral result — and a skip here silently removes every
    # case in this file at once.
    assert family_list.get_row_count() > 0, (
        "TC-REQ-001 SETUP: the botanical-family catalogue is empty. The seed ships 18 "
        "global families, so this is a stack or seeding failure, not a missing fixture."
    )
    family_list.click_row(0)
    family_list.wait_for_url_contains("/stammdaten/botanical-families/")
    return family_list.driver.current_url


# Every case below either edits, deletes, or asserts the delete affordance, and
# #1120 made those platform-admin-only. In full mode they therefore run as the
# seeded admin account (#1155); in light mode the marker is a no-op, because the
# sole operator already is that admin (REQ-027).
@pytest.mark.platform_admin
class TestBotanicalFamilyDetailPage:
    """Detail page view, edit, delete (Spec: TC-001-005, TC-001-010, TC-001-011, TC-001-012)."""

    @pytest.mark.smoke
    def test_display_detail_page_with_populated_form(
        self,
        family_list: BotanicalFamilyListPage,
        detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-005: Display detail page with populated form.

        Spec: TC-001-005 -- Navigation von Liste zu Detailansicht einer Botanischen Familie.
        """
        _navigate_to_first_family_detail(family_list)
        screenshot(
            "TC-REQ-001-023_detail-loaded", "Botanical family detail page with populated form"
        )

        title = detail_page.get_title()
        assert title, "TC-REQ-001-023 FAIL: Page title should not be empty"

        name = detail_page.get_field_value("name")
        assert name, "TC-REQ-001-023 FAIL: Name field should be populated"

        assert detail_page.has_delete_button(), (
            "TC-REQ-001-023 FAIL: Delete button should be visible"
        )

    @pytest.mark.core_crud
    def test_edit_family_and_save(
        self,
        app_mode: str,
        family_list: BotanicalFamilyListPage,
        detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-010: Edit a botanical family and save changes.

        Spec: TC-001-010 -- Botanische Familie bearbeiten und speichern.

        **Light mode only, since #1120.** The PUT is platform-admin-only now, and
        the demo user in full mode is deliberately an ordinary member. Left
        running there it would not fail — its only assertion is that the URL is
        still the detail route, which a refused save satisfies too — so it would
        have gone on reporting green while testing nothing. Skipping full mode was
        the honest answer while the demo user was the only account; running as the
        seeded admin (#1155) is the better one. The refusal itself stays pinned at
        the API tier (`test_botanical_family_role_gate.py`), where a 403 is
        observable without a browser.
        """
        _navigate_to_first_family_detail(family_list)
        screenshot("TC-REQ-001-024_before-edit", "Family detail page before editing")

        unique = uuid.uuid4().hex[:6]
        detail_page.set_textarea("description", f"E2E-Updated description {unique}")
        screenshot(
            "TC-REQ-001-024_field-modified",
            f"Description changed to E2E-Updated description {unique}",
        )

        detail_page.click_save()

        detail_page.wait_for_loading_complete()
        screenshot("TC-REQ-001-024_after-save", "Family detail page after saving")

        # Verify the page remains on detail view (no redirect)
        assert "/stammdaten/botanical-families/" in detail_page.driver.current_url, (
            f"TC-REQ-001-024 FAIL: Expected detail URL, got {detail_page.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_cancel_deletion_keeps_family(
        self,
        family_list: BotanicalFamilyListPage,
        detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-012: Cancel deletion keeps the family.

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

        assert detail_page.wait_for_confirm_dialog_closed(), (
            "TC-REQ-001-027 FAIL: Dialog should close after cancel"
        )
        assert "/stammdaten/botanical-families/" in detail_page.driver.current_url, (
            f"TC-REQ-001-027 FAIL: Should remain on detail page, got {detail_page.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_delete_family_with_confirmation(
        self,
        app_mode: str,
        family_list: BotanicalFamilyListPage,
        detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path],
        browser: WebDriver,
        base_url: str,
    ) -> None:
        """TC-001-011: Delete a botanical family via confirmation dialog.

        Spec: TC-001-011 -- Botanische Familie loeschen mit Bestaetigungsdialog.

        **Light mode only, since #1120.** The case provisions the family it
        deletes, and that create is platform-admin-only now. In full mode the
        create was refused, the row lookup below then raised `ValueError`, and
        the `except` turned it into "Family not found after creation" — a skip
        that blames the search for an authorization refusal and quietly removed
        the delete happy path from three nightly profiles. Running as the seeded
        admin (#1155) puts it back in all four. The refusal stays pinned at the
        API tier (`test_botanical_family_role_gate.py`).
        """
        # First create a family to delete
        family_list.open()
        family_list.click_create()
        unique = uuid.uuid4().hex[:6]
        delete_name = f"Delete{unique}aceae"
        family_list.fill_create_form(delete_name)
        family_list.submit_create_form()
        # The exact post-condition of the create, not `wait_for_loading_complete()`:
        # that waits for a loading skeleton to *unmount*, and a refetch that
        # resolves before one renders leaves it waiting for nothing. The dialog
        # closes only after `await api.createBotanicalFamily(...)` resolves 2xx.
        # TC-001-006 learned this a few functions away in the create module; this
        # case had not picked it up.
        family_list.wait_for_create_dialog_closed()
        screenshot(
            "TC-REQ-001-026_family-created", f"Family {delete_name} created for deletion test"
        )

        # Found by searching, not by scanning whatever the table happens to show.
        # `click_row_by_name` reads the rendered page only, so a bare scan depends
        # on where the new row sorts and on whether the list has refetched at all
        # — and when it missed, the `except` turned an authorization or timing
        # failure into a neutral skip that blamed the search.
        family_list.open()
        family_list.search(delete_name)
        family_list.wait_for_search_applied(delete_name, what="botanical family list")
        family_list.click_row_by_name(delete_name)

        family_list.wait_for_url_contains("/stammdaten/botanical-families/")
        screenshot(
            "TC-REQ-001-026_detail-before-delete", f"Detail page of {delete_name} before deletion"
        )

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
        assert delete_name not in names, f"TC-REQ-001-026 FAIL: {delete_name} should be deleted"

    @pytest.mark.smoke
    def test_detail_page_nonexistent_key_shows_error(
        self, detail_page: BotanicalFamilyDetailPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-068: Detail page shows error for non-existent key.

        Spec: TC-001-068 -- Ungueltige URL — Botanische Familie nicht gefunden zeigt Fehlermeldung.
        """
        detail_page.navigate("/stammdaten/botanical-families/nonexistent123")
        # The skeleton-absence wait is satisfied before the lazy route chunk
        # mounts, so it cannot gate the read below; (ErrorDisplay | page root)
        # exhausts the route's settled states.
        detail_page.wait_for_any_present(
            (detail_page.ERROR_DISPLAY, detail_page.PAGE),
            "TC-REQ-001-028: botanical-family detail route for a non-existent key",
        )
        screenshot(
            "TC-REQ-001-028_nonexistent-key", "Detail page for non-existent botanical family key"
        )

        assert detail_page.is_error_displayed() or "nonexistent" not in detail_page.driver.title, (
            "TC-REQ-001-028 FAIL: Should show error display or not-found state"
        )


class TestDetailPageRoleGate:
    """The detail page offers no mutation to an ordinary member (Spec: TC-001-099)."""

    @pytest.mark.core_crud
    def test_delete_and_save_are_not_offered_to_an_ordinary_member(
        self,
        family_list: BotanicalFamilyListPage,
        detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path],
        app_mode: str,
    ) -> None:
        """TC-001-099: The detail page shows no delete or save to a non-admin.

        Spec: TC-001-099 -- Nur ein Plattform-Admin darf globale Botanische Familien anlegen.

        The list-page half of this rule is in the create module. This is the other
        end of the same dead end: before #1155 an ordinary member could edit every
        field on this page and press save, and the 403 arrived then.

        The explanation is the anchor rather than the absence, and deliberately
        so — a page still loading has no delete button either, and an absence read
        taken there would hold for an administrator too.
        """
        if app_mode == "light":
            pytest.skip(
                "light mode's sole anonymous operator is treated as platform admin "
                "(REQ-027), so there is no non-admin caller here"
            )

        _navigate_to_first_family_detail(family_list)
        assert detail_page.has_edit_denied_note(), (
            "TC-REQ-001-099 SETUP: the read-only explanation must have rendered before the "
            "absence of the delete button means anything — it arrives with the form"
        )
        screenshot("TC-REQ-001-099_detail-as-member", "Family detail page as an ordinary member")

        assert not detail_page.has_delete_button(), (
            "TC-REQ-001-099 FAIL: an ordinary member is offered delete on a global botanical "
            "family. The API refuses it with 403 (#1120), so the button is a dead end."
        )
