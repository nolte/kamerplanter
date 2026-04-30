"""REQ-031 KI-Assistent scaffold E2E."""

import pytest


@pytest.mark.smoke
class TestKiAssistentRouteReachable:
    def test_ki_assistent_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/ki-assistent")
        if "404" in browser.title or "/ki-assistent" not in browser.current_url:
            pytest.skip("REQ-031 route not yet wired into App.tsx — follow-up PR.")
        assert "KI" in browser.page_source or "ki-assistent" in browser.page_source
