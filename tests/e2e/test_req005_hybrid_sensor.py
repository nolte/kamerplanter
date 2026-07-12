"""E2E tests for REQ-005 — Hybrid-Sensorik.

Spec reference: ``spec/req/REQ-005_Hybrid-Sensorik.md``

Hybrid-Sensorik registers sensors from four data-source tiers (automatic IoT/MQTT
-> semi-automatic Home Assistant REST -> weather APIs -> manual) and tracks the
provenance of every reading.  The most user-facing entry point is the
``SensorCreateDialog`` reachable from a Site or Location detail page (and
optionally a Tank detail page).

This file covers the smoke-level scenarios that the audit
(``tests/e2e/test_req005_*.py`` glob) requires:

* TC-REQ-005-001  Standortdetail-Seite zeigt den ``Sensor hinzufuegen``-Button
                  (Acceptance: REQ-005 §1 -- Sensoren werden auf Standortebene
                  verwaltet).
* TC-REQ-005-002  Klick oeffnet den SensorCreateDialog mit allen Pflichtfeldern
                  fuer manuelle Anlage (Acceptance: REQ-005 §1 -- 4-Quellen-
                  Fallback-Kette inkl. ``manual``; UI muss die Anlage einer
                  manuell-gespeisten Sensor-Quelle erlauben).
* TC-REQ-005-003  Smoke flow: Sensor anlegen, Dialog schliesst, neue Zeile in
                  der Sensor-Tabelle sichtbar (Acceptance: REQ-005 §1 / Szenario 3
                  -- manuelle Eingabe wird mit Provenance gespeichert und in der
                  Liste angezeigt).

Uebrige Quellen-Tiers (HA-Auto, MQTT-Auto, Wetter-API) werden in REQ-005 §1
beschrieben; ihre End-to-End-Verifikation erfordert externe Systeme (HA / MQTT /
DWD) und wird nicht in der Selenium-Smoke-Suite getestet.

TODO[FIXME-DataTestId]: Provenance-Badges (``data-testid='provenance-badge'``)
sind in der aktuellen Frontend-Implementierung noch nicht vorhanden.  Sobald die
UI Provenance-Indikatoren rendert (Hauptabhaengigkeit zu REQ-018), ergaenzen wir
hier einen ``test_sensor_row_shows_provenance_badge``-Fall.  Production-Code
wird in dieser Aenderung *nicht* angefasst -- der Hinweis dient ausschliesslich
zur spaeteren Erweiterung der E2E-Coverage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.sensor_create_dialog_page import SensorCreateDialogPage
from .pages.site_detail_page import SiteDetailPage
from .pages.site_list_page import SiteListPage


# Site name created by the session-scoped ``e2e_seed_data`` fixture in conftest.py
SEEDED_SITE_NAME = "E2E-Sonnengarten"


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def site_list(browser: WebDriver, base_url: str) -> SiteListPage:
    """Return a SiteListPage bound to the test browser."""
    return SiteListPage(browser, base_url)


@pytest.fixture
def site_detail(browser: WebDriver, base_url: str) -> SiteDetailPage:
    """Return a SiteDetailPage bound to the test browser."""
    return SiteDetailPage(browser, base_url)


@pytest.fixture
def sensor_dialog(browser: WebDriver, base_url: str) -> SensorCreateDialogPage:
    """Return a SensorCreateDialogPage bound to the test browser."""
    return SensorCreateDialogPage(browser, base_url)


@pytest.fixture
def opened_site_detail(
    site_list: SiteListPage,
    site_detail: SiteDetailPage,
) -> SiteDetailPage:
    """Open the seeded ``E2E-Sonnengarten`` site via the list page.

    Falls back to the first available site if the seeded one is not present
    (defensive: keeps the smoke suite green on a fresh light-mode environment
    that still seeds at least one site).
    """
    site_list.open()

    if site_list.get_row_count() == 0:
        pytest.skip("No sites available -- e2e_seed_data did not seed a site")

    target_index = site_list.find_row_index_by_text(SEEDED_SITE_NAME)
    if target_index == -1:
        target_index = 0

    site_list.click_row(target_index)

    # Wait until the SiteDetailPage is loaded (URL change + page title visible)
    site_detail.wait_for_url_contains("/standorte/sites/")
    site_detail.wait_for_element_visible(SiteDetailPage.PAGE_TITLE)
    site_detail._wait_for_skeleton_gone()
    return site_detail


# ── TC-REQ-005-001: Sensors section is visible on Site detail ───────────────


class TestSensorsSectionVisibility:
    """The Site detail page exposes the sensor management entry point.

    Spec: REQ-005 §1 -- Sensoren werden in der Standort-Detailansicht angelegt.
    """

    @pytest.mark.smoke
    def test_add_sensor_button_visible_on_site_detail(
        self,
        opened_site_detail: SiteDetailPage,
        sensor_dialog: SensorCreateDialogPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-005-001: ``add-sensor-button`` is reachable from the Site detail.

        Spec: REQ-005 §1 -- Hybrid-Sensorik registriert Sensoren auf Standortebene.
        """
        screenshot(
            "TC-REQ-005-001_site-detail-loaded",
            "Site-Detail nach initialem Laden -- Sensors-Section sichtbar",
        )

        # The button is rendered inside a section that may need scrolling
        # into view on smaller viewports; existence in the DOM is the
        # contract we verify.
        assert sensor_dialog.is_add_sensor_button_present(), (
            "TC-REQ-005-001 FAIL: Expected [data-testid='add-sensor-button'] "
            "to be present on the Site detail page (REQ-005 §1)."
        )

        # Scroll the button into the viewport and assert it becomes visible
        sensor_dialog.scroll_add_sensor_button_into_view()
        screenshot(
            "TC-REQ-005-001_add-sensor-button-in-view",
            "add-sensor-button nach scrollIntoView",
        )
        assert sensor_dialog.is_add_sensor_button_visible(), (
            "TC-REQ-005-001 FAIL: add-sensor-button is in the DOM but not "
            "displayed after scrolling into view."
        )


