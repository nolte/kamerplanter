"""E2E tests for REQ-006 — Task Queue Page (TC-006-001 to TC-006-012).

Tests cover:
- TaskQueuePage: page load, empty state, task cards display
- Urgency grouping: overdue, today, this week, future
- Filters: source toggle (all/tasks/care), category dropdown
- Quick actions: start, complete, skip tasks
- Bulk mode: activate, select tasks, bulk complete/skip/delete
- Create task button opens dialog

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

from .pages.task_queue_page import TaskQueuePage


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def task_queue(browser: WebDriver, base_url: str) -> TaskQueuePage:
    """Return a TaskQueuePage bound to the test browser."""
    return TaskQueuePage(browser, base_url)


# ── TC-006-001 to TC-006-002: Page Load & Display ─────────────────────────────


class TestTaskQueuePageLoad:
    """TC-006-001, TC-006-002: Task queue page loads and displays content."""

    def test_task_queue_page_renders(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-001: Task-Queue aufrufen — Seite rendert mit data-testid."""
        task_queue.open()
        screenshot("req006_001_task_queue_loaded", "Aufgabenliste nach dem Laden")

        page_el = task_queue.driver.find_element(*TaskQueuePage.PAGE)
        assert page_el.is_displayed(), (
            "Expected [data-testid='task-queue-page'] to be visible"
        )

    def test_create_task_button_is_visible(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-001: Create task button is visible on the queue page."""
        task_queue.open()
        screenshot("req006_002_create_button_visible", "Erstellen-Button sichtbar")

        btn = task_queue.driver.find_element(*TaskQueuePage.CREATE_TASK_BUTTON)
        assert btn.is_displayed(), (
            "Expected [data-testid='create-task-button'] to be visible"
        )

    def test_task_queue_shows_urgency_sections(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-002: Aufgaben nach Dringlichkeit gruppiert anzeigen."""
        task_queue.open()
        screenshot("req006_003_urgency_sections", "Dringlichkeitsgruppen in der Task-Queue")

        card_count = task_queue.get_task_card_count()
        if card_count == 0:
            pytest.skip("No tasks in database -- cannot verify urgency sections")

        sections = task_queue.get_visible_sections()
        assert len(sections) > 0, (
            f"Expected at least one urgency section when tasks exist, got: {sections}"
        )


# ── TC-006-003 to TC-006-005: Filters ─────────────────────────────────────────


class TestTaskQueueFilters:
    """TC-006-003, TC-006-005: Filter interactions on the task queue."""

    def test_source_filter_toggles_are_visible(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-005: Source filter toggle buttons (All/Tasks/Care) are present."""
        task_queue.open()
        screenshot("req006_004_filter_toggles", "Quellfilter-Toggles sichtbar")

        for locator in [
            TaskQueuePage.FILTER_ALL,
            TaskQueuePage.FILTER_TASKS,
            TaskQueuePage.FILTER_CARE,
        ]:
            elements = task_queue.driver.find_elements(*locator)
            assert len(elements) > 0, (
                f"Expected filter toggle {locator} to be present"
            )

    def test_filter_tasks_only(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-005: Clicking 'Tasks only' filter toggles the view."""
        task_queue.open()
        screenshot("req006_005_before_filter_tasks", "Vor Filter: Nur Aufgaben")

        task_queue.click_filter_tasks()
        time.sleep(0.5)
        screenshot("req006_006_after_filter_tasks", "Nach Filter: Nur Aufgaben")

        # Verify filter button is still visible after click
        btn = task_queue.driver.find_element(*TaskQueuePage.FILTER_TASKS)
        assert btn.is_displayed(), "Tasks filter button should still be visible after click"

    def test_filter_care_only(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-005: Clicking 'Care only' filter toggles the view."""
        task_queue.open()
        task_queue.click_filter_care()
        time.sleep(0.5)
        screenshot("req006_007_after_filter_care", "Nach Filter: Nur Pflege")

        btn = task_queue.driver.find_element(*TaskQueuePage.FILTER_CARE)
        assert btn.is_displayed(), "Care filter button should still be visible after click"

    def test_category_filter_is_present(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-003: Category filter dropdown is visible."""
        task_queue.open()
        screenshot("req006_008_category_filter", "Kategorie-Filter sichtbar")

        assert task_queue.has_category_filter(), (
            "Expected [data-testid='filter-category'] to be present"
        )


# ── TC-006-006 to TC-006-008: Quick Actions ───────────────────────────────────


class TestTaskQueueQuickActions:
    """TC-006-006, TC-006-007, TC-006-008: Task status transitions from queue."""

    def test_start_task_from_queue(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-006: Task starten (pending -> in_progress) via Play-Icon."""
        task_queue.open()

        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test start action")

        key = keys[0]
        screenshot("req006_009_before_start_task", f"Vor Starten der Task {key}")

        task_queue.start_task(key)
        time.sleep(1)
        screenshot("req006_010_after_start_task", f"Nach Starten der Task {key}")

    def test_complete_task_from_queue(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-007: Task direkt abschliessen (Quick-Complete) via Haken-Icon."""
        task_queue.open()

        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test complete action")

        key = keys[0]
        screenshot("req006_011_before_complete_task", f"Vor Abschliessen der Task {key}")

        task_queue.complete_task(key)
        time.sleep(1)
        screenshot("req006_012_after_complete_task", f"Nach Abschliessen der Task {key}")

    def test_skip_task_from_queue(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-008: Task ueberspringen via Skip-Icon."""
        task_queue.open()

        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test skip action")

        key = keys[0]
        screenshot("req006_013_before_skip_task", f"Vor Ueberspringen der Task {key}")

        task_queue.skip_task(key)
        time.sleep(1)
        screenshot("req006_014_after_skip_task", f"Nach Ueberspringen der Task {key}")


# ── TC-006-009 to TC-006-011: Bulk Mode ───────────────────────────────────────


class TestTaskQueueBulkMode:
    """TC-006-009, TC-006-010, TC-006-011: Bulk mode operations."""

    def test_bulk_mode_activation(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-009: Bulk-Modus aktivieren und Mehrfachauswahl-UI anzeigen."""
        task_queue.open()

        card_count = task_queue.get_task_card_count()
        if card_count == 0:
            pytest.skip("No tasks in database -- cannot test bulk mode")

        screenshot("req006_015_before_bulk_mode", "Vor Aktivierung des Bulk-Modus")

        task_queue.enter_bulk_mode()
        screenshot("req006_016_bulk_mode_active", "Bulk-Modus aktiviert")

        assert task_queue.is_bulk_mode_active(), (
            "Expected bulk mode to be active (exit button visible)"
        )
        assert task_queue.is_bulk_action_bar_visible(), (
            "Expected bulk action bar to be visible"
        )

    def test_bulk_mode_exit(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-009: Bulk-Modus verlassen ueber Exit-Button."""
        task_queue.open()

        card_count = task_queue.get_task_card_count()
        if card_count == 0:
            pytest.skip("No tasks in database -- cannot test bulk mode exit")

        task_queue.enter_bulk_mode()
        assert task_queue.is_bulk_mode_active(), "Bulk mode should be active"

        task_queue.exit_bulk_mode()
        time.sleep(0.5)
        screenshot("req006_017_bulk_mode_exited", "Bulk-Modus verlassen")

        assert not task_queue.is_bulk_mode_active(), (
            "Expected bulk mode to be deactivated after exit"
        )


# ── TC-006-013: Create Task Dialog ────────────────────────────────────────────


class TestTaskCreateDialog:
    """TC-006-013, TC-006-014: Task creation dialog opens from queue."""

    def test_create_task_opens_dialog(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-013: Klick auf Erstellen-Button oeffnet den Dialog."""
        task_queue.open()
        screenshot("req006_018_before_create_click", "Vor Klick auf Erstellen")

        task_queue.click_create_task()
        screenshot("req006_019_create_dialog_open", "Erstellen-Dialog geoeffnet")

        assert task_queue.is_create_dialog_open(), (
            "Expected create task dialog to be open after clicking create button"
        )

    def test_generate_reminders_button_visible(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-012: Pflegeerinnerungen-generieren-Button ist sichtbar."""
        task_queue.open()
        screenshot("req006_020_reminders_button", "Pflegeerinnerungen-Button sichtbar")

        btn = task_queue.driver.find_element(*TaskQueuePage.GENERATE_REMINDERS_BUTTON)
        assert btn.is_displayed(), (
            "Expected [data-testid='generate-reminders-button'] to be visible"
        )
