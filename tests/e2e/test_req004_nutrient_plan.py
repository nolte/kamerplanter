"""E2E tests for REQ-004 — Nutrient Plan CRUD and management.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-004.md):
  TC-REQ-004-031  ->  TC-004-012  Naehrstoffplan-Liste aufrufen
  TC-REQ-004-032  ->  TC-004-012  Naehrstoffplan-Liste aufrufen
  TC-REQ-004-033  ->  TC-004-013  Naehrstoffplan nach Substrattyp filtern
  TC-REQ-004-034  ->  TC-004-013  Naehrstoffplan nach Substrattyp filtern
  TC-REQ-004-035  ->  TC-004-012  Naehrstoffplan-Liste aufrufen
  TC-REQ-004-036  ->  TC-004-012  Naehrstoffplan-Liste aufrufen
  TC-REQ-004-037  ->  TC-004-012  Naehrstoffplan-Liste aufrufen (Row Click Navigation)
  TC-REQ-004-043  ->  TC-004-015  Neuen Naehrstoffplan erstellen -- Happy Path (Dialog)
  TC-REQ-004-044  ->  TC-004-015  Neuen Naehrstoffplan erstellen -- Happy Path (Minimal)
  TC-REQ-004-045  ->  TC-004-015  Neuen Naehrstoffplan erstellen -- Happy Path (Full)
  TC-REQ-004-046  ->  TC-004-016  Naehrstoffplan erstellen -- Namensfeld leer
  TC-REQ-004-047  ->  TC-004-015  Neuen Naehrstoffplan erstellen -- Cancel
  TC-REQ-004-048  ->  TC-004-015  Neuen Naehrstoffplan erstellen -- Template Flag
  TC-REQ-004-053  ->  TC-004-012  Naehrstoffplan-Detailseite laedt
  TC-REQ-004-054  ->  TC-004-012  Naehrstoffplan-Detailseite -- Tabs
  TC-REQ-004-055  ->  TC-004-017  Phase-Entry zu Naehrstoffplan hinzufuegen (Phase Entries Tab)
  TC-REQ-004-056  ->  TC-004-021  Plan-Vollstaendigkeits-Validierung (Validation Tab)
  TC-REQ-004-057  ->  TC-004-012  Naehrstoffplan-Detailseite -- Edit Tab prefilled
  TC-REQ-004-058  ->  TC-004-012  Naehrstoffplan-Detailseite -- Save disabled
  TC-REQ-004-059  ->  TC-004-012  Naehrstoffplan-Detailseite -- Save enables after change
  TC-REQ-004-060  ->  TC-004-027  Naehrstoffplan loeschen (Delete Confirm Dialog)
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.nutrient_plan_list_page import NutrientPlanListPage
from .pages.nutrient_plan_detail_page import NutrientPlanDetailPage

# Feature-axis marker(s) for machine-selectable test identification
# (see conftest.py::KNOWN_FEATURE_MARKERS / pytest -m <feature>).
FEATURES = ("nutrient",)


# ── Fixtures ──────────────────────────────────────────────��────────────────────


@pytest.fixture
def plan_list(browser: WebDriver, base_url: str) -> NutrientPlanListPage:
    """Return a NutrientPlanListPage bound to the current browser session."""
    return NutrientPlanListPage(browser, base_url)


@pytest.fixture
def plan_detail(browser: WebDriver, base_url: str) -> NutrientPlanDetailPage:
    """Return a NutrientPlanDetailPage bound to the current browser session."""
    return NutrientPlanDetailPage(browser, base_url)


# ── TC-REQ-004-031 to TC-REQ-004-042: Nutrient Plan List Page ─────────────────


class TestNutrientPlanListPage:
    """Nutrient plan list display and interaction (Spec: TC-004-012, TC-004-013)."""

    @pytest.mark.smoke
    def test_plan_list_page_loads(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-012: Nutrient plan list page loads and the table is present.

        Spec: TC-004-012 -- Naehrstoffplan-Liste aufrufen.
        """
        plan_list.open()
        screenshot("TC-REQ-004-031_plan-list-loaded", "Nutrient plan list page after initial load")

        assert plan_list.get_row_count() >= 0, (
            "TC-REQ-004-031 FAIL: Nutrient plan table should be present with row count >= 0"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.smoke
    def test_plan_list_has_required_columns(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-012: Nutrient plan list shows name, author, template and version columns.

        Spec: TC-004-012 -- Naehrstoffplan-Liste aufrufen.
        """
        plan_list.open()
        screenshot("TC-REQ-004-032_plan-list-columns", "Nutrient plan list showing column headers")

        headers = plan_list.get_column_headers()
        assert len(headers) > 0, (
            f"TC-REQ-004-032 FAIL: Expected column headers in the nutrient plan table, got none. Headers: {headers}"
        )

    @pytest.mark.core_crud
    def test_plan_list_search_filters_results(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-013: Searching the plan list filters visible rows.

        Spec: TC-004-013 -- Naehrstoffplan nach Substrattyp filtern.
        """
        plan_list.open()
        initial_count = plan_list.get_row_count()
        if initial_count == 0:
            pytest.skip("No nutrient plans in database — cannot test search filtering")

        term = "zzzz_nonexistent_plan_xxxx"
        plan_list.search(term)
        # The chip is the only signal that the *filter* reached the table: the
        # `DataTable` search is client-side behind a 300 ms debounce, so the
        # `wait_for_loading_complete()` that stood here polled a skeleton that
        # never mounts and returned while the unfiltered rows were still up.
        plan_list.wait_for_search_applied(term, what="nutrient plan list")

        screenshot(
            "TC-REQ-004-033_plan-search-no-match",
            "Nutrient plan list after searching for non-existent term",
        )

        # `filtered_count <= initial_count` was satisfied by a filter that does
        # nothing at all -- every one of the rows staying put holds it, and so
        # does a table that emptied for an unrelated reason (#956). No plan can
        # match this term, so the falsifiable post-condition is that the list
        # names none of them.
        remaining = plan_list.get_first_column_texts()
        assert remaining == [], (
            f"TC-REQ-004-033 FAIL: Searching for {term!r} must leave the nutrient "
            f"plan list empty, but {len(remaining)} of the {initial_count} rows are "
            f"still listed: {remaining!r}. The search chip already carries the term, "
            f"so `tableState.search` holds it and the filter has run -- a surviving "
            f"row therefore means some column's `searchValue` matches this term, "
            f"not that the search never arrived."
        )

    @pytest.mark.core_crud
    def test_plan_list_search_chip_appears(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-013: Search chip is shown after entering search text.

        Spec: TC-004-013 -- Naehrstoffplan nach Substrattyp filtern.
        """
        plan_list.open()
        plan_list.search("organic")
        plan_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-034_plan-search-chip",
            "Nutrient plan list with search chip after typing 'organic'",
        )

        assert plan_list.has_search_chip(), (
            "TC-REQ-004-034 FAIL: Expected a search chip to appear after typing in the search field"
        )

    @pytest.mark.requires_desktop
    @pytest.mark.core_crud
    def test_plan_list_sort_by_column(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-012: Clicking a column header sorts the nutrient plan list.

        Spec: TC-004-012 -- Naehrstoffplan-Liste aufrufen.
        """
        plan_list.open()
        if plan_list.get_row_count() == 0:
            pytest.skip("No nutrient plans to sort")

        headers = plan_list.get_column_headers()
        # `requires_desktop` already guarantees the table layout, so an empty
        # header list here does not mean "card layout" -- it means the table did
        # not render, which is a defect this test used to swallow as a skip
        # (#778 A6).
        assert headers, (
            "TC-REQ-004-035 FAIL: Expected column headers on a desktop viewport, but the table "
            "rendered none"
        )

        plan_list.click_column_header(headers[0])
        plan_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-035_plan-sorted", "Nutrient plan list after clicking column header to sort"
        )

        assert plan_list.has_sort_chip(), (
            "TC-REQ-004-035 FAIL: Expected a sort chip to appear after clicking a column header"
        )

    @pytest.mark.smoke
    def test_plan_list_showing_count(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-012: Nutrient plan list shows a 'Zeigt X von Y' count label.

        Spec: TC-004-012 -- Naehrstoffplan-Liste aufrufen.
        """
        plan_list.open()
        screenshot("TC-REQ-004-036_plan-showing-count", "Nutrient plan list showing count label")

        showing_text = plan_list.get_showing_count_text()
        assert showing_text, (
            f"TC-REQ-004-036 FAIL: Expected a non-empty showing count text, got: '{showing_text}'"
        )

    @pytest.mark.core_crud
    def test_plan_list_row_click_navigates_to_detail(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-012: Clicking a nutrient plan row navigates to its detail page.

        Spec: TC-004-012 -- Naehrstoffplan-Liste aufrufen (Row Click Navigation).
        """
        plan_list.open()
        if plan_list.get_row_count() == 0:
            pytest.skip("No nutrient plans in database — skipping navigation test")

        screenshot(
            "TC-REQ-004-037_before-plan-row-click", "Nutrient plan list before clicking first row"
        )

        plan_list.click_row(0)
        plan_list.wait_for_url_contains("/duengung/plans/")

        screenshot(
            "TC-REQ-004-037_after-plan-row-click",
            "Nutrient plan detail page after row click navigation",
        )

        current_url = plan_list.driver.current_url
        assert "/duengung/plans/" in current_url, (
            f"TC-REQ-004-037 FAIL: Expected URL to contain '/duengung/plans/', got: {current_url}"
        )


# ── TC-REQ-004-043 to TC-REQ-004-052: Create Dialog ──────────────────────────


class TestNutrientPlanCreateDialog:
    """Nutrient plan create dialog and validation (Spec: TC-004-015, TC-004-016)."""

    @pytest.mark.core_crud
    def test_create_dialog_opens(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-015: Clicking 'Create' opens the nutrient plan create dialog.

        Spec: TC-004-015 -- Neuen Naehrstoffplan erstellen -- Happy Path (Dialog).
        """
        plan_list.open()

        screenshot(
            "TC-REQ-004-043_before-create-plan-click",
            "Nutrient plan list before clicking create button",
        )

        plan_list.click_create()
        screenshot(
            "TC-REQ-004-043_plan-create-dialog-open",
            "Nutrient plan create dialog open with form fields",
        )

        assert plan_list.is_create_dialog_open(), (
            "TC-REQ-004-043 FAIL: Nutrient plan create dialog should be visible after clicking create"
        )

    @pytest.mark.core_crud
    def test_create_plan_with_required_name(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-015: Create a nutrient plan with only the required name field.

        Spec: TC-004-015 -- Neuen Naehrstoffplan erstellen -- Happy Path (Minimal).
        """
        plan_list.open()

        plan_list.click_create()
        unique = uuid.uuid4().hex[:8]
        plan_name = f"E2E-Plan-{unique}"

        screenshot(
            "TC-REQ-004-044_plan-create-minimal", "Create dialog with minimal plan name filled"
        )

        plan_list.fill_name(plan_name)
        plan_list.submit_create_form()
        # The exact post-condition of the create, replacing a
        # `wait_for_loading_complete()` that polled a skeleton which never
        # mounts: the dialog closes only after `await api.createNutrientPlan(...)`
        # resolves 2xx. Had this stood here before, the 500 of #966 would have
        # been reported on its first run instead of 274 days later.
        plan_list.wait_for_create_dialog_closed()

        plan_list.open()
        plan_list.search(plan_name)
        plan_list.wait_for_search_applied(plan_name, what="nutrient plan list")
        plan_list.wait_for_row_identity(
            0,
            NutrientPlanListPage.NAME_COLUMN_ID,
            plan_name,
            rows_locator=NutrientPlanListPage.TABLE_ROWS,
            what=f"self-provisioned nutrient plan {plan_name!r} (create confirmed)",
        )
        screenshot(
            "TC-REQ-004-044_after-plan-create-minimal",
            "Nutrient plan list filtered to the plan that was just created",
        )

        # Identity, not arithmetic. `new_count >= initial_count` is satisfied by
        # a create that was rejected, never submitted, or answered 500 -- which
        # is exactly what it was doing for 274 days (#956/#966). The plan is
        # named by a per-run uuid, so nothing but this create can satisfy this.
        listed = plan_list.get_first_column_texts()
        assert listed == [plan_name], (
            f"TC-REQ-004-044 FAIL: The list filtered by {plan_name!r} must name "
            f"exactly the plan just created, but reads {listed!r}. The create "
            f"dialog closed, so the POST returned 2xx -- an empty list here means "
            f"the plan is outside the 50-row slice `fetchNutrientPlans` requests "
            f"(the backend sorts by name server-side, the search filters only the "
            f"fetched slice), and more than one row means the name is not unique."
        )

    @pytest.mark.core_crud
    def test_create_plan_with_all_fields(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-015: Create a nutrient plan with all major fields filled.

        Spec: TC-004-015 -- Neuen Naehrstoffplan erstellen -- Happy Path (Full).
        """
        plan_list.open()

        plan_list.click_create()
        unique = uuid.uuid4().hex[:6]
        # The ``E2E-`` prefix is load-bearing, not cosmetic: `fetchNutrientPlans`
        # asks for 50 rows and the backend sorts by name, while the seed data
        # already ships exactly 50 plans -- so a created plan is only inside the
        # fetched slice if its name sorts early. ``FullPlan-…`` did; ``Template-…``
        # (rank 49 of 54, measured against the seed names) was one position from
        # falling out. Sorting the whole E2E-created set into one early block
        # keeps the read-back below about the *create*, not about pagination.
        plan_name = f"E2E-FullPlan-{unique}"
        plan_author = f"E2E Test Author {unique}"

        plan_list.fill_name(plan_name)
        plan_list.fill_description("E2E test nutrient plan with full data")
        plan_list.fill_author(plan_author)

        screenshot(
            "TC-REQ-004-045_plan-create-full-fields", "Create dialog with all major fields filled"
        )

        plan_list.submit_create_form()
        plan_list.wait_for_create_dialog_closed()

        plan_list.open()
        plan_list.search(plan_name)
        plan_list.wait_for_search_applied(plan_name, what="nutrient plan list")
        plan_list.wait_for_row_identity(
            0,
            NutrientPlanListPage.NAME_COLUMN_ID,
            plan_name,
            rows_locator=NutrientPlanListPage.TABLE_ROWS,
            what=f"self-provisioned nutrient plan {plan_name!r} (create confirmed)",
        )
        screenshot(
            "TC-REQ-004-045_after-plan-create-full",
            "Nutrient plan list filtered to the fully populated plan just created",
        )

        # Identity instead of a count that cannot fall (#956), and the *author*
        # too: "all major fields" is the claim this test makes, and a create that
        # persists the name while dropping the rest satisfied the old assertion
        # exactly as well as a correct one.
        listed = plan_list.get_first_column_texts()
        assert listed == [plan_name], (
            f"TC-REQ-004-045 FAIL: The list filtered by {plan_name!r} must name "
            f"exactly the plan just created, but reads {listed!r}. The create "
            f"dialog closed, so the POST returned 2xx -- an empty list here means "
            f"the plan is outside the 50-row slice `fetchNutrientPlans` requests, "
            f"and more than one row means the name is not unique."
        )
        authors = plan_list.get_column_texts("author")
        assert authors == [plan_author], (
            f"TC-REQ-004-045 FAIL: The created plan must carry the author "
            f"{plan_author!r} that was typed into the dialog, but the author "
            f"column of the one matching row reads {authors!r}. The plan itself "
            f"exists (its name matched above), so this is the create dropping a "
            f"field rather than a create that never happened -- '—' is the list's "
            f"placeholder for an empty author."
        )

    @pytest.mark.core_crud
    def test_validation_empty_name_rejected(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-016: Submitting with empty plan name shows validation error.

        Spec: TC-004-016 -- Naehrstoffplan erstellen -- Namensfeld leer.
        """
        plan_list.open()
        plan_list.click_create()

        # Do not fill any field — submit with empty name
        plan_list.submit_create_form()
        plan_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-046_plan-validation-empty-name",
            "Create dialog showing validation error for empty plan name",
        )

        assert plan_list.is_create_dialog_open(), (
            "TC-REQ-004-046 FAIL: Create dialog should remain open when submitted with an empty plan name"
        )

    @pytest.mark.core_crud
    def test_cancel_plan_create_discards_input(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-015: Cancelling the create dialog discards the entered name.

        Spec: TC-004-015 -- Neuen Naehrstoffplan erstellen -- Cancel.
        """
        plan_list.open()

        plan_list.click_create()
        plan_list.fill_name("CancelledPlan")

        screenshot(
            "TC-REQ-004-047_plan-before-cancel", "Create dialog with plan name before cancelling"
        )

        plan_list.cancel_create_form()
        plan_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-004-047_plan-after-cancel", "Nutrient plan list after cancelling create dialog"
        )

        assert not plan_list.is_create_dialog_open(), (
            "TC-REQ-004-047 FAIL: Create dialog should be closed after clicking cancel"
        )

        # Reopen dialog — name should be cleared
        plan_list.click_create()
        name_value = plan_list.get_name_field_value()
        assert name_value != "CancelledPlan", (
            f"TC-REQ-004-047 FAIL: Form should be reset after cancel, but name field still shows '{name_value}'"
        )

    @pytest.mark.core_crud
    def test_create_plan_with_template_flag(
        self, plan_list: NutrientPlanListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-004-015: Create a nutrient plan and mark it as a template.

        Spec: TC-004-015 -- Neuen Naehrstoffplan erstellen -- Template Flag.
        """
        plan_list.open()

        plan_list.click_create()
        unique = uuid.uuid4().hex[:6]
        # ``E2E-`` first, for the 50-row-slice reason spelled out in
        # `test_create_plan_with_all_fields`: ``Template-…`` sorted at rank 49 of
        # 54 against the 50 seeded plans, one position from being unfetchable.
        plan_name = f"E2E-Template-{unique}"
        plan_list.fill_name(plan_name)
        plan_list.toggle_is_template()

        screenshot(
            "TC-REQ-004-048_plan-create-template", "Create dialog with template flag enabled"
        )

        plan_list.submit_create_form()
        plan_list.wait_for_create_dialog_closed()

        plan_list.open()
        plan_list.search(plan_name)
        plan_list.wait_for_search_applied(plan_name, what="nutrient plan list")
        plan_list.wait_for_row_identity(
            0,
            NutrientPlanListPage.NAME_COLUMN_ID,
            plan_name,
            rows_locator=NutrientPlanListPage.TABLE_ROWS,
            what=f"self-provisioned template plan {plan_name!r} (create confirmed)",
        )
        screenshot(
            "TC-REQ-004-048_after-plan-create-template",
            "Nutrient plan list filtered to the template plan just created",
        )

        # Identity instead of a count that cannot fall (#956). The *flag* itself
        # is still unverified, here and anywhere else: the `is_template` column
        # is a chip on the desktop table but a conditionally rendered card chip
        # on mobile, so reading it there answers "the flag did not persist" and
        # "this page object cannot address the column" with the same error --
        # one observation, two mechanisms. `test_nutrient_plans_tenant_router.py`
        # only ever posts `is_template: False`, so nothing covers the true case;
        # the gap is recorded here rather than papered over with a read that
        # cannot say which of the two it saw.
        listed = plan_list.get_first_column_texts()
        assert listed == [plan_name], (
            f"TC-REQ-004-048 FAIL: The list filtered by {plan_name!r} must name "
            f"exactly the template plan just created, but reads {listed!r}. The "
            f"create dialog closed, so the POST returned 2xx -- an empty list here "
            f"means the plan is outside the 50-row slice `fetchNutrientPlans` "
            f"requests, and more than one row means the name is not unique."
        )


# ── TC-REQ-004-053 to TC-REQ-004-060: Detail Page ────────────────────────────


class TestNutrientPlanDetailPage:
    """Nutrient plan detail page tabs and editing (Spec: TC-004-012, TC-004-017, TC-004-021, TC-004-027)."""

    @pytest.fixture(autouse=True)
    def _ensure_plan_exists(self, plan_list: NutrientPlanListPage) -> None:
        """Pre-condition: at least one nutrient plan must exist for the detail tests.

        The seed data ships 50 plans, so on a seeded stack this returns after the
        first read and the provisioning below never runs. It exists for a stack
        that starts empty — and it now *provisions*, where it used to guess.

        What it used to do was the shape #966 exploited, one level down:
        ``except Exception: pass`` around the whole create, with the comment "if
        creation fails, seed data may still provide plans", followed by a skip.
        A create failing with HTTP 500 — which is exactly what
        ``POST /nutrient-plans`` did for 274 days — was therefore reported as
        "not available", and eight detail tests reported *skipped* rather than
        pointing at the defect they had just triggered. A pre-condition that
        cannot be established is a failure of this fixture, not a property of
        the tests that depend on it.
        """
        plan_list.open()
        if plan_list.get_row_count() > 0:
            return

        # ``E2E-`` prefix for the 50-row-slice reason spelled out in
        # `test_create_plan_with_all_fields`: the read-back has to be able to
        # find what it just created.
        plan_name = f"E2E-DetailFixture-{uuid.uuid4().hex[:6]}"
        plan_list.click_create()
        plan_list.fill_name(plan_name)
        plan_list.submit_create_form()
        # Loud where it used to be silent: the dialog closes only after
        # `await api.createNutrientPlan(...)` resolves 2xx, so a rejected create
        # times out here with the dialog still up instead of turning into a skip.
        plan_list.wait_for_create_dialog_closed()

        plan_list.open()
        plan_list.search(plan_name)
        plan_list.wait_for_search_applied(plan_name, what="nutrient plan list")
        plan_list.wait_for_row_identity(
            0,
            NutrientPlanListPage.NAME_COLUMN_ID,
            plan_name,
            rows_locator=NutrientPlanListPage.TABLE_ROWS,
            what=f"self-provisioned nutrient plan {plan_name!r} (detail-test fixture)",
        )
        # Back to the unfiltered list: `_navigate_to_first_plan` opens the route
        # fresh, but the search lives in the URL query (`useTableUrlState`), and
        # leaving it set would hand every test in this class a one-row table.
        plan_list.open()

    def _navigate_to_first_plan(self, plan_list: NutrientPlanListPage) -> str:
        """Click the first row and return the resulting URL."""
        plan_list.open()
        plan_list.click_row(0)
        plan_list.wait_for_url_contains("/duengung/plans/")
        return plan_list.driver.current_url

    @pytest.mark.smoke
    def test_plan_detail_page_loads(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-012: Nutrient plan detail page loads with plan name as title.

        Spec: TC-004-012 -- Naehrstoffplan-Detailseite laedt.
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-053_plan-detail-loaded", "Nutrient plan detail page with plan name as title"
        )

        title = detail.get_page_title_text()
        assert title, (
            f"TC-REQ-004-053 FAIL: Expected a non-empty page title on the nutrient plan detail page, got: '{title}'"
        )

    @pytest.mark.smoke
    def test_plan_detail_has_three_tabs(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-012: Nutrient plan detail page has three tabs (Phase Entries / Validation / Edit).

        Spec: TC-004-012 -- Naehrstoffplan-Detailseite -- Tabs.
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)

        tab_count = detail.get_tab_count()

        screenshot("TC-REQ-004-054_plan-detail-tabs", "Nutrient plan detail page showing tabs")

        assert tab_count >= 3, (
            f"TC-REQ-004-054 FAIL: Expected at least 3 tabs in the nutrient plan detail page, got {tab_count}"
        )

    @pytest.mark.core_crud
    def test_phase_entries_tab_is_default(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-017: Phase Entries tab is active by default on page load.

        Spec: TC-004-017 -- Phase-Entry zu Naehrstoffplan hinzufuegen (Phase Entries Tab).
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-055_plan-phase-entries-tab-default",
            "Nutrient plan detail with Phase Entries tab active by default",
        )

        active_tab = detail.get_active_tab_text()
        assert active_tab, "TC-REQ-004-055 FAIL: Expected an active tab label, got empty string"
        # First tab should be active (Phase Entries / Phaseneintraege)
        assert detail.is_first_tab_selected(), (
            "TC-REQ-004-055 FAIL: Expected the first tab (Phase Entries) to be selected by default"
        )

    @pytest.mark.core_crud
    def test_validation_tab_loads_results(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-021: Switching to the Validation tab triggers plan validation.

        Spec: TC-004-021 -- Plan-Vollstaendigkeits-Validierung (Validation Tab).
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        screenshot(
            "TC-REQ-004-056_before-validation-tab",
            "Nutrient plan detail before switching to validation tab",
        )

        detail.click_tab_validation()
        # Wait for validation to complete (spinner disappears)
        detail.wait_for_validation_loaded(timeout=30)

        screenshot(
            "TC-REQ-004-056_validation-tab-loaded", "Validation tab loaded with validation results"
        )

        alerts = detail.get_validation_alerts()
        assert len(alerts) > 0, (
            "TC-REQ-004-056 FAIL: Expected at least one alert (completeness or EC budget) in the validation tab"
        )

    @pytest.mark.core_crud
    def test_edit_tab_is_prefilled(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-012: Edit tab form is pre-filled with the plan's current data.

        Spec: TC-004-012 -- Naehrstoffplan-Detailseite -- Edit Tab prefilled.
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        title = detail.get_page_title_text()
        detail.click_tab_edit()

        screenshot(
            "TC-REQ-004-057_plan-edit-tab-prefilled",
            "Nutrient plan edit tab with pre-filled name field",
        )

        name_value = detail.get_name_field_value()
        assert name_value, (
            "TC-REQ-004-057 FAIL: Expected the name field in the edit tab to be pre-filled with the plan name"
        )
        # The assertion message already named the plan; only the check was
        # missing (#802). A non-empty field is not "pre-filled with the plan
        # name" -- it has to be *this* plan's name.
        assert name_value == title, (
            f"TC-REQ-004-057 FAIL: The edit tab must pre-fill the loaded plan's name '{title}', "
            f"but the field holds '{name_value}'"
        )

    @pytest.mark.core_crud
    def test_edit_tab_save_disabled_without_changes(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-012: Edit tab save button is disabled when no changes have been made.

        Spec: TC-004-012 -- Naehrstoffplan-Detailseite -- Save disabled.
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()
        if detail.is_read_only():
            pytest.skip(
                "First nutrient plan is origin-protected (read-only); "
                "no editable save button in light mode"
            )
        detail.click_tab_edit()

        screenshot(
            "TC-REQ-004-058_plan-edit-save-disabled",
            "Nutrient plan edit tab with save button disabled",
        )

        submit_enabled = detail.is_submit_button_enabled()
        assert not submit_enabled, (
            "TC-REQ-004-058 FAIL: Expected the save button to be disabled when no changes have been made"
        )

    @pytest.mark.core_crud
    def test_edit_tab_save_enables_after_change(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-012: Modifying a field in edit tab enables the save button.

        Spec: TC-004-012 -- Naehrstoffplan-Detailseite -- Save enables after change.
        """
        self._navigate_to_first_plan(plan_list)

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()
        if detail.is_read_only():
            pytest.skip(
                "First nutrient plan is origin-protected (read-only); "
                "no editable save button in light mode"
            )
        detail.click_tab_edit()

        detail.fill_author(f"E2E-Author-{uuid.uuid4().hex[:4]}")

        screenshot(
            "TC-REQ-004-059_plan-edit-save-enabled",
            "Nutrient plan edit tab with save button enabled after modification",
        )

        submit_enabled = detail.is_submit_button_enabled()
        assert submit_enabled, (
            "TC-REQ-004-059 FAIL: Expected the save button to be enabled after modifying a field"
        )

    @pytest.mark.core_crud
    def test_plan_delete_confirm_dialog(
        self,
        plan_list: NutrientPlanListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-027: Delete button on nutrient plan opens a confirm dialog.

        Spec: TC-004-027 -- Naehrstoffplan loeschen (Delete Confirm Dialog).
        """
        # Create a dedicated plan to delete so we don't destroy shared test data
        plan_list.open()
        plan_list.click_create()
        unique = uuid.uuid4().hex[:6]
        delete_plan_name = f"DeleteMe-{unique}"
        plan_list.fill_name(delete_plan_name)
        plan_list.submit_create_form()
        # Read-back on the arrange step, replacing a `wait_for_loading_complete()`
        # whose only real effect here was the ~3 s the implicit wait charged for
        # its empty lookup. That pause was what let the create POST land before
        # the `open()` below fired a hard navigation; with the pause gone the
        # navigation could abort the request, and the test then blamed the list
        # for not showing a plan that was never persisted. The dialog closes only
        # after `await api.createNutrientPlan(...)` resolves, so this is an exact
        # post-condition and it fails *here* when the create fails.
        plan_list.wait_for_create_dialog_closed()

        # Navigate to it via list. The two waits below replace a
        # `wait_for_loading_complete()` that proved nothing: the DataTable filter
        # is client-side behind a 300 ms debounce, so no skeleton mounts and the
        # poll returned while the table still rendered the *unfiltered* plans.
        # `click_row(0)` then opened a seeded system plan, which renders no
        # delete button at all (UI-NFR-018 R-012) -- reported on run 31113673507
        # as an empty `TimeoutException` 15 s later, nowhere near the cause.
        #
        # The skip that stood here went with it: this plan was created by this
        # test four lines above, so "could not find it" is a defect of the
        # feature under test, not an unmet environmental precondition.
        plan_list.open()
        plan_list.search(delete_plan_name)
        plan_list.wait_for_search_applied(delete_plan_name, what="nutrient plan list")
        plan_list.wait_for_row_identity(
            0,
            NutrientPlanListPage.NAME_COLUMN_ID,
            delete_plan_name,
            rows_locator=NutrientPlanListPage.TABLE_ROWS,
            # With the create now proven above, a "0 rows" here can no longer
            # mean "never created" — it would mean the plan exists but is not in
            # what the page fetched. `fetchNutrientPlans` defaults to `limit=50`
            # and the backend sorts by name server-side, while the DataTable
            # search filters only the fetched slice. The two hypotheses this
            # message names are therefore bisected by which step failed.
            what=f"self-provisioned nutrient plan {delete_plan_name!r} (create confirmed)",
        )

        plan_list.click_row(0)
        plan_list.wait_for_url_contains("/duengung/plans/")

        detail = NutrientPlanDetailPage(plan_list.driver, plan_list.base_url)
        detail.wait_for_element(detail.PAGE)
        detail.wait_for_loading_complete()

        detail.click_delete()

        screenshot(
            "TC-REQ-004-060_plan-delete-confirm-dialog", "Nutrient plan delete confirmation dialog"
        )

        assert detail.is_confirm_dialog_open(), (
            "TC-REQ-004-060 FAIL: Expected the confirm dialog to open after clicking the delete button"
        )

        # Cancel — do not actually delete
        detail.cancel_delete()
        screenshot(
            "TC-REQ-004-060_plan-delete-cancelled", "Nutrient plan detail after cancelling delete"
        )

        assert not detail.is_confirm_dialog_open(), (
            "TC-REQ-004-060 FAIL: Confirm dialog should be closed after clicking cancel"
        )
