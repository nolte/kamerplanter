"""E2E of REQ-053 wave 4 - care tasks on a bed and its history (WP 4.6, issue #2424; spec pin REQ-053 v1.6).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-053.md, GP-ACC from the coverage matrix):
  TC-053-020  ->  create a feeding task on the bed, complete it with product and amount,   (GP-ACC-024)
                  the history shows the line
                  partial: see the test's docstring
  TC-053-022  ->  correct a care event: the original stays, the correction supersedes it,   (GP-ACC-026)
                  PATCH is refused (supersede via the API)
  TC-053-023  ->  60 care events: category filter, 50 per page, newest first, the           (GP-ACC-027)
                  planting timeline per year
                  partial: see the test's docstring
  TC-053-028  ->  the lead redacts an entry: its whole supersede chain shows "[redacted]"   (GP-ACC-044)
                  (redact via the API)

Not automated here, on purpose (no skip, no xfail - there is nothing to run):
  TC-053-021  not part of wave 4 E2E (GP-ACC-025 is #2424's neighbour in the matrix, not in its acceptance);
              the 5-minute / 365-day window is pinned by the backend API tests of V-11.

Preconditions are self-provisioned through the application's own API, one fresh site per test with a
UUID-derived name (`_garden_plan_helpers.py`): no test reads or mutates a bed another test or xdist worker
touches. Species come from the seed catalogue (`species.yaml`), never created. All cases are desktop cases
(TC-REQ-053 "Gerät: Desktop") and carry ``requires_desktop``.

Waits are anchored on state - a row in the care list, a closed dialog, the history live region's count, the
timeline chip - never on time, and there is no retry loop.
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._garden_plan_helpers import (
    BedSpec,
    bed_rect,
    backfill_last_year,
    care_events,
    create_bed_task,
    log_care_event,
    plant_on_positions,
    provision_garden,
    redact_care_event,
    species,
    supersede_care_event,
    task_state,
    tenant_get,
    tenant_request,
    unique_tag,
    utc_today,
)
from .pages.bed_care_page import BedCareTab, HistoryTab
from .pages.bed_view_page import BedViewPage

pytestmark = pytest.mark.requires_desktop

BED_NAME = "Beet 1"
TOMATO = "Solanum lycopersicum"
CABBAGE = "Brassica oleracea var. capitata"

#: ``GET /care-events`` and the bed history page by 50 (GP-FR-102, GP-ACC-027).
PAGE_SIZE = 50


@pytest.fixture
def bed_view(browser: WebDriver, base_url: str) -> BedViewPage:
    return BedViewPage(browser, base_url)


@pytest.fixture
def care_tab(browser: WebDriver, base_url: str) -> BedCareTab:
    return BedCareTab(browser, base_url)


@pytest.fixture
def history_tab(browser: WebDriver, base_url: str) -> HistoryTab:
    return HistoryTab(browser, base_url)


def _one_bed(base_url: str, seed: dict, purpose: str, width: float = 2.0, length: float = 1.0):
    garden = provision_garden(
        base_url, seed, purpose=purpose, beds=(BedSpec(BED_NAME, bed_rect(width, length)),)
    )
    return garden, garden.bed_key(BED_NAME)


def _bed_area_m2(base_url: str, seed: dict, bed_key: str) -> float:
    location = tenant_get(base_url, seed, f"/locations/{bed_key}")
    assert isinstance(location, dict)
    return float(location["area_m2"])


# ── TC-053-020 ──────────────────────────────────────────────────────────────


@pytest.mark.smoke
def test_tc_053_020_feeding_task_completed_with_product_and_amount_shows_in_the_history(
    bed_view: BedViewPage,
    care_tab: BedCareTab,
    history_tab: HistoryTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-020 — create a feeding task on the bed, complete it with product and 2 l/m²: one care event (GP-ACC-024).

    Precondition (API): a 2,0 x 1,0 m bed (2,0 m²) with two tomatoes. The task is created through the care tab's
    own "Neue Aufgabe" dialog (category Düngung, whole bed), completed through its "Erledigen" dialog with a
    free-text product, 2 and "Liter pro m²". The line is read back twice: from the server (exactly one care
    event with ``trigger = task`` and this ``task_key``, ``category = feeding``, ``quantity_total = 2 x area``,
    the task ``completed``) and from the history tab (the row names product, amount and category, and the task
    left the open list). Breaks if the completion writes no line or two, if the area dose is not totalled over
    the bed, if the task stays open, or if the history does not show the line.

    Spec deviations, not asserted: step 2 says the user "wählt beide Pflanzen" - the completion dialog has no
    plant selector (the plants are an API field of ``POST /tasks/{key}/complete``); the failing-save branch
    ("Fehler z. B. simuliert") needs an injected server fault and is pinned by the backend integration test of
    the atomic completion (GP-ACC-024 second half).
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc020")
    plants = plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=tomato["key"],
        id_prefix="TCA",
        points=((0.5, 0.5), (1.5, 0.5)),
    )
    assert len(plants.plant_by_slot) == 2, "the arrangement must stand two plants in the bed"
    area = _bed_area_m2(base_url, e2e_seed_data, bed)
    assert area == pytest.approx(2.0, abs=0.01), f"the bed must measure 2,0 m², it measures {area}"

    tag = unique_tag()
    task_name = f"Düngen {tag}"
    product = f"Komposttee {tag}"
    bed_view.open(bed, "care")
    task_key = care_tab.create_task("feeding", task_name)
    screenshot(
        "053_020_01_task_created", "Pflege-Tab: die neue Düngeaufgabe steht offen in der Liste"
    )

    dialog = care_tab.open_completion(task_key)
    dialog.set_product(product)
    dialog.set_quantity("2", "l_per_m2")
    screenshot("053_020_02_completion_form", "Erledigen-Dialog: Produkt, 2 Liter pro m²")
    dialog.submit_and_wait_closed("TC-053-020: completing the feeding task")
    care_tab.wait_for_task_gone(task_key, "TC-053-020")

    events = [e for e in care_events(base_url, e2e_seed_data, bed) if e.get("task_key") == task_key]
    assert len(events) == 1, (
        f"TC-053-020: completing the task must write exactly one care event, found {events}"
    )
    event = events[0]
    assert (event["category"], event["trigger"]) == ("feeding", "task"), event
    assert (event["quantity"], event["unit"]) == (2.0, "l_per_m2"), event
    assert event["quantity_total"] == pytest.approx(2.0 * area, abs=0.01), (
        f"TC-053-020: 2 l/m² on {area} m² is {2.0 * area} l in total, the event totals {event}"
    )
    assert event["product_label"] == product, event
    assert task_state(base_url, e2e_seed_data, task_key)["status"] == "completed"

    bed_view.open(bed, "history")
    entry = bed_view.wait_for_history_entry(product, "TC-053-020: the history row")
    assert "Düngung" in entry, f"TC-053-020: the row names the category: {entry!r}"
    assert "2 Liter pro m²" in entry, f"TC-053-020: the row names the amount: {entry!r}"
    screenshot("053_020_03_history", "Historie: Eintrag Düngung mit Produkt und Menge")


# ── TC-053-022 ──────────────────────────────────────────────────────────────


def test_tc_053_022_a_corrected_care_event_keeps_the_original_and_refuses_an_overwrite(
    bed_view: BedViewPage,
    history_tab: HistoryTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-022 — correct a care event by superseding it: the original stays, PATCH is refused (GP-ACC-026).

    Precondition (API): a bed with one feeding event, 2 l/m². The history tab has no edit control on a row;
    the correction is the API's ``POST /care-events/{key}/supersede`` with 3 l/m² (the issue names it
    "supersede via API"). Asserted on the server: the new event ``supersedes_key`` the first, the first
    ``superseded_by_key`` the new one, the default list answers only the correction, ``include_superseded``
    both, and ``PATCH`` on the original is refused (405 or 422). Asserted in the browser: the history row
    carries no action, shows by default only the corrected 3 l/m², and with "Korrekturen anzeigen" both, the
    original marked "Korrigiert". Breaks if a correction overwrites the original, if the default list still
    shows the replaced line, or if the switch does not reveal it.

    Spec deviation, not asserted: step 2 says the user "wählt Korrigieren" - there is no such button in the
    history list (``HistoryList`` is read-only by design; the supersede is an API operation in this release).
    """
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc022")
    original = log_care_event(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        category="feeding",
        summary="Düngen",
        quantity=2.0,
        unit="l_per_m2",
        product_label="Komposttee",
    )
    corrected = supersede_care_event(
        base_url,
        e2e_seed_data,
        original["key"],
        {
            "category": "feeding",
            "summary": "Düngen",
            "performed_at": original["performed_at"],
            "quantity": 3.0,
            "unit": "l_per_m2",
            "product_label": "Komposttee",
        },
    )

    assert corrected["supersedes_key"] == original["key"], corrected
    stored_original = tenant_get(base_url, e2e_seed_data, f"/care-events/{original['key']}")
    assert isinstance(stored_original, dict)
    assert stored_original["superseded_by_key"] == corrected["key"], stored_original
    assert stored_original["quantity"] == 2.0, "the original must keep its amount"
    default = [e["key"] for e in care_events(base_url, e2e_seed_data, bed)]
    assert default == [corrected["key"]], (
        f"TC-053-022: the default list answers the correction only: {default}"
    )
    both = {e["key"] for e in care_events(base_url, e2e_seed_data, bed, include_superseded=True)}
    assert both == {original["key"], corrected["key"]}, both
    status, body = tenant_request(
        base_url, e2e_seed_data, "PATCH", f"/care-events/{original['key']}", {"quantity": 9.0}
    )
    assert status in (405, 422), (
        f"TC-053-022: PATCH on a care event must be refused, got {status} {body}"
    )

    bed_view.open(bed, "history")
    history_tab.wait_for_shown(1, "TC-053-022: the default history")
    assert not history_tab.item_has_button(), (
        "TC-053-022: a history row must offer no edit or delete action"
    )
    (row,) = history_tab.item_texts()
    assert "3 Liter pro m²" in row and "2 Liter pro m²" not in row, (
        f"TC-053-022: the default view shows only the corrected amount: {row!r}"
    )
    screenshot("053_022_01_default", "Historie: nur der korrigierte Eintrag, 3 Liter pro m²")

    bed_view.show_corrections()
    history_tab.wait_for_shown(2, "TC-053-022: with the corrections switch")
    rows = history_tab.item_texts()
    replaced = [text for text in rows if "2 Liter pro m²" in text]
    assert len(replaced) == 1 and "Korrigiert" in replaced[0], (
        f"TC-053-022: the replaced entry is listed and marked 'Korrigiert': {rows}"
    )
    assert any("3 Liter pro m²" in text and "Korrektur" in text for text in rows), rows
    screenshot(
        "053_022_02_with_corrections",
        "Historie mit Korrekturen: Original als „Korrigiert“ markiert",
    )


