"""E2E tests for REQ-006 — Navigation between task/workflow pages.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-006.md):
  TC-REQ-006-036  ->  TC-006-019  Navigation Queue -> Detail -> Browser-Back -> Queue
  TC-REQ-006-037  ->  TC-006-020  Pflanzenverweis in der Detailseite navigiert zur Pflanze
  TC-REQ-006-038  ->  TC-006-039  Navigation Workflow-Liste -> Detail -> Back -> Liste
  TC-REQ-006-039  ->  TC-006-001  Direkte URL-Navigation zu /aufgaben/queue
  TC-REQ-006-040  ->  TC-006-034  Direkte URL-Navigation zu /aufgaben/workflows (Redirect)
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.task_detail_page import TaskDetailPage
from .pages.task_queue_page import TaskQueuePage
from .pages.workflow_detail_page import WorkflowDetailPage
from .pages.workflow_list_page import WorkflowListPage


# -- Fixtures ---------------------------------------------------------------


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


# -- Navigation: Task Queue <-> Task Detail ----------------------------------


class TestTaskNavigation:
    """Navigation between task queue and task detail pages (Spec: TC-006-019, TC-006-020)."""

    @pytest.mark.smoke
    def test_queue_to_detail_and_back(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-036: Navigation Queue -> Detail -> Browser-Back -> Queue.

        Spec: TC-006-019 -- Task-Detailseite aufrufen -- Tab-Navigation.
        """
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test navigation")

        screenshot(
            "TC-REQ-006-036_queue-start",
            "Task queue as navigation starting point",
        )

        # Navigate to detail
        task_queue.click_task_card(keys[0])
        task_queue.wait_for_url_contains("/aufgaben/tasks/")
        screenshot(
            "TC-REQ-006-036_detail-reached",
            "Task detail page reached via card click",
        )

        assert "/aufgaben/tasks/" in task_queue.driver.current_url, (
            f"TC-REQ-006-036 FAIL: Expected URL to contain '/aufgaben/tasks/', "
            f"got: {task_queue.driver.current_url}"
        )

        # Navigate back
        task_queue.driver.back()
        task_queue.wait_for_url_contains("/aufgaben/queue")
        screenshot(
            "TC-REQ-006-036_back-to-queue",
            "Task queue after browser back navigation",
        )

        assert "/aufgaben/queue" in task_queue.driver.current_url, (
            f"TC-REQ-006-036 FAIL: Expected URL to contain '/aufgaben/queue', "
            f"got: {task_queue.driver.current_url}"
        )

    @pytest.mark.core_crud
    def test_task_detail_plant_link_navigates(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-037: Plant link on detail page navigates to plant detail.

        Spec: TC-006-020 -- Pflanzenverweis in der Detailseite navigiert zur Pflanzen-Detailseite.
        """
        task_queue.open()
        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test plant link")

        task_detail.open(keys[0])
        screenshot(
            "TC-REQ-006-037_detail-with-plant",
            "Task detail page with potential plant link",
        )

        if not task_detail.has_plant_link():
            pytest.skip("Task has no plant link -- cannot test plant navigation")

        task_detail.click_plant_link()
        task_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-037_plant-detail-reached",
            "Plant detail page reached via task plant link",
        )

        assert "/pflanzen/" in task_detail.driver.current_url or "/plants/" in task_detail.driver.current_url, (
            f"TC-REQ-006-037 FAIL: Expected URL to navigate to plant detail, "
            f"got: {task_detail.driver.current_url}"
        )


# -- Navigation: Workflow List <-> Workflow Detail ---------------------------


class TestWorkflowNavigation:
    """Navigation between workflow list and workflow detail pages (Spec: TC-006-034, TC-006-039)."""

    @pytest.mark.skip(
        reason="WorkflowListPage route /aufgaben/workflows redirects to /stammdaten/species — no standalone list page"
    )
    @pytest.mark.core_crud
    def test_workflow_list_to_detail_and_back(
        self,
        workflow_list: WorkflowListPage,
        workflow_detail: WorkflowDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-038: Navigation Workflow-List -> Detail -> Browser-Back -> List.

        Spec: TC-006-039 -- Workflow-Detailseite aufrufen.
        """
        workflow_list.open()

        if workflow_list.get_row_count() == 0:
            pytest.skip("No workflows in database -- cannot test navigation")

        screenshot(
            "TC-REQ-006-038_workflow-list-start",
            "Workflow list as navigation starting point",
        )

        workflow_list.click_row(0)
        workflow_list.wait_for_url_contains("/aufgaben/workflows/")
        screenshot(
            "TC-REQ-006-038_workflow-detail-reached",
            "Workflow detail reached via row click",
        )

        assert "/aufgaben/workflows/" in workflow_list.driver.current_url, (
            f"TC-REQ-006-038 FAIL: Expected URL to contain '/aufgaben/workflows/', "
            f"got: {workflow_list.driver.current_url}"
        )

        # Navigate back
        workflow_list.driver.back()
        workflow_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-038_back-to-workflow-list",
            "Workflow list after browser back navigation",
        )

    @pytest.mark.smoke
    def test_direct_url_navigation_task_queue(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-039: Direct URL navigation to /aufgaben/queue works.

        Spec: TC-006-001 -- Task-Queue aufrufen.
        """
        task_queue.open()
        screenshot(
            "TC-REQ-006-039_direct-queue",
            "Task queue after direct URL navigation",
        )

        assert "/aufgaben/queue" in task_queue.driver.current_url, (
            f"TC-REQ-006-039 FAIL: Expected URL to contain '/aufgaben/queue', "
            f"got: {task_queue.driver.current_url}"
        )

        assert task_queue.is_page_visible(), (
            "TC-REQ-006-039 FAIL: Expected task queue page to render after "
            "direct URL navigation"
        )

    @pytest.mark.smoke
    def test_direct_url_navigation_workflow_list_loads(
        self,
        workflow_list: WorkflowListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-040: Direct URL /aufgaben/workflows loads the workflow template list.

        Spec: TC-006-034 -- Workflow-Template-Liste direkt aufrufen.
        """
        workflow_list.open()
        screenshot(
            "TC-REQ-006-040_direct-workflows-loaded",
            "Workflow template list page loaded via direct URL",
        )

        current_url = workflow_list.driver.current_url
        assert "/aufgaben/workflows" in current_url, (
            f"TC-REQ-006-040 FAIL: Expected URL to contain /aufgaben/workflows, "
            f"got: {current_url}"
        )
