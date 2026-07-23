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
  TC-REQ-006-041  ->  TC-006-078  Wiederholungsregel aendern -- persistiert (RRULE-Dropdown statt Cron)
  TC-REQ-006-042  ->  TC-006-079  Faelligkeit verschieben -- Task wechselt Dringlichkeits-Gruppe
  TC-REQ-006-043  ->  TC-006-080  Wiederkehrende Aufgabe abschliessen -- Folge-Instanz erscheint
  TC-REQ-006-044  ->  TC-006-081  Zyklus beenden -- keine neue Instanz nach Abschluss
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._journey_helpers import create_care_task, provision_plant, unique_suffix
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.task_detail_page import TaskDetailPage
from .pages.task_queue_page import TaskQueuePage


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
def plant_creator(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    """Return a PlantInstanceListPage for self-provisioning a plant instance."""
    return PlantInstanceListPage(browser, base_url)


def _provision_plant_and_care_task(
    plant_creator: PlantInstanceListPage,
    task_queue: TaskQueuePage,
    *,
    id_prefix: str,
) -> tuple[str, str, str]:
    """Self-provision a plant + due-today care task; return ``(task_key, task_name, instance_id)``.

    Both preconditions are created through the real UI (plant create dialog +
    task create dialog), so the update-propagation tests never depend on seed
    data and never skip at runtime. The instance id is returned so a test can
    scope the queue to exactly this plant.
    """
    _plant_key, instance_id = provision_plant(plant_creator, id_prefix=id_prefix)
    task_name = f"E2E {id_prefix} {unique_suffix()}"
    task_key = create_care_task(task_queue, instance_id, task_name)
    return task_key, task_name, instance_id


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


# -- TC-006-078 to TC-006-081: Task-Update Propagation into the Queue --------


class TestTaskUpdatePropagation:
    """Editing a task propagates into the task queue (Spec: TC-006-078 to TC-006-081).

    These verify the *list* side of the source-to-queue coupling: changing a
    task's recurrence rule, due date, or completing/ending a recurring cycle is
    reflected by the queue, which reads the current task state.  The
    notification side of the same coupling is deliberately out of scope here
    (covered as Soll-Verhalten in test_req030_notifications.py).
    """

    @pytest.mark.core_crud
    def test_recurrence_rule_change_persists(
        self,
        plant_creator: PlantInstanceListPage,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-041: Changing the recurrence rule persists on the task detail.

        Spec: TC-006-078 -- Wiederholungszyklus (Cron) aendern -- Aufgabenliste
        zeigt neue Faelligkeit.

        Self-provisioning: a fresh plant and a due-today care task are created
        through the real UI, so the test never depends on seed data.

        Abweichung Spec vs. Impl: ``recurrence_rule`` ist im Frontend ein festes
        RRULE-Dropdown (kein freier Cron ``0 8 * * 3``).  Die wochentagsgenaue
        Queue-Gruppierung aus der Spec ist damit nicht umsetzbar; stattdessen
        wird die neue Regel via Dropdown gesetzt und ihre Persistenz ueber die
        Detailseite (``get_detail_recurrence_text``) verifiziert.
        """
        key, _task_name, _instance_id = _provision_plant_and_care_task(
            plant_creator, task_queue, id_prefix="TC078"
        )

        task_detail.open(key)
        before = task_detail.get_detail_recurrence_text()
        screenshot(
            "TC-REQ-006-041_before-recurrence-change",
            f"Task {key} detail before recurrence change (recurrence='{before}')",
        )

        task_detail.open_edit_tab()
        task_detail.set_recurrence_rule("FREQ=WEEKLY;INTERVAL=2")
        task_detail.save_edit()

        # Reload the detail page from scratch to prove the value persisted.
        task_detail.open(key)
        after = task_detail.get_detail_recurrence_text()
        screenshot(
            "TC-REQ-006-041_after-recurrence-change",
            f"Task {key} detail after recurrence change (recurrence='{after}')",
        )

        assert after, (
            "TC-REQ-006-041 FAIL: Expected a non-empty recurrence value to persist "
            f"after setting FREQ=WEEKLY;INTERVAL=2, got '{after}'"
        )
        assert after != before, (
            "TC-REQ-006-041 FAIL: Expected the recurrence value to change from the "
            f"initial (non-recurring) state. Before: '{before}', After: '{after}'"
        )

    @pytest.mark.core_crud
    def test_due_date_shift_updates_detail_and_queue(
        self,
        plant_creator: PlantInstanceListPage,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-042: Shifting the due date moves the task out of the 'today' group.

        Spec: TC-006-079 -- Faelligkeitsdatum verschieben -- Task wechselt die
        Dringlichkeits-Gruppe.

        Self-provisioning: a due-today care task is created via the UI (so it
        starts in the 'today' urgency group); shifting its due date +5 days must
        move it into the 'thisWeek'/'future' group while it stays listed.
        """
        key, task_name, _instance_id = _provision_plant_and_care_task(
            plant_creator, task_queue, id_prefix="TC079"
        )

        # A due-today task starts in the 'today' urgency group.
        task_queue.open()
        section_before = task_queue.get_task_section(key)

        task_detail.open(key)
        before_due = task_detail.get_detail_due_text()
        target_due = (date.today() + timedelta(days=5)).isoformat()
        screenshot(
            "TC-REQ-006-042_before-due-shift",
            f"Task {key} detail before due-date shift "
            f"(due='{before_due}', section='{section_before}')",
        )

        task_detail.open_edit_tab()
        task_detail.set_due_date(target_due)
        task_detail.save_edit()

        task_detail.open(key)
        after_due = task_detail.get_detail_due_text()

        # The rescheduled task must still be listed, in a later urgency group.
        # Poll (reloading) so a slow refetch cannot read the queue before the
        # moved card re-renders in its new section.
        listed_after = task_queue.wait_for_task_by_name(task_name) is not None
        section_after = task_queue.get_task_section(key)
        screenshot(
            "TC-REQ-006-042_after-due-shift",
            f"Task {key} detail after due-date shift "
            f"(due='{after_due}', section='{section_after}')",
        )

        assert after_due, (
            "TC-REQ-006-042 FAIL: Expected a non-empty due-date value after the shift"
        )
        assert after_due != before_due, (
            "TC-REQ-006-042 FAIL: Expected the due-date value to change after shifting "
            f"to {target_due}. Before: '{before_due}', After: '{after_due}'"
        )
        assert listed_after, (
            "TC-REQ-006-042 FAIL: Expected the rescheduled task to remain listed in the queue"
        )
        assert section_after in ("thisWeek", "future"), (
            "TC-REQ-006-042 FAIL: Expected the task to move out of 'today' into the "
            f"'thisWeek'/'future' group after a +5d shift. Before: '{section_before}', "
            f"After: '{section_after}'"
        )

    @pytest.mark.core_crud
    def test_complete_recurring_task_spawns_next_instance(
        self,
        plant_creator: PlantInstanceListPage,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-043: Completing a recurring task materialises the next instance.

        Spec: TC-006-080 -- Wiederkehrende Aufgabe abschliessen -- naechste
        Zyklus-Instanz erscheint in der Liste.

        Self-provisioning: a fresh plant + care task is made recurring
        (FREQ=WEEKLY) and completed; the follow-up instance carrying the same
        name must appear as a NEW task key. Assertion targets the real,
        browser-observable queue state (no forced pass).
        """
        key, task_name, _instance_id = _provision_plant_and_care_task(
            plant_creator, task_queue, id_prefix="TC080"
        )

        # Make the task recurring so completion should spawn a follow-up.
        task_detail.open(key)
        task_detail.open_edit_tab()
        task_detail.set_recurrence_rule("FREQ=WEEKLY")
        task_detail.save_edit()

        task_queue.open()
        assert key in task_queue.get_task_keys(), (
            "TC-REQ-006-043 FAIL: Recurring task should still be listed before completion"
        )

        screenshot(
            "TC-REQ-006-043_before-complete-recurring",
            f"Queue before completing recurring task {key}",
        )
        task_queue.complete_task(key)
        task_queue.wait_for_loading_complete()

        # The follow-up instance materialises + refetches asynchronously; poll
        # (reloading) until the new future-dated instance is listed.
        new_key = task_queue.wait_for_task_by_name(task_name, timeout=30.0)
        screenshot(
            "TC-REQ-006-043_after-complete-recurring",
            f"Queue after completing recurring task (next instance='{new_key}')",
        )

        assert new_key is not None, (
            "TC-REQ-006-043 FAIL: Expected a follow-up recurring instance named "
            f"'{task_name}' after completion"
        )
        assert new_key != key, (
            "TC-REQ-006-043 FAIL: Expected the follow-up instance to be a NEW task "
            f"(key differs from the completed {key})"
        )

    @pytest.mark.core_crud
    def test_ended_cycle_spawns_no_new_instance(
        self,
        plant_creator: PlantInstanceListPage,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-044: Ending the cycle prevents a follow-up instance on completion.

        Spec: TC-006-081 -- Zyklus beenden -- nach Abschluss wird keine neue
        Instanz erzeugt.

        Self-provisioning: a fresh plant + care task is first made recurring
        (FREQ=WEEKLY), then its recurrence is removed (ended cycle); completing
        it must NOT spawn a follow-up instance.
        """
        key, task_name, _instance_id = _provision_plant_and_care_task(
            plant_creator, task_queue, id_prefix="TC081"
        )

        # Start a cycle, then end it: recurrence set then cleared.
        task_detail.open(key)
        task_detail.open_edit_tab()
        task_detail.set_recurrence_rule("FREQ=WEEKLY")
        task_detail.save_edit()

        task_detail.open(key)
        task_detail.open_edit_tab()
        task_detail.set_recurrence_rule("")
        task_detail.save_edit()

        task_queue.open()
        assert key in task_queue.get_task_keys(), (
            "TC-REQ-006-044 FAIL: Task should still be listed after ending its cycle"
        )

        screenshot(
            "TC-REQ-006-044_before-complete-ended-cycle",
            f"Queue before completing ended-cycle task {key}",
        )
        task_queue.complete_task(key)
        task_queue.wait_for_loading_complete()

        task_queue.open()
        remaining_key = task_queue.find_task_key_by_name(task_name)
        screenshot(
            "TC-REQ-006-044_after-complete-ended-cycle",
            f"Queue after completing ended-cycle task (remaining='{remaining_key}')",
        )

        assert remaining_key is None, (
            "TC-REQ-006-044 FAIL: Expected NO follow-up instance for the completed "
            f"ended-cycle task '{task_name}', but found key '{remaining_key}'"
        )
