"""E2E of REQ-053 wave 8 part A - soil, area dose, nutrient hint, history CSV, rotation, suggestions (WP 8.30, #2673).

Spec pin REQ-053 v1.9. Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md, GP-FR rows "abgeleitet"):
  TC-053-061  ->  record three soil analyses in the browser; the pH history keeps "CaCl₂-Lösung" and "Wasser"   (GP-FR-122)
                  apart, marks the method change, the table view lists the same values, the profile holds
                  the newest; unchanged after a reload
  TC-053-062  ->  "Gehaltsklasse" only for a lab value by CAL; an older analysis does not overwrite the        (GP-FR-122)
                  profile; a future date and an EC value without method are refused in the dialog
  TC-053-063  ->  feeding with a catalogue product: the data-sheet rate is pre-filled, the total for 3,6 m²   (GP-FR-123)
                  follows the typing (288 g, 360 g, 10,8 L), a dose of 0 per m² is refused, the stored
                  event carries 80 g/m² and 288 g; a bed without area blocks the per-m² units
  TC-053-064  ->  soil amendment (compost), mulch by the care log (bark mulch), liming with the text-only    (GP-FR-124)
                  hint and no pre-filled amount; three history entries, both tasks completed
  TC-053-065  ->  nutrient hint as shipped: no chip, no salt chip, no amount in the head or the soil tab    (GP-FR-125)
                  while the server says "insufficient_data / thresholds_without_source"
  TC-053-066  ->  SKIPPED with reason (no way for the E2E stack to activate a sourced test threshold)        (GP-FR-125)
  TC-053-067  ->  history as CSV: UTF-8 BOM, formula cells prefixed with ', the performer's display name,   (GP-FR-104)
                  only the filtered category of the bed; the tenant-wide page's file holds the other bed
  TC-053-068  ->  rotation matrix: columns, families differ by pattern/code, "Fruchtfolge aus" mark, backfill (GP-FR-135)
                  from an empty past cell (matrix and bed history agree), jump to the bed
  TC-053-069  ->  follow-up crop recommendation after a heavy feeder; "no history" on an empty bed;         (GP-FR-133)
                  "Dauerkultur" on top of "Eingeschaltet" is refused and nothing changes; state after reload
  TC-053-070  ->  accept a seeded suggestion: it becomes an ordinary open task, no care entry               (GP-FR-086)
  TC-053-071  ->  dismiss one of two seeded suggestions: it is closed (skipped) without a care entry,       (GP-FR-086)
                  the other stays a suggestion

Deviations from the written steps, on purpose (each also named in the test's docstring):
  TC-053-061/062  "vor einem Jahr" / "vor zwei Jahren" are outside the dialog's 365-day window; the tests use 300
                  and 200 days. The date is written through the field's native value setter (``SoilAnalysisDialog
                  .set_performed_days_from_now``): typing a ``datetime-local`` value is locale-dependent in Chrome.
  TC-053-063  The l/m² case switches the unit of the same product (no second product); the "≈ kg N/ha" line is
              asserted as a labelled approximation; the history row shows the dose only (the total is read from
              the stored event).
  TC-053-065  "Vorjahr Erbse" is not arranged: a preceding legume only adds a reason code to a hint the shipped
              state does not show (§15.3 M1 needs a sourced relief).
  TC-053-067  The display name is whatever name the acting account carries (light: the system user, full: the
              E2E demo user); the file is read from the blob the page saves (``DownloadCapture``), the Selenium
              grid's download folder is out of the runner's reach.
  TC-053-068  Years are relative to the current UTC year (the backfill accepts the last ten years only). Not
              automated: the planned 2027 cell (no rotation plan is part of this arrangement), the greyscale view
              (two families differing by fill pattern and code is asserted instead), the 390 px phone view.
  TC-053-071  The viewer half needs a second account with the role "Betrachter", which the E2E stack does not
              seed; the "abgebrochene Aufgaben" filter does not exist in the care tab (the skipped status is read
              from the server).

Preconditions are self-provisioned through the application's own API, one fresh site per test with a UUID-derived
name (`_garden_plan_helpers.py`), species from the seed catalogue. ONE named exception: the suggestion flag of a task
has no route and no producer yet (REQ-053 E-02), so ``mark_task_suggested`` sets it on a task created through
``POST /tasks`` directly in the backend's ArangoDB (see its docstring). All cases are desktop cases and carry
``requires_desktop``.

Waits are anchored on state - a closed dialog, a table row count, a live total line, a field's error line, the
switch section's "Gespeichert.", a row leaving the suggestions section, the saved download - never on time, and
there is no retry loop. Every written outcome is read back from the server.
"""

from __future__ import annotations

import csv
import io
import re

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._garden_plan_helpers import (
    BedSpec,
    backfill_year,
    bed_summary,
    botanical_family_key,
    care_events,
    create_bed_task,
    create_bed_without_area,
    create_fertilizer,
    log_care_event,
    mark_task_suggested,
    patch_location,
    plant_on_positions,
    provision_garden,
    record_soil_analysis,
    rect,
    rotation_matrix,
    rotation_years,
    soil_analyses,
    soil_series,
    species,
    stored_soil_profile,
    succession_recommendation,
    task_state,
    tenant_location,
    unique_tag,
    utc_today,
)
from .pages.bed_care_page import BedCareTab, CareHistoryPage, HistoryTab
from .pages.bed_view_page import BedViewPage
from .pages.rotation_matrix_page import RotationMatrixPage
from .pages.soil_tab_page import SoilTab

pytestmark = pytest.mark.requires_desktop

TOMATO = "Solanum lycopersicum"
CABBAGE = "Brassica oleracea var. capitata"
PEA = "Pisum sativum"
#: The seed catalogue has no Feldsalat (Valerianella locusta); lettuce stands in as the spring pre-crop.
LETTUCE = "Lactuca sativa"

#: A bed of 3,0 x 1,2 m: 3,6 m², the area of the TC-053-063 arithmetic.
BED_1 = BedSpec("Beet 1", rect(1.0, 1.0, 3.0, 1.2))
BED_2 = BedSpec("Beet 2", rect(1.0, 4.0, 2.0, 1.0))
BED_3 = BedSpec("Beet 3", rect(1.0, 7.0, 2.0, 1.0))

#: Columns of the care-history CSV (``app/domain/engines/care_event_csv_engine.py`` CARE_EVENT_CSV_COLUMNS).
CSV_COLUMNS = [
    "performed_at",
    "category",
    "summary",
    "location_key",
    "plant_names",
    "performed_by",
    "performed_for",
    "trigger",
    "reason",
    "product_label",
    "quantity",
    "unit",
    "quantity_total",
    "quantity_total_unit",
    "material",
    "observed_outcome",
    "outcome_rating",
    "photo_count",
    "superseded",
    "voided_at",
    "void_reason",
    "redacted_at",
    "key",
]

#: A number followed by a dose or amount unit: what the nutrient hint must never show (hint-only list).
AMOUNT = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:g/m²|g pro m²|Gramm|kg/ha|kg N/ha|kg\b|l/m²|L/m²|Liter|ml\b|g N\b)",
    re.IGNORECASE,
)


@pytest.fixture
def bed_view(browser: WebDriver, base_url: str) -> BedViewPage:
    return BedViewPage(browser, base_url)


@pytest.fixture
def care_tab(browser: WebDriver, base_url: str) -> BedCareTab:
    return BedCareTab(browser, base_url)


@pytest.fixture
def history_tab(browser: WebDriver, base_url: str) -> HistoryTab:
    return HistoryTab(browser, base_url)


@pytest.fixture
def soil_tab(browser: WebDriver, base_url: str) -> SoilTab:
    return SoilTab(browser, base_url)


@pytest.fixture
def matrix(browser: WebDriver, base_url: str) -> RotationMatrixPage:
    return RotationMatrixPage(browser, base_url)


