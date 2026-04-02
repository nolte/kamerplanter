"""E2E tests for REQ-021 — UI-Erfahrungsstufen (Experience Levels).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-021.md):
  TC-REQ-021-001  ->  TC-021-004  Nutzer oeffnet Tab 'Erfahrungsstufe' in Kontoeinstellungen
  TC-REQ-021-002  ->  TC-021-005  Upgrade von Anfaenger auf Fortgeschritten -- keine Warnung
  TC-REQ-021-003  ->  TC-021-006  Upgrade von Anfaenger auf Experte -- keine Warnung
  TC-REQ-021-004  ->  TC-021-007  Downgrade von Experte auf Anfaenger -- Bestaetigungs-Dialog
  TC-REQ-021-005  ->  TC-021-009  Downgrade-Dialog -- Nutzer bricht ab, Stufe bleibt
  TC-REQ-021-006  ->  TC-021-010  Downgrade von Fortgeschritten auf Anfaenger -- Warnung
  TC-REQ-021-007  ->  TC-021-011  Nach erneutem Login ist zuletzt gewaehlte Stufe aktiv
  TC-REQ-021-008  ->  TC-021-013  Anfaenger-Navigation zeigt genau die Kernmenuepunkte
  TC-REQ-021-009  ->  TC-021-014  Fortgeschritten-Navigation enthaelt zusaetzliche Abschnitte
  TC-REQ-021-010  ->  TC-021-015  Experten-Navigation zeigt alle Menuepunkte
  TC-REQ-021-011  ->  TC-021-016  Direktaufruf einer Expert-only-URL als Anfaenger
  TC-REQ-021-012  ->  TC-021-017  SpeciesCreateDialog im Anfaenger-Modus
  TC-REQ-021-013  ->  TC-021-018  SpeciesCreateDialog im Fortgeschritten-Modus
  TC-REQ-021-014  ->  TC-021-019  SpeciesCreateDialog im Experten-Modus
  TC-REQ-021-015  ->  TC-021-020  'Alle Felder anzeigen' im Anfaenger-Modus aktivieren
  TC-REQ-021-016  ->  TC-021-021  'Weniger Felder anzeigen' -- erweiterte Felder verschwinden
  TC-REQ-021-017  ->  TC-021-022  Toggle-Zustand wird nach Schliessen des Dialogs zurueckgesetzt
  TC-REQ-021-018  ->  TC-021-023  PlantingRunCreateDialog im Anfaenger-Modus
  TC-REQ-021-019  ->  TC-021-024  PlantingRunCreateDialog im Fortgeschritten-Modus
  TC-REQ-021-020  ->  TC-021-025  PlantingRunCreateDialog im Experten-Modus
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.expertise_level_page import ExpertiseLevelPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def expertise_page(browser: WebDriver, base_url: str) -> ExpertiseLevelPage:
    """Return an ExpertiseLevelPage bound to the test browser."""
    return ExpertiseLevelPage(browser, base_url)


# -- Helpers -------------------------------------------------------------------


def _set_experience_level(
    expertise_page: ExpertiseLevelPage,
    target_level: str,
) -> None:
    """Navigate to the experience tab and set the level, handling confirm dialogs."""
    expertise_page.open_experience_tab()
    current = expertise_page.get_active_toggle_level()
    if current == target_level:
        return

    LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "expert": 2}
    is_downgrade = LEVEL_ORDER.get(target_level, 0) < LEVEL_ORDER.get(current, 0)

    expertise_page.click_level(target_level)

    if is_downgrade:
        expertise_page.accept_confirm_dialog()

    expertise_page.wait_for_saved_snackbar()


# -- TC-021-004 to TC-021-009: Experience Level Switcher -----------------------


class TestExperienceLevelSwitcher:
    """Experience level switching in AccountSettings (Spec: TC-021-004 to TC-021-010)."""

    @pytest.mark.smoke
    def test_experience_tab_renders_toggle_group(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-001: Experience tab shows ToggleButtonGroup with 3 levels.

        Spec: TC-021-004 -- Nutzer oeffnet Tab 'Erfahrungsstufe' in den Kontoeinstellungen.
        """
        expertise_page.open_experience_tab()
        screenshot(
            "TC-REQ-021-001_experience-tab-loaded",
            "AccountSettings experience tab with toggle group",
        )

        assert expertise_page.is_toggle_visible(), (
            "TC-REQ-021-001 FAIL: Expected ToggleButtonGroup to be visible"
        )
        active = expertise_page.get_active_toggle_level()
        assert active in ("beginner", "intermediate", "expert"), (
            f"TC-REQ-021-001 FAIL: Expected one toggle to be selected, got: {active}"
        )

    @pytest.mark.core_crud
    def test_upgrade_beginner_to_intermediate_no_warning(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-002: Upgrade from beginner to intermediate -- no confirm, immediate change.

        Spec: TC-021-005 -- Upgrade von Anfaenger auf Fortgeschritten -- keine Warnung, sofortige Aenderung.
        """
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_experience_tab()
        screenshot(
            "TC-REQ-021-002_before-upgrade-to-intermediate",
            "Experience tab showing beginner before upgrade",
        )

        expertise_page.click_level("intermediate")

        assert not expertise_page.is_confirm_dialog_present(), (
            "TC-REQ-021-002 FAIL: No confirm dialog expected on upgrade"
        )

        expertise_page.wait_for_saved_snackbar()
        screenshot(
            "TC-REQ-021-002_after-upgrade-to-intermediate",
            "Experience tab after upgrade to intermediate",
        )

        assert expertise_page.get_active_toggle_level() == "intermediate", (
            "TC-REQ-021-002 FAIL: Expected 'intermediate' to be the active toggle after upgrade"
        )

    @pytest.mark.core_crud
    def test_upgrade_beginner_to_expert_no_warning(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-003: Upgrade from beginner to expert -- no confirm, all nav items appear.

        Spec: TC-021-006 -- Upgrade von Anfaenger auf Experte -- keine Warnung, erweiterte Navigation.
        """
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_experience_tab()
        expertise_page.click_level("expert")

        assert not expertise_page.is_confirm_dialog_present(), (
            "TC-REQ-021-003 FAIL: No confirm dialog expected on upgrade"
        )

        expertise_page.wait_for_saved_snackbar()
        screenshot(
            "TC-REQ-021-003_after-upgrade-to-expert",
            "Experience tab and sidebar after upgrade to expert",
        )

        assert expertise_page.get_active_toggle_level() == "expert", (
            "TC-REQ-021-003 FAIL: Expected 'expert' to be the active toggle after upgrade"
        )

    @pytest.mark.core_crud
    def test_downgrade_expert_to_beginner_shows_confirm(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-004: Downgrade expert->beginner shows confirm; accept changes level.

        Spec: TC-021-007 / TC-021-008 -- Downgrade von Experte auf Anfaenger -- Bestaetigungs-Dialog.
        """
        _set_experience_level(expertise_page, "expert")

        expertise_page.open_experience_tab()
        screenshot(
            "TC-REQ-021-004_before-downgrade",
            "Expert level before downgrade",
        )

        expertise_page.click_level("beginner")

        assert expertise_page.is_confirm_dialog_present(), (
            "TC-REQ-021-004 FAIL: Expected confirm dialog when downgrading expert to beginner"
        )

        expertise_page.accept_confirm_dialog()
        expertise_page.wait_for_saved_snackbar()
        screenshot(
            "TC-REQ-021-004_after-downgrade",
            "Beginner level after confirmed downgrade",
        )

        assert expertise_page.get_active_toggle_level() == "beginner", (
            "TC-REQ-021-004 FAIL: Expected 'beginner' after confirmed downgrade"
        )

    @pytest.mark.core_crud
    def test_downgrade_cancel_keeps_current_level(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-005: Dismiss downgrade dialog -- level stays unchanged.

        Spec: TC-021-009 -- Downgrade-Dialog -- Nutzer bricht ab, Stufe bleibt unveraendert.
        """
        _set_experience_level(expertise_page, "expert")

        expertise_page.open_experience_tab()
        expertise_page.click_level("beginner")

        assert expertise_page.is_confirm_dialog_present(), (
            "TC-REQ-021-005 FAIL: Expected confirm dialog when downgrading"
        )

        expertise_page.dismiss_confirm_dialog()
        screenshot(
            "TC-REQ-021-005_downgrade-cancelled",
            "Expert level preserved after dismissing downgrade",
        )

        assert expertise_page.get_active_toggle_level() == "expert", (
            "TC-REQ-021-005 FAIL: Expected 'expert' to remain active after cancelling downgrade"
        )

    @pytest.mark.core_crud
    def test_downgrade_intermediate_to_beginner_shows_confirm(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-006: Downgrade intermediate->beginner also shows confirm dialog.

        Spec: TC-021-010 -- Downgrade von Fortgeschritten auf Anfaenger -- Warnung erscheint.
        """
        _set_experience_level(expertise_page, "intermediate")

        expertise_page.open_experience_tab()
        expertise_page.click_level("beginner")

        assert expertise_page.is_confirm_dialog_present(), (
            "TC-REQ-021-006 FAIL: Expected confirm dialog when downgrading intermediate to beginner"
        )

        expertise_page.accept_confirm_dialog()
        expertise_page.wait_for_saved_snackbar()
        screenshot(
            "TC-REQ-021-006_downgrade-intermediate-to-beginner",
            "Beginner level after downgrade from intermediate",
        )

        assert expertise_page.get_active_toggle_level() == "beginner", (
            "TC-REQ-021-006 FAIL: Expected 'beginner' after confirmed downgrade from intermediate"
        )


# -- TC-021-011 to TC-021-012: Persistence ------------------------------------


class TestExperienceLevelPersistence:
    """Level persisted across page reload (Spec: TC-021-011)."""

    @pytest.mark.core_crud
    def test_level_persists_after_page_reload(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-007: After page reload, the previously set experience level is restored.

        Spec: TC-021-011 -- Nach erneutem Login ist zuletzt gewaehlte Erfahrungsstufe aktiv.
        """
        _set_experience_level(expertise_page, "intermediate")

        # Reload the page to simulate a new session
        expertise_page.navigate("/dashboard")
        expertise_page.wait_for_element(expertise_page.SIDEBAR)

        screenshot(
            "TC-REQ-021-007_after-reload-intermediate",
            "Dashboard after reload, intermediate nav expected",
        )

        assert expertise_page.is_nav_item_visible("/standorte/sites"), (
            "TC-REQ-021-007 FAIL: Expected '/standorte/sites' visible after reload with intermediate"
        )
        assert not expertise_page.is_nav_item_visible("/pflanzenschutz/pests"), (
            "TC-REQ-021-007 FAIL: Expected '/pflanzenschutz/pests' hidden for intermediate"
        )

        expertise_page.open_experience_tab()
        screenshot(
            "TC-REQ-021-007_experience-tab-after-reload",
            "Experience tab showing intermediate after page reload",
        )
        assert expertise_page.get_active_toggle_level() == "intermediate", (
            "TC-REQ-021-007 FAIL: Expected 'intermediate' to be active after page reload"
        )


# -- TC-021-013 to TC-021-016: Navigation Tiering -----------------------------


class TestNavigationTiering:
    """Sidebar nav items per experience level (Spec: TC-021-013 to TC-021-016)."""

    @pytest.mark.core_crud
    def test_beginner_navigation_minimal(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-008: Beginner sees only core nav items (dashboard, plants, tasks).

        Spec: TC-021-013 -- Anfaenger-Navigation zeigt genau die Kernmenuepunkte.
        """
        _set_experience_level(expertise_page, "beginner")

        expertise_page.navigate("/dashboard")
        expertise_page.wait_for_element(expertise_page.SIDEBAR)
        screenshot(
            "TC-REQ-021-008_beginner-sidebar",
            "Sidebar in beginner mode with minimal nav items",
        )

        # Beginner items should be visible
        assert expertise_page.is_nav_item_visible("/dashboard"), (
            "TC-REQ-021-008 FAIL: Expected '/dashboard' visible for beginner"
        )
        assert expertise_page.is_nav_item_visible("/pflanzen/plant-instances"), (
            "TC-REQ-021-008 FAIL: Expected '/pflanzen/plant-instances' visible for beginner"
        )
        assert expertise_page.is_nav_item_visible("/aufgaben/queue"), (
            "TC-REQ-021-008 FAIL: Expected '/aufgaben/queue' visible for beginner"
        )

        # Intermediate/expert items should be hidden
        assert not expertise_page.is_nav_item_visible("/standorte/sites"), (
            "TC-REQ-021-008 FAIL: Expected '/standorte/sites' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/kalender"), (
            "TC-REQ-021-008 FAIL: Expected '/kalender' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/stammdaten/species"), (
            "TC-REQ-021-008 FAIL: Expected '/stammdaten/species' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/duengung/fertilizers"), (
            "TC-REQ-021-008 FAIL: Expected '/duengung/fertilizers' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/pflanzenschutz/pests"), (
            "TC-REQ-021-008 FAIL: Expected '/pflanzenschutz/pests' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/ernte/batches"), (
            "TC-REQ-021-008 FAIL: Expected '/ernte/batches' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/durchlaeufe/planting-runs"), (
            "TC-REQ-021-008 FAIL: Expected '/durchlaeufe/planting-runs' hidden for beginner"
        )

    @pytest.mark.core_crud
    def test_intermediate_navigation_adds_sections(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-009: Intermediate sees beginner items + stammdaten, standorte, duengung, kalender.

        Spec: TC-021-014 -- Fortgeschritten-Navigation enthaelt zusaetzliche Abschnitte.
        """
        _set_experience_level(expertise_page, "intermediate")

        expertise_page.navigate("/dashboard")
        expertise_page.wait_for_element(expertise_page.SIDEBAR)
        screenshot(
            "TC-REQ-021-009_intermediate-sidebar",
            "Sidebar in intermediate mode with additional sections",
        )

        assert expertise_page.is_nav_item_visible("/dashboard"), (
            "TC-REQ-021-009 FAIL: Expected '/dashboard' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/pflanzen/plant-instances"), (
            "TC-REQ-021-009 FAIL: Expected '/pflanzen/plant-instances' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/kalender"), (
            "TC-REQ-021-009 FAIL: Expected '/kalender' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/standorte/sites"), (
            "TC-REQ-021-009 FAIL: Expected '/standorte/sites' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/stammdaten/species"), (
            "TC-REQ-021-009 FAIL: Expected '/stammdaten/species' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/stammdaten/botanical-families"), (
            "TC-REQ-021-009 FAIL: Expected '/stammdaten/botanical-families' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/duengung/fertilizers"), (
            "TC-REQ-021-009 FAIL: Expected '/duengung/fertilizers' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/duengung/plans"), (
            "TC-REQ-021-009 FAIL: Expected '/duengung/plans' visible for intermediate"
        )

        # Expert items still hidden
        assert not expertise_page.is_nav_item_visible("/pflanzenschutz/pests"), (
            "TC-REQ-021-009 FAIL: Expected '/pflanzenschutz/pests' hidden for intermediate"
        )
        assert not expertise_page.is_nav_item_visible("/ernte/batches"), (
            "TC-REQ-021-009 FAIL: Expected '/ernte/batches' hidden for intermediate"
        )
        assert not expertise_page.is_nav_item_visible("/durchlaeufe/planting-runs"), (
            "TC-REQ-021-009 FAIL: Expected '/durchlaeufe/planting-runs' hidden for intermediate"
        )
        assert not expertise_page.is_nav_item_visible("/standorte/substrates"), (
            "TC-REQ-021-009 FAIL: Expected '/standorte/substrates' hidden for intermediate"
        )
        assert not expertise_page.is_nav_item_visible("/standorte/tanks"), (
            "TC-REQ-021-009 FAIL: Expected '/standorte/tanks' hidden for intermediate"
        )

    @pytest.mark.core_crud
    def test_expert_navigation_shows_all(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-010: Expert sees all nav sections and items.

        Spec: TC-021-015 -- Experten-Navigation zeigt alle Menuepunkte.
        """
        _set_experience_level(expertise_page, "expert")

        expertise_page.navigate("/dashboard")
        expertise_page.wait_for_element(expertise_page.SIDEBAR)
        screenshot(
            "TC-REQ-021-010_expert-sidebar",
            "Sidebar in expert mode with all nav items visible",
        )

        assert expertise_page.is_nav_item_visible("/pflanzenschutz/pests"), (
            "TC-REQ-021-010 FAIL: Expected '/pflanzenschutz/pests' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/pflanzenschutz/diseases"), (
            "TC-REQ-021-010 FAIL: Expected '/pflanzenschutz/diseases' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/pflanzenschutz/treatments"), (
            "TC-REQ-021-010 FAIL: Expected '/pflanzenschutz/treatments' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/ernte/batches"), (
            "TC-REQ-021-010 FAIL: Expected '/ernte/batches' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/durchlaeufe/planting-runs"), (
            "TC-REQ-021-010 FAIL: Expected '/durchlaeufe/planting-runs' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/standorte/substrates"), (
            "TC-REQ-021-010 FAIL: Expected '/standorte/substrates' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/standorte/tanks"), (
            "TC-REQ-021-010 FAIL: Expected '/standorte/tanks' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/duengung/calculations"), (
            "TC-REQ-021-010 FAIL: Expected '/duengung/calculations' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/stammdaten/companion-planting"), (
            "TC-REQ-021-010 FAIL: Expected '/stammdaten/companion-planting' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/stammdaten/crop-rotation"), (
            "TC-REQ-021-010 FAIL: Expected '/stammdaten/crop-rotation' visible for expert"
        )

    @pytest.mark.core_crud
    def test_direct_url_access_as_beginner_loads_page(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-011: Beginner can directly access expert-only URLs (no access control).

        Spec: TC-021-016 -- Direktaufruf einer Expert-only-URL als Anfaenger -- Seite laedt trotzdem.
        """
        _set_experience_level(expertise_page, "beginner")

        expertise_page.navigate_direct("/standorte/tanks")
        screenshot(
            "TC-REQ-021-011_beginner-direct-tanks-url",
            "Tank list page loaded via direct URL as beginner",
        )

        assert not expertise_page.is_error_displayed(), (
            "TC-REQ-021-011 FAIL: Expected no error when beginner accesses expert-only URL directly"
        )


# -- TC-021-017 to TC-021-019: SpeciesCreateDialog Field Visibility -----------


class TestSpeciesFieldVisibility:
    """Field visibility in SpeciesCreateDialog per level (Spec: TC-021-017 to TC-021-019)."""

    @pytest.mark.core_crud
    def test_beginner_species_dialog_no_fields(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-012: Beginner -- SpeciesCreateDialog shows no fields (all are intermediate+).

        Spec: TC-021-017 -- SpeciesCreateDialog im Anfaenger-Modus -- alle Felder ausgeblendet.
        """
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_species_list()
        expertise_page.open_species_create_dialog()
        screenshot(
            "TC-REQ-021-012_beginner-species-dialog",
            "Species create dialog as beginner -- no fields visible",
        )

        assert not expertise_page.is_form_field_visible("scientific_name"), (
            "TC-REQ-021-012 FAIL: Expected 'scientific_name' hidden for beginner"
        )
        assert not expertise_page.is_form_field_visible("common_names"), (
            "TC-REQ-021-012 FAIL: Expected 'common_names' hidden for beginner"
        )
        assert not expertise_page.is_form_field_visible("family_key"), (
            "TC-REQ-021-012 FAIL: Expected 'family_key' hidden for beginner"
        )
        assert not expertise_page.is_form_field_visible("root_type"), (
            "TC-REQ-021-012 FAIL: Expected 'root_type' hidden for beginner"
        )
        assert expertise_page.is_show_all_fields_visible(), (
            "TC-REQ-021-012 FAIL: Expected ShowAllFieldsToggle button visible"
        )

        expertise_page.close_create_dialog()

    @pytest.mark.core_crud
    def test_intermediate_species_dialog_intermediate_fields(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-013: Intermediate -- SpeciesCreateDialog shows intermediate fields, hides expert.

        Spec: TC-021-018 -- SpeciesCreateDialog im Fortgeschritten-Modus -- intermediate-Felder sichtbar.
        """
        _set_experience_level(expertise_page, "intermediate")

        expertise_page.open_species_list()
        expertise_page.open_species_create_dialog()
        screenshot(
            "TC-REQ-021-013_intermediate-species-dialog",
            "Species create dialog as intermediate -- intermediate fields visible",
        )

        assert expertise_page.is_form_field_visible("scientific_name"), (
            "TC-REQ-021-013 FAIL: Expected 'scientific_name' visible for intermediate"
        )
        assert expertise_page.is_form_field_visible("common_names"), (
            "TC-REQ-021-013 FAIL: Expected 'common_names' visible for intermediate"
        )
        assert expertise_page.is_form_field_visible("family_key"), (
            "TC-REQ-021-013 FAIL: Expected 'family_key' visible for intermediate"
        )
        assert expertise_page.is_form_field_visible("genus"), (
            "TC-REQ-021-013 FAIL: Expected 'genus' visible for intermediate"
        )
        assert not expertise_page.is_form_field_visible("root_type"), (
            "TC-REQ-021-013 FAIL: Expected 'root_type' hidden for intermediate"
        )
        assert not expertise_page.is_form_field_visible("allelopathy_score"), (
            "TC-REQ-021-013 FAIL: Expected 'allelopathy_score' hidden for intermediate"
        )
        assert not expertise_page.is_form_field_visible("hardiness_zones"), (
            "TC-REQ-021-013 FAIL: Expected 'hardiness_zones' hidden for intermediate"
        )

        expertise_page.close_create_dialog()

    @pytest.mark.core_crud
    def test_expert_species_dialog_all_fields(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-014: Expert -- SpeciesCreateDialog shows all fields.

        Spec: TC-021-019 -- SpeciesCreateDialog im Experten-Modus -- alle Felder sichtbar.
        """
        _set_experience_level(expertise_page, "expert")

        expertise_page.open_species_list()
        expertise_page.open_species_create_dialog()
        screenshot(
            "TC-REQ-021-014_expert-species-dialog",
            "Species create dialog as expert -- all fields visible",
        )

        assert expertise_page.is_form_field_visible("scientific_name"), (
            "TC-REQ-021-014 FAIL: Expected 'scientific_name' visible for expert"
        )
        assert expertise_page.is_form_field_visible("root_type"), (
            "TC-REQ-021-014 FAIL: Expected 'root_type' visible for expert"
        )
        assert expertise_page.is_form_field_visible("allelopathy_score"), (
            "TC-REQ-021-014 FAIL: Expected 'allelopathy_score' visible for expert"
        )
        assert expertise_page.is_form_field_visible("hardiness_zones"), (
            "TC-REQ-021-014 FAIL: Expected 'hardiness_zones' visible for expert"
        )

        expertise_page.close_create_dialog()


# -- TC-021-020 to TC-021-022: ShowAllFieldsToggle -----------------------------


class TestShowAllFieldsToggle:
    """Temporary field override via ShowAllFieldsToggle (Spec: TC-021-020 to TC-021-022)."""

    @pytest.mark.core_crud
    def test_show_all_fields_reveals_hidden_fields(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-015: Clicking 'Alle Felder anzeigen' reveals all fields without changing level.

        Spec: TC-021-020 -- 'Alle Felder anzeigen' im Anfaenger-Modus aktivieren.
        """
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_species_list()
        expertise_page.open_species_create_dialog()
        expertise_page.wait_for_loading_complete()

        assert not expertise_page.is_form_field_visible("scientific_name"), (
            "TC-REQ-021-015 FAIL: Expected 'scientific_name' hidden before toggle"
        )

        screenshot(
            "TC-REQ-021-015_before-show-all-fields",
            "Dialog before clicking ShowAllFieldsToggle",
        )

        if not expertise_page.is_show_all_fields_visible():
            expertise_page.close_create_dialog()
            pytest.skip("ShowAllFieldsToggle not visible in species create dialog")

        expertise_page.click_show_all_fields()
        expertise_page.wait_for_loading_complete()
        screenshot(
            "TC-REQ-021-015_after-show-all-fields",
            "Dialog after clicking ShowAllFieldsToggle -- all fields visible",
        )

        assert expertise_page.is_form_field_visible("scientific_name"), (
            "TC-REQ-021-015 FAIL: Expected 'scientific_name' visible after ShowAllFieldsToggle"
        )

        toggle_text = expertise_page.get_show_all_fields_text()
        assert "weniger" in toggle_text.lower() or "fewer" in toggle_text.lower(), (
            f"TC-REQ-021-015 FAIL: Expected toggle text to contain 'weniger'/'fewer', got: '{toggle_text}'"
        )

        expertise_page.close_create_dialog()

    @pytest.mark.core_crud
    def test_show_fewer_fields_hides_again(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-016: Clicking 'Weniger Felder anzeigen' hides extended fields again.

        Spec: TC-021-021 -- 'Weniger Felder anzeigen' -- erweiterte Felder verschwinden wieder.
        """
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_species_list()
        expertise_page.open_species_create_dialog()
        expertise_page.wait_for_loading_complete()

        if not expertise_page.is_show_all_fields_visible():
            expertise_page.close_create_dialog()
            pytest.skip("ShowAllFieldsToggle not visible in species create dialog")

        # Activate show all
        expertise_page.click_show_all_fields()
        expertise_page.wait_for_loading_complete()
        assert expertise_page.is_form_field_visible("scientific_name"), (
            "TC-REQ-021-016 FAIL: Expected fields visible after first toggle click"
        )

        # Deactivate show all
        expertise_page.click_show_all_fields()
        expertise_page.wait_for_loading_complete()
        screenshot(
            "TC-REQ-021-016_after-show-fewer-fields",
            "Dialog after toggling back to fewer fields",
        )

        assert not expertise_page.is_form_field_visible("scientific_name"), (
            "TC-REQ-021-016 FAIL: Expected 'scientific_name' hidden after toggling back"
        )

        toggle_text = expertise_page.get_show_all_fields_text()
        assert "alle" in toggle_text.lower() or "all" in toggle_text.lower(), (
            f"TC-REQ-021-016 FAIL: Expected toggle text to contain 'alle'/'all', got: '{toggle_text}'"
        )

        expertise_page.close_create_dialog()

    @pytest.mark.core_crud
    def test_toggle_resets_after_dialog_close(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-017: ShowAllFieldsToggle state resets when dialog is closed and reopened.

        Spec: TC-021-022 -- Toggle-Zustand wird nach Schliessen des Dialogs zurueckgesetzt.
        """
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_planting_run_list()
        expertise_page.open_planting_run_create_dialog()
        expertise_page.wait_for_loading_complete()

        if not expertise_page.is_show_all_fields_visible():
            expertise_page.close_create_dialog()
            pytest.skip("ShowAllFieldsToggle not visible in planting run create dialog")

        # Activate show all and verify
        expertise_page.click_show_all_fields()
        expertise_page.wait_for_loading_complete()
        has_any_extra_field = (
            expertise_page.is_form_field_visible("substrate_batch_key")
            or expertise_page.is_form_field_visible("source_plant_key")
            or expertise_page.is_form_field_visible("run_type")
            or expertise_page.is_form_field_visible("notes")
            or expertise_page.is_form_field_visible("site_key")
        )
        assert has_any_extra_field, (
            "TC-REQ-021-017 FAIL: Expected at least one extra field visible after ShowAllFields toggle"
        )

        # Close and reopen
        expertise_page.close_create_dialog()
        expertise_page.wait_for_loading_complete()
        expertise_page.open_planting_run_create_dialog()
        expertise_page.wait_for_loading_complete()
        screenshot(
            "TC-REQ-021-017_toggle-reset-after-reopen",
            "PlantingRunCreateDialog reopened -- toggle should be reset",
        )

        toggle_text = expertise_page.get_show_all_fields_text()
        assert "alle" in toggle_text.lower() or "all" in toggle_text.lower(), (
            f"TC-REQ-021-017 FAIL: Expected toggle reset to 'Alle Felder anzeigen', got: '{toggle_text}'"
        )

        expertise_page.close_create_dialog()


# -- TC-021-023 to TC-021-025: PlantingRunCreateDialog Field Visibility --------


class TestPlantingRunFieldVisibility:
    """Field visibility in PlantingRunCreateDialog per level (Spec: TC-021-023 to TC-021-025)."""

    @pytest.mark.core_crud
    def test_beginner_planting_run_dialog_core_fields_only(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-018: Beginner -- PlantingRunCreateDialog shows only 3 core fields.

        Spec: TC-021-023 -- PlantingRunCreateDialog im Anfaenger-Modus -- nur 3 Kernfelder sichtbar.
        """
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_planting_run_list()
        expertise_page.open_planting_run_create_dialog()
        screenshot(
            "TC-REQ-021-018_beginner-planting-run-dialog",
            "PlantingRun create dialog as beginner -- only core fields",
        )

        assert expertise_page.is_form_field_visible("name"), (
            "TC-REQ-021-018 FAIL: Expected 'name' visible for beginner"
        )
        assert not expertise_page.is_form_field_visible("run_type"), (
            "TC-REQ-021-018 FAIL: Expected 'run_type' hidden for beginner"
        )
        assert not expertise_page.is_form_field_visible("site_key"), (
            "TC-REQ-021-018 FAIL: Expected 'site_key' hidden for beginner"
        )
        assert not expertise_page.is_form_field_visible("notes"), (
            "TC-REQ-021-018 FAIL: Expected 'notes' hidden for beginner"
        )
        assert not expertise_page.is_form_field_visible("substrate_batch_key"), (
            "TC-REQ-021-018 FAIL: Expected 'substrate_batch_key' hidden for beginner"
        )

        expertise_page.close_create_dialog()

    @pytest.mark.core_crud
    def test_intermediate_planting_run_dialog(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-019: Intermediate -- PlantingRunCreateDialog shows intermediate fields.

        Spec: TC-021-024 -- PlantingRunCreateDialog im Fortgeschritten-Modus -- zusaetzliche Felder.
        """
        _set_experience_level(expertise_page, "intermediate")

        expertise_page.open_planting_run_list()
        expertise_page.open_planting_run_create_dialog()
        screenshot(
            "TC-REQ-021-019_intermediate-planting-run-dialog",
            "PlantingRun create dialog as intermediate",
        )

        assert expertise_page.is_form_field_visible("name"), (
            "TC-REQ-021-019 FAIL: Expected 'name' visible for intermediate"
        )
        assert expertise_page.is_form_field_visible("run_type"), (
            "TC-REQ-021-019 FAIL: Expected 'run_type' visible for intermediate"
        )
        assert not expertise_page.is_form_field_visible("substrate_batch_key"), (
            "TC-REQ-021-019 FAIL: Expected 'substrate_batch_key' hidden for intermediate"
        )

        expertise_page.close_create_dialog()

    @pytest.mark.core_crud
    def test_expert_planting_run_dialog_all_fields(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-021-020: Expert -- PlantingRunCreateDialog shows all fields.

        Spec: TC-021-025 -- PlantingRunCreateDialog im Experten-Modus -- alle Felder.
        """
        _set_experience_level(expertise_page, "expert")

        expertise_page.open_planting_run_list()
        expertise_page.open_planting_run_create_dialog()
        screenshot(
            "TC-REQ-021-020_expert-planting-run-dialog",
            "PlantingRun create dialog as expert -- all fields visible",
        )

        assert expertise_page.is_form_field_visible("name"), (
            "TC-REQ-021-020 FAIL: Expected 'name' visible for expert"
        )
        assert expertise_page.is_form_field_visible("run_type"), (
            "TC-REQ-021-020 FAIL: Expected 'run_type' visible for expert"
        )
        assert expertise_page.is_form_field_visible("substrate_batch_key"), (
            "TC-REQ-021-020 FAIL: Expected 'substrate_batch_key' visible for expert"
        )

        expertise_page.close_create_dialog()
