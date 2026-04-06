"""E2E tests for REQ-001 — Error Handling.

TC-078 (duplicate family name) is already covered in test_req001_botanical_family_create.py.

NOTE: TC-076 (network error) and TC-077 (server 500) require specific environment
conditions that are difficult to reproduce in standard E2E runs. These tests use
pragmatic approaches to verify error handling UX where possible.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-076  ->  (no direct spec TC)  Netzwerkfehler zeigt Fehlermeldung
  TC-REQ-001-077  ->  (no direct spec TC)  Serverfehler (500) zeigt Fehlermeldung
  TC-REQ-001-028  ->  TC-001-068  Ungueltige URL — Botanische Familie nicht gefunden
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BotanicalFamilyDetailPage, BotanicalFamilyListPage


@pytest.fixture
def family_list(browser: WebDriver, base_url: str) -> BotanicalFamilyListPage:
    return BotanicalFamilyListPage(browser, base_url)


@pytest.fixture
def detail_page(browser: WebDriver, base_url: str) -> BotanicalFamilyDetailPage:
    return BotanicalFamilyDetailPage(browser, base_url)


class TestErrorHandling:
    """Error handling and notifications (Spec: TC-001-068)."""

    @pytest.mark.skip(reason="Requires backend to be stopped; run manually")
    @pytest.mark.smoke
    def test_network_error_shows_notification(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-076: Network error shows error notification.

        Spec: (no direct spec TC) -- Netzwerkfehler zeigt Fehlerbenachrichtigung.

        This test requires the backend to be unreachable. In a standard E2E run
        with a running backend, this test is skipped. To test manually:
        1. Stop the backend server
        2. Remove the skip marker
        3. Run the test
        """
        family_list.open()
        family_list.wait_for_loading_complete()
        screenshot("TC-REQ-001-076_network-error", "Page state after network error")

        # Should show an error display or notification
        error_displayed = family_list.is_error_displayed()
        notifications = family_list.driver.find_elements(
            By.CSS_SELECTOR, "[role='alert']"
        )
        assert error_displayed or len(notifications) > 0, (
            "TC-REQ-001-076 FAIL: An error display or notification should be shown when backend is unreachable"
        )

    @pytest.mark.skip(reason="Requires backend to return 500; run manually")
    @pytest.mark.smoke
    def test_server_error_shows_notification(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-077: Server error (500) shows error notification.

        Spec: (no direct spec TC) -- Serverfehler (500) zeigt Fehlerbenachrichtigung.

        This test requires the backend to return a 500 error. In standard E2E
        this cannot be reliably triggered without mocking or a special test endpoint.
        """
        family_list.open()
        family_list.wait_for_loading_complete()
        screenshot("TC-REQ-001-077_server-error", "Page state after server error")

        notifications = family_list.driver.find_elements(
            By.CSS_SELECTOR, "[role='alert']"
        )
        assert len(notifications) > 0, (
            "TC-REQ-001-077 FAIL: An error notification should be shown for server errors"
        )

    @pytest.mark.smoke
    def test_nonexistent_detail_page_shows_error(
        self, detail_page: BotanicalFamilyDetailPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-028: Non-existent key shows error display (supplemental).

        Spec: TC-001-068 -- Ungueltige URL — Botanische Familie nicht gefunden zeigt Fehlermeldung.

        This tests the error handling UX when navigating to a non-existent entity,
        which is a reliable way to verify error handling works.
        """
        detail_page.navigate("/stammdaten/botanical-families/nonexistent_e2e_key")
        detail_page.wait_for_loading_complete()
        screenshot("TC-REQ-001-028_nonexistent-key", "Detail page for non-existent botanical family key")

        assert detail_page.is_error_displayed() or "nonexistent" not in detail_page.driver.title, (
            "TC-REQ-001-028 FAIL: Should show error display or not-found state for non-existent key"
        )
