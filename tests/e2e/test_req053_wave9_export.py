"""E2E of REQ-053 wave 9 part B - PNG, template exchange, parcel page, site flags, water distance, rain, Ctrl+D, Konva (WP 9.16, #2756).

Spec pin REQ-053 v1.13 §34 wave 9. Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md, section 13 and
TC-053-047 in section 7, TC file v1.12); each docstring names the requirement it is derived from:
  TC-053-091  ->  PNG drawn in the browser: 2x by default, 1x half as wide; file name, PNG signature, the size     (GP-FR-144,
                  line and the IHDR equal factor x the fitted view box; no watermark by default                   WP 9.8)
  TC-053-092  ->  bed template: export a tenant template as JSON without keys, import the same file back: the    (GP-FR-173,
                  taken name is refused with a proposal, the re-check and the import write a copy, selected       GP-API-070/071,
                                                                                                                  WP 9.9)
  TC-053-093  ->  PDF: no parcel page without the opt-in, "Parzellenliste: <Standort>" with it; the assignment    (GP-FR-176,
                  opt-in only under the parcel list, its privacy note, and only it asks for the names            SR-024, WP 9.10)
  TC-053-094  ->  site flags "Wurzelkonkurrenz" / "Allelopathie-Risiko" in the site-conditions panel and as the   (GP-FR-165,
                  neutral chip in the bed head; switched off, the chip goes                                       WP 9.11)
  TC-053-095  ->  nearest water source: bed list column, bed head, CSV column ``nearest_water_source_m``; a bed   (GP-FR-167,
                  without geometry has none (never "0 m")                                                         WP 9.12)
  TC-053-047  ->  watering round "Regen — übersprungen": one rainfall line without an amount per bed, no         (GP-FR-117,
                  watering, the open watering task stays open                                                      WP 9.13)
  TC-053-096  ->  Ctrl+D duplicates the selected bed one grid step down-right as "<Name> (Kopie)", one unsaved    (GP-FR-025/026,
                  change, the copy selected; moved clear (V-05) it is saved as a copy of the bed                  V-05, WP 9.14)
  TC-053-097  ->  renderer switch: a plan of 3 000 objects is drawn by Konva (canvas), one of 2 970 by SVG         (GP-NFR-033,
                                                                                                                  D-01, WP 9.7)

NOT covered, on purpose (no skip, no xfail - there is nothing to run):
  * GP-FR-025 slot copy on duplicate: Ctrl+D copies a bed WITHOUT its planting positions. Copying slots was
    deliberately not built - it contradicts the decided §32.4 item 8, and the operator decision is pending
    (``editor/tools/duplicate.ts``: "the closed plan operation list has no ``create_slot``"). TC-053-096 arranges a
    bed without slots and asserts nothing about slots, so it neither certifies nor freezes either answer.
  * The member names in the PDF's parcel table (the assignment column's cells): the E2E image has no PDF text
    extraction - the page content is glyph ids of a subset font. TC-053-093 reads the PDF's bookmarks (headings) and
    the request the dialog sent; the column itself is pinned server-side (the print engine's tests).
  * The site-flags note in the planting dialog (``planting-site-flags``): it is shown only with a species chosen;
    TC-053-094 covers the panel and the chip the issue names.

Corrections against the issue text: "Flags im Panel" is the site-conditions dialog of the bed view ("Merkmale
ändern"), where WP 9.11 put the two flags; "Ctrl+D Slot-Kopie" is tested as Ctrl+D without slots (above).

Device: every case is a desktop case (``requires_desktop``; the export dialog offers PNG and CSV only off the phone,
GP-UX-050). Preconditions are self-provisioned through the application's own API, one fresh site per test with a
UUID-derived name (`_garden_plan_helpers.py`, `_export_helpers.py`); the Konva case imports its plan through the
plan import like the renderer measurement (``_renderer_plans.py``). Waits are anchored on state - a pressed toggle, a
closed dialog, a saved download, a notice, the pending-change count, the ``data-renderer`` attribute - never on
time; every written outcome is read back from the server.
"""

from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

import pytest
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from ._export_helpers import (
    add_water_source,
    bed_list_rows,
    bed_templates,
    create_bed_template,
    expected_png_size,
    pdf_outline_titles,
    png_size,
)
from ._garden_plan_helpers import (
    BedSpec,
    care_events,
    create_bed_task,
    create_bed_without_area,
    create_zone,
    provision_garden,
    read_plan,
    rect,
    site_conditions,
    task_state,
    tenant_key_of,
    unique_tag,
)
from ._renderer_plans import GridPlan, provision_grid_plan
from .pages.bed_site_page import SiteConditionsDialog
from .pages.plan_export_page import BedHeadWave9, PlanExportDialog, Wave9PlanPage

