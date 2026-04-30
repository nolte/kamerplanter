"""REQ-031 KI-Assistent scaffold E2E."""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestKiAssistentRouteReachable:
    def test_ki_assistent_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/ki-assistent")
        skip_if_route_unwired(browser, "REQ-031")
        assert "KI" in browser.page_source or "ki-assistent" in browser.page_source
