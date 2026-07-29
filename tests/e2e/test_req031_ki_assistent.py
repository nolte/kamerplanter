"""REQ-031 KI-Assistent scaffold E2E.

Spec-TC Mapping (test -> spec/e2e-testcases/TC-REQ-031.md):
  test_ki_assistent_route_reachable_or_skipped -> TC-031-001

Note: TC-REQ-031.md is a newly-created, scaffold-scoped spec document --
only this route-reachability case has been derived so far. See its "Offene
Abschnitte" section for the full REQ-031 scope that still needs derivation.
"""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestKiAssistentRouteReachable:
    def test_ki_assistent_route_reachable_or_skipped(self, browser, base_url):
        """TC-031-001: Smoke test: navigate to /ki-assistent. Skip when not yet wired."""
        browser.get(f"{base_url}/ki-assistent")
        skip_if_route_unwired(browser, "REQ-031")
        assert "KI" in browser.page_source or "ki-assistent" in browser.page_source
