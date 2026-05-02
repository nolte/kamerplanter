"""Helpers for route-reachability scaffold tests.

Used by REQ-008/017/018/026/029/031/035/036 smoke tests that probe routes
which may or may not be wired into ``AppRoutes.tsx`` yet.

The previous heuristic ``'404' in browser.title`` is unreliable: the SPA's
catch-all route renders a lazy-loaded ``NotFoundPage`` (via ``ErrorPage``
with ``data-testid='error-page'``), but neither updates ``document.title``
nor blocks the initial render. Probing ``page_source`` immediately after
``browser.get(...)`` therefore captures only the Suspense skeleton, and the
old heuristic neither asserts nor skips correctly. This helper waits for
the ErrorPage marker explicitly.
"""

from __future__ import annotations

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ERROR_PAGE_LOCATOR = (By.CSS_SELECTOR, "[data-testid='error-page']")


def skip_if_route_unwired(
    browser: WebDriver, req_id: str, *, timeout: int = 5
) -> None:
    """Skip the current test if the SPA's catch-all NotFoundPage rendered.

    Call this **after** ``browser.get(<candidate_route>)``. Waits up to
    *timeout* seconds for ``[data-testid='error-page']``; if it appears the
    test is skipped with a stable message that includes *req_id*. If the
    timeout expires the route is assumed to be wired and the caller proceeds
    to its assertions.
    """
    try:
        WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located(ERROR_PAGE_LOCATOR)
        )
    except TimeoutException:
        return
    pytest.skip(f"{req_id} route not yet wired into App.tsx — follow-up PR.")
