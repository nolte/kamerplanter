"""REQ-017 Propagation scaffold E2E."""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestPropagationRouteReachable:
    def test_propagation_page_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/propagation")
        skip_if_route_unwired(browser, "REQ-017")
        assert "Vermehrungsmanagement" in browser.page_source or "propagation" in browser.page_source
