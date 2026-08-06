"""E2E core-lifecycle journeys for REQ-006 — care task queue (self-provisioning).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-006.md, Gruppe 17):
  TC-REQ-006-J076  ->  TC-006-076  Core-Journey — create a care task and complete it in the queue
  TC-REQ-006-J077  ->  TC-006-077  Core-Journey — completed care task is documented

Each journey provisions its own plant instance through the real create dialog, so
the core path always runs — no runtime ``pytest.skip`` for missing seed data
(NFR-008a §2 self-provisioning; UI-NFR-022 data-testid addressing).

Adaptations to the real implemented flow (issue #589 R3):
- The TaskCreateDialog category enum has no dedicated "watering/Gießen" value; the
  journey uses the ``care_reminder`` (Pflege) category, which is the care-task
  category in the merged task queue.
- The TaskQueuePage has no "show completed tasks" toggle. TC-006-077 therefore
  verifies the completed task on the plant instance's Tasks tab, which reliably
  lists open *and* completed tasks (#578/#599) — the real surface where a
  completed care task stays documented. See the referenced follow-up issue.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._journey_helpers import create_care_task, provision_plant, unique_suffix
from .pages.phase_transition_page import PlantInstanceDetailExt
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.task_queue_page import TaskQueuePage


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def plant_creator(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    return PlantInstanceListPage(browser, base_url)


@pytest.fixture
def plant_detail(browser: WebDriver, base_url: str) -> PlantInstanceDetailExt:
    return PlantInstanceDetailExt(browser, base_url)


@pytest.fixture
def task_queue(browser: WebDriver, base_url: str) -> TaskQueuePage:
    return TaskQueuePage(browser, base_url)


# ── Shared arrange step ──────────────────────────────────────────────────────


def _create_care_task(task_queue: TaskQueuePage, instance_id: str, task_name: str) -> str:
    """Create a care task for the plant *instance_id* and return its key.

    Delegates to the shared :func:`_journey_helpers.create_care_task`. The
    version that stood here was a weaker duplicate of it — same dialog, same
    field values, but it drove the form once, ended on
    ``wait_for_loading_complete()`` and returned nothing. Three checks the
    shared helper makes were missing:

    * it asserts the plant autocomplete actually offered *instance_id*, instead
      of discarding the boolean that says whether the task got a plant at all;
    * it retries the whole dialog when the queue behind it renders slowly enough
      to intercept a click;
    * it **polls the queue across reloads** until the new card materialises, and
      raises naming the task when it never does.

    That last one is what failed on 2026-08-06: the queue refetches after the
    mutation, `wait_for_loading_complete()` is an absence poll on a skeleton
    that has not mounted yet, and the caller's single
    ``find_task_key_by_name()`` therefore read the pre-mutation queue and
    answered ``None``. The implicit wait had been covering that read; #835
    removed it and TC-REQ-006-J077 went red.
    """
    return create_care_task(task_queue, instance_id, task_name)


# ── TC-006-076 ───────────────────────────────────────────────────────────────


class TestCoreJourneyCreateAndCompleteTask:
    """Self-provision a plant, create a care task and complete it in the queue."""

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_create_and_complete_care_task(
        self,
        plant_creator: PlantInstanceListPage,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-006-076: Create a care task and complete it from the queue.

        Spec: TC-006-076 -- Core-Journey Pflege-Task anlegen + abschließen.
        """
        _key, instance_id = provision_plant(plant_creator, id_prefix="JOURNEY-006")
        task_name = f"Journey gießen {unique_suffix()}"

        # "The task appears in the queue" is now the helper's post-condition: it
        # polls the queue across reloads and raises naming the task if the card
        # never materialises. The single `find_task_key_by_name()` + `assert`
        # that stood here read the queue once, before its post-mutation refetch,
        # and would be unreachable now that the helper raises first.
        task_key = _create_care_task(task_queue, instance_id, task_name)
        screenshot("TC-REQ-006-J076_task-created", f"Task queue after creating '{task_name}'")

        task_queue.complete_task(task_key)
        time.sleep(1.0)
        screenshot("TC-REQ-006-J076_task-completed", "Task queue after completing the care task")

        # The completed task leaves the active groups (overdue/today/week).
        task_queue.open()
        assert not task_queue.has_task_with_name(task_name), (
            f"TC-REQ-006-J076 FAIL: Completed task '{task_name}' should disappear "
            f"from the active task queue"
        )


# ── TC-006-077 ───────────────────────────────────────────────────────────────


class TestCoreJourneyCompletedTaskDocumented:
    """A completed care task stays documented on the plant's Tasks tab."""

    @pytest.mark.core_crud
    def test_completed_task_visible_on_plant_tab(
        self,
        plant_creator: PlantInstanceListPage,
        task_queue: TaskQueuePage,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-006-077: Completed care task remains documented for the plant.

        Spec: TC-006-077 -- Core-Journey abgeschlossener Care-Task nachvollziehbar.
        Verified on the plant instance Tasks tab (real flow; the queue has no
        "show completed" toggle — see PR follow-up issue).
        """
        key, instance_id = provision_plant(plant_creator, id_prefix="JOURNEY-006V")
        task_name = f"Journey gießen {unique_suffix()}"

        # See the sibling journey above: "the task appears before completion" is
        # the helper's own post-condition, polled across queue reloads instead of
        # read once off the pre-refetch queue — which is how this assertion went
        # red on 2026-08-06 with `assert None is not None`.
        task_key = _create_care_task(task_queue, instance_id, task_name)
        task_queue.complete_task(task_key)
        time.sleep(1.0)

        # The plant's Tasks tab lists open AND completed tasks (#578/#599).
        plant_detail.open(key)
        plant_detail.open_tasks_tab()
        screenshot(
            "TC-REQ-006-J077_plant-tasks-tab",
            f"Plant {instance_id} Tasks tab showing the completed task",
        )
        assert task_name in plant_detail.get_body_text(), (
            f"TC-REQ-006-J077 FAIL: Completed task '{task_name}' should stay documented "
            f"on the plant instance Tasks tab"
        )
