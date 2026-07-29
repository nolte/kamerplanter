"""REQ-036 Diagnose scaffold E2E.

Spec-TC Mapping (test -> spec/e2e-testcases/TC-REQ-036.md):
  test_diagnose_route_reachable_or_skipped -> TC-036-001

Note: TC-REQ-036.md is a newly-created, scaffold-scoped spec document --
only this route-reachability case has been derived so far. See its "Offene
Abschnitte" section for the full REQ-036 scope that still needs derivation.
"""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestDiagnoseRouteReachable:
    def test_diagnose_route_reachable_or_skipped(self, browser, base_url):
        """TC-036-001: Smoke test: navigate to /diagnose. Skip when not yet wired."""
        browser.get(f"{base_url}/diagnose")
        skip_if_route_unwired(browser, "REQ-036")
        assert "Diagnose" in browser.page_source
