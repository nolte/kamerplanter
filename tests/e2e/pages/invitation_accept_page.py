"""Page object for the Invitation Accept page (REQ-024)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage, DEFAULT_TIMEOUT


class InvitationAcceptPage(BasePage):
    """Interact with the Invitation Accept page (``/invitations/accept?token=...``)."""

    PATH = "/invitations/accept"

    # -- Locators ----------------------------------------------------------
    # Every locator below is scoped to the page's own result card.
    #
    # `InvitationAcceptPage` renders inside `MainLayout`, whose app shell
    # carries chrome built from the very same MUI classes -- most importantly
    # the Sidebar brand, a plain `<Typography variant="h6">Kamerplanter`
    # (`Sidebar.tsx:400`). An unscoped `.MuiTypography-h6` therefore resolved
    # to *that* element: at >= `md` the drawer is `persistent` and visible, so
    # `get_heading_text()` returned "Kamerplanter" and TC-REQ-024-030 passed
    # without ever having looked at the invitation heading. Below `md` the same
    # drawer is a closed `temporary` modal kept in the DOM by `keepMounted`, so
    # its text reads '' and the assertion finally failed (393px, run
    # `20260725_193834`) -- the desktop pass had been a false positive for the
    # whole life of the test.
    #
    # The card is the invitation page's only `MuiCard-root`, and no app-shell
    # chrome (AppBar, Sidebar, light-mode banner, Breadcrumbs) renders one, so
    # this prefix is exact. Whatever the viewport does to the drawer, a locator
    # under `CARD` can only ever address this page's own content.
    CARD = ".MuiCard-root .MuiCardContent-root"

    LOADING_SPINNER = (By.CSS_SELECTOR, f"{CARD} .MuiCircularProgress-root")
    SUCCESS_ICON = (
        By.CSS_SELECTOR,
        f"{CARD} [data-testid='CheckCircleIcon'],{CARD} svg.MuiSvgIcon-colorSuccess",
    )
    ERROR_ICON = (
        By.CSS_SELECTOR,
        f"{CARD} [data-testid='ErrorIcon'],{CARD} svg.MuiSvgIcon-colorError",
    )
    HEADING = (By.CSS_SELECTOR, f"{CARD} .MuiTypography-h6")
    #: Verified dead in the installed MUI 9 (2026-07-26): the predecessor
    #: selector matched neither
    #: ``.MuiTypography-root[class*='colorText']`` nor
    #: ``.MuiTypography-root.MuiTypography-colorTextSecondary``.
    #: MUI 9's ``Typography`` no longer emits any ``color``-derived class at
    #: all -- confirmed by reading ``useUtilityClasses`` in
    #: ``@mui/material@9``'s ``Typography.js``: its class list is only
    #: ``['root', variant, align*, gutterBottom, noWrap]``, and the ``color``
    #: prop (including the legacy ``MuiTypography-colorTextSecondary``-style
    #: enum values) is applied purely through the ``styled`` variants
    #: mechanism, never as a static class. ``MuiTypography-colorTextSecondary``
    #: is MUI v4 naming and was never valid for this app's MUI 9. This made
    #: ``get_error_detail()`` return ``''`` unconditionally, which is also the
    #: probable cause of the ``error_detail`` F841 in
    #: ``test_req024_invitation.py`` (#802) -- the value was never anything
    #: but an empty string, so no assertion could have used it. Fixed by
    #: addressing the element through a dedicated
    #: ``data-testid='invitation-error-detail'`` added to
    #: ``InvitationAcceptPage.tsx`` (#778 A11).
    ERROR_DETAIL = (By.CSS_SELECTOR, f"{CARD} [data-testid='invitation-error-detail']")
    DASHBOARD_BUTTON = (By.CSS_SELECTOR, f"{CARD} button.MuiButton-contained")
    DASHBOARD_BUTTON_OUTLINED = (By.CSS_SELECTOR, f"{CARD} button.MuiButton-outlined")

    #: The heading the result card renders per state, in both UI languages.
    #: The suite's default locale is German (`TC-REQ-024.md`); the i18n tests
    #: can leave a session-scoped browser on English.
    RESULT_HEADINGS = {
        "success": (
            "Einladung angenommen! Sie sind jetzt Mitglied.",
            "Invitation accepted! You are now a member.",
        ),
        "error": ("Einladung fehlgeschlagen", "Invitation failed"),
    }

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # -- Navigation --------------------------------------------------------

    def open_with_token(self, token: str) -> InvitationAcceptPage:
        """Navigate to the invitation accept page with the given token."""
        self.navigate(f"{self.PATH}?token={token}")
        return self

    def open_without_token(self) -> InvitationAcceptPage:
        """Navigate to the invitation accept page without a token."""
        self.navigate(self.PATH)
        return self

    # -- Queries -----------------------------------------------------------

    def is_loading(self) -> bool:
        """Check if the loading spinner is displayed."""
        elements = self.driver.find_elements(*self.LOADING_SPINNER)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_success(self) -> bool:
        """Check if the success state is displayed."""
        elements = self.driver.find_elements(*self.SUCCESS_ICON)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_error(self) -> bool:
        """Check if the error state is displayed."""
        elements = self.driver.find_elements(*self.ERROR_ICON)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_heading_text(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Return the result card's heading text (success or error title).

        Waits for the result state first: the heading is rendered *only* in the
        ``success``/``error`` branch (`InvitationAcceptPage.tsx:49`/`:60`).
        Before that the card shows the loading spinner, or the lazy route's
        Suspense fallback is still up (`AppRoutes.tsx:278`), and a caller
        reading straight after ``open_with_token()`` observed exactly that
        skeleton (screenshots of run ``20260725_193834``).

        Waits for *visibility*, not mere presence: presence alone is satisfied
        by a heading that is in the DOM but hidden, which is the silent-empty-
        read class `e2e-test-stability` §G forbids. A heading that never
        becomes visible raises here instead of returning ``''``.
        """
        self.wait_for_result(timeout=timeout)
        return self.wait_for_element_visible(self.HEADING, timeout=timeout).text

    def get_error_detail(self) -> str:
        """Return the error detail text."""
        elements = self.driver.find_elements(*self.ERROR_DETAIL)
        if elements and elements[0].is_displayed():
            return elements[0].text
        return ""

    def wait_for_result(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait until either success or error state is reached.

        Returns 'success' or 'error'.
        """

        def _check_result(driver):
            success = driver.find_elements(*self.SUCCESS_ICON)
            error = driver.find_elements(*self.ERROR_ICON)
            if success and success[0].is_displayed():
                return "success"
            if error and error[0].is_displayed():
                return "error"
            return False

        return self.poll(timeout).until(_check_result)

    # -- Interactions ------------------------------------------------------

    def click_dashboard_button(self) -> None:
        """Click the 'Go to Dashboard' button (available on success)."""
        btn = self.wait_for_element_clickable(self.DASHBOARD_BUTTON)
        self.scroll_and_click(btn)

    def click_dashboard_button_on_error(self) -> None:
        """Click the outlined dashboard button (available on error)."""
        btn = self.wait_for_element_clickable(self.DASHBOARD_BUTTON_OUTLINED)
        self.scroll_and_click(btn)
