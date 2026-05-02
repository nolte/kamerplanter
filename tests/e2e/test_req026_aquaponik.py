"""REQ-026 Aquaponik scaffold E2E."""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestAquaponikRouteReachable:
    def test_aquaponik_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/aquaponik")
        skip_if_route_unwired(browser, "REQ-026")
        assert "Aquaponik" in browser.page_source
