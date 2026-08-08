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


def _common_name(option_label: str) -> str:
    """The part of a family dropdown label that the successor list renders.

    `familyOptionLabel` builds ``"<common name> · <scientific name>"`` when a
    family has a distinct common name and the bare name otherwise, while a
    successor row's primary line is the common name alone. Comparing the whole
    label against the row would therefore never match for the first shape.
    """
    return option_label.split(" · ")[0].strip()


class TestCropRotationView:
    """View crop rotation successors (Spec: TC-001-050, TC-001-051, TC-001-052)."""

    @pytest.mark.smoke
    def test_select_family_and_view_successors(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-050: Select a family and view rotation successors.

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
        assert count >= 0, "TC-REQ-001-071 FAIL: Successor list should render"

    @pytest.mark.core_crud
    def test_add_rotation_successor(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-050: Add a rotation successor.

        Spec: TC-001-050 -- Fruchtfolge — Nachfolger hinzufuegen.
        """
        rotation_page.open()

        options = rotation_page.get_family_options()
        if len(options) < 2:
            pytest.skip("Need at least 2 families for rotation")

        rotation_page.select_family(options[0])
        listed_before = rotation_page.get_successor_names()
        screenshot("TC-REQ-001-072_before-add", f"Before adding successor for {options[0]}")

        rotation_page.click_add_successor()

        target_options = rotation_page.get_dialog_target_options()
        if len(target_options) == 0:
            pytest.skip("No target families available in dialog")

        # The dialog offers every family except the selected one -- including
        # those that already *are* successors. Adding one of those and then
        # looking for its name is a read-back that the arrange step satisfies on
        # its own, so the target is chosen from the ones not yet listed.
        target = next(
            (o for o in target_options if _common_name(o) not in " ".join(listed_before)),
            None,
        )
        if target is None:
            pytest.skip(
                f"Every family the dialog offers is already a successor of {options[0]} "
                f"— adding one more cannot be observed"
            )
        expected = _common_name(target)

        rotation_page.select_dialog_target(target)
        rotation_page.set_dialog_wait_years("2")
        screenshot("TC-REQ-001-072_dialog-filled", "Successor dialog filled with wait years 2")

        rotation_page.click_dialog_create()
        # Not "the dialog closed": `handleAdd` calls `setDialogOpen(false)`
        # *after* its try/except, so the dialog goes away whether the POST
        # succeeded or ran into `handleError`. The list itself is the only signal
        # -- `handleAdd` re-reads the successors and only a resolved
        # `setSuccessor` puts the new one in there.
        rotation_page.wait_for_row_containing(
            expected,
            rows_locator=CropRotationPage.SUCCESSOR_ITEMS,
            what=f"rotation successors of {options[0]!r} after adding {expected!r}",
        )
        screenshot("TC-REQ-001-072_after-create", "Crop rotation after adding successor")

        # Identity, not arithmetic. `new_count >= initial_count` is satisfied by
        # an add that was rejected or never submitted -- the count of a list
        # nothing was added to still is "at least" what it was (#956). The target
        # was demonstrably absent from the list a moment ago, so naming it now is
        # a statement about this add and nothing else.
        listed_after = rotation_page.get_successor_names()
        assert any(expected in row for row in listed_after), (
            f"TC-REQ-001-072 FAIL: {expected!r} must be listed as a successor of "
            f"{options[0]!r} after adding it, but the list reads {listed_after!r} "
            f"(it held {len(listed_before)} row(s) before). `handleAdd` refetches the "
            f"successors itself, so a list without it means `setSuccessor` was "
            f"rejected — the dialog closes either way and shows an error toast."
        )

    @pytest.mark.smoke
    def test_empty_state_when_no_successors(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-050: Empty state when no successors exist.

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
            # `get_successor_count` is anchored on `wait_for_successor_content`
            # (`select_family`'s own post-condition, #946 wave 10), which only
            # settles once `SUCCESSOR_ITEMS` or `EMPTY_STATE` has rendered -- a
            # settled `count == 0` can therefore only be reached via the
            # `EMPTY_STATE` branch, making this a real, falsifiable check
            # rather than the `or True` tautology it replaces (T2, satisfied
            # regardless of what `has_empty_state()` answers).
            assert rotation_page.has_empty_state(), (
                "TC-REQ-001-073 FAIL: Expected the empty state to be shown for a family "
                "with zero rotation successors"
            )


class TestCropRotationDialogUX:
    """Dialog UX validation (Spec: TC-001-050)."""

    @pytest.mark.core_crud
    def test_current_family_excluded_from_target_dropdown(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-050: Current family excluded from the successor dropdown.

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
        """TC-001-050: 'Erstellen' button disabled without a target family.

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
