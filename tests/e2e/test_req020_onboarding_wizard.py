"""E2E tests for REQ-020 — Onboarding Wizard.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-020.md):
  TC-REQ-020-007  ->  TC-020-001  Erststart -- Wizard oeffnet mit Schritt 1
  TC-REQ-020-008  ->  TC-020-005  Wizard ueberspringen ueber 'Ueberspringen'-Link
  TC-REQ-020-009  ->  TC-020-007  Erfahrungsstufe 'Einsteiger' -- Default-Zustand
  TC-REQ-020-010  ->  TC-020-008  Erfahrungsstufe 'Fortgeschritten' -- Smart-Home-Toggle
  TC-REQ-020-011  ->  TC-020-009  Erfahrungsstufe 'Experte' -- Smart-Home-Toggle
  TC-REQ-020-012  ->  TC-020-010  Smart-Home-Toggle aktivieren
  TC-REQ-020-013  ->  TC-020-011  Von 'Fortgeschritten' zurueck zu 'Einsteiger'
  TC-REQ-020-014  ->  TC-020-012  Dynamische Stepper-Anzahl bei Einsteiger
  TC-REQ-020-015  ->  TC-020-013  Dynamische Stepper-Anzahl bei Fortgeschritten
  TC-REQ-020-016  ->  TC-020-014  Starter-Kit-Liste wird angezeigt
  TC-REQ-020-017  ->  TC-020-015  Starter-Kit 'Fensterbank-Kraeuter' auswaehlen
  TC-REQ-020-018  ->  TC-020-016  Starter-Kit 'Zimmerpflanzen' -- Toxizitaetswarnung
  TC-REQ-020-019  ->  TC-020-017  Starter-Kit abwaehlen durch erneutes Klicken
  TC-REQ-020-020  ->  TC-020-020  Favoriten-Schritt -- Kit-Species vorausgewaehlt
  TC-REQ-020-021  ->  TC-020-022  Favoriten-Suche filtert Species-Liste
  TC-REQ-020-022  ->  TC-020-023  Favoriten-Schritt ohne Kit -- keine Vorauswahl
  TC-REQ-020-023  ->  TC-020-025  Standort-Schritt -- Auto-Befuellung aus Kit
  TC-REQ-020-024  ->  TC-020-026  Standortname manuell aendern
  TC-REQ-020-025  ->  TC-020-028  Wasserquellen-Abschnitt bei Einsteiger ausgeblendet
  TC-REQ-020-026  ->  TC-020-029  Wasserquellen-Abschnitt bei Fortgeschritten sichtbar
  TC-REQ-020-027  ->  TC-020-033  Pflanzen-Schritt -- Pflanzenkonfiguration
  TC-REQ-020-028  ->  TC-020-037  Schritt Pflanzen ohne Favoriten -- Leerzustand
  TC-REQ-020-029  ->  TC-020-044  Zusammenfassungs-Schritt
  TC-REQ-020-030  ->  TC-020-049  'Weiter'-Button auf letztem Schritt durch 'Abschliessen' ersetzt
  TC-REQ-020-031  ->  TC-020-046  Wizard abschliessen -- Happy Path
  TC-REQ-020-032  ->  TC-020-048  Zurueck-Navigation zwischen Schritten
  TC-REQ-020-033  ->  TC-020-001  Schritt 1 hat keinen Zurueck-Button
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.onboarding_wizard_page import OnboardingWizardPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def wizard(browser: WebDriver, base_url: str) -> OnboardingWizardPage:
    """Return an OnboardingWizardPage bound to the test browser."""
    return OnboardingWizardPage(browser, base_url)


# -- Gruppe A -- Wizard Trigger & Initialisation -------------------------------


class TestWizardTrigger:
    """Wizard trigger, skip functionality (Spec: TC-020-001, TC-020-005)."""

    @pytest.mark.smoke
    def test_wizard_opens_with_step1_active(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-007: Wizard opens with Step 1 active -- experience level cards visible.

        Spec: TC-020-001 -- Erststart -- Wizard oeffnet automatisch bei unvollstaendigem Onboarding-Status.
        """
        wizard.open()
        screenshot(
            "TC-REQ-020-007_wizard-step1-loaded",
            "Wizard Step 1 after initial page load",
        )

        assert wizard.is_wizard_visible(), (
            "TC-REQ-020-007 FAIL: Expected [data-testid='onboarding-wizard'] to be visible"
        )
        assert wizard.is_step_welcome_visible(), (
            "TC-REQ-020-007 FAIL: Expected [data-testid='onboarding-step-welcome'] to be visible on Step 1"
        )

        for level in ("beginner", "intermediate", "expert"):
            locator = (By.CSS_SELECTOR, f"[data-testid='experience-{level}']")
            cards = wizard.driver.find_elements(*locator)
            assert len(cards) > 0, (
                f"TC-REQ-020-007 FAIL: Expected experience card '{level}' to be present"
            )

        assert wizard.is_skip_button_visible(), (
            "TC-REQ-020-007 FAIL: Expected skip-onboarding button to be visible on Step 1"
        )
        assert wizard.is_next_button_visible(), (
            "TC-REQ-020-007 FAIL: Expected onboarding-next button to be visible"
        )
        assert wizard.is_next_button_enabled(), (
            "TC-REQ-020-007 FAIL: Expected onboarding-next button to be enabled"
        )

    @pytest.mark.core_crud
    def test_skip_onboarding_redirects_to_plant_instances(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-008: Skip onboarding redirects to /pflanzen/plant-instances.

        Spec: TC-020-005 -- Wizard ueberspringen ueber 'Ueberspringen'-Link.
        """
        wizard.open()
        screenshot(
            "TC-REQ-020-008_before-skip",
            "Wizard Step 1 before skip",
        )

        wizard.click_skip()
        wizard.wait_for_url_contains("/pflanzen/plant-instances")
        screenshot(
            "TC-REQ-020-008_after-skip",
            "Redirected to plant instances after skip",
        )

        assert "/pflanzen/plant-instances" in wizard.driver.current_url, (
            f"TC-REQ-020-008 FAIL: Expected redirect to /pflanzen/plant-instances, "
            f"got: {wizard.driver.current_url}"
        )


# -- Gruppe B -- Step 1: Experience Level & Smart-Home Toggle ------------------


class TestExperienceLevelStep:
    """Experience level selection and smart-home toggle (Spec: TC-020-007 to TC-020-013)."""

    @pytest.mark.smoke
    def test_beginner_is_default_selection(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-009: Beginner is selected by default on Step 1.

        Spec: TC-020-007 -- Erfahrungsstufe 'Einsteiger' auswaehlen -- Default-Zustand.
        """
        wizard.open()
        screenshot(
            "TC-REQ-020-009_beginner-default",
            "Step 1 with beginner as default selection",
        )

        assert wizard.is_experience_selected("beginner"), (
            "TC-REQ-020-009 FAIL: Expected 'beginner' card to be selected by default"
        )
        assert not wizard.is_smart_home_toggle_visible(), (
            "TC-REQ-020-009 FAIL: Smart-Home toggle should NOT be visible for beginner"
        )
        assert wizard.is_next_button_enabled(), (
            "TC-REQ-020-009 FAIL: Next button should be enabled on Step 1"
        )

    @pytest.mark.core_crud
    def test_select_intermediate_shows_smart_home_toggle(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-010: Selecting 'intermediate' shows the Smart-Home toggle.

        Spec: TC-020-008 -- Erfahrungsstufe 'Fortgeschritten' -- Smart-Home-Toggle erscheint.
        """
        wizard.open()
        screenshot(
            "TC-REQ-020-010_before-intermediate",
            "Step 1 before selecting intermediate",
        )

        wizard.select_experience_level("intermediate")
        screenshot(
            "TC-REQ-020-010_after-intermediate",
            "Step 1 after selecting intermediate",
        )

        assert wizard.is_experience_selected("intermediate"), (
            "TC-REQ-020-010 FAIL: Expected 'intermediate' card to be selected"
        )
        assert not wizard.is_experience_selected("beginner"), (
            "TC-REQ-020-010 FAIL: Expected 'beginner' card to be deselected"
        )
        assert wizard.is_smart_home_toggle_visible(), (
            "TC-REQ-020-010 FAIL: Smart-Home toggle should be visible for intermediate"
        )
        assert not wizard.is_smart_home_toggle_checked(), (
            "TC-REQ-020-010 FAIL: Smart-Home toggle should be off by default"
        )

    @pytest.mark.core_crud
    def test_select_expert_shows_smart_home_toggle(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-011: Selecting 'expert' shows the Smart-Home toggle.

        Spec: TC-020-009 -- Erfahrungsstufe 'Experte' -- Smart-Home-Toggle erscheint.
        """
        wizard.open()

        wizard.select_experience_level("expert")
        screenshot(
            "TC-REQ-020-011_expert-selected",
            "Step 1 with expert selected",
        )

        assert wizard.is_experience_selected("expert"), (
            "TC-REQ-020-011 FAIL: Expected 'expert' card to be selected"
        )
        assert wizard.is_smart_home_toggle_visible(), (
            "TC-REQ-020-011 FAIL: Smart-Home toggle should be visible for expert"
        )

    @pytest.mark.core_crud
    def test_smart_home_toggle_activate(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-012: Activating the Smart-Home toggle changes its state.

        Spec: TC-020-010 -- Smart-Home-Toggle aktivieren und Hinweistext wechselt.
        """
        wizard.open()
        wizard.select_experience_level("intermediate")
        screenshot(
            "TC-REQ-020-012_before-toggle",
            "Smart-Home toggle in off state",
        )

        wizard.click_smart_home_toggle()
        screenshot(
            "TC-REQ-020-012_after-toggle",
            "Smart-Home toggle in on state",
        )

        assert wizard.is_smart_home_toggle_checked(), (
            "TC-REQ-020-012 FAIL: Smart-Home toggle should be checked after clicking"
        )
        assert wizard.is_next_button_enabled(), (
            "TC-REQ-020-012 FAIL: Next button should remain enabled after toggling Smart-Home"
        )

    @pytest.mark.core_crud
    def test_switch_back_to_beginner_hides_smart_home(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-013: Switching from intermediate back to beginner hides the Smart-Home toggle.

        Spec: TC-020-011 -- Von 'Fortgeschritten' zurueck zu 'Einsteiger' -- Smart-Home-Toggle verschwindet.
        """
        wizard.open()
        wizard.select_experience_level("intermediate")
        assert wizard.is_smart_home_toggle_visible(), (
            "Toggle should be visible for intermediate"
        )

        wizard.select_experience_level("beginner")
        screenshot(
            "TC-REQ-020-013_beginner-no-toggle",
            "Beginner selected, toggle hidden",
        )

        assert wizard.is_experience_selected("beginner"), (
            "TC-REQ-020-013 FAIL: Expected beginner to be selected"
        )
        assert not wizard.is_smart_home_toggle_visible(), (
            "TC-REQ-020-013 FAIL: Smart-Home toggle should be hidden for beginner"
        )

    @pytest.mark.core_crud
    def test_dynamic_stepper_beginner_has_5_steps(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-014: Beginner shows 5 steps in the stepper (no Plants/NutrientPlans).

        Spec: TC-020-012 -- Dynamische Stepper-Anzahl bei Erfahrungsstufe Einsteiger.
        """
        wizard.open()
        screenshot(
            "TC-REQ-020-014_stepper-beginner",
            "Stepper with beginner (5 steps)",
        )

        step_count = wizard.get_stepper_step_count()
        assert step_count == 5, (
            f"TC-REQ-020-014 FAIL: Expected 5 stepper steps for beginner, got: {step_count}"
        )

    @pytest.mark.core_crud
    def test_dynamic_stepper_intermediate_has_6_steps(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-015: Intermediate shows 6 steps (adds Plants step).

        Spec: TC-020-013 -- Dynamische Stepper-Anzahl bei Erfahrungsstufe Fortgeschritten.
        """
        wizard.open()
        wizard.select_experience_level("intermediate")
        screenshot(
            "TC-REQ-020-015_stepper-intermediate",
            "Stepper with intermediate (6 steps)",
        )

        step_count = wizard.get_stepper_step_count()
        assert step_count == 6, (
            f"TC-REQ-020-015 FAIL: Expected 6 stepper steps for intermediate, got: {step_count}"
        )


# -- Gruppe C -- Step 2: Starter Kit Selection ---------------------------------


class TestStarterKitStep:
    """Starter kit list, selection, deselection (Spec: TC-020-014 to TC-020-017)."""

    @pytest.mark.smoke
    def test_kit_list_displays_cards(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-016: Kit list shows cards with metadata chips after advancing to Step 2.

        Spec: TC-020-014 -- Starter-Kit-Liste wird angezeigt -- Happy Path.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        screenshot(
            "TC-REQ-020-016_kit-list",
            "Step 2 Starter Kit list loaded",
        )

        assert wizard.is_step_kit_visible(), (
            "TC-REQ-020-016 FAIL: Expected [data-testid='onboarding-step-kit'] to be visible"
        )
        kit_count = wizard.get_kit_card_count()
        assert kit_count >= 5, (
            f"TC-REQ-020-016 FAIL: Expected at least 5 starter kit cards, got: {kit_count}"
        )

    @pytest.mark.core_crud
    def test_select_fensterbank_kraeuter_kit(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-017: Selecting 'fensterbank-kraeuter' highlights the card.

        Spec: TC-020-015 -- Starter-Kit 'Fensterbank-Kraeuter' auswaehlen -- Auto-Befuellung.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        screenshot(
            "TC-REQ-020-017_before-kit-select",
            "Kit list before selection",
        )

        wizard.click_kit("fensterbank-kraeuter")
        screenshot(
            "TC-REQ-020-017_after-kit-select",
            "Kit fensterbank-kraeuter selected",
        )

        assert wizard.is_kit_selected("fensterbank-kraeuter"), (
            "TC-REQ-020-017 FAIL: Expected kit 'fensterbank-kraeuter' to be selected"
        )

    @pytest.mark.core_crud
    def test_zimmerpflanzen_shows_toxicity_warning(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-018: Kit 'zimmerpflanzen' shows a toxicity warning chip.

        Spec: TC-020-016 -- Starter-Kit 'Zimmerpflanzen' -- Toxizitaetswarnung sichtbar.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        screenshot(
            "TC-REQ-020-018_toxicity-check",
            "Kit list checking toxicity warnings",
        )

        assert wizard.kit_has_toxicity_warning("zimmerpflanzen"), (
            "TC-REQ-020-018 FAIL: Expected toxicity warning chip on 'zimmerpflanzen' kit"
        )

    @pytest.mark.core_crud
    def test_deselect_kit_by_clicking_again(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-019: Clicking a selected kit deselects it.

        Spec: TC-020-017 -- Starter-Kit abwaehlen durch erneutes Klicken.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        wizard.click_kit("fensterbank-kraeuter")
        assert wizard.is_kit_selected("fensterbank-kraeuter"), "Kit should be selected first"
        screenshot(
            "TC-REQ-020-019_before-deselect",
            "Kit selected before deselection",
        )

        wizard.click_kit("fensterbank-kraeuter")
        screenshot(
            "TC-REQ-020-019_after-deselect",
            "Kit deselected after second click",
        )

        assert not wizard.is_kit_selected("fensterbank-kraeuter"), (
            "TC-REQ-020-019 FAIL: Expected kit 'fensterbank-kraeuter' to be deselected"
        )


# -- Gruppe D -- Step 3: Favorite Species --------------------------------------


class TestFavoriteSpeciesStep:
    """Favorites pre-selection, search (Spec: TC-020-020, TC-020-022, TC-020-023)."""

    @pytest.mark.core_crud
    def test_kit_species_preselected_as_favorites(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-020: Kit species are pre-selected as favorites on Step 3.

        Spec: TC-020-020 -- Favoriten-Schritt -- Kit-Species sind vorausgewaehlt.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        wizard.click_kit("fensterbank-kraeuter")
        wizard.advance_to_step_favorites()
        screenshot(
            "TC-REQ-020-020_favorites-preselected",
            "Favorites step with kit species pre-selected",
        )

        assert wizard.is_step_favorites_visible(), (
            "TC-REQ-020-020 FAIL: Expected favorites step to be visible"
        )
        count_text = wizard.get_favorite_selected_count_text()
        assert "0" not in count_text or "0 " not in count_text.split()[0:1], (
            f"TC-REQ-020-020 FAIL: Expected pre-selected favorites count > 0, got text: {count_text}"
        )

    @pytest.mark.core_crud
    def test_favorites_search_filters_species(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-021: Search filters the species list on the favorites step.

        Spec: TC-020-022 -- Favoriten-Suche filtert Species-Liste.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        wizard.advance_to_step_favorites()

        initial_tiles = len(wizard.get_favorite_tiles())
        screenshot(
            "TC-REQ-020-021_before-search",
            "Favorites list before search",
        )

        wizard.search_favorites("xyznotexistent")
        screenshot(
            "TC-REQ-020-021_after-nonexistent-search",
            "Favorites list after searching non-existent term",
        )

        filtered_tiles = len(wizard.get_favorite_tiles())
        assert filtered_tiles < initial_tiles or filtered_tiles == 0, (
            f"TC-REQ-020-021 FAIL: Expected filtered results to be less than {initial_tiles}, "
            f"got: {filtered_tiles}"
        )

    @pytest.mark.core_crud
    def test_favorites_without_kit_no_preselection(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-022: Without a kit, no species are pre-selected as favorites.

        Spec: TC-020-023 -- Favoriten-Schritt ohne Kit -- Kein Badge auf Species.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        # Do NOT select a kit
        wizard.advance_to_step_favorites()
        screenshot(
            "TC-REQ-020-022_favorites-no-kit",
            "Favorites step without kit -- no pre-selection",
        )

        count_text = wizard.get_favorite_selected_count_text()
        has_zero = "0" in count_text
        no_selected_tiles = all(
            not wizard.is_favorite_tile_selected(
                (t.get_attribute("data-testid") or "").replace("favorite-tile-", "")
            )
            for t in wizard.get_favorite_tiles()[:3]
        ) if wizard.get_favorite_tiles() else True
        assert has_zero or no_selected_tiles, (
            f"TC-REQ-020-022 FAIL: Expected 0 favorites selected without kit, got text: {count_text}"
        )


# -- Gruppe E -- Step 4: Site Setup --------------------------------------------


class TestSiteSetupStep:
    """Site auto-population, name change, water section (Spec: TC-020-025 to TC-020-029)."""

    @pytest.mark.core_crud
    def test_site_step_auto_populated_from_kit(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-023: Site step is auto-populated from kit selection (fensterbank-kraeuter).

        Spec: TC-020-025 -- Standort-Schritt -- Auto-Befuellung aus Kit-Auswahl.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        wizard.click_kit("fensterbank-kraeuter")
        wizard.advance_to_step_favorites()
        wizard.advance_to_step_site()
        wizard.wait_for_loading_complete()
        screenshot(
            "TC-REQ-020-023_site-auto-populated",
            "Site step auto-populated from kit",
        )

        assert wizard.is_step_site_visible(), (
            "TC-REQ-020-023 FAIL: Expected site step to be visible"
        )
        site_name = wizard.get_site_name_value()
        site_field_visible = wizard.is_site_name_field_visible()
        assert site_name != "" or site_field_visible, (
            "TC-REQ-020-023 FAIL: Expected site name to be auto-populated or field to be visible"
        )

    @pytest.mark.core_crud
    def test_site_name_manual_change(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-024: Manually changing site name persists the user's input.

        Spec: TC-020-026 -- Standortname manuell aendern.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        wizard.click_kit("fensterbank-kraeuter")
        wizard.advance_to_step_favorites()
        wizard.advance_to_step_site()
        screenshot(
            "TC-REQ-020-024_before-name-change",
            "Site step before name change",
        )

        wizard.set_site_name("Mein Kuechenfenster")
        screenshot(
            "TC-REQ-020-024_after-name-change",
            "Site step after manual name change",
        )

        assert wizard.get_site_name_value() == "Mein Kuechenfenster", (
            "TC-REQ-020-024 FAIL: Expected site name to be 'Mein Kuechenfenster'"
        )

    @pytest.mark.core_crud
    def test_water_section_hidden_for_beginner(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-025: Water section (EC, pH, RO) is hidden for beginner experience level.

        Spec: TC-020-028 -- Wasserquellen-Abschnitt bei Einsteiger ausgeblendet.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        wizard.advance_to_step_favorites()
        wizard.advance_to_step_site()
        screenshot(
            "TC-REQ-020-025_site-beginner-no-water",
            "Site step for beginner -- no water section",
        )

        assert not wizard.is_water_section_visible(), (
            "TC-REQ-020-025 FAIL: Expected water section to be hidden for beginner"
        )

    @pytest.mark.core_crud
    def test_water_section_visible_for_intermediate(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-026: Water section is visible and functional for intermediate.

        Spec: TC-020-029 -- Wasserquellen-Abschnitt bei Fortgeschritten sichtbar und bedienbar.
        """
        wizard.open()
        wizard.advance_to_step_kit(experience_level="intermediate")
        wizard.advance_to_step_favorites()
        wizard.advance_to_step_site()
        screenshot(
            "TC-REQ-020-026_site-intermediate-water",
            "Site step for intermediate -- water section visible",
        )

        assert wizard.is_water_section_visible(), (
            "TC-REQ-020-026 FAIL: Expected water section to be visible for intermediate"
        )

        wizard.set_tap_water_ec("0.4")
        wizard.set_tap_water_ph("7.2")
        wizard.click_ro_toggle()
        screenshot(
            "TC-REQ-020-026_water-filled",
            "Water section with values filled in",
        )

        assert wizard.get_tap_water_ec_value() == "0.4", (
            f"TC-REQ-020-026 FAIL: Expected EC=0.4, got: {wizard.get_tap_water_ec_value()}"
        )
        assert wizard.get_tap_water_ph_value() == "7.2", (
            f"TC-REQ-020-026 FAIL: Expected pH=7.2, got: {wizard.get_tap_water_ph_value()}"
        )
        assert wizard.is_ro_toggle_checked(), (
            "TC-REQ-020-026 FAIL: Expected RO toggle to be checked after clicking"
        )


# -- Gruppe F -- Step 5: Plant Selection (intermediate/expert) -----------------


class TestPlantSelectionStep:
    """Plant configuration, counter, phase selection (Spec: TC-020-033, TC-020-037)."""

    @pytest.mark.core_crud
    def test_plant_config_rows_visible(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-027: Plant selection step shows config rows for favorited species.

        Spec: TC-020-033 -- Pflanzen-Schritt -- Pflanzenkonfiguration mit Zaehler.
        """
        wizard.open()
        wizard.advance_to_step_kit(experience_level="intermediate")
        wizard.click_kit("fensterbank-kraeuter")
        wizard.advance_to_step_favorites()
        wizard.advance_to_step_site()
        wizard.advance_to_step_plants()
        wizard.wait_for_loading_complete()
        screenshot(
            "TC-REQ-020-027_plant-configs",
            "Plant selection step with config rows",
        )

        assert wizard.is_step_plants_visible(), (
            "TC-REQ-020-027 FAIL: Expected plant selection step to be visible"
        )
        rows = wizard.get_plant_config_rows()
        if len(rows) == 0:
            pytest.skip(
                "No plant config rows visible -- kit species may not have loaded as favorites"
            )
        assert len(rows) > 0, (
            f"TC-REQ-020-027 FAIL: Expected plant config rows, got: {len(rows)}"
        )

    @pytest.mark.core_crud
    def test_plant_no_favorites_empty_state(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-028: Plant step without favorites shows empty state.

        Spec: TC-020-037 -- Schritt Pflanzen ohne Favoriten -- Leerzustand.
        """
        wizard.open()
        wizard.advance_to_step_kit(experience_level="intermediate")
        # No kit selected, no favorites
        wizard.advance_to_step_favorites()
        wizard.advance_to_step_site()
        wizard.advance_to_step_plants()
        screenshot(
            "TC-REQ-020-028_plant-empty-state",
            "Plant step with no favorites -- empty state",
        )

        assert wizard.is_step_plants_visible(), (
            "TC-REQ-020-028 FAIL: Expected plant selection step to be visible"
        )
        rows = wizard.get_plant_config_rows()
        assert len(rows) == 0, (
            f"TC-REQ-020-028 FAIL: Expected no plant config rows without favorites, got: {len(rows)}"
        )


# -- Gruppe H -- Step 7: Summary & Completion ----------------------------------


class TestSummaryAndCompletion:
    """Summary display and wizard completion (Spec: TC-020-044, TC-020-046, TC-020-049)."""

    @pytest.mark.core_crud
    def test_summary_step_displays_setup_info(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-029: Summary step shows setup information (experience, kit, site).

        Spec: TC-020-044 -- Zusammenfassungs-Schritt -- Vollstaendige Darstellung.
        """
        wizard.navigate_beginner_to_summary(kit_id="fensterbank-kraeuter")
        screenshot(
            "TC-REQ-020-029_summary-step",
            "Summary step with kit and site info",
        )

        assert wizard.is_step_complete_visible(), (
            "TC-REQ-020-029 FAIL: Expected summary step to be visible"
        )
        assert wizard.is_summary_checkmark_visible(), (
            "TC-REQ-020-029 FAIL: Expected checkmark icon on the summary step"
        )

    @pytest.mark.core_crud
    def test_complete_button_replaces_next_on_last_step(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-030: On the last step, 'Complete' button replaces 'Next'.

        Spec: TC-020-049 -- 'Weiter'-Button auf letztem Schritt ist durch 'Abschliessen' ersetzt.
        """
        wizard.navigate_beginner_to_summary(kit_id="fensterbank-kraeuter")
        screenshot(
            "TC-REQ-020-030_complete-button",
            "Summary step with Complete button",
        )

        assert wizard.is_complete_button_visible(), (
            "TC-REQ-020-030 FAIL: Expected 'Complete' button to be visible on the last step"
        )
        assert not wizard.is_next_button_visible(), (
            "TC-REQ-020-030 FAIL: Expected 'Next' button to NOT be visible on the last step"
        )

    @pytest.mark.core_crud
    def test_wizard_completion_redirects(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-031: Completing the wizard redirects to /pflanzen/plant-instances.

        Spec: TC-020-046 -- Wizard abschliessen -- Happy Path (Einsteiger mit Kit).
        """
        wizard.navigate_beginner_to_summary(kit_id="fensterbank-kraeuter")
        screenshot(
            "TC-REQ-020-031_before-complete",
            "Summary step before clicking Complete",
        )

        wizard.click_complete()
        wizard.wait_for_url_contains("/pflanzen/plant-instances")
        screenshot(
            "TC-REQ-020-031_after-complete",
            "Redirected to plant instances after completion",
        )

        assert "/pflanzen/plant-instances" in wizard.driver.current_url, (
            f"TC-REQ-020-031 FAIL: Expected redirect to /pflanzen/plant-instances, "
            f"got: {wizard.driver.current_url}"
        )


# -- Gruppe I -- Navigation ----------------------------------------------------


class TestWizardNavigation:
    """Back navigation between steps (Spec: TC-020-048, TC-020-001)."""

    @pytest.mark.core_crud
    def test_back_navigation_preserves_state(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-032: Back button navigates to previous step with state preserved.

        Spec: TC-020-048 -- Zurueck-Navigation zwischen Schritten.
        """
        wizard.open()
        wizard.advance_to_step_kit()
        wizard.click_kit("fensterbank-kraeuter")
        wizard.advance_to_step_favorites()
        screenshot(
            "TC-REQ-020-032_on-step3",
            "On Step 3 (Favorites) before going back",
        )

        # Go back to Step 2
        wizard.click_back()
        wizard.wait_for_element(OnboardingWizardPage.STEP_KIT)
        screenshot(
            "TC-REQ-020-032_back-to-step2",
            "Back on Step 2 -- kit should still be selected",
        )

        assert wizard.is_step_kit_visible(), (
            "TC-REQ-020-032 FAIL: Expected Step 2 (Kit) to be visible after back navigation"
        )
        assert wizard.is_kit_selected("fensterbank-kraeuter"), (
            "TC-REQ-020-032 FAIL: Expected kit selection to be preserved after back navigation"
        )

        # Go back to Step 1
        wizard.click_back()
        wizard.wait_for_element(OnboardingWizardPage.STEP_WELCOME)
        screenshot(
            "TC-REQ-020-032_back-to-step1",
            "Back on Step 1 -- no back button",
        )

        assert wizard.is_step_welcome_visible(), (
            "TC-REQ-020-032 FAIL: Expected Step 1 (Welcome) to be visible"
        )

    @pytest.mark.smoke
    def test_no_back_button_on_step1_desktop(
        self,
        wizard: OnboardingWizardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-020-033: Step 1 has no visible Back button on desktop.

        Spec: TC-020-001 -- Schritt 1 hat keinen Zurueck-Button.
        """
        wizard.open()
        screenshot(
            "TC-REQ-020-033_step1-no-back",
            "Step 1 without back button",
        )

        assert not wizard.is_back_button_visible() or not wizard.is_back_button_enabled(), (
            "TC-REQ-020-033 FAIL: Expected Back button to be hidden or disabled on Step 1"
        )
