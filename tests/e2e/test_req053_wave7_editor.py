"""E2E of REQ-053 wave 7 part A - zones, watering round, templates, snap, arrange, auto-save (WP 7.25, #2491).

Spec pin REQ-053 v1.7. Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md):
  TC-053-045  ->  create an irrigation zone, take the beds from the plan's multi-selection,   (GP-FR-110)
                  the "zones" layer hatches exactly them, the bed info names the zone
  TC-053-046  ->  watering round of a zone: the total divided by bed area, marked as          (GP-FR-117)
                  allocated (not measured) in the dialog, the log and the zone status
  TC-053-048  ->  "last watered" layer: days since the last watering per bed, legend,         (GP-UX-031)
                  no hatching without a recorded watering
  TC-053-049  ->  place a bed from a system template, turned by 90 degrees                   (GP-FR-044)
  TC-053-050  ->  standard size in "add with dimensions": shape, size, bed type and height   (GP-FR-045)
  TC-053-051  ->  object snap: a dragged bed snaps to the corner of its neighbour, Alt        (GP-FR-012)
                  switches it off
  TC-053-052  ->  align to the bottom edge and distribute horizontally, saved                (GP-FR-029)
  TC-053-053  ->  duplicate several times with the naming scheme "Parzelle {n}", one undo     (GP-FR-025)
                  step
  TC-053-054  ->  auto-save after two quiet seconds, paused while a conflict stands          (GP-UX-004)
  TC-053-055  ->  mini-map: shown only when zoomed in, the viewport rectangle follows a pan,  (GP-UX-014)
                  a click jumps back

Not automated here, on purpose (no skip, no xfail - there is nothing to run):
  TC-053-047  "Regen - übersprungen" of the watering round: the round dialog offers no such action and the
              backend has no route for it yet (`WateringRoundDialog.tsx` docstring, placeholder bundle #2466).

Preconditions are self-provisioned through the application's own API, one fresh site per test with a
UUID-derived name (`_garden_plan_helpers.py`): no test reads or mutates a plan, a zone or a care event another
test or xdist worker touches. Bed templates are the system templates of migration v0101 (seed data, read
only). Layer, auto-save and length-unit choices live in the browser's ``localStorage``, which every test's
fresh browser session starts empty. All cases are desktop cases and carry ``requires_desktop``.

Waits are anchored on state - the pending-change count of the save bar (emptied only by a fulfilled save), a
result view that replaces a form only on the server's answer, the zone status that renders only for a stored
record, the layer's ``data-*`` attributes - never on time, and there is no retry loop. Every saved outcome is
read back from the server.

Positions are model metres (x right, y up); a rect's ``origin`` is its lower-left corner; the grid is 10 cm.
"""

from __future__ import annotations

import pytest
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from ._garden_plan_helpers import (
    BedSpec,
    care_events,
    create_zone,
    days_since_utc,
    log_care_event,
    move_location_via_api,
    provision_garden,
    read_plan,
    rect,
    stored_location,
    stored_origin,
    unique_tag,
    zones_of_site,
)
from .pages.garden_plan_page import GardenPlanPage

pytestmark = pytest.mark.requires_desktop

SAVED = "Gespeichert"
CONFLICT = "Konflikt – Plan wurde zwischenzeitlich geändert"


@pytest.fixture
def plan(browser: WebDriver, base_url: str) -> GardenPlanPage:
    return GardenPlanPage(browser, base_url)


def _days_label(days: int) -> str:
    """The layer's wording of a day count (``wateredDays_one`` / ``_other``)."""
    return f"{days} Tag seit" if days == 1 else f"{days} Tage seit"


# ── TC-053-045 ──────────────────────────────────────────────────────────────


