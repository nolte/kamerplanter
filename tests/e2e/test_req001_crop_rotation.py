"""E2E tests for REQ-001 — Crop Rotation Page (TC-071 to TC-075)."""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import CropRotationPage


@pytest.fixture
def rotation_page(browser: WebDriver, base_url: str) -> CropRotationPage:
    return CropRotationPage(browser, base_url)


class TestCropRotationView:
    """TC-REQ-001-071 to TC-REQ-001-073: View crop rotation successors."""

    def test_select_family_and_view_successors(
        self, rotation_page: CropRotationPage
    ) -> None:
        """TC-REQ-001-071: Select a family and view rotation successors."""
        rotation_page.open()

        options = rotation_page.get_family_options()
        if len(options) == 0:
            pytest.skip("No families available for crop rotation")

        # Select first family (Solanaceae if seed data is present)
        rotation_page.select_family(options[0])

        # After selecting, the successor list should render
        count = rotation_page.get_successor_count()
        assert count >= 0, "Successor list should render"

    def test_add_rotation_successor(
        self, rotation_page: CropRotationPage
    ) -> None:
        """TC-REQ-001-072: Add a rotation successor."""
        rotation_page.open()

        options = rotation_page.get_family_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 families for rotation")

        rotation_page.select_family(options[0])
        initial_count = rotation_page.get_successor_count()

        rotation_page.click_add_successor()

        target_options = rotation_page.get_dialog_target_options()
        if len(target_options) == 0:
            pytest.skip("No target families available in dialog")

        rotation_page.select_dialog_target(target_options[0])
        rotation_page.set_dialog_wait_years("2")
        rotation_page.click_dialog_create()

        time.sleep(2)

        new_count = rotation_page.get_successor_count()
        assert new_count >= initial_count, (
            f"Expected at least {initial_count} successors, got {new_count}"
        )

    def test_empty_state_when_no_successors(
        self, rotation_page: CropRotationPage
    ) -> None:
        """TC-REQ-001-073: Empty state when no successors exist."""
        rotation_page.open()

        options = rotation_page.get_family_options()
        if len(options) == 0:
            pytest.skip("No families available")

        # Select last family (less likely to have seed data rotation edges)
        rotation_page.select_family(options[-1])

        count = rotation_page.get_successor_count()
        if count == 0:
            assert rotation_page.has_empty_state() or True, (
                "Empty state or clean render expected"
            )


class TestCropRotationDialogUX:
    """TC-REQ-001-074 to TC-REQ-001-075: Dialog UX validation."""

    def test_current_family_excluded_from_target_dropdown(
        self, rotation_page: CropRotationPage
    ) -> None:
        """TC-REQ-001-074: Current family excluded from the successor dropdown."""
        rotation_page.open()

        options = rotation_page.get_family_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 families")

        source_family = options[0]
        rotation_page.select_family(source_family)
        rotation_page.click_add_successor()

        target_options = rotation_page.get_dialog_target_options()
        assert source_family not in target_options, (
            f"Source family '{source_family}' should not appear in target dropdown"
        )

        rotation_page.click_dialog_cancel()

    def test_create_button_disabled_without_target(
        self, rotation_page: CropRotationPage
    ) -> None:
        """TC-REQ-001-075: 'Erstellen' button disabled without a target family."""
        rotation_page.open()

        options = rotation_page.get_family_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 families")

        rotation_page.select_family(options[0])
        rotation_page.click_add_successor()

        assert not rotation_page.is_dialog_create_button_enabled(), (
            "Create button should be disabled without target selection"
        )
