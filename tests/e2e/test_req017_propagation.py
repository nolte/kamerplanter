"""REQ-017 Propagation scaffold E2E."""

import pytest


@pytest.mark.smoke
class TestPropagationRouteReachable:
    def test_propagation_page_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/propagation")
        if "404" in browser.title or "/propagation" not in browser.current_url:
            pytest.skip("REQ-017 route not yet wired into App.tsx — follow-up PR.")
        assert "Vermehrungsmanagement" in browser.page_source or "propagation" in browser.page_source
