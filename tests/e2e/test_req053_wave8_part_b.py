"""E2E of REQ-053 wave 8 part B - companion layer, site features, reach, bed photos, CSV bed list, frost reason (WP 8.31, #2674).

Spec pin REQ-053 v1.9. Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md, rows "abgeleitet"):
  TC-053-072  ->  layer "Mischkultur": solid / dashed / dotted lines for good / bad / unknown neighbours, the     (GP-FR-134)
                  card names status, pair, reason and score, the legend shows the same dash, no line at the
                  cluster zoom, none without the layer, the planting dialog names the same bad neighbour
  TC-053-073  ->  "Standortmerkmale": frost risk, cold-air pocket, wind, slope, aspect, access sides as choices    (GP-FR-162/163/168)
                  with help texts; stored, shown in the bed head after a reload, frost risk set back
  TC-053-074  ->  site hints of the planting dialog: frost, wind, waterlogging - one each where the bed and the  (GP-FR-161)
                  species meet, none on an unknown or a sheltered bed, never blocking (the run is created)
  TC-053-075  ->  field mode on a phone: "Feucht / Normal / Trocken" and "Windig" store with one tap, toggle,    (GP-UX-057)
                  survive a fresh field mode, every chip >= 64 px, no sideways scroll
  TC-053-076  ->  reach hint "Beet zu breit": by width and access sides, never an error, never blocking;        (GP-FR-166)
                  widening a bed in the editor brings it
  TC-053-077  ->  photos tab: empty state, a text file refused; (full) two photos, cover, remove, no photo in    (GP-FR-051)
                  the JSON backup
  TC-053-078  ->  field mode: "Foto vom Beet" measures >= 64 px and is on screen; (full) the photo lands in the  (GP-FR-051)
                  bed's gallery, not the plant's, and becomes the cover
  TC-053-079  ->  bed list CSV: default columns, two site columns on top, the Excel variant, the formula name    (GP-FR-145/175)
                  prefixed with ', no download without a column
  TC-053-080  ->  bed list CSV: the assignment only with the opt-in, its privacy note, not remembered          (GP-FR-175, SR-024)
  TC-053-081  ->  CSV bed list import: dry-run report with the line errors and the formula warning, cancel      (GP-FR-174)
                  writes nothing, confirm writes the four valid beds side by side and selects them in the editor
  TC-053-082  ->  frost reason of the plant state: only a "Hoch" bed at a site with a predicted frost; frost   (§11.4, GP-FR-162)
                  before an overdue task; no reason without a forecast

The TC texts were written ahead of the product (their quoted strings are placeholders); where the product differs the
test follows the product and says so in its docstring. Corrections, in short:
  TC-053-072  Companion lines join neighbouring PLANTED SLOTS INSIDE ONE BED (``GET /locations/{key}/companion-edges``),
              not neighbouring beds: the arrangement is one bed with a tomato and three neighbours. The "unknown"
              species is chicory (no relation to the tomato; the sunflower is incompatible through the enrichment). The cluster stage needs the fit zoom of a
              large garden (200 x 200 m), where 30 cm spacing falls below the 10 px marker threshold.
  TC-053-073  The features live in the bed view ("Merkmale ändern" -> "Standortmerkmale: <Beet>"), not in the editor's
              properties panel. The cold-air pocket is called "Kaltluftsee"; the aspect is entered and shown as
              degrees ("Ausrichtung 200°") - nothing is derived (§29), so no "Süd-Südwest"; access sides are four
              toggles N/E/S/W ("beidseitig" = Ost + West); the head shows "Frostrisiko: Hoch" as text (no
              snowflake) and the drainage as its own fact; the water regime is not part of the head.
  TC-053-074  "Beet N" (waterlogging) is its own case; the hint needed ``waterlogging_tolerance`` in
              ``SpeciesResponse``, which the first run found missing and #2765 added.
              "Staunass" is the drainage "Schlecht" (``poor``); the texts are the product's: "… ist frostempfindlich,
              und die Frostgefahr an diesem Beet ist erhöht." etc. The seeded tomato has no light requirement, so no
              light verdict is shown next to the axis hints (not asserted).
  TC-053-076  Reach reads the ACCESS SIDES only, not adjacent paths: "Breit mit Weg" is arranged with access
              Ost + West, and "Grenzwert" (1,2 m) needs both sides recorded - with unknown access the one-side value
              0,6 m applies and 1,2 m would already be "too wide". "Breit mit Weg" (1,3 m, both sides) DOES show the
              hint: 1,3 m is above the two-side value 1,2 m - the TC's "no hint" contradicts its own threshold. The hint is shown in the bed head ("Beet zu breit"
              plus a detail line with width and threshold), not as a badge on the plan.
  TC-053-077  The upload accepts PNG (the fixture pictures are generated PNGs, one colour each, so the attachment
              store's SHA-256 dedup cannot merge them); a text file is refused by the capture panel with "Nicht
              unterstütztes Bildformat. Erlaubt sind JPEG und PNG." The "Beet-Sheet der Zusammenfassung" is read as the
              server's summary (``cover_photo_ref``).
  TC-053-079  The entry is "Plan exportieren …" -> format "Beetliste (CSV)". The header holds the machine column ids
              (``name,type,area_m2,…``), not German titles; "Sonne" is the column "Sonneneinstrahlung"
              (``sun_exposure``); enum cells carry API values (``full_sun``, ``high``).
  TC-053-080  The switch is "Zuweisungen einschließen", the column ``assigned_to``. "Anna Beispiel" is the acting
              account's own display name: the E2E stack seeds no second member to assign.
  TC-053-081  The entry is "Beetliste importieren (CSV) …" in "Export & Import" (not a file type inside "Sicherung
              einspielen"). "=Beet4" becomes "Beet4" with the warning "Ein Formelzeichen am Anfang (= + - @) wurde
              entfernt." Not automated: the "Gärtner" half (no second account with that role is seeded).
  TC-053-082  The frost badge is the hexagon with a star ("Sechseck mit Stern: Frostgefahr"), not a snowflake. "Beet D"
              cannot carry an open finding (a finding is a REQ-044 detection; no route the E2E stack drives writes one):
              it carries an overdue task instead, and the one badge is then the frost (frost before overdue,
              GP-UX-060). Not automated: the early-warning notification (a Celery beat task).

Device: TC-053-075 and TC-053-078 run on a phone. On the desktop profile the browser is put at exactly 390 x 844
(``set_phone_viewport``); on the ``mobile`` profile the CDP emulation fixes the viewport at 393 x 852, which the
``phone`` fixture reads back and records (``record_property("phone_viewport", ...)``); the tablet profile is no phone
and skips them. Every other case is a desktop case (``requires_desktop``). The photo uploads need the full profile:
only ``backend-full`` mounts writable attachment storage (as TC-053-044).

Preconditions are self-provisioned through the application's own API, one fresh site per test with a UUID-derived
name (`_garden_plan_helpers.py`), species from the seed catalogue. ONE named exception: TC-053-082's weather forecast
(``store_frost_forecast``), which only the weather fetch task writes (see its docstring).

Waits are anchored on state - a closed dialog, a checked input, a drawn line, a card's status, a saved download, a
check report, the stored record - never on time, and there is no retry loop. Every written outcome is read back from
the server.
"""

from __future__ import annotations

import csv
import io
import json
import struct
import uuid
import zlib
from pathlib import Path

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from ._garden_plan_helpers import (
    BedSpec,
    acting_member,
    assign_bed,
    bed_photos,
    bed_summary,
    companion_edges,
    create_zone,
    edge_between,
    export_plan_json,
    mark_neighbours,
    overdue_task,
    patch_location,
    plant_on_positions,
    plant_photos,
    plant_states,
    provision_garden,
    read_plan,
    rect,
    runs_of_bed,
    site_conditions,
    soil_profile_of,
    species,
    store_frost_forecast,
    stored_location,
    tenant_key_of,
    tenant_location,
)
from .pages.bed_list_csv_page import BedCsvImportPanel, BedListExportDialog
from .pages.bed_site_page import BedPhotosTab, SiteConditionsDialog
from .pages.bed_view_page import BedViewPage
from .pages.field_mode_page import FieldModePage, set_phone_viewport
from .pages.garden_plan_page import GardenPlanPage

TOMATO = "Solanum lycopersicum"
BASIL = "Ocimum basilicum"
FENNEL = "Foeniculum vulgare"
#: The "unknown" neighbour: chicory has no companion relation to the tomato in either direction, neither in
#: ``companion_planting.yaml`` nor from the plant-info enrichment (checked against the running stack with
#: ``GET /companion-planting/species/{key}/compatible|incompatible``). The sunflower looked unrelated in the seed
#: file but the enrichment adds "Allelopathie: Heliannuole hemmen Tomatenwachstum" (incompatible).
CHICORY = "Cichorium intybus"

#: The kiosk touch target of field mode (GP-UX-023, ``KIOSK_TOUCH_TARGET`` in ``src/frontend/src/kiosk/kioskTheme.ts``).
TOUCH_PX = 64
#: The phone of the TC texts; the ``mobile`` profile's emulation is 393 x 852 instead (recorded per test).
PHONE = (390, 844)
#: How long a server-side effect of one tap or save may take to be readable (a request, not an animation).
STORED_WITHIN_S = 15

PHOTOS_NEED_STORAGE = (
    "needs the full E2E profile: only backend-full has writable attachment storage "
    "(docker-compose.e2e.yml, object-storage-full); the light backend refuses the upload"
)

#: GP-FR-145's pre-selected columns, in file order (``bed_list_csv_engine.DEFAULT_COLUMNS``).
DEFAULT_COLUMNS = [
    "name",
    "type",
    "area_m2",
    "status",
    "soil_texture",
    "irrigation_zone",
    "active_plants",
]


# ── fixtures and local helpers ──────────────────────────────────────────────


@pytest.fixture
def plan(browser: WebDriver, base_url: str) -> GardenPlanPage:
    return GardenPlanPage(browser, base_url)