def test_tc_053_045_zone_from_plan_selection_and_zone_layer(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-045 - a zone takes its beds from the plan's multi-selection; the layer hatches them (GP-FR-110).

    Three beds; Ctrl+A selects all three, "Auswahl vom Plan übernehmen" ticks them, Beet C is unticked again.
    Breaks if the selection is not taken over, the zone is not stored with exactly Beet A and Beet B, the
    "zones" layer hatches another set of beds, or the bed info does not name the zone.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc045",
        beds=(
            BedSpec("Beet A", rect(1.0, 4.5, 2.0, 1.0)),
            BedSpec("Beet B", rect(4.0, 4.5, 2.0, 1.0)),
            BedSpec("Beet C", rect(7.0, 4.5, 2.0, 1.0)),
        ),
    )
    bed_a, bed_b, bed_c = (garden.bed_key(n) for n in ("Beet A", "Beet B", "Beet C"))
    zone_name = f"Tropfzone {unique_tag()}"
    plan.open(garden.site_key)
    plan.zoom_to(100)
    screenshot("053_045_01_plan_three_beds", "Plan mit drei Beeten, noch ohne Zone")

    plan.select_all_with_keyboard({bed_a, bed_b, bed_c})
    plan.open_zone_panel()
    plan.start_new_zone(zone_name)
    plan.take_selection_into_zone({bed_a, bed_b, bed_c})
    plan.set_zone_bed(bed_c, False)
    screenshot("053_045_02_zone_form", "Neue Zone: Auswahl übernommen, Beet C abgewählt")

    plan.save_zone()
    stored = zones_of_site(base_url, e2e_seed_data, garden.site_key)
    assert [(z["name"], sorted(z["location_keys"])) for z in stored] == [
        (zone_name, sorted([bed_a, bed_b]))
    ], (
        f"TC-053-045: exactly one stored zone {zone_name!r} with Beet A and Beet B expected, got {stored}"
    )
    zone_key = stored[0]["key"]
    screenshot("053_045_03_zone_saved", "Zone gespeichert, Stand der Zone sichtbar")

    plan.set_layer("zones", True)
    plan.wait_for_zone_layer_beds(
        zone_key, {bed_a, bed_b}, "TC-053-045: the zones layer hatches the zone's beds only"
    )
    screenshot("053_045_04_zone_layer", "Ebene Zonen: Beet A und Beet B schraffiert, Beet C nicht")

    plan.select_with_keyboard(bed_a)
    plan.wait_for_text(
        plan.PANEL_ZONE, f"Bewässerungszone: 1. {zone_name}", "TC-053-045: bed info of Beet A"
    )
    plan.select_with_keyboard(bed_c)
    plan.wait_for_element(plan.PANEL_LAST_WATERED)
    assert plan.panel_name() == "Beet C", (
        f"TC-053-045: the panel should show Beet C, it shows {plan.panel_name()!r}"
    )
    assert not plan.is_present(plan.PANEL_ZONE), (
        "TC-053-045: Beet C belongs to no zone, its bed info must not name one"
    )
    screenshot("053_045_05_bed_info", "Beet C gewählt: keine Zone in der Beet-Info")


# ── TC-053-046 ──────────────────────────────────────────────────────────────


