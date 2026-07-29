"""REQ-018 Actuators / environment control scaffold E2E.

Spec-TC Mapping (test -> spec/e2e-testcases/TC-REQ-018.md):
  test_environment_control_route_reachable_or_skipped -> TC-018-073
"""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestActuatorsRouteReachable:
    def test_environment_control_route_reachable_or_skipped(self, browser, base_url):
        """TC-018-073: Smoke test: navigate to /environment-control. Skip when not yet wired."""
        browser.get(f"{base_url}/environment-control")
        skip_if_route_unwired(browser, "REQ-018")
        assert "Umgebungssteuerung" in browser.page_source or "environment" in browser.page_source
