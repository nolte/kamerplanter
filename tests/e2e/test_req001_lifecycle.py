"""E2E tests for REQ-001 — Lifecycle Config & Growth Phases.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-051  ->  TC-001-047  Lebenszyklus-Tab zeigt LifecycleConfig und GrowthPhases
  TC-REQ-001-052  ->  TC-001-047  Lifecycle-Config fuer einjaehrige Art erstellen
  TC-REQ-001-055  ->  TC-001-047  Bestehende Lifecycle-Config bearbeiten
  TC-REQ-001-056  ->  TC-001-048  Wachstumsphasen-Bereich nach Lifecycle-Erstellung sichtbar
  TC-REQ-001-057  ->  TC-001-048  Neue Wachstumsphase anlegen
  TC-REQ-001-059  ->  TC-001-048  Bestehende Wachstumsphase bearbeiten
  TC-REQ-001-060  ->  TC-001-048  Wachstumsphase loeschen
  TC-REQ-001-063  ->  TC-001-047  Profile fuer Wachstumsphase anzeigen
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import SpeciesDetailPage, SpeciesListPage


@pytest.fixture
def species_list(browser: WebDriver, base_url: str) -> SpeciesListPage:
    return SpeciesListPage(browser, base_url)


@pytest.fixture
def species_detail(browser: WebDriver, base_url: str) -> SpeciesDetailPage:
    return SpeciesDetailPage(browser, base_url)


def _navigate_to_lifecycle_tab(
    species_list: SpeciesListPage,
    species_detail: SpeciesDetailPage,
) -> None:
    """Navigate to the 'Lebenszyklus-Konfiguration' tab of the first species.

    Both waits are keyed on content that must be present, not on the absence of
    a skeleton. With the weak wait this helper had a *silent-skip* hazard on top
    of the timing one: the URL commit does not mean the detail route rendered, so
    ``get_tab_labels()`` could return ``[]`` and every test routed through here
    skipped with "Lifecycle tab not found among []" -- an availability-shaped
    skip that is really "not loaded yet" (`e2e-test-stability` §A/§D).
    """
    species_list.open()
    if species_list.get_row_count() == 0:
        pytest.skip("No species in database")
    species_list.click_row(0)
    species_list.wait_for_url_contains("/stammdaten/species/")
    species_detail.wait_for_content(
        SpeciesDetailPage.TABS, "species detail tab bar (lifecycle navigation)"
    )
    tabs = species_detail.get_tab_labels()
    lifecycle_tab = next((i for i, t in enumerate(tabs) if "LEBENSZYKLUS" in t.upper()), None)
    if lifecycle_tab is None:
        pytest.skip(f"Lifecycle tab not found among {tabs}")
    species_detail.click_tab(lifecycle_tab)
    species_detail.wait_for_content(
        SpeciesDetailPage.LIFECYCLE_FORM_SUBMIT, "lifecycle configuration tab panel"
    )


def _provision_species_with_phase(
    species_list: SpeciesListPage,
    species_detail: SpeciesDetailPage,
    *,
    return_count: bool = False,
) -> "str | tuple[int, str]":
    """Create a species this test owns, with one manually created growth phase.

    Row 0 of a fresh seed is a *managed* (system) species: its growth phases come
    from a shared phase-sequence template, so the row renders neither the delete
    nor the profile action (``isManaged`` in ``GrowthPhaseListSection.tsx``).
    Any assertion about a per-phase action therefore needs a species with its own
    lifecycle config and a legacy, non-managed ``GrowthPhase``.

    Shared by TC-REQ-001-060 (delete) and TC-REQ-001-063 (profiles) so the two
    cannot drift apart -- and so the tautological assertion the latter used to
    carry could be replaced by a real one (#778 A8).

    Returns the provisioned phase's display name, or ``(phase_count, name)``
    when *return_count* is set.
    """
    unique = uuid.uuid4().hex[:6]
    scientific_name = f"Deletus e2e{unique}"
    phase_display_name = f"E2E Phase {unique}"

    species_list.open()
    species_list.click_create()
    species_list.fill_scientific_name(scientific_name)
    species_list.set_field("genus", "Deletus")
    species_list.submit_form()
    # Not `wait_for_loading_complete()`: that is satisfied by a skeleton which
    # has not mounted yet, i.e. exactly the frame the list is about to re-render
    # in -- and the `search()` below then captured its box out of a toolbar that
    # was seconds from being swapped (TC-REQ-001-060/063, nightly 2026-08-13).
    # The dialog being gone is a signal that can actually fail: it clears only
    # once the create POST resolved.
    species_list.wait_for_create_dialog_closed()

    species_list.click_row_by_name(scientific_name)
    species_list.wait_for_url_contains("/stammdaten/species/")
    # Same pairing as `_navigate_to_lifecycle_tab`: without a content-keyed wait
    # the tab read below can return `[]` and turn this into a skip that reads
    # like "the app has no lifecycle tab".
    species_detail.wait_for_content(SpeciesDetailPage.TABS, "provisioned species detail tab bar")

    tabs = species_detail.get_tab_labels()
    lifecycle_tab = next((i for i, t in enumerate(tabs) if "LEBENSZYKLUS" in t.upper()), None)
    if lifecycle_tab is None:
        pytest.skip(f"Lifecycle tab not found among {tabs}")
    species_detail.click_tab(lifecycle_tab)
    species_detail.wait_for_content(
        SpeciesDetailPage.LIFECYCLE_FORM_SUBMIT,
        "provisioned species lifecycle configuration tab panel",
    )

    species_detail.select_lifecycle_option("cycle_type", "Einjährig")
    species_detail.select_lifecycle_option("photoperiod_type", "Tagneutral")
    species_detail.click_lifecycle_save()
    species_detail.wait_for_loading_complete()

    if not species_detail.can_create_growth_phase():
        pytest.skip("Freshly provisioned species did not expose a phase-create button")

    initial_count = species_detail.get_phase_count()
    species_detail.click_phase_create()
    species_detail.fill_phase_form(
        name=f"e2e_phase_{unique}",
        display_name=phase_display_name,
        duration="7",
        order=str(initial_count),
    )
    species_detail.submit_phase_form()
    species_detail.wait_for_loading_complete()

    provisioned_count = species_detail.get_phase_count()
    if provisioned_count <= initial_count:
        pytest.skip("Self-provisioning failed: growth phase was not created")

    if return_count:
        return provisioned_count, phase_display_name
    return phase_display_name


class TestLifecycleConfigSection:
    """Lifecycle config CRUD (Spec: TC-001-047)."""

    @pytest.mark.smoke
    def test_display_lifecycle_config_tab(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-047: Display lifecycle config tab.

        Spec: TC-001-047 -- Lebenszyklus-Tab zeigt LifecycleConfig und GrowthPhases.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)
        screenshot("TC-REQ-001-051_lifecycle-tab", "Lifecycle config tab displayed")

        # The lifecycle tab should render with form fields
        submit_label = species_detail.get_lifecycle_submit_label()
        assert submit_label in ("Erstellen", "Speichern"), (
            f"TC-REQ-001-051 FAIL: Expected 'Erstellen' or 'Speichern', got '{submit_label}'"
        )

    @pytest.mark.core_crud
    def test_create_annual_lifecycle_config(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-047: Create a lifecycle config for an annual species.

        Spec: TC-001-047 -- Lifecycle-Config fuer einjaehrige Art erstellen.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Speichern":
            pytest.skip("Lifecycle config already exists")

        species_detail.select_lifecycle_option("cycle_type", "Einjährig")
        species_detail.select_lifecycle_option("photoperiod_type", "Tagneutral")
        screenshot(
            "TC-REQ-001-052_before-create", "Lifecycle config form filled for annual species"
        )

        species_detail.click_lifecycle_save()

        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-052_after-create", "Lifecycle config after creation")

        new_label = species_detail.get_lifecycle_submit_label()
        assert new_label == "Speichern", (
            f"TC-REQ-001-052 FAIL: After creation, button should show 'Speichern', got '{new_label}'"
        )

    @pytest.mark.core_crud
    def test_edit_existing_lifecycle_config(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-047: Edit an existing lifecycle config.

        Spec: TC-001-047 -- Bestehende Lifecycle-Config bearbeiten.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label != "Speichern":
            pytest.skip("No existing lifecycle config to edit")

        screenshot("TC-REQ-001-055_before-edit", "Lifecycle config before editing")
        species_detail.click_lifecycle_save()
        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-055_after-save", "Lifecycle config after saving")

        # Should remain on the same page
        assert "/stammdaten/species/" in species_detail.driver.current_url, (
            f"TC-REQ-001-055 FAIL: Should remain on species detail, got {species_detail.driver.current_url}"
        )


class TestGrowthPhaseManagement:
    """Growth phase CRUD (Spec: TC-001-048)."""

    @pytest.mark.smoke
    def test_growth_phases_section_visible(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-048: Growth phases section appears after lifecycle config creation.

        Spec: TC-001-048 -- Wachstumsphasen-Bereich nach Lifecycle-Erstellung sichtbar.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Erstellen":
            pytest.skip("No lifecycle config exists — phases section not visible")

        screenshot("TC-REQ-001-056_phases-section", "Growth phases section visible")

        assert species_detail.has_growth_phase_section(), (
            "TC-REQ-001-056 FAIL: Growth phases section should be visible"
        )

    @pytest.mark.core_crud
    def test_create_growth_phase(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-048: Create a growth phase via dialog.

        Spec: TC-001-048 -- Neue Wachstumsphase anlegen.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Erstellen":
            pytest.skip("No lifecycle config — cannot create phases")

        if not species_detail.can_create_growth_phase():
            pytest.skip("Growth phases not editable (no create button — e.g. system species)")

        initial_count = species_detail.get_phase_count()
        unique = uuid.uuid4().hex[:4]
        display_name = f"E2E Phase {unique}"

        species_detail.click_phase_create()
        species_detail.fill_phase_form(
            name=f"e2e_phase_{unique}",
            display_name=display_name,
            duration="7",
            order=str(initial_count),
        )
        screenshot("TC-REQ-001-057_phase-form-filled", f"Phase form filled for e2e_phase_{unique}")

        species_detail.submit_phase_form()
        # The exact post-condition of the create, replacing a
        # `wait_for_loading_complete()` that can return before the POST has even
        # been answered: the dialog closes only after
        # `await phasesApi.createGrowthPhase(...)` resolves 2xx.
        species_detail.wait_for_phase_dialog_closed()
        species_detail.wait_for_row_containing(
            display_name,
            rows_locator=SpeciesDetailPage.PHASE_TABLE_ROWS,
            what=f"growth phase table after creating {display_name!r}",
        )
        screenshot("TC-REQ-001-057_after-create", "Growth phases after creation")

        # Identity, not arithmetic. `new_count >= initial_count` is satisfied by
        # a create that was rejected, never submitted or answered 500 -- the
        # shape that kept four nutrient-plan tests green for 274 days while their
        # POSTs returned HTTP 500 (#956/#966). The display name carries a per-run
        # uuid, so nothing but this create can satisfy this.
        #
        # Read through the `name` *column* rather than through the row text the
        # wait above scanned: the two disagree exactly when the value landed in
        # some other cell, which a whole-row containment check cannot see.
        phase_names = species_detail.get_phase_names()
        assert any(display_name in name for name in phase_names), (
            f"TC-REQ-001-057 FAIL: The growth-phase table must name the phase just "
            f"created, {display_name!r}, in its `name` column, but that column reads "
            f"{phase_names!r} across {len(phase_names)} row(s) (it held {initial_count} "
            f"before). The dialog closed, so the POST returned 2xx and the row is "
            f"rendered -- so the display name is being rendered somewhere other than "
            f"the name column."
        )

    @pytest.mark.core_crud
    def test_edit_growth_phase(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-048: Edit an existing growth phase.

        Spec: TC-001-048 -- Bestehende Wachstumsphase bearbeiten.
        """
        _navigate_to_lifecycle_tab(species_list, species_detail)

        submit_label = species_detail.get_lifecycle_submit_label()
        if submit_label == "Erstellen":
            pytest.skip("No lifecycle config")

        if species_detail.get_phase_count() == 0:
            pytest.skip("No phases to edit")

        screenshot("TC-REQ-001-059_before-edit", "Growth phases before editing")
        species_detail.click_phase_row(0)
        species_detail.wait_for_loading_complete()

        # Edit dialog should open — wait for the dialog to appear
        if not species_detail.is_create_dialog_open():
            pytest.skip("Edit dialog did not open on phase row click")

        # Modify duration inside the dialog
        species_detail.set_field("typical_duration_days", "35")
        screenshot("TC-REQ-001-059_field-modified", "Phase duration changed to 35")

        species_detail.submit_phase_form()

        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-059_after-edit", "Growth phases after editing")

    @pytest.mark.core_crud
    def test_delete_growth_phase(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-048: Delete a growth phase.

        Spec: TC-001-048 -- Wachstumsphase loeschen.

        Row 0 of a fresh seed is a managed (system) species: its growth phases
        come from a shared phase-sequence template and hide the delete action
        (``isManaged`` in ``GrowthPhaseListSection.tsx:98/180``). Self-provision
        a fresh species with its own lifecycle config and one manually created
        phase (mirrors ``test_create_growth_phase``) so the phase is a legacy,
        non-managed ``GrowthPhase`` and the delete button is actually
        exercisable.
        """
        provisioned_count, _ = _provision_species_with_phase(
            species_list, species_detail, return_count=True
        )

        screenshot(
            "TC-REQ-001-060_before-delete",
            f"Growth phases before deletion ({provisioned_count} phases)",
        )

        species_detail.delete_phase_at_index(0)
        species_detail.confirm_delete()

        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-060_after-delete", "Growth phases after deletion")

        new_count = species_detail.get_phase_count()
        assert new_count < provisioned_count, (
            f"TC-REQ-001-060 FAIL: Expected fewer phases after delete: was {provisioned_count}, now {new_count}"
        )


class TestGrowthPhaseProfiles:
    """Growth phase profiles (Spec: TC-001-047)."""

    @pytest.mark.smoke
    def test_view_profiles_for_growth_phase(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-047: View profiles for a growth phase.

        Spec: TC-001-047 -- Profile fuer Wachstumsphase anzeigen.
        """
        # Row 0 of a fresh seed is a managed (system) species, whose phase rows
        # render no actions column at all (`isManaged` in
        # GrowthPhaseListSection.tsx) -- so the profile action can only be
        # asserted on a species this test owns. Same self-provisioning as
        # TC-REQ-001-060, which is why both now share a helper.
        provisioned = _provision_species_with_phase(species_list, species_detail)
        screenshot("TC-REQ-001-063_lifecycle-tab", "Lifecycle tab with phase profiles")

        # The old assertion here was `phase_count >= 0` -- true for every
        # possible table, and unreachable-by-failure anyway because the skip
        # above already guaranteed a non-zero count (#778 A8). What the case
        # actually claims is that a growth phase offers its profiles, which is
        # the per-phase `phase-profile-<key>` action.
        profile_keys = species_detail.get_phase_profile_keys()
        assert profile_keys, (
            "TC-REQ-001-063 FAIL: Expected the provisioned growth phase "
            f"'{provisioned}' to offer a profile action, but none of the "
            f"{species_detail.get_phase_count()} phase rows rendered one"
        )