def test_tc_053_046_watering_round_divides_by_area_and_is_marked_allocated(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-046 - 10 l over a 2 m² and a 3 m² bed: 4 l and 6 l, marked "allocated" (GP-FR-117).

    Precondition (API): a zone covering both beds, no watering recorded. Breaks if the shares are not
    proportional to the bed area, the dialog or the result does not say the amounts are allocated, the log
    lines are stored as measured, the hand-over note is lost, or the zone status does not mark the last
    watering as allocated.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc046",
        beds=(
            BedSpec("Beet A", rect(1.0, 4.5, 2.0, 1.0)),
            BedSpec("Beet B", rect(4.0, 4.5, 3.0, 1.0)),
        ),
    )
    bed_a, bed_b = garden.bed_key("Beet A"), garden.bed_key("Beet B")
    zone = create_zone(
        base_url,
        e2e_seed_data,
        site_key=garden.site_key,
        name=f"Zone {unique_tag()}",
        bed_keys=(bed_a, bed_b),
    )
    note = f"Übergabe: Regentonne fast leer {unique_tag()}"

    plan.open(garden.site_key)
    plan.open_zone_panel()
    plan.open_zone(zone["key"])
    assert "Noch kein Gießen erfasst." in plan.text_of(plan.ZONE_LAST_WATERING), (
        f"TC-053-046: a fresh zone has no watering yet; status reads "
        f"{plan.text_of(plan.ZONE_LAST_WATERING)!r}"
    )
    screenshot("053_046_01_zone_status", "Zone geöffnet, noch kein Gießen erfasst")

    plan.open_watering_round()
    assert plan.text_of(plan.ROUND_MARKER) == (
        "Die Menge wird auf die Beete verteilt und nicht gemessen. Das Protokoll kennzeichnet das so."
    ), (
        f"TC-053-046: the dialog must say the amounts are allocated: {plan.text_of(plan.ROUND_MARKER)!r}"
    )
    plan.choose_round_allocation("by_area")
    screenshot("053_046_02_round_dialog", "Gießrunde: Verteilung nach Beetfläche, Hinweis verteilt")

    shares = plan.submit_watering_round("10", note)
    assert sorted(shares) == ["Beet A: 4 Liter", "Beet B: 6 Liter"], (
        f"TC-053-046: 10 l by area over 2 m² and 3 m² is 4 l and 6 l, the result lists {shares}"
    )
    assert plan.text_of(plan.ROUND_RESULT_MARKER) == (
        "Nach Fläche verteilt: Diese Mengen sind verteilt, nicht gemessen."
    ), f"TC-053-046: result marker reads {plan.text_of(plan.ROUND_RESULT_MARKER)!r}"
    screenshot("053_046_03_round_result", "Ergebnis: Anteile je Beet, als verteilt gekennzeichnet")
    plan.close_watering_round()

    logged = {
        bed: care_events(base_url, e2e_seed_data, bed, category="watering")
        for bed in (bed_a, bed_b)
    }
    summary = {
        bed: [(e["quantity"], e["unit"], e["allocation"], e["summary"]) for e in events]
        for bed, events in logged.items()
    }
    assert summary == {
        bed_a: [(4.0, "l", "by_area", note)],
        bed_b: [(6.0, "l", "by_area", note)],
    }, f"TC-053-046: one allocated watering line per bed with the note expected, stored {summary}"

    plan.wait_for_text(
        plan.ZONE_ALLOCATION_MARKER,
        "Nach Fläche verteilt",
        "TC-053-046: the zone status marks the last watering as allocated",
    )
    screenshot(
        "053_046_04_status_after_round", "Stand der Zone: zuletzt gegossen, nach Fläche verteilt"
    )


# ── TC-053-048 ──────────────────────────────────────────────────────────────


def test_tc_053_048_last_watered_layer_days_since_per_bed(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-048 - the "last watered" layer: today, five days ago, never (GP-UX-031).

    Precondition (API): a watering logged on Beet A now and on Beet B five days ago, none on Beet C. The
    expected day counts are taken from the stored instants by the same UTC calendar-day rule the layer uses,
    so a run just after midnight UTC does not flip the expectation. Breaks if the layer draws another class or
    number, hatches Beet C, the legend lacks the classes or the "no need" note, or the bed info disagrees.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc048",
        beds=(
            BedSpec("Beet A", rect(1.0, 4.5, 2.0, 1.0)),
            BedSpec("Beet B", rect(4.0, 4.5, 2.0, 1.0)),
            BedSpec("Beet C", rect(7.0, 4.5, 2.0, 1.0)),
        ),
    )
    bed_a, bed_b, bed_c = (garden.bed_key(n) for n in ("Beet A", "Beet B", "Beet C"))
    today = log_care_event(
        base_url, e2e_seed_data, bed_key=bed_a, category="watering", summary="Gegossen heute"
    )
    earlier = log_care_event(
        base_url,
        e2e_seed_data,
        bed_key=bed_b,
        category="watering",
        summary="Gegossen vor fünf Tagen",
        days_ago=5,
    )
    days_a = days_since_utc(today["performed_at"])
    days_b = days_since_utc(earlier["performed_at"])
    assert days_a in (0, 1) and days_b in (5, 6), (
        f"TC-053-048: arrangement drift - the logged waterings are {days_a} and {days_b} days old"
    )

    plan.open(garden.site_key)
    plan.zoom_to(100)
    assert not plan.is_layer_on("lastWatered"), "TC-053-048: the layer starts switched off"
    screenshot("053_048_01_layer_off", "Plan mit drei Beeten, Ebene zuletzt gegossen aus")

    plan.set_layer("lastWatered", True)
    plan.wait_for_watered_layer(
        {
            bed_a: ("d0_1", _days_label(days_a)),
            bed_b: ("d4_7", _days_label(days_b)),
        },
        "TC-053-048: classes and labels of the last-watered layer, Beet C without hatching",
    )
    legend = plan.text_of(plan.LEGEND_WATERED)
    for fragment in (
        "Tage seit dem letzten Gießen",
        "0 bis 1 Tag seit",
        "4 bis 7 Tage seit",
        "Ohne Schraffur: kein Gießen erfasst.",
        "Ob ein Beet Wasser braucht, sagt der Plan nicht.",
    ):
        assert fragment in legend, f"TC-053-048: the legend lacks {fragment!r}: {legend!r}"
    screenshot(
        "053_048_02_layer_on", "Ebene an: Beet A 0-1 Tag, Beet B 4-7 Tage, Beet C ohne Schraffur"
    )

    plan.select_with_keyboard(bed_b)
    plan.wait_for_text(
        plan.PANEL_LAST_WATERED,
        f"Zuletzt gegossen: {_days_label(days_b)}",
        "TC-053-048: bed info of Beet B",
    )
    plan.select_with_keyboard(bed_c)
    plan.wait_for_text(
        plan.PANEL_LAST_WATERED, "Kein Gießen erfasst.", "TC-053-048: bed info of Beet C"
    )
    screenshot("053_048_03_bed_info", "Beet C gewählt: kein Gießen erfasst")