@pytest.fixture
def bed_view(browser: WebDriver, base_url: str) -> BedViewPage:
    return BedViewPage(browser, base_url)


@pytest.fixture
def phone(browser: WebDriver, device_profile: dict, record_property) -> tuple[int, int]:
    """A phone viewport: 390 x 844 on the desktop profile, the emulated 393 x 852 on ``mobile`` (read back, recorded)."""
    name = device_profile["name"]
    if name == "tablet":
        pytest.skip(
            "a phone case: the tablet profile emulates 820 x 1180 (no phone); it runs on desktop (390 x 844) "
            "and mobile (393 x 852)"
        )
    if name == "mobile":
        inner = browser.execute_script("return [window.innerWidth, window.innerHeight];")
        actual = (int(inner[0]), int(inner[1]))
        expected = (int(device_profile["width"]), int(device_profile["height"]))
        if actual != expected:
            raise AssertionError(
                f"the mobile profile should emulate {expected[0]} x {expected[1]}, the page has {actual}"
            )
    else:
        actual = set_phone_viewport(browser, *PHONE)
    record_property("phone_viewport", f"{actual[0]}x{actual[1]} ({name})")
    return actual


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


def _png(path: Path, size: int = 96) -> Path:
    """A solid-colour PNG of *size* x *size* px in a colour unique to this call (UUID-derived).

    Unique bytes on purpose: the attachment store deduplicates an uploader's identical bytes (SHA-256), so two
    copies of one fixture would become one photo and a "two photos" case would test nothing.
    """
    colour = uuid.uuid4().bytes[:3]
    raw = b"".join(b"\x00" + colour * size for _ in range(size))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    return path


def _csv_rows(
    saved: dict, what: str, delimiter: str = ","
) -> tuple[list[str], dict[str, dict[str, str]]]:
    """Header and rows (by the ``name`` cell) of a saved bed-list download; loud without BOM or header."""
    text = saved["text"]
    if saved.get("head") != [0xEF, 0xBB, 0xBF] or not text.startswith("﻿"):
        raise AssertionError(
            f"{what}: the file does not start with the UTF-8 BOM: {saved.get('head')}"
        )
    lines = list(csv.reader(io.StringIO(text[1:], newline=""), delimiter=delimiter))
    if not lines:
        raise AssertionError(f"{what}: the file has no header row")
    header = lines[0]
    rows = [dict(zip(header, line, strict=True)) for line in lines[1:] if line]
    if "name" not in header:
        return header, {str(i): row for i, row in enumerate(rows)}
    return header, {row["name"]: row for row in rows}


def _overlap(a: dict, b: dict) -> bool:
    """Whether two unrotated rects overlap with a positive area."""
    ax, ay = a["origin"]
    bx, by = b["origin"]
    return (
        ax < bx + b["width_m"] - 1e-9
        and bx < ax + a["width_m"] - 1e-9
        and ay < by + b["length_m"] - 1e-9
        and by < ay + a["length_m"] - 1e-9
    )


