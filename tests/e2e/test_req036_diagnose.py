"""REQ-036 Diagnose scaffold E2E."""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestDiagnoseRouteReachable:
    def test_diagnose_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/diagnose")
        skip_if_route_unwired(browser, "REQ-036")
        assert "Diagnose" in browser.page_source