#: ``pages.gardenPlan.io.export.png.summary``.
PNG_SUMMARY = "Das Bild wird {w} × {h} Pixel groß und zeigt den ganzen Plan."
TEMPLATE_EXPORTED = (
    "Die Vorlage ist als JSON-Datei heruntergeladen – ohne Mandanten-Kennung, Autor und Notizen."
)
TEMPLATE_IMPORTED = "Die Vorlage ist importiert und ausgewählt."
TEMPLATE_NAME_TAKEN = (
    "Eine Vorlage mit diesem Namen gibt es schon. Übernimm den vorgeschlagenen Namen oder gib einen anderen ein und "
    "prüfe erneut."
)
#: What a template file may carry (``BedTemplateExchange``) - and what it must never carry (GP-API-070).
TEMPLATE_FILE_FIELDS = {
    "format",
    "schema_version",
    "name",
    "location_type_key",
    "default_geometry",
    "height_m",
    "default_layout",
    "soil_profile_defaults",
}
PRIVACY_DEFAULT = "Der Export enthält keine Namen von Mitgliedern, keine Zuweisungen und keine Notizen anderer Personen."
PRIVACY_PARCEL_ASSIGNMENT = (
    "Das PDF enthält in der Parzellenliste die Namen der Mitglieder, denen Beete zugewiesen sind. Notizen und "
    "Kontodaten sind nie enthalten."
)
RAIN_RESULT_MARKER = "Regen-Einträge ohne Menge. Offene Gieß-Aufgaben bleiben offen."
NO_WATERING_YET = "Noch kein Gießen erfasst."
#: ``renderer/createRenderer.ts`` ``KONVA_MIN_PLAN_OBJECTS``: beds + garden objects + slots.
KONVA_MIN_PLAN_OBJECTS = 3000


@pytest.fixture
def plan(browser: WebDriver, base_url: str) -> Wave9PlanPage:
    return Wave9PlanPage(browser, base_url)


@pytest.fixture
def export(browser: WebDriver, base_url: str) -> PlanExportDialog:
    return PlanExportDialog(browser, base_url)


def _csv_by_name(text: str) -> tuple[list[str], dict[str, dict[str, str]]]:
    """Header and rows (by the ``name`` cell) of a bed-list CSV (UTF-8 BOM kept as U+FEFF by the probe)."""
    lines = list(csv.reader(io.StringIO(text.lstrip("\ufeff"), newline="")))
    if not lines or "name" not in lines[0]:
        raise AssertionError(f"the bed list CSV has no header with 'name': {lines[:1]!r}")
    header = lines[0]
    return header, {
        row["name"]: row
        for row in (dict(zip(header, line, strict=True)) for line in lines[1:] if line)
    }


# ── TC-053-091 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_091_png_is_factor_times_the_fitted_view_box(
    plan: Wave9PlanPage, export: PlanExportDialog, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-091 — the PNG is drawn in the browser at factor x the fitted view box, 2x by default (GP-FR-144).

    Source: REQ-053 GP-FR-144, wave 9 placeholder 9 (no watermark by default); WP 9.8. Precondition (API): a 20 x 10 m
    garden with two beds inside it (the content box is the boundary). Expected size from the Python reference of
    ``fitViewport`` / ``resolvePngSize`` (``_export_helpers.expected_png_size``): 1x = 1200 x 655, 2x = 2400 x 1310.
    The dialog opens on 2x, says "Das Bild wird 2400 × 1310 Pixel groß …", the watermark is off, the download is a
    PNG named ``garden-plan-<site>-<yyyymmdd>.png`` whose IHDR is 2400 x 1310; at 1x the line and the file say
    1200 x 655 - exactly half. Breaks if the factor is not applied, the size line and the file disagree, the PNG is
    no PNG, or the watermark is on by default.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc091",
        boundary=rect(0.0, 0.0, 20.0, 10.0),
        beds=(
            BedSpec("Beet A", rect(2.0, 2.0, 3.0, 1.5)),
            BedSpec("Beet B", rect(12.0, 6.0, 4.0, 1.0)),
        ),
    )
    bounds = (0.0, 0.0, 20.0, 10.0)
    two = expected_png_size(bounds, 2)
    one = expected_png_size(bounds, 1)
    assert (one, two) == ((1200, 655), (2400, 1310)), (
        f"TC-053-091: the reference itself drifted: {one}, {two}"
    )

    plan.open(garden.site_key)
    export.open_with_format(plan, "png")
    assert export.png_factor_chosen() == 2, "TC-053-091: the dialog opens on 2x"
    assert not export.is_png_watermark_on(), (
        "TC-053-091: the watermark is off by default (placeholder 9)"
    )
    export.wait_for_png_summary(PNG_SUMMARY.format(w=two[0], h=two[1]), "TC-053-091: 2x")
    assert not export.is_png_capped(), "TC-053-091: 2400 x 1310 is far below the canvas limits"
    screenshot("053_091_01_png_dialog", "Export als PNG, 2×: 2400 × 1310 Pixel")
    saved = export.download_file("TC-053-091: the 2x PNG")
    assert re.fullmatch(rf"garden-plan-{re.escape(garden.site_key)}-\d{{8}}\.png", saved["name"]), (
        f"TC-053-091: the file name: {saved['name']!r}"
    )
    assert png_size(saved["data"]) == two, (
        f"TC-053-091: the 2x PNG is {png_size(saved['data'])}, expected {two}"
    )

    export.open_with_format(plan, "png")
    export.choose_png_factor(1)
    export.wait_for_png_summary(PNG_SUMMARY.format(w=one[0], h=one[1]), "TC-053-091: 1x")
    screenshot("053_091_02_png_dialog_1x", "Export als PNG, 1×: 1200 × 655 Pixel")
    single = export.download_file("TC-053-091: the 1x PNG")
    assert png_size(single["data"]) == one, (
        f"TC-053-091: the 1x PNG is {png_size(single['data'])}, expected {one}"
    )
    assert png_size(saved["data"])[0] == 2 * png_size(single["data"])[0], (
        "TC-053-091: the width scales with the factor"
    )
    screenshot("053_091_03_after_downloads", "Nach zwei PNG-Downloads (2× und 1×)")