# ── TC-053-072 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_072_companion_layer_draws_good_bad_and_unknown_neighbours(
    plan: GardenPlanPage,
    bed_view: BedViewPage,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
    screenshot_dir,
) -> None:
    """TC-053-072 — layer "Mischkultur": three line styles, the card, the legend, cluster zoom, off (GP-FR-134).

    Precondition (API): a 200 x 200 m garden with one 3 x 3 m bed in its middle; a tomato in the bed's centre and,
    one metre away each, a basil (compatible), a fennel (incompatible) and a chicory (no relation); each of the
    three is marked as the tomato's neighbour (``PUT /slots/{a}/adjacent/{b}``). The server's judgement is the
    precondition (compatible / incompatible / unknown, read from ``companion-edges``). In the editor at 100 %: no line
    before the layer is on; with it, the three pairs are drawn solid / dashed ``8 5`` / dotted ``0.1 5`` (three
    distinct dash patterns - the status is never colour only); hovering each line opens the card with the server's
    status, the pair, the reason text and - for the good pair only - "Bewertung: …"; the legend shows the three rows
    with the same dashes and the product's words. At the fit zoom (cluster stage) the layer draws no line and the page
    shows no error; switched off, the layer is gone. The planting dialog for a tomato names "Ungünstiger Nachbar im
    Beet". Breaks if a status is drawn wrong or only by colour, if the card disagrees with the server, if the cluster
    zoom still draws lines, or if the dialog and the line disagree.

    Spec corrections: lines join neighbouring planted slots inside ONE bed (not neighbouring beds); chicory is
    the species without a relation; the cluster stage is the fit zoom of a large garden.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc072",
        boundary=rect(0.0, 0.0, 200.0, 200.0),
        beds=(BedSpec("Mischbeet", rect(98.5, 98.5, 3.0, 3.0)),),
    )
    bed = garden.bed_key("Mischbeet")
    keys = {
        name: species(base_url, e2e_seed_data, name)["key"]
        for name in (TOMATO, BASIL, FENNEL, CHICORY)
    }
    slot_of: dict[str, str] = {}
    for name, point, prefix in (
        (TOMATO, (1.5, 1.5), "TOM"),
        (BASIL, (0.5, 1.5), "BAS"),
        (FENNEL, (2.5, 1.5), "FEN"),
        (CHICORY, (1.5, 0.5), "CHI"),
    ):
        planted = plant_on_positions(
            base_url,
            e2e_seed_data,
            bed_key=bed,
            species_key=keys[name],
            id_prefix=prefix,
            points=(point,),
        )
        slot_of[name] = planted.point_slots[0]
    expected_status = {BASIL: "compatible", FENNEL: "incompatible", CHICORY: "unknown"}
    for other in expected_status:
        mark_neighbours(base_url, e2e_seed_data, slot_of[TOMATO], slot_of[other])
    edges = companion_edges(base_url, e2e_seed_data, bed)
    server = {
        other: edge_between(edges, slot_of[TOMATO], slot_of[other]) for other in expected_status
    }
    judged = {other: edge["status"] for other, edge in server.items()}
    assert judged == expected_status, (
        f"TC-053-072 precondition: the server must judge basil/fennel/chicory as {expected_status}, it judges {judged}"
    )

    plan.open(garden.site_key)
    plan.zoom_in_until(100)
    assert not plan.is_layer_on("companion"), "TC-053-072: the layer 'Mischkultur' starts off"
    assert not plan.is_present(plan.COMPANION_LAYER), (
        "TC-053-072: no companion line before the layer is on"
    )
    plan.set_layer("companion", True)
    pairs = [(slot_of[TOMATO], slot_of[other]) for other in expected_status]
    line_of = plan.wait_for_companion_pairs(bed, pairs, "TC-053-072: the layer switched on")
    lines = plan.companion_lines()
    drawn = {other: lines[line_of[(slot_of[TOMATO], slot_of[other])]] for other in expected_status}
    assert {other: line["status"] for other, line in drawn.items()} == expected_status, (
        f"TC-053-072: each line carries the server's status: {drawn}"
    )
    assert (drawn[BASIL]["dash"], drawn[FENNEL]["dash"], drawn[CHICORY]["dash"]) == (
        "none",
        "8 5",
        "0.1 5",
    ), f"TC-053-072: solid / dashed / dotted for good / bad / unknown: {drawn}"
    screenshot("053_072_01_layer_on", "Ebene Mischkultur: durchgezogen, gestrichelt, gepunktet")

    for other in (BASIL, FENNEL, CHICORY):
        edge = server[other]
        card = plan.hover_companion_line(
            line_of[(slot_of[TOMATO], slot_of[other])], expected_status[other]
        )
        # The card names "the two species that decided it" (CompanionEdgeInfo.tsx:12/43); an unknown line has no
        # deciding pair, so it shows none - the server's `deciding` is the oracle for which lines must name one.
        assert bool(edge.get("deciding")) == (expected_status[other] != "unknown"), (
            f"TC-053-072: precondition - good and bad lines carry a deciding pair, the unknown one none: {edge}"
        )
        if edge.get("deciding"):
            assert card["pair"], f"TC-053-072: the card names the deciding pair of {other}: {card}"
        else:
            assert card["pair"] == "", (
                f"TC-053-072: no deciding pair, no pair line ({other}): {card}"
            )
        reason = (
            f"Grund: {edge['reason']}"
            if edge.get("reason")
            else {
                "compatible": "Diese Arten fördern sich als Nachbarn.",
                "incompatible": "Diese Arten hemmen sich als Nachbarn.",
                "unknown": "Für diese Nachbarn ist keine Mischkultur-Beziehung hinterlegt.",
            }[expected_status[other]]
        )
        assert card["reason"] == reason, f"TC-053-072: the card's reason for {other}: {card}"
        if edge.get("score") is not None:
            score = f"{round(float(edge['score']), 2):g}".replace(".", ",")
            assert card["score"] == f"Bewertung: {score} von 1", (
                f"TC-053-072: the score for {other}: {card}"
            )
        else:
            assert card["score"] == "", (
                f"TC-053-072: no score without a compatible pair ({other}): {card}"
            )
    assert server[BASIL].get("score") is not None, (
        f"TC-053-072: the good pair carries a score in plain text: {server[BASIL]}"
    )
    # Viewport-only: a full-page capture resizes the viewport under the resting pointer and closes the card.
    plan.take_screenshot("053_072_02_card", screenshot_dir)

    legend = plan.companion_legend_rows()
    assert {status: row["dash"] for status, row in legend.items()} == {
        "compatible": "none",
        "incompatible": "8 5",
        "unknown": "0.1 5",
    }, f"TC-053-072: the legend draws the same three dashes: {legend}"
    assert {status: row["text"] for status, row in legend.items()} == {
        "compatible": "Durchgezogen: gute Nachbarn (fördern sich)",
        "incompatible": "Gestrichelt: schlechte Nachbarn (hemmen sich)",
        "unknown": "Gepunktet: keine Angabe zu diesem Paar",
    }, f"TC-053-072: the legend explains colour and line style: {legend}"

    plan.zoom_out_to_fit()
    try:
        plan.poll().until(lambda _d: not plan.is_present(plan.COMPANION_LAYER))
    except TimeoutException as exc:
        raise AssertionError(
            f"TC-053-072: the cluster zoom ({plan.zoom_percent()} %) still draws companion lines: "
            f"{plan.companion_lines()}"
        ) from exc
    assert plan.is_layer_on("companion"), (
        "TC-053-072: the layer stays on at the cluster zoom - only its lines go"
    )
    assert not plan.is_error_displayed(), "TC-053-072: the cluster zoom shows no error"
    screenshot("053_072_03_cluster", "Cluster-Stufe: keine Verbindungslinien, keine Fehlermeldung")

    # Back at a readable zoom the lines return - so their absence above was the zoom, not a lost layer - and only
    # then is the layer switched off, so "gone without the layer" is measured against lines that were drawn.
    plan.zoom_in_until(100)
    plan.wait_for_companion_pairs(bed, pairs, "TC-053-072: back at 100 %")
    plan.set_layer("companion", False)
    try:
        plan.poll().until(lambda _d: not plan.is_present(plan.COMPANION_LAYER))
    except TimeoutException as exc:
        raise AssertionError(
            "TC-053-072: the companion layer stays drawn after switching it off"
        ) from exc

    bed_view.open(bed, "planting")
    dialog = bed_view.open_planting_dialog()
    dialog.choose_species(TOMATO)
    _severity, hint = dialog.wait_for_hint(keys[TOMATO], "TC-053-072: the tomato beside the fennel")
    assert "Ungünstiger Nachbar im Beet" in hint, (
        f"TC-053-072: the planting dialog names the bad neighbour the red line shows: {hint!r}"
    )
    screenshot(
        "053_072_04_planting_hint", "Bepflanzen: ungünstiger Nachbar wie die gestrichelte Linie"
    )


# ── TC-053-073 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_073_site_features_are_choices_stored_and_shown_in_the_bed_head(
    bed_view: BedViewPage,
    browser: WebDriver,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-073 — "Standortmerkmale": frost risk, cold-air pocket, wind, slope, aspect, access (GP-FR-162/163/168).

    Precondition (API): "Beet 1" (2 x 1 m) with drainage "Gut" and no site features. In the dialog: every chip group
    has a title and a help text and holds only radios (frost, wind) or checkboxes (access) - no free text; the slope
    field is empty (nothing inherited from the site). Chosen: frost "Hoch", "Kaltluftsee" on, wind "Windausgesetzt",
    slope 8, aspect 200, access Ost + West; saved. The server holds exactly these values; after a reload the head reads
    "Frostrisiko: Hoch · Kaltluftsee · Wind: Windausgesetzt · Hang 8° · Ausrichtung 200° · Zugang: Ost, West" and the
    drainage "Gut", and the reopened dialog shows the same choices. Frost set back to "Normal" is stored and shown.
    Breaks if a choice is not stored or stored as something else, if the head or the dialog shows another value after
    the reload, or if a slope appears without an entry.

    Spec corrections: the dialog sits in the bed view, not the editor panel; "Kaltluftsee"; the aspect is shown as
    degrees (nothing is derived); access = four toggles ("beidseitig" = Ost + West); the head shows the frost risk as
    text (no snowflake) and the drainage, not the water regime.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc073",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet 1")
    patch_location(base_url, e2e_seed_data, bed, {"soil_profile": {"drainage": "good"}})
    before = site_conditions(base_url, e2e_seed_data, bed)
    assert (before.get("microclimate") or {}).get("frost_risk") in (
        None,
        "unknown",
    ) and not before.get("access_sides"), (
        f"TC-053-073 precondition: no site features recorded: {before}"
    )

    bed_view.open(bed, "soil")
    bed_view.open_site_dialog()
    dialog = SiteConditionsDialog(browser, base_url)
    for group, role, kind in (
        ("frost", "radiogroup", "radio"),
        ("heat", "radiogroup", "radio"),
        ("wind", "radiogroup", "radio"),
        ("access", "group", "checkbox"),
    ):
        info = dialog.group_info(group)
        assert info["role"] == role and info["title"] and info["hint"], (
            f"TC-053-073: the group {group!r} has a title and a help text: {info}"
        )
        assert {input_type for _value, input_type in info["inputs"]} == {kind}, (
            f"TC-053-073: {group!r} is a choice ({kind}), no free text: {info['inputs']}"
        )
        assert not dialog.has_free_text_for(group), f"TC-053-073: {group!r} holds no text field"
    assert dialog.checked("frost") == ["unknown"], "TC-053-073: frost risk starts at 'Unbekannt'"
    assert dialog.degrees("slope") == "", (
        "TC-053-073: no slope inherited from the site - the field is empty"
    )

    dialog.choose("frost", "high")
    dialog.set_cold_air_pocket(True)
    dialog.choose("wind", "exposed")
    dialog.enter_degrees("slope", "8")
    dialog.enter_degrees("aspect", "200")
    dialog.toggle("access", "E")
    dialog.toggle("access", "W")
    screenshot(
        "053_073_01_dialog",
        "Standortmerkmale: Frost hoch, Kaltluftsee, windausgesetzt, 8°, 200°, Ost+West",
    )
    dialog.save_and_wait_closed("TC-053-073: saving the site features")

    stored = site_conditions(base_url, e2e_seed_data, bed)
    microclimate = stored.get("microclimate") or {}
    assert (
        microclimate.get("frost_risk"),
        microclimate.get("cold_air_pocket"),
        stored.get("wind_exposure"),
        stored.get("slope_deg"),
        stored.get("aspect_deg"),
        sorted(stored.get("access_sides") or []),
    ) == ("high", True, "exposed", 8.0, 200.0, ["E", "W"]), (
        f"TC-053-073: the stored site features: {stored}"
    )

    bed_view.open(bed, "soil")
    line = bed_view.wait_for_head_site_line(
        "Frostrisiko: Hoch", "TC-053-073: the head after a reload"
    )
    for fragment in (
        "Frostrisiko: Hoch",
        "Kaltluftsee",
        "Wind: Windausgesetzt",
        "Hang 8°",
        "Ausrichtung 200°",
        "Zugang: Ost, West",
    ):
        assert fragment in line, f"TC-053-073: the head names {fragment!r}: {line!r}"
    drainage = bed_view.head_drainage()
    assert drainage is not None and drainage.endswith("Gut"), (
        f"TC-053-073: the head shows the drainage 'Gut' beside the site features: {drainage!r}"
    )
    screenshot("053_073_02_head", "Beetkopf nach dem Neuladen: Standortmerkmale und Drainage")

    bed_view.open_site_dialog()
    dialog = SiteConditionsDialog(browser, base_url)
    shown = (
        dialog.checked("frost"),
        dialog.checked("wind"),
        sorted(dialog.checked("access")),
        dialog.degrees("slope"),
        dialog.degrees("aspect"),
    )
    assert shown == (["high"], ["exposed"], ["E", "W"], "8", "200"), (
        f"TC-053-073: the reopened dialog shows the stored choices: {shown}"
    )
    dialog.choose("frost", "normal")
    dialog.save_and_wait_closed("TC-053-073: frost risk back to 'Normal'")
    _wait_stored(
        browser,
        lambda: (site_conditions(base_url, e2e_seed_data, bed).get("microclimate") or {}).get(
            "frost_risk"
        ),
        "normal",
        "TC-053-073: frost risk 'Normal'",
    )
    bed_view.wait_for_head_site_line(
        "Frostrisiko: Normal", "TC-053-073: the head after setting 'Normal'"
    )
    screenshot("053_073_03_normal", "Frostrisiko wieder Normal")


# ── TC-053-074 ──────────────────────────────────────────────────────────────


def _axis_hints_of(bed_view: BedViewPage, bed_key: str, species_key: str, what: str):
    """Open "Bepflanzen" on *bed_key* with a tomato; return the dialog and its axis hints for *species_key*."""
    bed_view.open(bed_key, "planting")
    dialog = bed_view.open_planting_dialog()
    dialog.choose_species(TOMATO)
    dialog.wait_for_hint(species_key, f"{what}: the hint block")
    return dialog, dialog.site_axis_hints(species_key)


@pytest.mark.requires_desktop
def test_tc_053_074_site_hints_for_frost_and_wind_never_block(
    bed_view: BedViewPage,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-074 — the planting dialog's frost and wind hints, one per matching bed, never blocking (GP-FR-161).

    Precondition (API): the seeded tomato is frost-sensitive and needs support (read from the catalogue, loud
    otherwise). Four beds: "Beet F" frost risk "Hoch", "Beet W" wind "Windausgesetzt", "Beet U" nothing recorded,
    "Beet G" frost "Normal", wind "Geschützt", drainage "Gut". For each bed the dialog "Bepflanzen" with a tomato
    shows exactly: F ``frost_mismatch``, W ``wind_support_needed``, U and G none - each a warning (never an error)
    with the product's sentence. In "Beet F" the run is created despite the hint (the server lists it). Breaks if a
    hint is missing, appears on the wrong bed, is shown as an error, or blocks the planting.

    The waterlogging bed ("Beet N") is its own case below (it was held by a product defect, fixed in #2765).

    Spec corrections: the texts are the product's; the seeded tomato has no light requirement, so the light verdict
    beside the axis hints is not asserted.
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    assert (tomato.get("frost_sensitivity"), tomato.get("support_required")) == (
        "sensitive",
        True,
    ), f"TC-053-074 precondition: the seeded tomato is frost-sensitive and needs support: {tomato}"
    beds = tuple(
        BedSpec(f"Beet {tag}", rect(0.5 + 2.2 * i, 1.0, 1.5, 2.0)) for i, tag in enumerate("FWUG")
    )
    garden = provision_garden(base_url, e2e_seed_data, purpose="tc074", beds=beds)
    key = {tag: garden.bed_key(f"Beet {tag}") for tag in "FWUG"}
    patch_location(
        base_url,
        e2e_seed_data,
        key["F"],
        {"site_conditions": {"microclimate": {"frost_risk": "high"}}},
    )
    patch_location(
        base_url, e2e_seed_data, key["W"], {"site_conditions": {"wind_exposure": "exposed"}}
    )
    patch_location(
        base_url,
        e2e_seed_data,
        key["G"],
        {
            "site_conditions": {
                "microclimate": {"frost_risk": "normal"},
                "wind_exposure": "sheltered",
            },
            "soil_profile": {"drainage": "good"},
        },
    )
    expected = {
        "F": {
            "frost_mismatch": "ist frostempfindlich, und die Frostgefahr an diesem Beet ist erhöht."
        },
        "W": {
            "wind_support_needed": "braucht eine Stütze, und dieses Beet ist dem Wind ausgesetzt."
        },
        "U": {},
        "G": {},
    }

    for number, tag in enumerate("WUGF", start=1):
        dialog, shown = _axis_hints_of(bed_view, key[tag], tomato["key"], f"TC-053-074: Beet {tag}")
        assert set(shown) == set(expected[tag]), (
            f"TC-053-074: Beet {tag} shows the axis hints {sorted(expected[tag])}, the dialog shows {shown}"
        )
        for axis, sentence in expected[tag].items():
            severity, text = shown[axis]
            assert severity == "warning" and sentence in text, (
                f"TC-053-074: Beet {tag}: the {axis} hint is a warning with {sentence!r}: {shown[axis]}"
            )
        screenshot(f"053_074_0{number}_beet_{tag.lower()}", f"Bepflanzen in Beet {tag}")
    dialog.choose_layout("rows")
    dialog.set_count(2)
    dialog.set_spacing(50)
    dialog.set_row_spacing(50)
    dialog.wait_for_server_preview(2, "TC-053-074: two tomatoes in Beet F")
    dialog.submit_and_wait_closed("TC-053-074: planting despite the frost hint")
    runs = runs_of_bed(base_url, e2e_seed_data, key["F"])
    assert len(runs) == 1, f"TC-053-074: the hint did not block - Beet F holds the new run: {runs}"


@pytest.mark.requires_desktop
def test_tc_053_074_waterlogging_hint_on_a_poorly_drained_bed(
    bed_view: BedViewPage,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-074 — "Beet N" (drainage "Schlecht") warns that the tomato does not tolerate waterlogging (GP-FR-161).

    Precondition (API): "Beet N" with ``soil_profile.drainage = poor`` (the TC's "Staunass"); the seed catalogue gives
    the tomato ``waterlogging_tolerance: sensitive`` (``species.yaml``). The dialog "Bepflanzen" with a tomato must
    show exactly ``waterlogging_risk`` as a warning: "… verträgt Staunässe schlecht, und dieses Beet ist schlecht
    drainiert." Breaks when the hint is missing - as it did until #2765 made ``GET /species`` serve the tolerance.
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc074n",
        beds=(BedSpec("Beet N", rect(1.0, 1.0, 1.5, 2.0)),),
    )
    bed = garden.bed_key("Beet N")
    patch_location(base_url, e2e_seed_data, bed, {"soil_profile": {"drainage": "poor"}})
    _dialog, shown = _axis_hints_of(bed_view, bed, tomato["key"], "TC-053-074: Beet N")
    screenshot("053_074_05_beet_n", "Beet N (Drainage schlecht): Staunässe-Hinweis erwartet")
    assert set(shown) == {"waterlogging_risk"}, (
        f"TC-053-074: Beet N shows exactly the waterlogging hint, the dialog shows {shown} "
        f"(the catalogue's tomato carries waterlogging_tolerance={tomato.get('waterlogging_tolerance')!r})"
    )
    severity, text = shown["waterlogging_risk"]
    assert (
        severity == "warning"
        and "verträgt Staunässe schlecht, und dieses Beet ist schlecht drainiert." in text
    ), f"TC-053-074: the waterlogging hint is a warning with the product's sentence: {shown}"


# ── TC-053-075 ──────────────────────────────────────────────────────────────


def test_tc_053_075_field_mode_moisture_and_wind_chips_store_with_one_tap(
    phone: tuple[int, int],
    browser: WebDriver,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-075 — field mode on a phone: "Feucht / Normal / Trocken" and "Windig" (GP-UX-057, GP-FR-162/163).

    Precondition (API): "Beet 1" without water regime and wind. In the bed sheet the section "Feuchte und Wind" holds
    three radios and one checkbox - no text field, no button; before a tap no water chip is checked. One tap on
    "Trocken" stores ``site_water_regime = dry`` (no save button), one on "Windig" stores ``wind_exposure = exposed``;
    the second tap on "Windig" switches it off (stored ``normal``), "Normal" replaces "Trocken" (``fresh``). A fresh
    field mode shows "Normal" checked and "Windig" off. Every chip measures >= 64 x 64 px and the page does not scroll
    sideways. Breaks if a tap stores nothing or something else, if a chip is smaller than the kiosk target, or if the
    reload shows another state.

    Device: 390 x 844 on desktop, 393 x 852 under the mobile profile (recorded as ``phone_viewport``).
    """
    field = FieldModePage(browser, base_url)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc075",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet 1")
    assert soil_profile_of(base_url, e2e_seed_data, bed).get("site_water_regime") in (
        None,
        "unknown",
    ), "TC-053-075 precondition: no water regime stored"

    def stored() -> tuple[str | None, str | None]:
        location = tenant_location(base_url, e2e_seed_data, bed)
        return (
            (location.get("soil_profile") or {}).get("site_water_regime"),
            (location.get("site_conditions") or {}).get("wind_exposure"),
        )

    field.open(garden.site_key)
    field.tap_bed(bed)
    controls = field.site_section_controls()
    assert controls == {"radio": 3, "checkbox": 1, "text": 0, "button": 0}, (
        f"TC-053-075: the section holds the four chips only, no form: {controls}"
    )
    assert field.checked_site_values(field.MOISTURE) == [], (
        "TC-053-075: no water chip is checked before a tap"
    )
    sizes = field.site_chip_sizes()
    small = {chip: size for chip, size in sizes.items() if min(size) < TOUCH_PX}
    assert len(sizes) == 4 and not small, (
        f"TC-053-075: every chip measures >= {TOUCH_PX} px; too small: {small}"
    )
    assert not field.page_scrolls_sideways(), "TC-053-075: the page does not scroll sideways"
    screenshot("053_075_01_sheet", f"Feldmodus {phone[0]} px: Feuchte und Wind")

    field.tap_site_chip(field.MOISTURE, "dry")
    _wait_stored(browser, lambda: stored()[0], "dry", "TC-053-075: one tap on 'Trocken'")
    field.tap_site_chip(field.WIND, "windy")
    _wait_stored(browser, stored, ("dry", "exposed"), "TC-053-075: one tap on 'Windig'")
    screenshot("053_075_02_dry_windy", "Trocken und Windig gespeichert")
    field.tap_site_chip(field.WIND, "windy")
    _wait_stored(browser, lambda: stored()[1], "normal", "TC-053-075: the second tap on 'Windig'")
    field.tap_site_chip(field.MOISTURE, "fresh")
    _wait_stored(browser, stored, ("fresh", "normal"), "TC-053-075: 'Normal' replaces 'Trocken'")

    field.open(garden.site_key)
    field.tap_bed(bed)
    after = (field.checked_site_values(field.MOISTURE), field.checked_site_values(field.WIND))
    assert after == (["fresh"], []), (
        f"TC-053-075: after a reload 'Normal' is checked and 'Windig' off: {after}"
    )
    screenshot("053_075_03_reloaded", "Nach dem Neuladen: Normal, nicht windig")


