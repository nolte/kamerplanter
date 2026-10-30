"""E2E of REQ-053 wave 3 - planting a bed (WP 3.8, issue #2398; spec pin REQ-053 v1.6).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md, GP-ACC from the coverage matrix):
  TC-053-015  ->  "Bepflanzen" in rows: preview, 6 planned positions, run planned   (GP-ACC-019)
  TC-053-016  ->  create the plants of the planned run: on the planned positions    (GP-ACC-020)
  TC-053-018  ->  crop-rotation hint before the layout, "Trotzdem pflanzen" + reason (GP-ACC-047)
  TC-053-019  ->  correct a position by drag (desktop variant), history entry       (GP-ACC-022)
                  partial: see the test's docstring
  TC-053-034  ->  plant info on hover without a request, Esc, keyboard focus        (GP-ACC-051)
  TC-053-035  ->  marker state channels: ring, one badge, legend without colour      (GP-ACC-052)
                  partial: see the test's docstring

Not automated here, on purpose (no skip, no xfail - there is nothing to run):
  TC-053-017  the product has no browser path that reserves an *existing* position for a
              second run: the planting dialog creates new slots (layout or freely placed),
              and ``plan-slots`` is only called for the slots the dialog itself just made.
              The double booking (GP-ACC-021, 409 ``slot.already_planned``) is an
              integration-test contract (V-08), not a browser-observable flow.

Preconditions are self-provisioned through the application's own API, one fresh
site per test with a UUID-derived name (`_garden_plan_helpers.py`): no test reads
or mutates a bed another test or xdist worker touches. Species come from the seed
catalogue (`species.yaml`), never created. All cases are desktop cases
(TC-REQ-053 "Gerät: Desktop"; TC-053-019 runs its desktop variant, see there) and
carry ``requires_desktop``.

Positions are bed-frame metres (origin = the bed's lower-left corner, x right,
y up). Waits are anchored on state - a server-confirmed preview line, a list
count, ``aria-describedby``, a closed dialog - never on time.
"""

from __future__ import annotations

import re

import pytest
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from ._garden_plan_helpers import (
    BedSpec,
    backfill_last_year,
    bed_rect,
    bed_slots,
    create_plants,
    overdue_task,
    plant_on_positions,
    planned_run_with_layout,
    plantings,
    provision_garden,
    runs_of_bed,
    species,
    tenant_get,
    unique_tag,
)
from .pages.bed_view_page import BedViewPage
from .pages.planting_run_detail_page import PlantingRunDetailPage

pytestmark = pytest.mark.requires_desktop

BED_NAME = "Beet 1"
TOMATO = "Solanum lycopersicum"
CAULIFLOWER = "Brassica oleracea var. botrytis"
CABBAGE = "Brassica oleracea var. capitata"

#: How long the bubble survives the pointer leaving the marker (`usePlantInfoHover`).
LEAVE_GRACE_MS = 150


@pytest.fixture
def bed_view(browser: WebDriver, base_url: str) -> BedViewPage:
    return BedViewPage(browser, base_url)


def _one_bed(base_url: str, seed: dict, purpose: str, width: float, length: float):
    garden = provision_garden(
        base_url, seed, purpose=purpose, beds=(BedSpec(BED_NAME, bed_rect(width, length)),)
    )
    return garden, garden.bed_key(BED_NAME)


def _steps(values: list[float]) -> set[float]:
    """The distances between neighbouring distinct values, to the centimetre."""
    distinct = sorted({round(v, 3) for v in values})
    return {round(b - a, 2) for a, b in zip(distinct, distinct[1:])}


def _natural(text: str) -> list:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


# ── TC-053-015 ──────────────────────────────────────────────────────────────


