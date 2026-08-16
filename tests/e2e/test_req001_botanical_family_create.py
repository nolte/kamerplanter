"""E2E tests for REQ-001 — Botanical Family Create Dialog.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-013  ->  TC-001-006  Neue Botanische Familie erfolgreich erstellen (Dialog oeffnen)
  TC-REQ-001-014  ->  TC-001-006  Neue Botanische Familie erfolgreich erstellen (Happy Path)
  TC-REQ-001-015  ->  TC-001-007  Validierung — Familienname muss auf '-aceae' enden
  TC-REQ-001-016  ->  TC-001-009  Validierung — Pflichtfelder (Name leer)
  TC-REQ-001-020  ->  TC-001-006  Neue Botanische Familie mit minimalen Feldern erstellen
  TC-REQ-001-021  ->  TC-001-012  Loeschen abbrechen / Dialog-Cancel
  TC-REQ-001-022  ->  TC-001-013  pH-Bereich-Validierung — Grenzwerte
  TC-REQ-001-019  ->  TC-001-017  Nitrogen-Fixing + Heavy Demand Kombination abgelehnt
  TC-REQ-001-078  ->  TC-001-078  Duplikat-Schutz — Species mit identischem Namen abgelehnt
  TC-REQ-001-099  ->  TC-001-099  Nur ein Plattform-Admin darf globale Familien anlegen (full mode)
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BotanicalFamilyListPage


@pytest.fixture
def family_list(browser: WebDriver, base_url: str) -> BotanicalFamilyListPage:
    return BotanicalFamilyListPage(browser, base_url)


@pytest.mark.platform_admin
class TestBotanicalFamilyCreateDialog:
    """Create dialog and validation (Spec: TC-001-006, TC-001-007, TC-001-009, TC-001-013)."""

    @pytest.mark.smoke
    def test_open_create_dialog(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-006: Open the create dialog and verify form fields.

        Spec: TC-001-006 -- Neue Botanische Familie erfolgreich erstellen (Dialog-Oeffnung).
        """
        family_list.open()
        screenshot(
            "TC-REQ-001-013_family-list-loaded",
            "Botanical family list page before opening create dialog",
        )

        family_list.click_create()
        screenshot(
            "TC-REQ-001-013_create-dialog-open",
            "Botanical family create dialog with form fields visible",
        )

        assert family_list.is_create_dialog_open(), "Create dialog should be open"

    @pytest.mark.core_crud
    def test_create_family_with_all_fields(
        self,
        family_list: BotanicalFamilyListPage,
        screenshot: Callable[..., Path],
        app_mode: str,
    ) -> None:
        """TC-001-006: Successfully create a botanical family with all fields.

        Spec: TC-001-006 -- Neue Botanische Familie erfolgreich erstellen (Happy Path).

        **Light mode only, since #1120.** `BotanicalFamily` is global reference
        data with no `tenant_key`, so creating one is curation and requires a
        platform admin. In light mode the sole anonymous operator *is* that
        admin (REQ-027); in full mode this runs as the seeded admin account
        (#1155). It used to skip full mode entirely, because no such account
        existed — so the happy path was verified in one profile out of four while
        the report showed a neutral skip for the rest.
        """
        family_list.open()

        family_list.click_create()
        unique = uuid.uuid4().hex[:6]
        # Family names must end in "-aceae" and order names in "-ales" (botanical
        # nomenclature, enforced by BotanicalFamily and mirrored on FamilyCreate),
        # so the uniqueness suffix goes BEFORE the suffix — otherwise the create is
        # a legitimate 422 and this happy-path never provisions a family.
        family_name = f"E2eTest{unique}aceae"
        common_name_de = f"Testfamilie {unique}"
        common_name_en = f"Test family {unique}"
        family_list.fill_create_form(
            family_name,
            common_name_de=common_name_de,
            common_name_en=common_name_en,
            order=f"Test{unique}ales",
            description="E2E-Test botanische Familie",
            ph_min="5.5",
            ph_max="7.0",
            rotation_category="test",
        )
        screenshot("TC-REQ-001-014_form-filled", f"Create dialog filled with {family_name}")

        family_list.submit_create_form()
        # The exact post-condition of the create, replacing a
        # `wait_for_loading_complete()` that can return before the POST has even
        # been answered: the dialog closes only after
        # `await api.createBotanicalFamily(...)` resolves 2xx.
        family_list.wait_for_create_dialog_closed()

        family_list.open()
        family_list.search(family_name)
        family_list.wait_for_search_applied(family_name, what="botanical family list")
        family_list.wait_for_row_identity(
            0,
            BotanicalFamilyListPage.NAME_COLUMN_ID,
            family_name,
            rows_locator=BotanicalFamilyListPage.TABLE_ROWS,
            what=f"self-provisioned botanical family {family_name!r} (create confirmed)",
        )
        screenshot("TC-REQ-001-014_after-create", "Family list filtered to the family just created")

        # Identity, not arithmetic. `new_count >= initial_count` is satisfied by
        # a create that was rejected, never submitted or answered 500 -- which is
        # exactly what four nutrient-plan tests of this shape did for 274 days
        # (#956/#966). The name carries a per-run uuid, so nothing but this
        # create can satisfy this.
        listed = family_list.get_first_column_texts()
        assert listed == [family_name], (
            f"TC-REQ-001-014 FAIL: The list filtered by {family_name!r} must name "
            f"exactly the family just created, but reads {listed!r}. The create dialog "
            f"closed, so the POST returned 2xx -- an empty list here means the family "
            f"fell outside the 50-row slice `fetchBotanicalFamilies` requests (18 "
            f"families are seeded and 'E2e…' sorts among them, so that needs ~32 more "
            f"created ones), and more than one row means the name is not unique."
        )

        # …and a second field, because "with all fields" is the claim this test
        # makes: a create that persists the name while dropping the rest
        # satisfied the old count exactly as well as a correct one. Either
        # common name is accepted — the column renders the one matching the UI
        # language, and both were typed, so this stays a statement about the
        # *create* rather than about which locale the profile runs in.
        common_names = family_list.get_column_texts("commonName")
        assert common_names in ([common_name_de], [common_name_en]), (
            f"TC-REQ-001-014 FAIL: The created family must carry a common name that "
            f"was typed into the dialog ({common_name_de!r} / {common_name_en!r}), but "
            f"the common-name column of the one matching row reads {common_names!r}. "
            f"The family itself exists (its name matched above), so the create dropped "
            f"the field rather than failing -- '—' is the list's placeholder for a "
            f"family that carries neither common name."
        )

    @pytest.mark.core_crud
    def test_validation_name_not_ending_with_aceae(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-007: Validation error — family name does not end with '-aceae'.

        Spec: TC-001-007 -- Validierung — Familienname muss auf '-aceae' enden.
        """
        family_list.open()
        family_list.click_create()
        family_list.fill_name_only("Solanidae")
        family_list.submit_create_form()

        family_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-015_validation-error",
            "Create dialog after submitting name not ending with -aceae",
        )

        assert family_list.is_create_dialog_open(), (
            "TC-REQ-001-015 FAIL: Dialog should remain open after validation error"
        )

    @pytest.mark.core_crud
    def test_validation_empty_name(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-009: Validation error — empty name field.

        Spec: TC-001-009 -- Validierung — Pflichtfelder (Name leer).
        """
        family_list.open()
        family_list.click_create()
        family_list.fill_name_only("")
        family_list.submit_create_form()

        family_list.wait_for_loading_complete()
        screenshot("TC-REQ-001-016_validation-error", "Create dialog after submitting empty name")

        assert family_list.is_create_dialog_open(), (
            "TC-REQ-001-016 FAIL: Dialog should remain open after validation error"
        )

    @pytest.mark.core_crud
    def test_create_family_minimal_fields(
        self,
        family_list: BotanicalFamilyListPage,
        screenshot: Callable[..., Path],
        app_mode: str,
    ) -> None:
        """TC-001-006: Create a family with minimal fields (only required).

        Spec: TC-001-006 -- Neue Botanische Familie mit minimalen Pflichtfeldern erstellen.

        **What this case means, decided in #1153.** The minimum field set *is*
        sufficient: ``FamilyCreate`` requires only ``name``, and the dialog's two
        ``required`` multi-selects (``typical_growth_forms``,
        ``pollination_type``) ship pre-filled with ``['herb']`` and ``['insect']``.
        So typing only a name is a create that must land, and this asserts that it
        did.

        Until #1153 it asserted **nothing**. Its comment said either outcome was
        acceptable — dialog closed *or* dialog still open — which made it green on
        a successful create, on a validation refusal, and (as measured against the
        ``full`` profile after #1120) on an *authorization* refusal. Its sibling
        ``test_create_family_with_all_fields`` had to be mode-split because the
        create genuinely stopped working for the demo user; this one did not
        notice. It also stated a reason that was not true: no required multi-select
        was ever empty.

        Creating global reference data is curation and needs a platform admin
        (#1120): the sole anonymous operator in light mode (REQ-027), the seeded
        admin account in full mode (#1155). Skipped in full mode until that
        account existed.
        """
        family_list.open()
        family_list.click_create()

        unique = uuid.uuid4().hex[:6]
        # The uniqueness suffix goes BEFORE "-aceae": botanical nomenclature is
        # enforced on both FamilyCreate and the domain model, so a trailing suffix
        # would make this a legitimate 422 and the case would never create anything.
        family_name = f"Minimal{unique}aceae"
        family_list.fill_name_only(family_name)
        screenshot("TC-REQ-001-020_minimal-filled", f"Create dialog with only name {family_name}")

        family_list.submit_create_form()
        # The exact post-condition, not `wait_for_loading_complete()` — that can
        # return before the POST has been answered at all. The dialog closes only
        # after `await api.createBotanicalFamily(...)` resolves 2xx, so waiting for
        # it to close is what makes "the server accepted this" observable.
        family_list.wait_for_create_dialog_closed()

        family_list.open()
        family_list.search(family_name)
        family_list.wait_for_search_applied(family_name, what="botanical family list")
        family_list.wait_for_row_identity(
            0,
            BotanicalFamilyListPage.NAME_COLUMN_ID,
            family_name,
            rows_locator=BotanicalFamilyListPage.TABLE_ROWS,
            what=f"self-provisioned botanical family {family_name!r} (minimal create confirmed)",
        )
        screenshot(
            "TC-REQ-001-020_after-submit", "Family list filtered to the minimally created family"
        )

        # Identity, not arithmetic, and not "the app did not crash" — the two
        # shapes that let this class of test stay green through a refusal
        # (#956/#966, and this very case for as long as it existed). The name
        # carries a per-run uuid, so nothing but this create can satisfy it.
        listed = family_list.get_first_column_texts()
        assert listed == [family_name], (
            f"TC-REQ-001-020 FAIL: The list filtered by {family_name!r} must name exactly "
            f"the family just created from the minimum field set, but reads {listed!r}. "
            f"An empty list means the create did not land despite the dialog closing; "
            f"more than one row means the name is not unique."
        )

    @pytest.mark.core_crud
    def test_cancel_create_dialog(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-012: Cancel the create dialog discards unsaved input.

        Spec: TC-001-012 -- Loeschen abbrechen — Dialog-Cancel verwirft Eingaben.
        """
        from selenium.webdriver.support.ui import WebDriverWait

        family_list.open()
        family_list.click_create()
        family_list.fill_name_only("Discardaceae")
        screenshot("TC-REQ-001-021_before-cancel", "Create dialog with Discardaceae before cancel")

        family_list.cancel_create_form()

        # MUI Dialog animates on close — wait for dialog to disappear
        WebDriverWait(family_list.driver, 10).until(
            lambda d: not family_list.is_create_dialog_open()
        )
        screenshot("TC-REQ-001-021_after-cancel", "Family list after cancelling create dialog")

        assert not family_list.is_create_dialog_open(), (
            "TC-REQ-001-021 FAIL: Dialog should be closed after cancel"
        )

        # Reopen and check that the form is reset
        family_list.click_create()
        family_list.wait_for_loading_complete()
        name_value = family_list.get_name_field_value()
        assert name_value != "Discardaceae", (
            f"TC-REQ-001-021 FAIL: Expected form reset, but name field still contains '{name_value}'"
        )

    @pytest.mark.core_crud
    def test_ph_range_boundary_values(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-013: pH range boundary values (min=3.0, max=9.0).

        Spec: TC-001-013 -- pH-Bereich-Validierung — Grenzwerte.
        """
        family_list.open()
        family_list.click_create()

        unique = uuid.uuid4().hex[:6]
        family_list.fill_create_form(
            f"Boundary{unique}aceae",
            ph_min="3.0",
            ph_max="9.0",
        )
        screenshot(
            "TC-REQ-001-022_ph-boundary-filled",
            f"Create dialog with pH 3.0-9.0 for Boundary{unique}aceae",
        )

        family_list.submit_create_form()

        family_list.wait_for_loading_complete()
        screenshot("TC-REQ-001-022_after-submit", "Family list after pH boundary creation")
        # Should succeed (boundary values are valid)


@pytest.mark.platform_admin
class TestBotanicalFamilyBackendValidation:
    """Backend validation rules (Spec: TC-001-017, TC-001-078)."""

    @pytest.mark.core_crud
    def test_nitrogen_fixing_with_heavy_demand_rejected(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-017: nitrogen_fixing=true with heavy nutrient demand is rejected.

        Spec: TC-001-017 -- Nitrogen-Fixing + Heavy Demand Kombination wird abgelehnt.
        """

        family_list.open()
        family_list.click_create()

        unique = uuid.uuid4().hex[:6]
        family_list.fill_name_only(f"Conflict{unique}aceae")
        # Neither of these is attempted-and-excused any more.
        #
        # This block used to try the German label, fall back to the raw enum
        # value, and skip on any exception; the toggle skipped on any exception
        # too, with the message "nitrogen_fixing toggle not available in create
        # dialog". That message was never measured, and it is wrong:
        # `BotanicalFamilyCreateDialog` renders a `FormSwitchField` named
        # `nitrogen_fixing`, which is exactly what `toggle_switch` addresses,
        # and `enums.nutrientDemand.heavy` is "Starkzehrer", which is exactly
        # what the first attempt asked for. So the fallback was dead and the
        # skips asserted a cause nobody had checked — while destroying the
        # evidence of whatever really went wrong.
        #
        # If either interaction fails now, it fails with its own exception. A
        # red case with a traceback is worth more than a neutral result whose
        # explanation is a guess.
        family_list.select_option("typical_nutrient_demand", "Starkzehrer")
        family_list.toggle_switch("nitrogen_fixing")

        screenshot(
            "TC-REQ-001-019_before-submit", "Create dialog with nitrogen_fixing + heavy demand"
        )
        family_list.submit_create_form()

        # Wait for backend response
        family_list.wait_for_loading_complete()

        screenshot(
            "TC-REQ-001-019_validation-result",
            "Result after submitting nitrogen_fixing + heavy demand",
        )

        # Backend validation should either keep dialog open or show an error
        # snackbar. Both are valid outcomes.
        dialog_open = family_list.is_create_dialog_open()
        snackbar_visible = family_list.has_error_snackbar()
        assert dialog_open or snackbar_visible, (
            "TC-REQ-001-019 FAIL: Backend validation error should keep dialog open or show error snackbar"
        )

    @pytest.mark.core_crud
    def test_duplicate_family_name_rejected(
        self,
        family_list: BotanicalFamilyListPage,
        screenshot: Callable[..., Path],
        app_mode: str,
    ) -> None:
        """TC-001-078: Duplicate family name shows backend validation error.

        Spec: TC-001-078 -- Duplikat-Schutz — Familie mit identischem Namen wird abgelehnt.

        The assertion is "the dialog stays open", which the #1120 role gate also
        satisfies — so between #1120 and #1155 this ran in light mode only, since
        in full mode the demo user was refused *before* the unique index could
        reject the duplicate and the case would have passed without observing its
        own subject. Running as the seeded admin (#1155) puts the duplicate back
        in front of the index.
        """
        family_list.open()
        family_list.click_create()
        family_list.fill_name_only("Solanaceae")  # Exists in seed data
        screenshot("TC-REQ-001-078_duplicate-name", "Create dialog with duplicate name Solanaceae")

        family_list.submit_create_form()

        family_list.wait_for_loading_complete()
        screenshot("TC-REQ-001-078_after-submit", "Result after submitting duplicate family name")

        # Should show error notification — dialog remains open
        assert family_list.is_create_dialog_open(), (
            "TC-REQ-001-078 FAIL: Dialog should remain open after duplicate name error"
        )


class TestGlobalCatalogueRoleGate:
    """Who may curate the global family catalogue (Spec: TC-001-099)."""

    @pytest.mark.core_crud
    def test_the_create_action_is_not_offered_to_an_ordinary_member(
        self,
        family_list: BotanicalFamilyListPage,
        screenshot: Callable[..., Path],
        app_mode: str,
    ) -> None:
        """TC-001-099: An ordinary member is not offered the global-catalogue create.

        Spec: TC-001-099 -- Nur ein Plattform-Admin darf globale Botanische Familien anlegen.

        `BotanicalFamily` is global reference data with no `tenant_key`, so #1120
        gated its mutations on the platform admin — the same rule #1109 set for
        the global cultivar catalogue.

        **This case used to submit the form and assert the refusal**, which was
        the right shape while the button was still offered to everyone: the whole
        point of #1155 is that it was, and that a member could fill in every field
        before learning they may not. Now that the affordance is gone the dialog
        is unreachable, so the observable fact moved with it — from "the refusal
        arrives" to "the request is never invited".

        The API refusal itself is not lost, and is not re-asserted here: it lives
        in the backend tests for #1120, where it belongs. Asserting it through a
        UI that no longer offers the path would mean reaching around the product
        to reach the rule.

        Full mode only: in light mode the sole operator *is* that admin
        (REQ-027), so there is no ordinary member to refuse.
        """
        if app_mode == "light":
            pytest.skip(
                "light mode's sole anonymous operator is treated as platform admin "
                "(REQ-027), so there is no non-admin caller here — TC-001-006 covers it"
            )

        family_list.open()
        # Anchored on a rendered row, not read bare: the button and the table
        # arrive in the same commit, so an absence read on a still-loading page
        # would be satisfied for an administrator too, and this assertion would
        # pass no matter who is logged in.
        assert family_list.get_row_count() > 0, (
            "TC-REQ-001-099 SETUP: the seeded family catalogue must have rendered before "
            "the absence of the create button means anything"
        )
        screenshot("TC-REQ-001-099_list-as-member", "Family list as an ordinary member")

        assert not family_list.has_create_button(), (
            "TC-REQ-001-099 FAIL: an ordinary member is offered 'Familie erstellen'. "
            "The API refuses the create with 403 (#1120), so the dialog is a dead end: "
            "every field accepts input and the refusal arrives only on submit."
        )