# ── TC-053-076 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_076_reach_hint_by_width_and_access_sides_is_never_an_error(
    plan: GardenPlanPage,
    bed_view: BedViewPage,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-076 — "Beet zu breit": a hint from width and access sides, never an error, never blocking (GP-FR-166).

    Precondition (API): four 3 m long beds - "Breit" 1,3 m (no access recorded), "Breit mit Weg" 1,3 m (access Ost +
    West), "Grenzwert" 1,2 m (Ost + West), "Schmal einseitig" 0,7 m (West); the site's default thresholds 1,2 / 0,6 m.
    The bed head shows "Beet zu breit" for "Breit" (detail: unknown access, threshold 0,6 m) and "Schmal einseitig"
    ("von einer Seite … bis 0,6 m"), "Breit mit Weg" with the two-side detail ("von zwei gegenüberliegenden Seiten … bis
    1,2 m" - 1,3 m is above 1,2 m), none for "Grenzwert" (1,2 m is not above 1,2 m). The editor's
    "Breite" field widens "Grenzwert" to 1,3 m and "Breit" to 2,0 m; the save goes through (stored widths) and the head
    of "Grenzwert" then shows the hint ("von zwei gegenüberliegenden Seiten … bis 1,2 m"). Every hint is an outlined
    warning chip, never an error colour, and the planting button of a hinted bed stays enabled. Breaks if the
    threshold is applied wrongly (equal counted as too wide, the access sides ignored), if the hint is red, or if it
    blocks saving or planting.

    Spec corrections: reach reads the access sides, not adjacent paths ("Breit mit Weg" and "Grenzwert" carry Ost +
    West); the hint is in the bed head, not a badge on the plan. The TC expects no hint for "Breit mit Weg" (1,3 m,
    both sides), which contradicts its own threshold (1,2 m for two sides, "genau 1,2 m gilt noch nicht als
    überschritten"): 1,3 m is above it, so the product - consistently with the spec - shows the hint with the
    two-side detail, and so does this test (first browser run, 2026-11-06).
    """
    beds = (
        BedSpec("Breit", rect(0.5, 1.0, 1.3, 3.0)),
        BedSpec("Breit mit Weg", rect(3.0, 1.0, 1.3, 3.0)),
        BedSpec("Grenzwert", rect(5.0, 1.0, 1.2, 3.0)),
        BedSpec("Schmal einseitig", rect(7.5, 1.0, 0.7, 3.0)),
    )
    garden = provision_garden(base_url, e2e_seed_data, purpose="tc076", beds=beds)
    key = {spec.name: garden.bed_key(spec.name) for spec in beds}
    for name, sides in (
        ("Breit mit Weg", ["E", "W"]),
        ("Grenzwert", ["E", "W"]),
        ("Schmal einseitig", ["W"]),
    ):
        patch_location(
            base_url, e2e_seed_data, key[name], {"site_conditions": {"access_sides": sides}}
        )

    def hint_of(name: str) -> dict[str, str] | None:
        bed_view.open(key[name], "planting")
        bed_view.wait_for_header_plants("0 Pflanzen", f"TC-053-076: the head of {name}")
        return bed_view.reach_hint()

    expected = {
        "Breit": "1,3 m breit – die Zugangsseiten sind nicht erfasst, deshalb gilt der Wert für einseitigen Zugang (0,6 m).",
        # 1,3 m with both opposite sides still exceeds the two-side value 1,2 m: the hint stays, now with the
        # two-side detail (the TC's "no hint" contradicts its own thresholds, see the docstring).
        "Breit mit Weg": "1,3 m breit – von zwei gegenüberliegenden Seiten erreichst du bis 1,2 m.",
        "Grenzwert": None,
        "Schmal einseitig": "0,7 m breit – von einer Seite erreichst du bis 0,6 m.",
    }
    for name, detail in expected.items():
        hint = hint_of(name)
        if detail is None:
            assert hint is None, f"TC-053-076: {name!r} shows no reach hint: {hint}"
            continue
        assert (
            hint is not None
            and hint["badge"] == "Beet zu breit"
            and hint["detail"].startswith(detail)
        ), f"TC-053-076: {name!r} shows 'Beet zu breit' with {detail!r}: {hint}"
        assert (hint["color"], hint["variant"]) == ("warning", "outlined"), (
            f"TC-053-076: the hint is an outlined warning, never an error: {hint}"
        )
        screenshot(
            f"053_076_0{list(expected).index(name) + 1}_{name.split()[0].lower()}",
            f"Beetkopf {name}",
        )
    assert bed_view.is_planting_enabled(), (
        "TC-053-076: a hinted bed can still be planted ('Bepflanzen' is enabled)"
    )

    plan.open(garden.site_key)
    plan.select_with_keyboard(key["Grenzwert"])
    plan.set_panel_field("width", 1.3)
    plan.select_with_keyboard(key["Breit"])
    plan.set_panel_field("width", 2.0)
    plan.save_with_button()
    stored = read_plan(base_url, e2e_seed_data, garden.site_key)
    widths = {
        name: stored_location(stored, name)["geometry"]["width_m"]
        for name in ("Grenzwert", "Breit")
    }
    assert widths == {"Grenzwert": 1.3, "Breit": 2.0}, (
        f"TC-053-076: the hint never blocks saving: {widths}"
    )
    screenshot("053_076_05_widened", "Editor: Grenzwert 1,3 m, Breit 2,0 m gespeichert")

    widened = hint_of("Grenzwert")
    assert widened is not None and widened["detail"].startswith(
        "1,3 m breit – von zwei gegenüberliegenden Seiten erreichst du bis 1,2 m."
    ), f"TC-053-076: 'Grenzwert' at 1,3 m shows the hint: {widened}"
    wider = hint_of("Breit")
    assert wider is not None and wider["detail"].startswith("2 m breit"), (
        f"TC-053-076: 'Breit' at 2,0 m keeps the hint: {wider}"
    )
    screenshot("053_076_06_grenzwert_after", "Grenzwert nach dem Verbreitern: Hinweis")


# ── TC-053-077 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_077_empty_photo_tab_offers_the_upload_and_refuses_a_text_file(
    bed_view: BedViewPage,
    browser: WebDriver,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
    tmp_path: Path,
) -> None:
    """TC-053-077 — the empty "Fotos" tab and a text file refused (GP-FR-051); steps 1 and 3.

    Precondition (API): "Beet 1" without photos. The tab reads "Noch keine Fotos vom Beet" with "Erstes Foto
    hinzufügen"; that action opens the upload dialog; "notiz.txt" is refused by the capture panel with "Nicht
    unterstütztes Bildformat. Erlaubt sind JPEG und PNG." and offers no upload; after cancelling the server still holds
    no photo. Runs in every profile (nothing is stored). Breaks if the empty tab offers no upload, if the text file is
    taken, or if anything reaches the gallery.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc077a",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet 1")
    note = tmp_path / "notiz.txt"
    note.write_text("Kein Bild, nur eine Notiz.\n", encoding="utf-8")
    photos = BedPhotosTab(browser, base_url)

    bed_view.open(bed, "photos")
    empty = photos.empty_state_text()
    assert (
        empty is not None
        and "Noch keine Fotos vom Beet" in empty
        and "Erstes Foto hinzufügen" in empty
    ), f"TC-053-077: the empty tab explains and offers the upload: {empty!r}"
    screenshot("053_077_01_empty", "Tab Fotos: noch keine Fotos, Hochladen angeboten")
    photos.open_upload()
    photos.choose_file(str(note))
    error = photos.wait_for_capture_error("TC-053-077: notiz.txt")
    assert error == "Nicht unterstütztes Bildformat. Erlaubt sind JPEG und PNG.", (
        f"TC-053-077: the text file is refused naming the allowed types: {error!r}"
    )
    # The dialog keeps its "Hochladen" button at all times (``PlantPhotoUploadDialog``: ``disabled={!file || uploading}``);
    # a refused file sets no file, so the button stays disabled and no preview is shown.
    assert photos.upload_state() == {"confirm_enabled": False, "preview": False}, (
        f"TC-053-077: a refused file offers no upload: {photos.upload_state()}"
    )
    screenshot("053_077_02_text_refused", "notiz.txt abgelehnt: erlaubte Dateitypen genannt")
    photos.cancel_upload()
    assert bed_photos(base_url, e2e_seed_data, bed)["photos"] == [], (
        "TC-053-077: nothing reached the gallery"
    )


@pytest.mark.requires_desktop
def test_tc_053_077_two_photos_a_chosen_cover_and_a_removal(
    bed_view: BedViewPage,
    browser: WebDriver,
    app_mode: str,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
    tmp_path: Path,
) -> None:
    """TC-053-077 — gallery, cover and remove on the desktop (GP-FR-051); steps 2 and 4-7. Full profile only.

    Precondition (API): "Beet 1" without photos; two generated PNGs (distinct bytes). Both are uploaded through the
    dialog: the gallery shows two cards, the first upload is the cover (the server's ``cover_photo_ref``). The star of
    the second card makes it the cover (chip, server, bed head picture, the summary's ``cover_photo_ref``). Removing it
    with the confirmation leaves the first photo; head and server agree on what the cover is then. The plan's JSON
    backup (the export dialog's request) names neither photo. Breaks if an upload is lost or doubled, if the cover
    does not follow the choice, if the removal takes the wrong photo, or if the backup carries a photo.
    """
    if app_mode != "full":
        pytest.skip(f"TC-053-077 (uploads) {PHOTOS_NEED_STORAGE}")
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc077b",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet 1")
    first_file, second_file = _png(tmp_path / "beet-1.png"), _png(tmp_path / "beet-2.png")
    photos = BedPhotosTab(browser, base_url)

    bed_view.open(bed, "photos")
    photos.upload(str(first_file), "TC-053-077: the first photo")
    (first,) = photos.wait_for_photo_count(1, "TC-053-077: after the first upload")
    photos.upload(str(second_file), "TC-053-077: the second photo")
    shown = photos.wait_for_photo_count(2, "TC-053-077: after the second upload")
    second = next(pid for pid in shown if pid != first)
    gallery = bed_photos(base_url, e2e_seed_data, bed)
    assert sorted(p["attachment_id"] for p in gallery["photos"]) == sorted([first, second]), (
        f"TC-053-077: the server holds exactly the two uploads: {gallery}"
    )
    assert gallery["cover_photo_ref"] == first, (
        f"TC-053-077: the first photo is the cover: {gallery}"
    )
    screenshot("053_077_03_two_photos", "Galerie: zwei Fotos, das erste ist Titelfoto")

    photos.toggle_cover(second)
    photos.wait_for_cover(second, "TC-053-077: the second photo as cover")
    _wait_stored(
        browser,
        lambda: bed_summary(base_url, e2e_seed_data, bed).get("cover_photo_ref"),
        second,
        "TC-053-077: the summary's cover after choosing the second photo",
    )
    bed_view.open(bed, "photos")
    cover_src = bed_view.wait_for_head_cover("TC-053-077: the bed head after choosing the cover")
    assert cover_src, "TC-053-077: the head draws the cover picture"
    screenshot("053_077_04_cover", "Beetkopf mit dem zweiten Foto als Titelfoto")

    photos.remove(second, "TC-053-077: removing the cover photo")
    left = bed_photos(base_url, e2e_seed_data, bed)
    assert [p["attachment_id"] for p in left["photos"]] == [first], (
        f"TC-053-077: the other photo stays: {left}"
    )
    assert left["cover_photo_ref"] in (None, first), (
        f"TC-053-077: no stale cover after the removal: {left}"
    )
    bed_view.open(bed, "photos")
    if left["cover_photo_ref"] is None:
        assert not bed_view.has_head_cover(), (
            "TC-053-077: the head shows no cover when the server has none"
        )
    else:
        bed_view.wait_for_head_cover("TC-053-077: the head shows the remaining photo as cover")
    screenshot("053_077_05_removed", "Nach dem Entfernen: ein Foto bleibt")

    backup = json.dumps(export_plan_json(base_url, e2e_seed_data, garden.site_key))
    assert first not in backup and second not in backup, (
        "TC-053-077: the JSON backup carries no photo"
    )


