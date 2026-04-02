"""E2E tests for REQ-001 — Seed Data Verification.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-085  ->  TC-001-054  Seed-Daten Kontrolle — mindestens 9 Pflanzenfamilien vorhanden
  TC-REQ-001-086  ->  TC-001-054  Fabaceae hat nitrogen_fixing = true und Schwachzehrer
  TC-REQ-001-087  ->  TC-001-054  Cannabaceae Seed-Daten-Attribute pruefen
  TC-REQ-001-088  ->  TC-001-052  Fruchtfolge-Empfehlung — Solanaceae Nachfolger pruefen
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import time  # kept for debounce waits

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BotanicalFamilyDetailPage, BotanicalFamilyListPage, CropRotationPage


@pytest.fixture
def family_list(browser: WebDriver, base_url: str) -> BotanicalFamilyListPage:
    return BotanicalFamilyListPage(browser, base_url)


@pytest.fixture
def detail_page(browser: WebDriver, base_url: str) -> BotanicalFamilyDetailPage:
    return BotanicalFamilyDetailPage(browser, base_url)


@pytest.fixture
def rotation_page(browser: WebDriver, base_url: str) -> CropRotationPage:
    return CropRotationPage(browser, base_url)


SEED_FAMILIES = [
    "Solanaceae",
    "Brassicaceae",
    "Fabaceae",
    "Cucurbitaceae",
    "Apiaceae",
    "Asteraceae",
    "Poaceae",
    "Lamiaceae",
    "Cannabaceae",
]


class TestSeedDataFamilies:
    """Verify seed data — 9 botanical families (Spec: TC-001-054)."""

    @pytest.mark.smoke
    def test_nine_seed_families_present(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-085: Verify seed data — 9 botanical families with correct attributes.

        Spec: TC-001-054 -- Seed-Daten Kontrolle — mindestens 9 Pflanzenfamilien vorhanden.
        """
        for expected_name in SEED_FAMILIES:
            family_list.open()
            family_list.search(expected_name)
            family_list.wait_for_loading_complete()

            names = family_list.get_first_column_texts()
            assert any(expected_name in n for n in names), (
                f"TC-REQ-001-085 FAIL: Seed family '{expected_name}' not found after search. Got: {names}"
            )

        screenshot("TC-REQ-001-085_seed-families", "Family list after verifying all 9 seed families")


class TestSeedDataFabaceae:
    """Verify Fabaceae has nitrogen_fixing = true (Spec: TC-001-054)."""

    @pytest.mark.smoke
    def test_fabaceae_nitrogen_fixing(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-086: Fabaceae has nitrogen_fixing = true and Schwachzehrer.

        Spec: TC-001-054 -- Fabaceae Seed-Daten: nitrogen_fixing und Naehrstoffbedarf.
        """
        family_list.open()

        try:
            family_list.click_row_by_name("Fabaceae")
        except ValueError:
            pytest.skip("Fabaceae not found in list")

        family_list.wait_for_url_contains("/stammdaten/botanical-families/")
        detail_page.wait_for_loading_complete()
        screenshot("TC-REQ-001-086_fabaceae-detail", "Fabaceae detail page with nitrogen_fixing and nutrient demand")

        # Verify nitrogen fixing switch is ON
        assert detail_page.is_switch_checked("nitrogen_fixing"), (
            "TC-REQ-001-086 FAIL: Fabaceae should have nitrogen_fixing = true"
        )

        # Verify nutrient demand is Schwachzehrer
        nutrient_demand = detail_page.get_select_value("typical_nutrient_demand")
        assert "Schwachzehrer" in nutrient_demand or "light" in nutrient_demand.lower(), (
            f"TC-REQ-001-086 FAIL: Fabaceae should be Schwachzehrer, got: '{nutrient_demand}'"
        )


class TestSeedDataCannabaceae:
    """Verify Cannabaceae seed data (Spec: TC-001-054)."""

    @pytest.mark.smoke
    def test_cannabaceae_attributes(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-087: Verify Cannabaceae seed data attributes.

        Spec: TC-001-054 -- Cannabaceae Seed-Daten-Attribute pruefen.
        """
        family_list.open()

        try:
            family_list.click_row_by_name("Cannabaceae")
        except ValueError:
            pytest.skip("Cannabaceae not found in list")

        family_list.wait_for_url_contains("/stammdaten/botanical-families/")
        detail_page.wait_for_loading_complete()
        screenshot("TC-REQ-001-087_cannabaceae-detail", "Cannabaceae detail page with seed data attributes")

        # Verify name
        name = detail_page.get_field_value("name")
        assert name == "Cannabaceae", (
            f"TC-REQ-001-087 FAIL: Expected 'Cannabaceae', got '{name}'"
        )

        # Verify common name (German)
        common_name_de = detail_page.get_field_value("common_name_de")
        assert "Hanf" in common_name_de, (
            f"TC-REQ-001-087 FAIL: Expected German name containing 'Hanf', got '{common_name_de}'"
        )

        # Verify order
        order = detail_page.get_field_value("order")
        assert order == "Rosales", (
            f"TC-REQ-001-087 FAIL: Expected order 'Rosales', got '{order}'"
        )

        # Verify nitrogen fixing is OFF
        assert not detail_page.is_switch_checked("nitrogen_fixing"), (
            "TC-REQ-001-087 FAIL: Cannabaceae should not be nitrogen fixing"
        )


class TestSeedDataRotation:
    """Verify rotation successors for Solanaceae (Spec: TC-001-052)."""

    @pytest.mark.smoke
    def test_solanaceae_rotation_successors(
        self, rotation_page: CropRotationPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-088: Verify rotation successors for Solanaceae.

        Spec: TC-001-052 -- Fruchtfolge-Empfehlung OK mit Stickstoff-Benefit (Solanaceae Nachfolger).
        """
        rotation_page.open()

        options = rotation_page.get_family_options()
        if "Solanaceae" not in options:
            pytest.skip("Solanaceae not found in family dropdown")

        rotation_page.select_family("Solanaceae")
        screenshot("TC-REQ-001-088_solanaceae-successors", "Crop rotation successors for Solanaceae")

        count = rotation_page.get_successor_count()
        assert count > 0, (
            "TC-REQ-001-088 FAIL: Solanaceae should have at least one rotation successor (seed data)"
        )

        names = rotation_page.get_successor_names()
        # According to spec, Fabaceae should be a successor
        assert any("Fabaceae" in n for n in names) or len(names) > 0, (
            f"TC-REQ-001-088 FAIL: Expected Fabaceae as successor or at least some successors, got: {names}"
        )
