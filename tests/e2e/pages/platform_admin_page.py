"""Page object for the platform admin hub ``/admin/platform`` (F-12, #2935)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from .base_page import DEFAULT_TIMEOUT, BasePage, SettledState


class PlatformAdminPage(BasePage):
    """Interact with the platform admin hub and its sidebar entry.

    The hub replaced the *platform* tab of the account settings page: it is the
    platform admin's way into every admin page, and every admin page's back link
    leads here. Selectors are ``data-testid`` hooks from ``AdminPlatformPage.tsx``,
    ``Sidebar.tsx`` and ``RequirePlatformAdmin.tsx``.
    """

    PATH = "/admin/platform"

    PAGE = (By.CSS_SELECTOR, "[data-testid='admin-platform-page']")
    REFUSED_PAGE = (By.CSS_SELECTOR, "[data-testid='platform-admin-required-page']")
    #: The sidebar entry. Not ``nav-/admin/platform``: the ``nav-/…`` namespace is
    #: the module-governed navigation the Sidebar ↔ moduleCatalog guard checks,
    #: and this footer entry is gated on the platform-admin flag instead.
    NAV_ENTRY = (By.CSS_SELECTOR, "[data-testid='nav-admin-platform']")

    # Full mode only — the admin reads the hub renders after a successful load.
    OIDC_CARD = (By.CSS_SELECTOR, "[data-testid='admin-oidc-card']")
    #: The tenant and user tables' edit buttons, keyed per row (``edit-tenant-<key>``).
    TENANT_EDIT_BUTTONS = (By.CSS_SELECTOR, "[data-testid^='edit-tenant-']")
    USER_EDIT_BUTTONS = (By.CSS_SELECTOR, "[data-testid^='edit-user-']")
    PLANS_OPEN = (By.CSS_SELECTOR, "[data-testid='admin-plans-open']")
    PLANS_PAGE = (By.CSS_SELECTOR, "[data-testid='admin-plans-page']")
    PLANS_BACK = (By.CSS_SELECTOR, "[data-testid='plans-back']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> PlatformAdminPage:
        """Navigate to the hub and wait until it rendered (fails on an error surface)."""
        self.navigate(self.PATH)
        self.wait_for_content(self.PAGE, "platform admin hub")
        return self

    def open_expecting_refusal(self) -> SettledState:
        """Navigate to the hub as a non-admin; return which branch the route settled into."""
        return self.navigate_direct(
            self.PATH,
            self.PAGE,
            what="platform admin hub (non-admin)",
            extra={"refused": self.REFUSED_PAGE},
        )

    def has_nav_entry(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Whether the sidebar offers the hub entry (opens the drawer first)."""
        self.ensure_sidebar_open(timeout=timeout)
        return self.is_visible_within(self.NAV_ENTRY, timeout=timeout)

    def open_via_sidebar(self, timeout: int = DEFAULT_TIMEOUT) -> PlatformAdminPage:
        """Click the sidebar entry and wait until the hub rendered."""
        self.ensure_sidebar_open(timeout=timeout)
        entry = self.wait_for_element_clickable(self.NAV_ENTRY, timeout=timeout)
        self.scroll_and_click(entry)
        self.poll(timeout).until(EC.url_contains(self.PATH))
        self.wait_for_content(self.PAGE, "platform admin hub via sidebar", timeout=timeout)
        return self

    def has_loaded_admin_data(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Whether the admin half rendered: launchers plus at least one tenant and one user row.

        The seeded platform admin is a member of the ``platform`` tenant, so both
        tables hold at least that tenant and that account once the reads succeeded.
        """
        return all(
            self.is_visible_within(locator, timeout=timeout)
            for locator in (self.OIDC_CARD, self.TENANT_EDIT_BUTTONS, self.USER_EDIT_BUTTONS)
        )

    def open_plans_and_return(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Open the plans page from the hub, then follow its back link to the hub."""
        self.scroll_and_click(self.wait_for_element_clickable(self.PLANS_OPEN, timeout=timeout))
        self.wait_for_content(self.PLANS_PAGE, "admin plans page", timeout=timeout)
        self.scroll_and_click(self.wait_for_element_clickable(self.PLANS_BACK, timeout=timeout))
        self.poll(timeout).until(EC.url_contains(self.PATH))
        self.wait_for_content(self.PAGE, "platform admin hub after back link", timeout=timeout)