# ── TC-053-078 ──────────────────────────────────────────────────────────────


def test_tc_053_078_bed_photo_action_in_the_field_sheet_measures_64_px(
    phone: tuple[int, int],
    browser: WebDriver,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-078 — "Foto vom Beet" in the field-mode bed sheet is a >= 64 x 64 px target, on screen (GP-FR-051, GP-UX-023).

    Scope note of issue #2674: the field-mode "Foto vom Beet" action of ``FieldBedSheet`` renders at >= 64 px
    (``KIOSK_TOUCH_TARGET``). Precondition (API): "Beet 1" with one tomato. The sheet's action carries the
    accessible name "Foto vom Beet Beet 1 aufnehmen", measures at least 64 x 64 px and lies fully inside the viewport
    without scrolling; the plant offers its own photo action. Runs in every phone profile (nothing is uploaded).
    Breaks if the action is missing, smaller than the kiosk target, or below the fold.

    Device: 390 x 844 on desktop, 393 x 852 under the mobile profile (recorded as ``phone_viewport``).
    """
    field = FieldModePage(browser, base_url)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc078a",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet 1")
    planted = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=species(base_url, e2e_seed_data, TOMATO)["key"],
        id_prefix="TOM",
        points=((1.0, 0.5),),
    )
    plant = planted.plant_on(planted.point_slots[0])

    field.open(garden.site_key)
    field.tap_bed(bed)
    button = field.bed_photo_button()
    width, height = field.element_size(button)
    assert width >= TOUCH_PX and height >= TOUCH_PX, (
        f"TC-053-078: 'Foto vom Beet' measures {width:.0f} x {height:.0f} px, at least {TOUCH_PX} x {TOUCH_PX} expected"
    )
    assert field.is_in_viewport_unscrolled(button), (
        f"TC-053-078: 'Foto vom Beet' is on screen without scrolling ({phone[0]} x {phone[1]})"
    )
    assert button.get_attribute("aria-label") == "Foto vom Beet Beet 1 aufnehmen", (
        f"TC-053-078: the action names its bed: {button.get_attribute('aria-label')!r}"
    )
    screenshot("053_078_01_sheet", f"Feldmodus {phone[0]} px: Foto vom Beet, mindestens 64 px")
    field.open_plant_groups()
    assert field.plant_photo_button(plant).is_displayed(), (
        "TC-053-078: the plant keeps its own photo action"
    )


def test_tc_053_078_bed_photo_from_field_mode_lands_in_the_bed_gallery(
    phone: tuple[int, int],
    browser: WebDriver,
    app_mode: str,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
    tmp_path: Path,
) -> None:
    """TC-053-078 — a photo taken with "Foto vom Beet" goes to the bed, not the plant, and is its cover (GP-FR-051).

    Full profile only (attachment storage). Precondition (API): "Beet 1" with one tomato, no photo. Tapping the action
    opens the upload dialog; a generated PNG is chosen and "Hochladen" is pressed twice in one gesture; the dialog
    closes, the snackbar says "Foto bei Beet 1 gespeichert.", the server's bed gallery holds exactly one photo and it
    is the cover; the plant's gallery stays empty; a fresh field mode shows the cover beside the bed name and the
    bed's "Fotos" tab lists the photo. Breaks if the photo lands at the plant, if the double tap stores two photos, or
    if the cover does not follow.

    Not falsifiable here: "the action is locked until the confirmation" as a timing property - the double tap is
    asserted only through its outcome (one photo).
    """
    if app_mode != "full":
        pytest.skip(f"TC-053-078 (upload) {PHOTOS_NEED_STORAGE}")
    field = FieldModePage(browser, base_url)
    photos = BedPhotosTab(browser, base_url)
    bed_view = BedViewPage(browser, base_url)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc078b",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet 1")
    planted = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=species(base_url, e2e_seed_data, TOMATO)["key"],
        id_prefix="TOM",
        points=((1.0, 0.5),),
    )
    plant = planted.plant_on(planted.point_slots[0])
    picture = _png(tmp_path / "beet-feld.png")

    field.open(garden.site_key)
    field.tap_bed(bed)
    field.tap_bed_photo()
    photos.choose_file(str(picture))
    photos.wait_for_preview("TC-053-078: the chosen picture")
    screenshot("053_078_02_preview", "Foto vom Beet: Vorschau vor dem Hochladen")
    photos.double_tap_confirm("TC-053-078: 'Hochladen' tapped twice")
    message = field.wait_for_snackbar("gespeichert", "TC-053-078: after the upload")
    assert message == "Foto bei Beet 1 gespeichert.", (
        f"TC-053-078: the confirmation names the bed: {message!r}"
    )

    gallery = bed_photos(base_url, e2e_seed_data, bed)
    assert len(gallery["photos"]) == 1, f"TC-053-078: one photo at the bed, not two: {gallery}"
    (photo,) = gallery["photos"]
    assert gallery["cover_photo_ref"] == photo["attachment_id"], (
        f"TC-053-078: the photo is the cover: {gallery}"
    )
    assert plant_photos(base_url, e2e_seed_data, plant) == [], (
        "TC-053-078: the bed photo is not at the plant"
    )

    field.open(garden.site_key)
    field.tap_bed(bed)
    assert field.wait_for_sheet_cover("TC-053-078: the sheet after the upload"), (
        "TC-053-078: the cover is drawn beside the bed name"
    )
    screenshot("053_078_03_sheet_cover", "Beet-Sheet mit Titelfoto")
    bed_view.open(bed, "photos")
    assert photos.wait_for_photo_count(1, "TC-053-078: the bed's photo tab") == [
        photo["attachment_id"]
    ]


# ── TC-053-079 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_079_bed_list_csv_default_columns_site_columns_and_excel_variant(
    plan: GardenPlanPage,
    browser: WebDriver,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-079 — "Beetliste (CSV)": default columns, two site columns, Excel variant, formula name (GP-FR-145/175).

    Precondition (API): three beds - "Beet A" (2,5 m², loam, zone, one tomato, full sun, frost "Hoch"), "Kräuterbeet"
    (sand, half shade, frost "Gering") and "=SUMME(A1)". The dialog pre-ticks exactly the seven default columns
    ("Name … Aktive Pflanzen"), no site column, the assignment off. File 1: BOM, header ``name,type,area_m2,status,
    soil_texture,irrigation_zone,active_plants``, three rows with the server's values, the formula name as
    ``'=SUMME(A1)``. File 2 (+ "Sonneneinstrahlung", "Frostrisiko"): the two columns appended in file order with
    ``full_sun``/``high`` and ``partial_shade``/``low``. File 3 ("Excel-Variante"): BOM, semicolons, ``2,5`` with a
    decimal comma, "Kräuterbeet" intact. With every column unticked the dialog says "Wähle mindestens eine Spalte aus."
    and "Herunterladen" is disabled. Breaks if the defaults, the columns, the delimiter, the BOM, the decimal mark or
    the formula prefix are wrong, or if an empty selection downloads.

    Spec corrections: "Plan exportieren …" -> "Beetliste (CSV)"; machine column ids; "Sonne" = "Sonneneinstrahlung".
    """
    beds = (
        BedSpec("Beet A", rect(1.0, 1.0, 2.5, 1.0)),
        BedSpec("Kräuterbeet", rect(1.0, 3.0, 2.0, 1.0)),
        BedSpec("=SUMME(A1)", rect(1.0, 5.0, 1.5, 1.0)),
    )
    garden = provision_garden(base_url, e2e_seed_data, purpose="tc079", beds=beds)
    bed_a, herbs, formula = (garden.bed_key(spec.name) for spec in beds)
    patch_location(
        base_url,
        e2e_seed_data,
        bed_a,
        {
            "soil_profile": {"soil_texture": "loam"},
            "sun_exposure": "full_sun",
            "site_conditions": {"microclimate": {"frost_risk": "high"}},
        },
    )
    patch_location(
        base_url,
        e2e_seed_data,
        herbs,
        {
            "soil_profile": {"soil_texture": "sand"},
            "sun_exposure": "partial_shade",
            "site_conditions": {"microclimate": {"frost_risk": "low"}},
        },
    )
    zone_name = "Zone Nord"
    create_zone(
        base_url, e2e_seed_data, site_key=garden.site_key, name=zone_name, bed_keys=(bed_a,)
    )
    plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed_a,
        species_key=species(base_url, e2e_seed_data, TOMATO)["key"],
        id_prefix="TOM",
        points=((1.0, 0.5),),
    )
    status = {
        key: tenant_location(base_url, e2e_seed_data, key)["bed_status"]
        for key in (bed_a, herbs, formula)
    }

    plan.open(garden.site_key)
    dialog = BedListExportDialog(browser, base_url).open_from(plan)
    ticked = dialog.columns()
    assert sorted(column for column, on in ticked.items() if on) == sorted(DEFAULT_COLUMNS), (
        f"TC-053-079: exactly the seven default columns are pre-ticked: {ticked}"
    )
    assert [dialog.column_label(column) for column in DEFAULT_COLUMNS] == [
        "Name",
        "Typ",
        "Fläche (m²)",
        "Status",
        "Bodenart",
        "Bewässerungszone",
        "Aktive Pflanzen",
    ], "TC-053-079: the default columns carry the product's names"
    assert not dialog.is_assignment_on(), "TC-053-079: the assignment is not ticked (TC-053-080)"
    screenshot("053_079_01_defaults", "Beetliste (CSV): sieben Standardspalten vorausgewählt")
    saved = dialog.download("TC-053-079: file 1")
    assert saved["name"].endswith(".csv"), f"TC-053-079: a .csv file: {saved['name']!r}"
    header, rows = _csv_rows(saved, "TC-053-079: file 1")
    assert header == DEFAULT_COLUMNS, (
        f"TC-053-079: file 1 holds exactly the default columns: {header}"
    )
    assert sorted(rows) == sorted(["Beet A", "Kräuterbeet", "'=SUMME(A1)"]), (
        f"TC-053-079: three rows, the formula name prefixed with ': {sorted(rows)}"
    )
    row_a = rows["Beet A"]
    assert (
        row_a["type"],
        row_a["area_m2"],
        row_a["status"],
        row_a["soil_texture"],
        row_a["irrigation_zone"],
        row_a["active_plants"],
    ) == ("Hochbeet", "2.5", status[bed_a], "loam", zone_name, "1"), (
        f"TC-053-079: the row of Beet A: {row_a}"
    )
    assert (
        rows["Kräuterbeet"]["soil_texture"],
        rows["Kräuterbeet"]["active_plants"],
        rows["Kräuterbeet"]["status"],
    ) == (
        "sand",
        "0",
        status[herbs],
    ), f"TC-053-079: the row of Kräuterbeet: {rows['Kräuterbeet']}"

    dialog = BedListExportDialog(browser, base_url).open_from(plan)
    dialog.set_column("sun_exposure", True)
    dialog.set_column("frost_risk", True)
    summary = dialog.text_of(dialog.SUMMARY)
    assert "Sonneneinstrahlung" in summary and "Frostrisiko" in summary, (
        f"TC-053-079: the preview names the two added columns: {summary!r}"
    )
    header, rows = _csv_rows(dialog.download("TC-053-079: file 2"), "TC-053-079: file 2")
    assert header == [*DEFAULT_COLUMNS, "sun_exposure", "frost_risk"], (
        f"TC-053-079: file 2 columns: {header}"
    )
    assert (rows["Beet A"]["sun_exposure"], rows["Beet A"]["frost_risk"]) == ("full_sun", "high"), (
        rows["Beet A"]
    )
    assert (rows["Kräuterbeet"]["sun_exposure"], rows["Kräuterbeet"]["frost_risk"]) == (
        "partial_shade",
        "low",
    ), rows["Kräuterbeet"]

    dialog = BedListExportDialog(browser, base_url).open_from(plan)
    dialog.set_excel(True)
    screenshot("053_079_02_excel", "Beetliste (CSV): Excel-Variante gewählt")
    saved = dialog.download("TC-053-079: file 3 (Excel)")
    assert saved["text"].splitlines()[0].count(";") == len(DEFAULT_COLUMNS) - 1, (
        f"TC-053-079: the Excel variant separates with semicolons: {saved['text'].splitlines()[0]!r}"
    )
    header, rows = _csv_rows(saved, "TC-053-079: file 3", delimiter=";")
    assert header == DEFAULT_COLUMNS and rows["Beet A"]["area_m2"] == "2,5", (
        f"TC-053-079: semicolon file with a decimal comma: {header}, {rows.get('Beet A')}"
    )
    assert "Kräuterbeet" in rows, f"TC-053-079: the umlaut survives the encoding: {sorted(rows)}"

    dialog = BedListExportDialog(browser, base_url).open_from(plan)
    for column in DEFAULT_COLUMNS:
        dialog.set_column(column, False)
    assert dialog.text_of(dialog.NO_COLUMNS) == "Wähle mindestens eine Spalte aus.", (
        "TC-053-079: the dialog asks for at least one column"
    )
    assert not dialog.is_download_enabled(), "TC-053-079: no download without a column"
    screenshot("053_079_03_no_columns", "Keine Spalte gewählt: Herunterladen gesperrt")
    dialog.close()


