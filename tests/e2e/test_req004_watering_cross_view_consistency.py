"""E2E cross-view consistency for a single watering event (REQ-004, self-provisioning).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-004.md):
  TC-004-092  ->  TC-004-092  Ein Gießvorgang erscheint konsistent in globalem
                              Gießprotokoll, Instanz-Gießprotokoll und
                              Aufgabenverlauf (Task-Abschluss + Folgeaufgabe)

A single ``WateringLog`` must surface coherently across three browser views:

  View 1  ``/giessprotokoll``                                  — global log
  View 2  ``/pflanzen/plant-instances/{key}#watering-log``     — instance log
  View 3  ``/pflanzen/plant-instances/{key}#tasks``            — task history

The scenario self-provisions all preconditions (NFR-008a): it creates its own
plant instance through the real create dialog, then persists a care profile with
``auto_create_watering_task`` and materialises exactly one pending ``— watering``
task. That open task is what makes the WateringLog→task coupling
(``advance_watering_task_after_log``) complete the task and schedule the
follow-up in View 3 — without it the action would only appear in Views 1+2 (the
Guard in the spec). The core path therefore always runs; it never
``pytest.skip``s for missing seed data, and the unique instance id keeps it
parallel-safe.

The German date parser, the watering i18n labels and the three page-object
fixtures this module needs are **not** defined here: they are shared with the
pytest-bdd sibling (``…_bdd.py``) via ``_journey_helpers`` and ``conftest`` so
the two flavours cannot drift apart. See BDR-004.

The View-3 expected result "der Overdue/Active/Done-Summary-Balken spiegelt dies
wider" is asserted as a *delta* against the pre-action counts: the summary bar
must gain exactly one Done task while its Active count stays put, because the
watering closes one task and its follow-up immediately takes that slot. An
absolute count would be wrong here — a fresh care profile also materialises the
other opted-in reminder types (pest check, repotting), so the plant's active
tasks are legitimately more than the one ``— watering`` task this journey tracks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from ._journey_helpers import (
    DRENCH_METHOD_LABEL,
    DRENCH_OPTION_LABEL,
    TAP_LABEL,
    parse_de_date,
    provision_plant,
    provision_watering_care_task,
)
from .pages.plant_instance_detail_page import PlantInstanceDetailPage
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.watering_log_list_page import WateringLogListPage

# Feature-axis marker(s) for machine-selectable test identification
# (see conftest.py::KNOWN_FEATURE_MARKERS / pytest -m watering).
FEATURES = ('watering',)

# Route the linked plant chip must point at (spec: "verlinkter Chip auf
# /pflanzen/plant-instances/{key}").
PLANT_DETAIL_ROUTE = "/pflanzen/plant-instances"


# ── Shared act step ──────────────────────────────────────────────────────────


def _log_plain_watering(watering_list: WateringLogListPage, instance_id: str) -> None:
    """Log ONE plain watering (Gießkanne/manuell, 1 L, no fertilizer channel)."""
    watering_list.open()
    watering_list.click_create()
    assert watering_list.select_plant_by_text(instance_id), (
        f"TC-004-092 FAIL: could not select plant '{instance_id}' in the "
        f"watering-log dialog"
    )
    watering_list.select_application_method(DRENCH_OPTION_LABEL)
    watering_list.fill_volume(1)
    watering_list.select_water_source(TAP_LABEL)
    watering_list.submit_create_form()
    watering_list.wait_for_loading_complete()


# ── TC-004-092 ───────────────────────────────────────────────────────────────


class TestWateringCrossViewConsistency:
    """One WateringLog, coherent across global log, instance log and task history."""

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_single_watering_consistent_across_three_views(
        self,
        plant_creator: PlantInstanceListPage,
        watering_list: WateringLogListPage,
        plant_detail: PlantInstanceDetailPage,
        base_url: str,
        e2e_seed_data: dict,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-092: A single watering shows coherently in all three views.

        Spec: TC-004-092 -- Cross-View-Konsistenz eines Gießvorgangs (globales
        Gießprotokoll, Instanz-``#watering-log`` und ``#tasks``-Aufgabenverlauf
        mit Task-Abschluss + Folgeaufgabe).
        """
        # ── Arrange: self-provision plant + care profile + pending watering task ──
        key, instance_id = provision_plant(plant_creator, id_prefix="JOURNEY-004X")
        provision_watering_care_task(base_url, e2e_seed_data, key)
        screenshot(
            "TC-004-092_provisioned",
            f"Self-provisioned plant {instance_id} with a pending watering task",
        )

        # Baseline counts BEFORE the action (spec precondition).
        plant_detail.open_watering_log_tab(key)
        baseline_instance_logs = plant_detail.get_watering_log_row_count()

        plant_detail.open_tasks_tab(key)
        baseline_pending_watering = plant_detail.count_watering_tasks(
            plant_detail.TASK_ACTIVE_SECTION
        )
        baseline_completed_watering = plant_detail.count_watering_tasks(
            plant_detail.TASK_DONE_SECTION
        )
        baseline_summary = plant_detail.get_task_summary_counts()
        screenshot("TC-004-092_baseline-tasks", "Task history before the watering")
        assert baseline_pending_watering == 1, (
            "TC-004-092 FAIL: precondition expects exactly one pending "
            f"'— watering' task before the action, found {baseline_pending_watering}"
        )
        assert baseline_completed_watering == 0, (
            "TC-004-092 FAIL: precondition expects zero completed '— watering' "
            f"tasks before the action, found {baseline_completed_watering}"
        )

        # ── Act: log ONE plain watering for the plant ────────────────────────
        _log_plain_watering(watering_list, instance_id)
        screenshot("TC-004-092_watering-logged", f"Global log after watering {instance_id}")

        # ── View 1: global Gießprotokoll ─────────────────────────────────────
        watering_list.open()
        watering_list.search(instance_id)
        watering_list.wait_for_loading_complete()
        assert watering_list.get_row_count() == 1, (
            "TC-004-092 FAIL (View 1): expected exactly one global watering-log "
            f"row for '{instance_id}', found {watering_list.get_row_count()}"
        )
        view1_logged = watering_list.get_row_cell(0, "loggedAt")
        view1_method = watering_list.get_row_cell(0, "applicationMethod")
        view1_plants = watering_list.get_row_cell(0, "plants")
        screenshot("TC-004-092_view1-global", "View 1 — global watering log filtered to the plant")

        today = watering_list.get_browser_today()
        assert parse_de_date(view1_logged) == today, (
            "TC-004-092 FAIL (View 1): global-log timestamp is not today "
            f"(cell={view1_logged!r}, today={today})"
        )
        assert DRENCH_METHOD_LABEL in view1_method, (
            "TC-004-092 FAIL (View 1): expected application method "
            f"{DRENCH_METHOD_LABEL!r}, found {view1_method!r}"
        )
        assert instance_id in view1_plants, (
            "TC-004-092 FAIL (View 1): expected the plant chip to reference "
            f"'{instance_id}', found {view1_plants!r}"
        )

        # The spec demands a *linked* chip ("verlinkter Chip auf
        # /pflanzen/plant-instances/{key}"), not merely the id as text.
        expected_href = f"{PLANT_DETAIL_ROUTE}/{key}"
        view1_plant_links = watering_list.get_row_plant_links(0)
        assert any(href.endswith(expected_href) for _, href in view1_plant_links), (
            "TC-004-092 FAIL (View 1): the plant chip must be a link to "
            f"'{expected_href}', found {view1_plant_links!r}"
        )

        # ── View 2: instance Gießprotokoll (#watering-log) ───────────────────
        plant_detail.open_watering_log_tab(key)
        assert plant_detail.get_watering_log_row_count() == baseline_instance_logs + 1, (
            "TC-004-092 FAIL (View 2): instance watering-log row count should have "
            f"risen by exactly 1 (baseline {baseline_instance_logs}, now "
            f"{plant_detail.get_watering_log_row_count()})"
        )
        view2_logged = plant_detail.get_watering_log_row_cell(0, "loggedAt")
        view2_method = plant_detail.get_watering_log_row_cell(0, "applicationMethod")
        view2_volume = plant_detail.get_watering_log_row_cell(0, "volume")
        view2_supplemental = plant_detail.get_watering_log_row_cell(0, "isSupplemental")
        screenshot("TC-004-092_view2-instance", "View 2 — instance watering-log tab")

        assert parse_de_date(view2_logged) == today, (
            "TC-004-092 FAIL (View 2): instance-log timestamp is not today "
            f"(cell={view2_logged!r}, today={today})"
        )
        assert DRENCH_METHOD_LABEL in view2_method, (
            "TC-004-092 FAIL (View 2): expected application method "
            f"{DRENCH_METHOD_LABEL!r}, found {view2_method!r}"
        )
        assert view2_volume.strip().startswith("1") and "L" in view2_volume, (
            f"TC-004-092 FAIL (View 2): expected a '1 L' volume, found {view2_volume!r}"
        )
        assert view2_supplemental.strip() == "", (
            "TC-004-092 FAIL (View 2): the 'Ergänzend' column must be empty for a "
            f"plain watering, found {view2_supplemental!r}"
        )

        # Coherence: Views 1 and 2 render the SAME WateringLog (same day).
        assert parse_de_date(view1_logged) == parse_de_date(view2_logged), (
            "TC-004-092 FAIL (coherence): the global and instance logs disagree on "
            f"the watering date (View 1={view1_logged!r}, View 2={view2_logged!r})"
        )

        # ── View 3: Aufgabenverlauf (#tasks) ─────────────────────────────────
        plant_detail.open_tasks_tab(key)
        completed_watering = plant_detail.count_watering_tasks(
            plant_detail.TASK_DONE_SECTION
        )
        pending_watering = plant_detail.count_watering_tasks(
            plant_detail.TASK_ACTIVE_SECTION
        )
        completed_at = plant_detail.get_watering_task_cell(
            plant_detail.TASK_DONE_SECTION, "completed_at"
        )
        screenshot("TC-004-092_view3-tasks", "View 3 — task history after the watering")

        assert completed_watering == baseline_completed_watering + 1, (
            "TC-004-092 FAIL (View 3): the completed '— watering' task count should "
            f"have risen by exactly 1 (baseline {baseline_completed_watering}, now "
            f"{completed_watering}) — the open watering task must move to 'Abgeschlossen'"
        )
        assert parse_de_date(completed_at) == today, (
            "TC-004-092 FAIL (View 3): the completed watering task must carry "
            f"today's completion date (cell={completed_at!r}, today={today})"
        )
        assert pending_watering == 1, (
            "TC-004-092 FAIL (View 3): exactly one new pending '— watering' "
            f"follow-up task must exist, found {pending_watering}"
        )

        # The Overdue/Active/Done summary bar above the two tables must mirror
        # that very transition: one task moved into 'Abgeschlossen', and the
        # follow-up took the freed slot in 'Ausstehend'.
        summary = plant_detail.get_task_summary_counts()
        assert summary["done"] == baseline_summary["done"] + 1, (
            "TC-004-092 FAIL (View 3): the summary bar's Done count should have "
            f"risen by exactly 1 (baseline {baseline_summary['done']}, now "
            f"{summary['done']})"
        )
        assert summary["active"] == baseline_summary["active"], (
            "TC-004-092 FAIL (View 3): the summary bar's Active count must be "
            "unchanged — the completed watering task is replaced by its follow-up "
            f"(baseline {baseline_summary['active']}, now {summary['active']})"
        )
