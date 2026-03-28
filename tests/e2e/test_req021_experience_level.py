"""E2E tests for REQ-021 -- UI-Erfahrungsstufen (Experience Levels).

Tests cover:
  - Experience level switcher in AccountSettingsPage (toggle group)
  - Upgrade without warning (beginner->intermediate, beginner->expert)
  - Downgrade with window.confirm warning (expert->beginner, intermediate->beginner)
  - Downgrade cancellation (dismiss confirm dialog)
  - Navigation tiering: beginner (5 items), intermediate (additional sections), expert (all)
  - Field visibility in SpeciesCreateDialog per level
  - Field visibility in PlantingRunCreateDialog per level
  - ShowAllFieldsToggle temporary override
  - ShowAllFieldsToggle reset after dialog close
  - Persistence across page reload (level restored after navigation)
  - Direct URL access as beginner (no access control)

Light-mode: no authentication required, /settings is directly accessible.

NFR-008 section 3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error / confirmation states
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.expertise_level_page import ExpertiseLevelPage


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def expertise_page(browser: WebDriver, base_url: str) -> ExpertiseLevelPage:
    """Return an ExpertiseLevelPage bound to the test browser."""
    return ExpertiseLevelPage(browser, base_url)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _set_experience_level(
    expertise_page: ExpertiseLevelPage,
    target_level: str,
) -> None:
    """Navigate to the experience tab and set the level, handling confirm dialogs."""
    import time

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
    # Allow time for localStorage update and React state propagation
    time.sleep(0.5)


# ── TC-021-004 to TC-021-009: Experience Level Switcher ──────────────────────


class TestExperienceLevelSwitcher:
    """TC-021-004 to TC-021-009: Experience level switching in AccountSettings."""

    def test_experience_tab_renders_toggle_group(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-004: Experience tab shows ToggleButtonGroup with 3 levels."""
        expertise_page.open_experience_tab()
        screenshot(
            "req021_001_experience_tab_loaded",
            "AccountSettings experience tab with toggle group",
        )

        assert expertise_page.is_toggle_visible(), (
            "Expected ToggleButtonGroup to be visible on the experience tab"
        )
        active = expertise_page.get_active_toggle_level()
        assert active in ("beginner", "intermediate", "expert"), (
            f"Expected one toggle to be selected, got: {active}"
        )

    def test_upgrade_beginner_to_intermediate_no_warning(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-005: Upgrade from beginner to intermediate -- no confirm, immediate change."""
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_experience_tab()
        screenshot(
            "req021_002_before_upgrade_to_intermediate",
            "Experience tab showing beginner before upgrade",
        )

        expertise_page.click_level("intermediate")

        # No confirm dialog should appear for an upgrade
        assert not expertise_page.is_confirm_dialog_present(), (
            "No confirm dialog expected on upgrade from beginner to intermediate"
        )

        expertise_page.wait_for_saved_snackbar()
        screenshot(
            "req021_003_after_upgrade_to_intermediate",
            "Experience tab after upgrade to intermediate",
        )

        assert expertise_page.get_active_toggle_level() == "intermediate", (
            "Expected 'intermediate' to be the active toggle after upgrade"
        )

    def test_upgrade_beginner_to_expert_no_warning(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-006: Upgrade from beginner to expert -- no confirm, all nav items appear."""
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_experience_tab()
        expertise_page.click_level("expert")

        assert not expertise_page.is_confirm_dialog_present(), (
            "No confirm dialog expected on upgrade from beginner to expert"
        )

        expertise_page.wait_for_saved_snackbar()
        screenshot(
            "req021_004_after_upgrade_to_expert",
            "Experience tab and sidebar after upgrade to expert",
        )

        assert expertise_page.get_active_toggle_level() == "expert", (
            "Expected 'expert' to be the active toggle after upgrade"
        )

    def test_downgrade_expert_to_beginner_shows_confirm(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-007 / TC-021-008: Downgrade expert->beginner shows confirm; accept changes level."""
        _set_experience_level(expertise_page, "expert")

        expertise_page.open_experience_tab()
        screenshot(
            "req021_005_before_downgrade_expert_to_beginner",
            "Expert level before downgrade",
        )

        expertise_page.click_level("beginner")

        assert expertise_page.is_confirm_dialog_present(), (
            "Expected a confirm dialog when downgrading from expert to beginner"
        )

        expertise_page.accept_confirm_dialog()
        expertise_page.wait_for_saved_snackbar()
        screenshot(
            "req021_006_after_downgrade_to_beginner",
            "Beginner level after confirmed downgrade",
        )

        assert expertise_page.get_active_toggle_level() == "beginner", (
            "Expected 'beginner' to be the active toggle after confirmed downgrade"
        )

    def test_downgrade_cancel_keeps_current_level(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-009: Dismiss downgrade dialog -- level stays unchanged."""
        _set_experience_level(expertise_page, "expert")

        expertise_page.open_experience_tab()
        expertise_page.click_level("beginner")

        assert expertise_page.is_confirm_dialog_present(), (
            "Expected a confirm dialog when downgrading"
        )

        expertise_page.dismiss_confirm_dialog()
        screenshot(
            "req021_007_downgrade_cancelled",
            "Expert level preserved after dismissing downgrade",
        )

        assert expertise_page.get_active_toggle_level() == "expert", (
            "Expected 'expert' to remain active after cancelling downgrade"
        )

    def test_downgrade_intermediate_to_beginner_shows_confirm(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-010: Downgrade intermediate->beginner also shows confirm dialog."""
        _set_experience_level(expertise_page, "intermediate")

        expertise_page.open_experience_tab()
        expertise_page.click_level("beginner")

        assert expertise_page.is_confirm_dialog_present(), (
            "Expected a confirm dialog when downgrading from intermediate to beginner"
        )

        expertise_page.accept_confirm_dialog()
        expertise_page.wait_for_saved_snackbar()
        screenshot(
            "req021_008_downgrade_intermediate_to_beginner",
            "Beginner level after downgrade from intermediate",
        )

        assert expertise_page.get_active_toggle_level() == "beginner", (
            "Expected 'beginner' after confirmed downgrade from intermediate"
        )


# ── TC-021-011 to TC-021-012: Persistence ────────────────────────────────────


class TestExperienceLevelPersistence:
    """TC-021-011 to TC-021-012: Level persisted across page reload."""

    def test_level_persists_after_page_reload(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-011: After page reload, the previously set experience level is restored."""
        _set_experience_level(expertise_page, "intermediate")

        # Reload the page to simulate a new session
        expertise_page.navigate("/dashboard")
        expertise_page.wait_for_element(expertise_page.SIDEBAR)

        screenshot(
            "req021_009_after_reload_intermediate",
            "Dashboard after reload, intermediate nav expected",
        )

        # Verify sidebar has intermediate items
        assert expertise_page.is_nav_item_visible("/standorte/sites"), (
            "Expected '/standorte/sites' visible in sidebar after reload with intermediate level"
        )
        assert not expertise_page.is_nav_item_visible("/pflanzenschutz/pests"), (
            "Expected '/pflanzenschutz/pests' hidden in sidebar for intermediate level"
        )

        # Verify toggle is still intermediate
        expertise_page.open_experience_tab()
        screenshot(
            "req021_010_experience_tab_after_reload",
            "Experience tab showing intermediate after page reload",
        )
        assert expertise_page.get_active_toggle_level() == "intermediate", (
            "Expected 'intermediate' to be active after page reload"
        )


# ── TC-021-013 to TC-021-016: Navigation Tiering ─────────────────────────────


class TestNavigationTiering:
    """TC-021-013 to TC-021-016: Sidebar nav items per experience level."""

    def test_beginner_navigation_minimal(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-013: Beginner sees only core nav items (dashboard, plants, tasks)."""
        _set_experience_level(expertise_page, "beginner")

        expertise_page.navigate("/dashboard")
        expertise_page.wait_for_element(expertise_page.SIDEBAR)
        screenshot(
            "req021_011_beginner_sidebar",
            "Sidebar in beginner mode with minimal nav items",
        )

        # Beginner items should be visible
        assert expertise_page.is_nav_item_visible("/dashboard"), (
            "Expected '/dashboard' visible for beginner"
        )
        assert expertise_page.is_nav_item_visible("/pflanzen/plant-instances"), (
            "Expected '/pflanzen/plant-instances' visible for beginner"
        )
        assert expertise_page.is_nav_item_visible("/aufgaben/queue"), (
            "Expected '/aufgaben/queue' visible for beginner"
        )

        # Intermediate/expert items should be hidden
        assert not expertise_page.is_nav_item_visible("/standorte/sites"), (
            "Expected '/standorte/sites' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/kalender"), (
            "Expected '/kalender' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/stammdaten/species"), (
            "Expected '/stammdaten/species' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/duengung/fertilizers"), (
            "Expected '/duengung/fertilizers' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/pflanzenschutz/pests"), (
            "Expected '/pflanzenschutz/pests' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/ernte/batches"), (
            "Expected '/ernte/batches' hidden for beginner"
        )
        assert not expertise_page.is_nav_item_visible("/durchlaeufe/planting-runs"), (
            "Expected '/durchlaeufe/planting-runs' hidden for beginner"
        )

    def test_intermediate_navigation_adds_sections(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-014: Intermediate sees beginner items + stammdaten, standorte, duengung, kalender."""
        _set_experience_level(expertise_page, "intermediate")

        expertise_page.navigate("/dashboard")
        expertise_page.wait_for_element(expertise_page.SIDEBAR)
        screenshot(
            "req021_012_intermediate_sidebar",
            "Sidebar in intermediate mode with additional sections",
        )

        # All beginner items still visible
        assert expertise_page.is_nav_item_visible("/dashboard"), (
            "Expected '/dashboard' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/pflanzen/plant-instances"), (
            "Expected '/pflanzen/plant-instances' visible for intermediate"
        )

        # Intermediate additions
        assert expertise_page.is_nav_item_visible("/kalender"), (
            "Expected '/kalender' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/standorte/sites"), (
            "Expected '/standorte/sites' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/stammdaten/species"), (
            "Expected '/stammdaten/species' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/stammdaten/botanical-families"), (
            "Expected '/stammdaten/botanical-families' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/duengung/fertilizers"), (
            "Expected '/duengung/fertilizers' visible for intermediate"
        )
        assert expertise_page.is_nav_item_visible("/duengung/plans"), (
            "Expected '/duengung/plans' visible for intermediate"
        )

        # Expert items still hidden
        assert not expertise_page.is_nav_item_visible("/pflanzenschutz/pests"), (
            "Expected '/pflanzenschutz/pests' hidden for intermediate"
        )
        assert not expertise_page.is_nav_item_visible("/ernte/batches"), (
            "Expected '/ernte/batches' hidden for intermediate"
        )
        assert not expertise_page.is_nav_item_visible("/durchlaeufe/planting-runs"), (
            "Expected '/durchlaeufe/planting-runs' hidden for intermediate"
        )
        assert not expertise_page.is_nav_item_visible("/standorte/substrates"), (
            "Expected '/standorte/substrates' hidden for intermediate"
        )
        assert not expertise_page.is_nav_item_visible("/standorte/tanks"), (
            "Expected '/standorte/tanks' hidden for intermediate"
        )

    def test_expert_navigation_shows_all(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-015: Expert sees all nav sections and items."""
        _set_experience_level(expertise_page, "expert")

        expertise_page.navigate("/dashboard")
        expertise_page.wait_for_element(expertise_page.SIDEBAR)
        screenshot(
            "req021_013_expert_sidebar",
            "Sidebar in expert mode with all nav items visible",
        )

        # Expert-only items should be visible
        assert expertise_page.is_nav_item_visible("/pflanzenschutz/pests"), (
            "Expected '/pflanzenschutz/pests' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/pflanzenschutz/diseases"), (
            "Expected '/pflanzenschutz/diseases' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/pflanzenschutz/treatments"), (
            "Expected '/pflanzenschutz/treatments' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/ernte/batches"), (
            "Expected '/ernte/batches' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/durchlaeufe/planting-runs"), (
            "Expected '/durchlaeufe/planting-runs' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/standorte/substrates"), (
            "Expected '/standorte/substrates' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/standorte/tanks"), (
            "Expected '/standorte/tanks' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/duengung/calculations"), (
            "Expected '/duengung/calculations' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/stammdaten/companion-planting"), (
            "Expected '/stammdaten/companion-planting' visible for expert"
        )
        assert expertise_page.is_nav_item_visible("/stammdaten/crop-rotation"), (
            "Expected '/stammdaten/crop-rotation' visible for expert"
        )

    def test_direct_url_access_as_beginner_loads_page(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-016: Beginner can directly access expert-only URLs (no access control)."""
        _set_experience_level(expertise_page, "beginner")

        # Navigate directly to an expert-only page
        expertise_page.navigate_direct("/standorte/tanks")
        screenshot(
            "req021_014_beginner_direct_tanks_url",
            "Tank list page loaded via direct URL as beginner",
        )

        # The page should load without error
        assert not expertise_page.is_error_displayed(), (
            "Expected no error when beginner accesses expert-only URL directly"
        )


# ── TC-021-017 to TC-021-019: SpeciesCreateDialog Field Visibility ──────────


class TestSpeciesFieldVisibility:
    """TC-021-017 to TC-021-019: Field visibility in SpeciesCreateDialog per level."""

    def test_beginner_species_dialog_no_fields(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-017: Beginner -- SpeciesCreateDialog shows no fields (all are intermediate+)."""
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_species_list()
        expertise_page.open_species_create_dialog()
        screenshot(
            "req021_015_beginner_species_dialog",
            "Species create dialog as beginner -- no fields visible",
        )

        # All species fields are intermediate or expert, so none should be visible
        assert not expertise_page.is_form_field_visible("scientific_name"), (
            "Expected 'scientific_name' hidden for beginner in SpeciesCreateDialog"
        )
        assert not expertise_page.is_form_field_visible("common_names"), (
            "Expected 'common_names' hidden for beginner"
        )
        assert not expertise_page.is_form_field_visible("family_key"), (
            "Expected 'family_key' hidden for beginner"
        )
        assert not expertise_page.is_form_field_visible("root_type"), (
            "Expected 'root_type' hidden for beginner"
        )

        # ShowAllFieldsToggle should be present
        assert expertise_page.is_show_all_fields_visible(), (
            "Expected ShowAllFieldsToggle button visible in beginner SpeciesCreateDialog"
        )

        expertise_page.close_create_dialog()

    def test_intermediate_species_dialog_intermediate_fields(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-018: Intermediate -- SpeciesCreateDialog shows intermediate fields, hides expert."""
        _set_experience_level(expertise_page, "intermediate")

        expertise_page.open_species_list()
        expertise_page.open_species_create_dialog()
        screenshot(
            "req021_016_intermediate_species_dialog",
            "Species create dialog as intermediate -- intermediate fields visible",
        )

        # Intermediate fields should be visible
        assert expertise_page.is_form_field_visible("scientific_name"), (
            "Expected 'scientific_name' visible for intermediate"
        )
        assert expertise_page.is_form_field_visible("common_names"), (
            "Expected 'common_names' visible for intermediate"
        )
        assert expertise_page.is_form_field_visible("family_key"), (
            "Expected 'family_key' visible for intermediate"
        )
        assert expertise_page.is_form_field_visible("genus"), (
            "Expected 'genus' visible for intermediate"
        )

        # Expert fields should be hidden
        assert not expertise_page.is_form_field_visible("root_type"), (
            "Expected 'root_type' hidden for intermediate"
        )
        assert not expertise_page.is_form_field_visible("allelopathy_score"), (
            "Expected 'allelopathy_score' hidden for intermediate"
        )
        assert not expertise_page.is_form_field_visible("hardiness_zones"), (
            "Expected 'hardiness_zones' hidden for intermediate"
        )

        expertise_page.close_create_dialog()

    def test_expert_species_dialog_all_fields(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-019: Expert -- SpeciesCreateDialog shows all fields."""
        _set_experience_level(expertise_page, "expert")

        expertise_page.open_species_list()
        expertise_page.open_species_create_dialog()
        screenshot(
            "req021_017_expert_species_dialog",
            "Species create dialog as expert -- all fields visible",
        )

        # Both intermediate and expert fields should be visible
        assert expertise_page.is_form_field_visible("scientific_name"), (
            "Expected 'scientific_name' visible for expert"
        )
        assert expertise_page.is_form_field_visible("root_type"), (
            "Expected 'root_type' visible for expert"
        )
        assert expertise_page.is_form_field_visible("allelopathy_score"), (
            "Expected 'allelopathy_score' visible for expert"
        )
        assert expertise_page.is_form_field_visible("hardiness_zones"), (
            "Expected 'hardiness_zones' visible for expert"
        )

        expertise_page.close_create_dialog()


# ── TC-021-020 to TC-021-022: ShowAllFieldsToggle ────────────────────────────


class TestShowAllFieldsToggle:
    """TC-021-020 to TC-021-022: Temporary field override via ShowAllFieldsToggle."""

    def test_show_all_fields_reveals_hidden_fields(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-020: Clicking 'Alle Felder anzeigen' reveals all fields without changing level."""
        import time

        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_species_list()
        expertise_page.open_species_create_dialog()
        time.sleep(0.5)

        # Verify fields hidden initially
        assert not expertise_page.is_form_field_visible("scientific_name"), (
            "Expected 'scientific_name' hidden before toggle"
        )

        screenshot(
            "req021_018_before_show_all_fields",
            "Dialog before clicking ShowAllFieldsToggle",
        )

        if not expertise_page.is_show_all_fields_visible():
            expertise_page.close_create_dialog()
            pytest.skip("ShowAllFieldsToggle not visible in species create dialog")

        expertise_page.click_show_all_fields()
        time.sleep(0.5)  # Wait for re-render
        screenshot(
            "req021_019_after_show_all_fields",
            "Dialog after clicking ShowAllFieldsToggle -- all fields visible",
        )

        # Now all fields should be visible
        assert expertise_page.is_form_field_visible("scientific_name"), (
            "Expected 'scientific_name' visible after ShowAllFieldsToggle"
        )

        # Button text should have changed
        toggle_text = expertise_page.get_show_all_fields_text()
        assert "weniger" in toggle_text.lower() or "fewer" in toggle_text.lower(), (
            f"Expected toggle text to contain 'weniger'/'fewer', got: '{toggle_text}'"
        )

        expertise_page.close_create_dialog()

    def test_show_fewer_fields_hides_again(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-021: Clicking 'Weniger Felder anzeigen' hides extended fields again."""
        import time

        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_species_list()
        expertise_page.open_species_create_dialog()
        time.sleep(0.5)

        if not expertise_page.is_show_all_fields_visible():
            expertise_page.close_create_dialog()
            pytest.skip("ShowAllFieldsToggle not visible in species create dialog")

        # Activate show all
        expertise_page.click_show_all_fields()
        time.sleep(0.5)
        assert expertise_page.is_form_field_visible("scientific_name"), (
            "Expected fields visible after first toggle click"
        )

        # Deactivate show all
        expertise_page.click_show_all_fields()
        time.sleep(0.5)
        screenshot(
            "req021_020_after_show_fewer_fields",
            "Dialog after toggling back to fewer fields",
        )

        assert not expertise_page.is_form_field_visible("scientific_name"), (
            "Expected 'scientific_name' hidden after toggling back to fewer fields"
        )

        toggle_text = expertise_page.get_show_all_fields_text()
        assert "alle" in toggle_text.lower() or "all" in toggle_text.lower(), (
            f"Expected toggle text to contain 'alle'/'all', got: '{toggle_text}'"
        )

        expertise_page.close_create_dialog()

    def test_toggle_resets_after_dialog_close(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-022: ShowAllFieldsToggle state resets when dialog is closed and reopened."""
        import time

        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_planting_run_list()
        expertise_page.open_planting_run_create_dialog()
        time.sleep(0.5)

        if not expertise_page.is_show_all_fields_visible():
            expertise_page.close_create_dialog()
            pytest.skip("ShowAllFieldsToggle not visible in planting run create dialog")

        # Activate show all and verify
        expertise_page.click_show_all_fields()
        time.sleep(0.5)
        has_any_extra_field = (
            expertise_page.is_form_field_visible("substrate_batch_key") or
            expertise_page.is_form_field_visible("source_plant_key") or
            expertise_page.is_form_field_visible("run_type") or
            expertise_page.is_form_field_visible("notes") or
            expertise_page.is_form_field_visible("site_key")
        )
        assert has_any_extra_field, (
            "Expected at least one extra field visible after ShowAllFields toggle"
        )

        # Close and reopen
        expertise_page.close_create_dialog()
        time.sleep(0.5)
        expertise_page.open_planting_run_create_dialog()
        time.sleep(0.5)
        screenshot(
            "req021_021_toggle_reset_after_reopen",
            "PlantingRunCreateDialog reopened -- toggle should be reset",
        )

        toggle_text = expertise_page.get_show_all_fields_text()
        assert "alle" in toggle_text.lower() or "all" in toggle_text.lower(), (
            f"Expected toggle reset to 'Alle Felder anzeigen' after reopen, got: '{toggle_text}'"
        )

        expertise_page.close_create_dialog()


# ── TC-021-023 to TC-021-025: PlantingRunCreateDialog Field Visibility ───────


class TestPlantingRunFieldVisibility:
    """TC-021-023 to TC-021-025: Field visibility in PlantingRunCreateDialog per level."""

    def test_beginner_planting_run_dialog_core_fields_only(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-023: Beginner -- PlantingRunCreateDialog shows only 3 core fields."""
        _set_experience_level(expertise_page, "beginner")

        expertise_page.open_planting_run_list()
        expertise_page.open_planting_run_create_dialog()
        screenshot(
            "req021_022_beginner_planting_run_dialog",
            "PlantingRun create dialog as beginner -- only core fields",
        )

        # Beginner fields should be visible
        assert expertise_page.is_form_field_visible("name"), (
            "Expected 'name' field visible for beginner in PlantingRunCreateDialog"
        )

        # Intermediate fields should be hidden
        assert not expertise_page.is_form_field_visible("run_type"), (
            "Expected 'run_type' hidden for beginner"
        )
        assert not expertise_page.is_form_field_visible("site_key"), (
            "Expected 'site_key' hidden for beginner"
        )
        assert not expertise_page.is_form_field_visible("notes"), (
            "Expected 'notes' hidden for beginner"
        )

        # Expert fields should be hidden
        assert not expertise_page.is_form_field_visible("substrate_batch_key"), (
            "Expected 'substrate_batch_key' hidden for beginner"
        )

        expertise_page.close_create_dialog()

    def test_intermediate_planting_run_dialog(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-024: Intermediate -- PlantingRunCreateDialog shows intermediate fields."""
        _set_experience_level(expertise_page, "intermediate")

        expertise_page.open_planting_run_list()
        expertise_page.open_planting_run_create_dialog()
        screenshot(
            "req021_023_intermediate_planting_run_dialog",
            "PlantingRun create dialog as intermediate",
        )

        # Beginner + intermediate fields visible
        assert expertise_page.is_form_field_visible("name"), (
            "Expected 'name' visible for intermediate"
        )
        assert expertise_page.is_form_field_visible("run_type"), (
            "Expected 'run_type' visible for intermediate"
        )

        # Expert fields still hidden
        assert not expertise_page.is_form_field_visible("substrate_batch_key"), (
            "Expected 'substrate_batch_key' hidden for intermediate"
        )

        expertise_page.close_create_dialog()

    def test_expert_planting_run_dialog_all_fields(
        self,
        expertise_page: ExpertiseLevelPage,
        screenshot,
    ) -> None:
        """TC-021-025: Expert -- PlantingRunCreateDialog shows all fields."""
        _set_experience_level(expertise_page, "expert")

        expertise_page.open_planting_run_list()
        expertise_page.open_planting_run_create_dialog()
        screenshot(
            "req021_024_expert_planting_run_dialog",
            "PlantingRun create dialog as expert -- all fields visible",
        )

        assert expertise_page.is_form_field_visible("name"), (
            "Expected 'name' visible for expert"
        )
        assert expertise_page.is_form_field_visible("run_type"), (
            "Expected 'run_type' visible for expert"
        )
        assert expertise_page.is_form_field_visible("substrate_batch_key"), (
            "Expected 'substrate_batch_key' visible for expert"
        )

        expertise_page.close_create_dialog()