# ── TC-053-080 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_080_bed_list_csv_names_people_only_with_the_opt_in(
    plan: GardenPlanPage,
    browser: WebDriver,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-080 — the assignment enters the bed list only with "Zuweisungen einschließen" (GP-FR-175, SR-024).

    Precondition (API): "Beet 1" assigned to the acting member (``POST /tenants/{slug}/assignments``), "Beet 2" not.
    The switch is off by default, labelled "Zuweisungen einschließen", with its privacy note ("personenbezogene
    Daten", "Standardmäßig aus") and the dialog's note that the export names no members. The file without the opt-in
    has no ``assigned_to`` column and nowhere the member's name. Switched on, the dialog's note says the file names the
    members; the file ends in ``assigned_to`` with the name at "Beet 1" and an empty cell at "Beet 2". Reopened, the
    switch is off again. Breaks if a name leaks without the opt-in, if the opt-in misses the name or puts it at the
    wrong bed, or if the opt-in is remembered.

    Spec corrections: "Zuweisungen einschließen" / ``assigned_to``; the member is the acting account (its display
    name), the stack seeds no "Anna Beispiel".
    """
    beds = (
        BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),
        BedSpec("Beet 2", rect(1.0, 3.0, 2.0, 1.0)),
    )
    garden = provision_garden(base_url, e2e_seed_data, purpose="tc080", beds=beds)
    member = acting_member(base_url, e2e_seed_data)
    assign_bed(
        base_url, e2e_seed_data, membership_key=member["key"], bed_key=garden.bed_key("Beet 1")
    )
    person = member["display_name"]

    plan.open(garden.site_key)
    dialog = BedListExportDialog(browser, base_url).open_from(plan)
    assert not dialog.is_assignment_on(), "TC-053-080: the assignment is off by default"
    assert dialog.assignment_label() == "Zuweisungen einschließen", dialog.assignment_label()
    hint = dialog.text_of(dialog.ASSIGNMENT_HINT)
    assert "personenbezogene Daten" in hint and "Standardmäßig aus" in hint, (
        f"TC-053-080: the option carries its privacy note: {hint!r}"
    )
    assert dialog.text_of(dialog.PRIVACY) == (
        "Der Export enthält keine Namen von Mitgliedern, keine Zuweisungen und keine Notizen anderer Personen."
    ), (
        f"TC-053-080: without the opt-in the dialog promises no names: {dialog.text_of(dialog.PRIVACY)!r}"
    )
    saved = dialog.download("TC-053-080: without the opt-in")
    header, _rows = _csv_rows(saved, "TC-053-080: without the opt-in")
    assert "assigned_to" not in header, (
        f"TC-053-080: no assignment column without the opt-in: {header}"
    )
    assert person not in saved["text"], f"TC-053-080: the file names {person!r} without the opt-in"

    dialog = BedListExportDialog(browser, base_url).open_from(plan)
    dialog.set_assignment(True)
    assert dialog.text_of(dialog.PRIVACY) == (
        "Die Datei enthält die Namen der Mitglieder, denen Beete zugewiesen sind. Notizen und Kontodaten sind nie enthalten."
    ), (
        f"TC-053-080: the switched-on note names the people in the file: {dialog.text_of(dialog.PRIVACY)!r}"
    )
    assert "Zugewiesen an" in dialog.text_of(dialog.SUMMARY), (
        "TC-053-080: the preview lists 'Zugewiesen an'"
    )
    screenshot("053_080_01_opt_in", "Zuweisungen einschließen: Datenschutz-Hinweis")
    header, rows = _csv_rows(
        dialog.download("TC-053-080: with the opt-in"), "TC-053-080: with the opt-in"
    )
    assert header[-1] == "assigned_to", f"TC-053-080: the assignment is the last column: {header}"
    assert (rows["Beet 1"]["assigned_to"], rows["Beet 2"]["assigned_to"]) == (person, ""), (
        f"TC-053-080: the name at Beet 1, an empty cell at Beet 2: {rows}"
    )

    dialog = BedListExportDialog(browser, base_url).open_from(plan)
    assert not dialog.is_assignment_on(), "TC-053-080: the opt-in is not remembered"
    screenshot("053_080_02_reopened", "Dialog erneut geöffnet: Zuweisung wieder aus")
    dialog.close()


# ── TC-053-081 ──────────────────────────────────────────────────────────────

#: GP-FR-174's file: four valid lines (one with a formula name), a width "abc" and a line without a name.
BED_CSV = (
    "Name;Typ;Breite_m;Länge_m;Sonne\r\n"
    "Hochbeet A;Hochbeet;1,2;2,0;Volle Sonne\r\n"
    "Hochbeet B;Hochbeet;1,0;2,0;Halbschatten\r\n"
    "Kräuterbeet;Hochbeet;0,8;1,5;\r\n"
    "=Beet4;Hochbeet;1,0;1,0;\r\n"
    "Beet abc;Hochbeet;abc;2,0;\r\n"
    ";Hochbeet;1,0;1,0;\r\n"
)
#: name -> (width, length) of the lines the import writes.
BED_CSV_VALID = {
    "Hochbeet A": (1.2, 2.0),
    "Hochbeet B": (1.0, 2.0),
    "Kräuterbeet": (0.8, 1.5),
    "Beet4": (1.0, 1.0),
}


@pytest.mark.requires_desktop
def test_tc_053_081_csv_bed_import_reports_line_errors_and_writes_only_after_the_confirmation(
    plan: GardenPlanPage,
    browser: WebDriver,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
    tmp_path: Path,
) -> None:
    """TC-053-081 — "Beetliste importieren (CSV)": report, cancel, confirm, the beds selected in the editor (GP-FR-174).

    Precondition (API): a site with a 10 x 10 m boundary and no bed; a UTF-8 file ``Name;Typ;Breite_m;Länge_m;Sonne``
    with four valid lines, a width "abc" (line 6) and a line without a name (line 7). The report reads "4 von 6
    Zeilen sind gültig, 2 werden übersprungen.", lists "Zeile 6" (no valid number) and "Zeile 7" (value missing) as
    errors, "Zeile 5" (formula character removed) as a warning, "4 Beete werden angelegt" and offers "4 Beete
    anlegen". Cancelled, the server's plan holds no bed. Repeated and confirmed: "4 Beete wurden angelegt …" and "2
    fehlerhafte Zeilen wurden übersprungen."; "Zum Plan" closes the wizard and the editor selects the four new beds.
    The server holds exactly them - "Beet4" without "=" - with the file's sizes, inside the boundary and without an
    overlap. Breaks if the dry run writes, if a line error is lost or the bad lines are written, if a formula survives,
    or if the beds overlap.

    Spec corrections: own menu entry; "=Beet4" -> "Beet4" with the warning. Not automated: the "Gärtner" half.
    """
    garden = provision_garden(base_url, e2e_seed_data, purpose="tc081")
    upload = tmp_path / "beetliste.csv"
    upload.write_text(BED_CSV, encoding="utf-8", newline="")

    plan.open(garden.site_key)
    panel = BedCsvImportPanel(browser, base_url).open_from(plan)
    panel.choose_file(str(upload))
    assert panel.summary() == "4 von 6 Zeilen sind gültig, 2 werden übersprungen.", panel.summary()
    errors = panel.error_lines()
    assert (
        len(errors) == 2
        and any(e.startswith("Zeile 6") and "Das ist keine gültige Zahl" in e for e in errors)
        and any(e.startswith("Zeile 7") and "Hier fehlt ein Pflichtwert." in e for e in errors)
    ), f"TC-053-081: the two error lines with line number and reason: {errors}"
    warnings = panel.warning_lines()
    assert any(w.startswith("Zeile 5") and "Formelzeichen" in w for w in warnings), (
        f"TC-053-081: the formula name is reported as a warning: {warnings}"
    )
    beds_listed = panel.bed_lines()
    assert [line.split("Zeile")[0].strip() for line in beds_listed] == list(BED_CSV_VALID), (
        f"TC-053-081: the report lists the four beds it would create: {beds_listed}"
    )
    assert panel.apply_label() == "4 Beete anlegen", panel.apply_label()
    screenshot("053_081_01_report", "Prüfbericht: 4 von 6 gültig, Zeilen 6 und 7 fehlerhaft")
    panel.cancel()
    assert read_plan(base_url, e2e_seed_data, garden.site_key).get("locations") in ([], None), (
        "TC-053-081: the dry run and the cancel wrote nothing"
    )

    panel = BedCsvImportPanel(browser, base_url).open_from(plan)
    panel.choose_file(str(upload))
    done = panel.apply("TC-053-081: confirming the report")
    assert done == (
        "4 Beete wurden angelegt und im Plan markiert – du kannst sie jetzt anordnen. "
        "2 fehlerhafte Zeilen wurden übersprungen."
    ), f"TC-053-081: the confirmation counts the beds and the skipped lines: {done!r}"
    screenshot("053_081_02_done", "4 Beete angelegt, 2 Zeilen übersprungen")
    panel.to_editor()

    stored = read_plan(base_url, e2e_seed_data, garden.site_key)
    created = {loc["name"]: loc for loc in stored.get("locations") or []}
    assert set(created) == set(BED_CSV_VALID), (
        f"TC-053-081: exactly the four valid beds: {sorted(created)}"
    )
    for name, (width, length) in BED_CSV_VALID.items():
        geometry = created[name]["geometry"]
        assert (geometry["width_m"], geometry["length_m"]) == (width, length), (
            f"TC-053-081: {name!r} carries the file's size: {geometry}"
        )
        x, y = geometry["origin"]
        assert 0.0 <= x and 0.0 <= y and x + width <= 10.0 and y + length <= 10.0, (
            f"TC-053-081: {name!r} lies inside the boundary: {geometry}"
        )
    names = list(created)
    clashes = [
        (a, b)
        for i, a in enumerate(names)
        for b in names[i + 1 :]
        if _overlap(created[a]["geometry"], created[b]["geometry"])
    ]
    assert not clashes, f"TC-053-081: the beds stand side by side without overlap: {clashes}"
    for name in names:
        plan.wait_for_selected(
            created[name]["key"], True, f"TC-053-081: {name!r} selected for arranging"
        )
    screenshot("053_081_03_editor", "Editor: die vier neuen Beete markiert")


# ── TC-053-082 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_082_frost_reason_only_on_a_high_bed_with_a_predicted_frost(
    bed_view: BedViewPage,
    app_mode: str,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
    screenshot_dir,
) -> None:
    """TC-053-082 — the frost reason of a plant: "Hoch" bed AND predicted frost; frost before overdue (§11.4, GP-UX-060).

    Precondition: site 1 with four beds, one tomato each - "Beet A" frost "Hoch", "Beet B" "Normal", "Beet C"
    "Gering", "Beet D" "Hoch" plus an overdue task on its tomato; a stored forecast for site 1 with -3 °C tonight (the
    named ArangoDB write, ``store_frost_forecast``). Site 2 without a forecast with "Beet E" "Hoch". The server's plant
    states are the precondition: A ``[frost]``, B and C none, D ``[frost, overdue]``, E none. In the bed plan: A's marker
    carries exactly the frost badge, its name says "Frostgefahr", and the hover bubble's attention part holds exactly one
    line, "Frostgefahr";
    B, C and E carry no badge and no frost; D carries one badge - the frost - and names both reasons. Breaks if a
    bed without "Hoch" or without a forecast shows the frost, or if the badge priority is wrong.

    Spec corrections: the frost badge is the hexagon with a star; "Beet D" carries an overdue task instead of an open
    finding (no route writes a finding). The bubble has no visible heading "Handlungsbedarf": in REQ-053 §11.4 (the
    plant-info table, ``spec/req/REQ-053_Grafische-Garten-Beetplanung.md:725``) "Handlungsbedarf" names the ROW, whose
    content is "die Gründe des Aufmerksamkeits-Badges im Klartext, z. B. „2 Aufgaben überfällig“" - the product renders
    exactly that as ``attention-*`` lines (``PlantInfoPopover.tsx:48-60``); the i18n key ``info.needsAttention`` is
    unused. The TC's "im Bereich „Handlungsbedarf“" is a placeholder, not a heading the spec demands. Not automated:
    the early-warning notification.
    """
    beds = tuple(
        BedSpec(f"Beet {tag}", rect(0.5 + 2.4 * i, 1.0, 2.0, 1.0)) for i, tag in enumerate("ABCD")
    )
    site_1 = provision_garden(base_url, e2e_seed_data, purpose="tc082a", beds=beds)
    site_2 = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc082b",
        beds=(BedSpec("Beet E", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    key = {tag: site_1.bed_key(f"Beet {tag}") for tag in "ABCD"}
    key["E"] = site_2.bed_key("Beet E")
    for tag, risk in (("A", "high"), ("B", "normal"), ("C", "low"), ("D", "high"), ("E", "high")):
        patch_location(
            base_url,
            e2e_seed_data,
            key[tag],
            {"site_conditions": {"microclimate": {"frost_risk": risk}}},
        )
    tomato = species(base_url, e2e_seed_data, TOMATO)["key"]
    plant: dict[str, str] = {}
    for tag in "ABCDE":
        planted = plant_on_positions(
            base_url,
            e2e_seed_data,
            bed_key=key[tag],
            species_key=tomato,
            id_prefix=f"TO{tag}",
            points=((1.0, 0.5),),
        )
        plant[tag] = planted.plant_on(planted.point_slots[0])
    overdue_task(base_url, e2e_seed_data, plant["D"], "E2E-GP Ausgeizen", days_ago=2)
    store_frost_forecast(
        app_mode, tenant_key=tenant_key_of(base_url, e2e_seed_data), site_key=site_1.site_key
    )

    reasons = {
        tag: plant_states(base_url, e2e_seed_data, key[tag]).get(plant[tag]) for tag in "ABCDE"
    }
    assert reasons == {"A": ["frost"], "B": [], "C": [], "D": ["frost", "overdue"], "E": []}, (
        f"TC-053-082 precondition: the server's attention reasons per bed: {reasons}"
    )

    bed_view.open(key["A"], "plan")
    bed_view.wait_for_plant_states(plant["A"], "TC-053-082: Beet A")
    assert bed_view.marker_badges(plant["A"]) == ["frost"], (
        f"TC-053-082: the tomato in Beet A carries the frost badge: {bed_view.marker_badges(plant['A'])}"
    )
    assert "Frostgefahr" in bed_view.marker_aria_label(plant["A"]), bed_view.marker_aria_label(
        plant["A"]
    )
    bed_view.hover_plant(plant["A"])
    bed_view.wait_for_bubble(plant["A"], "TC-053-082: hovering the tomato in Beet A")
    lines = bed_view.bubble_lines()
    attention = {key: value for key, value in lines.items() if key.startswith("attention-")}
    assert attention == {"attention-frost": "Frostgefahr"}, (
        f"TC-053-082: the bubble's attention part names the frost - and only the frost - in plain text: {lines}"
    )
    # Viewport-only: a full-page capture would move the viewport under the resting pointer and close the bubble.
    bed_view.take_screenshot("053_082_01_beet_a_bubble", screenshot_dir)

    for tag in "BCE":
        bed_view.open(key[tag], "plan")
        bed_view.wait_for_plant_states(plant[tag], f"TC-053-082: Beet {tag}")
        label = bed_view.marker_aria_label(plant[tag])
        assert bed_view.marker_badges(plant[tag]) == [] and "Frostgefahr" not in label, (
            f"TC-053-082: Beet {tag} shows no frost: badges {bed_view.marker_badges(plant[tag])}, name {label!r}"
        )
    screenshot("053_082_02_beet_e", "Beet E (Frostrisiko Hoch, keine Vorhersage): kein Frost-Grund")

    bed_view.open(key["D"], "plan")
    bed_view.wait_for_plant_states(plant["D"], "TC-053-082: Beet D")
    label = bed_view.marker_aria_label(plant["D"])
    assert bed_view.marker_badges(plant["D"]) == ["frost"], (
        f"TC-053-082: Beet D carries ONE badge, the frost (frost before overdue): {bed_view.marker_badges(plant['D'])}"
    )
    assert "Frostgefahr" in label and "1 Aufgabe überfällig" in label, (
        f"TC-053-082: Beet D names both reasons: {label!r}"
    )
    screenshot("053_082_03_beet_d", "Beet D: ein Badge (Frost), überfällige Aufgabe im Text")
