"""REQ-029 Plant identification scaffold E2E."""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestRecognitionRouteReachable:
    def test_recognition_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/plant-identification")
        skip_if_route_unwired(browser, "REQ-029")
        assert "Pflanzenerkennung" in browser.page_source or "identification" in browser.page_source