# ── TC-053-092 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_092_template_exported_without_keys_and_imported_back(
    plan: Wave9PlanPage, base_url: str, e2e_seed_data: dict, screenshot, tmp_path: Path
) -> None:
    """TC-053-092 — a template file carries no keys; importing it back proposes a free name and writes a copy (GP-FR-173).

    Source: REQ-053 GP-FR-173, GP-API-070/071; WP 9.9. Precondition (API): a tenant template "Kräuterbeet <tag>"
    (raised bed 1.6 x 0.8 m, 0.4 m, rows 25 cm / spacing 20 cm) and a garden. In the template tool the template is
    picked and exported: the notice confirms it, the file holds only the exchange fields (no ``_key``,
    ``tenant_key``, ``created_by`` …, and the tenant key nowhere in the text) with the template's values. The same
    file is imported: the check refuses the taken name, the name field proposes another; "Erneut prüfen" brings the
    report with that name; "Importieren" writes it, the notice confirms it and the picker selects the new template.
    The server holds the new template beside the original - same shape, height and grid, another key. Breaks if a
    key leaks into the file, the round trip changes the template, or a taken name is overwritten.
    """
    tag = unique_tag()
    original = create_bed_template(base_url, e2e_seed_data, name=f"Kräuterbeet {tag}")
    garden = provision_garden(base_url, e2e_seed_data, purpose="tc092")
    tenant_key = tenant_key_of(base_url, e2e_seed_data)

    plan.open(garden.site_key)
    plan.pick_template(original["key"])
    exported = plan.export_picked_template("TC-053-092: export")
    plan.wait_for_template_notice(TEMPLATE_EXPORTED, "TC-053-092: after the export")
    document = exported["document"]
    assert set(document) <= TEMPLATE_FILE_FIELDS and {"format", "name", "default_geometry"} <= set(
        document
    ), f"TC-053-092: the file holds only the exchange fields: {sorted(document)}"
    assert tenant_key not in json.dumps(document), (
        "TC-053-092: the tenant key appears nowhere in the file"
    )
    assert (
        document["format"] == "kamerplanter.bed_template" and document["name"] == original["name"]
    ), document
    assert (
        document["default_geometry"]["width_m"] == 1.6
        and document["default_geometry"]["length_m"] == 0.8
    ), f"TC-053-092: the geometry travels: {document['default_geometry']}"
    screenshot("053_092_01_exported", "Vorlage exportiert")

    path = tmp_path / exported["name"]
    path.write_text(json.dumps(document), encoding="utf-8")
    plan.open_template_import()
    branch = plan.choose_template_file(path, "TC-053-092: importing the same file")
    assert branch == "error", (
        f"TC-053-092: the taken name is refused first, the check showed {branch!r}"
    )
    assert plan.import_error_text() == TEMPLATE_NAME_TAKEN, (
        f"TC-053-092: {plan.import_error_text()!r}"
    )
    proposed = plan.import_name()
    assert proposed and proposed != original["name"], (
        f"TC-053-092: a free name is proposed: {proposed!r}"
    )
    screenshot("053_092_02_name_taken", "Name vergeben: Vorschlag im Namensfeld")

    plan.recheck_import("TC-053-092: with the proposed name")
    assert f"Name: {proposed}" in plan.import_report_text(), (
        f"TC-053-092: {plan.import_report_text()!r}"
    )
    screenshot("053_092_03_report", "Erneut geprüft: Prüfbericht mit dem vorgeschlagenen Namen")
    plan.confirm_import("TC-053-092: 'Importieren'")
    plan.wait_for_template_notice(TEMPLATE_IMPORTED, "TC-053-092: after the import")

    copies = [t for t in bed_templates(base_url, e2e_seed_data) if t.get("name") == proposed]
    assert len(copies) == 1, f"TC-053-092: exactly one template named {proposed!r}: {copies}"
    (copy,) = copies
    assert copy["key"] != original["key"], "TC-053-092: the import writes a new template"
    plan.wait_for_picked_template(copy["key"], "TC-053-092: the picker after the import")
    for field in ("location_type_key", "default_geometry", "height_m", "default_layout"):
        assert copy[field] == original[field], (
            f"TC-053-092: {field} survives the round trip: {copy[field]!r} != {original[field]!r}"
        )
    screenshot("053_092_04_imported", "Vorlage importiert und ausgewählt")
    labels = plan.open_template_options()
    named = [label for label in labels if original["name"] in label]
    assert len(named) >= 2 and any(proposed in label for label in named), (
        f"TC-053-092: the picker lists the original and the copy: {labels}"
    )
    screenshot("053_092_05_template_list", "Vorlagenliste: Original und importierte Kopie")
    plan.close_template_options()


