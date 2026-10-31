"""E2E of REQ-053 wave 7 part B - new season, underlay, layers, partial export, snapshots, field sun (WP 7.26, #2492).

Spec pin REQ-053 v1.7. Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md):
  TC-053-042  ->  new season from the previous year: last season's places become free slots,    (GP-FR-171)
                  a bed with standing plants is skipped, zones stay, no plant and no run is made,
                  the history still shows the season before, the bed can be planted
  TC-053-044  ->  step 2 only: underlay picture calibrated by two clicked points and a known      (GP-FR-033)
                  distance of 4,0 m; the editor draws that distance as 4,0 m; layer switch;
                  the picture is not in the JSON backup
  TC-053-056  ->  plant-state layer with ring and badge, the filter "only plants that need        (GP-UX-061,
                  attention", the filter locked without the layer, the sun-window layer           GP-FR-169)
  TC-053-057  ->  back up only the selection (frame selection, "Nur die Auswahl") and bring it    (GP-FR-172)
                  into another site with the target "Aus einem anderen Standort"
  TC-053-058  ->  restore an earlier state (snapshot) with a dry-run report and the site name     (GP-FR-148/170)
  TC-053-059  ->  sun-window chips in field mode on a 390 x 844 phone: one tap stores, hours      (GP-FR-158/159,
                  stored, both shown again after a reload                                         GP-UX-057)

Deviations from the written steps, on purpose:
  TC-053-042  The season copies the slots of runs that **ended** in the year before the new season, and a run
              ends (``archived_at``) only through "Beet räumen", which stamps *now*. No path the running system
              accepts writes an end in an earlier calendar year, so the test chooses the season ``UTC year + 1``:
              the current year is then the "previous year". The bed is cleared through the clear route
              (``POST /locations/{key}/clear``) because "Beet räumen" has no browser surface yet (TC-053-027).
              "Fruchtfolge-Hinweise beim Bepflanzen nutzen sie" is not asserted: the rotation hint reads the
              calendar years before the planting year, and the season the test can produce is the current one.
  TC-053-044  Runs in the full profile only (``UNDERLAY_NEEDS_STORAGE``: the light E2E backend has no writable
              attachment storage, so the picture upload fails there); in light profiles it skips with that reason.
              Only the calibration step on an **outdoor** site (the issue's scope). Not automated here: the
              indoor floor plan from the empty state (the empty plan offers no underlay - the editor, and with
              it the underlay button, mounts only on a plan with a boundary), the room polygon, the window with
              its derived direction, furniture and a pot on it (no window/furniture tool in the editor).

Not automated here, on purpose (no skip, no xfail - there is nothing to run):
  TC-053-027  "Beet räumen" has no browser surface (no button calls ``POST /locations/{key}/clear``).
  TC-053-041  The replace import through the wizard is not part of this work package; TC-053-058 uses the replace
              import only as its arrangement (API) and restores through the browser.
  Export dialog "Unterlage" switch: the export dialog has no underlay option (``EXPORT_LAYERS`` holds none);
              TC-053-044 therefore reads the backup and asserts the picture is absent.

Preconditions are self-provisioned through the application's own API, one fresh site per test with a
UUID-derived name (`_garden_plan_helpers.py`): no test reads or mutates a plan, a snapshot or a bed another test
or xdist worker touches. Species come from the seed catalogue. Layer and filter choices live in the browser's
``localStorage``, which every test's fresh browser session starts empty. The desktop cases carry
``requires_desktop``; TC-053-059 puts the browser at exactly 390 x 844 itself (``set_phone_viewport``), as the
wave-5 field-mode cases do.

Waits are anchored on state - a report that renders only for the server's answer, a success line that replaces a
form only after the write, ``aria-pressed`` / ``aria-disabled``, a closed dialog, the layer's ``data-*`` attributes,
the stored record - never on time, and there is no retry loop. Every written outcome is read back from the server.

Positions are model metres (x right, y up); a rect's ``origin`` is its lower-left corner; slots are bed-frame points.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from ._garden_plan_helpers import (
    BedSpec,
    add_bed_via_batch,
    bed_rect,
    bed_slots,
    clear_bed,
    create_zone,
    export_plan_json,
    overdue_task,
    plan_snapshots,
    plant_on_positions,
    plantings,
    provision_garden,
    read_plan,
    rect,
    replace_plan_with,
    rotation_years,
    runs_of_bed,
    set_sun_window,
    species,
    stored_location,
    sun_profile,
    unique_tag,
    utc_today,
    zones_of_site,
)
from .pages.bed_view_page import BedViewPage
from .pages.field_mode_page import FieldModePage, set_phone_viewport
from .pages.garden_plan_page import GardenPlanPage

TOMATO = "Solanum lycopersicum"
#: A 64 x 64 px PNG of the suite's fixtures - a picture as a user would upload it.
PICTURE = Path(__file__).parent / "fixtures" / "sample_plant_photo.png"
#: The kiosk touch target of field mode (GP-UX-023, ``KIOSK_TOUCH_TARGET``).
TOUCH_PX = 64
#: Why TC-053-044 runs in the full profile only: the underlay picture is an attachment (NFR-013 object storage),
#: and in ``docker-compose.e2e.yml`` only ``backend-full`` mounts a writable object store (``object-storage-full``);
#: the light ``backend`` answers the upload with a ``PermissionError`` on ``/data``. A harness gap, not a product
#: decision - mounting a store on the light backend would let the case run in every profile.
UNDERLAY_NEEDS_STORAGE = (
    "TC-053-044 needs the full E2E profile: only backend-full has writable attachment storage "
    "(docker-compose.e2e.yml, object-storage-full)"
)
#: How long a server-side effect of one tap may take to be readable (a request, not an animation).
STORED_WITHIN_S = 15


@pytest.fixture
def plan(browser: WebDriver, base_url: str) -> GardenPlanPage:
    return GardenPlanPage(browser, base_url)


@pytest.fixture
def bed_view(browser: WebDriver, base_url: str) -> BedViewPage:
    return BedViewPage(browser, base_url)


def _names(stored: dict) -> list[str]:
    return sorted(loc["name"] for loc in stored.get("locations") or [])


def _wait_stored(driver: WebDriver, read, expected, what: str):
    """Wait until the server-side read *read()* equals *expected*; loud with the last value read."""
    last: list = [None]

    def _check(_d) -> bool:
        last[0] = read()
        return last[0] == expected

    try:
        WebDriverWait(driver, STORED_WITHIN_S, poll_frequency=0.5).until(_check)
    except TimeoutException as exc:
        raise AssertionError(
            f"{what}: the server should hold {expected!r}, it holds {last[0]!r}"
        ) from exc
    return last[0]


# ── TC-053-042 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_042_new_season_turns_last_seasons_places_into_free_slots(
    plan: GardenPlanPage, bed_view: BedViewPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-042 - "Neue Saison aus Vorjahr": structure without plants, the history kept (GP-FR-171).

    Precondition (API): four beds; tomatoes stood on two places each in Beet A, B and C and were cleared this
    season; Beet C was planted again (a standing plant); Beet D never had a planting; one zone covers A and D.
    The season ``UTC year + 1`` is checked and confirmed in the dialog. Breaks if the report names other beds,
    counts or reasons, if the free slots are not at last season's places, if a plant or a run is created, if a
    bed with a standing plant is touched, if the zone changes, if the history loses last season, or if the bed
    cannot be planted.
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc042",
        beds=(
            BedSpec("Beet A", rect(0.5, 6.0, 2.0, 1.0)),
            BedSpec("Beet B", rect(3.5, 6.0, 2.0, 1.0)),
            BedSpec("Beet C", rect(6.5, 6.0, 2.0, 1.0)),
            BedSpec("Beet D", rect(0.5, 2.0, 2.0, 1.0)),
        ),
    )
    bed_a, bed_b, bed_c, bed_d = (
        garden.bed_key(n) for n in ("Beet A", "Beet B", "Beet C", "Beet D")
    )
    zone_name = f"Zone {unique_tag()}"
    create_zone(
        base_url, e2e_seed_data, site_key=garden.site_key, name=zone_name, bed_keys=(bed_a, bed_d)
    )
    places = ((0.5, 0.5), (1.5, 0.5))
    for bed, prefix in ((bed_a, "TA"), (bed_b, "TB"), (bed_c, "TC")):
        plant_on_positions(
            base_url,
            e2e_seed_data,
            bed_key=bed,
            species_key=tomato["key"],
            id_prefix=prefix,
            points=places,
        )
        clear_bed(base_url, e2e_seed_data, bed)
    plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed_c,
        species_key=tomato["key"],
        id_prefix="TCX",
        points=((1.0, 0.5),),
    )
    runs_before = {bed: len(runs_of_bed(base_url, e2e_seed_data, bed)) for bed in (bed_a, bed_b)}
    slots_c_before = sorted(slot["key"] for slot in bed_slots(base_url, e2e_seed_data, bed_c))
    year = utc_today().year + 1
    source = year - 1

    plan.open(garden.site_key)
    plan.open_new_season()
    title = plan.check_new_season(year)
    assert title == f"Prüfung: Plätze aus {source} für {year}", (
        f"TC-053-042: report title {title!r}"
    )
    rows = sorted(plan.season_report_rows())
    assert rows == [
        "Beet A: 2 freie Slots",
        "Beet B: 2 freie Slots",
        "Beet C: übersprungen, es stehen aktive Pflanzen darin",
    ], f"TC-053-042: the report lists per bed {rows}"
    report = plan.season_report_text()
    assert (
        "4 freie Slots in 2 Beeten werden angelegt." in report
        and "1 Beete werden übersprungen." in report
    ), f"TC-053-042: the report's summary reads {report!r}"
    assert bed_slots(base_url, e2e_seed_data, bed_a) == [], "TC-053-042: the check writes nothing"
    screenshot("053_042_01_report", "Neue Saison: Prüfbericht je Beet, Beet C übersprungen")

    done = plan.confirm_new_season()
    assert done == "4 freie Slots in 2 Beeten angelegt.", f"TC-053-042: success line {done!r}"
    screenshot("053_042_02_done", "Neue Saison angelegt: 4 freie Slots in 2 Beeten")
    plan.close_new_season()

    for bed in (bed_a, bed_b):
        slots = bed_slots(base_url, e2e_seed_data, bed)
        origins = sorted(tuple(slot["geometry"]["origin"]) for slot in slots)
        assert origins == sorted(places), (
            f"TC-053-042: free slots of {bed} at {origins}, expected {places}"
        )
        assert not any(slot.get("currently_occupied") for slot in slots), (
            f"TC-053-042: the new slots of {bed} must be free: {slots}"
        )
        assert plantings(base_url, e2e_seed_data, bed, "active") == [], (
            f"TC-053-042: no plant stands in {bed} after the season copy"
        )
        assert len(runs_of_bed(base_url, e2e_seed_data, bed)) == runs_before[bed], (
            f"TC-053-042: the season copy creates no run in {bed}"
        )
    assert (
        sorted(slot["key"] for slot in bed_slots(base_url, e2e_seed_data, bed_c)) == slots_c_before
    ), "TC-053-042: the bed with a standing plant keeps its slots"
    assert bed_slots(base_url, e2e_seed_data, bed_d) == [], (
        "TC-053-042: a bed without a last season gets nothing"
    )
    zones = [
        (z["name"], sorted(z["location_keys"]))
        for z in zones_of_site(base_url, e2e_seed_data, garden.site_key)
    ]
    assert zones == [(zone_name, sorted([bed_a, bed_d]))], (
        f"TC-053-042: the zone stays as it was: {zones}"
    )
    history = rotation_years(base_url, e2e_seed_data, bed_a).get(source) or []
    assert history, f"TC-053-042: the rotation timeline of Beet A must still show {source}"

    bed_view.open(bed_a, "history")
    shown = bed_view.timeline_family_keys(source, "TC-053-042: the history of Beet A")
    expected_families = sorted(entry.get("family_key") or "fallow" for entry in history)
    assert shown == expected_families, (
        f"TC-053-042: the history shows {shown} for {source}, the server records {expected_families}"
    )
    screenshot("053_042_03_history", f"Historie von Beet A: {source} zeigt die Tomaten")

    bed_view.open(bed_a, "planting")
    dialog = bed_view.open_planting_dialog()
    assert dialog.is_present(dialog.DIALOG), "TC-053-042: Beet A can be planted in the new season"
    screenshot("053_042_04_can_plant", "Beet A lässt sich in der neuen Saison bepflanzen")


# ── TC-053-044 (step 2) ─────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_044_underlay_calibrated_by_two_points_is_drawn_true_to_scale(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot, app_mode: str
) -> None:
    """TC-053-044 (step 2, outdoor site) - two clicked points 4,0 m apart calibrate the underlay (GP-FR-033).

    The picture is uploaded in the underlay dialog, point 1 and point 2 are clicked on it, the distance is typed
    as "4,0". Asserted: the scale the dialog shows is the clicked pixel distance over 4 m, the stored calibration
    holds the clicked pixels and 4,0 m, and the editor draws the two points exactly 4,0 m apart on the plan (the
    drawn image's own screen matrix over the plan's pixels per metre). The layer switch appears with the picture
    and hides and shows it; a reload draws it again; the JSON backup does not carry it. Breaks if the clicks mark
    other pixels, the scale is computed or stored wrongly, the picture is drawn at another scale, the layer
    switch has no effect, or the backup leaks the picture.
    """
    if app_mode != "full":
        pytest.skip(UNDERLAY_NEEDS_STORAGE)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc044",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    plan.open(garden.site_key)
    assert not plan.has_layer_toggle("underlay"), (
        "TC-053-044: without a picture the plan lists no underlay layer"
    )
    plan.open_underlay()
    size = plan.choose_underlay_picture(str(PICTURE))
    assert size == (64, 64), f"TC-053-044: the picture's natural size is {size}"
    assert plan.text_of(plan.UNDERLAY_SCALE).startswith("Noch kein Maßstab"), (
        f"TC-053-044: no scale before the points: {plan.text_of(plan.UNDERLAY_SCALE)!r}"
    )

    p1 = plan.mark_underlay_point("p1", 0.1, 0.5)
    p2 = plan.mark_underlay_point("p2", 0.9, 0.5)
    assert 0 <= p1[0] < p2[0] <= size[0] and abs(p1[0] - 6.4) <= 1.0 and abs(p2[0] - 57.6) <= 1.0, (
        f"TC-053-044: the clicks at 10 % and 90 % of the 64 px picture marked {p1} and {p2}"
    )
    pixels = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    plan.set_underlay_field("distance", "4,0")
    scale_text = plan.text_of(plan.UNDERLAY_SCALE)
    prefix, suffix = "Maßstab: ", " Pixel pro Meter"
    assert scale_text.startswith(prefix) and scale_text.endswith(suffix), (
        f"TC-053-044: scale reads {scale_text!r}"
    )
    shown = float(scale_text[len(prefix) : -len(suffix)].replace(",", "."))
    assert abs(shown - pixels / 4.0) <= 0.01, (
        f"TC-053-044: {pixels:.2f} px over 4,0 m is {pixels / 4.0:.2f} px/m, the dialog shows {shown}"
    )
    screenshot("053_044_01_calibrated", "Unterlage: zwei Punkte gesetzt, Abstand 4,0 m, Maßstab")

    plan.save_underlay()
    stored_plan = read_plan(base_url, e2e_seed_data, garden.site_key).get("plan") or {}
    underlay = stored_plan.get("underlay")
    assert underlay is not None, "TC-053-044: the plan stores no underlay after saving"
    calibration = underlay["calibration"]
    assert [
        tuple(calibration["p1_px"]),
        tuple(calibration["p2_px"]),
        calibration["distance_m"],
    ] == [p1, p2, 4.0], f"TC-053-044: stored calibration {calibration}, clicked {p1} {p2} and 4,0 m"
    assert plan.is_layer_on("underlay"), "TC-053-044: a saved picture switches its layer on"
    drawn = plan.underlay_screen_distance_m(p1, p2)
    assert abs(drawn - 4.0) <= 0.02, (
        f"TC-053-044: the two points are drawn {drawn:.3f} m apart, not 4,0 m"
    )
    screenshot("053_044_02_drawn", "Unterlage auf dem Plan: die Strecke misst 4,0 m")

    plan.set_layer("underlay", False)
    assert not plan.is_underlay_drawn(), (
        "TC-053-044: the switched-off layer still draws the picture"
    )
    plan.set_layer("underlay", True)
    plan.wait_for_element(plan.UNDERLAY_DRAWN)

    plan.reload(garden.site_key)
    plan.wait_for_element(plan.UNDERLAY_DRAWN)
    again = plan.underlay_screen_distance_m(p1, p2)
    assert abs(again - 4.0) <= 0.02, (
        f"TC-053-044: after a reload the points are {again:.3f} m apart"
    )
    backup = json.dumps(export_plan_json(base_url, e2e_seed_data, garden.site_key))
    assert "underlay" not in backup and underlay["attachment_key"] not in backup, (
        "TC-053-044: the JSON backup must not carry the underlay"
    )
    screenshot("053_044_03_reloaded", "Nach dem Neuladen: Unterlage unverändert, nicht im Export")


# ── TC-053-056 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_056_plant_state_layer_attention_filter_and_sun_layer(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-056 - the plant-state layer, its "needs attention" filter, and the sun-window layer (GP-UX-061).

    Precondition (API): three tomatoes in Beet 1, one with an overdue task; Beet 1's sun window is "morning".
    Breaks if the filter is usable without the layer, the layer draws another ring or badge set, the filter keeps
    a plant without a badge or drops the one with it, switching the layer off does not bring the plain markers
    back, or the sun layer draws another value.
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    garden = provision_garden(
        base_url, e2e_seed_data, purpose="tc056", beds=(BedSpec("Beet 1", bed_rect(2.0, 1.0)),)
    )
    bed = garden.bed_key("Beet 1")
    places = ((0.4, 0.5), (1.0, 0.5), (1.6, 0.5))
    planted = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=tomato["key"],
        id_prefix="TOM",
        points=places,
    )
    target, *others = (planted.plant_on(slot) for slot in planted.point_slots)
    overdue_task(base_url, e2e_seed_data, target, f"E2E-GP Kontrolle {unique_tag()}", days_ago=2)
    set_sun_window(base_url, e2e_seed_data, bed, "morning")
    origin = (4.0, 4.5)  # bed_rect(2.0, 1.0) in the 10 x 10 m garden
    on_plan = sorted((round(origin[0] + x, 3), round(origin[1] + y, 3)) for x, y in places)

    plan.open(garden.site_key)
    assert not plan.is_attention_filter_usable(), (
        "TC-053-056: the filter is locked without the layer"
    )
    assert plan.attention_filter_hint() == (
        "Schalte zuerst die Ebene „Pflanzenzustand“ ein, dann kannst du nach Handlungsbedarf filtern."
    ), f"TC-053-056: the locked filter says why: {plan.attention_filter_hint()!r}"
    assert sorted(plan.marker_centres(bed)) == on_plan, (
        "TC-053-056: three plain markers before the layer"
    )
    assert plan.layer_markers() == {}, "TC-053-056: no state markers before the layer"
    screenshot("053_056_01_plain", "Ohne Ebene: drei einfache Marker, Filter gesperrt")

    plan.set_layer("plantState", True)
    plan.wait_for_layer_markers(
        {
            target: {"lifecycle": "active", "badges": ["overdue"]},
            **{key: {"lifecycle": "active", "badges": []} for key in others},
        },
        "TC-053-056: the plant-state layer",
    )
    plan.wait_for_element(plan.LEGEND_PLANT_STATE)
    assert plan.is_attention_filter_usable(), "TC-053-056: the layer unlocks the filter"
    screenshot("053_056_02_layer", "Ebene Pflanzenzustand: Ringe, ein Zeichen, Legende")

    plan.set_attention_filter(True)
    plan.wait_for_layer_markers(
        {target: {"lifecycle": "active", "badges": ["overdue"]}},
        "TC-053-056: the filter keeps only the plant that needs attention",
    )
    screenshot("053_056_03_filter", "Filter: nur die Pflanze mit Handlungsbedarf")

    plan.set_layer("plantState", False)
    plan.wait_for_layer_markers({}, "TC-053-056: without the layer no state marker")
    assert sorted(plan.marker_centres(bed)) == on_plan, (
        "TC-053-056: all three plain markers are back"
    )
    assert not plan.is_attention_filter_usable(), "TC-053-056: the filter is locked again"

    plan.set_layer("sun", True)
    plan.wait_for_sun_layer({bed: "morning"}, "TC-053-056: the sun-window layer")
    assert plan.sun_layer_beds() == {bed: "morning"}, (
        "TC-053-056: the sun layer marks Beet 1 as 'morning'"
    )
    screenshot("053_056_04_sun", "Ebene Sonnenfenster: Muster „Morgens“ über Beet 1")


# ── TC-053-057 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_057_back_up_the_selection_and_import_it_into_another_site(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot, tmp_path: Path
) -> None:
    """TC-053-057 - "Nur die Auswahl" as JSON, imported into another site with that target (GP-FR-172).

    A frame selects Beet A and Beet B of site A; the export dialog previews exactly them. The file the dialog
    downloads is read through the same request (``GET /plan/export?scope=selection&keys=...``) - the browser's
    download folder sits inside the Selenium node - and handed to the import wizard of site B, mode "Hinzufügen",
    target "Aus einem anderen Standort". Breaks if the frame selects another set, the preview or the file holds
    Beet C, the report or the result counts differ, the beds in site B reuse site A's keys or lose their slots,
    or site A changes.
    """
    source = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc057a",
        beds=(
            BedSpec("Beet A", rect(1.0, 4.5, 2.0, 1.0), slots=((0.5, 0.5), (1.5, 0.5))),
            BedSpec("Beet B", rect(4.0, 4.5, 2.0, 1.0)),
            BedSpec("Beet C", rect(7.0, 4.5, 2.0, 1.0)),
        ),
    )
    target = provision_garden(base_url, e2e_seed_data, purpose="tc057b")
    bed_a, bed_b = source.bed_key("Beet A"), source.bed_key("Beet B")
    source_before = read_plan(base_url, e2e_seed_data, source.site_key)

    plan.open(source.site_key)
    plan.marquee_select((0.5, 3.5), (6.5, 6.5), {bed_a, bed_b})
    screenshot("053_057_01_selection", "Auswahlrahmen um Beet A und Beet B")
    plan.open_export()
    plan.choose_export_json()
    plan.choose_export_scope("selection")
    hint = plan.text_of(plan.EXPORT_SCOPE_HINT)
    assert hint.startswith("Genau die 2 ausgewählten Beete und Gartenobjekte"), (
        f"TC-053-057: scope hint {hint!r}"
    )
    plan.wait_for_export_summary(
        "Die Sicherung enthält 2 Standorte, 0 Gartenobjekte und 2 Pflanzplätze",
        "TC-053-057: the preview",
    )
    screenshot("053_057_02_export", "Export: JSON, nur die Auswahl, 2 Standorte und 2 Pflanzplätze")
    plan.download_export()

    document = export_plan_json(
        base_url, e2e_seed_data, source.site_key, scope="selection", keys=(bed_a, bed_b)
    )
    assert (
        sorted(loc["name"] for loc in document["locations"]),
        len(document["slots"]),
        document["plan"],
    ) == (["Beet A", "Beet B"], 2, None), (
        "TC-053-057: the partial file holds Beet A and B, their 2 slots, no plan"
    )
    backup = tmp_path / f"teil-{unique_tag()}.json"
    backup.write_text(json.dumps(document), encoding="utf-8")

    plan.open(target.site_key)
    plan.open_import()
    plan.choose_import_file(str(backup))
    counts = plan.import_report_counts()
    assert counts == [
        "Wird angelegt: 2 Standorte, 0 Gartenobjekte, 2 Pflanzplätze",
        "Wird gelöscht: 0 Standorte, 0 Gartenobjekte, 0 Pflanzplätze",
    ], f"TC-053-057: report counts {counts}"
    plan.wait_for_element(plan.IMPORT_OK)
    screenshot("053_057_03_report", "Import in Standort B: Prüfbericht ohne Probleme")
    plan.import_next()
    plan.choose_import_mode("merge")
    plan.choose_import_target("other_site")
    assert plan.target_hint() == (
        "Die Datei stammt von woanders: Verweise, die nicht in der Datei stehen, entfallen und werden im Bericht genannt."
    ), f"TC-053-057: target hint {plan.target_hint()!r}"
    plan.recheck_import()
    done = plan.apply_import()
    assert done == "Fertig: 2 Standorte, 0 Gartenobjekte und 2 Pflanzplätze wurden angelegt.", (
        f"TC-053-057: success line {done!r}"
    )
    screenshot("053_057_04_done", "Hinzugefügt: 2 Standorte und 2 Pflanzplätze")
    plan.close_import()

    stored = read_plan(base_url, e2e_seed_data, target.site_key)
    assert _names(stored) == ["Beet A", "Beet B"], f"TC-053-057: site B holds {_names(stored)}"
    copied_a = stored_location(stored, "Beet A")
    new_keys = {loc["key"] for loc in stored["locations"]}
    assert not new_keys & set(source.beds.values()), "TC-053-057: imported beds get new keys"
    origins = sorted(
        tuple(slot["geometry"]["origin"])
        for slot in bed_slots(base_url, e2e_seed_data, copied_a["key"])
    )
    assert origins == [(0.5, 0.5), (1.5, 0.5)], (
        f"TC-053-057: the copy of Beet A has slots at {origins}"
    )
    plan.wait_for_object_keys(new_keys, "TC-053-057: the editor of site B after the import")
    source_after = read_plan(base_url, e2e_seed_data, source.site_key)
    assert sorted(loc["key"] for loc in source_after["locations"]) == sorted(
        loc["key"] for loc in source_before["locations"]
    ), "TC-053-057: site A is unchanged"
    screenshot("053_057_05_target", "Standort B zeigt Beet A und Beet B")


# ── TC-053-058 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_058_restore_an_earlier_state_after_a_report_and_the_site_name(
    plan: GardenPlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-058 - an earlier state is restored after its dry run and the typed site name (GP-FR-148/170).

    Precondition (API): Beet A-C, then Beet D added, then a backup without Beet D written over it with "Ersetzen"
    - which leaves exactly one earlier state (four beds). Breaks if the list misses it, the report counts differ,
    the restore is possible without the right name, the plan is not the earlier state afterwards, or the
    overwritten state is not kept as a snapshot of its own.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc058",
        beds=(
            BedSpec("Beet A", rect(1.0, 6.0, 2.0, 1.0)),
            BedSpec("Beet B", rect(4.0, 6.0, 2.0, 1.0)),
            BedSpec("Beet C", rect(7.0, 6.0, 2.0, 1.0)),
        ),
    )
    first = export_plan_json(base_url, e2e_seed_data, garden.site_key)
    add_bed_via_batch(
        base_url,
        e2e_seed_data,
        site_key=garden.site_key,
        name="Beet D",
        geometry=rect(4.0, 2.0, 2.0, 1.0),
    )
    replace_plan_with(
        base_url,
        e2e_seed_data,
        site_key=garden.site_key,
        site_name=garden.site_name,
        document=first,
    )
    snapshots = plan_snapshots(base_url, e2e_seed_data, garden.site_key)
    assert [s["locations"] for s in snapshots] == [4], (
        f"Precondition: one earlier state with 4 beds: {snapshots}"
    )
    audit = snapshots[0]["audit_key"]

    plan.open(garden.site_key)
    assert len(plan.object_keys()) == 3, "Precondition: the plan shows the three beds of the backup"
    plan.open_import()
    plan.open_snapshots()
    rows = plan.snapshot_rows()
    assert (
        list(rows) == [audit] and "4 Standorte, 0 Gartenobjekte, 0 Pflanzplätze" in rows[audit]
    ), f"TC-053-058: the list of earlier states reads {rows}"
    plan.choose_snapshot(audit)
    counts = plan.snapshot_report_counts()
    assert counts == [
        "Wird angelegt: 4 Standorte, 0 Gartenobjekte, 0 Pflanzplätze",
        "Wird gelöscht: 3 Standorte, 0 Gartenobjekte, 0 Pflanzplätze",
    ], f"TC-053-058: restore report {counts}"
    assert plan.text_of(plan.SNAPSHOTS_NOTICE).startswith(
        "Der jetzige Plan wird vorher selbst als Stand gespeichert"
    ), f"TC-053-058: notice {plan.text_of(plan.SNAPSHOTS_NOTICE)!r}"
    assert not plan.is_restore_enabled(), "TC-053-058: no restore without the site name"
    plan.type_snapshot_confirm_name(f"{garden.site_name}-falsch")
    assert not plan.is_restore_enabled(), "TC-053-058: no restore with a wrong name"
    plan.type_snapshot_confirm_name(garden.site_name)
    assert plan.is_restore_enabled(), "TC-053-058: the right name unlocks the restore"
    assert len(plan_snapshots(base_url, e2e_seed_data, garden.site_key)) == 1, (
        "TC-053-058: the check writes nothing"
    )
    screenshot("053_058_01_report", "Früherer Stand: Bericht, Hinweis, Name eingegeben")

    done = plan.restore_snapshot()
    assert done == (
        "Fertig: 4 Standorte, 0 Gartenobjekte und 0 Pflanzplätze wurden angelegt. "
        "Der vorherige Stand liegt im Änderungsprotokoll."
    ), f"TC-053-058: success line {done!r}"
    screenshot("053_058_02_done", "Wiederhergestellt, vorheriger Stand gesichert")
    plan.close_import()

    stored = read_plan(base_url, e2e_seed_data, garden.site_key)
    assert _names(stored) == ["Beet A", "Beet B", "Beet C", "Beet D"], (
        f"TC-053-058: plan holds {_names(stored)}"
    )
    after = plan_snapshots(base_url, e2e_seed_data, garden.site_key)
    assert [s["locations"] for s in after] == [3, 4], (
        f"TC-053-058: earlier states after the restore {after}"
    )
    keys = {loc["key"] for loc in stored["locations"]}
    plan.wait_for_object_keys(keys, "TC-053-058: the editor after the restore")
    screenshot("053_058_03_plan", "Plan zeigt wieder Beet A bis Beet D")
    assert len(keys) == 4, f"TC-053-058: four beds after the restore, stored {sorted(keys)}"


# ── TC-053-059 ──────────────────────────────────────────────────────────────


def test_tc_053_059_field_mode_sun_window_chips_store_with_one_tap(
    browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-059 - sun-window chips in the field-mode bed sheet at 390 x 844 (GP-FR-158/159, GP-UX-057).

    One tap on "Nachmittags" stores the window (no save button), "6,5" + Enter stores the summer hours, and a
    fresh field mode shows both. The hours are typed into a freshly opened sheet (see the comment there). Breaks if a chip is smaller than the 64 px kiosk target, the tap does not store,
    the hours are stored as another number, or a reload shows something else.
    """
    set_phone_viewport(browser, 390, 844)
    field = FieldModePage(browser, base_url)
    garden = provision_garden(
        base_url, e2e_seed_data, purpose="tc059", beds=(BedSpec("Beet 1", bed_rect(2.0, 1.0)),)
    )
    bed = garden.bed_key("Beet 1")
    assert sun_profile(base_url, e2e_seed_data, bed).get("sun_window") in (None, "unknown"), (
        "Precondition: no sun window stored"
    )

    field.open(garden.site_key)
    field.tap_bed(bed)
    assert field.checked_sun_window() == "unknown", (
        "TC-053-059: 'Nicht bekannt' is chosen before anything is stored"
    )
    sizes = field.sun_chip_sizes()
    small = {window: size for window, size in sizes.items() if min(size) < TOUCH_PX}
    assert len(sizes) == 6 and not small, (
        f"TC-053-059: every chip measures >= {TOUCH_PX} px; too small: {small}"
    )
    screenshot("053_059_01_sheet", "Feldmodus 390 px: Abschnitt „Sonne am Beet“")

    field.tap_sun_chip("afternoon")
    _wait_stored(
        browser,
        lambda: sun_profile(base_url, e2e_seed_data, bed).get("sun_window"),
        "afternoon",
        "TC-053-059: one tap on 'Nachmittags'",
    )
    # A fresh sheet before typing: the stored chip makes the page reload its bed list, and a reload that lands
    # while the hours are being typed resets the field's draft (``SunWindowFields`` takes a changed stored value
    # over the draft). Waiting for that reload has no signal on the page, so the sheet is opened anew instead.
    field.open(garden.site_key)
    field.tap_bed(bed)
    assert field.checked_sun_window() == "afternoon", (
        "TC-053-059: the tapped chip is shown after a reload"
    )
    field.enter_sun_hours("6,5")
    stored = _wait_stored(
        browser,
        lambda: (lambda p: (p.get("sun_window"), p.get("direct_sun_hours_summer")))(
            sun_profile(base_url, e2e_seed_data, bed)
        ),
        ("afternoon", 6.5),
        "TC-053-059: the hours '6,5' with Enter",
    )
    assert stored == ("afternoon", 6.5)
    screenshot("053_059_02_stored", "Nachmittags gewählt, 6,5 Stunden gespeichert")

    field.open(garden.site_key)
    field.tap_bed(bed)
    assert (field.checked_sun_window(), field.sun_hours_text()) == ("afternoon", "6,5"), (
        f"TC-053-059: after a reload the sheet shows {(field.checked_sun_window(), field.sun_hours_text())}"
    )
    screenshot("053_059_03_reloaded", "Nach dem Neuladen: Nachmittags und 6,5")
