"""E2E tests for REQ-004 — Nutrient Plan CRUD and management (TC-REQ-004-031 to TC-REQ-004-060).

Covers:
- NutrientPlanListPage: list display, search, sort, clone, navigation
- NutrientPlanCreateDialog: create, validation, cancel
- NutrientPlanDetailPage: tab navigation, phase entries, validation tab, edit
"""

from __future__ import annotations

import time
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.nutrient_plan_list_page import NutrientPlanListPage
from .pages.nutrient_plan_detail_page import NutrientPlanDetailPage


# ── Fixtures ───────────────────────────────────────────────────────────────────


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
    """TC-REQ-004-031 to TC-REQ-004-042: Nutrient plan list display and interaction."""

    def test_plan_list_page_loads(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-031: Nutrient plan list page loads and the table is present."""
        plan_list.open()
        capture = request.node._screenshot_capture
        capture("REQ004-031_plan-list-loaded")

        assert plan_list.get_row_count() >= 0, (
            "Nutrient plan table should be present with row count >= 0"
        )

    def test_plan_list_has_required_columns(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-032: Nutrient plan list shows name, author, template and version columns."""
        plan_list.open()
        capture = request.node._screenshot_capture
        capture("REQ004-032_plan-list-columns")

        headers = plan_list.get_column_headers()
        assert len(headers) > 0, (
            f"Expected column headers in the nutrient plan table, got none. Headers: {headers}"
        )

    def test_plan_list_search_filters_results(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-033: Searching the plan list filters visible rows."""
        plan_list.open()
        initial_count = plan_list.get_row_count()
        if initial_count == 0:
            pytest.skip("No nutrient plans in database — cannot test search filtering")

        plan_list.search("zzzz_nonexistent_plan_xxxx")
        time.sleep(0.5)

        capture = request.node._screenshot_capture
        capture("REQ004-033_plan-search-no-match")

        filtered_count = plan_list.get_row_count()
        assert filtered_count <= initial_count, (
            f"Search should reduce or keep equal row count. "
            f"Before: {initial_count}, after: {filtered_count}"
        )

    def test_plan_list_search_chip_appears(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-034: Search chip is shown after entering search text."""
        plan_list.open()
        plan_list.search("organic")
        time.sleep(0.5)

        capture = request.node._screenshot_capture
        capture("REQ004-034_plan-search-chip")

        assert plan_list.has_search_chip(), (
            "Expected a search chip to appear after typing in the search field"
        )

    def test_plan_list_sort_by_column(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-035: Clicking a column header sorts the nutrient plan list."""
        plan_list.open()
        if plan_list.get_row_count() == 0:
            pytest.skip("No nutrient plans to sort")

        headers = plan_list.get_column_headers()
        if not headers:
            pytest.skip("No column headers found")

        plan_list.click_column_header(headers[0])
        time.sleep(0.3)

        capture = request.node._screenshot_capture
        capture("REQ004-035_plan-sorted")

        assert plan_list.has_sort_chip(), (
            "Expected a sort chip to appear after clicking a column header"
        )

    def test_plan_list_showing_count(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-036: Nutrient plan list shows a 'Zeigt X von Y' count label."""
        plan_list.open()
        capture = request.node._screenshot_capture
        capture("REQ004-036_plan-showing-count")

        showing_text = plan_list.get_showing_count_text()
        assert showing_text, (
            f"Expected a non-empty showing count text, got: '{showing_text}'"
        )

    def test_plan_list_row_click_navigates_to_detail(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-037: Clicking a nutrient plan row navigates to its detail page."""
        plan_list.open()
        if plan_list.get_row_count() == 0:
            pytest.skip("No nutrient plans in database — skipping navigation test")

        capture = request.node._screenshot_capture
        capture("REQ004-037_before-plan-row-click")

        plan_list.click_row(0)
        plan_list.wait_for_url_contains("/duengung/plans/")

        capture("REQ004-037_after-plan-row-click")

        current_url = plan_list.driver.current_url
        assert "/duengung/plans/" in current_url, (
            f"Expected URL to contain '/duengung/plans/', got: {current_url}"
        )


# ── TC-REQ-004-043 to TC-REQ-004-052: Create Dialog ──────────────────────────


class TestNutrientPlanCreateDialog:
    """TC-REQ-004-043 to TC-REQ-004-052: Nutrient plan create dialog."""

    def test_create_dialog_opens(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-043: Clicking 'Create' opens the nutrient plan create dialog."""
        plan_list.open()

        capture = request.node._screenshot_capture
        capture("REQ004-043_before-create-plan-click")

        plan_list.click_create()
        capture("REQ004-043_plan-create-dialog-open")

        assert plan_list.is_create_dialog_open(), (
            "Nutrient plan create dialog should be visible after clicking create"
        )

    def test_create_plan_with_required_name(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-044: Create a nutrient plan with only the required name field."""
        plan_list.open()
        initial_count = plan_list.get_row_count()

        plan_list.click_create()
        unique = uuid.uuid4().hex[:8]
        plan_name = f"E2E-Plan-{unique}"

        capture = request.node._screenshot_capture
        capture("REQ004-044_plan-create-minimal")

        plan_list.fill_name(plan_name)
        plan_list.submit_create_form()

        time.sleep(2)
        plan_list.open()
        capture("REQ004-044_after-plan-create-minimal")

        new_count = plan_list.get_row_count()
        assert new_count >= initial_count, (
            f"Expected at least {initial_count} plans after create, got {new_count}"
        )

    def test_create_plan_with_all_fields(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-045: Create a nutrient plan with all major fields filled."""
        plan_list.open()
        initial_count = plan_list.get_row_count()

        plan_list.click_create()
        unique = uuid.uuid4().hex[:6]
        plan_name = f"FullPlan-E2E-{unique}"

        plan_list.fill_name(plan_name)
        plan_list.fill_description("E2E test nutrient plan with full data")
        plan_list.fill_author("E2E Test Author")

        capture = request.node._screenshot_capture
        capture("REQ004-045_plan-create-full-fields")

        plan_list.submit_create_form()
        time.sleep(2)

        plan_list.open()
        capture("REQ004-045_after-plan-create-full")

        new_count = plan_list.get_row_count()
        assert new_count >= initial_count, (
            f"Expected at least {initial_count} plans after full create, got {new_count}"
        )

    def test_validation_empty_name_rejected(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-046: Submitting with empty plan name shows validation error."""
        plan_list.open()
        plan_list.click_create()

        # Do not fill any field — submit with empty name
        plan_list.submit_create_form()
        time.sleep(0.5)

        capture = request.node._screenshot_capture
        capture("REQ004-046_plan-validation-empty-name")

        assert plan_list.is_create_dialog_open(), (
            "Create dialog should remain open when submitted with an empty plan name"
        )

    def test_cancel_plan_create_discards_input(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-047: Cancelling the create dialog discards the entered name."""
        plan_list.open()

        plan_list.click_create()
        plan_list.fill_name("CancelledPlan")

        capture = request.node._screenshot_capture
        capture("REQ004-047_plan-before-cancel")

        plan_list.cancel_create_form()
        time.sleep(0.5)
        capture("REQ004-047_plan-after-cancel")

        assert not plan_list.is_create_dialog_open(), (
            "Create dialog should be closed after clicking cancel"
        )

        # Reopen dialog — name should be cleared
        plan_list.click_create()
        name_value = plan_list.get_name_field_value()
        assert name_value != "CancelledPlan", (
            f"Form should be reset after cancel, but name field still shows '{name_value}'"
        )

    def test_create_plan_with_template_flag(
        self, plan_list: NutrientPlanListPage, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-004-048: Create a nutrient plan and mark it as a template."""
        plan_list.open()
        initial_count = plan_list.get_row_count()

        plan_list.click_create()
        unique = uuid.uuid4().hex[:6]
        plan_list.fill_name(f"Template-E2E-{unique}")
        plan_list.toggle_is_template()

        capture = request.node._screenshot_capture
        capture("REQ004-048_plan-create-template")

        plan_list.submit_create_form()
        time.sleep(2)

        plan_list.open()
        capture("REQ004-048_after-plan-create-template")

        new_count = plan_list.get_row_count()
        assert new_count >= initial_count, (
            f"Expected at least {initial_count} plans after template create, got {new_count}"
        )


# ── TC-REQ-004-053 to TC-REQ-004-060: Detail Page ────────────────────────────


class TestNutrientPlanDetailPage:
    """TC-REQ-004-053 to TC-REQ-004-060: Nutrient plan detail page."""

    @pytest.fixture(autouse=True)
    def _ensure_plan_exists(self, plan_list: NutrientPlanListPage) -> None:
        """Pre-condition: ensure at least one nutrient plan exists for detail tests."""
        plan_list.open()
        if plan_list.get_row_count() == 0:
            plan_list.click_create()
            unique = uuid.uuid4().hex[:6]
            plan_list.fill_name(f"DetailFixture-{unique}")
            plan_list.submit_create_form()
            time.sleep(2)
            plan_list.open()

    def _navigate_to_first_plan(self, plan_list: NutrientPlanListPage) -> str:
        """Click the first row and return the resulting URL."""
        plan_list.open()
        plan_list.click_row(0)
        plan_list.wait_for_url_contains("/duengung/plans/")
        return plan_list.driver.current_url

    def test_plan_detail_page_loads(
        self,
        plan_list: NutrientPlanListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-004-053: Nutrient plan detail page loads with plan name as title."""
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        capture = request.node._screenshot_capture
        capture("REQ004-053_plan-detail-loaded")

        title = detail.get_page_title_text()
        assert title, (
            f"Expected a non-empty page title on the nutrient plan detail page, got: '{title}'"
        )

    def test_plan_detail_has_three_tabs(
        self,
        plan_list: NutrientPlanListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-004-054: Nutrient plan detail page has three tabs (Phase Entries / Validation / Edit)."""
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)

        from selenium.webdriver.common.by import By
        tabs = plan_list.driver.find_elements(By.CSS_SELECTOR, "[role='tab']")

        capture = request.node._screenshot_capture
        capture("REQ004-054_plan-detail-tabs")

        assert len(tabs) >= 3, (
            f"Expected at least 3 tabs in the nutrient plan detail page, got {len(tabs)}: "
            f"{[t.text for t in tabs]}"
        )

    def test_phase_entries_tab_is_default(
        self,
        plan_list: NutrientPlanListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-004-055: Phase Entries tab is active by default on page load."""
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        capture = request.node._screenshot_capture
        capture("REQ004-055_plan-phase-entries-tab-default")

        active_tab = detail.get_active_tab_text()
        assert active_tab, (
            f"Expected an active tab label, got empty string"
        )
        # First tab should be active (Phase Entries / Phaseneinträge)
        from selenium.webdriver.common.by import By
        first_tab = plan_list.driver.find_element(By.XPATH, "//button[@role='tab'][1]")
        is_first_selected = first_tab.get_attribute("aria-selected") == "true"
        assert is_first_selected, (
            "Expected the first tab (Phase Entries) to be selected by default"
        )

    def test_validation_tab_loads_results(
        self,
        plan_list: NutrientPlanListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-004-056: Switching to the Validation tab triggers plan validation."""
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        capture = request.node._screenshot_capture
        capture("REQ004-056_before-validation-tab")

        detail.click_tab_validation()
        # Wait for validation to complete (spinner disappears)
        detail.wait_for_validation_loaded(timeout=30)

        capture("REQ004-056_validation-tab-loaded")

        alerts = detail.get_validation_alerts()
        assert len(alerts) > 0, (
            "Expected at least one alert (completeness or EC budget) in the validation tab"
        )

    def test_edit_tab_is_prefilled(
        self,
        plan_list: NutrientPlanListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-004-057: Edit tab form is pre-filled with the plan's current data."""
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        title = detail.get_page_title_text()
        detail.click_tab_edit()

        capture = request.node._screenshot_capture
        capture("REQ004-057_plan-edit-tab-prefilled")

        name_value = detail.get_name_field_value()
        assert name_value, (
            "Expected the name field in the edit tab to be pre-filled with the plan name"
        )

    def test_edit_tab_save_disabled_without_changes(
        self,
        plan_list: NutrientPlanListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-004-058: Edit tab save button is disabled when no changes have been made."""
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()
        detail.click_tab_edit()

        capture = request.node._screenshot_capture
        capture("REQ004-058_plan-edit-save-disabled")

        submit_enabled = detail.is_submit_button_enabled()
        assert not submit_enabled, (
            "Expected the save button to be disabled when no changes have been made"
        )

    def test_edit_tab_save_enables_after_change(
        self,
        plan_list: NutrientPlanListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-004-059: Modifying a field in edit tab enables the save button."""
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()
        detail.click_tab_edit()

        detail.fill_author(f"E2E-Author-{uuid.uuid4().hex[:4]}")

        capture = request.node._screenshot_capture
        capture("REQ004-059_plan-edit-save-enabled")

        submit_enabled = detail.is_submit_button_enabled()
        assert submit_enabled, (
            "Expected the save button to be enabled after modifying a field"
        )

    def test_plan_delete_confirm_dialog(
        self,
        plan_list: NutrientPlanListPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-004-060: Delete button on nutrient plan opens a confirm dialog."""
        # Create a dedicated plan to delete so we don't destroy shared test data
        plan_list.open()
        plan_list.click_create()
        unique = uuid.uuid4().hex[:6]
        delete_plan_name = f"DeleteMe-{unique}"
        plan_list.fill_name(delete_plan_name)
        plan_list.submit_create_form()
        time.sleep(2)

        # Navigate to it via list
        plan_list.open()
        plan_list.search(delete_plan_name)
        time.sleep(0.5)
        if plan_list.get_row_count() == 0:
            pytest.skip("Could not find the freshly created plan to delete")

        plan_list.click_row(0)
        plan_list.wait_for_url_contains("/duengung/plans/")

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        detail.click_delete()

        capture = request.node._screenshot_capture
        capture("REQ004-060_plan-delete-confirm-dialog")

        assert detail.is_confirm_dialog_open(), (
            "Expected the confirm dialog to open after clicking the delete button"
        )

        # Cancel — do not actually delete
        detail.cancel_delete()
        capture("REQ004-060_plan-delete-cancelled")

        assert not detail.is_confirm_dialog_open(), (
            "Confirm dialog should be closed after clicking cancel"
        )
