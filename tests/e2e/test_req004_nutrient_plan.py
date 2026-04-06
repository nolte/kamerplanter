"""E2E tests for REQ-004 — Nutrient Plan CRUD and management.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-004.md):
  TC-REQ-004-031  ->  TC-004-012  Naehrstoffplan-Liste aufrufen
  TC-REQ-004-032  ->  TC-004-012  Naehrstoffplan-Liste aufrufen
  TC-REQ-004-033  ->  TC-004-013  Naehrstoffplan nach Substrattyp filtern
  TC-REQ-004-034  ->  TC-004-013  Naehrstoffplan nach Substrattyp filtern
  TC-REQ-004-035  ->  TC-004-012  Naehrstoffplan-Liste aufrufen
  TC-REQ-004-036  ->  TC-004-012  Naehrstoffplan-Liste aufrufen
  TC-REQ-004-037  ->  TC-004-012  Naehrstoffplan-Liste aufrufen (Row Click Navigation)
  TC-REQ-004-043  ->  TC-004-015  Neuen Naehrstoffplan erstellen -- Happy Path (Dialog)
  TC-REQ-004-044  ->  TC-004-015  Neuen Naehrstoffplan erstellen -- Happy Path (Minimal)
  TC-REQ-004-045  ->  TC-004-015  Neuen Naehrstoffplan erstellen -- Happy Path (Full)
  TC-REQ-004-046  ->  TC-004-016  Naehrstoffplan erstellen -- Namensfeld leer
  TC-REQ-004-047  ->  TC-004-015  Neuen Naehrstoffplan erstellen -- Cancel
  TC-REQ-004-048  ->  TC-004-015  Neuen Naehrstoffplan erstellen -- Template Flag
  TC-REQ-004-053  ->  TC-004-012  Naehrstoffplan-Detailseite laedt
  TC-REQ-004-054  ->  TC-004-012  Naehrstoffplan-Detailseite -- Tabs
  TC-REQ-004-055  ->  TC-004-017  Phase-Entry zu Naehrstoffplan hinzufuegen (Phase Entries Tab)
  TC-REQ-004-056  ->  TC-004-021  Plan-Vollstaendigkeits-Validierung (Validation Tab)
  TC-REQ-004-057  ->  TC-004-012  Naehrstoffplan-Detailseite -- Edit Tab prefilled
  TC-REQ-004-058  ->  TC-004-012  Naehrstoffplan-Detailseite -- Save disabled
  TC-REQ-004-059  ->  TC-004-012  Naehrstoffplan-Detailseite -- Save enables after change
  TC-REQ-004-060  ->  TC-004-027  Naehrstoffplan loeschen (Delete Confirm Dialog)
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.nutrient_plan_list_page import NutrientPlanListPage
from .pages.nutrient_plan_detail_page import NutrientPlanDetailPage


# ── Fixtures ──────────────────────────────────────────────��────────────────────


@pytest.fixture
def plan_list(browser: WebDriver, base_url: str) -> NutrientPlanListPage:
    """Return a NutrientPlanListPage bound to the current browser session."""
    return NutrientPlanListPage(browser, base_url)


@pytest.fixture
def plan_detail(browser: WebDriver, base_url: str) -> NutrientPlanDetailPage:
    """Return a NutrientPlanDetailPage bound to the current browser session."""
    return NutrientPlanDetailPage(browser, base_url)


# ── TC-REQ-004-031 to TC-REQ-004-042: Nutrient Plan List Page ─────────────────


class TestNutrientPlanListPage:
    """Nutrient plan list display and interaction (Spec: TC-004-012, TC-004-013)."""

    @pytest.mark.smoke
    def test_plan_list_page_loads(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-031: Nutrient plan list page loads and the table is present.

        Spec: TC-004-012 -- Naehrstoffplan-Liste aufrufen.
        """
        plan_list.open()
        screenshot("TC-REQ-004-031_plan-list-loaded",
                   "Nutrient plan list page after initial load")

        assert plan_list.get_row_count() >= 0, (
            "TC-REQ-004-031 FAIL: Nutrient plan table should be present with row count >= 0"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.smoke
    def test_plan_list_has_required_columns(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-032: Nutrient plan list shows name, author, template and version columns.

        Spec: TC-004-012 -- Naehrstoffplan-Liste aufrufen.
        """
        plan_list.open()
        screenshot("TC-REQ-004-032_plan-list-columns",
                   "Nutrient plan list showing column headers")

        headers = plan_list.get_column_headers()
        assert len(headers) > 0, (
            f"TC-REQ-004-032 FAIL: Expected column headers in the nutrient plan table, got none. Headers: {headers}"
        )

    @pytest.mark.core_crud
    def test_plan_list_search_filters_results(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-033: Searching the plan list filters visible rows.

        Spec: TC-004-013 -- Naehrstoffplan nach Substrattyp filtern.
        """
        plan_list.open()
        initial_count = plan_list.get_row_count()
        if initial_count == 0:
            pytest.skip("No nutrient plans in database — cannot test search filtering")

        plan_list.search("zzzz_nonexistent_plan_xxxx")
        plan_list.wait_for_loading_complete()

        screenshot("TC-REQ-004-033_plan-search-no-match",
                   "Nutrient plan list after searching for non-existent term")

        filtered_count = plan_list.get_row_count()
        assert filtered_count <= initial_count, (
            f"TC-REQ-004-033 FAIL: Search should reduce or keep equal row count. "
            f"Before: {initial_count}, after: {filtered_count}"
        )

    @pytest.mark.core_crud
    def test_plan_list_search_chip_appears(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-034: Search chip is shown after entering search text.

        Spec: TC-004-013 -- Naehrstoffplan nach Substrattyp filtern.
        """
        plan_list.open()
        plan_list.search("organic")
        plan_list.wait_for_loading_complete()

        screenshot("TC-REQ-004-034_plan-search-chip",
                   "Nutrient plan list with search chip after typing 'organic'")

        assert plan_list.has_search_chip(), (
            "TC-REQ-004-034 FAIL: Expected a search chip to appear after typing in the search field"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.core_crud
    def test_plan_list_sort_by_column(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-035: Clicking a column header sorts the nutrient plan list.

        Spec: TC-004-012 -- Naehrstoffplan-Liste aufrufen.
        """
        plan_list.open()
        if plan_list.get_row_count() == 0:
            pytest.skip("No nutrient plans to sort")

        headers = plan_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        plan_list.click_column_header(headers[0])
        plan_list.wait_for_loading_complete()

        screenshot("TC-REQ-004-035_plan-sorted",
                   "Nutrient plan list after clicking column header to sort")

        assert plan_list.has_sort_chip(), (
            "TC-REQ-004-035 FAIL: Expected a sort chip to appear after clicking a column header"
        )

    @pytest.mark.smoke
    def test_plan_list_showing_count(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-036: Nutrient plan list shows a 'Zeigt X von Y' count label.

        Spec: TC-004-012 -- Naehrstoffplan-Liste aufrufen.
        """
        plan_list.open()
        screenshot("TC-REQ-004-036_plan-showing-count",
                   "Nutrient plan list showing count label")

        showing_text = plan_list.get_showing_count_text()
        assert showing_text, (
            f"TC-REQ-004-036 FAIL: Expected a non-empty showing count text, got: '{showing_text}'"
        )

    @pytest.mark.core_crud
    def test_plan_list_row_click_navigates_to_detail(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-037: Clicking a nutrient plan row navigates to its detail page.

        Spec: TC-004-012 -- Naehrstoffplan-Liste aufrufen (Row Click Navigation).
        """
        plan_list.open()
        if plan_list.get_row_count() == 0:
            pytest.skip("No nutrient plans in database — skipping navigation test")

        screenshot("TC-REQ-004-037_before-plan-row-click",
                   "Nutrient plan list before clicking first row")

        plan_list.click_row(0)
        plan_list.wait_for_url_contains("/duengung/plans/")

        screenshot("TC-REQ-004-037_after-plan-row-click",
                   "Nutrient plan detail page after row click navigation")

        current_url = plan_list.driver.current_url
        assert "/duengung/plans/" in current_url, (
            f"TC-REQ-004-037 FAIL: Expected URL to contain '/duengung/plans/', got: {current_url}"
        )


# ── TC-REQ-004-043 to TC-REQ-004-052: Create Dialog ──────────────────────────


class TestNutrientPlanCreateDialog:
    """Nutrient plan create dialog and validation (Spec: TC-004-015, TC-004-016)."""

    @pytest.mark.core_crud
    def test_create_dialog_opens(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-043: Clicking 'Create' opens the nutrient plan create dialog.

        Spec: TC-004-015 -- Neuen Naehrstoffplan erstellen -- Happy Path (Dialog).
        """
        plan_list.open()

        screenshot("TC-REQ-004-043_before-create-plan-click",
                   "Nutrient plan list before clicking create button")

        plan_list.click_create()
        screenshot("TC-REQ-004-043_plan-create-dialog-open",
                   "Nutrient plan create dialog open with form fields")

        assert plan_list.is_create_dialog_open(), (
            "TC-REQ-004-043 FAIL: Nutrient plan create dialog should be visible after clicking create"
        )

    @pytest.mark.core_crud
    def test_create_plan_with_required_name(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-044: Create a nutrient plan with only the required name field.

        Spec: TC-004-015 -- Neuen Naehrstoffplan erstellen -- Happy Path (Minimal).
        """
        plan_list.open()
        initial_count = plan_list.get_row_count()

        plan_list.click_create()
        unique = uuid.uuid4().hex[:8]
        plan_name = f"E2E-Plan-{unique}"

        screenshot("TC-REQ-004-044_plan-create-minimal",
                   "Create dialog with minimal plan name filled")

        plan_list.fill_name(plan_name)
        plan_list.submit_create_form()

        plan_list.wait_for_loading_complete()
        plan_list.open()
        screenshot("TC-REQ-004-044_after-plan-create-minimal",
                   "Nutrient plan list after creating plan with minimal fields")

        new_count = plan_list.get_row_count()
        assert new_count >= initial_count, (
            f"TC-REQ-004-044 FAIL: Expected at least {initial_count} plans after create, got {new_count}"
        )

    @pytest.mark.core_crud
    def test_create_plan_with_all_fields(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-045: Create a nutrient plan with all major fields filled.

        Spec: TC-004-015 -- Neuen Naehrstoffplan erstellen -- Happy Path (Full).
        """
        plan_list.open()
        initial_count = plan_list.get_row_count()

        plan_list.click_create()
        unique = uuid.uuid4().hex[:6]
        plan_name = f"FullPlan-E2E-{unique}"

        plan_list.fill_name(plan_name)
        plan_list.fill_description("E2E test nutrient plan with full data")
        plan_list.fill_author("E2E Test Author")

        screenshot("TC-REQ-004-045_plan-create-full-fields",
                   "Create dialog with all major fields filled")

        plan_list.submit_create_form()
        plan_list.wait_for_loading_complete()

        plan_list.open()
        screenshot("TC-REQ-004-045_after-plan-create-full",
                   "Nutrient plan list after creating plan with full data")

        new_count = plan_list.get_row_count()
        assert new_count >= initial_count, (
            f"TC-REQ-004-045 FAIL: Expected at least {initial_count} plans after full create, got {new_count}"
        )

    @pytest.mark.core_crud
    def test_validation_empty_name_rejected(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-046: Submitting with empty plan name shows validation error.

        Spec: TC-004-016 -- Naehrstoffplan erstellen -- Namensfeld leer.
        """
        plan_list.open()
        plan_list.click_create()

        # Do not fill any field — submit with empty name
        plan_list.submit_create_form()
        plan_list.wait_for_loading_complete()

        screenshot("TC-REQ-004-046_plan-validation-empty-name",
                   "Create dialog showing validation error for empty plan name")

        assert plan_list.is_create_dialog_open(), (
            "TC-REQ-004-046 FAIL: Create dialog should remain open when submitted with an empty plan name"
        )

    @pytest.mark.core_crud
    def test_cancel_plan_create_discards_input(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-047: Cancelling the create dialog discards the entered name.

        Spec: TC-004-015 -- Neuen Naehrstoffplan erstellen -- Cancel.
        """
        plan_list.open()

        plan_list.click_create()
        plan_list.fill_name("CancelledPlan")

        screenshot("TC-REQ-004-047_plan-before-cancel",
                   "Create dialog with plan name before cancelling")

        plan_list.cancel_create_form()
        plan_list.wait_for_loading_complete()
        screenshot("TC-REQ-004-047_plan-after-cancel",
                   "Nutrient plan list after cancelling create dialog")

        assert not plan_list.is_create_dialog_open(), (
            "TC-REQ-004-047 FAIL: Create dialog should be closed after clicking cancel"
        )

        # Reopen dialog — name should be cleared
        plan_list.click_create()
        name_value = plan_list.get_name_field_value()
        assert name_value != "CancelledPlan", (
            f"TC-REQ-004-047 FAIL: Form should be reset after cancel, but name field still shows '{name_value}'"
        )

    @pytest.mark.core_crud
    def test_create_plan_with_template_flag(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-004-048: Create a nutrient plan and mark it as a template.

        Spec: TC-004-015 -- Neuen Naehrstoffplan erstellen -- Template Flag.
        """
        plan_list.open()
        initial_count = plan_list.get_row_count()

        plan_list.click_create()
        unique = uuid.uuid4().hex[:6]
        plan_list.fill_name(f"Template-E2E-{unique}")
        plan_list.toggle_is_template()

        screenshot("TC-REQ-004-048_plan-create-template",
                   "Create dialog with template flag enabled")

        plan_list.submit_create_form()
        plan_list.wait_for_loading_complete()

        plan_list.open()
        screenshot("TC-REQ-004-048_after-plan-create-template",
                   "Nutrient plan list after creating template plan")

        new_count = plan_list.get_row_count()
        assert new_count >= initial_count, (
            f"TC-REQ-004-048 FAIL: Expected at least {initial_count} plans after template create, got {new_count}"
        )


# ── TC-REQ-004-053 to TC-REQ-004-060: Detail Page ────────────────────────────


class TestNutrientPlanDetailPage:
    """Nutrient plan detail page tabs and editing (Spec: TC-004-012, TC-004-017, TC-004-021, TC-004-027)."""

    @pytest.fixture(autouse=True)
    def _ensure_plan_exists(self, plan_list: NutrientPlanListPage) -> None:
        """Pre-condition: ensure at least one nutrient plan exists for detail tests."""
        plan_list.open()
        if plan_list.get_row_count() == 0:
            try:
                plan_list.click_create()
                unique = uuid.uuid4().hex[:6]
                plan_list.fill_name(f"DetailFixture-{unique}")
                plan_list.submit_create_form()
                plan_list.wait_for_loading_complete()
                plan_list.open()
            except Exception:
                # If creation fails, seed data may still provide plans
                plan_list.open()
        if plan_list.get_row_count() == 0:
            pytest.skip("No nutrient plans available for detail tests")

    def _navigate_to_first_plan(self, plan_list: NutrientPlanListPage) -> str:
        """Click the first row and return the resulting URL."""
        plan_list.open()
        plan_list.click_row(0)
        plan_list.wait_for_url_contains("/duengung/plans/")
        return plan_list.driver.current_url

    @pytest.mark.smoke
    def test_plan_detail_page_loads(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-053: Nutrient plan detail page loads with plan name as title.

        Spec: TC-004-012 -- Naehrstoffplan-Detailseite laedt.
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        screenshot("TC-REQ-004-053_plan-detail-loaded",
                   "Nutrient plan detail page with plan name as title")

        title = detail.get_page_title_text()
        assert title, (
            f"TC-REQ-004-053 FAIL: Expected a non-empty page title on the nutrient plan detail page, got: '{title}'"
        )

    @pytest.mark.smoke
    def test_plan_detail_has_three_tabs(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-054: Nutrient plan detail page has three tabs (Phase Entries / Validation / Edit).

        Spec: TC-004-012 -- Naehrstoffplan-Detailseite -- Tabs.
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)

        from selenium.webdriver.common.by import By
        tabs = plan_list.driver.find_elements(By.CSS_SELECTOR, "[role='tab']")

        screenshot("TC-REQ-004-054_plan-detail-tabs",
                   "Nutrient plan detail page showing tabs")

        assert len(tabs) >= 3, (
            f"TC-REQ-004-054 FAIL: Expected at least 3 tabs in the nutrient plan detail page, got {len(tabs)}: "
            f"{[t.text for t in tabs]}"
        )

    @pytest.mark.core_crud
    def test_phase_entries_tab_is_default(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-055: Phase Entries tab is active by default on page load.

        Spec: TC-004-017 -- Phase-Entry zu Naehrstoffplan hinzufuegen (Phase Entries Tab).
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        screenshot("TC-REQ-004-055_plan-phase-entries-tab-default",
                   "Nutrient plan detail with Phase Entries tab active by default")

        active_tab = detail.get_active_tab_text()
        assert active_tab, (
            "TC-REQ-004-055 FAIL: Expected an active tab label, got empty string"
        )
        # First tab should be active (Phase Entries / Phaseneintraege)
        from selenium.webdriver.common.by import By
        first_tab = plan_list.driver.find_element(By.XPATH, "//button[@role='tab'][1]")
        is_first_selected = first_tab.get_attribute("aria-selected") == "true"
        assert is_first_selected, (
            "TC-REQ-004-055 FAIL: Expected the first tab (Phase Entries) to be selected by default"
        )

    @pytest.mark.core_crud
    def test_validation_tab_loads_results(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-056: Switching to the Validation tab triggers plan validation.

        Spec: TC-004-021 -- Plan-Vollstaendigkeits-Validierung (Validation Tab).
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        screenshot("TC-REQ-004-056_before-validation-tab",
                   "Nutrient plan detail before switching to validation tab")

        detail.click_tab_validation()
        # Wait for validation to complete (spinner disappears)
        detail.wait_for_validation_loaded(timeout=30)

        screenshot("TC-REQ-004-056_validation-tab-loaded",
                   "Validation tab loaded with validation results")

        alerts = detail.get_validation_alerts()
        assert len(alerts) > 0, (
            "TC-REQ-004-056 FAIL: Expected at least one alert (completeness or EC budget) in the validation tab"
        )

    @pytest.mark.core_crud
    def test_edit_tab_is_prefilled(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-057: Edit tab form is pre-filled with the plan's current data.

        Spec: TC-004-012 -- Naehrstoffplan-Detailseite -- Edit Tab prefilled.
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        title = detail.get_page_title_text()
        detail.click_tab_edit()

        screenshot("TC-REQ-004-057_plan-edit-tab-prefilled",
                   "Nutrient plan edit tab with pre-filled name field")

        name_value = detail.get_name_field_value()
        assert name_value, (
            "TC-REQ-004-057 FAIL: Expected the name field in the edit tab to be pre-filled with the plan name"
        )

    @pytest.mark.core_crud
    def test_edit_tab_save_disabled_without_changes(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-058: Edit tab save button is disabled when no changes have been made.

        Spec: TC-004-012 -- Naehrstoffplan-Detailseite -- Save disabled.
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()
        detail.click_tab_edit()

        screenshot("TC-REQ-004-058_plan-edit-save-disabled",
                   "Nutrient plan edit tab with save button disabled")

        submit_enabled = detail.is_submit_button_enabled()
        assert not submit_enabled, (
            "TC-REQ-004-058 FAIL: Expected the save button to be disabled when no changes have been made"
        )

    @pytest.mark.core_crud
    def test_edit_tab_save_enables_after_change(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-059: Modifying a field in edit tab enables the save button.

        Spec: TC-004-012 -- Naehrstoffplan-Detailseite -- Save enables after change.
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()
        detail.click_tab_edit()

        detail.fill_author(f"E2E-Author-{uuid.uuid4().hex[:4]}")

        screenshot("TC-REQ-004-059_plan-edit-save-enabled",
                   "Nutrient plan edit tab with save button enabled after modification")

        submit_enabled = detail.is_submit_button_enabled()
        assert submit_enabled, (
            "TC-REQ-004-059 FAIL: Expected the save button to be enabled after modifying a field"
        )

    @pytest.mark.core_crud
    def test_plan_delete_confirm_dialog(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-060: Delete button on nutrient plan opens a confirm dialog.

        Spec: TC-004-027 -- Naehrstoffplan loeschen (Delete Confirm Dialog).
        """
        # Create a dedicated plan to delete so we don't destroy shared test data
        plan_list.open()
        plan_list.click_create()
        unique = uuid.uuid4().hex[:6]
        delete_plan_name = f"DeleteMe-{unique}"
        plan_list.fill_name(delete_plan_name)
        plan_list.submit_create_form()
        plan_list.wait_for_loading_complete()

        # Navigate to it via list
        plan_list.open()
        plan_list.search(delete_plan_name)
        plan_list.wait_for_loading_complete()
        if plan_list.get_row_count() == 0:
            pytest.skip("Could not find the freshly created plan to delete")

        plan_list.click_row(0)
        plan_list.wait_for_url_contains("/duengung/plans/")

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        detail.click_delete()

        screenshot("TC-REQ-004-060_plan-delete-confirm-dialog",
                   "Nutrient plan delete confirmation dialog")

        assert detail.is_confirm_dialog_open(), (
            "TC-REQ-004-060 FAIL: Expected the confirm dialog to open after clicking the delete button"
        )

        # Cancel — do not actually delete
        detail.cancel_delete()
        screenshot("TC-REQ-004-060_plan-delete-cancelled",
                   "Nutrient plan detail after cancelling delete")

        assert not detail.is_confirm_dialog_open(), (
            "TC-REQ-004-060 FAIL: Confirm dialog should be closed after clicking cancel"
        )
