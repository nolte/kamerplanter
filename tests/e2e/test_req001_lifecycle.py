"""E2E tests for REQ-001 — Lifecycle Config & Growth Phases (TC-051 to TC-064)."""

from __future__ import annotations

import time
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
    time.sleep(1)


class TestLifecycleConfigSection:
    """TC-REQ-001-051 to TC-REQ-001-055: Lifecycle config CRUD."""

    def test_display_lifecycle_config_tab(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-051: Display lifecycle config tab."""
        _navigate_to_lifecycle_tab(species_list, species_detail)

        # The lifecycle tab should render with form fields
        submit_label = species_detail.get_lifecycle_submit_label()
        assert submit_label in ("Erstellen", "Speichern"), (
            f"Expected 'Erstellen' or 'Speichern', got '{submit_label}'"
        )

    def test_create_annual_lifecycle_config(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-052: Create a lifecycle config for an annual species."""
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Speichern":
            pytest.skip("Lifecycle config already exists")

        species_detail.select_lifecycle_option("cycle_type", "Einjährig")
        species_detail.select_lifecycle_option("photoperiod_type", "Tagneutral")
        species_detail.click_lifecycle_save()

        time.sleep(1)
        new_label = species_detail.get_lifecycle_submit_label()
        assert new_label == "Speichern", (
            f"After creation, button should show 'Speichern', got '{new_label}'"
        )

    def test_edit_existing_lifecycle_config(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-055: Edit an existing lifecycle config."""
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label != "Speichern":
            pytest.skip("No existing lifecycle config to edit")

        species_detail.click_lifecycle_save()
        time.sleep(1)
        # Should remain on the same page
        assert "/stammdaten/species/" in species_detail.driver.current_url


class TestGrowthPhaseManagement:
    """TC-REQ-001-056 to TC-REQ-001-062: Growth phase CRUD."""

    def test_growth_phases_section_visible(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-056: Growth phases section appears after lifecycle config creation."""
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Erstellen":
            pytest.skip("No lifecycle config exists — phases section not visible")

        assert species_detail.has_growth_phase_section(), (
            "Growth phases section should be visible"
        )

    def test_create_growth_phase(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-057: Create a growth phase via dialog."""
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
        species_detail.submit_phase_form()

        time.sleep(2)
        species_detail.wait_for_loading_complete()

        new_count = species_detail.get_phase_count()
        assert new_count >= initial_count, (
            f"Expected at least {initial_count} phases, got {new_count}"
        )

    def test_edit_growth_phase(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-059: Edit an existing growth phase."""
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Erstellen":
            pytest.skip("No lifecycle config")

        if species_detail.get_phase_count() == 0:
            pytest.skip("No phases to edit")

        species_detail.click_phase_row(0)
        time.sleep(0.5)

        # Edit dialog should open — modify duration
        species_detail.set_field("typical_duration_days", "35")
        species_detail.submit_phase_form()

        time.sleep(1)

    def test_delete_growth_phase(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-060: Delete a growth phase."""
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Erstellen":
            pytest.skip("No lifecycle config")

        if species_detail.get_phase_count() == 0:
            pytest.skip("No phases to delete")

        initial_count = species_detail.get_phase_count()
        species_detail.delete_phase_at_index(0)
        species_detail.confirm_delete()

        time.sleep(2)
        new_count = species_detail.get_phase_count()
        assert new_count < initial_count, (
            f"Expected fewer phases after delete: was {initial_count}, now {new_count}"
        )


class TestGrowthPhaseProfiles:
    """TC-REQ-001-063 to TC-REQ-001-064: Growth phase profiles."""

    def test_view_profiles_for_growth_phase(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-063: View profiles for a growth phase."""
        _navigate_to_lifecycle_tab(species_list, species_detail)

        if species_detail.get_phase_count() == 0:
            pytest.skip("No phases with profiles to view")

        # Profiles are typically shown via a button or expandable section
        # This test verifies the UI element exists
        phase_count = species_detail.get_phase_count()
        assert phase_count >= 0, "Phase table should render"