# ── TC-053-093 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_093_parcel_page_only_with_its_opt_in(
    plan: Wave9PlanPage, export: PlanExportDialog, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-093 — the PDF gets the parcel page only with the opt-in; the names only with the second opt-in (GP-FR-176).

    Source: REQ-053 GP-FR-176, SR-024, wave 9 placeholder 8; WP 9.10. Precondition (API): a garden with two beds.
    (1) PDF as it opens: the parcel list is off and the assignment switch is not offered; the PDF's bookmarks hold
    "Gartenplan: <Standort>" and no "Parzellenliste: <Standort>". (2) Parcel list on: the assignment switch appears,
    off; the PDF holds both headings, the request asked ``parcel_list=true`` and no names. (3) Assignment on: the
    privacy line names the members' names; the PDF still holds the parcel page and only this request carried
    ``include_assignment=true``. Breaks if the parcel page is added without the opt-in or missing with it, or if names
    are requested without their own opt-in.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc093",
        beds=(
            BedSpec("Beet A", rect(1.0, 1.0, 2.0, 1.0)),
            BedSpec("Beet B", rect(5.0, 5.0, 2.0, 1.0)),
        ),
    )
    plan_heading = f"Gartenplan: {garden.site_name}"
    parcel_heading = f"Parzellenliste: {garden.site_name}"
    print_path = f"/print/garden-plan/{garden.site_key}"
    plan.open(garden.site_key)

    export.open_with_format(plan, "pdf")
    assert export.is_parcel_list_on() is False, "TC-053-093: the parcel list is an opt-in (off)"
    assert not export.has_parcel_assignment(), (
        "TC-053-093: no assignment switch without the parcel list"
    )
    assert export.text_of(export.PRIVACY) == PRIVACY_DEFAULT, export.text_of(export.PRIVACY)
    screenshot(
        "053_093_00_default",
        "PDF-Export im Ausgangszustand: Parzellenliste aus, kein Zuweisungs-Schalter",
    )
    plain = pdf_outline_titles(export.download_file("TC-053-093: the PDF without opt-in")["data"])
    assert plan_heading in plain, f"TC-053-093: the PDF's bookmarks were read: {plain}"
    assert parcel_heading not in plain, f"TC-053-093: no parcel page without the opt-in: {plain}"

    export.open_with_format(plan, "pdf")
    export.set_parcel_list(True)
    assert export.has_parcel_assignment() and not export.is_parcel_assignment_on(), (
        "TC-053-093: under the parcel list the assignment switch is offered, off"
    )
    screenshot("053_093_01_parcel_opt_in", "PDF mit Parzellenliste, Zuweisungen aus")
    parcels = pdf_outline_titles(
        export.download_file("TC-053-093: the PDF with the parcel page")["data"]
    )
    assert plan_heading in parcels and parcel_heading in parcels, (
        f"TC-053-093: the parcel page follows the plan: {parcels}"
    )

    export.open_with_format(plan, "pdf")
    if not export.is_parcel_list_on():
        export.set_parcel_list(True)
    export.set_parcel_assignment(True)
    assert export.text_of(export.PRIVACY) == PRIVACY_PARCEL_ASSIGNMENT, export.text_of(
        export.PRIVACY
    )
    screenshot("053_093_02_assignment_opt_in", "PDF mit Parzellenliste und Zuweisungen")
    named = pdf_outline_titles(
        export.download_file("TC-053-093: the PDF with the assignment")["data"]
    )
    assert parcel_heading in named, f"TC-053-093: the parcel page stays: {named}"

    pdf_requests = [
        url for url in export.request_urls(print_path) if "parcel_list" in url or "bed_list" in url
    ]
    assert len(pdf_requests) == 3, (
        f"TC-053-093: three PDF downloads, the page requested {pdf_requests}"
    )
    first, second, third = pdf_requests
    assert "parcel_list=true" not in first and "include_assignment" not in first, first
    assert "parcel_list=true" in second and "include_assignment" not in second, second
    assert "parcel_list=true" in third and "include_assignment=true" in third, third