@pytest.mark.smoke
def test_tc_053_015_plant_in_rows_with_preview_creates_a_planned_run(
    bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-015 — "Bepflanzen" tomato x 6 in rows 60/80 cm: preview, then 6 planned positions (GP-ACC-019).

    Precondition (API): a 3,0 x 1,6 m bed with geometry, no slots - the case's example
    (#2514): with the default edge margin (half the spacing, 40 cm across) a 1,2 m bed
    holds a single row of five, so six cannot fit. The preview is
    read from the drawn markers once the server confirmed it; what the run then
    stores must be exactly those six positions. Breaks if the preview is not
    server-confirmed, shows another count, puts a position outside the bed or
    off the 60 cm / 80 cm lattice, if the stored slots differ from the preview,
    the tab does not list six planned positions, or the submit already created
    plants or left the run anything but planned.

    Spec deviations, not asserted: the terms have no glossary explanation in the
    dialog (only their field labels, which are asserted); a rows preview offers no
    "remove a position and add it back" (only freely placed positions can be
    removed, step 4); the planned list shows name, slot id and date, not a dashed
    icon with the initial "T".
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc015", 3.0, 1.6)
    bed_view.open(bed, "planting")
    screenshot("053_015_01_empty_bed", "Beet 3,0 x 1,6 m ohne Pflanzung, Tab Bepflanzung")

    dialog = bed_view.open_planting_dialog()
    dialog.choose_species(TOMATO)
    dialog.choose_layout("rows")
    dialog.set_count(6)
    dialog.set_spacing(60)
    dialog.set_row_spacing(80)
    labels = (dialog.field_label("spacing"), dialog.field_label("row-spacing"))
    assert labels == ("Pflanzabstand", "Reihenabstand"), (
        f"TC-053-015: the dialog must name the terms Pflanzabstand / Reihenabstand, shows {labels}"
    )
    capacity = dialog.wait_for_server_preview(6, "TC-053-015: 6 tomatoes in rows 60/80 cm")
    assert capacity >= 6, f"TC-053-015: 'höchstens {capacity} passen' cannot hold 6 plants"

    preview = dialog.preview_positions()
    assert len(preview) == 6, f"TC-053-015: the preview must draw 6 positions, draws {preview}"
    outside = [p for p in preview if not (0.0 < p[0] < 3.0 and 0.0 < p[1] < 1.6)]
    assert not outside, f"TC-053-015: positions on or outside the bed edge: {outside}"
    lattice = sorted([_steps([x for x, _ in preview]), _steps([y for _, y in preview])], key=min)
    assert lattice == [{0.6}, {0.8}], (
        "TC-053-015: the positions must stand 60 cm apart in a row and 80 cm between rows; "
        f"neighbour distances per axis {lattice}, positions {preview}"
    )
    screenshot("053_015_02_preview", "Vorschau: 6 Positionen in Reihen, vom Server bestätigt")

    dialog.submit_and_wait_closed("TC-053-015: 'Pflanzung planen'")
    bed_view.wait_for_planting_lists(6, 0, "TC-053-015: after planning")
    screenshot("053_015_03_planned_list", "Tab Bepflanzung: 6 geplante Positionen")

    planned = sorted(
        plantings(base_url, e2e_seed_data, bed, "planned"), key=lambda p: p["sequence"]
    )
    assert [p["sequence"] for p in planned] == [1, 2, 3, 4, 5, 6], (
        f"TC-053-015: the run must reserve 6 positions in sequence 1..6: {planned}"
    )
    assert {p["species_key"] for p in planned} == {tomato["key"]}, "TC-053-015: all six are tomato"
    planned_keys = [p["slot_key"] for p in planned]
    assert sorted(bed_view.planned_slot_keys()) == sorted(planned_keys), (
        "TC-053-015: the tab must list exactly the reserved positions"
    )
    origins = {
        slot["key"]: slot["geometry"]["origin"] for slot in bed_slots(base_url, e2e_seed_data, bed)
    }
    stored = sorted((round(origins[k][0], 3), round(origins[k][1], 3)) for k in planned_keys)
    assert stored == sorted(preview), (
        f"TC-053-015: the stored positions must be the previewed ones; stored {stored}, "
        f"previewed {sorted(preview)}"
    )
    row = bed_view.planned_row_text(planned_keys[0])
    assert planned[0]["slot_id"] in row and " · ab " in row, (
        f"TC-053-015: a planned row names the position and the planned date: {row!r}"
    )

    runs = runs_of_bed(base_url, e2e_seed_data, bed)
    assert [run["status"] for run in runs] == ["planned"], (
        f"TC-053-015: one run, status planned, expected; got {[r['status'] for r in runs]}"
    )
    plants = tenant_get(base_url, e2e_seed_data, f"/planting-runs/{runs[0]['key']}/plants")
    assert plants == [], f"TC-053-015: planning must not create plants yet, run holds {plants}"


# ── TC-053-016 ──────────────────────────────────────────────────────────────


def test_tc_053_016_creating_the_plants_puts_them_on_the_planned_positions(
    bed_view: BedViewPage, browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-016 — "Pflanzen erzeugen" on the planned run: 6 plants on the 6 positions, in order (GP-ACC-020).

    Precondition (API): the outcome of TC-053-015 - a planned run with 6 reserved
    positions, laid out by the server (``POST /planting-runs`` with a rows entry).
    Breaks if fewer or other plants appear, a plant stands off the planned
    positions or out of their ``sequence`` order, the planned list is not
    empty afterwards, or the run does not become active.

    Spec deviation, not asserted: the planting tab's plant rows are not links,
    so "a click on a plant opens its detail page" has no target there.
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc016", 3.0, 1.6)
    run_key = planned_run_with_layout(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=tomato["key"],
        id_prefix="TOM",
        quantity=6,
        spacing_cm=60,
        row_spacing_cm=80,
    )
    planned = sorted(
        plantings(base_url, e2e_seed_data, bed, "planned"), key=lambda p: p["sequence"]
    )
    assert len(planned) == 6, f"TC-053-016 precondition: 6 planned positions, got {planned}"

    run_page = PlantingRunDetailPage(browser, base_url).open(run_key)
    status_before = run_page.get_status()
    screenshot("053_016_01_planned_run", "Geplanter Durchlauf mit 6 Positionen")
    run_page.click_create_plants()
    run_page.confirm_action()
    assert run_page.wait_for_confirm_dialog_closed(), "TC-053-016: the confirmation stays open"
    run_page.poll().until(lambda _d: run_page.get_status() != status_before)
    screenshot("053_016_02_run_active", "Durchlauf nach 'Pflanzen erzeugen'")

    bed_view.open(bed, "planting")
    bed_view.wait_for_planting_lists(0, 6, "TC-053-016: after creating the plants")
    screenshot(
        "053_016_03_plants_in_bed", "Tab Bepflanzung: 6 Pflanzen im Beet, nichts mehr geplant"
    )

    active = plantings(base_url, e2e_seed_data, bed, "active")
    assert sorted(bed_view.active_plant_keys()) == sorted(p["plant_key"] for p in active), (
        "TC-053-016: the tab must list exactly the bed's plants"
    )
    by_id = sorted(active, key=lambda p: _natural(p["instance_id"] or ""))
    assert [p["slot_key"] for p in by_id] == [p["slot_key"] for p in planned], (
        "TC-053-016: plant n must stand on the position with sequence n; plants by id stand on "
        f"{[(p['instance_id'], p['slot_key']) for p in by_id]}, planned order "
        f"{[p['slot_key'] for p in planned]}"
    )
    assert plantings(base_url, e2e_seed_data, bed, "planned") == [], (
        "TC-053-016: no position may stay planned once its plant stands there"
    )
    run = tenant_get(base_url, e2e_seed_data, f"/planting-runs/{run_key}")
    assert run["status"] == "active", f"TC-053-016: the run must be active, is {run['status']!r}"


# ── TC-053-018 ──────────────────────────────────────────────────────────────


def test_tc_053_018_rotation_hint_before_layout_and_plant_anyway_needs_a_reason(
    bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-018 — cabbage stood here last year: the hint for cauliflower, a reason to go ahead (GP-ACC-047).

    Precondition (API): last year's cabbage (Brassicaceae, pause 4 years) recorded
    through "what stood here" (backfill, GP-API-042). Breaks if the dialog shows
    no hint or one without reason (family, years, pause) and strength, if the
    hint comes after the layout, if "Trotzdem pflanzen" goes through without a
    reason, if the reason is not stored on the run, or if the bed carries no
    badge afterwards.

    Spec deviation, not asserted: the garden plan editor draws no rotation badge
    on the bed; the badge is asserted in the bed view's head.
    """
    cauliflower = species(base_url, e2e_seed_data, CAULIFLOWER)
    cabbage = species(base_url, e2e_seed_data, CABBAGE)
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc018", 2.0, 1.0)
    backfill_last_year(base_url, e2e_seed_data, bed, cabbage["key"])
    bed_view.open(bed, "planting")

    dialog = bed_view.open_planting_dialog()
    dialog.choose_species(CAULIFLOWER)
    severity, hint = dialog.wait_for_hint(
        cauliflower["key"], "TC-053-018: cauliflower after cabbage"
    )
    assert severity in ("warning", "error"), (
        f"TC-053-018: a pause not elapsed is a warning, the hint is {severity!r}: {hint!r}"
    )
    for fragment in ("Brassicaceae", "vor 1 Jahr(en)", "Anbaupause beträgt 4 Jahre"):
        assert fragment in hint, f"TC-053-018: the hint must name {fragment!r}: {hint!r}"
    assert re.search(r"Hinweis (Warnung|kritisch)", hint), (
        f"TC-053-018: the hint must name its strength: {hint!r}"
    )
    assert dialog.hints_precede_layout(), "TC-053-018: the hint must come before the layout"
    screenshot("053_018_01_rotation_hint", "Fruchtfolge-Hinweis vor der Layoutwahl")

    dialog.choose_layout("grid")
    dialog.set_count(4)
    dialog.set_spacing(50)
    dialog.wait_for_server_preview(4, "TC-053-018: 4 cauliflowers")
    dialog.check_plant_anyway()
    assert dialog.submit_button_text() == "Trotzdem pflanzen", (
        f"TC-053-018: with the hint confirmed the button reads {dialog.submit_button_text()!r}"
    )
    dialog.click_submit()
    dialog.poll().until(lambda _d: dialog.reason_is_invalid())
    assert dialog.reason_helper_text() == "Nenne einen Grund, um trotzdem zu pflanzen.", (
        f"TC-053-018: the empty reason must be flagged: {dialog.reason_helper_text()!r}"
    )
    assert dialog.is_open(), "TC-053-018: without a reason the dialog must stay open"
    assert runs_of_bed(base_url, e2e_seed_data, bed) == [], (
        "TC-053-018: 'Trotzdem pflanzen' without a reason must not create a run"
    )
    screenshot("053_018_02_reason_required", "Ohne Begründung: Pflichtfeld-Meldung")

    reason = f"Kohlhernie-freier Boden laut Analyse {unique_tag()}"
    dialog.set_reason(reason)
    dialog.submit_and_wait_closed("TC-053-018: 'Trotzdem pflanzen' with a reason")
    runs = runs_of_bed(base_url, e2e_seed_data, bed)
    assert [run.get("rotation_override_reason") for run in runs] == [reason], (
        f"TC-053-018: the run must carry the reason, runs: {runs}"
    )
    badge = bed_view.wait_for_rotation_badge("TC-053-018: after planting anyway")
    assert reason in badge, f"TC-053-018: the bed badge must show the reason: {badge!r}"
    screenshot("053_018_03_bed_badge", "Beetkopf mit Fruchtfolge-Badge und Begründung")


# ── TC-053-019 ──────────────────────────────────────────────────────────────


def test_tc_053_019_correct_a_position_by_drag_is_saved_at_once_and_logged(
    bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-019 (desktop variant) — drag a plant from (0,30 | 0,90) to (0,60 | 0,90) (GP-ACC-022).

    Precondition (API): a 2,0 x 1,2 m bed, one tomato on the position
    (0,30 | 0,90) and one in a zone. "Position korrigieren" from the planting
    tab, a real pointer drag of the marker, then "Position speichern". Breaks if
    the dialog does not start at the plant's position, the drag does not land
    on (0,60 | 0,90) to the centimetre, the stepper does not move the plant,
    what is stored differs from what the fields showed, the zone plant is
    movable, or the history has no "Position korrigiert" entry for the plant.

    Not covered: the smartphone part of the case - long-press drag in field mode,
    "pan without long press" (WP 5.x); this run is the desktop path the issue
    names. Spec deviations, not asserted: the stepper moves 1 cm (5 cm with the
    big buttons), not 10 cm; the history line is the server's summary
    "Position corrected (<slot>)" and names the slot, not the plant - the plant
    is asserted on the stored event instead.
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc019", 2.0, 1.2)
    planted = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=tomato["key"],
        id_prefix="TOM",
        points=((0.30, 0.90),),
        zones=(((1.2, 0.2), (1.8, 0.2), (1.8, 0.8), (1.2, 0.8)),),
    )
    slot = planted.point_slots[0]
    plant = planted.plant_on(slot)
    zone_plant = planted.plant_on(planted.zone_slots[0])
    bed_view.open(bed, "planting")
    bed_view.wait_for_planting_lists(0, 2, "TC-053-019 precondition: two plants in the bed")

    dialog = bed_view.open_position_dialog(plant)
    assert dialog.wait_until_loaded() == "position", "TC-053-019: the plant has a single position"
    dialog.wait_for_fields((30.0, 90.0), "TC-053-019: the dialog starts at the plant's position")
    screenshot("053_019_01_position_dialog", "Position korrigieren: Pflanze bei 30 / 90 cm")

    dialog.drag_marker_to(0.60, 0.90)
    dialog.wait_for_fields((60.0, 90.0), "TC-053-019: dragged to (0,60 | 0,90)", tolerance=1.0)
    dragged = dialog.fields_cm()
    dialog.step("right")
    assert dialog.fields_cm() == (dragged[0] + 1, dragged[1]), (
        f"TC-053-019: the stepper must move the plant one step right: {dragged} -> "
        f"{dialog.fields_cm()}"
    )
    dialog.step("left")
    assert dialog.fields_cm() == dragged, "TC-053-019: one step left puts it back"
    screenshot("053_019_02_dragged", "Nach dem Ziehen: Position bei 60 / 90 cm")

    dialog.save("TC-053-019: 'Position speichern'")
    stored = tenant_get(base_url, e2e_seed_data, f"/slots/{slot}")["geometry"]["origin"]
    expected = [round(dragged[0] / 100, 2), round(dragged[1] / 100, 2)]
    assert [round(v, 4) for v in stored] == expected, (
        f"TC-053-019: the server must hold what the fields showed at once, holds {stored}, "
        f"expected {expected}"
    )

    zone = bed_view.open_position_dialog(zone_plant)
    assert zone.wait_until_loaded() == "zone", "TC-053-019: a zone plant has no single position"
    assert not zone.is_save_enabled(), "TC-053-019: a zone plant cannot be moved"
    screenshot("053_019_03_zone_note", "Pflanze in einer Zone: Hinweis statt Verschieben")
    zone.close_with_escape()

    bed_view.open(bed, "history")
    bed_view.show_corrections()
    entry = bed_view.wait_for_history_entry(
        "Position korrigiert", "TC-053-019: the history after the correction"
    )
    screenshot("053_019_04_history", "Historie mit Eintrag 'Position korrigiert'")
    history = tenant_get(
        base_url, e2e_seed_data, f"/locations/{bed}/history?include_corrections=true&limit=50"
    )
    events = [
        item["care_event"]
        for item in history
        if item.get("care_event") and item["care_event"]["category"] == "position_corrected"
    ]
    assert [event["plant_keys"] for event in events] == [[plant]], (
        f"TC-053-019: exactly one position_corrected event naming the plant; got {events} "
        f"(entry shown: {entry!r})"
    )


# ── TC-053-034 ──────────────────────────────────────────────────────────────


def test_tc_053_034_plant_info_on_hover_needs_no_request_and_follows_keyboard_focus(
    bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot_dir
) -> None:
    """TC-053-034 — hover a tomato among 40: the bubble shows its facts without a request (GP-ACC-051).

    Precondition (API): 40 tomatoes in rows, the bed's tab-stop plant with two
    overdue tasks. A request probe (XHR, fetch, resource timing; with a positive
    control) runs from before the hover to the end. Breaks if the bubble does
    not open for the hovered plant, misses species, phase, age, position, next
    task or "2 Aufgaben überfällig", if any request leaves the page, if the
    bubble closes while the pointer is on it or stays after Esc, or if keyboard
    focus does not show the same information and point the marker at it.

    Not covered: "focus another plant with the arrow keys" - the bed view's plan
    has one tab stop and no arrow-key walk between plants (the editor has
    PageDown); "no bubble while dragging" - the bed view's plan is read-only, there
    is no drag to suppress it during.
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc034", 3.0, 1.2)
    run_key = planned_run_with_layout(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=tomato["key"],
        id_prefix="TOM",
        quantity=40,
        spacing_cm=25,
        row_spacing_cm=25,
    )
    assert len(create_plants(base_url, e2e_seed_data, run_key)) == 40, (
        "TC-053-034 precondition: 40 plants in the bed"
    )
    bed_view.open(bed, "plan")
    assert len(bed_view.plant_marker_keys()) == 40, "TC-053-034 precondition: 40 markers drawn"
    target = bed_view.tab_stop_plant()
    first = f"E2E-GP Ausgeizen {unique_tag()}"
    overdue_task(base_url, e2e_seed_data, target, first, days_ago=3)
    overdue_task(base_url, e2e_seed_data, target, f"E2E-GP Anbinden {unique_tag()}", days_ago=2)

    bed_view.open(bed, "plan")
    bed_view.wait_for_plant_states(target, "TC-053-034: the plan with the plant states")
    bed_view.start_network_probe()

    bed_view.hover_plant(target)
    hover_text = bed_view.wait_for_bubble(target, "TC-053-034: hovering the tomato")
    lines = bed_view.bubble_lines()
    # Viewport-only: a full-page capture resizes the viewport under the resting pointer, which
    # the app reads as the pointer leaving the marker - and closes the bubble the case is about.
    bed_view.take_screenshot("053_034_01_bubble", screenshot_dir)
    assert TOMATO in hover_text, f"TC-053-034: the bubble must name the species: {hover_text!r}"
    for line in ("phase", "age", "position", "task"):
        assert line in lines, f"TC-053-034: the bubble lacks its {line!r} line: {lines}"
    assert lines["task"].startswith(f"Nächste Aufgabe: {first}"), (
        f"TC-053-034: the next task is the one due first: {lines['task']!r}"
    )
    assert lines.get("attention-overdue") == "2 Aufgaben überfällig", (
        f"TC-053-034: the bubble must say '2 Aufgaben überfällig': {lines}"
    )
    assert bed_view.requests_since_probe() == [], (
        f"TC-053-034: hovering must not request anything: {bed_view.requests_since_probe()}"
    )

    bed_view.move_pointer_into_bubble()
    assert bed_view.bubble_survives(3 * LEAVE_GRACE_MS), (
        "TC-053-034: the bubble must stay while the pointer is on it"
    )
    bed_view.press(Keys.ESCAPE)
    bed_view.wait_for_bubble_gone("TC-053-034: Esc")

    bed_view.focus_before_canvas()
    focused = bed_view.tab_to_plant()
    assert focused == target, f"TC-053-034: Tab lands on the tab-stop plant {target}, not {focused}"
    focus_text = bed_view.wait_for_bubble(target, "TC-053-034: keyboard focus on the tomato")
    assert focus_text == hover_text, (
        f"TC-053-034: focus must show the same information as hover: {focus_text!r} vs "
        f"{hover_text!r}"
    )
    assert "2 Aufgaben überfällig" in bed_view.marker_aria_label(target), (
        f"TC-053-034: the marker's accessible name must carry the overdue tasks: "
        f"{bed_view.marker_aria_label(target)!r}"
    )
    bed_view.take_screenshot("053_034_02_focus", screenshot_dir)
    assert bed_view.requests_since_probe() == [], (
        f"TC-053-034: bubble, Esc and focus must not request anything: "
        f"{bed_view.requests_since_probe()}"
    )


# ── TC-053-035 ──────────────────────────────────────────────────────────────


def test_tc_053_035_marker_channels_one_badge_and_a_legend_without_colour(
    bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-035 (partial) — active ring, exactly one badge, and a legend that needs no colour (GP-ACC-052).

    Precondition (API): three tomatoes in the bed, one with two overdue tasks.
    Asserted: every plant draws the "active" ring; the one with overdue tasks
    carries exactly one badge (overdue), the others none, and its accessible
    name says so; the legend explains the five ring styles and the five badges,
    and every row differs from the others in a non-colour channel (dash pattern,
    number of rings, cross; badge shape) - which is what keeps the states apart
    in greyscale and with a red-green deficiency.

    Not covered: the planned, sown, harvesting and failed states on real plants
    (a planned or sown position is a reservation the plant-states answer does not
    carry; a harvesting or failed plant needs a harvest batch or a removal), the
    "finding beats overdue" badge priority (needs a diagnosis record), the
    greyscale / colour-vision simulation and dark mode as rendered pictures.
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc035", 2.0, 1.0)
    planted = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=tomato["key"],
        id_prefix="TOM",
        points=((0.4, 0.5), (1.0, 0.5), (1.6, 0.5)),
    )
    plants = [planted.plant_on(slot) for slot in planted.point_slots]
    target, others = plants[0], plants[1:]
    overdue_task(base_url, e2e_seed_data, target, f"E2E-GP Kontrolle {unique_tag()}", days_ago=3)
    overdue_task(base_url, e2e_seed_data, target, f"E2E-GP Ausgeizen {unique_tag()}", days_ago=2)

    bed_view.open(bed, "plan")
    bed_view.wait_for_plant_states(target, "TC-053-035: the plan with the plant states")
    lifecycles = {key: bed_view.marker_lifecycle(key) for key in plants}
    assert set(lifecycles.values()) == {"active"}, f"TC-053-035: rings drawn {lifecycles}"
    assert bed_view.marker_badges(target) == ["overdue"], (
        f"TC-053-035: the plant with overdue tasks carries one badge: "
        f"{bed_view.marker_badges(target)}"
    )
    assert {key: bed_view.marker_badges(key) for key in others} == {key: [] for key in others}, (
        "TC-053-035: plants without a reason carry no badge"
    )
    assert "2 Aufgaben überfällig" in bed_view.marker_aria_label(target), (
        f"TC-053-035: the badge's reason is in the accessible name: "
        f"{bed_view.marker_aria_label(target)!r}"
    )
    screenshot("053_035_01_markers", "Marker: durchgezogener Ring, ein Badge an der Pflanze")

    bed_view.open_legend()
    rows = bed_view.legend_rows()
    rings = [row for row in rows if row["lifecycle"]]
    badges = [row for row in rows if row["shape"]]
    assert [row["lifecycle"] for row in rings] == [
        "planned",
        "sown",
        "active",
        "harvesting",
        "failed",
    ], f"TC-053-035: the legend must explain the five ring styles: {rings}"
    signatures = [(row["dash"], row["rings"], row["cross"]) for row in rings]
    assert len(set(signatures)) == 5, (
        f"TC-053-035: every ring style must differ without colour; channels {signatures}"
    )
    shapes = [row["shape"] for row in badges]
    assert len(shapes) == 5 and len(set(shapes)) == 5, (
        f"TC-053-035: the legend must show five badges of five shapes: {shapes}"
    )
    assert all(row["text"] for row in rows), f"TC-053-035: every legend row has a text: {rows}"
    screenshot("053_035_02_legend", "Legende: Ringstile und Badges")
