"""BDD binding for TC-004-092 — cross-view consistency of a single watering.

This module is the *step layer* of the BDD proof-of-concept (issue #761). It is
the only layer that knows both worlds: it binds the Gherkin steps of
``features/watering_cross_view_consistency.feature`` and translates each one
into calls on the existing page objects. Per
``spec/project/bdd-page-object-integration/`` it holds no user-interface
plumbing of its own — no selectors, no waits, no raw driver calls — and the
page objects it consumes know nothing about Gherkin in return. They are the
very same objects the classic implementation
(``test_req004_watering_cross_view_consistency.py``) drives, which is what
proves the decoupling rather than merely asserting it. The date parser, the
watering i18n labels and the three page-object fixtures are literally the same
objects too: they live in ``_journey_helpers`` and ``conftest`` and are shared
with the classic sibling, so the two flavours cannot drift apart (BDR-004).

**Reusability of the bindings.** Every count and every date in the scenario is a
step *parameter*, not a literal baked into the step text, so the same bindings
serve a REQ-004 case expecting two entries, or a date other than today, without
a single new step definition. That is the property the proof-of-concept has to
demonstrate, because the migration estimate for the remaining ~90 REQ-004 cases
stands or falls with it. Counts are matched as ``\\d+`` with an optional plural
``s`` (so both "1 watering" and "3 waterings" read naturally), and days are
symbolic tokens — ``today``/``yesterday``/``tomorrow`` or a literal German
``d.m.Y`` date — resolved by ``_journey_helpers.resolve_day_token`` against the
browser's own notion of today. The vocabulary stops there on purpose: a
scenario has to stay readable for a contributor who has never opened a Selenium
file, so this is a handful of named parameters, not a generic DSL.

The View-3 expected result "der Overdue/Active/Done-Summary-Balken spiegelt dies
wider" is asserted by the final ``Then``, in the same gain-over-baseline shape as
the steps around it: one task more in Done, an unchanged Active count. An
absolute pair of counts would be the wrong claim — a fresh care profile also
materialises the other opted-in reminder types (pest check, repotting), so the
plant carries more active tasks than the one ``— watering`` task this scenario
follows.

The module name is load-bearing: ``conftest.py`` derives the ``req004``
selection axis from the ``test_req<NNN>_*.py`` file name, and the module-level
``FEATURES`` tuple below opts into the semantic ``watering`` axis.
"""

from __future__ import annotations

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from ._journey_helpers import (
    DRENCH_METHOD_LABEL,
    DRENCH_OPTION_LABEL,
    TAP_LABEL,
    parse_de_date,
    provision_plant,
    provision_watering_care_task,
    resolve_day_token,
)
from .pages.base_page import BasePage
from .pages.plant_instance_detail_page import PlantInstanceDetailPage
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.watering_log_list_page import WateringLogListPage

# Feature-axis marker(s) for machine-selectable test identification
# (see conftest.py::KNOWN_FEATURE_MARKERS / pytest -m watering). Must sit after
# the last import so ruff's E402 stays satisfied.
FEATURES = ("watering",)

FEATURE_FILE = "features/watering_cross_view_consistency.feature"
SCENARIO_NAME = "A single watering is reflected consistently in every view"

# Route the linked plant chip must point at (spec: "verlinkter Chip auf
# /pflanzen/plant-instances/{key}").
PLANT_DETAIL_ROUTE = "/pflanzen/plant-instances"


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def context() -> dict[str, Any]:
    """Scenario-scoped state shared between step bindings.

    Keeping the state here rather than in module globals is what makes the
    scenario parallel-safe under xdist.
    """
    return {}


def _day(context: dict[str, Any], page: BasePage, token: str) -> tuple[int, int, int]:
    """Resolve a scenario's day *token* against the browser's today.

    "Today" is read from the browser once per scenario and cached in *context*:
    browser and test runner can sit in different timezones in the containerised
    stack, and every date cell under assertion was rendered by the frontend, so
    the browser's notion of today is the only correct anchor. Any page object
    can answer it — the call is a page-object call, not driver access.
    """
    if "today" not in context:
        context["today"] = page.get_browser_today()
    return resolve_day_token(token, context["today"])


# ── Scenario ─────────────────────────────────────────────────────────────────


