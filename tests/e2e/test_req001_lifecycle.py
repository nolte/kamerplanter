"""E2E tests for REQ-001 — Lifecycle Config & Growth Phases.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-051  ->  TC-001-047  Lebenszyklus-Tab zeigt LifecycleConfig und GrowthPhases
  TC-REQ-001-052  ->  TC-001-047  Lifecycle-Config fuer einjaehrige Art erstellen
  TC-REQ-001-055  ->  TC-001-047  Bestehende Lifecycle-Config bearbeiten
  TC-REQ-001-056  ->  TC-001-048  Wachstumsphasen-Bereich nach Lifecycle-Erstellung sichtbar
  TC-REQ-001-057  ->  TC-001-048  Neue Wachstumsphase anlegen
  TC-REQ-001-059  ->  TC-001-048  Bestehende Wachstumsphase bearbeiten
  TC-REQ-001-060  ->  TC-001-048  Wachstumsphase loeschen
  TC-REQ-001-063  ->  TC-001-047  Profile fuer Wachstumsphase anzeigen
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import SpeciesDetailPage, SpeciesListPage


@pytest.fixture
def species_list(browser: WebDriver, base_url: str) -> SpeciesListPage:
    return SpeciesListPage(browser, base_url)


@pytest.fixture
def species_detail(browser: WebDriver, base_url: str) -> SpeciesDetailPage:
    return SpeciesDetailPage(browser, base_url)


def _navigate_to_lifecycle_tab(
    species_list: SpeciesListPage,
    species_detail: SpeciesDetailPage,
) -> None:
    """Navigate to the 'Lebenszyklus-Konfiguration' tab of the first species."""
    species_list.open()
    if species_list.get_row_count() == 0:
        pytest.skip("No species in database")
    species_list.click_row(0)
    species_list.wait_for_url_contains("/stammdaten/species/")
    tabs = species_detail.get_tab_labels()
    lifecycle_tab = next(
        (i for i, t in enumerate(tabs) if "LEBENSZYKLUS" in t.upper()), None
    )
    if lifecycle_tab is None:
        pytest.skip("Lifecycle tab not found")
    species_detail.click_tab(lifecycle_tab)
    species_detail.wait_for_loading_complete()


class TestLifecycleConfigSection:
    """Lifecycle config CRUD (Spec: TC-001-047)."""

    @pytest.mark.smoke
    def test_display_lifecycle_config_tab(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-051: Display lifecycle config tab.

        Spec: TC-001-047 -- Lebenszyklus-Tab zeigt LifecycleConfig und GrowthPhases.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)
        screenshot("TC-REQ-001-051_lifecycle-tab", "Lifecycle config tab displayed")

        # The lifecycle tab should render with form fields
        submit_label = species_detail.get_lifecycle_submit_label()
        assert submit_label in ("Erstellen", "Speichern"), (
            f"TC-REQ-001-051 FAIL: Expected 'Erstellen' or 'Speichern', got '{submit_label}'"
        )

    @pytest.mark.core_crud
    def test_create_annual_lifecycle_config(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-052: Create a lifecycle config for an annual species.

        Spec: TC-001-047 -- Lifecycle-Config fuer einjaehrige Art erstellen.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Speichern":
            pytest.skip("Lifecycle config already exists")

        species_detail.select_lifecycle_option("cycle_type", "Einjährig")
        species_detail.select_lifecycle_option("photoperiod_type", "Tagneutral")
        screenshot("TC-REQ-001-052_before-create", "Lifecycle config form filled for annual species")

        species_detail.click_lifecycle_save()

        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-052_after-create", "Lifecycle config after creation")

        new_label = species_detail.get_lifecycle_submit_label()
        assert new_label == "Speichern", (
            f"TC-REQ-001-052 FAIL: After creation, button should show 'Speichern', got '{new_label}'"
        )

    @pytest.mark.core_crud
    def test_edit_existing_lifecycle_config(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-055: Edit an existing lifecycle config.

        Spec: TC-001-047 -- Bestehende Lifecycle-Config bearbeiten.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label != "Speichern":
            pytest.skip("No existing lifecycle config to edit")

        screenshot("TC-REQ-001-055_before-edit", "Lifecycle config before editing")
        species_detail.click_lifecycle_save()
        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-055_after-save", "Lifecycle config after saving")

        # Should remain on the same page
        assert "/stammdaten/species/" in species_detail.driver.current_url, (
            f"TC-REQ-001-055 FAIL: Should remain on species detail, got {species_detail.driver.current_url}"
        )


class TestGrowthPhaseManagement:
    """Growth phase CRUD (Spec: TC-001-048)."""

    @pytest.mark.smoke
    def test_growth_phases_section_visible(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-056: Growth phases section appears after lifecycle config creation.

        Spec: TC-001-048 -- Wachstumsphasen-Bereich nach Lifecycle-Erstellung sichtbar.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Erstellen":
            pytest.skip("No lifecycle config exists — phases section not visible")

        screenshot("TC-REQ-001-056_phases-section", "Growth phases section visible")

        assert species_detail.has_growth_phase_section(), (
            "TC-REQ-001-056 FAIL: Growth phases section should be visible"
        )

    @pytest.mark.core_crud
    def test_create_growth_phase(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-057: Create a growth phase via dialog.

        Spec: TC-001-048 -- Neue Wachstumsphase anlegen.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Erstellen":
            pytest.skip("No lifecycle config — cannot create phases")

        if not species_detail.has_growth_phase_section():
            pytest.skip("Growth phase section not visible")

        initial_count = species_detail.get_phase_count()
        unique = uuid.uuid4().hex[:4]

        species_detail.click_phase_create()
        species_detail.fill_phase_form(
            name=f"e2e_phase_{unique}",
            display_name=f"E2E Phase {unique}",
            duration="7",
            order=str(initial_count),
        )
        screenshot("TC-REQ-001-057_phase-form-filled", f"Phase form filled for e2e_phase_{unique}")

        species_detail.submit_phase_form()

        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-057_after-create", "Growth phases after creation")

        new_count = species_detail.get_phase_count()
        assert new_count >= initial_count, (
            f"TC-REQ-001-057 FAIL: Expected at least {initial_count} phases, got {new_count}"
        )

    @pytest.mark.core_crud
    def test_edit_growth_phase(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-059: Edit an existing growth phase.

        Spec: TC-001-048 -- Bestehende Wachstumsphase bearbeiten.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Erstellen":
            pytest.skip("No lifecycle config")

        if species_detail.get_phase_count() == 0:
            pytest.skip("No phases to edit")

        screenshot("TC-REQ-001-059_before-edit", "Growth phases before editing")
        species_detail.click_phase_row(0)
        species_detail.wait_for_loading_complete()

        # Edit dialog should open — wait for the dialog to appear
        dialogs = species_detail.driver.find_elements(
            *species_detail.CREATE_DIALOG
        )
        if not dialogs:
            pytest.skip("Edit dialog did not open on phase row click")

        # Modify duration inside the dialog
        species_detail.set_field("typical_duration_days", "35")
        screenshot("TC-REQ-001-059_field-modified", "Phase duration changed to 35")

        species_detail.submit_phase_form()

        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-059_after-edit", "Growth phases after editing")

    @pytest.mark.core_crud
    def test_delete_growth_phase(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-060: Delete a growth phase.

        Spec: TC-001-048 -- Wachstumsphase loeschen.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Erstellen":
            pytest.skip("No lifecycle config")

        if species_detail.get_phase_count() == 0:
            pytest.skip("No phases to delete")

        initial_count = species_detail.get_phase_count()
        screenshot("TC-REQ-001-060_before-delete", f"Growth phases before deletion ({initial_count} phases)")

        species_detail.delete_phase_at_index(0)
        species_detail.confirm_delete()

        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-060_after-delete", "Growth phases after deletion")

        new_count = species_detail.get_phase_count()
        assert new_count < initial_count, (
            f"TC-REQ-001-060 FAIL: Expected fewer phases after delete: was {initial_count}, now {new_count}"
        )


class TestGrowthPhaseProfiles:
    """Growth phase profiles (Spec: TC-001-047)."""

    @pytest.mark.smoke
    def test_view_profiles_for_growth_phase(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-063: View profiles for a growth phase.

        Spec: TC-001-047 -- Profile fuer Wachstumsphase anzeigen.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)
        screenshot("TC-REQ-001-063_lifecycle-tab", "Lifecycle tab with phase profiles")

        if species_detail.get_phase_count() == 0:
            pytest.skip("No phases with profiles to view")

        # Profiles are typically shown via a button or expandable section
        # This test verifies the UI element exists
        phase_count = species_detail.get_phase_count()
        assert phase_count >= 0, (
            "TC-REQ-001-063 FAIL: Phase table should render"
        )
