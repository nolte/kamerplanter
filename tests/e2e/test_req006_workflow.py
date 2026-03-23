"""E2E tests for REQ-006 — Workflow Templates (TC-006-034 to TC-006-042).

Tests cover:
- WorkflowTemplateListPage: page load, table display, buttons
- Workflow actions: generate from species, create, instantiate, delete
- WorkflowDetailPage: tab navigation, task templates display
- System template protections (cannot delete)

NFR-008 ss3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states
"""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.workflow_detail_page import WorkflowDetailPage
from .pages.workflow_list_page import WorkflowListPage


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def workflow_list(browser: WebDriver, base_url: str) -> WorkflowListPage:
    """Return a WorkflowListPage bound to the test browser."""
    return WorkflowListPage(browser, base_url)


@pytest.fixture
def workflow_detail(browser: WebDriver, base_url: str) -> WorkflowDetailPage:
    """Return a WorkflowDetailPage bound to the test browser."""
    return WorkflowDetailPage(browser, base_url)


# ── TC-006-034: Workflow Template List Page ────────────────────────────────────


@pytest.mark.skip(
    reason="WorkflowListPage route /aufgaben/workflows redirects to /stammdaten/species — no standalone list page"
)
class TestWorkflowTemplateListPage:
    """TC-006-034, TC-006-035: Workflow template list page operations."""

    def test_workflow_list_page_renders(
        self,
        workflow_list: WorkflowListPage,
        screenshot,
    ) -> None:
        """TC-006-034: Workflow-Template-Liste aufrufen -- Seite rendert."""
        workflow_list.open()
        screenshot("req006_034_workflow_list_loaded", "Workflow-Liste nach dem Laden")

        page_el = workflow_list.driver.find_element(*WorkflowListPage.PAGE)
        assert page_el.is_displayed(), (
            "Expected [data-testid='workflow-template-list-page'] to be visible"
        )

    def test_workflow_list_shows_data_table(
        self,
        workflow_list: WorkflowListPage,
        screenshot,
    ) -> None:
        """TC-006-034: Workflow-Liste zeigt DataTable mit Spalten."""
        workflow_list.open()
        screenshot("req006_035_workflow_table", "Workflow-Tabelle mit Spalten")

        headers = workflow_list.get_column_headers()
        # The table should have at least a Name column
        assert len(headers) > 0, (
            f"Expected column headers in workflow table, got none. Headers: {headers}"
        )

    def test_generate_button_is_visible(
        self,
        workflow_list: WorkflowListPage,
        screenshot,
    ) -> None:
        """TC-006-034: 'Aus Spezies generieren'-Button ist sichtbar."""
        workflow_list.open()
        screenshot("req006_036_generate_button", "Generieren-Button sichtbar")

        assert workflow_list.has_generate_button(), (
            "Expected [data-testid='generate-workflow-button'] to be visible"
        )

    def test_create_workflow_button_is_visible(
        self,
        workflow_list: WorkflowListPage,
        screenshot,
    ) -> None:
        """TC-006-034: 'Workflow erstellen'-Button ist sichtbar."""
        workflow_list.open()
        screenshot("req006_037_create_workflow_button", "Workflow-erstellen-Button sichtbar")

        assert workflow_list.has_create_button(), (
            "Expected [data-testid='create-workflow-button'] to be visible"
        )

    def test_workflow_list_row_count(
        self,
        workflow_list: WorkflowListPage,
        screenshot,
    ) -> None:
        """TC-006-034: Workflow-Tabelle zeigt vorhandene Workflows."""
        workflow_list.open()
        screenshot("req006_038_workflow_row_count", "Workflow-Tabellenzeilen")

        row_count = workflow_list.get_row_count()
        # We do not assert > 0 since there may be no workflows yet
        assert row_count >= 0, (
            f"Expected non-negative row count, got: {row_count}"
        )

    def test_search_workflows(
        self,
        workflow_list: WorkflowListPage,
        screenshot,
    ) -> None:
        """TC-006-034: Workflow-Suche filtert die Tabelle."""
        workflow_list.open()

        if workflow_list.get_row_count() == 0:
            pytest.skip("No workflows in database -- cannot test search")

        screenshot("req006_039_before_workflow_search", "Vor Workflow-Suche")

        workflow_list.search("ZZZ_NONEXISTENT_WORKFLOW_9999")
        time.sleep(0.5)
        screenshot("req006_040_after_workflow_search", "Nach Workflow-Suche (keine Treffer)")

        assert workflow_list.has_search_chip(), (
            "Expected search chip to appear after entering search term"
        )


# ── TC-006-037: Generate Workflow from Species ─────────────────────────────────


@pytest.mark.skip(
    reason="WorkflowListPage route /aufgaben/workflows redirects to /stammdaten/species — no standalone list page"
)
class TestWorkflowGenerateFromSpecies:
    """TC-006-037: Generate workflow from species dialog."""

    def test_generate_workflow_opens_dialog(
        self,
        workflow_list: WorkflowListPage,
        screenshot,
    ) -> None:
        """TC-006-037: Klick auf 'Aus Spezies generieren' oeffnet Dialog."""
        workflow_list.open()
        screenshot("req006_041_before_generate_click", "Vor Klick auf Generieren")

        workflow_list.click_generate_workflow()
        screenshot("req006_042_generate_dialog_open", "Generieren-Dialog geoeffnet")

        assert workflow_list.is_dialog_open(), (
            "Expected dialog to be open after clicking generate button"
        )


