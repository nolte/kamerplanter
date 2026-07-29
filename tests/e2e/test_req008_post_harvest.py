"""REQ-008 Post-Harvest scaffold E2E.

The full UI flow (start drying -> curing -> stored -> released) lands
with the REQ-008 implementation PR. Until the route is wired into
App.tsx, this test self-skips so CI stays green.
"""

import pytest

from ._route_helpers import skip_if_route_unwired

# Feature-axis marker(s) for machine-selectable test identification
# (see conftest.py::KNOWN_FEATURE_MARKERS / pytest -m <feature>).
FEATURES = ("harvest",)


@pytest.mark.smoke
class TestPostHarvestRouteReachable:
    def test_post_harvest_page_route_reachable_or_skipped(self, browser, base_url):
        """Smoke test: navigate to /post-harvest. Skip when not yet wired."""
        browser.get(f"{base_url}/post-harvest")
        skip_if_route_unwired(browser, "REQ-008")

        # When the route is wired, a marker container should render.
        assert "Nacherntebehandlung" in browser.page_source or "post-harvest" in browser.page_source