# ── TC-REQ-005-002: Dialog opens and exposes the manual-input fields ────────


class TestSensorCreateDialogOpens:
    """Clicking ``Sensor hinzufuegen`` opens the SensorCreateDialog."""

    @pytest.mark.smoke
    def test_dialog_opens_with_required_fields(
        self,
        opened_site_detail: SiteDetailPage,
        sensor_dialog: SensorCreateDialogPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-005-002: Dialog renders name + metric_type + submit/cancel.

        Spec: REQ-005 §1 -- Manuelle Quelle (4. Tier der Fallback-Kette) muss in
        der UI anlegbar sein, damit Provenance ``manual`` ueberhaupt entstehen
        kann.
        """
        screenshot(
            "TC-REQ-005-002_before-open",
            "Site-Detail vor dem Oeffnen des SensorCreateDialog",
        )

        sensor_dialog.click_add_sensor()
        screenshot(
            "TC-REQ-005-002_dialog-open",
            "SensorCreateDialog nach Oeffnen",
        )

        assert sensor_dialog.is_open(), (
            "TC-REQ-005-002 FAIL: SensorCreateDialog did not open after "
            "clicking add-sensor-button."
        )

        # Required fields for manual sensor creation per REQ-005 §1
        assert sensor_dialog.has_field(SensorCreateDialogPage.NAME_INPUT), (
            "TC-REQ-005-002 FAIL: Expected sensor 'name' input in dialog."
        )
        assert sensor_dialog.has_field(SensorCreateDialogPage.METRIC_TYPE_SELECT), (
            "TC-REQ-005-002 FAIL: Expected 'metric_type' select in dialog."
        )
        assert sensor_dialog.has_field(SensorCreateDialogPage.SUBMIT_BUTTON), (
            "TC-REQ-005-002 FAIL: Expected submit button in dialog."
        )
        assert sensor_dialog.has_field(SensorCreateDialogPage.CANCEL_BUTTON), (
            "TC-REQ-005-002 FAIL: Expected cancel button in dialog."
        )


# ── TC-REQ-005-003: Smoke flow -- create sensor and verify it appears ───────


class TestSensorCreationSmokeFlow:
    """End-to-end smoke flow: create sensor, see it in the list."""

    @pytest.mark.smoke
    def test_create_manual_sensor_round_trip(
        self,
        opened_site_detail: SiteDetailPage,
        sensor_dialog: SensorCreateDialogPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-005-003: Anlegen eines Sensors, Dialog schliesst, Zeile sichtbar.

        Spec: REQ-005 §1 + Szenario 3 -- manuell gepflegte Quelle wird mit
        Datenherkunft abgespeichert; UI listet den neuen Eintrag in der
        Sensor-Tabelle.
        """
        # Use a unique sensor name so the test is idempotent across re-runs.
        # The session-scoped browser fixture means previous runs in the same
        # session would otherwise collide.
        from datetime import datetime, timezone

        ts = datetime.now(tz=timezone.utc).strftime("%H%M%S%f")
        sensor_name = f"E2E-Smoke-Sensor-{ts}"

        screenshot(
            "TC-REQ-005-003_before-create",
            "Site-Detail vor Sensor-Anlage",
        )

        sensor_dialog.click_add_sensor()
        screenshot(
            "TC-REQ-005-003_dialog-open",
            "Dialog geoeffnet, Felder leer",
        )

        sensor_dialog.set_name(sensor_name)
        # Default metric_type for site context is 'temperature_celsius' --
        # we keep the default so the test does not depend on i18n labels.
        screenshot(
            "TC-REQ-005-003_form-filled",
            f"Formular mit Sensor-Name '{sensor_name}' ausgefuellt",
        )

        sensor_dialog.submit()

        # The dialog closes on success; on validation/server error it would
        # remain open and we would surface that as an assertion failure.
        try:
            sensor_dialog.wait_until_closed(timeout=15)
        except Exception:
            screenshot(
                "TC-REQ-005-003_dialog-still-open",
                "FEHLER: Dialog blieb nach Submit offen",
            )
            pytest.fail(
                "TC-REQ-005-003 FAIL: SensorCreateDialog did not close after "
                "submit -- check for validation errors or server-side rejection."
            )

        screenshot(
            "TC-REQ-005-003_after-submit",
            "Site-Detail nach Sensor-Anlage -- neue Zeile erwartet",
        )

        # Reload the site detail page to make sure the sensor list reflects the
        # new entry (the page reloads its sensor list via ``loadSensors`` after
        # save, but a hard refresh is the most defensive verification).
        opened_site_detail.driver.refresh()
        opened_site_detail.wait_for_element_visible(SiteDetailPage.PAGE_TITLE)
        opened_site_detail._wait_for_skeleton_gone()

        # Wait until at least one data-table-row containing the sensor name
        # appears.  We avoid hard-coding which DataTable on the page renders
        # the sensor (locations vs. sensors); the unique sensor name makes the
        # match unambiguous.
        try:
            sensor_dialog.wait_for_row_containing(sensor_name, timeout=15)
        except Exception:
            screenshot(
                "TC-REQ-005-003_row-missing",
                "FEHLER: Neuer Sensor-Eintrag nicht in der Liste sichtbar",
            )
            pytest.fail(
                f"TC-REQ-005-003 FAIL: Expected sensor row '{sensor_name}' "
                "in any data-table on the Site detail page after creation."
            )

        screenshot(
            "TC-REQ-005-003_row-visible",
            f"Sensor-Zeile '{sensor_name}' nach Refresh sichtbar",
        )
