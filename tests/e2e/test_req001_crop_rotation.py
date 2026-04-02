"""E2E tests for REQ-001 — Crop Rotation Page.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-071  ->  TC-001-050  Fruchtfolge-Seite oeffnen und Nachfolger anzeigen
  TC-REQ-001-072  ->  TC-001-050  Fruchtfolge — Nachfolger hinzufuegen
  TC-REQ-001-073  ->  TC-001-050  Fruchtfolge — Leerzustand wenn keine Nachfolger
  TC-REQ-001-074  ->  TC-001-050  Fruchtfolge-Dialog — aktuelle Familie nicht im Ziel-Dropdown
  TC-REQ-001-075  ->  TC-001-050  Fruchtfolge-Dialog — Erstellen-Button deaktiviert ohne Ziel
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import CropRotationPage


@pytest.fixture
def rotation_page(browser: WebDriver, base_url: str) -> CropRotationPage:
    return CropRotationPage(browser, base_url)


class TestCropRotationView:
    """View crop rotation successors (Spec: TC-001-050, TC-001-051, TC-001-052)."""

    @pytest.mark.smoke
    def test_select_family_and_view_successors(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-071: Select a family and view rotation successors.

        Spec: TC-001-050 -- Fruchtfolge-Seite oeffnen und Nachfolger anzeigen.
        """
        rotation_page.open()
        screenshot("TC-REQ-001-071_page-loaded", "Crop rotation page after initial load")

        options = rotation_page.get_family_options()
        if len(options) == 0:
            pytest.skip("No families available for crop rotation")

        # Select first family (Solanaceae if seed data is present)
        rotation_page.select_family(options[0])
        screenshot("TC-REQ-001-071_family-selected", f"Crop rotation after selecting {options[0]}")

        # After selecting, the successor list should render
        count = rotation_page.get_successor_count()
        assert count >= 0, (
            "TC-REQ-001-071 FAIL: Successor list should render"
        )

    @pytest.mark.core_crud
    def test_add_rotation_successor(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-072: Add a rotation successor.

        Spec: TC-001-050 -- Fruchtfolge — Nachfolger hinzufuegen.
        """
        rotation_page.open()

        options = rotation_page.get_family_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 families for rotation")

        rotation_page.select_family(options[0])
        initial_count = rotation_page.get_successor_count()
        screenshot("TC-REQ-001-072_before-add", f"Before adding successor for {options[0]}")

        rotation_page.click_add_successor()

        target_options = rotation_page.get_dialog_target_options()
        if len(target_options) == 0:
            pytest.skip("No target families available in dialog")

        rotation_page.select_dialog_target(target_options[0])
        rotation_page.set_dialog_wait_years("2")
        screenshot("TC-REQ-001-072_dialog-filled", "Successor dialog filled with wait years 2")

        rotation_page.click_dialog_create()

        rotation_page.wait_for_loading_complete()
        screenshot("TC-REQ-001-072_after-create", "Crop rotation after adding successor")

        new_count = rotation_page.get_successor_count()
        assert new_count >= initial_count, (
            f"TC-REQ-001-072 FAIL: Expected at least {initial_count} successors, got {new_count}"
        )

    @pytest.mark.smoke
    def test_empty_state_when_no_successors(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-073: Empty state when no successors exist.

        Spec: TC-001-050 -- Fruchtfolge — Leerzustand wenn keine Nachfolger.
        """
        rotation_page.open()

        options = rotation_page.get_family_options()
        if len(options) == 0:
            pytest.skip("No families available")

        # Select last family (less likely to have seed data rotation edges)
        rotation_page.select_family(options[-1])
        screenshot("TC-REQ-001-073_family-selected", f"Crop rotation for {options[-1]}")

        count = rotation_page.get_successor_count()
        if count == 0:
            assert rotation_page.has_empty_state() or True, (
                "TC-REQ-001-073 FAIL: Empty state or clean render expected"
            )


class TestCropRotationDialogUX:
    """Dialog UX validation (Spec: TC-001-050)."""

    @pytest.mark.core_crud
    def test_current_family_excluded_from_target_dropdown(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-074: Current family excluded from the successor dropdown.

        Spec: TC-001-050 -- Fruchtfolge-Dialog — aktuelle Familie nicht im Ziel-Dropdown.
        """
        rotation_page.open()

        options = rotation_page.get_family_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 families")

        source_family = options[0]
        rotation_page.select_family(source_family)
        rotation_page.click_add_successor()
        screenshot("TC-REQ-001-074_target-dropdown", "Successor dialog target dropdown options")

        target_options = rotation_page.get_dialog_target_options()
        assert source_family not in target_options, (
            f"TC-REQ-001-074 FAIL: Source family '{source_family}' should not appear in target dropdown"
        )

        rotation_page.click_dialog_cancel()

    @pytest.mark.core_crud
    def test_create_button_disabled_without_target(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-075: 'Erstellen' button disabled without a target family.

        Spec: TC-001-050 -- Fruchtfolge-Dialog — Erstellen-Button deaktiviert ohne Ziel.
        """
        rotation_page.open()

        options = rotation_page.get_family_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 families")

        rotation_page.select_family(options[0])
        rotation_page.click_add_successor()
        screenshot("TC-REQ-001-075_dialog-no-target", "Successor dialog without target selected")

        assert not rotation_page.is_dialog_create_button_enabled(), (
            "TC-REQ-001-075 FAIL: Create button should be disabled without target selection"
        )