@pytest.fixture
def care_history(browser: WebDriver, base_url: str) -> CareHistoryPage:
    return CareHistoryPage(browser, base_url)


def _garden(base_url: str, seed: dict, purpose: str, *beds: BedSpec):
    return provision_garden(base_url, seed, purpose=purpose, beds=beds or (BED_1,))


def _parse_csv(saved: dict, what: str) -> tuple[list[str], list[dict[str, str]]]:
    """Header and rows of a saved CSV download; loud on a missing BOM (checked by the caller) or an empty file."""
    text = saved["text"]
    if not text.startswith("﻿"):
        raise AssertionError(
            f"{what}: the file does not start with the UTF-8 byte order mark: {text[:20]!r}"
        )
    reader = csv.reader(io.StringIO(text[1:], newline=""))
    lines = list(reader)
    if not lines:
        raise AssertionError(f"{what}: the file has no header row")
    header = lines[0]
    return header, [dict(zip(header, line, strict=True)) for line in lines[1:] if line]


# ── TC-053-061 ──────────────────────────────────────────────────────────────


def test_tc_053_061_soil_analyses_keep_each_ph_method_on_its_own_line(
    bed_view: BedViewPage,
    soil_tab: SoilTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-061 — three soil analyses recorded in the browser; the pH history keeps the methods apart (GP-FR-122).

    Precondition (API): a fresh bed without analysis. Recorded through "Bodenanalyse erfassen": pH 6,4 CaCl₂ 300
    days back, pH 6,8 CaCl₂ plus humus 3 % an hour ago, pH 7,2 "Wasser" now. Asserted on the server: the pH series
    is ``cacl2: [6.4, 6.8]`` and ``h2o: [7.2]`` (nothing converted, nothing merged), the method change is recorded,
    the profile holds the newest values (pH 7,2 by water, humus 3). Asserted in the browser: the dialog names
    Messgröße, Wert, Einheit, Methode, Entnahmetiefe and Herkunft; the pH panel draws a chart; "Als Tabelle
    anzeigen" shows the same three values with two "CaCl₂-Lösung" rows, one "Wasser" row and one "Methodenwechsel"
    mark; after a reload the table still holds three rows. Breaks if the dialog stores nothing, if the server merges
    or converts the methods, if the profile keeps an older value, or if the table loses a row.

    Spec deviation: "vor einem Jahr" lies outside the dialog's 365-day window - 300 days are used.
    """
    garden = _garden(base_url, e2e_seed_data, "tc061")
    bed = garden.bed_key(BED_1.name)
    bed_view.open(bed, "soil")
    screenshot("053_061_01_soil_tab_empty", "Boden-Tab: noch keine Bodenanalyse")

    dialog = soil_tab.open_record_dialog()
    labels = " | ".join(dialog.labels())
    for label in (
        "Probe genommen am",
        "Herkunft",
        "Entnahmetiefe",
        "Messgröße",
        "Wert",
        "Einheit",
        "Methode",
    ):
        assert label in labels, (
            f"TC-053-061: the dialog should offer {label!r}; its labels: {labels}"
        )
    dialog.set_performed_days_from_now(-300)
    dialog.set_source("lab")
    dialog.set_value(1, "6,4")
    dialog.set_method(1, "cacl2")
    screenshot("053_061_02_dialog_first", "Bodenanalyse erfassen: pH 6,4 CaCl₂ vor 300 Tagen")
    dialog.submit_and_wait_closed("TC-053-061: first analysis")
    soil_tab.wait_for_history_rows("ph", 1, "TC-053-061: after the first analysis")

    dialog = soil_tab.open_record_dialog()
    dialog.set_performed_days_from_now(-1 / 24)
    dialog.set_value(1, "6,8")
    dialog.set_method(1, "cacl2")
    dialog.add_row(2)
    dialog.set_parameter(2, "humus")
    dialog.set_value(2, "3")
    dialog.submit_and_wait_closed("TC-053-061: second analysis")
    soil_tab.wait_for_history_rows("ph", 2, "TC-053-061: after the second analysis")

    dialog = soil_tab.open_record_dialog()
    dialog.set_value(1, "7,2")
    dialog.set_method(1, "h2o")
    dialog.submit_and_wait_closed("TC-053-061: third analysis")
    soil_tab.wait_for_history_rows("ph", 3, "TC-053-061: after the third analysis")

    analyses = soil_analyses(base_url, e2e_seed_data, bed)
    assert soil_series(analyses, "ph") == {"cacl2": [6.4, 6.8], "h2o": [7.2]}, (
        f"TC-053-061: each pH method is its own series, values as typed: {analyses['series']}"
    )
    changes = [
        (c["parameter"], c["from_method"], c["to_method"]) for c in analyses["method_changes"]
    ]
    assert ("ph", "cacl2", "h2o") in changes, (
        f"TC-053-061: the method change is recorded: {changes}"
    )
    profile = stored_soil_profile(base_url, e2e_seed_data, bed)
    assert (profile.get("ph"), profile.get("ph_method"), profile.get("humus_percent")) == (
        7.2,
        "h2o",
        3.0,
    ), f"TC-053-061: the profile holds the newest pH (7,2 water) and humus (3): {profile}"

    assert soil_tab.chart_drawn("ph"), (
        "TC-053-061: the pH panel draws its chart before the table switch"
    )
    screenshot(
        "053_061_03_chart", "Verlauf pH-Wert: zwei Linien je Methode, Methodenwechsel markiert"
    )
    soil_tab.show_as_table()
    assert not soil_tab.chart_drawn("ph"), (
        "TC-053-061: 'Als Tabelle anzeigen' replaces the chart by the table"
    )
    rows = soil_tab.history_rows("ph")
    methods = [row[1] for row in rows]
    assert sum(m.startswith("CaCl₂-Lösung") for m in methods) == 2, (
        f"TC-053-061: two CaCl₂ rows: {rows}"
    )
    assert sum(m.startswith("Wasser") for m in methods) == 1, f"TC-053-061: one water row: {rows}"
    assert sum("Methodenwechsel" in m for m in methods) == 1, (
        f"TC-053-061: one method-change mark: {rows}"
    )
    values = " | ".join(row[2] for row in rows)
    for value in ("6,4", "6,8", "7,2"):
        assert value in values, f"TC-053-061: the table names {value}: {rows}"
    humus = soil_tab.history_rows("humus")
    assert len(humus) == 1 and humus[0][2].startswith("3"), (
        f"TC-053-061: one humus row of 3 %: {humus}"
    )
    screenshot("053_061_04_table", "Tabellenansicht: drei pH-Werte mit Datum und Methode")

    bed_view.open(bed, "soil")
    reloaded = soil_tab.wait_for_history_rows("ph", 3, "TC-053-061: after the reload")
    assert sorted(row[2] for row in reloaded) == sorted(row[2] for row in rows), (
        f"TC-053-061: the reload shows the same pH values: {reloaded} vs {rows}"
    )


# ── TC-053-062 ──────────────────────────────────────────────────────────────


def test_tc_053_062_content_class_only_from_a_lab_and_an_older_analysis_keeps_the_profile(
    bed_view: BedViewPage,
    soil_tab: SoilTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-062 — "Gehaltsklasse" only for a lab value by CAL; older analysis, future date, EC without method (GP-FR-122).

    Precondition (API): a bed with one analysis from today, pH 6,8 CaCl₂ (the body the dialog sends). In the
    dialog: Phosphor by CAL from a "Testset" offers no "Gehaltsklasse", from "Labor" it does. pH 5,9 CaCl₂ 200 days
    back is stored: the server series becomes ``cacl2: [5.9, 6.8]`` and the profile stays at 6,8; the table gains the
    older row. A date tomorrow is refused with "Der Zeitpunkt liegt in der Zukunft.", an EC value without method with
    "Wähle die Messmethode – ohne sie ist der Wert nicht lesbar."; after cancelling, the server still counts two
    analyses. Breaks if a test kit can state a class, if an older analysis overwrites the profile, or if the dialog
    stores a future or method-less value.

    Spec deviations: "vor zwei Jahren" lies outside the 365-day window - 200 days are used. The written expectation
    "EC ohne Methode wird gespeichert" contradicts the product (EC needs its method, U-002); the TC text was
    corrected to the refusal.
    """
    garden = _garden(base_url, e2e_seed_data, "tc062")
    bed = garden.bed_key(BED_1.name)
    record_soil_analysis(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        measurements=[
            {"parameter": "ph", "value": 6.8, "unit": "pH", "source": "lab", "ph_method": "cacl2"}
        ],
    )
    bed_view.open(bed, "soil")
    soil_tab.wait_for_history_rows("ph", 1, "TC-053-062: the seeded analysis")

    dialog = soil_tab.open_record_dialog()
    dialog.set_parameter(1, "p")
    dialog.set_method(1, "cal")
    dialog.set_source("test_kit")
    dialog.wait_for_content_class(1, False, "TC-053-062: P by CAL from a test kit")
    dialog.set_source("lab")
    dialog.wait_for_content_class(1, True, "TC-053-062: P by CAL from a lab")
    screenshot("053_062_01_content_class", "Gehaltsklasse nur bei Labor und CAL")

    dialog.set_parameter(1, "ph")
    dialog.wait_for_content_class(1, False, "TC-053-062: a pH row")
    dialog.set_value(1, "5,9")
    dialog.set_method(1, "cacl2")
    dialog.set_performed_days_from_now(-200)
    dialog.submit_and_wait_closed("TC-053-062: the older analysis")
    rows = soil_tab.wait_for_history_rows("ph", 2, "TC-053-062: after the older analysis")
    assert rows[0][2].startswith("5,9"), (
        f"TC-053-062: the older value stands first (oldest first): {rows}"
    )
    analyses = soil_analyses(base_url, e2e_seed_data, bed)
    assert soil_series(analyses, "ph") == {"cacl2": [5.9, 6.8]}, analyses["series"]
    assert stored_soil_profile(base_url, e2e_seed_data, bed).get("ph") == 6.8, (
        "TC-053-062: an older analysis must not overwrite the profile's newer pH 6,8"
    )

    dialog = soil_tab.open_record_dialog()
    dialog.set_value(1, "6,0")
    dialog.set_method(1, "cacl2")
    dialog.set_performed_days_from_now(1)
    dialog.submit_expecting_field_error(
        dialog.PERFORMED_AT, "Der Zeitpunkt liegt in der Zukunft.", "TC-053-062: a date tomorrow"
    )
    screenshot("053_062_02_future_refused", "Datum morgen: Feldmeldung, Dialog bleibt offen")
    dialog.set_performed_days_from_now(0)
    dialog.set_parameter(1, "ec")
    dialog.set_value(1, "1,2")
    dialog.submit_expecting_field_error(
        "soil-analysis-method-1",
        "Wähle die Messmethode – ohne sie ist der Wert nicht lesbar.",
        "TC-053-062: EC without its method",
    )
    screenshot("053_062_03_ec_without_method", "EC ohne Methode: Feldmeldung")
    dialog.cancel()

    after = soil_analyses(base_url, e2e_seed_data, bed)
    assert after["analyses"] == 2, (
        f"TC-053-062: the refused analyses wrote nothing: {after['analyses']} analyses"
    )
    assert "check_salt_content" not in (
        bed_summary(base_url, e2e_seed_data, bed).get("nutrient_hint") or {}
    ).get("reasons", []), "TC-053-062: no salt hint from a refused EC value"


# ── TC-053-063 ──────────────────────────────────────────────────────────────


def test_tc_053_063_area_dose_prefills_the_rate_and_totals_it_over_the_bed(
    bed_view: BedViewPage,
    care_tab: BedCareTab,
    history_tab: HistoryTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-063 — feeding with a data-sheet rate: live total over 3,6 m², 0 refused, a bed without area (GP-FR-123).

    Precondition (API): bed "Beet 1" of 3,0 x 1,2 m (3,6 m²) with an open feeding task, a tenant product with
    80 g/m² and N 10 %, and a legacy bed without geometry (``area_m2 = 0``) with an open feeding task. In the
    completion dialog: choosing the product pre-fills 80 "Gramm pro m²" with the data-sheet line and the total
    "Gesamtmenge für 3,6 m²: 288 g", typing 100 shows 360 g, "Liter pro m²" with 3 shows "10,8 L", the
    approximation reads "Näherung: ≈ 80 kg N/ha", a dose of 0 is refused with "Eine Menge pro m² muss größer als 0
    sein." and the dialog stays open; 80 g/m² is stored. Asserted on the server: one feeding event with
    ``quantity 80 g_per_m2``, ``quantity_total 288 g`` and the product's label; the history row names "80 Gramm pro
    m²". On the bed without area "Gramm pro m²" and "Liter pro m²" are disabled and the no-area hint is shown.
    Breaks if the rate is not pre-filled, if the total does not follow the typing or the area, if 0 per m² is
    accepted, or if a bed without area offers a per-m² unit.

    Spec deviations: the l/m² case changes the unit of the same product; the history row shows the dose only
    (the total is read from the stored event).
    """
    garden = _garden(base_url, e2e_seed_data, "tc063")
    bed = garden.bed_key(BED_1.name)
    area = float(tenant_location(base_url, e2e_seed_data, bed)["area_m2"])
    assert area == pytest.approx(3.6, abs=0.01), (
        f"the arrangement needs 3,6 m², the bed measures {area}"
    )
    tag = unique_tag()
    product = f"E2E Hornmehl {tag}"
    create_fertilizer(
        base_url, e2e_seed_data, name=product, rate_g_per_m2=80.0, npk=(10.0, 0.0, 0.0)
    )
    task = create_bed_task(
        base_url, e2e_seed_data, bed_key=bed, name=f"Düngen {tag}", category="feeding"
    )
    legacy = create_bed_without_area(
        base_url, e2e_seed_data, site_key=garden.site_key, name=f"Beet 2 {tag}"
    )
    legacy_task = create_bed_task(
        base_url,
        e2e_seed_data,
        bed_key=legacy,
        name=f"Düngen ohne Fläche {tag}",
        category="feeding",
    )

    bed_view.open(bed, "care")
    care_tab.wait_for_task(f"Düngen {tag}")
    dialog = care_tab.open_completion(task)
    dialog.choose_product(product)
    assert (dialog.quantity_value(), dialog.unit_value()) == ("80", "g_per_m2"), (
        f"TC-053-063: the data-sheet rate is pre-filled: {dialog.quantity_value()!r} {dialog.unit_value()!r}"
    )
    assert "aus dem Datenblatt" in dialog.text_of("rate-source")
    assert "Gesamtmenge für 3,6 m²: 288 g" in dialog.wait_for_total("288 g", "TC-053-063: 80 g/m²")
    nitrogen = dialog.text_of("nitrogen")
    assert nitrogen.startswith("Näherung: ≈ 80 kg N/ha"), (
        f"TC-053-063: the approximation line: {nitrogen!r}"
    )
    screenshot("053_063_01_prefilled", "Erledigen: Datenblatt-Rate 80 g/m², Gesamtmenge 288 g")

    dialog.set_quantity_only("100")
    dialog.wait_for_total("360 g", "TC-053-063: 100 g/m²")
    dialog.set_unit("l_per_m2")
    dialog.set_quantity_only("3")
    litres = dialog.wait_for_total("10,8 L", "TC-053-063: 3 l/m²")
    assert "Gesamtmenge für 3,6 m²: 10,8 L" in litres, litres
    dialog.set_quantity_only("0")
    dialog.submit_expecting_field_error(
        "quantity", "Eine Menge pro m² muss größer als 0 sein.", "TC-053-063: a dose of 0 per m²"
    )
    screenshot("053_063_02_zero_refused", "Dosis 0 pro m²: Feldmeldung, Dialog bleibt offen")
    assert not [
        e for e in care_events(base_url, e2e_seed_data, bed) if e.get("task_key") == task
    ], "TC-053-063: the refused dose wrote a care event"

    dialog.set_unit("g_per_m2")
    dialog.set_quantity_only("80")
    dialog.wait_for_total("288 g", "TC-053-063: back to 80 g/m²")
    dialog.submit_and_wait_closed("TC-053-063: completing with 80 g/m²")
    care_tab.wait_for_task_gone(task, "TC-053-063")

    events = [e for e in care_events(base_url, e2e_seed_data, bed) if e.get("task_key") == task]
    assert len(events) == 1, f"TC-053-063: one care event for the task, found {events}"
    event = events[0]
    assert (event["category"], event["quantity"], event["unit"]) == ("feeding", 80.0, "g_per_m2"), (
        event
    )
    assert (
        event["quantity_total"] == pytest.approx(288.0, abs=0.01)
        and event["quantity_total_unit"] == "g"
    ), event
    assert event["product_label"] == product, event

    bed_view.open(bed, "history")
    row = bed_view.wait_for_history_entry(product, "TC-053-063: the history row")
    assert "80 Gramm pro m²" in row, f"TC-053-063: the row names the dose: {row!r}"
    on_screen = history_tab.reveal_entries(1, "TC-053-063: the history")
    assert on_screen == 1, f"TC-053-063: the one history entry is on screen, {on_screen} are"
    screenshot("053_063_03_history", "Historie: Düngung mit 80 Gramm pro m²")

    bed_view.open(legacy, "care")
    care_tab.wait_for_task(f"Düngen ohne Fläche {tag}")
    legacy_dialog = care_tab.open_completion(legacy_task)
    hint = legacy_dialog.text_of("no-area-hint")
    assert hint.startswith("Das Beet hat keine Fläche."), f"TC-053-063: the no-area hint: {hint!r}"
    states = legacy_dialog.unit_options_disabled()
    assert states.get("g_per_m2") is True and states.get("l_per_m2") is True, (
        f"TC-053-063: a bed without area blocks the per-m² units: {states}"
    )
    assert states.get("g") is False, f"TC-053-063: a total unit stays available: {states}"
    screenshot("053_063_04_no_area", "Beet ohne Fläche: pro-m²-Einheiten gesperrt, Hinweis")


# ── TC-053-064 ──────────────────────────────────────────────────────────────

AMENDMENT_MATERIALS = [
    "Kompost",
    "Mist",
    "Hornspäne",
    "Gesteinsmehl",
    "Pflanzenkohle",
    "Sand",
    "Perlite",
    "Kaffeesatz",
    "Gründüngung",
    "Schwefel",
    "Kalk",
    "Holzasche",
    "Sonstiges",
]


def test_tc_053_064_amendment_mulch_and_liming_with_a_text_only_hint(
    bed_view: BedViewPage,
    care_tab: BedCareTab,
    history_tab: HistoryTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-064 — compost as soil amendment, bark mulch by the care log, liming with a text-only hint (GP-FR-124).

    Precondition (API): bed "Beet 1" (3,6 m²) with an open "Bodenverbesserung" and an open "Kalkung" task. The
    amendment dialog offers exactly the 13 amendment materials (Kompost … Sonstiges) and no liming hint for compost;
    3 "Liter" compost are stored. "Pflege protokollieren" stores a mulch layer of "Rindenmulch". The liming dialog
    shows the hint ending "Eine Kalkmenge berechnet die App nicht.", leaves the amount empty and offers Kalk,
    Holzasche, Sonstiges; Kalk with 150 g/m² is stored. Asserted on the server: three events (soil_amendment compost
    3 l, mulching bark_mulch, liming lime 150 g/m²), both tasks completed; in the history the three rows with their
    categories and materials. Breaks if a material list is wrong, if the liming dialog pre-fills an amount or shows
    no hint, or if a completion writes no event.
    """
    garden = _garden(base_url, e2e_seed_data, "tc064")
    bed = garden.bed_key(BED_1.name)
    tag = unique_tag()
    amendment = create_bed_task(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        name=f"Bodenverbesserung {tag}",
        category="soil_amendment",
    )
    liming = create_bed_task(
        base_url, e2e_seed_data, bed_key=bed, name=f"Kalkung {tag}", category="liming"
    )

    bed_view.open(bed, "care")
    care_tab.wait_for_task(f"Kalkung {tag}")
    dialog = care_tab.open_completion(amendment)
    offered = dialog.material_options()
    assert offered == AMENDMENT_MATERIALS, f"TC-053-064: the amendment materials: {offered}"
    dialog.choose_material("Kompost")
    assert not dialog.has_part("liming-hint"), "TC-053-064: compost carries no liming hint"
    dialog.set_quantity_only("3")
    dialog.set_unit("l")
    screenshot("053_064_01_compost", "Bodenverbesserung: Kompost, 3 Liter")
    dialog.submit_and_wait_closed("TC-053-064: compost")
    care_tab.wait_for_task_gone(amendment, "TC-053-064: amendment")

    log = care_tab.open_care_log()
    log.choose_category("mulching")
    log.choose_material("Rindenmulch")
    log.submit_and_wait_closed("TC-053-064: mulch by the care log")

    dialog = care_tab.open_completion(liming)
    hint = dialog.text_of("liming-hint")
    assert hint.startswith("Kalk und Holzasche heben den pH-Wert.") and hint.endswith(
        "Eine Kalkmenge berechnet die App nicht."
    ), f"TC-053-064: the liming hint: {hint!r}"
    assert not AMOUNT.search(hint), f"TC-053-064: the hint names no amount: {hint!r}"
    assert dialog.quantity_value() == "", (
        f"TC-053-064: no lime amount is pre-filled: {dialog.quantity_value()!r}"
    )
    liming_materials = dialog.material_options()
    assert liming_materials == ["Kalk", "Holzasche", "Sonstiges"], f"TC-053-064: {liming_materials}"
    dialog.choose_material("Kalk")
    dialog.set_quantity_only("150")
    screenshot("053_064_02_liming", "Kalkung: Hinweistext ohne Menge, Kalk 150 g/m²")
    dialog.submit_and_wait_closed("TC-053-064: liming")
    care_tab.wait_for_task_gone(liming, "TC-053-064: liming")

    stored = care_events(base_url, e2e_seed_data, bed)
    assert sorted(e["category"] for e in stored) == ["liming", "mulching", "soil_amendment"], (
        f"TC-053-064: exactly one event per action, three in total: {[e['category'] for e in stored]}"
    )
    events = {e["category"]: e for e in stored}
    assert (
        events["soil_amendment"]["material"],
        events["soil_amendment"]["quantity"],
        events["soil_amendment"]["unit"],
    ) == (
        "compost",
        3.0,
        "l",
    ), events["soil_amendment"]
    assert events["mulching"]["material"] == "bark_mulch", events["mulching"]
    assert (
        events["liming"]["material"],
        events["liming"]["quantity"],
        events["liming"]["unit"],
    ) == (
        "lime",
        150.0,
        "g_per_m2",
    ), events["liming"]
    for key in (amendment, liming):
        assert task_state(base_url, e2e_seed_data, key)["status"] == "completed", (
            f"TC-053-064: task {key} done"
        )

    bed_view.open(bed, "history")
    for category, material in (
        ("Bodenverbesserung", "Kompost"),
        ("Mulchen", "Rindenmulch"),
        ("Kalkung", "Kalk"),
    ):
        row = bed_view.wait_for_history_entry(material, f"TC-053-064: the {category} row")
        assert category in row, f"TC-053-064: the {material} row names {category}: {row!r}"
    on_screen = history_tab.reveal_entries(3, "TC-053-064: the history")
    assert on_screen >= 1, f"TC-053-064: no history entry is on screen ({on_screen})"
    screenshot("053_064_03_history", "Historie: Bodenverbesserung, Mulchen, Kalkung")


# ── TC-053-065 / TC-053-066 ─────────────────────────────────────────────────


@pytest.mark.smoke
def test_tc_053_065_shipped_nutrient_hint_shows_no_chip_and_no_amount(
    bed_view: BedViewPage,
    soil_tab: SoilTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-065 — the shipped nutrient hint: no chip, no salt chip, no number with an amount unit (GP-FR-125).

    Precondition (API): a 3,6 m² bed of natural soil ("Gewachsener Boden", loam, lab target pH 6,5) with one
    tomato (a heavy feeder in the seed catalogue), a pea last year, a feeding 120 days ago, a lab analysis with
    phosphorus class "D" by CAL and pH 5,2 CaCl₂. The arrangement is checked on the server: the summary's hint is
    ``insufficient_data`` with ``thresholds_without_source`` - the feeder gate was passed, only the sourced threshold
    is missing (a "demand_unknown" bed would prove nothing) - and carries the reason codes of the pea
    (``preceding_nitrogen_fixer``) and of class D (``p_or_k_class_high``); the soil analyses answer liming
    ``likely / below_target``. Asserted in the browser, after the head named "1 Pflanze": neither "Düngebedarf
    wahrscheinlich"/"Düngung prüfen" nor "Salzgehalt prüfen" is shown, the head names no number with a dose unit,
    and the soil tab shows the reasoned hint "Kalkung wahrscheinlich sinnvoll" (``data-status = likely``) that says
    the app names no amount and contains no number with an amount unit. Breaks if a chip appears without a sourced
    threshold, if the reasoned liming hint does not render, or if any surface prints an amount.
    """
    garden = _garden(base_url, e2e_seed_data, "tc065")
    bed = garden.bed_key(BED_1.name)
    tomato = species(base_url, e2e_seed_data, TOMATO)
    plants = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=tomato["key"],
        id_prefix="TCN",
        points=((0.5, 0.5),),
    )
    assert len(plants.plant_by_slot) == 1, "the arrangement must stand one tomato in the bed"
    # Natural soil with a known texture and a lab target pH: without them the liming line only says why it cannot
    # judge ("nur für gewachsenen Boden"), and the reasoned hint - the one that must carry no amount - never renders.
    # Written before the analysis: the analysis then writes its newer pH into this profile.
    patch_location(
        base_url,
        e2e_seed_data,
        bed,
        {
            "soil_profile": {
                "growing_medium_kind": "native_soil",
                "soil_texture": "loam",
                "target_ph": 6.5,
            }
        },
    )
    backfill_year(
        base_url,
        e2e_seed_data,
        bed,
        utc_today().year - 1,
        species_key=species(base_url, e2e_seed_data, PEA)["key"],
    )
    log_care_event(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        category="feeding",
        summary="Düngen (E2E)",
        days_ago=120,
        quantity=80.0,
        unit="g_per_m2",
    )
    record_soil_analysis(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        days_ago=10,
        measurements=[
            {
                "parameter": "p",
                "value": 30.0,
                "unit": "mg_per_100g",
                "source": "lab",
                "extraction_method": "cal",
                "content_class": "D",
            },
            {"parameter": "ph", "value": 5.2, "unit": "pH", "source": "lab", "ph_method": "cacl2"},
        ],
    )
    hint = bed_summary(base_url, e2e_seed_data, bed).get("nutrient_hint") or {}
    assert hint.get("state") == "insufficient_data" and "thresholds_without_source" in hint.get(
        "reasons", []
    ), (
        f"TC-053-065 arrangement: the shipped engine must stop at the missing sourced threshold: {hint}"
    )
    reasons = hint.get("reasons", [])
    assert "preceding_nitrogen_fixer" in reasons and "p_or_k_class_high" in reasons, (
        f"TC-053-065 arrangement: last year's pea and the class D must reach the hint as reason codes: {reasons}"
    )
    liming_server = soil_analyses(base_url, e2e_seed_data, bed)["liming_hint"]
    assert liming_server == {"status": "likely", "reason": "below_target"}, (
        f"TC-053-065 arrangement: pH 5,2 CaCl₂ under the target 6,5 on loam must make liming likely: {liming_server}"
    )

    bed_view.open(bed, "soil")
    bed_view.wait_for_header_plants("1 Pflanze", "TC-053-065: the head read the summary")
    assert bed_view.head_badges() == {"nutrient": False, "salt": False}, (
        f"TC-053-065: no nutrient and no salt chip without a sourced threshold: {bed_view.head_badges()}"
    )
    head = bed_view.header_text()
    assert not AMOUNT.search(head), (
        f"TC-053-065: the head names an amount: {AMOUNT.search(head)!r} in {head!r}"
    )
    status, liming = soil_tab.liming_hint()
    assert status == "likely" and liming.startswith("Kalkung wahrscheinlich sinnvoll"), (
        f"TC-053-065: the reasoned liming hint must render on natural soil: {status!r} {liming!r}"
    )
    assert "die App nennt keine Menge" in liming, (
        f"TC-053-065: the hint says it names no amount: {liming!r}"
    )
    assert not AMOUNT.search(liming), (
        f"TC-053-065: the liming hint names an amount: {AMOUNT.search(liming)!r} in {liming!r}"
    )
    screenshot(
        "053_065_01_head_without_chip", "Beetkopf ohne Nährstoff-Chip, Boden-Tab ohne Mengenangabe"
    )


def test_tc_053_066_nutrient_hint_with_an_activated_test_threshold() -> None:
    """TC-053-066 — counter-check with a sourced test threshold: skipped, the E2E stack cannot activate one (GP-FR-125).

    The thresholds are code constants: ``DEFAULT_CONFIG`` in ``app/domain/engines/nutrient_hint_engine.py`` has no
    active threshold, and ``app/common/dependencies.py`` builds ``NutrientHintService`` without a config. No
    environment variable, setting or route sets one, so no state the running E2E stack can reach shows the chip.
    """
    pytest.skip(
        "TC-053-066: the nutrient thresholds are code constants (DEFAULT_CONFIG in "
        "app/domain/engines/nutrient_hint_engine.py; NutrientHintService is built without a config in "
        "app/common/dependencies.py) - no env var, setting or route lets the E2E stack activate a sourced test "
        "threshold, so the chip cannot be produced in the browser"
    )


# ── TC-053-067 ──────────────────────────────────────────────────────────────


def test_tc_053_067_history_csv_is_bom_utf8_formula_safe_and_names_the_performer(
    bed_view: BedViewPage,
    history_tab: HistoryTab,
    care_history: CareHistoryPage,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-067 — "CSV exportieren" of the bed history and of "Historie aller Beete" (GP-FR-104, SR-016).

    Precondition (API): "Beet 1" with two watering lines whose texts start with "=" and "@" and one feeding line;
    "Beet 2" with one watering line - every text carries a per-test tag. The bed history filtered to "Gießen" lists
    two rows; its "CSV (Komma)" file is read from the blob the page saves. Asserted: a ``care-events-*.csv`` name,
    the bytes ``EF BB BF`` first, the 23 documented columns, exactly the two watering lines of "Beet 1" (no feeding
    line, nothing of "Beet 2"), their texts prefixed with ``'`` (``'=1+1 …``, ``'@Hinweis …``), and ``performed_by``
    equal to the display name the JSON list names (never empty). The file of the tenant-wide page also holds the
    line of "Beet 2". Breaks if the BOM or the prefix is missing, if the filter does not reach the file, if the
    performer column carries something other than the display name, or if the tenant file misses a bed.

    Spec deviation: the display name is the acting account's own (light: the system user, full: the demo user).
    """
    garden = _garden(base_url, e2e_seed_data, "tc067", BED_1, BED_2)
    bed_1, bed_2 = garden.bed_key(BED_1.name), garden.bed_key(BED_2.name)
    tag = unique_tag()
    formula, at_sign = f"=1+1 {tag}", f"@Hinweis {tag}"
    for summary in (formula, at_sign):
        log_care_event(base_url, e2e_seed_data, bed_key=bed_1, category="watering", summary=summary)
    log_care_event(
        base_url, e2e_seed_data, bed_key=bed_1, category="feeding", summary=f"Düngen {tag}"
    )
    other = f"Beet 2 gegossen {tag}"
    log_care_event(base_url, e2e_seed_data, bed_key=bed_2, category="watering", summary=other)
    performers = {
        e["key"]: e.get("performed_by")
        for e in care_events(base_url, e2e_seed_data, bed_1, category="watering")
    }

    bed_view.open(bed_1, "history")
    history_tab.wait_for_shown(3, "TC-053-067: all lines of Beet 1")
    history_tab.filter_category("watering")
    on_screen = history_tab.reveal_entries(2, "TC-053-067: filtered to Gießen")
    assert on_screen >= 1, f"TC-053-067: no history entry is on screen ({on_screen})"
    screenshot("053_067_01_filtered", "Historie Beet 1, Kategorie Gießen: zwei Einträge")
    saved = history_tab.export_csv_comma("TC-053-067: bed CSV")
    assert re.fullmatch(r"care-events-\d{8}\.csv", saved["name"]), (
        f"TC-053-067: file name {saved['name']!r}"
    )
    assert saved["head"] == [0xEF, 0xBB, 0xBF], (
        f"TC-053-067: UTF-8 BOM expected, got {saved['head']}"
    )
    header, rows = _parse_csv(saved, "TC-053-067: bed CSV")
    assert header == CSV_COLUMNS, f"TC-053-067: the columns: {header}"
    assert len(rows) == 2, f"TC-053-067: only the two watering lines of Beet 1: {rows}"
    assert {row["location_key"] for row in rows} == {bed_1}, rows
    assert {row["category"] for row in rows} == {"watering"}, rows
    assert {row["summary"] for row in rows} == {f"'{formula}", f"'{at_sign}"}, (
        f"TC-053-067: formula-looking texts are prefixed with ': {[row['summary'] for row in rows]}"
    )
    for row in rows:
        expected = performers.get(row["key"])
        assert expected and row["performed_by"] == expected, (
            f"TC-053-067: performed_by names the display name {expected!r}, the file says {row['performed_by']!r}"
        )

    care_history.open()
    screenshot("053_067_02_all_beds", "Historie aller Beete")
    whole = care_history.export_csv_comma("TC-053-067: tenant CSV")
    assert whole["head"] == [0xEF, 0xBB, 0xBF], f"TC-053-067: tenant file BOM, got {whole['head']}"
    _header, all_rows = _parse_csv(whole, "TC-053-067: tenant CSV")
    mine = {(row["location_key"], row["summary"]) for row in all_rows if tag in row["summary"]}
    assert (bed_2, other) in mine and (bed_1, f"'{formula}") in mine, (
        f"TC-053-067: the tenant file holds the lines of both beds: {sorted(mine)}"
    )


# ── TC-053-068 ──────────────────────────────────────────────────────────────


def test_tc_053_068_rotation_matrix_lists_beds_by_year_and_backfills_from_a_cell(
    matrix: RotationMatrixPage,
    bed_view: BedViewPage,
    history_tab: HistoryTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-068 — the rotation matrix of a site, a backfill from an empty past cell, the jump to a bed (GP-FR-135).

    Precondition (API): a site with "Beet 1" (last year lettuce in spring as pre-crop and tomato in the main
    season, this year a pea standing in the bed), "Beet 2" (cabbage last year) and "Beet 3" taken out of the
    rotation (``rotation_exempt``). Asserted against the server's matrix: the column years; the cell "Beet 1"/last
    year lists both entries in the server's order, spring before main season, each with its season label
    ("Frühjahr", "Hauptsaison"); the current-year cell of "Beet 1" shows the pea's family; the families of tomato
    and cabbage differ by fill pattern and code (not colour only); the "Fruchtfolge aus" mark on "Beet 3" and none
    on "Beet 1". Tapping the empty cell "Beet 2"/two years ago opens "Was stand hier <Jahr>?"; with
    Cucurbitaceae saved, the cell shows that family, the server's rotation of "Beet 2" holds it for that year, and
    the history timeline of "Beet 2" shows it too. The bed link opens the bed view of "Beet 1". Breaks if the matrix
    misreads the server, if the backfill writes nothing or somewhere else, or if matrix and history disagree.

    Spec deviations: relative years (last year = "2025", this year = "2026" of the TC); the product has no
    "Vorkultur" role - a pre-crop is a second main-crop entry of the same year dated to spring (``season =
    spring``), the cell tells the two apart by their season label; Feldsalat is not in the seed catalogue, lettuce
    (Lactuca sativa) stands in for it; the pea of this year is a real planting (a backfill only takes past years).
    Not automated: the planned 2027 cell, greyscale and the phone view.
    """
    garden = _garden(base_url, e2e_seed_data, "tc068", BED_1, BED_2, BED_3)
    bed_1, bed_2, bed_3 = (garden.bed_key(spec.name) for spec in (BED_1, BED_2, BED_3))
    year = utc_today().year
    backfill_year(
        base_url,
        e2e_seed_data,
        bed_1,
        year - 1,
        species_key=species(base_url, e2e_seed_data, LETTUCE)["key"],
        season="spring",
    )
    backfill_year(
        base_url,
        e2e_seed_data,
        bed_1,
        year - 1,
        species_key=species(base_url, e2e_seed_data, TOMATO)["key"],
        season="main",
    )
    peas = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed_1,
        species_key=species(base_url, e2e_seed_data, PEA)["key"],
        id_prefix="TCP",
        points=((0.5, 0.5),),
    )
    assert len(peas.plant_by_slot) == 1, "the arrangement must stand one pea in Beet 1 this year"
    backfill_year(
        base_url,
        e2e_seed_data,
        bed_2,
        year - 1,
        species_key=species(base_url, e2e_seed_data, CABBAGE)["key"],
    )
    patch_location(base_url, e2e_seed_data, bed_3, {"rotation_exempt": True})
    cucurbits = botanical_family_key(base_url, e2e_seed_data, "Cucurbitaceae")
    target = year - 2

    server = rotation_matrix(base_url, e2e_seed_data, garden.site_key)
    cells = {
        (row["location_key"], cell["year"]): [
            p.get("family_key") for p in cell["plantings"] if p.get("family_key")
        ]
        for row in server["beds"]
        for cell in row["cells"]
    }
    assert target in server["columns"], f"the matrix must show {target}: {server['columns']}"
    assert cells[(bed_2, target)] == [], (
        f"the arrangement needs an empty {target} cell: {cells[(bed_2, target)]}"
    )
    seasons = {
        (row["location_key"], cell["year"]): [p.get("season") for p in cell["plantings"]]
        for row in server["beds"]
        for cell in row["cells"]
    }
    # The order inside a cell is the server's (the spec names no order; the matrix lists main before spring
    # today - reported in #2764); the browser must show exactly that order.
    pair_seasons = seasons[(bed_1, year - 1)]
    assert sorted(pair_seasons) == ["main", "spring"], (
        f"the arrangement needs a pre-crop and a main crop in Beet 1/{year - 1}: {pair_seasons}"
    )
    pair_families = cells[(bed_1, year - 1)]
    assert len(pair_families) == 2 and len(set(pair_families)) == 2, (
        f"pre-crop and main crop must carry two families: {pair_families}"
    )
    tomato_family = pair_families[pair_seasons.index("main")]
    pea_families = cells[(bed_1, year)]
    assert pea_families, f"the arrangement needs the pea in Beet 1/{year}: {cells[(bed_1, year)]}"
    cabbage_families = cells[(bed_2, year - 1)]
    assert cabbage_families and cabbage_families[0] != tomato_family, (
        f"the arrangement needs two different main-crop families in {year - 1}: {cells}"
    )

    matrix.open(garden.site_key)
    assert matrix.column_years() == server["columns"], (
        f"TC-053-068: columns {matrix.column_years()}"
    )
    assert matrix.cell_families(bed_1, year - 1) == pair_families, (
        f"TC-053-068: Beet 1/{year - 1} lists pre-crop and main crop in the server's order: "
        f"{matrix.cell_families(bed_1, year - 1)} ({matrix.cell_text(bed_1, year - 1)!r})"
    )
    pair_text = matrix.cell_text(bed_1, year - 1)
    labels = {"spring": "Frühjahr", "main": "Hauptsaison"}
    assert all(labels[season] in pair_text for season in pair_seasons) and (
        pair_text.index(labels[pair_seasons[0]]) < pair_text.index(labels[pair_seasons[1]])
    ), (
        f"TC-053-068: the cell names both seasons in the server's order {pair_seasons}: {pair_text!r}"
    )
    assert matrix.cell_families(bed_1, year) == pea_families, (
        f"TC-053-068: Beet 1/{year} shows this year's pea: {matrix.cell_text(bed_1, year)!r}"
    )
    # Colour must not be the only carrier (greyscale, GP-FR-135): ``familyMarks`` gives each family of the page
    # its own entry of FAMILY_PATTERNS - index 0 is the plain fill ``none`` by design - and a code. So the claim is
    # "two families differ by pattern and by code", not "every swatch is patterned".
    tomato_pattern = matrix.swatch_pattern(bed_1, year - 1, tomato_family)
    cabbage_pattern = matrix.swatch_pattern(bed_2, year - 1, cabbage_families[0])
    assert tomato_pattern != cabbage_pattern, (
        f"TC-053-068: two families must differ by fill pattern, not only colour: {tomato_pattern!r} vs "
        f"{cabbage_pattern!r}"
    )
    pea_cell, cabbage_cell = matrix.cell_text(bed_1, year), matrix.cell_text(bed_2, year - 1)
    assert pea_cell and cabbage_cell and pea_cell != cabbage_cell, (
        f"TC-053-068: each single-family cell names its own code: {pea_cell!r} vs {cabbage_cell!r}"
    )
    off = matrix.off_mark(bed_3)
    assert off is not None and "Fruchtfolge" in off, (
        f"TC-053-068: Beet 3 is marked as out of the rotation: {off!r}"
    )
    assert matrix.off_mark(bed_1) is None, "TC-053-068: Beet 1 takes part in the rotation"
    assert matrix.legend_text(), "TC-053-068: the matrix shows its family legend"
    screenshot(
        "053_068_01_matrix", "Fruchtfolge-Matrix: Beete x Jahre, Familien mit Kürzel und Muster"
    )

    dialog = matrix.open_backfill(bed_2, target)
    assert dialog.title() == f"Was stand hier {target}?", dialog.title()
    dialog.choose_family(cucurbits)
    dialog.submit_and_wait_closed("TC-053-068: backfill from the cell")
    matrix.wait_for_cell_family(bed_2, target, cucurbits, "TC-053-068: the backfilled cell")
    screenshot("053_068_02_backfilled", f"Zelle Beet 2 / {target}: Kürbisgewächse nacherfasst")
    stored = [
        p.get("family_key") for p in rotation_years(base_url, e2e_seed_data, bed_2).get(target, [])
    ]
    assert cucurbits in stored, f"TC-053-068: the rotation of Beet 2 holds {target}: {stored}"

    bed_view.open(bed_2, "history")
    history_tab.wait_for_timeline_family(target, cucurbits, "TC-053-068: the history of Beet 2")

    matrix.open(garden.site_key)
    matrix.jump_to_bed(bed_1)
    screenshot("053_068_03_jump", "Sprung aus der Matrix in die Beetansicht von Beet 1")


# ── TC-053-069 ──────────────────────────────────────────────────────────────


def test_tc_053_069_follow_up_crop_after_a_heavy_feeder_and_the_rotation_switch(
    bed_view: BedViewPage,
    history_tab: HistoryTab,
    soil_tab: SoilTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-069 — "Folgekultur-Empfehlung" after a tomato; no history; "Dauerkultur" on top of "Eingeschaltet" (GP-FR-133).

    Precondition (API): "Beet 1" with tomato last year, "Beet 2" without history. The server's recommendation for
    "Beet 1" is read first (``ok``, previous heavy feeder, target medium feeder, every listed species with a stored
    feeder level). Asserted in the browser: the panel says "Nach <Vorjahr> (Starkzehrer) passt als Nächstes:
    Mittelzehrer." and lists exactly the server's families, without any amount; "Beet 2" says "Es ist noch kein Jahr
    erfasst. …" and lists none. On the soil tab "Fruchtfolge-Prüfung" set to "Eingeschaltet" is saved; switching
    "Dauerkultur" on top is refused ("… Es wurde nichts geändert.") and the switch stays off; the server holds
    ``rotation_enabled true / rotation_exempt false`` and a reload shows the same. Breaks if the panel shows another
    step or invents a species, if an empty bed gets a recommendation, or if the contradictory pair is stored.
    """
    garden = _garden(base_url, e2e_seed_data, "tc069", BED_1, BED_2)
    bed_1, bed_2 = garden.bed_key(BED_1.name), garden.bed_key(BED_2.name)
    previous = utc_today().year - 1
    backfill_year(
        base_url,
        e2e_seed_data,
        bed_1,
        previous,
        species_key=species(base_url, e2e_seed_data, TOMATO)["key"],
    )
    recommendation = succession_recommendation(base_url, e2e_seed_data, bed_1)
    assert recommendation["status"] == "ok" and (recommendation["previous"] or {}).get(
        "nutrient_demand"
    ) == ("heavy_feeder"), f"the arrangement needs a heavy feeder last year: {recommendation}"
    assert recommendation["target"] == "medium_feeder", recommendation
    listed = [s for family in recommendation["families"] for s in family["species"]]
    assert listed and all(s.get("nutrient_demand") for s in listed), (
        f"TC-053-069: every recommended species has a stored feeder level: {listed}"
    )

    bed_view.open(bed_1, "history")
    shown = history_tab.wait_for_succession("TC-053-069: Beet 1")
    assert shown["basis"] == f"Nach {previous} (Starkzehrer) passt als Nächstes: Mittelzehrer.", (
        shown
    )
    assert shown["families"] == [family["family_key"] for family in recommendation["families"]], (
        shown
    )
    assert not AMOUNT.search(str(shown["text"])), (
        f"TC-053-069: the panel names an amount: {shown['text']!r}"
    )
    screenshot("053_069_01_recommendation", "Folgekultur-Empfehlung nach Starkzehrer: Mittelzehrer")

    bed_view.open(bed_2, "history")
    empty = history_tab.wait_for_succession("TC-053-069: Beet 2")
    assert empty["families"] == [] and (empty["status"] or "").startswith(
        "Es ist noch kein Jahr erfasst."
    ), empty

    bed_view.open(bed_1, "soil")
    assert soil_tab.rotation_check() == "default", (
        "the arrangement starts at the bed type's default"
    )
    soil_tab.set_rotation_check("on", "TC-053-069: Fruchtfolge-Prüfung eingeschaltet")
    refusal = soil_tab.toggle_exempt_expecting_refusal("TC-053-069: Dauerkultur on top")
    assert refusal.endswith("Es wurde nichts geändert."), f"TC-053-069: the refusal: {refusal!r}"
    assert not soil_tab.exempt_on(), "TC-053-069: the refused switch falls back to off"
    screenshot("053_069_02_refused", "Fruchtfolge-Schalter: Dauerkultur zusätzlich abgelehnt")
    summary = bed_summary(base_url, e2e_seed_data, bed_1)
    assert (summary.get("rotation_enabled"), summary.get("rotation_exempt")) == (True, False), (
        f"TC-053-069: only the valid switch is stored: {summary.get('rotation_enabled')}, "
        f"{summary.get('rotation_exempt')}"
    )
    bed_view.open(bed_1, "soil")
    assert (soil_tab.rotation_check(), soil_tab.exempt_on()) == ("on", False), (
        "TC-053-069: the reload shows the last valid state"
    )


# ── TC-053-070 / TC-053-071 ─────────────────────────────────────────────────


def _suggested_task(
    base_url: str, seed: dict, app_mode: str, bed: str, category: str, name: str, reason: str
) -> str:
    """An open bed task turned into a system suggestion; read back through the API (see ``mark_task_suggested``)."""
    key = create_bed_task(base_url, seed, bed_key=bed, name=name, category=category)
    mark_task_suggested(app_mode, key, reason)
    state = task_state(base_url, seed, key)
    assert (state.get("suggested"), state.get("suggestion_reason")) == (True, reason), (
        f"the suggestion flag did not reach the application: {state}"
    )
    return key


def test_tc_053_070_accepting_a_suggestion_makes_it_an_ordinary_open_task(
    bed_view: BedViewPage,
    care_tab: BedCareTab,
    base_url: str,
    e2e_seed_data: dict,
    app_mode: str,
    screenshot,
) -> None:
    """TC-053-070 — accept a seeded suggestion: an ordinary open task, no care entry (GP-FR-086, GP-API-040).

    Precondition: "Beet 1" with an open watering task marked as a suggestion with the reason "ET0-Bedarf 4,2 L/m²
    seit 3 Tagen" (task through ``POST /tasks``, flag in the database - no producer exists), "Beet 2" with an
    ordinary open task. "Beet 2"'s care tab, settled on that task, has no "Vorschläge" section; "Beet 1" lists the
    suggestion under "Vorschläge (1)" with "Grund: …" and both decisions. "Annehmen" moves it to "Offen". Asserted on
    the server: ``suggested false``, the status unchanged, no care event; after a reload the task is still open and
    the section is gone. Breaks if the section shows without a suggestion, if accepting completes or drops the task,
    or if it writes a care entry.
    """
    garden = _garden(base_url, e2e_seed_data, "tc070", BED_1, BED_2)
    bed_1, bed_2 = garden.bed_key(BED_1.name), garden.bed_key(BED_2.name)
    tag = unique_tag()
    reason = "ET0-Bedarf 4,2 L/m² seit 3 Tagen"
    task = _suggested_task(
        base_url, e2e_seed_data, app_mode, bed_1, "watering", f"Gießen {tag}", reason
    )
    status_before = task_state(base_url, e2e_seed_data, task)["status"]
    create_bed_task(base_url, e2e_seed_data, bed_key=bed_2, name=f"Jäten {tag}", category="weeding")

    bed_view.open(bed_2, "care")
    care_tab.wait_for_task(f"Jäten {tag}")
    assert not care_tab.has_suggestions_section(), (
        "TC-053-070: Beet 2 has no suggestion, so no section"
    )

    bed_view.open(bed_1, "care")
    section = care_tab.wait_for_suggestion(task, "TC-053-070: Beet 1")
    assert section.startswith("Vorschläge (1)"), f"TC-053-070: the section heading: {section!r}"
    assert care_tab.suggestion_reason(task) == f"Grund: {reason}"
    assert care_tab.suggestion_has_decisions(task) == (True, True), (
        "TC-053-070: Annehmen and Verwerfen"
    )
    screenshot("053_070_01_suggestion", "Pflege-Tab: Abschnitt Vorschläge mit Grund")
    care_tab.accept_suggestion(task, "TC-053-070: Annehmen")
    screenshot("053_070_02_accepted", "Angenommen: Aufgabe steht unter Offen")

    state = task_state(base_url, e2e_seed_data, task)
    assert (state["suggested"], state["status"]) == (False, status_before), f"TC-053-070: {state}"
    assert not [
        e for e in care_events(base_url, e2e_seed_data, bed_1) if e.get("task_key") == task
    ], "TC-053-070: accepting writes no care entry"
    bed_view.open(bed_1, "care")
    care_tab.wait_for_task(f"Gießen {tag}")
    assert task in care_tab.open_task_keys() and not care_tab.has_suggestions_section(), (
        f"TC-053-070: after the reload the task is open and no suggestion is left: {care_tab.open_task_keys()}"
    )


def test_tc_053_071_dismissing_a_suggestion_closes_it_without_a_care_entry(
    bed_view: BedViewPage,
    care_tab: BedCareTab,
    base_url: str,
    e2e_seed_data: dict,
    app_mode: str,
    screenshot,
) -> None:
    """TC-053-071 — dismiss one of two seeded suggestions: closed as skipped, no care entry, the other stays (GP-FR-086).

    Precondition: "Beet 1" with two suggestions, "Gießen" and "Düngen", each with a reason (tasks through the API,
    flag in the database). "Verwerfen" on "Düngen": it leaves "Vorschläge" and does not appear under "Offen";
    "Gießen" stays a suggestion. Asserted on the server: "Düngen" is ``skipped`` (still ``suggested``, never
    accepted), "Gießen" untouched, no care event for either. Breaks if dismissing completes the task, writes a care
    entry, turns it into an open task or touches the other suggestion.

    Not automated: the viewer half (no account with the role "Betrachter" in the E2E stack) and the "abgebrochene
    Aufgaben" filter (the care tab has none; the status is read from the server).
    """
    garden = _garden(base_url, e2e_seed_data, "tc071")
    bed = garden.bed_key(BED_1.name)
    tag = unique_tag()
    keep = _suggested_task(
        base_url,
        e2e_seed_data,
        app_mode,
        bed,
        "watering",
        f"Gießen {tag}",
        "Trockenheit seit 5 Tagen",
    )
    drop = _suggested_task(
        base_url,
        e2e_seed_data,
        app_mode,
        bed,
        "feeding",
        f"Düngen {tag}",
        "Letzte Düngung lange her",
    )

    bed_view.open(bed, "care")
    care_tab.wait_for_suggestion(keep, "TC-053-071")
    care_tab.wait_for_suggestion(drop, "TC-053-071")
    screenshot("053_071_01_two_suggestions", "Zwei Vorschläge: Gießen und Düngen")
    care_tab.dismiss_suggestion(drop, "TC-053-071: Verwerfen")
    # Settle on the server's state before the negative checks: a fresh document load renders the task list from the
    # server alone, and the kept suggestion being listed proves the list arrived - a dismissed task that came back
    # with the refetch would be listed by then, so its absence below is falsifiable.
    bed_view.open(bed, "care")
    care_tab.wait_for_suggestion(keep, "TC-053-071: after the reload")
    assert drop not in care_tab.suggestion_keys(), "TC-053-071: the dismissed suggestion stays gone"
    assert drop not in care_tab.open_task_keys(), (
        "TC-053-071: a dismissed suggestion is no open task"
    )
    screenshot("053_071_02_dismissed", "Verworfen: nur Gießen bleibt als Vorschlag")

    dropped, kept = (
        task_state(base_url, e2e_seed_data, drop),
        task_state(base_url, e2e_seed_data, keep),
    )
    assert (dropped["status"], dropped["suggested"]) == ("skipped", True), f"TC-053-071: {dropped}"
    assert kept["suggested"] is True and kept["status"] not in ("skipped", "completed"), (
        f"TC-053-071: {kept}"
    )
    assert not [
        e for e in care_events(base_url, e2e_seed_data, bed) if e.get("task_key") in (drop, keep)
    ], "TC-053-071: dismissing writes no care entry"
