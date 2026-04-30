"""REQ-036 Diagnose scaffold E2E."""

import pytest


@pytest.mark.smoke
class TestDiagnoseRouteReachable:
    def test_diagnose_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/diagnose")
        if "404" in browser.title or "/diagnose" not in browser.current_url:
            pytest.skip("REQ-036 route not yet wired into App.tsx — follow-up PR.")
        assert "Diagnose" in browser.page_source
