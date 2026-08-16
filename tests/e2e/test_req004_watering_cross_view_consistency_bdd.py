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


def _day(context: dict[str, Any], page: BasePage, token: str) -> set[tuple[int, int, int]]:
    """Resolve a scenario's day *token* to the day(s) the assertion may accept.

    "Today" is read from the **browser**: browser and test runner can sit in
    different timezones in the containerised stack, and every date cell under
    assertion was rendered by the frontend, so the browser's notion of today is
    the only correct anchor. Any page object can answer it — the call is a
    page-object call, not driver access.

    **Anchored to the action, and a set rather than one day.** It used to read
    "today" lazily, on the first *Then* step — i.e. after the watering had been
    logged. A run that crossed midnight in between then compared a row written
    on one day against an anchor taken on the next, and failed:

        global-log timestamp of row 0 is not today
        (cell='15.08.2026, 23:59', expected=(16, 8, 2026))

    measured on the 2026-08-16 matrix, which ran 23:23Z–00:07Z.

    So the day is captured around the *action* (see ``record_plain_watering``),
    twice: before and after. Normally both reads agree and this returns a single
    day, so the assertion is exactly as strict as it was. They differ only when
    the action itself straddled 00:00 — and then the row legitimately carries
    either day, so asserting one of them would be asserting the clock, not the
    behaviour.
    """
    anchors = context.get("action_days")
    if not anchors:
        # No action-anchored capture (a step that runs before the action, or a
        # scenario that never acts): fall back to reading now, which is what the
        # old behaviour was for every caller.
        anchors = [page.get_browser_today()]
    return {resolve_day_token(token, anchor) for anchor in anchors}


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

    **At least, not exactly.** The precondition this journey needs is "there is an
    open watering task to complete"; the number of them is not the subject. It
    used to demand an exact count and failed the 2026-08-15 nightly with
    ``expected 1 … found 2``.

    The reason it cannot be exact: ``provision_watering_care_task`` materialises
    the task through ``POST /t/{slug}/tasks/generate-care-reminders``, which runs
    ``generate_due_care_reminders`` — the **daily producer**, for every plant it
    finds, not for this one. In light mode all four xdist workers share a single
    tenant, so another worker provisioning its own plant runs that producer over
    this plant too. A second qualifying reminder is therefore ordinary, not a
    defect, and its presence depends on scheduling.

    The sibling summary-bar step already knew this — it states a *gain* over a
    baseline for exactly the same reason ("a fresh care profile also materialises
    the other opted-in reminder types"). This step records the same kind of
    baseline; ``follow_up_watering_tasks_are_due`` is what consumes it.
    """
    at_least = int(count)
    plant_detail.open_tasks_tab(context["key"])
    pending = plant_detail.count_watering_tasks(plant_detail.TASK_ACTIVE_SECTION)
    if pending < at_least:
        raise RuntimeError(
            f"TC-004-092 SETUP: expected at least {at_least} pending '— watering' task(s) "
            f"before the action, found {pending} — the self-provisioned task did not "
            f"materialise, so there is nothing for the coupling to complete"
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
    """Log one watering with no fertilizer channel — the single action under test.

    Brackets the action with the browser's date, so the outcome steps compare the
    logged row against the day it was *written* on rather than the day the
    assertion happens to run on. Both reads normally agree; they differ only when
    the action straddles midnight, and ``_day`` widens to accept either only then.
    """
    volume = int(litres)
    watering_list.open()
    context["action_days"] = [watering_list.get_browser_today()]
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
    # The closing bracket. Equal to the opening read in every normal run; a
    # second, different day here is the only honest signal that the write itself
    # straddled 00:00, and it is what lets `_day` widen exactly then and never
    # otherwise.
    after = watering_list.get_browser_today()
    if after not in context["action_days"]:
        context["action_days"].append(after)
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
    # Not `wait_for_loading_complete()`: the DataTable filter is client-side
    # behind a 300 ms debounce, so no skeleton ever mounts and that poll returns
    # while the table still holds every watering log in the tenant (#835).
    watering_list.wait_for_search_applied(context["instance_id"], what="global watering log")

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
        assert parse_de_date(logged_at) in expected_day, (
            f"TC-004-092 FAIL (View 1): global-log timestamp of row {index} is not "
            f"{day} (cell={logged_at!r}, expected one of {sorted(expected_day)})"
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

        assert parse_de_date(logged_at) in expected_day, (
            f"TC-004-092 FAIL (View 2): instance-log timestamp of row {index} is not "
            f"{day} (cell={logged_at!r}, expected one of {sorted(expected_day)})"
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
    assert parse_de_date(completed_at) in expected_day, (
        f"TC-004-092 FAIL (View 3): the completed watering task must carry the "
        f"{day} completion date (cell={completed_at!r}, expected one of {sorted(expected_day)})"
    )


@then(parsers.re(r"(?P<count>\d+) follow-up watering tasks? (?:is|are) due"))
def follow_up_watering_tasks_are_due(
    count: str,
    context: dict[str, Any],
    plant_detail: PlantInstanceDetailPage,
) -> None:
    """View 3 — the coupling scheduled the next watering.

    Stated as a *balance*, not an absolute count, and for the same reason the
    summary-bar step below states a gain: the plant may legitimately carry more
    than one pending watering task, because the daily producer that materialises
    them runs tenant-wide and light mode shares one tenant across four xdist
    workers.

    What the coupling guarantees is the exchange: the completed task leaves the
    Active section and its follow-up takes the freed slot, so the pending count
    is **unchanged**. That is a stronger statement than "there is one", not a
    weaker one — it fails if the follow-up is never scheduled (count drops) and
    it fails if the completed task stays pending (count rises). An absolute
    ``== 1`` asserted neither of those; it asserted that nothing else in the
    tenant had happened.

    ``count`` is how many follow-ups the scenario expects the exchange to
    produce, which is what keeps this readable against the feature file.
    """
    expected_gain = int(count)
    baseline = context["baseline_pending"]
    pending = plant_detail.count_watering_tasks(plant_detail.TASK_ACTIVE_SECTION)
    assert pending == baseline, (
        f"TC-004-092 FAIL (View 3): completing a watering task must leave the pending "
        f"count unchanged — {expected_gain} follow-up task(s) replace the {expected_gain} "
        f"completed one(s) (baseline {baseline}, now {pending})"
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
