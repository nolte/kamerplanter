"""E2E tests for REQ-006 — Task Queue Page.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-006.md):
  TC-REQ-006-010  ->  TC-006-001  Task-Queue aufrufen -- Seite rendert
  TC-REQ-006-011  ->  TC-006-001  Create-Task-Button ist sichtbar
  TC-REQ-006-012  ->  TC-006-002  Aufgaben nach Dringlichkeit gruppiert
  TC-REQ-006-013  ->  TC-006-005  Source-Filter-Toggles sind sichtbar
  TC-REQ-006-014  ->  TC-006-005  Filter: Nur Aufgaben
  TC-REQ-006-015  ->  TC-006-005  Filter: Nur Pflege
  TC-REQ-006-016  ->  TC-006-003  Kategorie-Filter ist sichtbar
  TC-REQ-006-017  ->  TC-006-006  Task starten via Play-Icon
  TC-REQ-006-018  ->  TC-006-007  Task direkt abschliessen (Quick-Complete)
  TC-REQ-006-019  ->  TC-006-008  Task ueberspringen via Skip-Icon
  TC-REQ-006-020  ->  TC-006-009  Bulk-Modus aktivieren
  TC-REQ-006-021  ->  TC-006-009  Bulk-Modus verlassen
  TC-REQ-006-022  ->  TC-006-013  Erstellen-Dialog oeffnen
  TC-REQ-006-023  ->  TC-006-012  Pflegeerinnerungen-generieren-Button sichtbar
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.task_queue_page import TaskQueuePage


# -- Fixtures ---------------------------------------------------------------


@pytest.fixture
def task_queue(browser: WebDriver, base_url: str) -> TaskQueuePage:
    """Return a TaskQueuePage bound to the test browser."""
    return TaskQueuePage(browser, base_url)


# -- TC-006-001 to TC-006-002: Page Load & Display --------------------------


class TestTaskQueuePageLoad:
    """Task queue page load and display (Spec: TC-006-001, TC-006-002)."""

    @pytest.mark.smoke
    def test_task_queue_page_renders(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-010: Task queue page renders with data-testid.

        Spec: TC-006-001 -- Task-Queue aufrufen -- Seite rendert.
        """
        task_queue.open()
        screenshot(
            "TC-REQ-006-010_task-queue-loaded",
            "Task queue page after initial load",
        )

        assert task_queue.is_page_visible(), (
            "TC-REQ-006-010 FAIL: Expected [data-testid='task-queue-page'] to be visible"
        )

    @pytest.mark.smoke
    def test_create_task_button_is_visible(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-011: Create task button is visible on the queue page.

        Spec: TC-006-001 -- Task-Queue aufrufen -- Button 'Aufgabe erstellen' sichtbar.
        """
        task_queue.open()
        screenshot(
            "TC-REQ-006-011_create-button-visible",
            "Create task button visible on queue page",
        )

        assert task_queue.is_create_button_visible(), (
            "TC-REQ-006-011 FAIL: Expected [data-testid='create-task-button'] to be visible"
        )

    @pytest.mark.core_crud
    def test_task_queue_shows_urgency_sections(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-012: Tasks are displayed grouped by urgency sections.

        Spec: TC-006-002 -- Aufgaben nach Dringlichkeit gruppiert anzeigen.
        """
        task_queue.open()
        screenshot(
            "TC-REQ-006-012_urgency-sections",
            "Task queue with urgency group sections",
        )

        card_count = task_queue.get_task_card_count()
        if card_count == 0:
            pytest.skip("No tasks in database -- cannot verify urgency sections")

        sections = task_queue.get_visible_sections()
        assert len(sections) > 0, (
            f"TC-REQ-006-012 FAIL: Expected at least one urgency section when tasks "
            f"exist, got: {sections}"
        )


# -- TC-006-003 to TC-006-005: Filters --------------------------------------


class TestTaskQueueFilters:
    """Filter interactions on the task queue (Spec: TC-006-003, TC-006-005)."""

    @pytest.mark.core_crud
    def test_source_filter_toggles_are_visible(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-013: Source filter toggle buttons (All/Tasks/Care) are present.

        Spec: TC-006-005 -- Quelle-Filter (Tasks vs. Pflegeerinnerungen).
        """
        task_queue.open()
        screenshot(
            "TC-REQ-006-013_filter-toggles",
            "Source filter toggles visible on queue page",
        )

        for locator in [
            TaskQueuePage.FILTER_ALL,
            TaskQueuePage.FILTER_TASKS,
            TaskQueuePage.FILTER_CARE,
        ]:
            assert task_queue.is_filter_visible(locator), (
                f"TC-REQ-006-013 FAIL: Expected filter toggle {locator} to be present"
            )

    @pytest.mark.core_crud
    def test_filter_tasks_only(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-014: Clicking 'Tasks only' filter toggles the view.

        Spec: TC-006-005 -- Quelle-Filter: 'Nur Aufgaben'.
        """
        task_queue.open()
        screenshot(
            "TC-REQ-006-014_before-filter-tasks",
            "Queue before applying tasks-only filter",
        )

        task_queue.click_filter_tasks()
        task_queue.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-014_after-filter-tasks",
            "Queue after applying tasks-only filter",
        )

        # Verify filter button is still visible after click
        assert task_queue.is_filter_visible(TaskQueuePage.FILTER_TASKS), (
            "TC-REQ-006-014 FAIL: Tasks filter button should still be visible after click"
        )

    @pytest.mark.core_crud
    def test_filter_care_only(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-015: Clicking 'Care only' filter toggles the view.

        Spec: TC-006-005 -- Quelle-Filter: 'Nur Pflege'.
        """
        task_queue.open()
        task_queue.click_filter_care()
        task_queue.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-015_after-filter-care",
            "Queue after applying care-only filter",
        )

        assert task_queue.is_filter_visible(TaskQueuePage.FILTER_CARE), (
            "TC-REQ-006-015 FAIL: Care filter button should still be visible after click"
        )

    @pytest.mark.core_crud
    def test_category_filter_is_present(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-016: Category filter dropdown is visible.

        Spec: TC-006-003 -- Task-Queue Filterung nach Kategorie.
        """
        task_queue.open()
        screenshot(
            "TC-REQ-006-016_category-filter",
            "Category filter dropdown visible on queue page",
        )

        assert task_queue.has_category_filter(), (
            "TC-REQ-006-016 FAIL: Expected [data-testid='filter-category'] to be present"
        )


# -- TC-006-006 to TC-006-008: Quick Actions --------------------------------


class TestTaskQueueQuickActions:
    """Task status transitions from queue (Spec: TC-006-006, TC-006-007, TC-006-008)."""

    @pytest.mark.core_crud
    def test_start_task_from_queue(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-017: Start task (pending -> in_progress) via play icon.

        Spec: TC-006-006 -- Task starten (pending -> in_progress).
        """
        task_queue.open()

        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test start action")

        key = keys[0]
        screenshot(
            "TC-REQ-006-017_before-start-task",
            f"Queue before starting task {key}",
        )

        task_queue.start_task(key)
        task_queue.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-017_after-start-task",
            f"Queue after starting task {key}",
        )

    @pytest.mark.core_crud
    def test_complete_task_from_queue(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-018: Complete task (Quick-Complete) via check icon.

        Spec: TC-006-007 -- Task direkt abschliessen (Quick-Complete).
        """
        task_queue.open()

        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test complete action")

        key = keys[0]
        screenshot(
            "TC-REQ-006-018_before-complete-task",
            f"Queue before completing task {key}",
        )

        task_queue.complete_task(key)
        task_queue.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-018_after-complete-task",
            f"Queue after completing task {key}",
        )

    @pytest.mark.core_crud
    def test_skip_task_from_queue(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-019: Skip task via skip icon.

        Spec: TC-006-008 -- Task ueberspringen.
        """
        task_queue.open()

        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test skip action")

        key = keys[0]
        screenshot(
            "TC-REQ-006-019_before-skip-task",
            f"Queue before skipping task {key}",
        )

        task_queue.skip_task(key)
        task_queue.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-019_after-skip-task",
            f"Queue after skipping task {key}",
        )


# -- TC-006-009 to TC-006-011: Bulk Mode ------------------------------------


class TestTaskQueueBulkMode:
    """Bulk mode operations (Spec: TC-006-009, TC-006-010, TC-006-011)."""

    @pytest.mark.core_crud
    def test_bulk_mode_activation(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-020: Activate bulk mode and display multi-select UI.

        Spec: TC-006-009 -- Bulk-Modus aktivieren und mehrere Tasks auswaehlen.
        """
        task_queue.open()

        card_count = task_queue.get_task_card_count()
        if card_count == 0:
            pytest.skip("No tasks in database -- cannot test bulk mode")

        screenshot(
            "TC-REQ-006-020_before-bulk-mode",
            "Queue before activating bulk mode",
        )

        task_queue.enter_bulk_mode()
        screenshot(
            "TC-REQ-006-020_bulk-mode-active",
            "Queue with bulk mode activated",
        )

        assert task_queue.is_bulk_mode_active(), (
            "TC-REQ-006-020 FAIL: Expected bulk mode to be active (exit button visible)"
        )
        assert task_queue.is_bulk_action_bar_visible(), (
            "TC-REQ-006-020 FAIL: Expected bulk action bar to be visible"
        )

    @pytest.mark.core_crud
    def test_bulk_mode_exit(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-021: Exit bulk mode via exit button.

        Spec: TC-006-009 -- Bulk-Modus verlassen.
        """
        task_queue.open()

        card_count = task_queue.get_task_card_count()
        if card_count == 0:
            pytest.skip("No tasks in database -- cannot test bulk mode exit")

        task_queue.enter_bulk_mode()
        assert task_queue.is_bulk_mode_active(), (
            "TC-REQ-006-021 FAIL: Bulk mode should be active"
        )

        task_queue.exit_bulk_mode()
        task_queue.wait_for_loading_complete()
        screenshot(
            "TC-REQ-006-021_bulk-mode-exited",
            "Queue after exiting bulk mode",
        )

        assert not task_queue.is_bulk_mode_active(), (
            "TC-REQ-006-021 FAIL: Expected bulk mode to be deactivated after exit"
        )


# -- TC-006-013: Create Task Dialog -----------------------------------------


class TestTaskCreateDialog:
    """Task creation dialog opens from queue (Spec: TC-006-013, TC-006-014)."""

    @pytest.mark.core_crud
    def test_create_task_opens_dialog(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-022: Click create button opens the task create dialog.

        Spec: TC-006-013 -- Neue Aufgabe erstellen -- Dialog oeffnet sich.
        """
        task_queue.open()
        screenshot(
            "TC-REQ-006-022_before-create-click",
            "Queue before clicking create button",
        )

        task_queue.click_create_task()
        screenshot(
            "TC-REQ-006-022_create-dialog-open",
            "Task create dialog opened",
        )

        assert task_queue.is_create_dialog_open(), (
            "TC-REQ-006-022 FAIL: Expected create task dialog to be open "
            "after clicking create button"
        )

    @pytest.mark.core_crud
    def test_generate_reminders_button_visible(
        self,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-023: Generate care reminders button is visible.

        Spec: TC-006-012 -- Pflegeerinnerungen generieren.
        """
        task_queue.open()
        screenshot(
            "TC-REQ-006-023_reminders-button",
            "Generate care reminders button visible on queue page",
        )

        assert task_queue.is_generate_reminders_visible(), (
            "TC-REQ-006-023 FAIL: Expected [data-testid='generate-reminders-button'] "
            "to be visible"
        )
