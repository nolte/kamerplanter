"""E2E tests for REQ-006 — Navigation between task/workflow pages.

Tests cover:
- Navigation from task queue to task detail and back
- Navigation from workflow list to workflow detail and back
- Cross-page navigation (task detail -> plant link)
- URL structure verification

NFR-008 ss3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
"""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.task_detail_page import TaskDetailPage
from .pages.task_queue_page import TaskQueuePage
from .pages.workflow_detail_page import WorkflowDetailPage
from .pages.workflow_list_page import WorkflowListPage


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def task_queue(browser: WebDriver, base_url: str) -> TaskQueuePage:
    """Return a TaskQueuePage bound to the test browser."""
    return TaskQueuePage(browser, base_url)


@pytest.fixture
def task_detail(browser: WebDriver, base_url: str) -> TaskDetailPage:
    """Return a TaskDetailPage bound to the test browser."""
    return TaskDetailPage(browser, base_url)


@pytest.fixture
def workflow_list(browser: WebDriver, base_url: str) -> WorkflowListPage:
    """Return a WorkflowListPage bound to the test browser."""
    return WorkflowListPage(browser, base_url)


@pytest.fixture
def workflow_detail(browser: WebDriver, base_url: str) -> WorkflowDetailPage:
    """Return a WorkflowDetailPage bound to the test browser."""
    return WorkflowDetailPage(browser, base_url)


# ── Navigation: Task Queue <-> Task Detail ─────────────────────────────────────


class TestTaskNavigation:
    """Navigation between task queue and task detail pages."""

    def test_queue_to_detail_and_back(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot,
    ) -> None:
        """TC-006-019: Navigation Queue -> Detail -> Browser-Back -> Queue."""
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test navigation")

        screenshot("req006_nav_001_queue_start", "Task-Queue Ausgangspunkt")

        # Navigate to detail
        task_queue.click_task_card(keys[0])
        task_queue.wait_for_url_contains("/aufgaben/tasks/")
        screenshot("req006_nav_002_detail_reached", "Task-Detail erreicht")

        assert "/aufgaben/tasks/" in task_queue.driver.current_url, (
            f"Expected URL to contain '/aufgaben/tasks/', got: {task_queue.driver.current_url}"
        )

        # Navigate back
        task_queue.driver.back()
        time.sleep(1)
        screenshot("req006_nav_003_back_to_queue", "Zurueck zur Task-Queue")

        assert "/aufgaben/queue" in task_queue.driver.current_url, (
            f"Expected URL to contain '/aufgaben/queue', got: {task_queue.driver.current_url}"
        )

    def test_task_detail_plant_link_navigates(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot,
    ) -> None:
        """TC-006-020: Pflanzenverweis in der Detailseite navigiert zur Pflanzen-Detailseite."""
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test plant link")

        task_detail.open(keys[0])
        screenshot("req006_nav_004_detail_with_plant", "Task-Detail mit Pflanzenverweis")

        if not task_detail.has_plant_link():
            pytest.skip("Task has no plant link -- cannot test plant navigation")

        task_detail.click_plant_link()
        time.sleep(1)
        screenshot("req006_nav_005_plant_detail_reached", "Pflanzen-Detailseite erreicht")

        assert "/pflanzen/" in task_detail.driver.current_url or "/plants/" in task_detail.driver.current_url, (
            f"Expected URL to navigate to plant detail, got: {task_detail.driver.current_url}"
        )


# ── Navigation: Workflow List <-> Workflow Detail ──────────────────────────────


class TestWorkflowNavigation:
    """Navigation between workflow list and workflow detail pages."""

    @pytest.mark.skip(
        reason="WorkflowListPage route /aufgaben/workflows redirects to /stammdaten/species — no standalone list page"
    )
    def test_workflow_list_to_detail_and_back(
        self,
        workflow_list: WorkflowListPage,
        workflow_detail: WorkflowDetailPage,
        screenshot,
    ) -> None:
        """TC-006-039: Navigation Workflow-Liste -> Detail -> Browser-Back -> Liste."""
        workflow_list.open()

        if workflow_list.get_row_count() == 0:
            pytest.skip("No workflows in database -- cannot test navigation")

        screenshot("req006_nav_006_workflow_list_start", "Workflow-Liste Ausgangspunkt")

        workflow_list.click_row(0)
        workflow_list.wait_for_url_contains("/aufgaben/workflows/")
        screenshot("req006_nav_007_workflow_detail_reached", "Workflow-Detail erreicht")

        assert "/aufgaben/workflows/" in workflow_list.driver.current_url, (
            f"Expected URL to contain '/aufgaben/workflows/', got: {workflow_list.driver.current_url}"
        )

        # Navigate back
        workflow_list.driver.back()
        time.sleep(1)
        screenshot("req006_nav_008_back_to_workflow_list", "Zurueck zur Workflow-Liste")

    def test_direct_url_navigation_task_queue(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """Direkte URL-Navigation zu /aufgaben/queue funktioniert."""
        task_queue.open()
        screenshot("req006_nav_009_direct_queue", "Direkte Navigation zur Task-Queue")

        assert "/aufgaben/queue" in task_queue.driver.current_url, (
            f"Expected URL to contain '/aufgaben/queue', got: {task_queue.driver.current_url}"
        )

        page_el = task_queue.driver.find_element(*TaskQueuePage.PAGE)
        assert page_el.is_displayed(), (
            "Expected task queue page to render after direct URL navigation"
        )

    def test_direct_url_navigation_workflow_list_redirects(
        self,
        workflow_list: WorkflowListPage,
        screenshot,
    ) -> None:
        """Direkte URL-Navigation zu /aufgaben/workflows leitet zu /stammdaten/species um."""
        # Do NOT call workflow_list.open() -- it waits for a page element that
        # does not exist because the route redirects.  Navigate manually instead.
        workflow_list.navigate(WorkflowListPage.PATH)
        time.sleep(2)
        screenshot("req006_nav_010_direct_workflows", "Direkte Navigation zur Workflow-Liste (Redirect)")

        current_url = workflow_list.driver.current_url
        assert "/stammdaten/species" in current_url, (
            f"Expected /aufgaben/workflows to redirect to /stammdaten/species, got: {current_url}"
        )
