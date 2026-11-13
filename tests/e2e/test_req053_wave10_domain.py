"""E2E of REQ-053 wave 10 part B - sown/thinned/failed slots, object tasks, trellis and tent hints (WP 10.14, #2835).

Spec pin REQ-053 v1.16 (§11.3 W-015, §9.5 W-005, R-7.2 W-008, §9.2a W-016.6, §12.1 W-007; Anhang A 60-63). Spec-TC
Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md, section 15):
  TC-053-109  ->  a planned row is recorded as sown ("Gesät"), thinned with the run's spacing (the species'     (§11.3
                  Steckbrief value) into exactly the count the server computes; the row is no longer sown,       W-015)
                  the plants stand in it, one "thinning" care event names them
  TC-053-110  ->  a sown row whose run has no spacing: the dialog asks for it (no default, E-10), refuses an      (§11.3
                  empty submit, takes the grower's count of seedlings left standing                              W-015, E-10)
  TC-053-111  ->  a died plant's slot is "Ausgefallen" with "Nachpflanzen" (a senesced one is not); the planting  (§11.3
                  dialog opens with that crop and its Steckbrief spacing; the died plant is no previous crop of  W-015,
                  the replant, its disease leaves a residual warning; the replant is planned                     #2888)
  TC-053-112  ->  "Aufgaben" on a compost heap: the object's own category list, no "for every plant", the new    (R-7.2
                  task listed and stored on the object; a trellis gets no task section                           W-008)
  TC-053-113  ->  trellis hint in the planting dialog: a species with support_required names the trellis in    (§9.5
                  the bed (with its height), says "none drawn" in a bed without one, and a species without        W-005)
                  the flag gets no hint
  TC-053-114  ->  tent with plants whose current phases ask for different photoperiods (from the phase          (§9.2a
                  profiles, saved as entered - #2857): the light-schedule hint names both groups; a tent with    W-016.6)
                  one photoperiod has none
  TC-053-115  ->  soil amendment "Kompost" recorded through "Pflege protokollieren" (no task) writes exactly one  (§12.1
                  feeding event for the bed's plant, shown on its feeding page; "Sand" writes none                W-007)

Agronomic values come from the catalogue, never from this file (G-W10 d): the thinning spacing is the lower bound of the
species' ``spacing_cm`` (the planting dialog's own prefill rule) and the count is the server's thinning plan; the
photoperiods are the ``photoperiod_hours`` of the requirement profiles of the species' phases. The only numbers typed
here are the grower's own observations (a count of seedlings left standing, an amount of compost).

Preconditions are self-provisioned through the application's own API, one fresh site per test with a UUID-derived name
(`_garden_plan_helpers.py`): beds, tents and garden objects through ``plan/batch``, slots and their reservation through
the slot and run routes, sowing through ``PUT /slots/{key}/sowing``, failed plants through ``POST …/remove`` and plants
in a phase through ``POST /plant-instances``. No shared fixture is mutated; nothing global is touched.

Waits are anchored on state - the planting tab's lists, a dialog's facts and its leaving the DOM, the task section's
settled list, the settled ``data-state`` of the trellis hint, the tent rules section - never on time. Every absence is
asserted after a positive anchor of the same render, and every stored outcome is read back from the server.
"""

from __future__ import annotations

import re

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._garden_plan_helpers import (
    BedSpec,
    ObjectSpec,
    care_events,
    create_plant_in_phase,
    enter_phase_photoperiods,
    lower_bound_cm,
    object_tasks,
    phase_photoperiods,
    plant_feeding_events,
    plant_on_positions,
    plantings,
    polyline,
    provision_garden,
    rect,
    remove_plant,
    reserved_row,
    sow_slot,
    species,
    stored_slot,
    tenant_get,
    thinning_plan,
    unique_tag,
    utc_today,
)
from .pages.bed_care_page import BedCareTab
from .pages.bed_view_page import BedViewPage
from .pages.feeding_event_detail_page import FeedingEventDetailPage
from .pages.garden_plan_workspace_page import WorkspacePlanPage

pytestmark = pytest.mark.requires_desktop

CARROT = "Daucus carota"
LETTUCE = "Lactuca sativa"
PEA = "Pisum sativum"
HEMP = "Cannabis sativa"

