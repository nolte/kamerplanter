"""E2E tests for REQ-007 — Erntemanagement: HarvestReadinessCard.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-007.md):
  TC-REQ-007-030  ->  TC-007-035  Erntereife-Karte zeigt Gesamtscore mit Fortschrittsbalken
  TC-REQ-007-031  ->  TC-007-036  Erntereife-Karte zeigt Empfehlungs-Chip
  TC-REQ-007-032  ->  TC-007-037  Erntereife-Karte zeigt Indikator-Aufschluesselungstabelle

Note: The HarvestReadinessCard is embedded in the plant detail page and requires
a plant with readiness data. If no such data exists, tests are skipped.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.harvest_readiness_card_page import HarvestReadinessCardPage

# Feature-axis marker(s) for machine-selectable test identification
# (see conftest.py::KNOWN_FEATURE_MARKERS / pytest -m <feature>).
FEATURES = ("harvest",)


# -- Fixtures ---------------------------------------------------------------


@pytest.fixture
def readiness_card(browser: WebDriver, base_url: str) -> HarvestReadinessCardPage:
    """Return a HarvestReadinessCardPage bound to the test browser."""
    return HarvestReadinessCardPage(browser, base_url)


def _navigate_to_first_plant_detail(readiness_card: HarvestReadinessCardPage) -> None:
    """Navigate to the first plant instance detail page via list click."""
    if not readiness_card.open_first_plant_detail_via_list():
        pytest.skip("No plant instances -- cannot test readiness card")


# -- Tests ------------------------------------------------------------------


class TestHarvestReadinessCard:
    """HarvestReadinessCard display and behavior (Spec: TC-007-035, TC-007-036, TC-007-037)."""

    @pytest.mark.core_crud
    def test_readiness_card_displays_score(
        self,
        readiness_card: HarvestReadinessCardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-030: Readiness card shows overall score with progress bar.

        Spec: TC-007-035 -- Erntereife-Karte zeigt Gesamtscore mit Fortschrittsbalken.
        """
        _navigate_to_first_plant_detail(readiness_card)
        screenshot(
            "TC-REQ-007-030_plant-detail-for-readiness",
            "Plant detail page for readiness card check",
        )

        if not readiness_card.is_card_visible():
            pytest.skip(
                "No HarvestReadinessCard visible on plant detail -- "
                "readiness data may not exist for this plant"
            )

        screenshot(
            "TC-REQ-007-030_readiness-card",
            "Harvest readiness card visible with score",
        )

        assert readiness_card.has_score_value(), (
            "TC-REQ-007-030 FAIL: Expected overall score value in readiness card"
        )
        assert readiness_card.has_progress_bar(), (
            "TC-REQ-007-030 FAIL: Expected LinearProgress in readiness card"
        )

    @pytest.mark.core_crud
    def test_readiness_card_recommendation_chip(
        self,
        readiness_card: HarvestReadinessCardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-031: Readiness card shows recommendation chip.

        Spec: TC-007-036 -- Empfehlungs-Chip (optimal/approaching/developing).
        """
        _navigate_to_first_plant_detail(readiness_card)

        if not readiness_card.is_card_visible():
            pytest.skip("No HarvestReadinessCard visible on plant detail")

        chip = readiness_card.get_recommendation_chip()
        screenshot(
            "TC-REQ-007-031_readiness-recommendation",
            "Readiness card recommendation chip",
        )

        assert chip is not None, (
            "TC-REQ-007-031 FAIL: Expected recommendation chip in readiness card"
        )

        # Verify chip has an appropriate MUI color class
        classes = readiness_card.get_recommendation_chip_classes()
        valid_colors = ["Success", "Warning", "Info", "Error"]
        has_color = any(c.lower() in classes.lower() for c in valid_colors)
        assert has_color, (
            f"TC-REQ-007-031 FAIL: Expected recommendation chip to have a "
            f"MUI color class, got: {classes}"
        )

    @pytest.mark.core_crud
    def test_readiness_card_indicator_table(
        self,
        readiness_card: HarvestReadinessCardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-032: Readiness card shows indicator breakdown table.

        Spec: TC-007-037 -- Indikator-Aufschluesselungstabelle.
        """
        _navigate_to_first_plant_detail(readiness_card)

        if not readiness_card.is_card_visible():
            pytest.skip("No HarvestReadinessCard visible on plant detail")

        screenshot(
            "TC-REQ-007-032_readiness-indicators",
            "Readiness card indicator breakdown table",
        )

        if not readiness_card.has_indicator_table():
            # Indicator table is only shown when indicators exist
            pytest.skip("No indicator breakdown table -- indicators may be empty")

        assert readiness_card.get_indicator_row_count() > 0, (
            "TC-REQ-007-032 FAIL: Expected at least one indicator row in the breakdown table"
        )
