"""Shared helpers for the self-provisioning core-lifecycle journeys (issue #589).

The core-lifecycle journeys (TC-001-079..081, TC-003-046..048, TC-004-089..091,
TC-006-076..077, TC-022-087..088) must never skip at runtime for lack of seed
data — every journey provisions its own preconditions through the real UI.

These helpers centralise the "create a plant instance via the
PlantInstanceCreateDialog" step so each journey can arrange a fresh plant and
then act/assert on it. Creation goes through the actual create dialog (not the
backend API) so the arrange step itself exercises the production UI, matching
the browser-user perspective mandated by NFR-008a.
"""

from __future__ import annotations

import time

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
)

from .pages.pflege_dashboard_page import PflegeDashboardPage
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.task_queue_page import TaskQueuePage


def unique_suffix() -> str:
    """Return a short, run-unique numeric suffix.

    Uses millisecond wall-clock time so repeated runs against the same
    persistent tenant never collide on instance ids (the seed DB survives
    between sessions — idempotency requirement).
    """
    return f"{int(time.time() * 1000) % 1_000_000:06d}"


def provision_plant(
    list_page: PlantInstanceListPage,
    *,
    id_prefix: str,
    plant_name: str | None = None,
    phase_index: int | None = None,
    species_query: str = "a",
) -> tuple[str, str]:
    """Create a plant instance through the create dialog and return ``(key, instance_id)``.

    Selects the first species matching *species_query* from the autocomplete,
    optionally sets a display name and a start phase (``phase_index`` into the
    current-phase select — e.g. ``-2`` for a late 'Ist-Stand' start), assigns a
    unique instance id derived from *id_prefix*, submits, then locates the new
    row by searching for the unique instance id and navigates to its detail
    page. The browser is left on the plant detail page.

    Raising (never skipping) on failure is deliberate: the journey's whole point
    is that the core path always runs.
    """
    instance_id = f"{id_prefix}-{unique_suffix()}"

    list_page.open()
    list_page.click_create()
    list_page.select_species(species_query)
    if plant_name is not None:
        list_page.fill_plant_name(plant_name)
    if phase_index is not None:
        list_page.select_current_phase_by_index(phase_index)
    list_page.set_instance_id(instance_id)
    list_page.submit_create_form()
    list_page.wait_for_loading_complete()

    # Locate exactly this plant by its unique instance id.
    list_page.search(instance_id)
    list_page.wait_for_loading_complete()
    if list_page.get_row_count() == 0:
        raise AssertionError(
            f"Self-provisioning failed: plant instance '{instance_id}' did not "
            f"appear in the list after creation"
        )
    list_page.click_row(0)
    list_page.wait_for_url_contains("/pflanzen/plant-instances/")
    key = list_page.driver.current_url.rstrip("/").rsplit("/", 1)[-1]
    return key, instance_id


def create_care_task(
    task_queue: TaskQueuePage,
    instance_id: str,
    task_name: str,
    *,
    category: str = "care_reminder",
    priority: str = "high",
) -> str:
    """Create a care task for plant *instance_id* via the queue dialog and return its key.

    Drives the real TaskCreateDialog (category ``care_reminder``, due today,
    high priority, plant selected by its unique instance id), submits, then
    locates the new card in the queue by its unique *task_name*.

    Raising (never skipping) on a missing card is deliberate: a self-provisioning
    test must always establish its own precondition.
    """
    # Fill and submit the create dialog. Under heavy parallel load (xdist) the
    # queue behind the dialog can render slowly enough to delay a dialog field
    # beyond its wait, or intercept a click; retry the whole dialog several
    # times before giving up. Each attempt re-navigates (task_queue.open), which
    # dismisses any half-open dialog from a previous failed attempt.
    last_exc: Exception | None = None
    for _attempt in range(4):
        try:
            task_queue.open()
            task_queue.click_create_task()
            # Confirm the dialog is actually interactive (its first field is
            # present) before driving the remaining fields — the MUI Dialog can
            # be in the DOM/visible while its form is still mounting under load.
            task_queue.wait_for_element_visible(task_queue.FORM_NAME)
            task_queue.fill_task_name(task_name)
            task_queue.select_task_category(category)
            task_queue.set_due_date_today()
            task_queue.select_task_priority(priority)
            if not task_queue.select_task_plant_by_text(instance_id):
                raise AssertionError(
                    f"Self-provisioning failed: plant '{instance_id}' offered no "
                    f"option in the task-create plant autocomplete"
                )
            task_queue.submit_task_form()
            task_queue.wait_for_loading_complete()
            break
        except (
            TimeoutException,
            ElementClickInterceptedException,
            ElementNotInteractableException,
            StaleElementReferenceException,
        ) as exc:
            last_exc = exc
            time.sleep(1.5)
    else:
        raise AssertionError(
            f"Self-provisioning failed: could not drive the task-create dialog "
            f"for '{task_name}' after 4 attempts: {last_exc}"
        )

    # The queue refetches after the mutation; poll a few reloads so a slow
    # refetch does not read the list before the new card is materialised.
    deadline = time.time() + 15.0
    while time.time() < deadline:
        task_queue.open()
        key = task_queue.find_task_key_by_name(task_name)
        if key is not None:
            return key
        time.sleep(1.0)
    raise AssertionError(
        f"Self-provisioning failed: care task '{task_name}' did not appear "
        f"in the queue after creation"
    )


def wait_for_watering_card(
    pflege: PflegeDashboardPage,
    plant_key: str,
    timeout: float = 15.0,
) -> bool:
    """Wait for the plant's live watering care card to render on ``/pflege``.

    A freshly provisioned plant gets an auto care profile whose watering entry
    is due today, so the merged care dashboard renders the
    ``care-card-care-{plant_key}-watering`` card on its own — no explicit
    "Generate reminders" click (which would materialise a task and deduplicate
    the live card away). Returns True once the card appears within *timeout*.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        pflege.open()
        if pflege.has_care_card(plant_key, "watering"):
            return True
        time.sleep(1.0)
    return False
