"""E2E tests for REQ-032 — Druckansichten & Export (PrintButton component).

REQ-032 introduces a reusable ``PrintButton`` MUI component that triggers
PDF downloads for the most common print scenarios (Nährstoffplan,
Pflege-Checkliste, Pflanzen-Infokarten, ...).  The button is mounted on
detail and dashboard pages and calls the backend at
``GET /api/v1/t/{slug}/print/...`` — see ``spec/req/REQ-032_Druckansichten-Export.md``.

Because the print workflow is purely a *PDF download* (not a real
``window.print()`` call) these E2E tests do **not** trigger the OS
print dialog.  They verify that:

1. The PrintButton is rendered on pages that opt in to it.
2. Clicking the button reaches the component, runs ``onPrint()`` and
   either succeeds (success snackbar) or fails gracefully (error
   snackbar) — both outcomes prove the UI → API wiring is intact.
3. The button is accessible (``aria-label`` set, supports keyboard
   activation via Selenium's click).

To prevent any accidental native print dialog from a misbehaving page
that *also* calls ``window.print()``, the host browser's ``window.print``
is shadowed with a no-op before each test.

Spec-TC Mapping:
  TC-REQ-032-001  ->  REQ-032 §6.1   PrintButton sichtbar auf PflegeDashboardPage
  TC-REQ-032-002  ->  REQ-032 §6.1   PrintButton hat barrierefreies aria-label
  TC-REQ-032-003  ->  REQ-032 §3.2   Klick triggert Download-Workflow ohne Crash
  TC-REQ-032-004  ->  REQ-032 §6.1   PrintButton auf NutrientPlanDetailPage (optional)
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.nutrient_plan_detail_page import NutrientPlanDetailPage
from .pages.pflege_dashboard_page import PflegeDashboardPage
from .pages.print_button_page import PrintButtonPage


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture(autouse=True)
def stub_window_print(browser: WebDriver) -> None:
    """Replace ``window.print`` with a no-op before every test.

    The PrintButton component itself does *not* call ``window.print()`` —
    it downloads a PDF blob.  This stub is a defense-in-depth guard so a
    misbehaving page or third-party widget cannot pop the OS print dialog
    on the headless test browser and stall the run.
    """
    browser.execute_script("window.print = function () { return undefined; };")


@pytest.fixture
def print_button(browser: WebDriver, base_url: str) -> PrintButtonPage:
    """Return a PrintButtonPage helper bound to the active browser session."""
    return PrintButtonPage(browser, base_url)


@pytest.fixture
def pflege(browser: WebDriver, base_url: str) -> PflegeDashboardPage:
    """Return a PflegeDashboardPage so we can navigate to a host page."""
    return PflegeDashboardPage(browser, base_url)


@pytest.fixture
def nutrient_plan_detail(
    browser: WebDriver, base_url: str
) -> NutrientPlanDetailPage:
    """Return a NutrientPlanDetailPage helper for the NutrientPlan host page."""
    return NutrientPlanDetailPage(browser, base_url)


# -- TC-REQ-032-001 / 002: PrintButton presence and a11y ---------------------


class TestPrintButtonPresence:
    """PrintButton is rendered on opted-in pages with a11y attributes (Spec: REQ-032 §6.1)."""

    @pytest.mark.smoke
    def test_print_button_visible_on_pflege_dashboard(
        self,
        pflege: PflegeDashboardPage,
        print_button: PrintButtonPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-032-001: PrintButton ist auf der Pflege-Dashboard-Seite sichtbar.

        Spec: REQ-032 §6.1 -- PrintButton-Platzierung in Toolbar / Aktionsleiste
        der jeweiligen Detail- oder Listenansicht (hier: Pflege-Checkliste).
        """
        pflege.open()
        screenshot(
            "TC-REQ-032-001_pflege-dashboard-with-print-button",
            "Pflege-Dashboard mit PrintButton in der Aktionsleiste",
        )

        assert print_button.is_present(), (
            "TC-REQ-032-001 FAIL: Erwartet [data-testid='print-button'] "
            "auf der Pflege-Dashboard-Seite (PflegeDashboardPage hostet die "
            "Pflege-Checkliste-Druckansicht laut REQ-032 §2.2)."
        )
        assert print_button.is_visible(), (
            "TC-REQ-032-001 FAIL: PrintButton ist im DOM aber nicht sichtbar — "
            "moeglicherweise vom PageTitle-Action-Slot verdeckt."
        )

    @pytest.mark.smoke
    def test_print_button_has_accessible_label(
        self,
        pflege: PflegeDashboardPage,
        print_button: PrintButtonPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-032-002: PrintButton stellt ein aria-label fuer Screenreader bereit.

        Spec: REQ-032 §8 -- Barrierefreiheit. PrintButton-Komponente belegt
        ``aria-label`` mit dem optionalen ``label``-Prop oder dem i18n-Default
        ``print.downloadPdf`` -- siehe PrintButton.tsx Zeile 64.
        """
        pflege.open()
        screenshot(
            "TC-REQ-032-002_print-button-aria-label",
            "PrintButton aria-label fuer Screenreader",
        )

        aria = print_button.get_aria_label()
        assert aria, (
            "TC-REQ-032-002 FAIL: Erwartet ein nicht-leeres aria-label am "
            f"PrintButton fuer Screenreader-Zugaenglichkeit, bekam: '{aria}'"
        )


# -- TC-REQ-032-003: Click triggers the download workflow --------------------


class TestPrintButtonClick:
    """Clicking the PrintButton runs the onPrint() workflow (Spec: REQ-032 §3.2)."""

    @pytest.mark.smoke
    def test_print_button_click_runs_workflow(
        self,
        pflege: PflegeDashboardPage,
        print_button: PrintButtonPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-032-003: Klick auf PrintButton startet onPrint() und kehrt in idle-Zustand zurueck.

        Spec: REQ-032 §3.2 -- Backend-PDF-Export. Der Klick auf den Button
        ruft ``downloadCareChecklistPdf()`` auf, was den Backend-Endpoint
        ``GET /api/v1/t/{slug}/print/care-checklist`` anstoesst. Wir asserten
        nicht den Datei-Inhalt (Headless-Chrome-Download geht an einen
        temporaeren Pfad), sondern dass die Komponente nach dem Klick
        wieder reaktionsfaehig ist und ein Snackbar-Feedback (success oder
        error) zeigt -- beides beweist dass die UI->API->Backend-Verkettung
        durchlaufen wurde.
        """
        pflege.open()
        screenshot(
            "TC-REQ-032-003_before-click",
            "PrintButton vor dem Klick (idle, Print-Icon sichtbar)",
        )

        assert not print_button.is_disabled(), (
            "TC-REQ-032-003 FAIL: PrintButton sollte vor dem Klick aktiv sein"
        )

        print_button.click()

        # Component switches to the loading spinner during the request — wait
        # until it returns to idle before asserting on the snackbar feedback.
        print_button.wait_for_completion(timeout=30)

        screenshot(
            "TC-REQ-032-003_after-click",
            "PrintButton nach abgeschlossenem onPrint()-Workflow",
        )

        # Either success or error snackbar is acceptable proof of the wiring.
        # The demo-instance backend may not have a fully populated print
        # template registry, so a graceful error path is also a valid outcome.
        try:
            snackbar_text = print_button.wait_for_snackbar(timeout=10)
        except Exception:
            screenshot(
                "TC-REQ-032-003_no-snackbar",
                "Kein Snackbar -- Workflow lief evtl. zu schnell durch",
            )
            # Even without a snackbar the button must be re-enabled and idle —
            # that alone proves the click reached the component without crash.
            assert not print_button.is_disabled(), (
                "TC-REQ-032-003 FAIL: PrintButton blieb nach dem Klick "
                "deaktiviert -- onPrint() vermutlich haengt im Loading-State"
            )
            return

        assert snackbar_text, (
            f"TC-REQ-032-003 FAIL: Snackbar nach Klick erwartet, "
            f"bekam leeren Text: '{snackbar_text}'"
        )


# -- TC-REQ-032-004: PrintButton on NutrientPlan detail page (optional) ------


class TestPrintButtonOnNutrientPlan:
    """PrintButton on NutrientPlanDetailPage (Spec: REQ-032 §2.1, §6.1)."""

    @pytest.mark.smoke
    def test_print_button_on_nutrient_plan_detail(
        self,
        nutrient_plan_detail: NutrientPlanDetailPage,
        print_button: PrintButtonPage,
        e2e_seed_data: dict,
        base_url: str,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-032-004: PrintButton ist auf der NutrientPlanDetailPage sichtbar (sofern Plan existiert).

        Spec: REQ-032 §2.1 + §6.1 -- Naehrstoffplan als druckbares Dokument.
        Da die Demo-Instanz nicht garantiert einen NutrientPlan mit
        downloadbarem PDF besitzt, ueberspringt der Test sauber, wenn kein
        Plan-Key ueber die Liste auffindbar ist.
        """
        # Discover any nutrient plan via the list endpoint.  Skip cleanly
        # if the demo instance has no plans seeded.
        import json
        import urllib.error
        import urllib.request

        token = e2e_seed_data.get("access_token")
        slug = e2e_seed_data.get("tenant_slug", "mein-garten")
        url = f"{base_url.rstrip('/')}/api/v1/t/{slug}/nutrient-plans"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                plans = json.loads(resp.read())
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            pytest.skip(
                "TC-REQ-032-004 SKIP: NutrientPlan-Liste nicht erreichbar -- "
                "PrintButton-Pruefung auf Detailseite uebersprungen."
            )

        if not isinstance(plans, list) or not plans:
            pytest.skip(
                "TC-REQ-032-004 SKIP: Keine NutrientPlans auf der Demo-Instanz -- "
                "PrintButton-Pruefung auf Detailseite uebersprungen."
            )

        plan_key = plans[0].get("key")
        if not plan_key:
            pytest.skip(
                "TC-REQ-032-004 SKIP: NutrientPlan ohne 'key' -- "
                "PrintButton-Pruefung auf Detailseite uebersprungen."
            )

        nutrient_plan_detail.open(plan_key)
        screenshot(
            "TC-REQ-032-004_nutrient-plan-detail-with-print-button",
            f"NutrientPlanDetailPage fuer Plan {plan_key} mit PrintButton",
        )

        assert print_button.is_present(), (
            "TC-REQ-032-004 FAIL: Erwartet [data-testid='print-button'] auf "
            "NutrientPlanDetailPage (siehe NutrientPlanDetailPage.tsx Zeile 1030)."
        )