#: One bed of 3 x 1,2 m in the 10 x 10 m garden; its rows run along the 3 m side.
BED = rect(1.0, 1.0, 3.0, 1.2)
#: A sown row 1,0 m long in the middle of the bed (bed frame).
ROW = ((0.5, 0.6), (1.5, 0.6))
#: The categories a task on a compost, water source or storage object offers (REQ-053 R-7.2, W-008), in order.
OBJECT_TASK_CATEGORIES = ["maintenance", "cleaning", "observation", "covering", "uncovering"]
#: The young phases that take no part in the tent's photoperiod check (``phase_role_map.YOUNG_PHASE_NAMES``).
YOUNG_PHASES = frozenset(
    {
        "germination",
        "seedling",
        "rooting",
        "establishment",
        "pup_establishment",
        "bulbil_establishment",
    }
)


@pytest.fixture
def bed_view(browser: WebDriver, base_url: str) -> BedViewPage:
    return BedViewPage(browser, base_url)


@pytest.fixture
def care_tab(browser: WebDriver, base_url: str) -> BedCareTab:
    return BedCareTab(browser, base_url)


@pytest.fixture
def plan(browser: WebDriver, base_url: str) -> WorkspacePlanPage:
    return WorkspacePlanPage(browser, base_url)


def _steckbrief_spacing(entry: dict) -> float:
    """The lower bound of the species' ``spacing_cm`` - loud when the catalogue has none (a precondition, not a value)."""
    value = lower_bound_cm(entry.get("spacing_cm"))
    if value is None:
        raise AssertionError(
            f"precondition: the catalogue entry {entry.get('scientific_name')!r} has no spacing_cm "
            f"({entry.get('spacing_cm')!r}) - the case needs a Steckbrief spacing"
        )
    return value


def _cm_text(value: float) -> str:
    """How the dialogs print a centimetre value they took over (``String(5)`` -> ``"5"``, ``7.5`` -> ``"7.5"``)."""
    return f"{value:g}"


def _hours_de(value: float) -> str:
    """A photoperiod as the German UI prints it (``18`` / ``12,5``)."""
    return f"{value:g}".replace(".", ",")


def _active_on(base_url: str, seed: dict, bed_key: str, slot_key: str) -> list[dict]:
    return [
        item
        for item in plantings(base_url, seed, bed_key, "active")
        if item.get("slot_key") == slot_key
    ]


# ── TC-053-109 ──────────────────────────────────────────────────────────────


