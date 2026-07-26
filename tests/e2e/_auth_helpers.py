"""Shared full-mode auth-session helpers.

``driver.delete_all_cookies()`` only clears cookies visible on the *current
page's* path. The HttpOnly refresh cookie is scoped to ``path=/api/v1/auth``
(see ``conftest.ensure_authenticated``) and therefore survives, letting
``AuthProvider`` silently resurrect the session mid-test: auth pages redirect
to the dashboard while the test is still filling the form, and expected error
alerts never render. Clearing via CDP removes every cookie regardless of
path/domain. localStorage is deliberately left untouched — it carries the
language and module-visibility seeds set by the browser fixture.
"""

from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver


def clear_auth_session(driver: WebDriver) -> None:
    """Remove ALL browser cookies (path-independent), killing the session."""
    try:
        driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
    except Exception:
        # Non-chromium fallback: best effort for the current page's path.
        driver.delete_all_cookies()


def ensure_logged_out(driver: WebDriver, base_url: str) -> None:
    """Durably clear auth state and land on the login page."""
    clear_auth_session(driver)
    driver.get(f"{base_url}/login")
