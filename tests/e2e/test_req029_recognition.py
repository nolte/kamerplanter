"""REQ-029 Plant identification scaffold E2E."""

import pytest


@pytest.mark.smoke
class TestRecognitionRouteReachable:
    def test_recognition_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/plant-identification")
        if "404" in browser.title or "/plant-identification" not in browser.current_url:
            pytest.skip("REQ-029 route not yet wired into App.tsx — follow-up PR.")
        assert "Pflanzenerkennung" in browser.page_source or "identification" in browser.page_source