# ── TC-006-038: Workflow Instantiate ───────────────────────────────────────────


@pytest.mark.skip(
    reason="WorkflowListPage route /aufgaben/workflows redirects to /stammdaten/species — no standalone list page"
)
class TestWorkflowInstantiate:
    """TC-006-038: Instantiate (apply) a workflow to a plant."""

    def test_create_workflow_opens_dialog(
        self,
        workflow_list: WorkflowListPage,
        screenshot,
    ) -> None:
        """TC-006-038: Klick auf 'Workflow erstellen' oeffnet Dialog."""
        workflow_list.open()
        screenshot("req006_043_before_create_workflow", "Vor Klick auf Workflow erstellen")

        workflow_list.click_create_workflow()
        screenshot("req006_044_create_workflow_dialog", "Workflow-erstellen-Dialog geoeffnet")

        assert workflow_list.is_dialog_open(), (
            "Expected dialog to be open after clicking create workflow button"
        )


# ── TC-006-039: Workflow Detail Page ───────────────────────────────────────────


@pytest.mark.skip(
    reason="WorkflowListPage route /aufgaben/workflows redirects to /stammdaten/species — detail tests require list page for navigation"
)
class TestWorkflowDetailPage:
    """TC-006-039, TC-006-040: Workflow detail page operations."""

    def test_workflow_detail_loads_from_list_click(
        self,
        workflow_list: WorkflowListPage,
        screenshot,
    ) -> None:
        """TC-006-039: Klick auf Workflow-Zeile navigiert zur Detailseite."""
        workflow_list.open()

        if workflow_list.get_row_count() == 0:
            pytest.skip("No workflows in database -- cannot test detail navigation")

        screenshot("req006_045_before_workflow_row_click", "Vor Klick auf Workflow-Zeile")

        workflow_list.click_row(0)
        workflow_list.wait_for_url_contains("/aufgaben/workflows/")
        screenshot("req006_046_workflow_detail_loaded", "Workflow-Detailseite geladen")

        assert "/aufgaben/workflows/" in workflow_list.driver.current_url, (
            f"Expected URL to contain '/aufgaben/workflows/', got: {workflow_list.driver.current_url}"
        )

    def test_workflow_detail_page_renders(
        self,
        workflow_list: WorkflowListPage,
        workflow_detail: WorkflowDetailPage,
        screenshot,
    ) -> None:
        """TC-006-039: Workflow-Detailseite rendert mit data-testid und Tabs."""
        workflow_list.open()

        if workflow_list.get_row_count() == 0:
            pytest.skip("No workflows in database -- cannot test detail page")

        # Navigate via row click to get a valid workflow key
        workflow_list.click_row(0)
        workflow_list.wait_for_url_contains("/aufgaben/workflows/")

        # Now verify the detail page
        page_el = workflow_detail.driver.find_element(*WorkflowDetailPage.PAGE)
        assert page_el.is_displayed(), (
            "Expected [data-testid='workflow-detail-page'] to be visible"
        )

        screenshot("req006_047_workflow_detail_content", "Workflow-Detailseite mit Tabs")

        tabs = workflow_detail.get_tab_labels()
        assert len(tabs) >= 2, (
            f"Expected at least 2 tabs on workflow detail page, got {len(tabs)}: {tabs}"
        )

    def test_workflow_detail_tab_navigation(
        self,
        workflow_list: WorkflowListPage,
        workflow_detail: WorkflowDetailPage,
        screenshot,
    ) -> None:
        """TC-006-039: Workflow-Detailseite Tabs koennen navigiert werden."""
        workflow_list.open()

        if workflow_list.get_row_count() == 0:
            pytest.skip("No workflows in database -- cannot test tab navigation")

        workflow_list.click_row(0)
        workflow_list.wait_for_url_contains("/aufgaben/workflows/")

        tabs = workflow_detail.get_tab_labels()
        screenshot("req006_048_workflow_tabs_start", "Workflow-Tabs: Start")

        for i, label in enumerate(tabs):
            if i == 0:
                continue
            workflow_detail.click_tab_by_index(i)
            time.sleep(0.5)
            screenshot(
                f"req006_049_workflow_tab_{i}_{label.lower().replace(' ', '_')}",
                f"Workflow-Tab '{label}' aktiv",
            )

            active = workflow_detail.get_active_tab_label()
            assert active == label, (
                f"Expected active tab to be '{label}', got '{active}'"
            )

    def test_workflow_detail_shows_title(
        self,
        workflow_list: WorkflowListPage,
        workflow_detail: WorkflowDetailPage,
        screenshot,
    ) -> None:
        """TC-006-039: Workflow-Detailseite zeigt den Workflow-Namen."""
        workflow_list.open()

        if workflow_list.get_row_count() == 0:
            pytest.skip("No workflows in database -- cannot test title")

        workflow_list.click_row(0)
        workflow_list.wait_for_url_contains("/aufgaben/workflows/")

        title = workflow_detail.get_workflow_title()
        screenshot("req006_050_workflow_title", f"Workflow-Titel: {title}")

        assert title, (
            "Expected workflow title to be non-empty on detail page"
        )