# ── TC-053-094 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_094_site_flags_in_the_panel_and_as_the_head_chip(
    browser: WebDriver, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-094 — "Wurzelkonkurrenz" and "Allelopathie-Risiko" are set in the panel and named by the head chip (GP-FR-165).

    Source: REQ-053 GP-FR-165; WP 9.11. Precondition (API): a bed without site features. In the bed view "Merkmale
    ändern" shows the group "Konkurrenz am Standort" (two checkboxes, its hint, no free text); both are ticked and
    saved: the server stores ``flags`` = both, the head shows one neutral chip "Wurzelkonkurrenz/Allelopathie-Risiko am
    Standort gemeldet". "Allelopathie-Risiko" is unticked: the chip names only "Wurzelkonkurrenz"; the last is
    unticked: no flag stored, no chip. Breaks if a flag is not stored, the chip names other flags than stored, or a
    chip stays without a flag.
    """
    head = BedHeadWave9(browser, base_url)
    dialog = SiteConditionsDialog(browser, base_url)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc094",
        beds=(BedSpec("Beet 1", rect(1.0, 1.0, 2.0, 1.0)),),
    )
    bed = garden.bed_key("Beet 1")

    head.open(bed, "soil")
    assert head.site_flags_badge() is None, "TC-053-094: no chip before a flag is set"
    head.open_site_dialog()
    group = dialog.group_info("flags")
    assert group["title"] == "Konkurrenz am Standort", f"TC-053-094: group title {group['title']!r}"
    assert sorted(value for value, _type in group["inputs"]) == [
        "allelopathy_risk",
        "root_competition",
    ], group
    assert {kind for _value, kind in group["inputs"]} == {"checkbox"}, (
        f"TC-053-094: both are checkboxes: {group}"
    )
    assert group["hint"].startswith("Steht das Beet unter oder neben Bäumen"), (
        f"TC-053-094: hint {group['hint']!r}"
    )
    assert not dialog.has_free_text_for("flags"), "TC-053-094: the flags are choices, no free text"
    dialog.toggle("flags", "root_competition")
    dialog.toggle("flags", "allelopathy_risk")
    screenshot(
        "053_094_01_panel", "Standortmerkmale: Wurzelkonkurrenz und Allelopathie-Risiko gewählt"
    )
    dialog.save_and_wait_closed("TC-053-094: both flags")
    assert sorted(site_conditions(base_url, e2e_seed_data, bed).get("flags") or []) == [
        "allelopathy_risk",
        "root_competition",
    ], f"TC-053-094: stored flags {site_conditions(base_url, e2e_seed_data, bed)}"
    head.wait_for_site_flags_badge(
        "Wurzelkonkurrenz/Allelopathie-Risiko am Standort gemeldet", "TC-053-094: both flags"
    )
    screenshot("053_094_02_chip_both", "Kopf des Beets: Chip mit beiden Meldungen")

    head.open_site_dialog()
    dialog.toggle("flags", "allelopathy_risk")
    dialog.save_and_wait_closed("TC-053-094: one flag left")
    head.wait_for_site_flags_badge("Wurzelkonkurrenz am Standort gemeldet", "TC-053-094: one flag")
    screenshot("053_094_03_chip_one", "Kopf des Beets: Chip nur mit Wurzelkonkurrenz")
    assert site_conditions(base_url, e2e_seed_data, bed).get("flags") == ["root_competition"]

    head.open_site_dialog()
    dialog.toggle("flags", "root_competition")
    dialog.save_and_wait_closed("TC-053-094: no flag")
    assert not (site_conditions(base_url, e2e_seed_data, bed).get("flags") or []), (
        "TC-053-094: no flag is stored after unticking both"
    )
    head.open(bed, "soil")
    assert head.site_flags_badge() is None, "TC-053-094: without a flag the chip is gone"
    screenshot("053_094_04_chip_gone", "Ohne Meldung kein Chip")


# ── TC-053-095 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_095_nearest_water_source_in_list_head_and_csv(
    browser: WebDriver,
    plan: Wave9PlanPage,
    export: PlanExportDialog,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-095 — the distance to the nearest tap in the bed list, the bed head and the CSV; none without geometry (GP-FR-167).

    Source: REQ-053 GP-FR-167; WP 9.12. Precondition (API): a 10 x 10 m garden, "Beet Nah" (1..3 x 1..2 m) and
    "Beet Fern" (6..8 x 6..7 m), a tap (water source, point) at (5.5, 1.5) m, and "Beet Alt" without geometry. Edge to
    edge in a straight line: Nah 2.5 m, Fern sqrt(0.5² + 4.5²) = 4.528 m (stored to the mm), Alt none. The server's
    bed list carries those values; the plan's bed list column "Wasserquelle" reads "2,5 m", "4,53 m" and "—"; the
    head of "Beet Nah" reads "2,5 m Luftlinie von der Beetkante", the head of "Beet Alt" has no such fact; the CSV
    with the column ``nearest_water_source_m`` holds 2.5, 4.528 and an empty cell. Breaks if the distance is centre
    to centre, rounded wrongly, shown as "0 m" for a bed without geometry, or missing in one of the three places.
    """
    head = BedHeadWave9(browser, base_url)
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc095",
        beds=(
            BedSpec("Beet Nah", rect(1.0, 1.0, 2.0, 1.0)),
            BedSpec("Beet Fern", rect(6.0, 6.0, 2.0, 1.0)),
        ),
    )
    near, far = garden.bed_key("Beet Nah"), garden.bed_key("Beet Fern")
    add_water_source(
        base_url,
        e2e_seed_data,
        site_key=garden.site_key,
        revision=garden.revision,
        point=(5.5, 1.5),
        label=f"Hahn {unique_tag()}",
    )
    legacy = create_bed_without_area(
        base_url, e2e_seed_data, site_key=garden.site_key, name="Beet Alt"
    )

    rows = bed_list_rows(base_url, e2e_seed_data, garden.site_key)
    stored = {key: rows[key].get("nearest_water_source_m") for key in (near, far, legacy)}
    assert stored == {near: 2.5, far: 4.528, legacy: None}, (
        f"TC-053-095: the server's distances {stored}"
    )

    plan.open(garden.site_key)
    assert plan.has_bed_list_column("waterSource"), (
        "TC-053-095: the column appears once the site has a source"
    )
    shown = {
        key: plan.bed_list_cell(key, "waterSource", "TC-053-095") for key in (near, far, legacy)
    }
    assert shown == {near: "2,5 m", far: "4,53 m", legacy: "—"}, (
        f"TC-053-095: the bed list shows {shown}"
    )
    screenshot("053_095_01_bed_list", "Beetliste: Spalte Wasserquelle")

    export.open_from(plan)
    export.set_column("nearest_water_source_m", True)
    saved = export.download("TC-053-095: the bed list CSV")
    header, by_name = _csv_by_name(saved["text"])
    assert "nearest_water_source_m" in header, f"TC-053-095: the CSV carries the column: {header}"
    cells = {
        name: by_name[name]["nearest_water_source_m"]
        for name in ("Beet Nah", "Beet Fern", "Beet Alt")
    }
    assert float(cells["Beet Nah"].replace(",", ".")) == 2.5, cells
    assert float(cells["Beet Fern"].replace(",", ".")) == 4.528, cells
    assert cells["Beet Alt"] == "", f"TC-053-095: no distance is an empty cell, never 0: {cells}"

    head.open(near, "soil")
    # The head fact is a label line and a value line (``BedHeader`` ``Fact``); its text content joins them.
    water = head.head_water_source()
    assert water == "Nächste Wasserquelle" + "2,5 m Luftlinie von der Beetkante", (
        f"TC-053-095: the head of Beet Nah (label, then value): {water!r}"
    )
    screenshot("053_095_02_head", "Kopf von Beet Nah: 2,5 m Luftlinie von der Beetkante")
    head.open(legacy, "soil")
    assert head.head_water_source() is None, (
        "TC-053-095: a bed without geometry has no distance in the head"
    )
    screenshot(
        "053_095_03_head_legacy", "Kopf von Beet Alt (ohne Geometrie): keine Wasserquellen-Angabe"
    )


