"""E2E tests for REQ-027 -- Light-Modus (Anonymer Zugang).

Diese Tests pruefen das oeffentliche ``/api/v1/mode``-Endpoint sowie das
modus-abhaengige Frontend-Verhalten. Sie laufen sowohl im Light- als auch
im Full-Modus und passen ihre Erwartungen anhand der CLI-Option
``--app-mode`` an.

Spec: ``spec/req/REQ-027_Light-Modus.md`` (v1.4)

Spec-TC Mapping:
  TC-REQ-027-001  ->  §1, §6.1   ``GET /api/v1/mode`` liefert mode + features
  TC-REQ-027-002  ->  §1, §2.1   Feature-Flags ``auth``/``multi_tenant``/
                                  ``privacy_consent`` korrespondieren mit Modus
  TC-REQ-027-003  ->  §1.1       Mode-Endpoint ist anonym ohne JWT erreichbar
                                  (Public Endpoint)

Diese Tests sind read-only und idempotent — sie modifizieren keinen State
am Backend. Der Mode-Endpoint ist in beiden Modi aktiv (siehe
``src/backend/app/api/v1/router.py``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver


# -- Helpers -----------------------------------------------------------------


def _fetch_mode(driver: WebDriver, base_url: str) -> dict[str, Any]:
    """Call ``GET /api/v1/mode`` from the browser context (anonymous, no JWT).

    Returns the parsed JSON response. Uses the browser's same-origin
    ``fetch`` so we exercise the path the frontend actually uses without
    needing an extra HTTP client. Strips any auth headers explicitly to
    verify the endpoint is publicly reachable (REQ-027 §1: anonymous
    access).
    """
    script = """
    const cb = arguments[0];
    fetch('/api/v1/mode', {
      method: 'GET',
      credentials: 'omit',
      headers: { 'Accept': 'application/json' },
    })
      .then(r => r.text().then(body => cb({status: r.status, body: body})))
      .catch(err => cb({status: -1, body: String(err)}));
    """
    # Ensure we are on the app origin so fetch resolves to the same host.
    if base_url not in driver.current_url:
        driver.get(base_url)
    result = driver.execute_async_script(script)
    if result["status"] != 200:
        raise AssertionError(
            f"GET /api/v1/mode failed: status={result['status']}, "
            f"body={result['body'][:300]}"
        )
    return json.loads(result["body"])


# -- TC-REQ-027-001 to TC-REQ-027-003: Mode endpoint -------------------------


class TestModeEndpoint:
    """REQ-027 Mode-Endpoint — Public discovery of deployment configuration.

    Spec: REQ-027 §1 (Kernkonzepte), §6.1 (Lifespan / Mode). Der Endpoint
    ist in beiden Modi aktiv und ohne Auth erreichbar, damit das Frontend
    seine UI-Anteile (Login, Tenant-Switcher, Consent-Banner) anhand des
    Backend-Modus tunen kann.
    """

    @pytest.mark.smoke
    def test_mode_endpoint_returns_shape(
        self,
        browser: WebDriver,
        base_url: str,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-027-001: ``GET /api/v1/mode`` liefert ``mode`` + ``features``.

        Spec: REQ-027 §1 — Eine einzige Environment-Variable
        ``KAMERPLANTER_MODE`` steuert den Betriebsmodus; der Endpoint ist
        die kanonische Quelle fuer Feature-Flags zur Laufzeit.
        """
        payload = _fetch_mode(browser, base_url)
        screenshot(
            "req027_001_mode_endpoint",
            "Browser nach Mode-Endpoint-Abfrage (Public, ohne JWT)",
        )

        assert "mode" in payload, (
            f"Mode-Response sollte Feld 'mode' enthalten, war: {payload}"
        )
        assert payload["mode"] in {"light", "full"}, (
            f"Mode sollte 'light' oder 'full' sein, war: {payload['mode']!r}"
        )
        assert "features" in payload, (
            f"Mode-Response sollte Feld 'features' enthalten, war: {payload}"
        )
        for flag in ("auth", "multi_tenant", "privacy_consent"):
            assert flag in payload["features"], (
                f"Feature-Flag {flag!r} fehlt in features: "
                f"{payload['features']}"
            )
            assert isinstance(payload["features"][flag], bool), (
                f"Feature-Flag {flag!r} sollte bool sein, war: "
                f"{type(payload['features'][flag]).__name__}"
            )

    @pytest.mark.smoke
    def test_mode_features_match_app_mode(
        self,
        browser: WebDriver,
        base_url: str,
        app_mode: str,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-027-002: Feature-Flags entsprechen dem deklarierten Modus.

        Spec: REQ-027 §1 ``KAMERPLANTER_MODE``, §2.1 (Was deaktiviert ist).
        Im Light-Modus sind ``auth``/``multi_tenant``/``privacy_consent``
        deaktiviert; im Full-Modus aktiv. Stellt sicher, dass die CLI-
        Option ``--app-mode`` mit der tatsaechlichen Backend-Konfiguration
        konsistent ist (Test-Harness-Sanity-Check).
        """
        payload = _fetch_mode(browser, base_url)
        screenshot(
            "req027_002_mode_features",
            f"Mode-Response im {app_mode}-Modus",
        )

        assert payload["mode"] == app_mode, (
            f"Backend meldet Modus {payload['mode']!r}, CLI-Option "
            f"--app-mode={app_mode!r} — Test-Harness inkonsistent"
        )
        is_full = app_mode == "full"
        for flag in ("auth", "multi_tenant", "privacy_consent"):
            assert payload["features"][flag] is is_full, (
                f"Feature {flag!r} sollte im {app_mode}-Modus "
                f"{is_full} sein, war: {payload['features'][flag]}"
            )

    def test_mode_endpoint_reachable_without_auth(
        self,
        browser: WebDriver,
        base_url: str,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-027-003: Mode-Endpoint ist anonym (ohne JWT) erreichbar.

        Spec: REQ-027 §1.1 — Das Frontend muss den Modus erkennen koennen,
        BEVOR ein User authentifiziert ist. Der Endpoint darf daher nicht
        hinter einer Auth-Pruefung liegen. Der Test ruft ihn explizit ohne
        Cookies/Authorization-Header auf (``credentials: 'omit'``).
        """
        # _fetch_mode setzt credentials:'omit' und sendet keinen
        # Authorization-Header — gelingt der Call mit Status 200, ist der
        # Endpoint nachweislich public.
        payload = _fetch_mode(browser, base_url)
        screenshot(
            "req027_003_mode_anonymous",
            "Mode-Endpoint anonym (credentials='omit') erreichbar",
        )

        assert isinstance(payload, dict) and payload.get("mode") in {
            "light",
            "full",
        }, (
            f"Anonymer Aufruf von /api/v1/mode lieferte unerwartete "
            f"Response: {payload}"
        )