# ── TC-053-049 ──────────────────────────────────────────────────────────────


def test_tc_053_049_place_bed_from_system_template_turned(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-049 - "Beet 2 × 1 m" from the template tool, turned once, placed at the view centre (GP-FR-044).

    Breaks if the picker does not offer the system template, the turn is not applied, the bed is not created
    and saved in one step, or the stored bed is not a copy of the template (type, size, template reference,
    origin on the grid).
    """
    garden = provision_garden(base_url, e2e_seed_data, purpose="tc049")
    plan.open(garden.site_key)
    screenshot("053_049_01_plan_without_beds", "Plan mit Gartengrenze, ohne Beet")

    plan.pick_template("sys_bed_2x1")
    plan.wait_for_text(
        plan.TEMPLATE_HINT,
        "Klicke auf den Plan, um das Beet zu setzen. Alt hält den Rasterfang an, Esc beendet.",
        "TC-053-049: after picking a template",
    )
    plan.wait_and_click(plan.TEMPLATE_ROTATE)
    plan.wait_for_text(plan.TEMPLATE_ROTATE, "Drehen (aktuell 90°)", "TC-053-049: one turn")
    screenshot("053_049_02_template_picked", "Vorlage Beet 2 × 1 m gewählt, um 90° gedreht")

    plan.place_template_at_centre(
        "Das Beet wurde aus der Vorlage angelegt und ist gespeichert. Zum Zurücknehmen lösche das Beet."
    )
    assert plan.pending_count() == 0, (
        "TC-053-049: placing a template saves at once, nothing stays pending"
    )
    locations = read_plan(base_url, e2e_seed_data, garden.site_key)["locations"]
    assert len(locations) == 1, f"TC-053-049: exactly one stored bed expected, got {locations}"
    bed = locations[0]
    geometry = bed["geometry"]
    assert (
        bed["template_key"],
        bed["location_type_key"],
        geometry["kind"],
        geometry["width_m"],
        geometry["length_m"],
        geometry["rotation_deg"],
    ) == ("sys_bed_2x1", "bed", "rect", 2.0, 1.0, 90.0), (
        f"TC-053-049: the stored bed is no turned copy of the template: {bed}"
    )
    on_grid = [round(v * 10, 6) == round(v * 10) for v in geometry["origin"]]
    assert on_grid == [True, True], (
        f"TC-053-049: the placed origin must lie on the 10 cm grid, it is {geometry['origin']}"
    )
    assert plan.is_selected(bed["key"]), "TC-053-049: the placed bed is selected on the plan"
    screenshot("053_049_03_placed", "Beet aus Vorlage gesetzt und gespeichert")


# ── TC-053-050 ──────────────────────────────────────────────────────────────


def test_tc_053_050_standard_size_fills_add_with_dimensions(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-050 - the standard size "Hochbeet 2 × 1 × 0,8 m" fills shape, size, type and height (GP-FR-045).

    Breaks if the quick choice is missing, fills other values, or the saved bed differs from them.
    """
    garden = provision_garden(base_url, e2e_seed_data, purpose="tc050")
    name = "Hochbeet Standard"
    plan.open(garden.site_key)
    plan.open_add_with_dimensions()
    plan.pick_standard_size("sys_raised_bed_2x1x0_8")
    filled = (
        plan.add_field("width"),
        plan.add_field("length"),
        plan.add_field("height"),
        plan.add_bed_type(),
    )
    assert filled == ("2", "1", "0.8", "raised_bed"), (
        f"TC-053-050: the standard size should fill 2 / 1 / 0.8 / raised_bed, it filled {filled}"
    )
    plan.set_add_field("name", name)
    plan.set_add_field("x", "3")
    plan.set_add_field("y", "6")
    screenshot(
        "053_050_01_standard_size", "Hinzufügen mit Maßen: Standardgröße Hochbeet übernommen"
    )

    plan.submit_add_dialog()
    plan.wait_for_pending(1, "TC-053-050: the new bed is one unsaved change")
    plan.save_with_button()
    plan.wait_for_status_text(SAVED, "TC-053-050: after saving")
    bed = stored_location(read_plan(base_url, e2e_seed_data, garden.site_key), name)
    geometry = bed["geometry"]
    assert (
        geometry["origin"],
        geometry["width_m"],
        geometry["length_m"],
        bed["height_m"],
        bed["location_type_key"],
    ) == ([3.0, 6.0], 2.0, 1.0, 0.8, "raised_bed"), f"TC-053-050: stored bed differs: {bed}"
    screenshot("053_050_02_saved", "Hochbeet 2 × 1 × 0,8 m gespeichert")


# ── TC-053-051 ──────────────────────────────────────────────────────────────


def test_tc_053_051_object_snap_to_neighbour_corner_alt_switches_off(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot, screenshot_dir
) -> None:
    """TC-053-051 - a bed dragged next to its neighbour snaps to the neighbour's corner (GP-FR-012).

    Beet A's right edge is at x = 3,53 m - off the 10 cm grid on purpose. Beet B (x = 5,5 m) is dragged
    195 px to the left at 100 % zoom (1 px = 1 cm): its left corners come within 2 cm of Beet A's right
    corners, inside the 10 px tolerance, so B lands at x = 3,53 - a position the grid alone cannot produce
    (it would give 3,5 or 3,6). With Alt the same drag lands at 3,55. Breaks if the object snap is missing,
    loses against the grid, or Alt does not switch it off.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc051",
        beds=(
            BedSpec("Beet A", rect(2.03, 4.5, 1.5, 1.0)),
            BedSpec("Beet B", rect(5.5, 4.5, 1.5, 1.0)),
        ),
    )
    bed_b = garden.bed_key("Beet B")
    plan.open(garden.site_key)
    plan.zoom_to(100)
    screenshot("053_051_01_two_beds", "Beet A (rechte Kante 3,53 m) und Beet B (x = 5,5 m)")

    seen: dict[str, str | None] = {}

    def _while_dragging() -> None:
        seen["marker"] = plan.snap_marker_kind()
        # Viewport-only: a full-page capture would scroll under the held button.
        plan.take_screenshot("053_051_02_snapping", screenshot_dir)

    plan.drag_object_by(bed_b, -195, during=_while_dragging)
    plan.wait_for_panel_field("x", 3.53, "TC-053-051: B snaps to A's corner")
    assert plan.panel_field("y") == 4.5, "TC-053-051: a horizontal drag keeps y"
    assert seen == {"marker": "corner"}, (
        f"TC-053-051: while dragging, the snap marker must show a corner snap; observed {seen}"
    )
    screenshot("053_051_03_snapped", "Beet B an der Ecke von Beet A eingerastet (x = 3,53 m)")

    plan.undo_with_button()
    plan.wait_for_panel_field("x", 5.5, "TC-053-051: undo puts B back")
    plan.drag_object_by(bed_b, -195, alt=True)
    plan.wait_for_panel_field("x", 3.55, "TC-053-051: with Alt nothing snaps")
    screenshot("053_051_04_alt", "Mit Alt: x = 3,55 m, kein Einrasten")

    plan.undo_with_button()
    plan.wait_for_panel_field("x", 5.5, "TC-053-051: undo the Alt drag")
    plan.drag_object_by(bed_b, -195)
    plan.wait_for_panel_field("x", 3.53, "TC-053-051: snapping again")
    plan.save_with_button()
    assert stored_origin(read_plan(base_url, e2e_seed_data, garden.site_key), bed_b) == (
        3.53,
        4.5,
    ), "TC-053-051: the saved position of Beet B must be the snapped one"


# ── TC-053-052 ──────────────────────────────────────────────────────────────


def test_tc_053_052_align_bottom_and_distribute_horizontally(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-052 - three beds aligned to the lowest bottom edge, then spread with equal gaps (GP-FR-029).

    A (1,0 | 2,0, 2 m wide), B (4,5 | 3,0, 2 m), C (7,0 | 2,5, 1 m). "Unten ausrichten" puts every bottom
    edge on y = 2,0; "Horizontal gleichmäßig verteilen" keeps the outer beds and moves B to x = 4,0 (gaps of
    1,0 m). Breaks if either action moves the wrong beds, by the wrong amount, or is not saved.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc052",
        beds=(
            BedSpec("Beet A", rect(1.0, 2.0, 2.0, 1.0)),
            BedSpec("Beet B", rect(4.5, 3.0, 2.0, 1.0)),
            BedSpec("Beet C", rect(7.0, 2.5, 1.0, 1.0)),
        ),
    )
    keys = {n: garden.bed_key(n) for n in ("Beet A", "Beet B", "Beet C")}
    plan.open(garden.site_key)
    plan.zoom_to(100)
    plan.select_all_with_keyboard(set(keys.values()))
    screenshot("053_052_01_selected", "Drei Beete gewählt, versetzt")

    plan.align("bottom")
    plan.wait_for_pending(2, "TC-053-052: aligning moves Beet B and Beet C")
    for name, origin in {"Beet A": (1.0, 2.0), "Beet B": (4.5, 2.0), "Beet C": (7.0, 2.0)}.items():
        plan.wait_for_shape_origin(
            keys[name], origin, f"TC-053-052: {name} after 'Unten ausrichten'"
        )
    screenshot("053_052_02_aligned", "Unten ausgerichtet: alle Unterkanten auf y = 2,0 m")

    plan.align("distribute-horizontal")
    plan.wait_for_pending(3, "TC-053-052: distributing moves Beet B only")
    expected = {"Beet A": (1.0, 2.0), "Beet B": (4.0, 2.0), "Beet C": (7.0, 2.0)}
    for name, origin in expected.items():
        plan.wait_for_shape_origin(keys[name], origin, f"TC-053-052: {name} after distributing")
    screenshot("053_052_03_distributed", "Horizontal verteilt: gleiche Abstände von 1,0 m")

    plan.save_with_button()
    stored = read_plan(base_url, e2e_seed_data, garden.site_key)
    actual = {name: stored_origin(stored, key) for name, key in keys.items()}
    assert actual == expected, f"TC-053-052: stored positions {actual}, expected {expected}"


# ── TC-053-053 ──────────────────────────────────────────────────────────────


def test_tc_053_053_multi_duplicate_with_naming_scheme_is_one_undo_step(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-053 - three copies of a 1 × 1 m bed, 0,5 m apart, named "Parzelle 1…3" (GP-FR-025 SHOULD).

    Breaks if the dialog does not preview the names, the copies are not one undo step, or the saved copies
    have other names, positions (pitch 1,5 m to the right) or sizes.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc053",
        beds=(BedSpec("Beet 1", rect(1.0, 4.5, 1.0, 1.0)),),
    )
    source = garden.bed_key("Beet 1")
    plan.open(garden.site_key)
    plan.select_with_keyboard(source)
    plan.open_multi_duplicate()
    plan.set_multi_field("count", "3")
    plan.set_multi_field("scheme", "Parzelle {n}")
    plan.set_multi_field("spacing", "0,5")
    plan.wait_for_text(
        plan.MULTI_PREVIEW,
        "Die Kopien heißen: Parzelle 1 … Parzelle 3",
        "TC-053-053: name preview",
    )
    screenshot("053_053_01_dialog", "Mehrfach duplizieren: 3 Kopien, Parzelle {n}")

    plan.submit_multi_duplicate()
    plan.wait_for_pending(3, "TC-053-053: three copies are three unsaved changes")
    assert len(plan.object_keys()) == 4, (
        f"TC-053-053: the plan should draw the bed and three copies, it draws {plan.object_keys()}"
    )
    screenshot("053_053_02_copies", "Drei Kopien rechts neben Beet 1")

    plan.focus_canvas()
    plan.press(Keys.CONTROL, "z")
    plan.wait_for_pending(0, "TC-053-053: one Ctrl+Z takes all copies back")
    assert plan.object_keys() == [source], (
        f"TC-053-053: after one undo only Beet 1 is left, the plan draws {plan.object_keys()}"
    )
    plan.press(Keys.CONTROL, Keys.SHIFT, "z")
    plan.wait_for_pending(3, "TC-053-053: Ctrl+Shift+Z brings all copies back")

    plan.save_with_button()
    stored = read_plan(base_url, e2e_seed_data, garden.site_key)
    copies = {
        loc["name"]: (
            tuple(loc["geometry"]["origin"]),
            loc["geometry"]["width_m"],
            loc["geometry"]["length_m"],
        )
        for loc in stored["locations"]
        if loc["key"] != source
    }
    assert copies == {
        "Parzelle 1": ((2.5, 4.5), 1.0, 1.0),
        "Parzelle 2": ((4.0, 4.5), 1.0, 1.0),
        "Parzelle 3": ((5.5, 4.5), 1.0, 1.0),
    }, f"TC-053-053: stored copies differ: {copies}"
    screenshot("053_053_03_saved", "Parzelle 1 bis 3 gespeichert")


# ── TC-053-054 ──────────────────────────────────────────────────────────────


def test_tc_053_054_auto_save_saves_and_pauses_on_conflict(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-054 - auto-save stores a move without a click and pauses while a conflict stands (GP-UX-004).

    Then someone else saves (API, a second editor's batch at the editor's revision) and the next move meets
    the conflict. Breaks if auto-save needs the button, overwrites the other save, keeps going (or keeps
    quiet) while the conflict stands, or does not resume after "Neu laden".
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc054",
        beds=(
            BedSpec("Beet A", rect(2.0, 2.0, 2.0, 1.0)),
            BedSpec("Beet B", rect(6.0, 6.0, 2.0, 1.0)),
        ),
    )
    bed_a, bed_b = garden.bed_key("Beet A"), garden.bed_key("Beet B")
    plan.open(garden.site_key)
    plan.enable_autosave()
    screenshot("053_054_01_autosave_on", "Automatisch speichern eingeschaltet")

    plan.select_with_keyboard(bed_a)
    plan.press(Keys.ARROW_RIGHT)
    plan.wait_for_shape_origin(bed_a, (2.1, 2.0), "TC-053-054: the move is applied")
    plan.wait_for_pending(0, "TC-053-054: auto-save stores the move without the button")
    stored = read_plan(base_url, e2e_seed_data, garden.site_key)
    assert stored_origin(stored, bed_a) == (2.1, 2.0), (
        "TC-053-054: after the auto-save the server holds the moved position"
    )

    other = move_location_via_api(
        base_url,
        e2e_seed_data,
        site_key=garden.site_key,
        expected_revision=int(stored["plan_revision"]),
        location_key=bed_b,
        geometry=rect(6.5, 6.0, 2.0, 1.0),
    )
    plan.press(Keys.ARROW_RIGHT)
    plan.wait_for_shape_origin(bed_a, (2.2, 2.0), "TC-053-054: the second move is applied")
    plan.wait_for_conflict_dialog("TC-053-054: the auto-save meets the other save")
    plan.wait_for_status_text(CONFLICT, "TC-053-054: the save bar names the conflict")
    plan.wait_for_text(
        plan.AUTOSAVE_PAUSED,
        "Automatisches Speichern pausiert, solange der Konflikt offen ist.",
        "TC-053-054: auto-save says it is paused",
    )
    assert plan.pending_count() == 1, "TC-053-054: the refused move stays pending"
    after = read_plan(base_url, e2e_seed_data, garden.site_key)
    assert (
        int(after["plan_revision"]),
        stored_origin(after, bed_a),
        stored_origin(after, bed_b),
    ) == (other, (2.1, 2.0), (6.5, 6.0)), (
        "TC-053-054: the other save stays, the refused move is not written: "
        f"revision {after['plan_revision']}, A {stored_origin(after, bed_a)}, B {stored_origin(after, bed_b)}"
    )
    screenshot(
        "053_054_02_conflict_paused", "Konflikt: Dialog offen, automatisches Speichern pausiert"
    )

    plan.reload_after_conflict()
    plan.wait_for_shape_origin(bed_b, (6.5, 6.0), "TC-053-054: the reload shows the other save")
    assert not plan.is_present(plan.AUTOSAVE_PAUSED), (
        "TC-053-054: no pause once the conflict is resolved"
    )
    assert plan.is_autosave_on(), "TC-053-054: the auto-save choice survives the reload"

    plan.select_with_keyboard(bed_a)
    plan.press(Keys.ARROW_UP)
    plan.wait_for_shape_origin(bed_a, (2.1, 2.1), "TC-053-054: a move after the reload")
    plan.wait_for_pending(0, "TC-053-054: auto-save works again")
    assert stored_origin(read_plan(base_url, e2e_seed_data, garden.site_key), bed_a) == (
        2.1,
        2.1,
    ), "TC-053-054: after the conflict the auto-save stores again"
    screenshot("053_054_03_resumed", "Nach Neu laden: automatisches Speichern wieder aktiv")


# ── TC-053-055 ──────────────────────────────────────────────────────────────


def test_tc_053_055_minimap_shows_viewport_and_jumps(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-055 - the mini-map appears when zoomed in, follows a pan and jumps on a click (GP-UX-014).

    The opened plan is fitted (the whole 10 × 10 m garden in view, below 100 %) and the mini-map stays
    away; at 400 % it shows. Three
    Shift+Arrow-right presses pan the view by 1,2 m (480 px), which moves the viewport rectangle about
    14 px to the right in the 120 px drawing; a click in the mini-map's middle centres the view again.
    Breaks if the mini-map shows without need, is missing when zoomed in, its rectangle does not follow the
    view, or the click does not jump.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc055",
        beds=(
            BedSpec("Beet A", rect(1.0, 1.0, 2.0, 1.0)),
            BedSpec("Beet B", rect(7.0, 8.0, 2.0, 1.0)),
        ),
    )
    plan.open(garden.site_key)
    fitted = plan.zoom_percent()
    assert fitted < 100 and not plan.is_present(plan.MINIMAP), (
        f"TC-053-055: the opened plan is fitted ({fitted} %) with the whole garden in view, so there "
        "is no mini-map"
    )
    screenshot("053_055_01_no_minimap", "Eingepasst: ganzer Garten sichtbar, keine Mini-Map")

    plan.zoom_to(400)
    plan.wait_for_element_visible(plan.MINIMAP)
    start = plan.minimap_viewport_centre()
    screenshot("053_055_02_minimap", "400 %: Mini-Map rechts unten mit Ausschnitt-Rechteck")

    plan.focus_canvas()
    for _ in range(3):
        plan.press(Keys.SHIFT, Keys.ARROW_RIGHT)
    plan.wait_for_minimap_shift_right(start, 10, "TC-053-055: panning 1,2 m to the right")
    screenshot("053_055_03_panned", "Nach rechts verschoben: Rechteck in der Mini-Map folgt")

    plan.click_minimap_centre()
    plan.wait_for_minimap_centred(2.0, "TC-053-055: a click in the mini-map's middle")
    screenshot("053_055_04_jumped", "Klick in die Mitte der Mini-Map: Ansicht springt zurück")
