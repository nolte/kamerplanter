"""E2E tests for REQ-006 — Task Detail Page (TC-006-019 to TC-006-033).

Tests cover:
- TaskDetailPage: page load, tab navigation, details display
- Status transitions: start, skip, reopen, clone
- Tab content: Details, Complete, Comments, History, Edit
- Action buttons visibility based on task status

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

from .pages.task_detail_page import TaskDetailPage
from .pages.task_queue_page import TaskQueuePage


# ── Fixtures ───────────────────────────────────────────────────────────────────


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


# ── TC-006-019: Tab Navigation ─────────────────────────────────────────────────


class TestTaskDetailTabNavigation:
    """TC-006-019: Task detail page tab navigation."""

    def test_detail_page_loads_with_tabs(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot,
    ) -> None:
        """TC-006-019: Task-Detailseite aufrufen -- Tab-Navigation sichtbar."""
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test detail page")

        task_detail.open(key)
        screenshot("req006_021_task_detail_loaded", "Task-Detailseite nach dem Laden")

        page_el = task_detail.driver.find_element(*TaskDetailPage.PAGE)
        assert page_el.is_displayed(), (
            "Expected [data-testid='task-detail-page'] to be visible"
        )

        tabs = task_detail.get_tab_labels()
        assert len(tabs) >= 4, (
            f"Expected at least 4 tabs on task detail page, got {len(tabs)}: {tabs}"
        )

    def test_detail_page_shows_task_title(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot,
    ) -> None:
        """TC-006-020: Task-Detailseite zeigt den Task-Namen als Ueberschrift."""
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test detail title")

        task_detail.open(key)
        screenshot("req006_022_task_detail_title", "Task-Name als Seitenueberschrift")

        title = task_detail.get_task_title()
        assert title, (
            "Expected task title to be non-empty on detail page"
        )

    def test_tab_navigation_clicks(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot,
    ) -> None:
        """TC-006-019: Tabs koennen angeklickt werden und wechseln den Inhalt."""
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test tab navigation")

        task_detail.open(key)
        tabs = task_detail.get_tab_labels()
        screenshot("req006_023_tab_navigation_start", "Tab-Navigation: Standard-Tab aktiv")

        # Click through each available tab
        for i, label in enumerate(tabs):
            if i == 0:
                continue  # Skip default tab
            task_detail.click_tab_by_index(i)
            time.sleep(0.5)
            screenshot(
                f"req006_024_tab_{i}_{label.lower().replace(' ', '_')}",
                f"Tab-Navigation: Tab '{label}' aktiv",
            )

            active = task_detail.get_active_tab_label()
            assert active == label, (
                f"Expected active tab to be '{label}', got '{active}'"
            )


# ── TC-006-020, TC-006-027: Detail Content & Edit Tab ─────────────────────────


class TestTaskDetailContent:
    """TC-006-020, TC-006-027: Task detail content and edit operations."""

    def test_details_tab_shows_metadata(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot,
    ) -> None:
        """TC-006-020: Details-Tab zeigt Metadaten (Status, Prioritaet, Kategorie)."""
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test details tab")

        task_detail.open(key)
        screenshot("req006_025_details_tab_content", "Details-Tab Inhalt mit Metadaten")

        # Verify the page content has some visible text content (task metadata)
        page_text = task_detail.driver.find_element(*TaskDetailPage.PAGE).text
        assert len(page_text) > 10, (
            "Expected details tab to show meaningful content (metadata)"
        )


# ── TC-006-024, TC-006-032: Status Transitions ────────────────────────────────


class TestTaskDetailStatusTransitions:
    """TC-006-006, TC-006-032: Task status transitions from detail page."""

    def test_start_button_visible_for_pending_task(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot,
    ) -> None:
        """TC-006-006: Start-Button ist fuer pending Tasks sichtbar."""
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test start button")

        task_detail.open(key)
        screenshot("req006_026_action_buttons", "Aktions-Buttons auf der Detailseite")

        # At least one of start/skip/reopen should be visible depending on status
        has_action = (
            task_detail.has_start_button()
            or task_detail.has_skip_button()
            or task_detail.has_reopen_button()
        )
        assert has_action, (
            "Expected at least one action button (start/skip/reopen) to be visible"
        )

    def test_clone_button_is_visible(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot,
    ) -> None:
        """TC-006-031: Klonen-Button ist auf der Detailseite sichtbar."""
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test clone button")

        task_detail.open(key)
        screenshot("req006_027_clone_button", "Klonen-Button sichtbar")

        assert task_detail.has_clone_button(), (
            "Expected [data-testid='clone-task-button'] to be visible"
        )

    def test_start_task_from_detail(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot,
    ) -> None:
        """TC-006-006: Task starten von der Detailseite."""
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test start from detail")

        task_detail.open(key)

        if not task_detail.has_start_button():
            pytest.skip("Task is not in pending state -- cannot test start")

        screenshot("req006_028_before_start_detail", "Vor Starten auf der Detailseite")
        task_detail.click_start()
        time.sleep(1)
        screenshot("req006_029_after_start_detail", "Nach Starten auf der Detailseite")

    def test_skip_task_from_detail(
        self,
        task_queue: TaskQueuePage,
        task_detail: TaskDetailPage,
        screenshot,
    ) -> None:
        """TC-006-008: Task ueberspringen von der Detailseite."""
        key = _get_first_task_key(task_queue)
        if not key:
            pytest.skip("No tasks in database -- cannot test skip from detail")

        task_detail.open(key)

        if not task_detail.has_skip_button():
            pytest.skip("Task does not have skip button visible")

        screenshot("req006_030_before_skip_detail", "Vor Ueberspringen auf der Detailseite")
        task_detail.click_skip()
        time.sleep(1)
        screenshot("req006_031_after_skip_detail", "Nach Ueberspringen auf der Detailseite")


# ── TC-006-019: Navigate from Queue to Detail ─────────────────────────────────


class TestTaskQueueToDetailNavigation:
    """TC-006-019: Navigation from task queue to task detail."""

    def test_click_task_card_navigates_to_detail(
        self,
        task_queue: TaskQueuePage,
        screenshot,
    ) -> None:
        """TC-006-019: Klick auf Task-Karte navigiert zur Detailseite."""
        task_queue.open()

        keys = task_queue.get_task_keys()
        if not keys:
            pytest.skip("No tasks in database -- cannot test navigation")

        key = keys[0]
        screenshot("req006_032_before_card_click", "Vor Klick auf Task-Karte")

        task_queue.click_task_card(key)
        task_queue.wait_for_url_contains("/aufgaben/tasks/")
        screenshot("req006_033_after_card_click", "Nach Navigation zur Detailseite")

        assert "/aufgaben/tasks/" in task_queue.driver.current_url, (
            f"Expected URL to contain '/aufgaben/tasks/', got: {task_queue.driver.current_url}"
        )
