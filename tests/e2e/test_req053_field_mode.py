"""E2E of REQ-053 wave 5 - field mode on a phone, 390 x 844 (WP 5.4, issue #2433; spec pin REQ-053 v1.6).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md, GP-ACC from the coverage matrix):
  TC-053-025  ->  open task: bed, "Erledigt", "Fertig" - two taps after the bed, 64 px,   (GP-ACC-029)
                  a double tap completes once
  TC-053-026  ->  quick-protocol chip "Gejätet/Gemulcht", the 8 s "Rückgängig" snackbar,   (GP-ACC-048)
                  undo voids the line
  TC-053-019  ->  correct a position with the stepper in field mode (10 cm per step)        (GP-ACC-022)
                  mobile variant of the desktop case in test_req053_planting.py

The performance targets of the same work package (GP-ACC-033/034, GP-NFR-040) are not browser cases: they are
benchmarks with assertions (``applyOperation`` / ``computeLayout`` in vitest, containment and ``GET /plan`` in
pytest) and the Lighthouse route of ``src/frontend/lighthouserc.json``.

The phone is the browser at exactly 390 x 844 CSS px (``set_phone_viewport`` measures and reads it back); the
page is opened with ``?mode=field``, which is also what a phone gets by default. The Grid's remote Chrome takes no
CDP device emulation, so the taps are the real pointer clicks of WebDriver: what is counted as a "tap" is a
trusted ``click`` on a button, counted by the page itself (``start_counting_taps``).

Preconditions are self-provisioned through the application's own API, one fresh site per test with a
UUID-derived name (`_garden_plan_helpers.py`). Waits are anchored on state - the sheet's task section, a closed
dialog, a gone row, the snackbar's own appear/disappear stamps - never on time, and there is no retry loop.
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._garden_plan_helpers import (
    BedSpec,
    bed_rect,
    bed_slots,
    care_events,
    create_bed_task,
    plant_on_positions,
    provision_garden,
    species,
    task_state,
    unique_tag,
)
from .pages.field_mode_page import FieldModePage, set_phone_viewport
from .pages.bed_view_page import BedViewPage, PositionDialog

BED_NAME = "Beet 1"
TOMATO = "Solanum lycopersicum"
#: The kiosk touch target of UI-NFR-019 R-007 / GP-UX-020, and the field-mode font floor.
TOUCH_PX = 64
FONT_PX = 16
#: GP-FR-149 / GP-ACC-048: the "Rückgängig" snackbar stays 8 s. The page measures the real time on screen; the
#: window absorbs the exit transition (about 0.2 s) and a loaded runner, but not a 5 s or a 15 s snackbar.
UNDO_VISIBLE_MS = (7_500, 10_000)
#: One step of the field-mode stepper (``FIELD_STEP_CM``, §18.1 step 9).
FIELD_STEP_CM = 10


@pytest.fixture
def phone(browser: WebDriver) -> WebDriver:
    set_phone_viewport(browser, 390, 844)
    return browser


@pytest.fixture
def field(phone: WebDriver, base_url: str) -> FieldModePage:
    return FieldModePage(phone, base_url)


@pytest.fixture
def bed_view(phone: WebDriver, base_url: str) -> BedViewPage:
    return BedViewPage(phone, base_url)


def _one_bed(base_url: str, seed: dict, purpose: str):
    garden = provision_garden(
        base_url, seed, purpose=purpose, beds=(BedSpec(BED_NAME, bed_rect(2.0, 1.0)),)
    )
    return garden, garden.bed_key(BED_NAME)


def _events_of_task(base_url: str, seed: dict, bed_key: str, task_key: str) -> list[dict]:
    return [e for e in care_events(base_url, seed, bed_key) if e.get("task_key") == task_key]


# ── TC-053-025 ──────────────────────────────────────────────────────────────


@pytest.mark.smoke
def test_tc_053_025_a_task_is_done_in_two_taps_after_the_bed(
    field: FieldModePage,
    bed_view: BedViewPage,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-025 — "Erledigt" then "Fertig" without any input: two taps after the bed, 64 px (GP-ACC-029).

    Precondition (API): a bed with an open watering task due today. On the 390 x 844 phone the bed list shows
    the bed; the bed is tapped (tap 0, the choice), then the button taps are counted: "Erledigt" (tap 1) opens
    the short dialog, "Fertig" (tap 2) completes with nothing typed. Asserted: exactly those two taps, the
    "Erledigt" button measures at least 64 x 64 px with a font of at least 16 px, the task is ``completed`` on
    the server with exactly one care event (``category = watering``, no amount), the row leaves the sheet, and
    the bed's history shows the line. Breaks if the flow needs a third tap, if the target is smaller than the
    kiosk floor, if the completion writes no line or two, or if the history does not show it.
    """
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc025")
    name = f"Gießen {unique_tag()}"
    task_key = create_bed_task(base_url, e2e_seed_data, bed_key=bed, name=name, category="watering")

    field.open(_garden.site_key)
    screenshot("053_025_01_bed_list", "Feldmodus 390 px: „Meine Beete · heute fällig“")
    field.tap_bed(bed)
    field.start_counting_taps()

    width, height = field.element_size(field.done_button(task_key))
    assert width >= TOUCH_PX and height >= TOUCH_PX, (
        f"TC-053-025: 'Erledigt' must measure at least {TOUCH_PX} x {TOUCH_PX} px, it measures {width} x {height}"
    )
    font = field.computed_font_px(field.done_button(task_key))
    assert font >= FONT_PX, (
        f"TC-053-025: the 'Erledigt' font must be at least {FONT_PX} px, it is {font}"
    )
    field.tap_done(task_key)
    screenshot("053_025_02_dialog", "Schnell-Dialog nach dem ersten Tipp auf „Erledigt“")
    field.tap_finish("TC-053-025: 'Fertig' without any input")
    field.wait_for_task_gone(task_key, "TC-053-025")

    taps, targets = field.taps_since_reset()
    assert taps == 2, (
        f"TC-053-025: exactly two taps after the bed are needed, the page counted {targets}"
    )
    assert targets == [f"field-done-{task_key}", "care-complete-submit"], targets

    events = _events_of_task(base_url, e2e_seed_data, bed, task_key)
    assert len(events) == 1, f"TC-053-025: one completion is one care event, found {events}"
    assert events[0]["category"] == "watering" and events[0]["quantity"] is None, events[0]
    assert task_state(base_url, e2e_seed_data, task_key)["status"] == "completed"

    bed_view.open(bed, "history")
    entry = bed_view.wait_for_history_entry("Gießen", "TC-053-025: the history line")
    assert "Liter" not in entry and "ml" not in entry, (
        f"TC-053-025: a line without an amount: {entry!r}"
    )
    screenshot("053_025_03_history", "Historie des Beets: Eintrag „Gießen“ ohne Menge")


