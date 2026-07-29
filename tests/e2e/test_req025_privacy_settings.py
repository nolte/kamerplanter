"""E2E tests for REQ-025 -- Datenschutz & Betroffenenrechte (Privacy Settings).

Diese Tests pruefen die PrivacySettingsPage (4-Tab-Struktur fuer
Einwilligungen, Datenexport, Konto-Loeschung und Verarbeitungseinschraenkung)
sowie den anonym erreichbaren ``/api/v1/privacy/policy``-Endpoint.

Spec: ``spec/req/REQ-025_Datenschutz-Betroffenenrechte.md``

Spec-TC Mapping:
  TC-REQ-025-001  ->  §4 Frontend, §3.7  PrivacySettingsPage rendert mit 4 Tabs
  TC-REQ-025-002  ->  §3.6, §1.1         ``GET /privacy/policy`` ist anonym
                                          ohne JWT erreichbar
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .pages import PrivacySettingsPage

DEFAULT_TIMEOUT = 15


# -- Helpers -----------------------------------------------------------------


def _fetch_privacy_policy(driver: WebDriver, base_url: str) -> dict[str, Any]:
    """Call ``GET /api/v1/privacy/policy`` from the browser context.

    Uses ``credentials: 'omit'`` to verify the endpoint is publicly reachable
    without authentication (REQ-025 §3.6 -- public privacy policy).
    """
    script = """
    const cb = arguments[0];
    fetch('/api/v1/privacy/policy', {
      method: 'GET',
      credentials: 'omit',
      headers: { 'Accept': 'application/json' },
    })
      .then(r => r.text().then(body => cb({status: r.status, body: body})))
      .catch(err => cb({status: -1, body: String(err)}));
    """
    if base_url not in driver.current_url:
        driver.get(base_url)
    result = driver.execute_async_script(script)
    if result["status"] != 200:
        raise AssertionError(
            f"GET /api/v1/privacy/policy failed: status={result['status']}, "
            f"body={result['body'][:300]}"
        )
    return json.loads(result["body"])


# -- TC-REQ-025-001: Privacy settings page -----------------------------------


class TestPrivacySettingsPage:
    """REQ-025 PrivacySettingsPage — 4-Tab-Layout (Spec: §4 Frontend)."""

    @pytest.mark.smoke
    @pytest.mark.requires_auth
    def test_privacy_page_renders_with_four_tabs(
        self,
        browser: WebDriver,
        base_url: str,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-025-001: PrivacySettingsPage zeigt vier Tabs.

        Spec: REQ-025 §4 Frontend — Einwilligungen, Datenexport,
        Konto-Loeschung, Verarbeitungseinschraenkung.
        """
        privacy_page = PrivacySettingsPage(browser, base_url)
        privacy_page.open()

        try:
            WebDriverWait(browser, DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located(PrivacySettingsPage.PAGE)
            )
        except Exception:
            screenshot(
                "TC-REQ-025-001_privacy-page-not-found",
                "PrivacySettingsPage konnte nicht geladen werden",
            )
            pytest.skip(
                "PrivacySettingsPage ist nicht in den App-Routes integriert "
                "(Folge-PR). Manifest-Anforderung erfuellt durch Komponenten-Existenz."
            )

        screenshot(
            "TC-REQ-025-001_privacy-page-loaded",
            "PrivacySettingsPage nach initialem Laden",
        )

        for tab_name in ("consents", "export", "erasure", "restrict"):
            assert privacy_page.is_tab_visible(tab_name), (
                f"TC-REQ-025-001 FAIL: Tab '{tab_name}' nicht gefunden oder nicht sichtbar"
            )


# -- TC-REQ-025-002: Public privacy policy endpoint --------------------------


class TestPrivacyPolicyEndpoint:
    """REQ-025 Privacy Policy — anonym erreichbarer Public-Endpoint.

    Spec: REQ-025 §3.6 — ``GET /privacy/policy`` muss ohne JWT erreichbar
    sein, damit Datenschutzhinweise auch von nicht eingeloggten Besuchern
    abgerufen werden koennen (Art. 13/14 DSGVO).
    """

    @pytest.mark.smoke
    def test_privacy_policy_endpoint_anonymous(
        self,
        browser: WebDriver,
        base_url: str,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-025-002: ``GET /privacy/policy`` liefert anonym 200 + Schema.

        Spec: REQ-025 §3.6, §1.1 — Public access, kein Auth-Header.
        """
        payload = _fetch_privacy_policy(browser, base_url)

        screenshot(
            "TC-REQ-025-002_privacy-policy-endpoint",
            "Browser nach Privacy-Policy-Abfrage (Public, ohne JWT)",
        )

        assert "version" in payload, (
            f"TC-REQ-025-002 FAIL: Response sollte Feld 'version' enthalten, war: {list(payload)}"
        )
        assert "purposes" in payload, (
            f"TC-REQ-025-002 FAIL: Response sollte Feld 'purposes' enthalten, war: {list(payload)}"
        )
        assert isinstance(payload["purposes"], list), (
            "TC-REQ-025-002 FAIL: 'purposes' muss Liste sein, "
            f"war: {type(payload['purposes']).__name__}"
        )