# ── TC-053-047 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_047_rain_skipped_logs_rain_without_amount_and_keeps_tasks_open(
    plan: Wave9PlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-047 - Gießrunde „Regen — übersprungen": one rainfall line per bed without an amount, nothing watered (GP-FR-117).

    Precondition (API): a zone with "Beet A" and "Beet B", no watering recorded, an open watering task on "Beet A".
    In the zone's watering round the user writes a note and presses "Regen — übersprungen" (one click, no amount).
    Asserted: the result says the round was saved as skipped with "Regen-Einträge ohne Menge. Offene Gieß-Aufgaben
    bleiben offen." and names both beds; the server holds per bed exactly one ``rainfall`` line with that note and
    no quantity, no ``watering`` line; the watering task is still open; the zone still reads "Noch kein Gießen
    erfasst." Breaks if the skip writes an amount or a watering, closes the task, or changes the zone's watering
    state. (TC-053-047 was "not automated" in wave 7 - the action did not exist; WP 9.13 built it.)
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc047",
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
    task = create_bed_task(
        base_url, e2e_seed_data, bed_key=bed_a, name=f"Gießen {unique_tag()}", category="watering"
    )
    note = f"Regen seit dem Morgen {unique_tag()}"

    plan.open(garden.site_key)
    plan.open_zone_panel()
    plan.open_zone(zone["key"])
    assert NO_WATERING_YET in plan.text_of(plan.ZONE_LAST_WATERING), plan.text_of(
        plan.ZONE_LAST_WATERING
    )
    plan.open_watering_round()
    plan.write_round_note(note)
    screenshot("053_047_01_round_dialog", "Gießrunde mit „Regen — übersprungen“")
    beds_line = plan.skip_round_for_rain("TC-053-047")
    assert beds_line == "Eingetragen für 2 Beete: Beet A, Beet B.", (
        f"TC-053-047: the result names the beds: {beds_line!r}"
    )
    assert RAIN_RESULT_MARKER in plan.rain_result_text(), f"TC-053-047: {plan.rain_result_text()!r}"
    screenshot("053_047_02_rain_result", "Runde als übersprungen gespeichert")
    plan.close_watering_round()

    for bed in (bed_a, bed_b):
        rain = care_events(base_url, e2e_seed_data, bed, category="rainfall")
        assert [(e["summary"], e["quantity"]) for e in rain] == [(note, None)], (
            f"TC-053-047: one rainfall line without an amount at {bed}: {rain}"
        )
        assert care_events(base_url, e2e_seed_data, bed, category="watering") == [], (
            f"TC-053-047: nothing counts as watered at {bed}"
        )
    assert task_state(base_url, e2e_seed_data, task)["status"] not in ("completed", "skipped"), (
        "TC-053-047: the open watering task stays open"
    )
    assert NO_WATERING_YET in plan.text_of(plan.ZONE_LAST_WATERING), (
        f"TC-053-047: the zone's watering state is unchanged: {plan.text_of(plan.ZONE_LAST_WATERING)!r}"
    )