# ── TC-053-023 ──────────────────────────────────────────────────────────────


def test_tc_053_023_history_filters_by_category_pages_by_fifty_and_shows_the_timeline(
    bed_view: BedViewPage,
    history_tab: HistoryTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-023 — 60 care events: filter "Gießen", 50 per page newest first, the planting timeline (GP-ACC-027).

    Precondition (API): a bed with 55 watering and 5 feeding events spread over the last 352 days, two tomatoes
    standing in it this year and a cabbage recorded for last year. The history is opened, filtered to
    "Gießen": 50 rows (the live region says so), newest first, "Mehr laden" brings the other 5 and then offers
    no more. Without the filter the other categories are back. The timeline lists last year's family and this
    year's. Breaks if the filter lets another category through, if a page holds more or fewer than 50, if the
    order is not newest first, or if the timeline omits a year.

    Spec deviation, not asserted: the case says "über 2 Jahre" - a client may log at most 365 days back
    (V-11, ``care_event.too_old``), so the events span one year here and the second year is the backfilled
    planting of the timeline.
    """
    tomato = species(base_url, e2e_seed_data, TOMATO)
    cabbage = species(base_url, e2e_seed_data, CABBAGE)
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc023")
    plant_on_positions(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        species_key=tomato["key"],
        id_prefix="TCB",
        points=((0.5, 0.5), (1.5, 0.5)),
    )
    last_year = backfill_last_year(base_url, e2e_seed_data, bed, cabbage["key"])
    for index in range(55):
        log_care_event(
            base_url,
            e2e_seed_data,
            bed_key=bed,
            category="watering",
            summary=f"Gießen {index:02d}",
            days_ago=index * 6.4,
        )
    for index in range(5):
        log_care_event(
            base_url,
            e2e_seed_data,
            bed_key=bed,
            category="feeding",
            summary=f"Düngen {index:02d}",
            days_ago=index * 6.4 + 3.2,
        )
    assert len(care_events(base_url, e2e_seed_data, bed, category="watering")) == 55

    bed_view.open(bed, "history")
    history_tab.filter_category("watering")
    history_tab.wait_for_shown(PAGE_SIZE, "TC-053-023: the first page of the watering filter")
    first_page = history_tab.item_texts()
    assert all("Gießen" in text and "Düngen" not in text for text in first_page), first_page
    instants = history_tab.item_instants()
    assert instants == sorted(instants, reverse=True), "TC-053-023: the list must run newest first"
    assert history_tab.has_more(), "TC-053-023: 55 events need a second page"
    screenshot("053_023_01_filtered", "Historie nach „Gießen“ gefiltert: 50 Einträge, „Mehr laden“")

    history_tab.load_more()
    history_tab.wait_for_shown(55, "TC-053-023: the second page of the watering filter")
    assert not history_tab.has_more(), "TC-053-023: the second page holds the rest, nothing follows"
    assert all("Gießen" in text for text in history_tab.item_texts())

    history_tab.filter_category("")
    history_tab.wait_for_shown(PAGE_SIZE, "TC-053-023: no filter, first page")
    assert any("Düngen" in text for text in history_tab.item_texts()), (
        "TC-053-023: without the filter the other categories are back"
    )

    this_year = utc_today().year
    history_tab.wait_for_timeline_family(last_year, cabbage["family_key"], "TC-053-023: last year")
    history_tab.wait_for_timeline_family(this_year, tomato["family_key"], "TC-053-023: this year")
    screenshot("053_023_02_timeline", "Zeitstrahl: je Jahr die Pflanzenfamilie des Beets")


# ── TC-053-028 ──────────────────────────────────────────────────────────────


def test_tc_053_028_the_lead_redacts_an_entry_and_its_whole_correction_chain(
    bed_view: BedViewPage,
    history_tab: HistoryTab,
    base_url: str,
    e2e_seed_data: dict,
    screenshot,
) -> None:
    """TC-053-028 — redact a care event: the free texts of the entry and its supersede chain become "[redacted]" (GP-ACC-044).

    Precondition (API): a bed with a note that names a third party, corrected once (a chain of two). The
    redaction is the lead's API call (``POST /care-events/{key}/redact``, the issue names it "redact via
    API"); the demo user is the lead in light mode. Asserted on the server: both events carry
    ``redacted_at`` and ``[redacted]`` in their summary, the ground stays. Asserted in the browser (with the
    corrections switch): both rows read "[redacted]" and carry the "Geschwärzt" chip, and the name does not
    appear anywhere on the tab. Breaks if only the entry is redacted and the chain keeps the text, or if the
    history still renders the redacted words.

    Not covered: a non-lead being refused (403) needs a second member; that is the backend API test of the
    redaction's permission.
    """
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc028")
    secret = f"Frau Mustermann {unique_tag()}"
    first = log_care_event(
        base_url,
        e2e_seed_data,
        bed_key=bed,
        category="note",
        summary=f"Hat mit {secret} gegossen",
        reason=f"{secret} half mit",
    )
    second = supersede_care_event(
        base_url,
        e2e_seed_data,
        first["key"],
        {
            "category": "note",
            "summary": f"Hat mit {secret} gedüngt",
            "performed_at": first["performed_at"],
            "reason": f"{secret} half mit",
        },
    )

    redact_care_event(base_url, e2e_seed_data, first["key"], "Personenbezogene Daten Dritter")

    stored = [
        tenant_get(base_url, e2e_seed_data, f"/care-events/{key}")
        for key in (first["key"], second["key"])
    ]
    for event in stored:
        assert isinstance(event, dict)
        assert event["redacted_at"], f"TC-053-028: every event of the chain is redacted: {event}"
        assert event["summary"] == "[redacted]", event
        assert secret not in str(event), f"TC-053-028: the redacted words must be gone from {event}"
        assert event["redaction_reason"] == "Personenbezogene Daten Dritter", event

    bed_view.open(bed, "history")
    bed_view.show_corrections()
    history_tab.wait_for_shown(2, "TC-053-028: the redacted chain")
    rows = history_tab.item_texts()
    assert all("[redacted]" in row and "Geschwärzt" in row for row in rows), rows
    body = history_tab.get_body_text()
    assert secret not in body, "TC-053-028: the redacted name must appear nowhere on the page"
    screenshot("053_028_01_redacted", "Historie: beide Einträge der Kette geschwärzt")


# ── Arrangement guard ───────────────────────────────────────────────────────


def test_tc_053_020_a_bed_task_arranged_by_api_is_listed_on_the_care_tab(
    bed_view: BedViewPage,
    care_tab: BedCareTab,
    base_url: str,
    e2e_seed_data: dict,
) -> None:
    """TC-053-020 (arrangement control) — a task created through the API is the row the care tab lists.

    The completion test creates its task through the UI; this control proves the care tab also lists a
    task arranged through ``POST /tasks`` (``entity_type = location``), i.e. that "the task is listed" is a
    property of the page and not of how the test made it. Breaks if the bed queue omits a bed-bound task.
    """
    _garden, bed = _one_bed(base_url, e2e_seed_data, "tc020b")
    name = f"Gießen {unique_tag()}"
    task_key = create_bed_task(base_url, e2e_seed_data, bed_key=bed, name=name, category="watering")

    bed_view.open(bed, "care")

    assert care_tab.wait_for_task(name) == task_key
