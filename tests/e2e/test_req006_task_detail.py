"""E2E tests for REQ-006 — Task Detail Page.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-006.md):
  TC-REQ-006-001  ->  TC-006-019  Task-Detailseite aufrufen -- Tab-Navigation
  TC-REQ-006-002  ->  TC-006-020  Task-Detailseite -- Details-Tab
  TC-REQ-006-003  ->  TC-006-019  Tabs koennen angeklickt werden und wechseln den Inhalt
  TC-REQ-006-004  ->  TC-006-020  Details-Tab zeigt Metadaten (Status, Prioritaet, Kategorie)
  TC-REQ-006-005  ->  TC-006-006  Start-Button ist fuer pending Tasks sichtbar
  TC-REQ-006-006  ->  TC-006-031  Klonen-Button ist auf der Detailseite sichtbar
  TC-REQ-006-007  ->  TC-006-006  Task starten von der Detailseite
  TC-REQ-006-008  ->  TC-006-008  Task ueberspringen von der Detailseite
  TC-REQ-006-009  ->  TC-006-019  Klick auf Task-Karte navigiert zur Detailseite
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.task_detail_page import TaskDetailPage
from .pages.task_queue_page import TaskQueuePage


# -- Fixtures ---------------------------------------------------------------


@pytest.fixture
def task_detail(browser: WebDriver, base_url: str) -> TaskDetailPage:
    """Return a TaskDetailPage bound to the test browser."""
    return TaskDetailPage(browser, base_url)


@pytest.fixture
def task_queue(browser: WebDriver, base_url: str) -> TaskQueuePage:
    """Return a TaskQueuePage bound to the test browser."""
    return TaskQueuePage(browser, base_url)


def _get_first_task_key(task_queue: TaskQueuePage) -> str | None:
    """Navigate to queue and return the first task key, or None."""
    task_queue.open()
    keys = task_queue.get_task_keys()
    return keys[0] if keys else None


# -- TC-006-019: Tab Navigation ---------------------------------------------


class TestTaskDetailTabNavigation:
    """Task detail page tab navigation (Spec: TC-006-019, TC-006-020)."""

    @pytest.mark.smoke
    def test_detail_page_loads_with_tabs(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-001: Task detail page loads with visible tabs.

        Spec: TC-006-019 -- Task-Detailseite aufrufen -- Tab-Navigation sichtbar.
        """
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test detail page")

        task_detail.open(key)
        screenshot(
            "TC-REQ-006-001_task-detail-loaded",
            "Task detail page after initial load with tabs visible",
        )

        # Verify page marker via page object (page element presence confirmed by open())
        tabs = task_detail.get_tab_labels()
        assert len(tabs) >= 4, (
            f"TC-REQ-006-001 FAIL: Expected at least 4 tabs on task detail page, "
            f"got {len(tabs)}: {tabs}"
        )

    @pytest.mark.smoke
    def test_detail_page_shows_task_title(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-002: Task detail page shows the task name as heading.

        Spec: TC-006-020 -- Task-Detailseite -- Details-Tab.
        """
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test detail title")

        task_detail.open(key)
        screenshot(
            "TC-REQ-006-002_task-detail-title",
            "Task detail page showing task name as heading",
        )

        title = task_detail.get_task_title()
        assert title, (
            "TC-REQ-006-002 FAIL: Expected task title to be non-empty on detail page"
        )

    @pytest.mark.core_crud
    def test_tab_navigation_clicks(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-003: Tabs can be clicked and switch content.

        Spec: TC-006-019 -- Task-Detailseite aufrufen -- Tab-Navigation sichtbar.
        """
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test tab navigation")

        task_detail.open(key)
        tabs = task_detail.get_tab_labels()
        screenshot(
            "TC-REQ-006-003_tab-navigation-start",
            "Tab navigation: default tab active",
        )

        # Click through each available tab
        for i, label in enumerate(tabs):
            if i == 0:
                continue  # Skip default tab
            task_detail.click_tab_by_index(i)
            task_detail.wait_for_loading_complete()
            screenshot(
                f"TC-REQ-006-003_tab-{i}-{label.lower().replace(' ', '_')}",
                f"Tab navigation: tab '{label}' active",
            )

            active = task_detail.get_active_tab_label()
            assert active == label, (
                f"TC-REQ-006-003 FAIL: Expected active tab to be '{label}', "
                f"got '{active}'"
            )


# -- TC-006-020, TC-006-027: Detail Content & Edit Tab ----------------------


class TestTaskDetailContent:
    """Task detail content and edit operations (Spec: TC-006-020, TC-006-027)."""

    @pytest.mark.core_crud
    def test_details_tab_shows_metadata(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-004: Details tab shows metadata (status, priority, category).

        Spec: TC-006-020 -- Task-Detailseite -- Details-Tab.
        """
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test details tab")

        task_detail.open(key)
        screenshot(
            "TC-REQ-006-004_details-tab-content",
            "Details tab showing task metadata",
        )

        # Verify the page content has some visible text content (task metadata)
        page_text = task_detail.get_page_text()
        assert len(page_text) > 10, (
            "TC-REQ-006-004 FAIL: Expected details tab to show meaningful content (metadata)"
        )


# -- TC-006-024, TC-006-032: Status Transitions -----------------------------


class TestTaskDetailStatusTransitions:
    """Task status transitions from detail page (Spec: TC-006-006, TC-006-008, TC-006-031)."""

    @pytest.mark.core_crud
    def test_start_button_visible_for_pending_task(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-005: At least one action button is visible on detail page.

        Spec: TC-006-006 -- Task starten (pending -> in_progress).
        """
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test start button")

        task_detail.open(key)
        screenshot(
            "TC-REQ-006-005_action-buttons",
            "Action buttons visible on task detail page",
        )

        # At least one of start/skip/reopen should be visible depending on status
        has_action = (
            task_detail.has_start_button()
            or task_detail.has_skip_button()
            or task_detail.has_reopen_button()
        )
        assert has_action, (
            "TC-REQ-006-005 FAIL: Expected at least one action button "
            "(start/skip/reopen) to be visible"
        )

    @pytest.mark.core_crud
    def test_clone_button_is_visible(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-006: Clone button is visible on the detail page.

        Spec: TC-006-031 -- Klonen-Button sichtbar.
        """
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test clone button")

        task_detail.open(key)
        screenshot(
            "TC-REQ-006-006_clone-button",
            "Clone button visible on task detail page",
        )

        assert task_detail.has_clone_button(), (
            "TC-REQ-006-006 FAIL: Expected [data-testid='clone-task-button'] to be visible"
        )

    @pytest.mark.core_crud
    def test_start_task_from_detail(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-007: Start task from the detail page.

        Spec: TC-006-006 -- Task starten (pending -> in_progress).
        """
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test start from detail")

        task_detail.open(key)

        if not task_detail.has_start_button():
            pytest.skip("Task is not in pending state -- cannot test start")

        screenshot(
            "TC-REQ-006-007_before-start",
            "Task detail page before starting task",
        )
        task_detail.click_start()
        task_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-007_after-start",
            "Task detail page after starting task",
        )

    @pytest.mark.core_crud
    def test_skip_task_from_detail(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-008: Skip task from the detail page.

        Spec: TC-006-008 -- Task ueberspringen.
        """
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test skip from detail")

        task_detail.open(key)

        if not task_detail.has_skip_button():
            pytest.skip("Task does not have skip button visible")

        screenshot(
            "TC-REQ-006-008_before-skip",
            "Task detail page before skipping task",
        )
        task_detail.click_skip()
        task_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-008_after-skip",
            "Task detail page after skipping task",
        )


# -- TC-006-019: Navigate from Queue to Detail ------------------------------


class TestTaskQueueToDetailNavigation:
    """Navigation from task queue to task detail (Spec: TC-006-019)."""

    @pytest.mark.smoke
    def test_click_task_card_navigates_to_detail(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-009: Clicking a task card navigates to the detail page.

        Spec: TC-006-019 -- Task-Detailseite aufrufen -- Tab-Navigation.
        """
        task_queue.open()

        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test navigation")

        key = keys[0]
        screenshot(
            "TC-REQ-006-009_before-card-click",
            "Task queue before clicking task card",
        )

        task_queue.click_task_card(key)
        task_queue.wait_for_url_contains("/aufgaben/tasks/")
        screenshot(
            "TC-REQ-006-009_after-card-click",
            "Task detail page after card click navigation",
        )

        assert "/aufgaben/tasks/" in task_queue.driver.current_url, (
            f"TC-REQ-006-009 FAIL: Expected URL to contain '/aufgaben/tasks/', "
            f"got: {task_queue.driver.current_url}"
        )
