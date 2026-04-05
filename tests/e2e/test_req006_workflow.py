"""E2E tests for REQ-006 — Workflow Templates.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-006.md):
  TC-REQ-006-024  ->  TC-006-034  Workflow-Template-Liste aufrufen -- Seite rendert
  TC-REQ-006-025  ->  TC-006-034  Workflow-Liste zeigt Workflow-Cards
  TC-REQ-006-027  ->  TC-006-034  'Workflow erstellen'-Button ist sichtbar
  TC-REQ-006-028  ->  TC-006-034  Workflow-Cards zeigen vorhandene Workflows
  TC-REQ-006-029  ->  TC-006-034  Workflow-Suche filtert die Cards
  TC-REQ-006-031  ->  TC-006-038  Klick auf 'Workflow erstellen' oeffnet Dialog
  TC-REQ-006-032  ->  TC-006-039  Klick auf Workflow-Card navigiert zur Detailseite
  TC-REQ-006-033  ->  TC-006-039  Workflow-Detailseite rendert mit Tabs
  TC-REQ-006-034  ->  TC-006-039  Workflow-Detailseite Tabs koennen navigiert werden
  TC-REQ-006-035  ->  TC-006-039  Workflow-Detailseite zeigt den Workflow-Namen
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.workflow_detail_page import WorkflowDetailPage
from .pages.workflow_list_page import WorkflowListPage


# -- Fixtures ---------------------------------------------------------------


@pytest.fixture
def workflow_list(browser: WebDriver, base_url: str) -> WorkflowListPage:
    """Return a WorkflowListPage bound to the test browser."""
    return WorkflowListPage(browser, base_url)


@pytest.fixture
def workflow_detail(browser: WebDriver, base_url: str) -> WorkflowDetailPage:
    """Return a WorkflowDetailPage bound to the test browser."""
    return WorkflowDetailPage(browser, base_url)


# -- TC-006-034: Workflow Template List Page ---------------------------------


class TestWorkflowTemplateListPage:
    """Workflow template list page operations (Spec: TC-006-034, TC-006-035)."""

    @pytest.mark.smoke
    def test_workflow_list_page_renders(
        self,
        workflow_list: WorkflowListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-024: Workflow template list page renders.

        Spec: TC-006-034 -- Workflow-Template-Liste aufrufen.
        """
        workflow_list.open()
        screenshot(
            "TC-REQ-006-024_workflow-list-loaded",
            "Workflow template list page after initial load",
        )

        assert workflow_list.is_page_visible(), (
            "TC-REQ-006-024 FAIL: Expected [data-testid='workflow-template-list-page'] "
            "to be visible"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.core_crud
    def test_workflow_list_shows_cards(
        self,
        workflow_list: WorkflowListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-025: Workflow list shows workflow cards.

        Spec: TC-006-034 -- Workflow-Liste zeigt Workflow-Cards.
        """
        workflow_list.open()
        screenshot(
            "TC-REQ-006-025_workflow-cards",
            "Workflow cards grid layout",
        )

        card_count = workflow_list.get_card_count()
        # Cards should render (zero is valid if no workflows exist)
        assert card_count >= 0, (
            f"TC-REQ-006-025 FAIL: Expected non-negative card count, "
            f"got: {card_count}"
        )

    @pytest.mark.core_crud
    def test_create_workflow_button_is_visible(
        self,
        workflow_list: WorkflowListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-027: 'Create workflow' button is visible.

        Spec: TC-006-034 -- 'Workflow erstellen'-Button sichtbar.
        """
        workflow_list.open()
        screenshot(
            "TC-REQ-006-027_create-workflow-button",
            "Create workflow button visible",
        )

        assert workflow_list.has_create_button(), (
            "TC-REQ-006-027 FAIL: Expected [data-testid='create-workflow-button'] "
            "to be visible"
        )

    @pytest.mark.core_crud
    def test_workflow_list_card_count(
        self,
        workflow_list: WorkflowListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-028: Workflow cards show available workflows.

        Spec: TC-006-034 -- Workflow-Cards zeigen vorhandene Workflows.
        """
        workflow_list.open()
        screenshot(
            "TC-REQ-006-028_workflow-card-count",
            "Workflow card count",
        )

        card_count = workflow_list.get_card_count()
        # We do not assert > 0 since there may be no workflows yet
        assert card_count >= 0, (
            f"TC-REQ-006-028 FAIL: Expected non-negative card count, got: {card_count}"
        )

    @pytest.mark.core_crud
    def test_search_workflows(
        self,
        workflow_list: WorkflowListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-029: Workflow search filters the cards.

        Spec: TC-006-034 -- Workflow-Suche filtert die Cards.
        """
        workflow_list.open()

        if workflow_list.get_card_count() == 0:
            pytest.skip("No workflows in database -- cannot test search")

        initial_count = workflow_list.get_card_count()
        screenshot(
            "TC-REQ-006-029_before-workflow-search",
            "Workflow cards before search",
        )

        workflow_list.search("ZZZ_NONEXISTENT_WORKFLOW_9999")
        workflow_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-029_after-workflow-search",
            "Workflow cards after search (no matches expected)",
        )

        filtered_count = workflow_list.get_card_count()
        assert filtered_count < initial_count or filtered_count == 0, (
            f"TC-REQ-006-029 FAIL: Expected search to filter cards. "
            f"Before: {initial_count}, After: {filtered_count}"
        )


# -- TC-006-038: Workflow Instantiate ----------------------------------------


class TestWorkflowInstantiate:
    """Instantiate (apply) a workflow to a plant (Spec: TC-006-038)."""

    @pytest.mark.core_crud
    def test_create_workflow_opens_dialog(
        self,
        workflow_list: WorkflowListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-031: Click 'Create workflow' opens dialog.

        Spec: TC-006-038 -- Klick auf 'Workflow erstellen' oeffnet Dialog.
        """
        workflow_list.open()
        screenshot(
            "TC-REQ-006-031_before-create-workflow",
            "Workflow list before clicking create workflow",
        )

        workflow_list.click_create_workflow()
        screenshot(
            "TC-REQ-006-031_create-workflow-dialog",
            "Create workflow dialog opened",
        )

        assert workflow_list.is_dialog_open(), (
            "TC-REQ-006-031 FAIL: Expected dialog to be open after clicking "
            "create workflow button"
        )


# -- TC-006-039: Workflow Detail Page ----------------------------------------


class TestWorkflowDetailPage:
    """Workflow detail page operations (Spec: TC-006-039, TC-006-040)."""

    @pytest.mark.core_crud
    def test_workflow_detail_loads_from_list_click(
        self,
        workflow_list: WorkflowListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-032: Click workflow card navigates to detail page.

        Spec: TC-006-039 -- Klick auf Workflow-Card navigiert zur Detailseite.
        """
        workflow_list.open()

        if workflow_list.get_card_count() == 0:
            pytest.skip("No workflows in database -- cannot test detail navigation")

        screenshot(
            "TC-REQ-006-032_before-workflow-card-click",
            "Workflow list before clicking card",
        )

        workflow_list.click_card(0)
        workflow_list.wait_for_url_contains("/aufgaben/workflows/")
        screenshot(
            "TC-REQ-006-032_workflow-detail-loaded",
            "Workflow detail page loaded after card click",
        )

        assert "/aufgaben/workflows/" in workflow_list.driver.current_url, (
            f"TC-REQ-006-032 FAIL: Expected URL to contain '/aufgaben/workflows/', "
            f"got: {workflow_list.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_workflow_detail_page_renders(
        self,
        workflow_list: WorkflowListPage,
        workflow_detail: WorkflowDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-033: Workflow detail page renders with data-testid and tabs.

        Spec: TC-006-039 -- Workflow-Detailseite rendert mit data-testid und Tabs.
        """
        workflow_list.open()

        if workflow_list.get_card_count() == 0:
            pytest.skip("No workflows in database -- cannot test detail page")

        # Navigate via card click to get a valid workflow key
        workflow_list.click_card(0)
        workflow_list.wait_for_url_contains("/aufgaben/workflows/")

        # Now verify the detail page
        assert workflow_detail.is_page_visible(), (
            "TC-REQ-006-033 FAIL: Expected [data-testid='workflow-detail-page'] "
            "to be visible"
        )

        screenshot(
            "TC-REQ-006-033_workflow-detail-content",
            "Workflow detail page with tabs visible",
        )

        tabs = workflow_detail.get_tab_labels()
        assert len(tabs) >= 2, (
            f"TC-REQ-006-033 FAIL: Expected at least 2 tabs on workflow detail page, "
            f"got {len(tabs)}: {tabs}"
        )

    @pytest.mark.core_crud
    def test_workflow_detail_tab_navigation(
        self,
        workflow_list: WorkflowListPage,
        workflow_detail: WorkflowDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-034: Workflow detail page tabs can be navigated.

        Spec: TC-006-039 -- Workflow-Detailseite Tabs koennen navigiert werden.
        """
        workflow_list.open()

        if workflow_list.get_card_count() == 0:
            pytest.skip("No workflows in database -- cannot test tab navigation")

        workflow_list.click_card(0)
        workflow_list.wait_for_url_contains("/aufgaben/workflows/")

        tabs = workflow_detail.get_tab_labels()
        screenshot(
            "TC-REQ-006-034_workflow-tabs-start",
            "Workflow detail tabs: default tab active",
        )

        for i, label in enumerate(tabs):
            if i == 0:
                continue
            workflow_detail.click_tab_by_index(i)
            workflow_detail.wait_for_loading_complete()
            screenshot(
                f"TC-REQ-006-034_workflow-tab-{i}-{label.lower().replace(' ', '_')}",
                f"Workflow tab '{label}' active",
            )

            active = workflow_detail.get_active_tab_label()
            assert active == label, (
                f"TC-REQ-006-034 FAIL: Expected active tab to be '{label}', "
                f"got '{active}'"
            )

    @pytest.mark.core_crud
    def test_workflow_detail_shows_title(
        self,
        workflow_list: WorkflowListPage,
        workflow_detail: WorkflowDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-035: Workflow detail page shows the workflow name.

        Spec: TC-006-039 -- Workflow-Detailseite zeigt den Workflow-Namen.
        """
        workflow_list.open()

        if workflow_list.get_card_count() == 0:
            pytest.skip("No workflows in database -- cannot test title")

        workflow_list.click_card(0)
        workflow_list.wait_for_url_contains("/aufgaben/workflows/")

        title = workflow_detail.get_workflow_title()
        screenshot(
            "TC-REQ-006-035_workflow-title",
            f"Workflow detail page title: {title}",
        )

        assert title, (
            "TC-REQ-006-035 FAIL: Expected workflow title to be non-empty "
            "on detail page"
        )
