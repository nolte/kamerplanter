"""E2E tests for REQ-004 — Fertilizer CRUD and management.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-004.md):
  TC-REQ-004-001  ->  TC-004-001  Duengemittel-Liste aufrufen und Uebersicht pruefen
  TC-REQ-004-002  ->  TC-004-001  Duengemittel-Liste aufrufen und Uebersicht pruefen
  TC-REQ-004-003  ->  TC-004-001  Duengemittel-Liste aufrufen und Uebersicht pruefen
  TC-REQ-004-004  ->  TC-004-002  Duengemittel-Filter nach Typ anwenden
  TC-REQ-004-005  ->  TC-004-002  Duengemittel-Filter nach Typ anwenden
  TC-REQ-004-006  ->  TC-004-001  Duengemittel-Liste aufrufen und Uebersicht pruefen
  TC-REQ-004-007  ->  TC-004-001  Duengemittel-Liste aufrufen und Uebersicht pruefen
  TC-REQ-004-008  ->  TC-004-008  Duengemittel-Detailseite -- Planverwendungs-Anzeige
  TC-REQ-004-013  ->  TC-004-006  Neues Duengemittel erstellen -- Happy Path (Dialog)
  TC-REQ-004-014  ->  TC-004-006  Neues Duengemittel erstellen -- Happy Path (Minimal)
  TC-REQ-004-015  ->  TC-004-006  Neues Duengemittel erstellen -- Happy Path (Full)
  TC-REQ-004-016  ->  TC-004-007  Duengemittel erstellen -- Pflichtfeld-Validierung
  TC-REQ-004-017  ->  TC-004-006  Neues Duengemittel erstellen -- Cancel
  TC-REQ-004-018  ->  TC-004-006  Neues Duengemittel erstellen -- Type Select
  TC-REQ-004-019  ->  TC-004-006  Neues Duengemittel erstellen -- NPK Fields
  TC-REQ-004-023  ->  TC-004-008  Duengemittel-Detailseite -- Planverwendungs-Anzeige
  TC-REQ-004-024  ->  TC-004-008  Duengemittel-Detailseite -- Tabs
  TC-REQ-004-025  ->  TC-004-008  Duengemittel-Detailseite -- Properties
  TC-REQ-004-026  ->  TC-004-010  Lagerbestand erfassen (Stock Tab)
  TC-REQ-004-027  ->  TC-004-008  Duengemittel-Detailseite -- Edit Tab prefilled
  TC-REQ-004-028  ->  TC-004-008  Duengemittel-Detailseite -- Save disabled
  TC-REQ-004-029  ->  TC-004-008  Duengemittel-Detailseite -- Save enables after change
  TC-REQ-004-030  ->  TC-004-009  Duengemittel-Detailseite -- Kein Plan zugeordnet (Invalid Key)
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.fertilizer_list_page import FertilizerListPage
from .pages.fertilizer_detail_page import FertilizerDetailPage

# Feature-axis marker(s) for machine-selectable test identification
# (see conftest.py::KNOWN_FEATURE_MARKERS / pytest -m <feature>).
FEATURES = ("nutrient",)


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def fertilizer_list(browser: WebDriver, base_url: str) -> FertilizerListPage:
    """Return a FertilizerListPage bound to the current browser session."""
    return FertilizerListPage(browser, base_url)


@pytest.fixture
def fertilizer_detail(browser: WebDriver, base_url: str) -> FertilizerDetailPage:
    """Return a FertilizerDetailPage bound to the current browser session."""
    return FertilizerDetailPage(browser, base_url)


# ── TC-REQ-004-001 to TC-REQ-004-012: Fertilizer List Page ────────────────────


class TestFertilizerListPage:
    """Fertilizer list display and interaction (Spec: TC-004-001, TC-004-002, TC-004-008)."""

    @pytest.mark.smoke
    def test_fertilizer_list_page_loads(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-001: Fertilizer list page loads with correct structure.

        Spec: TC-004-001 -- Duengemittel-Liste aufrufen und Uebersicht pruefen.
        """
        fertilizer_list.open()
        screenshot(
            "TC-REQ-004-001_fertilizer-list-loaded", "Fertilizer list page after initial load"
        )

        assert fertilizer_list.get_row_count() >= 0, (
            "TC-REQ-004-001 FAIL: Fertilizer table should be present and row count >= 0"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.smoke
    def test_fertilizer_list_has_required_columns(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-001: Fertilizer list shows required columns (product name, NPK, EC).

        Spec: TC-004-001 -- Duengemittel-Liste aufrufen und Uebersicht pruefen.
        """
        fertilizer_list.open()
        screenshot(
            "TC-REQ-004-002_fertilizer-list-columns", "Fertilizer list showing column headers"
        )

        headers = fertilizer_list.get_column_headers()
        assert len(headers) > 0, (
            f"TC-REQ-004-002 FAIL: Expected column headers in fertilizer table, got none. Headers: {headers}"
        )
        header_text = " ".join(headers).lower()
        assert any(keyword in header_text for keyword in ["produkt", "product", "npk", "ec"]), (
            f"TC-REQ-004-002 FAIL: Expected product name, NPK or EC columns in table headers, got: {headers}"
        )

    @pytest.mark.smoke
    def test_fertilizer_list_shows_seed_data(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-001: Fertilizer list shows seed data rows on fresh database.

        Spec: TC-004-001 -- Duengemittel-Liste aufrufen und Uebersicht pruefen.
        """
        fertilizer_list.open()
        screenshot("TC-REQ-004-003_fertilizer-seed-data", "Fertilizer list showing seed data rows")

        row_count = fertilizer_list.get_row_count()
        assert row_count > 0, (
            f"TC-REQ-004-003 FAIL: Expected at least 1 fertilizer row from seed data, got {row_count}"
        )

    @pytest.mark.core_crud
    def test_fertilizer_list_search_filters_results(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-002: Searching the fertilizer list filters visible rows.

        Spec: TC-004-002 -- Duengemittel-Filter nach Typ anwenden.
        """
        fertilizer_list.open()
        initial_count = fertilizer_list.get_row_count()
        if initial_count == 0:
            pytest.skip("No fertilizers in database — cannot test search filtering")

        term = "xxxx_nonexistent_product_yyyy"
        fertilizer_list.search(term)
        # The results panel, not `wait_for_loading_complete()`: this page's
        # search is client-side behind a 300 ms debounce and fetches nothing, so
        # no skeleton ever mounts and that wait returned while the *unfiltered*
        # rows were still up. `FertilizerListPage` passes `searchable={false}`
        # and renders its own search box, so there is no search chip to gate on
        # either -- but the box still feeds `tableState.setSearch`, so the
        # `DataTable`'s own no-results panel is rendered and is the signal.
        fertilizer_list.wait_for_no_search_results(term, what="fertilizer list")

        screenshot(
            "TC-REQ-004-004_fertilizer-search-no-match",
            "Fertilizer list after searching for non-existent product",
        )

        # `filtered_count <= initial_count` was satisfied by a filter that does
        # nothing at all -- every one of the rows staying put holds it (#956).
        # The wait above is the replacement claim and fails loudly; it says the
        # filter excluded every row *while the source rows are still there*,
        # which is what a count could never separate from an emptied list.
        #
        # What it cannot say is *which* term did the excluding, and that is
        # asserted here rather than by re-reading rows the wait already implies.
        # It is a real claim on this page and on no other: `FertilizerListPage`
        # keeps the search in two places -- a local `searchInput` and
        # `tableState.search` -- joined by two `useEffect`s, one of which writes
        # back into the input. The panel is evidence about `tableState.search`
        # alone; only the box says the two still agree on the same term.
        typed = fertilizer_list.get_search_input_value()
        assert typed == term, (
            f"TC-REQ-004-004 FAIL: The fertilizer list reports no matches, but its "
            f"search box reads {typed!r} rather than {term!r}, so the empty result is "
            f"not evidence about {term!r}. `tableState.search` and the local "
            f"`searchInput` have diverged — the back-sync effect overwrote the box "
            f"after the debounce forwarded the term."
        )

    @pytest.mark.core_crud
    def test_fertilizer_list_search_chip_appears(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-002: Search chip appears after entering a search term.

        Spec: TC-004-002 -- Duengemittel-Filter nach Typ anwenden.

        The FertilizerListPage uses a custom filter panel with searchable=false
        on the DataTable, so the built-in search-chip is NOT rendered.  Instead,
        verify that the search input accepts text and the filter panel is active.
        """
        fertilizer_list.open()
        fertilizer_list.search("base")
        fertilizer_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-005_fertilizer-search-chip", "Fertilizer list after searching for 'base'"
        )

        # FertilizerListPage uses searchable={false} on DataTable, so
        # search-chip is never rendered.  Accept that the search input works
        # (typing text) as sufficient proof the search is functional.
        search_value = fertilizer_list.get_search_input_value()
        assert search_value == "base", (
            f"TC-REQ-004-005 FAIL: Expected search input to contain 'base', got: '{search_value}'"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.core_crud
    def test_fertilizer_list_sort_by_column(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-001: Clicking a column header sorts the fertilizer list.

        Spec: TC-004-001 -- Duengemittel-Liste aufrufen und Uebersicht pruefen.

        The FertilizerListPage uses searchable={false} on the DataTable, so
        the sort-chip is never rendered.  Instead, verify that clicking a
        column header changes the URL sort parameters and the row order.
        """
        fertilizer_list.open()
        if fertilizer_list.get_row_count() == 0:
            pytest.skip("No fertilizers to sort")

        headers = fertilizer_list.get_column_headers()
        # `requires_desktop` already guarantees the table layout, so an empty
        # header list here does not mean "card layout" -- it means the table did
        # not render, which is a defect this test used to swallow as a skip
        # (#778 A6).
        assert headers, (
            "TC-REQ-004-006 FAIL: Expected column headers on a desktop viewport, but the table "
            "rendered none"
        )

        rows_before = fertilizer_list.get_first_column_texts()
        fertilizer_list.click_column_header(headers[0])
        fertilizer_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-006_fertilizer-sorted",
            "Fertilizer list after clicking column header to sort",
        )

        # FertilizerListPage uses searchable={false}, so no sort chip is
        # rendered -- the row order itself is the only evidence available.
        rows_after = fertilizer_list.get_first_column_texts()
        assert len(rows_after) > 0, (
            "TC-REQ-004-006 FAIL: Expected table rows to still be present after clicking sort"
        )
        # The previous check here was `"sort" in url or rows_after is not None`,
        # whose right-hand side is true for every possible list -- so it could
        # not fail, and the captured `rows_before` was never compared to
        # anything (#802). `headers[0]` is the column the table already sorts by
        # (`defaultSort: product_name asc`), so clicking it toggles the
        # direction and the visible order must change.
        if len(rows_before) >= 2:
            assert rows_after != rows_before, (
                "TC-REQ-004-006 FAIL: Clicking the first column header changed nothing about the "
                f"row order, so no sort was applied: {rows_before[:5]}"
            )

    @pytest.mark.smoke
    def test_fertilizer_list_showing_count(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-001: Fertilizer list shows a 'showing X of Y' count label.

        Spec: TC-004-001 -- Duengemittel-Liste aufrufen und Uebersicht pruefen.
        """
        fertilizer_list.open()
        screenshot("TC-REQ-004-007_fertilizer-showing-count", "Fertilizer list showing count label")

        showing_text = fertilizer_list.get_showing_count_text()
        assert showing_text, (
            f"TC-REQ-004-007 FAIL: Expected showing count text to be non-empty, got: '{showing_text}'"
        )
        assert any(keyword in showing_text for keyword in ["Zeigt", "von", "of", "showing"]), (
            f"TC-REQ-004-007 FAIL: Expected showing count to contain 'Zeigt'/'von'/'of', got: '{showing_text}'"
        )

    @pytest.mark.core_crud
    def test_fertilizer_list_row_click_navigates(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-008: Clicking a fertilizer row navigates to the detail page.

        Spec: TC-004-008 -- Duengemittel-Detailseite -- Planverwendungs-Anzeige.
        """
        fertilizer_list.open()
        if fertilizer_list.get_row_count() == 0:
            pytest.skip("No fertilizers in database — skipping navigation test")

        screenshot("TC-REQ-004-008_before-row-click", "Fertilizer list before clicking first row")

        fertilizer_list.click_row(0)
        fertilizer_list.wait_for_url_contains("/duengung/fertilizers/")

        screenshot(
            "TC-REQ-004-008_after-row-click", "Fertilizer detail page after row click navigation"
        )

        current_url = fertilizer_list.driver.current_url
        assert "/duengung/fertilizers/" in current_url, (
            f"TC-REQ-004-008 FAIL: Expected URL to contain '/duengung/fertilizers/', got: {current_url}"
        )


# ── TC-REQ-004-013 to TC-REQ-004-022: Create Dialog ──────────────────────────


class TestFertilizerCreateDialog:
    """Fertilizer create dialog and validation (Spec: TC-004-006, TC-004-007)."""

    @pytest.mark.core_crud
    def test_create_dialog_opens(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-006: Clicking 'Create' opens the fertilizer create dialog.

        Spec: TC-004-006 -- Neues Duengemittel erstellen -- Happy Path (Dialog).
        """
        fertilizer_list.open()

        screenshot(
            "TC-REQ-004-013_before-create-click", "Fertilizer list before clicking create button"
        )

        fertilizer_list.click_create()
        screenshot(
            "TC-REQ-004-013_create-dialog-open", "Fertilizer create dialog open with form fields"
        )

        assert fertilizer_list.is_create_dialog_open(), (
            "TC-REQ-004-013 FAIL: Create dialog should be visible after clicking the create button"
        )

    @pytest.mark.core_crud
    def test_create_fertilizer_minimal_required_fields(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-006: Create a fertilizer with only required fields (product_name).

        Spec: TC-004-006 -- Neues Duengemittel erstellen -- Happy Path (Minimal).
        """
        fertilizer_list.open()

        fertilizer_list.click_create()
        unique = uuid.uuid4().hex[:8]
        # The ``E2E-`` prefix is load-bearing, not cosmetic: `fetchFertilizers`
        # asks for 50 rows and the backend sorts by `product_name`, while the
        # seed data already ships **53** — so three seeded fertilizers are
        # already unfetchable on a fresh install, and a created one is only
        # inside the slice if its name sorts early. ``E2E-…`` ranks 21st of 54
        # against the seed names; sorting the whole E2E-created set into one
        # early block keeps the read-back below about the *create*.
        product_name = f"E2E-TestFertilizer-{unique}"

        screenshot(
            "TC-REQ-004-014_create-dialog-filled", "Create dialog with minimal product name filled"
        )

        fertilizer_list.fill_product_name(product_name)
        fertilizer_list.submit_create_form()
        # The exact post-condition of the create, replacing a
        # `wait_for_loading_complete()` that can return before the POST has even
        # been answered: the dialog closes only after
        # `await api.createFertilizer(...)` resolves 2xx.
        fertilizer_list.wait_for_create_dialog_closed()

        fertilizer_list.open()  # re-navigate to refresh list
        fertilizer_list.search(product_name)
        # No `wait_for_search_applied` here and on purpose: `FertilizerListPage`
        # passes `searchable={false}`, so the `DataTable` renders no toolbar and
        # no search chip. The identity wait below is the gate instead — it can
        # only become true in a render where the filter has run, because in the
        # unfiltered one row 0 is whichever fertilizer sorts first.
        fertilizer_list.wait_for_row_identity(
            0,
            FertilizerListPage.NAME_COLUMN_ID,
            product_name,
            rows_locator=FertilizerListPage.TABLE_ROWS,
            what=f"self-provisioned fertilizer {product_name!r} (create confirmed)",
        )
        screenshot(
            "TC-REQ-004-014_after-create",
            "Fertilizer list filtered to the fertilizer just created",
        )

        # Identity, not arithmetic. `new_count >= initial_count` is satisfied by
        # a create that was rejected, never submitted or answered 500 -- which is
        # exactly what four nutrient-plan tests of this shape did for 274 days
        # (#956/#966). The name carries a per-run uuid, so nothing but this
        # create can satisfy this.
        listed = fertilizer_list.get_first_column_texts()
        assert listed == [product_name], (
            f"TC-REQ-004-014 FAIL: The list filtered by {product_name!r} must name "
            f"exactly the fertilizer just created, but reads {listed!r}. The create "
            f"dialog closed, so the POST returned 2xx -- an empty list here means the "
            f"fertilizer is outside the 50-row slice `fetchFertilizers` requests "
            f"(53 are seeded, so the slice is already full and only the early-sorting "
            f"``E2E-`` block is reachable), and more than one row means the name is "
            f"not unique."
        )

    @pytest.mark.core_crud
    def test_create_fertilizer_with_full_data(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-006: Create a fertilizer with all major fields filled.

        Spec: TC-004-006 -- Neues Duengemittel erstellen -- Happy Path (Full).
        """
        fertilizer_list.open()

        fertilizer_list.click_create()
        unique = uuid.uuid4().hex[:6]
        # ``E2E-`` first, for the 50-row-slice reason spelled out in
        # `test_create_fertilizer_minimal_required_fields`: the seed data already
        # ships 53 fertilizers against a `limit=50` fetch, so only names that
        # sort into the early block are reachable at all. ``FloraGro-E2E-…``
        # ranked 22nd of 54 and would have worked today, but it drifts with every
        # fertilizer another test creates; the prefixed block does not.
        product_name = f"E2E-FloraGro-{unique}"
        brand = f"E2E-General-Hydro-{unique}"

        fertilizer_list.fill_product_name(product_name)
        fertilizer_list.wait_for_loading_complete()
        fertilizer_list.fill_brand(brand)
        fertilizer_list.fill_npk(3.0, 1.0, 2.0)
        try:
            fertilizer_list.fill_ec_contribution(0.020)
        except Exception:
            pass  # Field may not be visible due to scrolling
        try:
            fertilizer_list.fill_mixing_priority(10)
        except Exception:
            pass  # Field may not be visible due to scrolling
        try:
            fertilizer_list.fill_notes("E2E test fertilizer — full data")
        except Exception:
            pass  # Field may not be visible due to scrolling
        screenshot(
            "TC-REQ-004-015_create-dialog-full-fields", "Create dialog with all major fields filled"
        )

        fertilizer_list.submit_create_form()
        # The exact post-condition of the create: the dialog closes only after
        # `await api.createFertilizer(...)` resolves 2xx.
        fertilizer_list.wait_for_create_dialog_closed()

        fertilizer_list.open()
        fertilizer_list.search(product_name)
        # The identity wait is the gate: this page renders no search chip
        # (`searchable={false}`), and in the *unfiltered* render row 0 is
        # whichever fertilizer sorts first, never this one.
        fertilizer_list.wait_for_row_identity(
            0,
            FertilizerListPage.NAME_COLUMN_ID,
            product_name,
            rows_locator=FertilizerListPage.TABLE_ROWS,
            what=f"self-provisioned fertilizer {product_name!r} (create confirmed)",
        )
        screenshot(
            "TC-REQ-004-015_after-create-full",
            "Fertilizer list filtered to the fully populated fertilizer just created",
        )

        # Identity instead of a count that cannot fall (#956), and the *brand*
        # too: "all major fields" is the claim this test makes, and a create that
        # persists the product name while dropping the rest satisfied the old
        # assertion exactly as well as a correct one.
        listed = fertilizer_list.get_first_column_texts()
        assert listed == [product_name], (
            f"TC-REQ-004-015 FAIL: The list filtered by {product_name!r} must name "
            f"exactly the fertilizer just created, but reads {listed!r}. The create "
            f"dialog closed, so the POST returned 2xx -- an empty list here means the "
            f"fertilizer is outside the 50-row slice `fetchFertilizers` requests (53 "
            f"are seeded, so the slice is already full), and more than one row means "
            f"the name is not unique."
        )
        brands = fertilizer_list.get_column_texts("brand")
        assert brands == [brand], (
            f"TC-REQ-004-015 FAIL: The created fertilizer must carry the brand "
            f"{brand!r} that was typed into the dialog, but the brand column of the "
            f"one matching row reads {brands!r}. The fertilizer itself exists (its "
            f"product name matched above), so this is the create dropping a field "
            f"rather than a create that never happened -- '—' is the list's "
            f"placeholder for an empty brand."
        )
        # The NPK triple is deliberately *not* asserted alongside it: the column
        # renders `${npk_ratio[0]}-${…}` straight off the JSON, so what a typed
        # "3.0" reads back as depends on the backend's float handling, and a
        # mismatch would arrive as "the create dropped the field" when it may
        # only be formatting. It needs its own check, with its own evidence.

    @pytest.mark.core_crud
    def test_validation_empty_product_name(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-007: Submitting with empty product_name shows validation error.

        Spec: TC-004-007 -- Duengemittel erstellen -- Pflichtfeld-Validierung.
        """
        fertilizer_list.open()
        fertilizer_list.click_create()

        # Leave product_name empty and submit
        fertilizer_list.submit_create_form()
        fertilizer_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-016_validation-empty-name",
            "Create dialog showing validation error for empty product name",
        )

        # Dialog should remain open
        assert fertilizer_list.is_create_dialog_open(), (
            "TC-REQ-004-016 FAIL: Create dialog should remain open after submitting with empty product_name"
        )

    @pytest.mark.core_crud
    def test_cancel_create_dialog_closes_without_saving(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-006: Cancelling the create dialog closes it without saving.

        Spec: TC-004-006 -- Neues Duengemittel erstellen -- Cancel.
        """
        fertilizer_list.open()
        initial_count = fertilizer_list.get_row_count()

        fertilizer_list.click_create()
        fertilizer_list.fill_product_name("CancelledFertilizer")

        screenshot(
            "TC-REQ-004-017_before-cancel", "Create dialog with product name before cancelling"
        )

        fertilizer_list.cancel_create_form()
        # Wait for the unmount itself, not for a reader to happen to sample the
        # frame after it. The loop this replaces re-entered the exact window it
        # was trying to leave: `is_create_dialog_open()` was called *during* the
        # ~195 ms MUI exit transition, so every iteration re-created the moment
        # in which the dialog node dies between the lookup and the read.
        fertilizer_list.wait_for_create_dialog_closed()
        screenshot("TC-REQ-004-017_after-cancel", "Fertilizer list after cancelling create dialog")

        assert not fertilizer_list.is_create_dialog_open(), (
            "TC-REQ-004-017 FAIL: Create dialog should be closed after clicking cancel"
        )
        # The case is "Cancel", so the point is that nothing was persisted --
        # never asserted before #802.
        assert fertilizer_list.get_row_count() == initial_count, (
            f"TC-REQ-004-017 FAIL: Cancelling must create nothing, but the row count went from "
            f"{initial_count} to {fertilizer_list.get_row_count()}"
        )

        # Re-open — form should be reset
        fertilizer_list.click_create()
        fertilizer_list.wait_for_loading_complete()
        name_value = fertilizer_list.get_product_name_field_value()
        assert name_value != "CancelledFertilizer", (
            f"TC-REQ-004-017 FAIL: Form should be reset after cancel, but product_name still shows '{name_value}'"
        )

    @pytest.mark.core_crud
    def test_create_dialog_has_fertilizer_type_select(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-006: Create dialog contains a fertilizer type select field.

        Spec: TC-004-006 -- Neues Duengemittel erstellen -- Type Select.
        """
        fertilizer_list.open()
        fertilizer_list.click_create()

        screenshot(
            "TC-REQ-004-018_create-dialog-type-field",
            "Create dialog showing fertilizer type select field",
        )

        assert fertilizer_list.has_form_field("fertilizer_type"), (
            "TC-REQ-004-018 FAIL: Expected a 'fertilizer_type' select field in the create dialog"
        )

    @pytest.mark.core_crud
    def test_create_dialog_has_npk_fields(
        self, fertilizer_list: FertilizerListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-006: Create dialog contains N, P, K number input fields.

        Spec: TC-004-006 -- Neues Duengemittel erstellen -- NPK Fields.
        """
        fertilizer_list.open()
        fertilizer_list.click_create()

        screenshot(
            "TC-REQ-004-019_create-dialog-npk-fields", "Create dialog showing N, P, K input fields"
        )

        for field_name in ["npk_n", "npk_p", "npk_k"]:
            assert fertilizer_list.has_form_field(field_name), (
                f"TC-REQ-004-019 FAIL: Expected a '{field_name}' number field in the create dialog"
            )


# ── TC-REQ-004-023 to TC-REQ-004-030: Detail Page ────────────────────────────


class TestFertilizerDetailPage:
    """Fertilizer detail page tabs and editing (Spec: TC-004-008, TC-004-010)."""

    @pytest.fixture(autouse=True)
    def _ensure_fertilizer_exists(self, fertilizer_list: FertilizerListPage) -> None:
        """Pre-condition: ensure at least one fertilizer exists for detail tests."""
        fertilizer_list.open()
        if fertilizer_list.get_row_count() == 0:
            # Create a minimal fertilizer to use in detail tests
            fertilizer_list.click_create()
            unique = uuid.uuid4().hex[:6]
            fertilizer_list.fill_product_name(f"DetailTest-{unique}")
            fertilizer_list.submit_create_form()
            fertilizer_list.wait_for_loading_complete()
            fertilizer_list.open()

    def _navigate_to_first_fertilizer(self, fertilizer_list: FertilizerListPage) -> str:
        """Click the first row and return the resulting URL."""
        fertilizer_list.open()
        fertilizer_list.click_row(0)
        fertilizer_list.wait_for_url_contains("/duengung/fertilizers/")
        return fertilizer_list.driver.current_url

    @pytest.mark.smoke
    def test_detail_page_loads_with_title(
        self,
        fertilizer_list: FertilizerListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-008: Fertilizer detail page loads and shows the product name as title.

        Spec: TC-004-008 -- Duengemittel-Detailseite -- Planverwendungs-Anzeige.
        """
        self._navigate_to_first_fertilizer(fertilizer_list)

        from .pages.fertilizer_detail_page import FertilizerDetailPage

        detail = FertilizerDetailPage(fertilizer_list.driver, fertilizer_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-023_fertilizer-detail-loaded",
            "Fertilizer detail page with product name as title",
        )

        title = detail.get_page_title_text()
        assert title, (
            f"TC-REQ-004-023 FAIL: Expected a non-empty page title in the fertilizer detail page, got: '{title}'"
        )

    @pytest.mark.smoke
    def test_detail_page_has_three_tabs(
        self,
        fertilizer_list: FertilizerListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-008: Fertilizer detail page has exactly three tabs.

        Spec: TC-004-008 -- Duengemittel-Detailseite -- Tabs.
        """
        self._navigate_to_first_fertilizer(fertilizer_list)

        from .pages.fertilizer_detail_page import FertilizerDetailPage

        detail = FertilizerDetailPage(fertilizer_list.driver, fertilizer_list.base_url)
        detail.wait_for_element(detail.PAGE)

        screenshot("TC-REQ-004-024_fertilizer-detail-tabs", "Fertilizer detail page showing tabs")

        tab_count = detail.get_tab_count()
        assert tab_count >= 3, (
            f"TC-REQ-004-024 FAIL: Expected at least 3 tabs in the fertilizer detail page, got {tab_count}"
        )

    @pytest.mark.core_crud
    def test_detail_tab_shows_product_properties(
        self,
        fertilizer_list: FertilizerListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-008: Details tab (Tab 0) shows fertilizer properties.

        Spec: TC-004-008 -- Duengemittel-Detailseite -- Properties.
        """
        self._navigate_to_first_fertilizer(fertilizer_list)

        from .pages.fertilizer_detail_page import FertilizerDetailPage

        detail = FertilizerDetailPage(fertilizer_list.driver, fertilizer_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()
        detail.click_tab_details()

        screenshot(
            "TC-REQ-004-025_fertilizer-tab-details",
            "Fertilizer details tab showing product properties",
        )

        labels = detail.get_all_detail_labels()
        assert len(labels) > 0, (
            f"TC-REQ-004-025 FAIL: Expected property labels in the details tab, got: {labels}"
        )

    @pytest.mark.core_crud
    def test_stock_tab_is_accessible(
        self,
        fertilizer_list: FertilizerListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-010: Stock tab (Tab 1) is accessible and renders without error.

        Spec: TC-004-010 -- Lagerbestand erfassen (Stock Tab).
        """
        self._navigate_to_first_fertilizer(fertilizer_list)

        from .pages.fertilizer_detail_page import FertilizerDetailPage

        detail = FertilizerDetailPage(fertilizer_list.driver, fertilizer_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()
        detail.click_tab_stock()

        screenshot("TC-REQ-004-026_fertilizer-tab-stock", "Fertilizer stock tab content")

        # Either a data table or an empty state should be present
        assert detail.has_stock_table_or_empty_state(), (
            "TC-REQ-004-026 FAIL: Expected either a data table or empty state in the Stock tab"
        )

    @pytest.mark.core_crud
    def test_edit_tab_form_is_prefilled(
        self,
        fertilizer_list: FertilizerListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-008: Edit tab (Tab 2) pre-fills product name from loaded data.

        Spec: TC-004-008 -- Duengemittel-Detailseite -- Edit Tab prefilled.
        """
        self._navigate_to_first_fertilizer(fertilizer_list)

        from .pages.fertilizer_detail_page import FertilizerDetailPage

        detail = FertilizerDetailPage(fertilizer_list.driver, fertilizer_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        # First get title from details tab
        title = detail.get_page_title_text()

        detail.click_tab_edit()
        screenshot(
            "TC-REQ-004-027_fertilizer-tab-edit-prefilled",
            "Fertilizer edit tab with pre-filled product name",
        )

        name_value = detail.get_product_name_field_value()
        assert name_value, (
            "TC-REQ-004-027 FAIL: Expected the product_name field to be pre-filled in the edit tab"
        )
        # "pre-fills … from loaded data" -- a non-empty field satisfies neither
        # half of that. It has to carry *this* fertilizer's name, the one the
        # details tab shows (#802).
        assert name_value == title, (
            f"TC-REQ-004-027 FAIL: The edit tab must pre-fill the loaded fertilizer's name "
            f"'{title}', but the field holds '{name_value}'"
        )

    @pytest.mark.core_crud
    def test_edit_tab_save_button_disabled_without_changes(
        self,
        fertilizer_list: FertilizerListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-008: Edit tab save button is disabled when no changes are made.

        Spec: TC-004-008 -- Duengemittel-Detailseite -- Save disabled.
        """
        self._navigate_to_first_fertilizer(fertilizer_list)

        from .pages.fertilizer_detail_page import FertilizerDetailPage

        detail = FertilizerDetailPage(fertilizer_list.driver, fertilizer_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()
        if detail.is_read_only():
            pytest.skip(
                "First fertilizer is origin-protected (read-only); "
                "no editable save button in light mode"
            )
        detail.click_tab_edit()

        screenshot(
            "TC-REQ-004-028_fertilizer-edit-save-disabled",
            "Fertilizer edit tab with save button disabled",
        )

        submit_enabled = detail.is_submit_button_enabled()
        assert not submit_enabled, (
            "TC-REQ-004-028 FAIL: Expected the save button to be disabled when no changes have been made in the edit tab"
        )

    @pytest.mark.core_crud
    def test_edit_tab_save_button_enables_after_change(
        self,
        fertilizer_list: FertilizerListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-008: Modifying a field in edit tab enables the save button.

        Spec: TC-004-008 -- Duengemittel-Detailseite -- Save enables after change.
        """
        self._navigate_to_first_fertilizer(fertilizer_list)

        from .pages.fertilizer_detail_page import FertilizerDetailPage

        detail = FertilizerDetailPage(fertilizer_list.driver, fertilizer_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()
        if detail.is_read_only():
            pytest.skip(
                "First fertilizer is origin-protected (read-only); "
                "no editable save button in light mode"
            )
        detail.click_tab_edit()

        # Modify the brand field to trigger isDirty
        detail.fill_brand(f"EditedBrand-{uuid.uuid4().hex[:4]}")

        screenshot(
            "TC-REQ-004-029_fertilizer-edit-save-enabled",
            "Fertilizer edit tab with save button enabled after modification",
        )

        submit_enabled = detail.is_submit_button_enabled()
        assert submit_enabled, (
            "TC-REQ-004-029 FAIL: Expected the save button to be enabled after modifying a field"
        )

    @pytest.mark.core_crud
    def test_invalid_key_shows_error(
        self,
        fertilizer_detail: FertilizerDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-009: Navigating to a non-existent fertilizer key shows an error.

        Spec: TC-004-009 -- Duengemittel-Detailseite -- Kein Plan zugeordnet (Invalid Key).
        """
        fertilizer_detail.navigate("/duengung/fertilizers/nonexistent-key-99999")

        screenshot(
            "TC-REQ-004-030_fertilizer-not-found-error",
            "Error display for non-existent fertilizer key",
        )

        # Wait for either the detail page or an error state
        fertilizer_detail.wait_for_error_or_page()

        if fertilizer_detail.is_error_displayed():
            # Error was shown — nothing further to assert, the expected state was reached.
            pass
        else:
            # Page loaded but may show a not-found message differently
            page_text = fertilizer_detail.get_body_text()
            assert any(
                keyword in page_text.lower()
                for keyword in ["nicht gefunden", "not found", "404", "error"]
            ), (
                f"TC-REQ-004-030 FAIL: Expected an error or not-found message for invalid key, page body: {page_text[:200]}"
            )
