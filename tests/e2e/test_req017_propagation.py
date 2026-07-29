"""REQ-017 Propagation scaffold E2E.

Spec-TC Mapping (test -> spec/e2e-testcases/TC-REQ-017.md):
  test_propagation_page_route_reachable_or_skipped -> TC-017-073
"""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestPropagationRouteReachable:
    def test_propagation_page_route_reachable_or_skipped(self, browser, base_url):
        """TC-017-073: Smoke test: navigate to /propagation. Skip when not yet wired."""
        browser.get(f"{base_url}/propagation")
        skip_if_route_unwired(browser, "REQ-017")
        assert (
            "Vermehrungsmanagement" in browser.page_source or "propagation" in browser.page_source
        )
