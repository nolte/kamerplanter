"""E2E core-lifecycle journeys for REQ-001 — plant instance create & edit (self-provisioning).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md, Gruppe 21):
  TC-REQ-001-J079  ->  TC-001-079  Core-Journey preparation — create test species + cultivar
  TC-REQ-001-J080  ->  TC-001-080  Core-Journey — create plant instance, verify in list + detail
  TC-REQ-001-J081  ->  TC-001-081  Core-Journey — edit plant core attributes, verify persistence

These journeys provision their own preconditions through the real UI, so the
core path always runs — no runtime ``pytest.skip`` for missing seed data
(NFR-008a §2 self-provisioning; UI-NFR-022 data-testid addressing).

Note on TC-001-079: the spec's illustrative scientific name
``Solanum lycopersicum 'Journey'`` embeds a cultivar quote that the species
name validator rejects; the journey uses a clean, unique binomial instead and
adds the cultivar 'Journey-01' via the species detail Cultivars tab. Selecting a
botanical family is optional in the create dialog, so the journey does not depend
on a specific seed family.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._journey_helpers import provision_plant, unique_suffix
from .pages.phase_transition_page import PlantInstanceDetailExt
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.species_detail_page import SpeciesDetailPage
from .pages.species_list_page import SpeciesListPage

# Feature-axis marker(s) for machine-selectable test identification
# (see conftest.py::KNOWN_FEATURE_MARKERS / pytest -m <feature>).
FEATURES = ("plant",)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def species_list(browser: WebDriver, base_url: str) -> SpeciesListPage:
    return SpeciesListPage(browser, base_url)


@pytest.fixture
def species_detail(browser: WebDriver, base_url: str) -> SpeciesDetailPage:
    return SpeciesDetailPage(browser, base_url)


@pytest.fixture
def plant_list(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    return PlantInstanceListPage(browser, base_url)


@pytest.fixture
def plant_detail(browser: WebDriver, base_url: str) -> PlantInstanceDetailExt:
    return PlantInstanceDetailExt(browser, base_url)


# ── TC-001-079 ───────────────────────────────────────────────────────────────


class TestCoreJourneySpeciesAndCultivar:
    """Prepare the journey by self-provisioning a test species and cultivar."""

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_create_test_species_and_cultivar(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-J079: Create a test species and a cultivar via the UI.

        Spec: TC-001-079 -- Core-Journey Vorbereitung (self-provisioning).
        """
        suffix = unique_suffix()
        scientific_name = f"Solanum journey{suffix}"
        cultivar_name = f"Journey-01-{suffix}"

        species_list.open()
        species_list.click_create()
        species_list.fill_scientific_name(scientific_name)
        species_list.set_field("genus", "Solanum")
        screenshot(
            "TC-REQ-001-J079_species-form-filled",
            "Species create dialog with scientific name filled",
        )
        species_list.submit_form()
        species_list.wait_for_loading_complete()

        # Locate the new species and open its detail page.
        species_list.open()
        species_list.click_row_by_name(scientific_name)
        species_list.wait_for_url_contains("/stammdaten/species/")
        screenshot(
            "TC-REQ-001-J079_species-detail",
            "Species detail page after creation",
        )

        # Create a cultivar — click_cultivar_create() switches to the "Sorten"
        # tab itself (it is no longer at a fixed low tab index).
        species_detail.click_cultivar_create()
        species_detail.fill_cultivar_form(cultivar_name)
        screenshot(
            "TC-REQ-001-J079_cultivar-form",
            "Cultivar create dialog with name filled",
        )
        species_detail.submit_cultivar_form()
        species_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-J079_cultivar-created",
            "Species Cultivars tab after creating the journey cultivar",
        )

        names = species_detail.get_cultivar_names()
        assert any(cultivar_name in n for n in names), (
            f"TC-REQ-001-J079 FAIL: Expected cultivar '{cultivar_name}' in the "
            f"Cultivars tab, got {names}"
        )


# ── TC-001-080 ───────────────────────────────────────────────────────────────


class TestCoreJourneyCreatePlantInstance:
    """Self-provision a plant instance and verify it in list + detail."""

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_create_plant_instance_and_verify(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-J080: Create a plant instance and verify list + detail.

        Spec: TC-001-080 -- Core-Journey Anlage (self-provisioning).
        """
        key, instance_id = provision_plant(plant_list, id_prefix="JOURNEY-001")
        screenshot(
            "TC-REQ-001-J080_plant-detail",
            "Plant instance detail page after self-provisioning",
        )

        assert "/pflanzen/plant-instances/" in plant_detail.driver.current_url, (
            "TC-REQ-001-J080 FAIL: Expected to land on the plant instance detail page"
        )
        assert plant_detail.is_plant_info_card_visible(), (
            f"TC-REQ-001-J080 FAIL: plant-info-card should be visible for '{instance_id}'"
        )
        phase_text = plant_detail.get_current_phase()
        assert phase_text, (
            f"TC-REQ-001-J080 FAIL: Expected a non-empty current phase for '{instance_id}'"
        )

        # Also visible in the list view.
        plant_list.open()
        plant_list.search(instance_id)
        plant_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-J080_plant-in-list",
            "Plant instance list filtered to the new plant",
        )
        assert plant_list.get_row_count() >= 1, (
            f"TC-REQ-001-J080 FAIL: Plant '{instance_id}' should be listed (key={key})"
        )


# ── TC-001-081 ───────────────────────────────────────────────────────────────


class TestCoreJourneyEditPlantInstance:
    """Self-provision a plant, edit its display name and verify persistence."""

    @pytest.mark.core_crud
    def test_edit_plant_name_persists(
        self,
        plant_list: PlantInstanceListPage,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-J081: Edit the plant display name and verify after reload.

        Spec: TC-001-081 -- Core-Journey Bearbeitung + Persistenz.
        """
        key, instance_id = provision_plant(plant_list, id_prefix="JOURNEY-001E")
        new_name = f"Journey-Tomate A {unique_suffix()}"

        plant_detail.open(key)
        plant_detail.open_edit_tab()
        plant_detail.set_edit_plant_name(new_name)
        screenshot(
            "TC-REQ-001-J081_edit-form",
            "Plant instance edit tab with new display name",
        )
        plant_detail.submit_edit()
        plant_detail.wait_for_loading_complete()

        # Reload the detail page to prove the change persisted server-side.
        plant_detail.open(key)
        screenshot(
            "TC-REQ-001-J081_after-reload",
            "Plant instance detail page after reload showing new name",
        )
        assert new_name in plant_detail.get_body_text(), (
            f"TC-REQ-001-J081 FAIL: Expected display name '{new_name}' to persist "
            f"after reload for plant '{instance_id}'"
        )
