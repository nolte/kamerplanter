"""REQ-035 Glossar scaffold E2E.

Spec-TC Mapping (test -> spec/e2e-testcases/TC-REQ-035.md):
  test_glossar_route_reachable_or_skipped -> TC-035-001

Note: TC-REQ-035.md is a newly-created, scaffold-scoped spec document --
only this route-reachability case has been derived so far. See its "Offene
Abschnitte" section for the full REQ-035 scope that still needs derivation.
"""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestGlossarRouteReachable:
    def test_glossar_route_reachable_or_skipped(self, browser, base_url):
        """TC-035-001: Smoke test: navigate to /glossar. Skip when not yet wired."""
        browser.get(f"{base_url}/glossar")
        skip_if_route_unwired(browser, "REQ-035")
        assert "Glossar" in browser.page_source or "glossar" in browser.page_source
