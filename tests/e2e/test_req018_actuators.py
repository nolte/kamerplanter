"""REQ-018 Actuators / environment control scaffold E2E."""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestActuatorsRouteReachable:
    def test_environment_control_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/environment-control")
        skip_if_route_unwired(browser, "REQ-018")
        assert "Umgebungssteuerung" in browser.page_source or "environment" in browser.page_source
