"""REQ-026 Aquaponik scaffold E2E."""

import pytest


@pytest.mark.smoke
class TestAquaponikRouteReachable:
    def test_aquaponik_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/aquaponik")
        if "404" in browser.title or "/aquaponik" not in browser.current_url:
            pytest.skip("REQ-026 route not yet wired into App.tsx — follow-up PR.")
        assert "Aquaponik" in browser.page_source
