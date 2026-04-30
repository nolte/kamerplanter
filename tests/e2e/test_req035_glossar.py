"""REQ-035 Glossar scaffold E2E."""

import pytest

from ._route_helpers import skip_if_route_unwired


@pytest.mark.smoke
class TestGlossarRouteReachable:
    def test_glossar_route_reachable_or_skipped(self, browser, base_url):
        browser.get(f"{base_url}/glossar")
        skip_if_route_unwired(browser, "REQ-035")
        assert "Glossar" in browser.page_source or "glossar" in browser.page_source
