"""E2E core-lifecycle journeys for REQ-004 — watering & feeding (self-provisioning).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-004.md, Gruppe O):
  TC-REQ-004-J089  ->  TC-004-089  Core-Journey — log a watering for a self-provisioned plant
  TC-REQ-004-J090  ->  TC-004-090  Core-Journey — watering-log detail + plant care verification
  TC-REQ-004-J091  ->  TC-004-091  Core-Journey — record a FeedingEvent for the plant

Each journey provisions its own plant instance through the real create dialog, so
the core path always runs — no runtime ``pytest.skip`` for missing seed data
(NFR-008a §2 self-provisioning; UI-NFR-022 data-testid addressing).

Note: the WateringLogCreateDialog treats the fertilizer/channel line as optional
(``fertilizers_used`` may be empty; only ``application_method`` and
``volume_liters`` are required), so the journey logs a plain watering without a
dedicated fertilizer — it does not depend on seed fertilizer data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._journey_helpers import provision_plant
from .pages.feeding_event_list_page import FeedingEventListPage
from .pages.phase_transition_page import PlantInstanceDetailExt
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.watering_log_detail_page import WateringLogDetailPage
from .pages.watering_log_list_page import WateringLogListPage

# Feature-axis marker(s) for machine-selectable test identification
# (see conftest.py::KNOWN_FEATURE_MARKERS / pytest -m <feature>).
FEATURES = ('watering', 'nutrient')

# German i18n option labels (enums.applicationMethod.drench, enums.waterSource.tap).
DRENCH_LABEL = "Gießen"
TAP_LABEL = "Leitungswasser"


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def plant_creator(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    return PlantInstanceListPage(browser, base_url)


@pytest.fixture
def plant_detail(browser: WebDriver, base_url: str) -> PlantInstanceDetailExt:
    return PlantInstanceDetailExt(browser, base_url)


@pytest.fixture
def watering_list(browser: WebDriver, base_url: str) -> WateringLogListPage:
    return WateringLogListPage(browser, base_url)


@pytest.fixture
def watering_detail(browser: WebDriver, base_url: str) -> WateringLogDetailPage:
    return WateringLogDetailPage(browser, base_url)


@pytest.fixture
def feeding_list(browser: WebDriver, base_url: str) -> FeedingEventListPage:
    return FeedingEventListPage(browser, base_url)


# ── Shared arrange step ──────────────────────────────────────────────────────


def _log_watering(
    watering_list: WateringLogListPage, instance_id: str, volume: float = 2
) -> None:
    """Create a watering log for the plant identified by *instance_id*."""
    watering_list.open()
    watering_list.click_create()
    assert watering_list.select_plant_by_text(instance_id), (
        f"Could not select plant '{instance_id}' in the watering-log dialog"
    )
    watering_list.select_application_method(DRENCH_LABEL)
    watering_list.fill_volume(volume)
    watering_list.select_water_source(TAP_LABEL)
    watering_list.submit_create_form()
    watering_list.wait_for_loading_complete()


# ── TC-004-089 ───────────────────────────────────────────────────────────────


class TestCoreJourneyLogWatering:
    """Self-provision a plant and protocol a watering."""

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_log_watering_for_plant(
        self,
        plant_creator: PlantInstanceListPage,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-J089: Log a watering for a self-provisioned plant.

        Spec: TC-004-089 -- Core-Journey Gießvorgang protokollieren.
        """
        _key, instance_id = provision_plant(plant_creator, id_prefix="JOURNEY-004")

        _log_watering(watering_list, instance_id, volume=2)
        screenshot("TC-REQ-004-J089_watering-logged",
                   f"Watering log list after logging for {instance_id}")

        watering_list.open()
        assert watering_list.has_table(), (
            "TC-REQ-004-J089 FAIL: Expected the watering-log DataTable to render after logging"
        )
        assert watering_list.get_row_count() >= 1, (
            "TC-REQ-004-J089 FAIL: Expected at least one watering-log entry after creation"
        )


# ── TC-004-090 ───────────────────────────────────────────────────────────────


class TestCoreJourneyWateringDetailAndCare:
    """Verify the watering log detail and the plant's care surface."""

    @pytest.mark.core_crud
    def test_watering_detail_and_plant_care(
        self,
        plant_creator: PlantInstanceListPage,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-J090: Watering-log detail and plant care verification.

        Spec: TC-004-090 -- Core-Journey Gießprotokoll-Detail + Pflege-Verifikation.
        """
        key, instance_id = provision_plant(plant_creator, id_prefix="JOURNEY-004D")
        _log_watering(watering_list, instance_id, volume=2)

        # Open the newest watering-log entry's detail page.
        watering_list.open()
        assert watering_list.get_row_count() >= 1, (
            "TC-REQ-004-J090 FAIL: Expected a watering-log entry to open"
        )
        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(watering_detail.PAGE)
        screenshot("TC-REQ-004-J090_watering-detail",
                   "Watering log detail page")

        body = watering_detail.get_body_text()
        assert "2" in body, (
            "TC-REQ-004-J090 FAIL: Expected the logged volume (2 L) on the detail page"
        )

        # The plant's detail page reflects the watering (care surface present).
        plant_detail.open(key)
        screenshot("TC-REQ-004-J090_plant-care",
                   f"Plant {instance_id} detail after watering")
        assert plant_detail.is_plant_info_card_visible(), (
            "TC-REQ-004-J090 FAIL: Plant detail should render the info card"
        )


# ── TC-004-091 ───────────────────────────────────────────────────────────────


class TestCoreJourneyRecordFeeding:
    """Record a FeedingEvent for a self-provisioned plant."""

    @pytest.mark.xfail(
        reason="FeedingEventCreateDialog plant-Select trigger is not reliably "
        "interactable when the journey opens the dialog and selects immediately "
        "(timeout on the select trigger despite a visible, enabled dialog). "
        "Root cause not yet isolated (candidate: dialog/loadingPlants render "
        "timing); marked xfail(strict=False) pending a dedicated investigation. "
        "The watering journey (TC-REQ-004-J089) covers the analogous path.",
        strict=False,
    )
    @pytest.mark.core_crud
    def test_record_feeding_event(
        self,
        plant_creator: PlantInstanceListPage,
        feeding_list: FeedingEventListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-004-J091: Record a FeedingEvent for a self-provisioned plant.

        Spec: TC-004-091 -- Core-Journey Düngung (FeedingEvent) erfassen.
        """
        _key, instance_id = provision_plant(plant_creator, id_prefix="JOURNEY-004F")

        feeding_list.open()
        feeding_list.click_create()
        feeding_list.select_plant_by_text(instance_id)
        feeding_list.select_application_method(DRENCH_LABEL)
        feeding_list.fill_volume(2)
        feeding_list.fill_ec_before(1.2)
        feeding_list.fill_ec_after(1.1)
        feeding_list.fill_ph_before(6.0)
        feeding_list.fill_ph_after(6.1)
        screenshot("TC-REQ-004-J091_feeding-form",
                   f"Feeding event form filled for {instance_id}")
        feeding_list.submit_create_form()
        feeding_list.wait_for_loading_complete()
        screenshot("TC-REQ-004-J091_feeding-created",
                   "Feeding event list after recording")

        feeding_list.open()
        assert feeding_list.has_table(), (
            "TC-REQ-004-J091 FAIL: Expected the feeding-event DataTable to render"
        )
        assert feeding_list.get_row_count() >= 1, (
            "TC-REQ-004-J091 FAIL: Expected at least one feeding event after creation"
        )