def test_tc_053_109_sow_a_row_and_thin_it_into_the_count_the_server_computes(
    bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-109 - planned row -> "Als gesät erfassen" -> "Gesät" -> "Vereinzeln" with the run's spacing -> plants.

    Precondition (API): Beet 1 (3 x 1,2 m) with a row slot 1,0 m long, reserved by a planned carrot run whose spacing
    after thinning is the species' Steckbrief value. Breaks if the planned row offers no sowing, the sowing is not
    stored for today, the row is not listed as sown, the thinning dialog does not take the run's spacing or shows
    another count than the server's plan, the thinning does not create exactly that many plants in the row, leaves the
    row sown, or logs no single "thinning" event naming them (§11.3, W-015).
    """
    carrot = species(base_url, e2e_seed_data, CARROT)
    spacing = _steckbrief_spacing(carrot)
    garden = provision_garden(
        base_url, e2e_seed_data, purpose="tc109", beds=(BedSpec("Beet 1", BED),)
    )
    bed = garden.bed_key("Beet 1")
    row = reserved_row(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=carrot["key"],
        id_prefix="MOE",
        points=ROW,
        thinning_to_cm=spacing,
    )

    bed_view.open(bed, "planting")
    bed_view.wait_for_slot_lists(
        row.slot_key, planned=True, sown=False, failed=False, what="TC-053-109: the reserved row"
    )
    assert bed_view.has_row_action(f"planting-sow-{row.slot_key}"), (
        "TC-053-109: a planned row must offer 'Als gesät erfassen'"
    )
    screenshot("053_109_01_planned_row", "Geplante Reihe mit „Als gesät erfassen“")

    sowing = bed_view.open_sowing_dialog(row.slot_key)
    today = utc_today().isoformat()
    assert sowing.date_value() == today, (
        f"TC-053-109: the sowing day starts at today ({today}): {sowing.date_value()!r}"
    )
    sowing.submit_and_wait_closed("TC-053-109: sowing")
    bed_view.wait_for_slot_lists(
        row.slot_key, planned=False, sown=True, failed=False, what="TC-053-109: after sowing"
    )
    sown_text = bed_view.row_text(f"planting-sown-{row.slot_key}")
    assert row.slot_id in sown_text and "gesät am" in sown_text, (
        f"TC-053-109: the sown row names its slot and 'gesät am …': {sown_text!r}"
    )
    assert stored_slot(base_url, e2e_seed_data, bed, row.slot_key).get("sown_at") == today, (
        "TC-053-109: the server must store today as the sowing day"
    )
    screenshot("053_109_02_sown", "Reihe unter „Gesät (1)“ mit „Vereinzeln“")

    server_plan = thinning_plan(base_url, e2e_seed_data, row.slot_key)
    assert server_plan.get("thinning_to_cm") == spacing, (
        f"TC-053-109: the server's plan takes the run's spacing {spacing}: {server_plan!r}"
    )
    expected = server_plan.get("suggested_count")
    assert isinstance(expected, int) and expected >= 1, (
        f"TC-053-109: the server suggests a plant count: {server_plan!r}"
    )

    thinning = bed_view.open_thinning_dialog(row.slot_key)
    assert thinning.spacing_value() == _cm_text(spacing), (
        f"TC-053-109: the spacing field takes the run's {spacing} cm: {thinning.spacing_value()!r}"
    )
    assert not thinning.has(thinning.NO_SPACING), (
        "TC-053-109: with a spacing on the run the dialog must not ask for one"
    )
    facts = thinning.facts_text()
    assert "Gesät am" in facts and "Reihenlänge" in facts, (
        f"TC-053-109: the facts name the sowing day and the row length: {facts!r}"
    )
    shown = thinning.result_count("TC-053-109: the thinning result")
    assert shown == expected, (
        f"TC-053-109: the dialog's count ({shown}) must be the server's plan ({expected})"
    )
    screenshot(
        "053_109_03_thinning",
        f"Vereinzeln: Abstand {spacing:g} cm aus dem Anbauplan, {shown} Pflanzen",
    )

    thinning.submit_and_wait_closed("TC-053-109: thinning")
    bed_view.wait_for_slot_lists(
        row.slot_key, planned=False, sown=False, failed=False, what="TC-053-109: after thinning"
    )
    bed_view.wait_for_planting_lists(0, expected, "TC-053-109: the thinned plants are in the bed")
    screenshot("053_109_04_plants", f"„Im Beet ({expected})“, keine gesäte Reihe mehr")

    standing = _active_on(base_url, e2e_seed_data, bed, row.slot_key)
    assert len(standing) == expected, (
        f"TC-053-109: {expected} plants should stand in the row, the server lists {len(standing)}"
    )
    assert {item["species_key"] for item in standing} == {carrot["key"]}, (
        f"TC-053-109: the plants are the run's carrots: {standing!r}"
    )
    assert stored_slot(base_url, e2e_seed_data, bed, row.slot_key).get("sown_at") is None, (
        "TC-053-109: a thinned row is no longer sown"
    )
    thinned = care_events(base_url, e2e_seed_data, bed, category="thinning")
    assert len(thinned) == 1, f"TC-053-109: exactly one thinning event: {thinned!r}"
    assert sorted(thinned[0].get("plant_keys") or []) == sorted(i["plant_key"] for i in standing), (
        f"TC-053-109: the thinning event names exactly the new plants: {thinned[0]!r}"
    )


# ── TC-053-110 ──────────────────────────────────────────────────────────────


def test_tc_053_110_thinning_without_a_spacing_asks_and_takes_the_growers_count(
    bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-110 - a sown row whose run has no spacing: hint, no prefill, empty submit refused, grower's count taken.

    Precondition (API): a sown row (sowing day today) reserved by a carrot run without ``thinning_to_cm`` - the state
    the planting dialog leaves behind, which has no field for it. Breaks if the dialog invents a spacing or a count,
    closes on an empty submit, or stores another number of plants than the grower typed (E-10, W-015).
    """
    carrot = species(base_url, e2e_seed_data, CARROT)
    garden = provision_garden(
        base_url, e2e_seed_data, purpose="tc110", beds=(BedSpec("Beet 1", BED),)
    )
    bed = garden.bed_key("Beet 1")
    row = reserved_row(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=carrot["key"],
        id_prefix="MOE",
        points=ROW,
        thinning_to_cm=None,
    )
    sow_slot(base_url, e2e_seed_data, row.slot_key, utc_today())
    server_plan = thinning_plan(base_url, e2e_seed_data, row.slot_key)
    assert (server_plan.get("thinning_to_cm"), server_plan.get("suggested_count")) == (
        None,
        None,
    ), f"precondition: the run has no spacing, so the server suggests no count: {server_plan!r}"

    bed_view.open(bed, "planting")
    bed_view.wait_for_slot_lists(
        row.slot_key, planned=False, sown=True, failed=False, what="TC-053-110: the sown row"
    )
    thinning = bed_view.open_thinning_dialog(row.slot_key)
    assert thinning.has(thinning.NO_SPACING), (
        "TC-053-110: without a spacing on the run the dialog must say so"
    )
    assert thinning.spacing_value() == "", (
        f"TC-053-110: no spacing may be pre-filled (E-10): {thinning.spacing_value()!r}"
    )
    assert not thinning.has(thinning.RESULT), (
        "TC-053-110: without a spacing or count there is no plant count to show"
    )
    warning = thinning.submit_expecting_missing("TC-053-110: empty submit")
    assert "Abstand" in warning and "Anzahl" in warning, (
        f"TC-053-110: the warning asks for the spacing or the count: {warning!r}"
    )
    assert stored_slot(base_url, e2e_seed_data, bed, row.slot_key).get("sown_at") == (
        utc_today().isoformat()
    ), "TC-053-110: the refused submit must leave the row sown"
    assert _active_on(base_url, e2e_seed_data, bed, row.slot_key) == [], (
        "TC-053-110: the refused submit must create no plant"
    )
    screenshot(
        "053_110_01_no_spacing", "Vereinzeln ohne Abstand: Hinweis und Warnung, nichts vorbelegt"
    )

    left_standing = 3
    thinning.set_count(left_standing)
    assert thinning.result_count("TC-053-110: the typed count") == left_standing, (
        "TC-053-110: the result line takes the grower's count"
    )
    screenshot("053_110_02_count", "Anzahl stehen gebliebener Pflanzen: 3")
    thinning.submit_and_wait_closed("TC-053-110: thinning with a count")
    bed_view.wait_for_planting_lists(
        0, left_standing, "TC-053-110: the grower's plants are in the bed"
    )

    standing = _active_on(base_url, e2e_seed_data, bed, row.slot_key)
    assert len(standing) == left_standing, (
        f"TC-053-110: exactly {left_standing} plants stand in the row: {len(standing)}"
    )
    assert stored_slot(base_url, e2e_seed_data, bed, row.slot_key).get("sown_at") is None, (
        "TC-053-110: a thinned row is no longer sown"
    )


# ── TC-053-111 ──────────────────────────────────────────────────────────────


def test_tc_053_111_failed_slot_offers_a_replant_with_the_same_crop(
    bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-111 - a died plant leaves its slot "Ausgefallen"; "Nachpflanzen" opens the dialog with that crop.

    Precondition (API): a lettuce and a carrot on two positions of Beet 1; the lettuce removed as died from a disease,
    the carrot as senesced (the natural end of an annual, another family - so no second lettuce of this year stands in
    the history). Breaks if the died one is not listed under "Ausgefallen", the senesced one is, the dialog opens
    without the crop or without its Steckbrief spacing, the replant meets the same-year rotation hint against the
    lettuce it replaces, the residual disease warning is missing, or the replant is not planned as that crop
    (§11.3 "ausgefallen", W-015, #2888).
    """
    lettuce = species(base_url, e2e_seed_data, LETTUCE)
    carrot = species(base_url, e2e_seed_data, CARROT)
    spacing = _steckbrief_spacing(lettuce)
    garden = provision_garden(
        base_url, e2e_seed_data, purpose="tc111", beds=(BedSpec("Beet 1", BED),)
    )
    bed = garden.bed_key("Beet 1")
    lettuce_planted = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=lettuce["key"],
        id_prefix="SAL",
        points=((0.5, 0.6),),
    )
    carrot_planted = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=carrot["key"],
        id_prefix="MOE",
        points=((2.5, 0.6),),
    )
    (died_slot,) = lettuce_planted.point_slots
    (senesced_slot,) = carrot_planted.point_slots
    remove_plant(base_url, e2e_seed_data, lettuce_planted.plant_on(died_slot), "died", "disease")
    remove_plant(base_url, e2e_seed_data, carrot_planted.plant_on(senesced_slot), "senesced")

    bed_view.open(bed, "planting")
    bed_view.wait_for_slot_lists(
        died_slot, planned=False, sown=False, failed=True, what="TC-053-111: the died plant's slot"
    )
    assert senesced_slot not in bed_view.failed_slot_keys(), (
        "TC-053-111: a senesced plant ended its natural life and is no failure to make good"
    )
    failed_text = bed_view.row_text(f"planting-failed-{died_slot}")
    assert "ausgefallen am" in failed_text, (
        f"TC-053-111: the failed row names the day of the loss: {failed_text!r}"
    )
    screenshot("053_111_01_failed", "„Ausgefallen (1)“ mit „Nachpflanzen“")

    dialog = bed_view.open_replant_dialog(died_slot)
    chosen = dialog.wait_for_species_value(f"({LETTUCE})", "TC-053-111: the replant crop")
    assert dialog.field_value("spacing") == _cm_text(spacing), (
        f"TC-053-111: the spacing is the Steckbrief's {spacing} cm: {dialog.field_value('spacing')!r}"
    )
    screenshot("053_111_02_replant_dialog", f"Bepflanzen vorbelegt: {chosen}")
    # The replant names the lettuce it replaces (#2888): that lettuce is no previous crop, so no same-year rotation
    # hint against it. Its disease leaves a residual warning - the cause may sit in the soil.
    severity, rotation = dialog.wait_for_hint(
        lettuce["key"], "TC-053-111: the replant's rotation hint"
    )
    assert "in diesem Jahr schon in diesem Beet" not in rotation, (
        f"TC-053-111: the replant meets no rotation hint against the plant it replaces: {rotation!r}"
    )
    assert severity == "warning" and "an einer Krankheit eingegangen" in rotation, (
        f"TC-053-111: the disease of the replaced plant leaves a residual warning: {severity!r}, {rotation!r}"
    )
    dialog.choose_layout("rows")
    dialog.set_count(2)
    dialog.wait_for_server_preview(2, "TC-053-111: two lettuces as the replant")
    dialog.check_plant_anyway()
    dialog.set_reason("Nachpflanzung für den ausgefallenen Salat")
    dialog.submit_and_wait_closed("TC-053-111: replant")
    bed_view.wait_for_planting_lists(2, 0, "TC-053-111: the replant is planned")

    planned = plantings(base_url, e2e_seed_data, bed, "planned")
    assert len(planned) == 2 and {item["species_key"] for item in planned} == {lettuce["key"]}, (
        f"TC-053-111: the replant plans two positions of the failed crop: {planned!r}"
    )


# ── TC-053-112 ──────────────────────────────────────────────────────────────


def test_tc_053_112_task_on_a_compost_heap_from_the_properties_panel(
    plan: WorkspacePlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-112 - "Aufgaben" of a compost heap: object categories, no plant scope, the task listed and stored.

    Breaks if the compost's section is missing or not empty at first, the dialog is not bound to the object, offers
    another category list or the "for every plant" scope, the new task is not listed or not stored on the object, or a
    trellis gets a task section (R-7.2, W-008).
    """
    tag = unique_tag()
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc112",
        objects=(
            ObjectSpec("Komposthaufen", "compost", rect(7.0, 7.0, 1.0, 1.0)),
            ObjectSpec(
                "Rankgitter",
                "trellis",
                polyline([(6.0, 2.0), (8.0, 2.0)], 0.1),
                props={"height_m": 1.8},
            ),
        ),
    )
    compost, trellis = garden.objects["Komposthaufen"], garden.objects["Rankgitter"]
    plan.open(garden.site_key)

    plan.select_with_keyboard(compost)
    state = plan.wait_for_object_tasks("compost", "TC-053-112: the compost's task section")
    assert state == "empty", (
        f"TC-053-112: a new compost heap has no open task, the section shows {state!r}"
    )
    screenshot("053_112_01_section", "Kompost ausgewählt: Abschnitt „Aufgaben“, keine offen")

    plan.open_object_task_dialog()
    title = plan.task_dialog_title()
    assert "Komposthaufen" in title, f"TC-053-112: the dialog names the object: {title!r}"
    categories = plan.task_dialog_categories()
    assert categories == OBJECT_TASK_CATEGORIES, (
        f"TC-053-112: the object's categories are {OBJECT_TASK_CATEGORIES}, offered {categories}"
    )
    assert not plan.task_dialog_has_scope_choice(), (
        "TC-053-112: a task on an object has no 'Gilt für' (bed / every plant)"
    )
    hint = plan.task_dialog_object_hint()
    assert hint.startswith("Die Aufgabe gilt für dieses Objekt"), (
        f"TC-053-112: the object hint: {hint!r}"
    )
    # No checkpoint while the dialog is open: the full-page capture resizes the layout viewport, the side panel
    # remounts across its breakpoint and takes the dialog (state of the panel's task section) with it - see the TC.

    name = f"Kompost umsetzen {tag}"
    task_key = plan.submit_object_task("maintenance", name, "TC-053-112: creating the task")
    rows = plan.object_task_rows()
    assert list(rows) == [task_key] and name in rows[task_key], (
        f"TC-053-112: the section lists exactly the new task: {rows!r}"
    )
    screenshot("053_112_03_listed", "Aufgabe „Kompost umsetzen“ im Abschnitt gelistet")

    stored = object_tasks(base_url, e2e_seed_data, compost)
    assert [(t["key"], t["category"], t["entity_type"], t["entity_key"]) for t in stored] == [
        (task_key, "maintenance", "garden_object", compost)
    ], f"TC-053-112: the server holds the one task on the compost heap: {stored!r}"

    # The section's chunk is loaded by now (the compost showed it), so its absence below is no loading race.
    plan.select_with_keyboard(trellis)
    plan.wait_for_object_props("trellis", "TC-053-112: the trellis' properties")
    assert not plan.has_object_tasks_section(), "TC-053-112: a trellis takes no tasks (no section)"


# ── TC-053-113 ──────────────────────────────────────────────────────────────


def test_tc_053_113_trellis_hint_in_the_planting_dialog(
    bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-113 - pea (``support_required``) names the trellis in Beet A, says "none drawn" in Beet B; carrot: no hint.

    Breaks if the hint of a species that needs a support is missing, names another trellis or not its height, does not
    say that Beet B has none, or appears for a species without the flag (§9.5, W-005, G-W10 d) - or if the hint names
    the pea in English in the German UI ("Pea", the first entry of ``common_names``) instead of "Erbse" (#2902).
    """
    pea = species(base_url, e2e_seed_data, PEA)
    carrot = species(base_url, e2e_seed_data, CARROT)
    assert (pea.get("support_required"), carrot.get("support_required")) == (True, False), (
        "precondition: the catalogue says the pea needs a support and the carrot does not: "
        f"{pea.get('support_required')!r}, {carrot.get('support_required')!r}"
    )
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc113",
        beds=(BedSpec("Beet A", BED), BedSpec("Beet B", rect(1.0, 5.0, 3.0, 1.2))),
        objects=(
            # Along the north half of Beet A, inside its outline.
            ObjectSpec(
                "Erbsenzaun",
                "trellis",
                polyline([(1.2, 1.9), (3.8, 1.9)], 0.1),
                props={"height_m": 1.8},
            ),
        ),
    )
    bed_a, bed_b = garden.bed_key("Beet A"), garden.bed_key("Beet B")
    fence = garden.objects["Erbsenzaun"]

    bed_view.open(bed_a, "planting")
    dialog = bed_view.open_planting_dialog()
    dialog.choose_species(PEA)
    hint = dialog.wait_for_support_hint(pea["key"], "TC-053-113: the pea in Beet A")
    assert (hint["state"], hint["count"]) == ("present", "1"), (
        f"TC-053-113: Beet A has one trellis: {hint!r}"
    )
    assert list(hint["trellises"]) == [fence], f"TC-053-113: the hint names the fence: {hint!r}"
    assert "Erbsenzaun" in hint["trellises"][fence] and "1,8 m hoch" in hint["trellises"][fence], (
        f"TC-053-113: the trellis line names its label and height: {hint['trellises'][fence]!r}"
    )
    # #2902: the species is named in the UI language (common_names_i18n.de), never by the first list entry, which
    # the seed spells in English ("Pea").
    assert hint["text"].startswith("Erbse") and not re.search(r"\bPea\b", hint["text"]), (
        f"TC-053-113: the hint names the pea in German: {hint['text']!r}"
    )
    screenshot("053_113_01_present", "Erbse in Beet A: Rankhilfe „Erbsenzaun (1,8 m hoch)“")

    dialog.choose_species(CARROT)
    dialog.wait_for_hint(carrot["key"], "TC-053-113: the carrot's hint block")
    assert not dialog.has_support_hint(carrot["key"]), (
        "TC-053-113: a species without support_required gets no trellis hint"
    )
    screenshot("053_113_02_carrot", "Möhre: kein Rankhilfe-Hinweis")

    bed_view.open(bed_b, "planting")
    dialog = bed_view.open_planting_dialog()
    dialog.choose_species(PEA)
    hint = dialog.wait_for_support_hint(pea["key"], "TC-053-113: the pea in Beet B")
    assert (hint["state"], hint["count"], hint["trellises"]) == ("missing", "0", {}), (
        f"TC-053-113: Beet B has no trellis: {hint!r}"
    )
    assert (
        "keine eingezeichnet" in hint["text"] and "Pflanzen kannst du trotzdem" in hint["text"]
    ), f"TC-053-113: the hint says none is drawn and does not block: {hint['text']!r}"
    screenshot("053_113_03_missing", "Erbse in Beet B: keine Rankhilfe eingezeichnet")


# ── TC-053-114 ──────────────────────────────────────────────────────────────


def test_tc_053_114_tent_photoperiod_conflict_hint_from_the_phase_profiles(
    bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-114 - two plants under one lamp whose current phases ask for different photoperiods: the hint says so.

    The phases and their photoperiods come from the catalogue: the light-triggered phases (no young phase) of the hemp
    lifecycle with the longest and the shortest ``photoperiod_hours``. Only a sourced light duration forms a group
    (#2857), and hemp's phases come from the generic phase template, so both profiles are first saved unchanged
    through the profile editor's route (the platform admin's ``PUT``), which stores them as entered. Tent A holds one
    plant in each, tent B two plants in the longest one. Breaks if tent A shows no conflict hint, the hint does not name both photoperiods with their
    phase by its German catalogue name (#2889), or tent B shows one (§9.2a, W-016.6, V-23 - a hint, never an error).
    """
    hemp = species(base_url, e2e_seed_data, HEMP)
    phases = [
        p
        for p in phase_photoperiods(base_url, e2e_seed_data, hemp["key"])
        if p.name not in YOUNG_PHASES
    ]
    longest = max(phases, key=lambda p: p.photoperiod_hours, default=None)
    shortest = min(phases, key=lambda p: p.photoperiod_hours, default=None)
    assert longest is not None and shortest is not None, (
        f"precondition: the hemp lifecycle has light-triggered phases with a photoperiod: {phases!r}"
    )
    assert longest.photoperiod_hours - shortest.photoperiod_hours >= 1.0, (
        f"precondition: two phases at least one hour apart (the hint's tolerance): {longest!r}, {shortest!r}"
    )
    for phase in (longest, shortest):
        # #2889: the hint must word the phase by the catalogue's German name; only one that differs from the English
        # name can tell the two apart (seed: "Vegetative Phase" / "Blüte").
        assert phase.display_name_de and phase.display_name_de != phase.display_name, (
            f"precondition: the phase has a German name of its own in the catalogue: {phase!r}"
        )
    # #2857: only a light duration from a Steckbrief or entered by a person forms a group. Hemp's phases come from the
    # generic phase template (`generated`); saving both profiles, as the profile editor does, makes them `sourced`.
    enter_phase_photoperiods(base_url, e2e_seed_data, hemp["key"], {longest.name, shortest.name})
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc114",
        site_type="indoor",
        boundary=rect(0.0, 0.0, 6.0, 4.0),
        beds=(
            BedSpec("Zelt A", rect(0.5, 0.5, 1.2, 1.2), location_type_key="tent"),
            BedSpec("Zelt B", rect(3.0, 0.5, 1.2, 1.2), location_type_key="tent"),
        ),
    )
    tent_a, tent_b = garden.bed_key("Zelt A"), garden.bed_key("Zelt B")
    for location, phase, name in (
        (tent_a, longest, "Hanf lang"),
        (tent_a, shortest, "Hanf kurz"),
        (tent_b, longest, "Hanf B1"),
        (tent_b, longest, "Hanf B2"),
    ):
        create_plant_in_phase(
            base_url,
            e2e_seed_data,
            site_key=garden.site_key,
            location_key=location,
            species_key=hemp["key"],
            phase_key=phase.key,
            name=f"{name} {unique_tag()}",
        )

    bed_view.open_tent_rules(tent_a)
    text = bed_view.photoperiod_conflict_text("TC-053-114: tent A")
    for phase in (longest, shortest):
        # The phase in brackets is its German catalogue name, never the English one (#2889).
        fragment = f"{_hours_de(phase.photoperiod_hours)} Stunden Licht für 1 Pflanze ({phase.display_name_de})"
        assert fragment in text, f"TC-053-114: the hint names {fragment!r}: {text!r}"
        assert f"({phase.display_name})" not in text, (
            f"TC-053-114: the hint names the phase in English ({phase.display_name!r}): {text!r}"
        )
    assert text.startswith("Unterschiedlicher Lichtbedarf unter einer Lampe"), (
        f"TC-053-114: the hint's title: {text!r}"
    )
    screenshot(
        "053_114_01_conflict", "Zelt A: Hinweis „Unterschiedlicher Lichtbedarf unter einer Lampe“"
    )

    bed_view.open_tent_rules(tent_b)
    assert bed_view.tent_hint_ids() == set(), (
        "TC-053-114: two plants with one photoperiod need no light-schedule hint"
    )
    screenshot("053_114_02_no_conflict", "Zelt B: gleiche Lichtdauer, kein Hinweis")


# ── TC-053-115 ──────────────────────────────────────────────────────────────


def test_tc_053_115_compost_through_the_care_log_writes_one_feeding_event(
    bed_view: BedViewPage,
    care_tab: BedCareTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-115 - "Pflege protokollieren": compost as soil amendment writes one feeding event; sand writes none.

    Precondition (API): one lettuce plant in Beet 1 without any feeding event. Breaks if the compost entry stores no
    feeding event, more than one, one that its care line does not point at, one not attributed to the plant or not a
    top dress, or if the sand entry (no nutrient amendment) stores one (§12.1, W-007; the same feeding event as the task
    completion of TC-053-064).
    """
    lettuce = species(base_url, e2e_seed_data, LETTUCE)
    garden = provision_garden(
        base_url, e2e_seed_data, purpose="tc115", beds=(BedSpec("Beet 1", BED),)
    )
    bed = garden.bed_key("Beet 1")
    planted = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=lettuce["key"],
        id_prefix="SAL",
        points=((1.5, 0.6),),
    )
    plant = planted.plant_on(planted.point_slots[0])
    assert plant_feeding_events(base_url, e2e_seed_data, plant) == [], (
        "precondition: the new plant has no feeding event"
    )

    bed_view.open(bed, "care")
    log = care_tab.open_care_log()
    log.choose_category("soil_amendment")
    log.choose_material("Kompost")
    log.set_quantity_only("2")
    log.set_unit("l")
    screenshot("053_115_01_compost", "Pflege protokollieren: Bodenverbesserung, Kompost, 2 Liter")
    log.submit_and_wait_closed("TC-053-115: compost by the care log")

    events = care_events(base_url, e2e_seed_data, bed, category="soil_amendment")
    assert len(events) == 1 and events[0].get("material") == "compost", (
        f"TC-053-115: one compost line in the care log: {events!r}"
    )
    reference = events[0].get("source_ref") or {}
    assert reference.get("collection") == "feeding_events" and reference.get("key"), (
        f"TC-053-115: the care line points at its feeding event: {events[0]!r}"
    )
    feedings = plant_feeding_events(base_url, e2e_seed_data, plant)
    assert [(f["key"], f["application_method"]) for f in feedings] == [
        (reference["key"], "top_dress")
    ], f"TC-053-115: exactly the referenced top dress names the plant: {feedings!r}"

    # The page names the plant by its label since #2920 - instance id plus the species name in the UI language,
    # taken from the API's language map (#2902), never the raw key.
    instance_id = tenant_get(base_url, e2e_seed_data, f"/plant-instances/{plant}")["instance_id"]
    plant_label = f"{instance_id} ({lettuce['common_names_i18n']['de'][0]})"
    detail = FeedingEventDetailPage(bed_view.driver, base_url).open(reference["key"])
    facts = detail.facts()
    assert (facts.get("Pflanze"), facts.get("Anwendungsart")) == (plant_label, "Aufstreuen"), (
        f"TC-053-115: the feeding page shows the plant and 'Aufstreuen': {facts!r}"
    )
    screenshot(
        "053_115_02_feeding_event",
        "Düngeereignis aus dem Pflegeeintrag: Aufstreuen, Pflanze im Beet",
    )

    bed_view.open(bed, "care")
    log = care_tab.open_care_log()
    log.choose_category("soil_amendment")
    log.choose_material("Sand")
    log.set_quantity_only("5")
    log.set_unit("l")
    log.submit_and_wait_closed("TC-053-115: sand by the care log")

    events = care_events(base_url, e2e_seed_data, bed, category="soil_amendment")
    sand = [event for event in events if event.get("material") == "sand"]
    assert len(events) == 2 and len(sand) == 1, (
        f"TC-053-115: the sand line is stored too: {events!r}"
    )
    assert sand[0].get("source_ref") is None, (
        f"TC-053-115: sand is no nutrient amendment and writes no feeding event: {sand[0]!r}"
    )
    after = plant_feeding_events(base_url, e2e_seed_data, plant)
    assert [f["key"] for f in after] == [reference["key"]], (
        f"TC-053-115: the sand entry adds no feeding event: {after!r}"
    )