@pytest.mark.smoke
@pytest.mark.core_crud
@scenario(FEATURE_FILE, SCENARIO_NAME)
def test_watering_is_consistent_across_views() -> None:
    """TC-004-092: A single watering shows coherently in all three views.

    Note: ``pytest-bdd`` overwrites this docstring at decoration time with
    ``"<feature>: <scenario>"``, so the TC-ID is carried by the ``@TC-004-092``
    Gherkin tag rather than lifted from here. The docstring is kept for the
    human reader of this module.
    """


# ── Given ────────────────────────────────────────────────────────────────────


@given("a plant whose care profile schedules watering tasks")
def plant_with_watering_care_profile(
    context: dict[str, Any],
    plant_creator: PlantInstanceListPage,
    plant_detail: PlantInstanceDetailPage,
    base_url: str,
    e2e_seed_data: dict,
) -> None:
    """Self-provision the plant and its care profile (NFR-008a: never skip).

    Also records the plant's watering-log row count as it stands *before* the
    action, so the outcome steps can express a *gain* rather than an absolute
    count — that is what lets them run against a plant with existing history.
    """
    key, instance_id = provision_plant(plant_creator, id_prefix="JOURNEY-004B")
    provision_watering_care_task(base_url, e2e_seed_data, key)
    context["key"] = key
    context["instance_id"] = instance_id

    plant_detail.open_watering_log_tab(key)
    context["baseline_instance_logs"] = plant_detail.get_watering_log_row_count()


@given(parsers.re(r"the plant has (?P<count>\d+) watering tasks? due"))
def plant_has_watering_tasks_due(
    count: str,
    context: dict[str, Any],
    plant_detail: PlantInstanceDetailPage,
) -> None:
    """Guard the pending-task precondition and record it as a baseline.

    A failure here is a *setup* failure, not an unmet expectation, so it raises
    explicitly instead of asserting — the behavioural assertions all live in the
    ``Then`` bindings, per ``spec/project/bdd-page-object-integration/``.

    While the tasks tab is open, the Overdue/Active/Done summary bar is recorded
    as well, so the outcome step can state a *gain* over the pre-action bar
    rather than an absolute count.
    """
    expected = int(count)
    plant_detail.open_tasks_tab(context["key"])
    pending = plant_detail.count_watering_tasks(plant_detail.TASK_ACTIVE_SECTION)
    if pending != expected:
        raise RuntimeError(
            f"TC-004-092 SETUP: expected {expected} pending '— watering' task(s) "
            f"before the action, found {pending}"
        )
    context["baseline_pending"] = pending
    context["baseline_summary"] = plant_detail.get_task_summary_counts()


@given(parsers.re(r"the plant has (?P<count>\d+) completed watering tasks?"))
def plant_has_completed_watering_tasks(
    count: str,
    context: dict[str, Any],
    plant_detail: PlantInstanceDetailPage,
) -> None:
    """Guard the completed-task precondition and record it as a baseline."""
    expected = int(count)
    plant_detail.open_tasks_tab(context["key"])
    completed = plant_detail.count_watering_tasks(plant_detail.TASK_DONE_SECTION)
    if completed != expected:
        raise RuntimeError(
            f"TC-004-092 SETUP: expected {expected} completed '— watering' task(s) "
            f"before the action, found {completed}"
        )
    context["baseline_completed"] = completed


# ── When ─────────────────────────────────────────────────────────────────────


@when(parsers.re(r"the gardener records a plain watering of (?P<litres>\d+) litres? for the plant"))
def record_plain_watering(
    litres: str,
    context: dict[str, Any],
    watering_list: WateringLogListPage,
) -> None:
    """Log one watering with no fertilizer channel — the single action under test."""
    volume = int(litres)
    watering_list.open()
    watering_list.click_create()
    if not watering_list.select_plant_by_text(context["instance_id"]):
        raise RuntimeError(
            f"TC-004-092 SETUP: could not select plant '{context['instance_id']}' "
            f"in the watering-log dialog"
        )
    watering_list.select_application_method(DRENCH_OPTION_LABEL)
    watering_list.fill_volume(volume)
    watering_list.select_water_source(TAP_LABEL)
    watering_list.submit_create_form()
    watering_list.wait_for_loading_complete()
    context["litres"] = volume


# ── Then ─────────────────────────────────────────────────────────────────────