def test_tc_053_025_a_double_tap_completes_the_task_once(
    field: FieldModePage,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-025 (second expectation) — a double tap on "Erledigt" and on "Fertig" is one tap (GP-UX-023, R-029).

    Two real clicks land inside the 300 ms guard on each button. Asserted: one dialog opens (not two), and the
    task has exactly one care event afterwards. Breaks if the guard is gone - a second completion, a second
    dialog, or a 409/422 toast would follow.
    """
    garden, bed = _one_bed(base_url, e2e_seed_data, "tc025d")
    task_key = create_bed_task(
        base_url, e2e_seed_data, bed_key=bed, name=f"Gießen {unique_tag()}", category="watering"
    )

    field.open(garden.site_key)
    field.tap_bed(bed)
    field.double_tap_done(task_key)
    assert field.dialogs_open() == 1, "TC-053-025: a double tap on 'Erledigt' opens one dialog"
    field.double_tap_finish("TC-053-025: a double tap on 'Fertig'")
    field.wait_for_task_gone(task_key, "TC-053-025 double tap")

    events = _events_of_task(base_url, e2e_seed_data, bed, task_key)
    assert len(events) == 1, f"TC-053-025: a double tap must not complete twice, found {events}"
    screenshot("053_025_04_double_tap", "Nach dem Doppeltipp: die Aufgabe ist einmal erledigt")


# ── TC-053-026 ──────────────────────────────────────────────────────────────


def test_tc_053_026_the_weeding_chip_writes_one_line_and_undo_voids_it_within_eight_seconds(
    field: FieldModePage,
    bed_view: BedViewPage,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-026 — "Gejätet/Gemulcht": one tap, one line, "Rückgängig" takes it back; untouched it stays (GP-ACC-048).

    Precondition (API): a bed. In the bed sheet the chip is tapped once. Asserted at once, before anything else:
    one care event ``category = weeding``, ``trigger = manual``, not voided, and a snackbar with "Rückgängig".
    Tapping it voids the event with ``void_reason = undo`` and the history marks the line "Storniert". A
    second tap on the chip, left alone, keeps its event; the snackbar's own stamps say it was on screen about 8 s
    (7,5-10 s, the page measures, the test waits for the snackbar to be gone). Breaks if a tap writes no line or
    two, if the undo voids with another reason or not at all, or if an untouched line is voided or the
    snackbar lives 4 s or 20 s.
    """
    garden, bed = _one_bed(base_url, e2e_seed_data, "tc026")

    field.open(garden.site_key)
    field.tap_bed(bed)
    field.tap_chip("weeding")
    message = field.wait_for_undo_offer("TC-053-026: after the first chip tap")
    assert "Jäten" in message, f"TC-053-026: the snackbar names what was logged: {message!r}"

    events = care_events(base_url, e2e_seed_data, bed, category="weeding")
    assert len(events) == 1, f"TC-053-026: one tap is one care event, found {events}"
    assert (events[0]["trigger"], events[0]["voided_at"]) == ("manual", None), events[0]
    screenshot("053_026_01_snackbar", "Feldmodus: Chip getippt, Snackbar „Rückgängig“")

    field.tap_undo()
    voided = [
        e
        for e in care_events(
            base_url, e2e_seed_data, bed, category="weeding", include_superseded=True
        )
    ]
    assert len(voided) == 1 and voided[0]["voided_at"] and voided[0]["void_reason"] == "undo", (
        f"TC-053-026: undo voids the line with the reason 'undo': {voided}"
    )

    field.watch_undo_lifetime()
    field.tap_chip("weeding")
    field.wait_for_undo_offer("TC-053-026: after the second chip tap")
    lifetime_ms = field.undo_lifetime_ms("TC-053-026: the untouched snackbar")
    assert UNDO_VISIBLE_MS[0] <= lifetime_ms <= UNDO_VISIBLE_MS[1], (
        f"TC-053-026: the snackbar stays about 8 s, the page measured {lifetime_ms:.0f} ms"
    )
    kept = [
        e
        for e in care_events(base_url, e2e_seed_data, bed, category="weeding")
        if not e["voided_at"]
    ]
    assert len(kept) == 1, f"TC-053-026: the untouched line stays valid: {kept}"

    bed_view.open(bed, "history")
    history = bed_view.wait_for_history_entry(
        "Storniert", "TC-053-026: the voided line in the history"
    )
    assert "Jäten" in history, history
    screenshot("053_026_02_history", "Historie: ein stornierter und ein gültiger Eintrag „Jäten“")


# ── TC-053-019 (mobile variant) ─────────────────────────────────────────────


def test_tc_053_019_field_mode_corrects_a_position_with_the_ten_centimetre_stepper(
    field: FieldModePage,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-019 (mobile variant) — "Position korrigieren" in the bed sheet: stepper in 10 cm steps (GP-ACC-022).

    Precondition (API): a 2,0 x 1,0 m bed with one tomato at (0,50 | 0,50). In field mode the plant group is
    opened, the plant's "Position korrigieren" tapped, the dialog's right arrow pressed twice and the position
    saved. Asserted: the fields read 10 cm further per press (60, then 70 cm), and the stored slot of the plant
    stands at x = 0,70 m, y unchanged. Breaks if the stepper moves another distance, if the save does not
    reach the plant's slot, or if the dialog closes without saving.

    Not covered here: the drag with a long press (500 ms, ``FIELD_LONG_PRESS_MS``) - a held pointer is a
    timing input, not a state; the desktop drag is TC-053-019 in test_req053_planting.py.
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    garden, bed = _one_bed(base_url, e2e_seed_data, "tc019m")
    planted = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=tomato["key"],
        id_prefix="TCC",
        points=((0.5, 0.5),),
    )
    slot_key = planted.point_slots[0]
    plant_key = planted.plant_on(slot_key)

    field.open(garden.site_key)
    field.tap_bed(bed)
    field.open_plant_groups()
    field.correct_position(plant_key)
    dialog = PositionDialog(field.driver, base_url)
    assert dialog.wait_until_loaded() == "position", "TC-053-019: a point slot offers the stepper"
    assert dialog.fields_cm() == (50.0, 50.0), dialog.fields_cm()
    dialog.step("right")
    dialog.wait_for_fields((50.0 + FIELD_STEP_CM, 50.0), "TC-053-019: one step right")
    dialog.step("right")
    dialog.wait_for_fields((50.0 + 2 * FIELD_STEP_CM, 50.0), "TC-053-019: a second step right")
    screenshot("053_019m_01_stepper", "Feldmodus: Position korrigieren, zwei Schritte nach rechts")
    dialog.save("TC-053-019 mobile: saving the corrected position")

    (stored,) = [s for s in bed_slots(base_url, e2e_seed_data, bed) if s["key"] == slot_key]
    x, y = stored["geometry"]["origin"]
    assert (round(x, 3), round(y, 3)) == (0.7, 0.5), (
        f"TC-053-019: the plant's slot must stand at (0.7 | 0.5) m, it stands at {stored['geometry']}"
    )
