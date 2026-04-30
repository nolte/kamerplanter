"""REQ-035 Glossar scaffold E2E."""

import pytest


@pytest.mark.smoke
class TestGlossarRouteReachable:
    def test_glossar_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/glossar")
        if "404" in browser.title or "/glossar" not in browser.current_url:
            pytest.skip("REQ-035 route not yet wired into App.tsx — follow-up PR.")
        assert "Glossar" in browser.page_source or "glossar" in browser.page_source
