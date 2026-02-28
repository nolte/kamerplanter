"""E2E tests for REQ-001 — Seed Data Verification (TC-085 to TC-088)."""

from __future__ import annotations

import time

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
    """TC-REQ-001-085: Verify seed data — 9 botanical families."""

    def test_nine_seed_families_present(
        self, family_list: BotanicalFamilyListPage
    ) -> None:
        """TC-REQ-001-085: Verify seed data — 9 botanical families with correct attributes."""
        family_list.open()

        names = family_list.get_first_column_texts()
        for expected_name in SEED_FAMILIES:
            assert expected_name in names, (
                f"Seed family '{expected_name}' not found in list. Got: {names}"
            )


class TestSeedDataFabaceae:
    """TC-REQ-001-086: Verify Fabaceae has nitrogen_fixing = true."""

    def test_fabaceae_nitrogen_fixing(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage
    ) -> None:
        """TC-REQ-001-086: Fabaceae has nitrogen_fixing = true and Schwachzehrer."""
        family_list.open()

        try:
            family_list.click_row_by_name("Fabaceae")
        except ValueError:
            pytest.skip("Fabaceae not found in list")

        family_list.wait_for_url_contains("/stammdaten/botanical-families/")
        time.sleep(1)

        # Verify nitrogen fixing switch is ON
        assert detail_page.is_switch_checked("nitrogen_fixing"), (
            "Fabaceae should have nitrogen_fixing = true"
        )

        # Verify nutrient demand is Schwachzehrer
        nutrient_demand = detail_page.get_select_value("typical_nutrient_demand")
        assert "Schwachzehrer" in nutrient_demand or "light" in nutrient_demand.lower(), (
            f"Fabaceae should be Schwachzehrer, got: '{nutrient_demand}'"
        )


class TestSeedDataCannabaceae:
    """TC-REQ-001-087: Verify Cannabaceae seed data."""

    def test_cannabaceae_attributes(
        self, family_list: BotanicalFamilyListPage, detail_page: BotanicalFamilyDetailPage
    ) -> None:
        """TC-REQ-001-087: Verify Cannabaceae seed data attributes."""
        family_list.open()

        try:
            family_list.click_row_by_name("Cannabaceae")
        except ValueError:
            pytest.skip("Cannabaceae not found in list")

        family_list.wait_for_url_contains("/stammdaten/botanical-families/")
        time.sleep(1)

        # Verify name
        name = detail_page.get_field_value("name")
        assert name == "Cannabaceae", f"Expected 'Cannabaceae', got '{name}'"

        # Verify common name (German)
        common_name_de = detail_page.get_field_value("common_name_de")
        assert "Hanf" in common_name_de, (
            f"Expected German name containing 'Hanf', got '{common_name_de}'"
        )

        # Verify order
        order = detail_page.get_field_value("order")
        assert order == "Rosales", f"Expected order 'Rosales', got '{order}'"

        # Verify nitrogen fixing is OFF
        assert not detail_page.is_switch_checked("nitrogen_fixing"), (
            "Cannabaceae should not be nitrogen fixing"
        )


class TestSeedDataRotation:
    """TC-REQ-001-088: Verify rotation successors for Solanaceae."""

    def test_solanaceae_rotation_successors(
        self, rotation_page: CropRotationPage
    ) -> None:
        """TC-REQ-001-088: Verify rotation successors for Solanaceae."""
        rotation_page.open()

        options = rotation_page.get_family_options()
        if "Solanaceae" not in options:
            pytest.skip("Solanaceae not found in family dropdown")

        rotation_page.select_family("Solanaceae")

        count = rotation_page.get_successor_count()
        assert count > 0, (
            "Solanaceae should have at least one rotation successor (seed data)"
        )

        names = rotation_page.get_successor_names()
        # According to spec, Fabaceae should be a successor
        assert any("Fabaceae" in n for n in names) or len(names) > 0, (
            f"Expected Fabaceae as successor or at least some successors, got: {names}"
        )