# ── TC-053-096 ──────────────────────────────────────────────────────────────


@pytest.mark.requires_desktop
def test_tc_053_096_ctrl_d_duplicates_the_selected_bed(
    plan: Wave9PlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-096 — Ctrl+D duplicates the selected bed one grid step down-right as "<Name> (Kopie)" (GP-FR-025/026).

    Source: REQ-053 GP-FR-025, GP-FR-026, V-05; WP 9.14. Precondition (API): a 10 x 10 m garden (grid 10 cm) with
    "Beet K" 2 x 1 m at (2, 4), without planting positions (slot copy: see the module docstring). The bed is
    selected with the keyboard and Ctrl+D is pressed on the plan: one unsaved change, two beds drawn, the copy
    selected and drawn one grid step down-right at (2.1, 3.9). A copy one grid step away still overlaps its original,
    and two beds of one parent may not overlap (V-05, ``bed.overlap``) - so, as a gardener does, the copy is moved
    clear with Shift+Arrow-Down (10 grid steps) before "Speichern". Saved, the server holds "Beet K (Kopie)" at
    (2.1, 2.9) with the same size and type beside the unchanged original. Breaks if Ctrl+D does nothing, opens the
    browser's bookmark dialog instead, duplicates twice, does not select the copy, or the copy differs.
    """
    garden = provision_garden(
        base_url,
        e2e_seed_data,
        purpose="tc096",
        beds=(BedSpec("Beet K", rect(2.0, 4.0, 2.0, 1.0)),),
    )
    source = garden.bed_key("Beet K")
    plan.open(garden.site_key)
    plan.select_with_keyboard(source)
    plan.press(Keys.CONTROL, "d")
    plan.wait_for_pending(1, "TC-053-096: Ctrl+D is one unsaved change")
    drawn = plan.object_keys()
    assert len(drawn) == 2, f"TC-053-096: the bed and its copy are drawn: {drawn}"
    (copy_key,) = [key for key in drawn if key != source]
    plan.wait_for_selected(copy_key, True, "TC-053-096: the copy is selected after Ctrl+D")
    plan.wait_for_shape_origin(copy_key, (2.1, 3.9), "TC-053-096: one grid step down-right")
    screenshot("053_096_01_duplicated", "Strg+D: Kopie von Beet K, ein Rasterschritt versetzt")

    plan.press(Keys.SHIFT, Keys.ARROW_DOWN)
    plan.wait_for_shape_origin(copy_key, (2.1, 2.9), "TC-053-096: the copy moved clear of Beet K")
    plan.save_with_button()

    stored = read_plan(base_url, e2e_seed_data, garden.site_key)
    beds = {loc["name"]: loc for loc in stored["locations"]}
    assert set(beds) == {"Beet K", "Beet K (Kopie)"}, f"TC-053-096: stored beds {sorted(beds)}"
    copy, original = beds["Beet K (Kopie)"], beds["Beet K"]
    assert original["key"] == source and tuple(original["geometry"]["origin"]) == (2.0, 4.0), (
        original
    )
    assert tuple(copy["geometry"]["origin"]) == (2.1, 2.9), (
        f"TC-053-096: the copy where it was moved to: {copy['geometry']}"
    )
    assert (copy["geometry"]["width_m"], copy["geometry"]["length_m"]) == (2.0, 1.0), copy[
        "geometry"
    ]
    assert copy["location_type_key"] == original["location_type_key"], copy
    screenshot("053_096_02_saved", "Kopie verschoben und gespeichert")


# ── TC-053-097 ──────────────────────────────────────────────────────────────


def _grid(name: str, slots_per_bed: int) -> GridPlan:
    """30 beds of 3.3 x 3 m (as the renderer measurement's synthetic plan), *slots_per_bed* unplanted positions."""
    return GridPlan(
        name=name,
        columns=6,
        rows=5,
        bed_width_m=3.3,
        bed_length_m=3.0,
        pitch_x_m=3.6,
        pitch_y_m=3.2,
        slots=tuple(
            (round(0.15 + c * 0.3, 3), round(0.15 + r * 0.3, 3))
            for r in range(10)
            for c in range(10)
        )[:slots_per_bed],
        planted=False,
    )


@pytest.mark.requires_desktop
def test_tc_053_097_konva_draws_a_plan_of_three_thousand_objects(
    plan: Wave9PlanPage, base_url: str, e2e_seed_data: dict, screenshot
) -> None:
    """TC-053-097 — from 3 000 objects the plan is drawn by Konva on a canvas; below, by SVG (GP-NFR-033, D-01, WP 9.7).

    Source: REQ-053 GP-NFR-033/034, decision D-01 (WP 9.6 was Go), WP 9.7. Precondition (API, plan import): two
    gardens of 30 beds - one with 99 positions per bed (30 + 2 970 = 3 000 objects), one with 98 (2 970). The first is
    drawn with ``data-renderer="konva"`` and at least one ``<canvas>`` in the editor; the second with
    ``data-renderer="svg"`` and no canvas. Breaks if the threshold moved, the switch never happens, or Konva is loaded
    for a small plan.
    """
    at = provision_grid_plan(base_url, e2e_seed_data, _grid("konva-3000", 99))
    below = provision_grid_plan(base_url, e2e_seed_data, _grid("konva-2970", 98))
    assert at.stored_beds + at.stored_slots == KONVA_MIN_PLAN_OBJECTS, at.as_dict()
    assert below.stored_beds + below.stored_slots == KONVA_MIN_PLAN_OBJECTS - 30, below.as_dict()

    plan.open(at.garden.site_key, timeout=90)
    plan.wait_for_renderer("konva", "TC-053-097: 3 000 objects")
    assert plan.canvas_count() >= 1, "TC-053-097: Konva draws on a canvas"
    screenshot("053_097_01_konva", "3 000 Objekte: Konva-Renderer")

    plan.open(below.garden.site_key, timeout=90)
    plan.wait_for_renderer("svg", "TC-053-097: 2 970 objects")
    assert plan.canvas_count() == 0, "TC-053-097: the SVG renderer draws no canvas"
    screenshot("053_097_02_svg", "2 970 Objekte: SVG-Renderer")