@then(
    parsers.re(
        r"the tenant-wide watering log holds (?P<count>\d+) waterings? "
        r"for the plant, dated (?P<day>.+)"
    )
)
def global_log_holds_waterings(
    count: str,
    day: str,
    context: dict[str, Any],
    watering_list: WateringLogListPage,
) -> None:
    """View 1 — the tenant-wide ``/giessprotokoll`` list, filtered to the plant."""
    expected = int(count)
    watering_list.open()
    watering_list.search(context["instance_id"])
    watering_list.wait_for_loading_complete()

    row_count = watering_list.get_row_count()
    assert row_count == expected, (
        f"TC-004-092 FAIL (View 1): expected exactly {expected} global watering-log "
        f"row(s) for '{context['instance_id']}', found {row_count}"
    )

    expected_day = _day(context, watering_list, day)
    for index in range(expected):
        logged_at = watering_list.get_row_cell(index, "loggedAt")
        plants = watering_list.get_row_cell(index, "plants")
        if index == 0:
            context["view1_logged_at"] = logged_at
        assert parse_de_date(logged_at) == expected_day, (
            f"TC-004-092 FAIL (View 1): global-log timestamp of row {index} is not "
            f"{day} (cell={logged_at!r}, expected={expected_day})"
        )
        assert context["instance_id"] in plants, (
            f"TC-004-092 FAIL (View 1): expected the plant chip of row {index} to "
            f"reference '{context['instance_id']}', found {plants!r}"
        )


@then("that watering is recorded as a plain watering, with no fertilizer involved")
def global_log_shows_plain_watering(
    watering_list: WateringLogListPage,
) -> None:
    """View 1 — the application method identifies it as a plain watering."""
    method = watering_list.get_row_cell(0, "applicationMethod")
    assert DRENCH_METHOD_LABEL in method, (
        f"TC-004-092 FAIL (View 1): expected application method "
        f"{DRENCH_METHOD_LABEL!r}, found {method!r}"
    )


@then("that watering links back to the plant it was recorded for")
def global_log_chip_links_to_plant(
    context: dict[str, Any],
    watering_list: WateringLogListPage,
) -> None:
    """View 1 — the plant chip is a *link*, as the spec demands, not just text."""
    expected_href = f"{PLANT_DETAIL_ROUTE}/{context['key']}"
    links = watering_list.get_row_plant_links(0)
    assert any(href.endswith(expected_href) for _, href in links), (
        f"TC-004-092 FAIL (View 1): the plant chip must be a link to "
        f"'{expected_href}', found {links!r}"
    )


@then(
    parsers.re(
        r"the plant's own watering log has gained (?P<count>\d+) entr(?:y|ies) "
        r"of (?P<litres>\d+) litres?, dated (?P<day>.+)"
    )
)
def instance_log_gained_entries(
    count: str,
    litres: str,
    day: str,
    context: dict[str, Any],
    plant_detail: PlantInstanceDetailPage,
) -> None:
    """View 2 — the instance-scoped ``#watering-log`` tab."""
    gained = int(count)
    volume = int(litres)
    plant_detail.open_watering_log_tab(context["key"])

    row_count = plant_detail.get_watering_log_row_count()
    expected = context["baseline_instance_logs"] + gained
    assert row_count == expected, (
        f"TC-004-092 FAIL (View 2): instance watering-log row count should have "
        f"risen by exactly {gained} (baseline {context['baseline_instance_logs']}, "
        f"now {row_count})"
    )

    expected_day = _day(context, plant_detail, day)
    # Rows are newest-first, so the entries just gained are the top ``gained`` ones.
    for index in range(gained):
        logged_at = plant_detail.get_watering_log_row_cell(index, "loggedAt")
        method = plant_detail.get_watering_log_row_cell(index, "applicationMethod")
        cell_volume = plant_detail.get_watering_log_row_cell(index, "volume")
        supplemental = plant_detail.get_watering_log_row_cell(index, "isSupplemental")
        if index == 0:
            context["view2_logged_at"] = logged_at

        assert parse_de_date(logged_at) == expected_day, (
            f"TC-004-092 FAIL (View 2): instance-log timestamp of row {index} is not "
            f"{day} (cell={logged_at!r}, expected={expected_day})"
        )
        assert DRENCH_METHOD_LABEL in method, (
            f"TC-004-092 FAIL (View 2): expected application method "
            f"{DRENCH_METHOD_LABEL!r}, found {method!r}"
        )
        assert cell_volume.strip().startswith(str(volume)) and "L" in cell_volume, (
            f"TC-004-092 FAIL (View 2): expected a '{volume} L' volume, found {cell_volume!r}"
        )
        assert supplemental.strip() == "", (
            f"TC-004-092 FAIL (View 2): the 'Ergänzend' column must be empty for a "
            f"plain watering, found {supplemental!r}"
        )


