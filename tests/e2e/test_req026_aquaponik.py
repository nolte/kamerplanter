"""REQ-026 Aquaponik scaffold E2E.

Spec-TC Mapping (test -> spec/e2e-testcases/TC-REQ-026.md):
  test_aquaponik_route_reachable_or_skipped -> TC-026-069
"""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestAquaponikRouteReachable:
    def test_aquaponik_route_reachable_or_skipped(self, browser, base_url):
        """TC-026-069: Smoke test: navigate to /aquaponik. Skip when not yet wired."""
        browser.get(f"{base_url}/aquaponik")
        skip_if_route_unwired(browser, "REQ-026")
        assert "Aquaponik" in browser.page_source
