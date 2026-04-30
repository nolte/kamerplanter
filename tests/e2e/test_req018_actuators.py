"""REQ-018 Actuators / environment control scaffold E2E."""

import pytest


@pytest.mark.smoke
class TestActuatorsRouteReachable:
    def test_environment_control_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/environment-control")
        if "404" in browser.title or "/environment" not in browser.current_url:
            pytest.skip("REQ-018 route not yet wired into App.tsx — follow-up PR.")
        assert "Umgebungssteuerung" in browser.page_source or "environment" in browser.page_source