@then("both watering logs agree on the day the plant was watered")
def both_logs_agree_on_the_day(context: dict[str, Any]) -> None:
    """Coherence — Views 1 and 2 render one and the same ``WateringLog``."""
    assert parse_de_date(context["view1_logged_at"]) == parse_de_date(context["view2_logged_at"]), (
        f"TC-004-092 FAIL (coherence): the global and instance logs disagree on the "
        f"watering date (View 1={context['view1_logged_at']!r}, "
        f"View 2={context['view2_logged_at']!r})"
    )


@then(parsers.re(r"(?P<count>\d+) watering tasks? (?:has|have) been completed, dated (?P<day>.+)"))
def watering_tasks_have_been_completed(
    count: str,
    day: str,
    context: dict[str, Any],
    plant_detail: PlantInstanceDetailPage,
) -> None:
    """View 3 — the ``#tasks`` history closed the task the watering satisfied."""
    gained = int(count)
    plant_detail.open_tasks_tab(context["key"])
    completed = plant_detail.count_watering_tasks(plant_detail.TASK_DONE_SECTION)
    completed_at = plant_detail.get_watering_task_cell(
        plant_detail.TASK_DONE_SECTION, "completed_at"
    )
    expected = context["baseline_completed"] + gained
    assert completed == expected, (
        f"TC-004-092 FAIL (View 3): the completed '— watering' task count should have "
        f"risen by exactly {gained} (baseline {context['baseline_completed']}, now "
        f"{completed}) — the open watering task must move to 'Abgeschlossen'"
    )
    expected_day = _day(context, plant_detail, day)
    assert parse_de_date(completed_at) == expected_day, (
        f"TC-004-092 FAIL (View 3): the completed watering task must carry the "
        f"{day} completion date (cell={completed_at!r}, expected={expected_day})"
    )


@then(parsers.re(r"(?P<count>\d+) follow-up watering tasks? (?:is|are) due"))
def follow_up_watering_tasks_are_due(
    count: str,
    context: dict[str, Any],
    plant_detail: PlantInstanceDetailPage,
) -> None:
    """View 3 — the coupling scheduled the next watering."""
    expected = int(count)
    pending = plant_detail.count_watering_tasks(plant_detail.TASK_ACTIVE_SECTION)
    assert pending == expected, (
        f"TC-004-092 FAIL (View 3): exactly {expected} new pending '— watering' "
        f"follow-up task(s) must exist, found {pending}"
    )


@then(
    parsers.re(
        r"the task summary bar reports (?P<count>\d+) more done tasks? "
        r"and as many active tasks as before"
    )
)
def task_summary_bar_reflects_the_transition(
    count: str,
    context: dict[str, Any],
    plant_detail: PlantInstanceDetailPage,
) -> None:
    """View 3 — the Overdue/Active/Done summary bar mirrors that same transition.

    Stated as a gain, not as an absolute pair of counts: a fresh care profile
    also materialises the other opted-in reminder types (pest check, repotting),
    so a plant legitimately carries more active tasks than the single
    ``— watering`` task this journey follows. What the bar must show is that one
    task moved into Done while the follow-up took the freed Active slot.
    """
    gained = int(count)
    summary = plant_detail.get_task_summary_counts()
    baseline = context["baseline_summary"]
    assert summary["done"] == baseline["done"] + gained, (
        f"TC-004-092 FAIL (View 3): the summary bar's Done count should have risen "
        f"by exactly {gained} (baseline {baseline['done']}, now {summary['done']})"
    )
    assert summary["active"] == baseline["active"], (
        f"TC-004-092 FAIL (View 3): the summary bar's Active count must be unchanged "
        f"— the completed watering task is replaced by its follow-up (baseline "
        f"{baseline['active']}, now {summary['active']})"
    )


# Note: the per-step screenshot checkpoint hook (``pytest_bdd_after_step``) lives
# in ``conftest.py``, not here. pytest-bdd's custom hooks are dispatched through
# pytest's plugin manager, which only collects hook implementations from
# registered plugins (conftest.py) — a same-named function defined in this
# module would never be registered and would silently never fire.
