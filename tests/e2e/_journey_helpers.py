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

from .pages.plant_instance_list_page import PlantInstanceListPage


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
