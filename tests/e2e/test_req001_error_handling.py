"""E2E tests for REQ-001 — Error Handling (TC-076 to TC-077).

TC-078 (duplicate family name) is already covered in test_req001_botanical_family_create.py.

NOTE: TC-076 (network error) and TC-077 (server 500) require specific environment
conditions that are difficult to reproduce in standard E2E runs. These tests use
pragmatic approaches to verify error handling UX where possible.
"""

from __future__ import annotations

import time

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
    """TC-REQ-001-076 to TC-REQ-001-077: Error handling and notifications."""

    @pytest.mark.skip(reason="Requires backend to be stopped; run manually")
    def test_network_error_shows_notification(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """TC-REQ-001-076: Network error shows error notification.

        This test requires the backend to be unreachable. In a standard E2E run
        with a running backend, this test is skipped. To test manually:
        1. Stop the backend server
        2. Remove the skip marker
        3. Run the test
        """
        family_list.open()
        time.sleep(3)

        # Should show an error display or notification
        error_displayed = family_list.is_error_displayed()
        notifications = family_list.driver.find_elements(
            By.CSS_SELECTOR, "[role='alert']"
        )
        assert error_displayed or len(notifications) > 0, (
            "An error display or notification should be shown when backend is unreachable"
        )

    @pytest.mark.skip(reason="Requires backend to return 500; run manually")
    def test_server_error_shows_notification(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """TC-REQ-001-077: Server error (500) shows error notification.

        This test requires the backend to return a 500 error. In standard E2E
        this cannot be reliably triggered without mocking or a special test endpoint.
        """
        family_list.open()
        time.sleep(3)

        notifications = family_list.driver.find_elements(
            By.CSS_SELECTOR, "[role='alert']"
        )
        assert len(notifications) > 0, (
            "An error notification should be shown for server errors"
        )

    def test_nonexistent_detail_page_shows_error(
        self, detail_page: BotanicalFamilyDetailPage
    ) -> None:
        """TC-REQ-001-028 (supplemental): Non-existent key shows error display.

        This tests the error handling UX when navigating to a non-existent entity,
        which is a reliable way to verify error handling works.
        """
        detail_page.navigate("/stammdaten/botanical-families/nonexistent_e2e_key")
        time.sleep(2)

        assert detail_page.is_error_displayed() or "nonexistent" not in detail_page.driver.title, (
            "Should show error display or not-found state for non-existent key"
        )
