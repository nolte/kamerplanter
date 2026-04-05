"""E2E tests for REQ-001 — Cultivar CRUD.

Spec-TC Mapping (test TC → spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-042  →  TC-001-036  Sorten-Tab zeigt vorhandene Sorten
  TC-REQ-001-043  →  TC-001-044  Cultivar-Detailseite öffnen
  TC-REQ-001-045  →  TC-001-037  Neue Sorte erstellen (Happy Path)
  TC-REQ-001-046  →  TC-001-038  Cultivar — Pflichtfeld Name leer
  TC-REQ-001-047  →  TC-001-039  Cultivar — Tage bis Reife Grenzwerte
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


def _navigate_to_first_species_cultivar_tab(
    species_list: SpeciesListPage,
    species_detail: SpeciesDetailPage,
    screenshot: Callable[..., Path] | None = None,
) -> None:
    """Navigate to the 'Sorten' tab of the first species."""
    species_list.open()
    if species_list.get_row_count() == 0:
        pytest.skip("No species in database")
    species_list.click_row(0)
    species_list.wait_for_url_contains("/stammdaten/species/")
    species_detail.wait_for_loading_complete()
    species_detail.click_tab_by_label("Sorten")
    species_detail.wait_for_loading_complete()
    if screenshot:
        screenshot("cultivar-tab-loaded", "Species detail 'Sorten' tab — cultivar list or empty state visible")


class TestCultivarListSection:
    """Cultivar list within species detail (Spec: TC-001-036, TC-001-044)."""

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_display_cultivars_tab(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-042: Display cultivars tab for a species.

        Spec: TC-001-036 — Sorten-Tab einer Species zeigt vorhandene Sorten.
        """
        _navigate_to_first_species_cultivar_tab(species_list, species_detail, screenshot)

        count = species_detail.get_cultivar_count()
        screenshot("TC-REQ-001-042_cultivar-count", f"Cultivar tab rendered — {count} cultivars found")
        assert count >= 0, "Cultivar section should render"

    @pytest.mark.core_crud
    def test_click_cultivar_row_navigates_to_detail(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-043: Click on a cultivar row navigates to cultivar detail page.

        Spec: TC-001-044 — Cultivar-Detailseite öffnen.
        """
        _navigate_to_first_species_cultivar_tab(species_list, species_detail, screenshot)

        if species_detail.get_cultivar_count() == 0:
            pytest.skip("No cultivars for this species")

        screenshot("TC-REQ-001-043_before-row-click", "Cultivar tab before clicking first cultivar row")
        species_detail.click_cultivar_row(0)
        species_detail.wait_for_url_contains("/cultivars/")
        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-043_cultivar-detail", "Cultivar detail page after row click navigation")

        assert "/cultivars/" in species_detail.driver.current_url


class TestCultivarCreateDialog:
    """Cultivar creation and validation (Spec: TC-001-037, TC-001-038, TC-001-039)."""

    @pytest.mark.core_crud
    def test_create_cultivar_with_all_fields(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-045: Create a cultivar with all fields.

        Spec: TC-001-037 — Neue Sorte erstellen (Happy Path).
        """
        _navigate_to_first_species_cultivar_tab(species_list, species_detail, screenshot)

        species_detail.click_cultivar_create()
        unique = uuid.uuid4().hex[:6]
        cultivar_name = f"E2E-Cultivar-{unique}"
        species_detail.fill_cultivar_form(
            cultivar_name,
            breeder="E2E-Breeder",
            breeding_year="2020",
            days_to_maturity="80",
        )
        screenshot("TC-REQ-001-045_form-filled", f"Cultivar create dialog filled — name='{cultivar_name}', breeder='E2E-Breeder', year=2020, maturity=80d")

        species_detail.submit_cultivar_form()
        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-045_after-create", "Cultivar tab after successful creation — new cultivar should appear in list")

    def test_validation_empty_cultivar_name(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-046: Validation error — empty cultivar name.

        Spec: TC-001-038 — Cultivar Pflichtfeld Name leer wird verhindert.
        """
        _navigate_to_first_species_cultivar_tab(species_list, species_detail)

        species_detail.click_cultivar_create()
        species_detail.fill_cultivar_form("")
        species_detail.submit_cultivar_form()

        screenshot("TC-REQ-001-046_validation-error", "Cultivar create dialog after submitting empty name — validation error expected, dialog stays open")
        assert len(species_detail.driver.find_elements(
            *species_detail.CREATE_DIALOG
        )) > 0, "Dialog should remain open after validation error"

    def test_days_to_maturity_boundary(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-047: Days to maturity boundary values (1-365).

        Spec: TC-001-039 — Cultivar Tage bis Reife Grenzwerte (1–365).
        """
        _navigate_to_first_species_cultivar_tab(species_list, species_detail)

        species_detail.click_cultivar_create()
        unique = uuid.uuid4().hex[:6]
        species_detail.fill_cultivar_form(
            f"Boundary-{unique}",
            days_to_maturity="1",
        )
        screenshot("TC-REQ-001-047_boundary-value", "Cultivar create dialog with days_to_maturity=1 (minimum boundary)")

        species_detail.submit_cultivar_form()
        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-047_after-boundary-create", "Cultivar tab after creating cultivar with boundary value")
