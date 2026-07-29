"""Page object for the reusable PrintButton component (REQ-032).

The ``PrintButton`` is mounted on detail and dashboard pages where a
PDF export is offered (e.g. nutrient plan detail, pflege dashboard).
It is not a standalone route — this page object therefore only exposes
locators and helpers for interacting with the button on whatever host
page it currently lives on.

Spec: ``spec/req/REQ-032_Druckansichten-Export.md`` §6.1 PrintButton-Komponente.
Source: ``src/frontend/src/components/common/PrintButton.tsx``.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import DEFAULT_TIMEOUT, BasePage


class PrintButtonPage(BasePage):
    """Helpers for the reusable ``PrintButton`` component.

    The component renders one of two MUI variants — an ``IconButton`` (default)
    or a full ``Button`` with text label.  Both expose ``data-testid='print-button'``
    so tests find them via the same locator.

    The button triggers an async ``onPrint()`` callback that returns a Blob.
    The callback wires up to the print API client (``downloadNutrientPlanPdf``,
    ``downloadCareChecklistPdf``, ``downloadPlantLabelsPdf``) which itself
    proxies to the backend at ``GET /api/v1/t/{slug}/print/...``.
    """

    PRINT_BUTTON = (By.CSS_SELECTOR, "[data-testid='print-button']")
    PRINT_BUTTON_LOADING = (
        By.CSS_SELECTOR,
        "[data-testid='print-button'] .MuiCircularProgress-root",
    )
    SNACKBAR = (By.CSS_SELECTOR, ".MuiSnackbar-root .MuiAlert-message")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Discovery ──────────────────────────────────────────────────────

    def is_present(self) -> bool:
        """Return True if at least one PrintButton is rendered on the page."""
        return len(self.driver.find_elements(*self.PRINT_BUTTON)) > 0

    def is_visible(self) -> bool:
        """Return True if a PrintButton is rendered AND visible."""
        elements = self.driver.find_elements(*self.PRINT_BUTTON)
        return any(el.is_displayed() for el in elements)

    def get_button(self, timeout: int = DEFAULT_TIMEOUT) -> WebElement:
        """Wait for the PrintButton to appear and return the first instance."""
        return self.wait_for_element(self.PRINT_BUTTON, timeout=timeout)

    def get_aria_label(self) -> str:
        """Return the ``aria-label`` of the PrintButton (for a11y assertions)."""
        return self.get_button().get_attribute("aria-label") or ""

    def is_disabled(self) -> bool:
        """Return True if the PrintButton is disabled."""
        btn = self.get_button()
        # MUI puts the underlying <button> inside the IconButton wrapper —
        # `disabled` is reflected on the <button> element itself.
        return btn.get_attribute("disabled") is not None

    # ── Interactions ───────────────────────────────────────────────────

    def click(self) -> None:
        """Click the PrintButton.

        The browser will receive a Blob response and trigger an anchor-based
        download — the actual download is handled by the browser's headless
        download manager and is not asserted here (the file would be written
        to a temp directory inside the headless Chrome).  What this method
        guarantees is that the click reaches the component, which exercises
        the full UI → API → backend wiring.
        """
        self.scroll_and_click(self.wait_for_element_clickable(self.PRINT_BUTTON))

    def wait_for_completion(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the loading spinner disappears and the button is idle again.

        While ``onPrint()`` runs the component shows a ``CircularProgress``
        instead of the print icon.  This method waits for that spinner to
        clear so subsequent assertions don't race the network call.
        """
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.PRINT_BUTTON_LOADING)
        )

    def wait_for_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for any MUI Snackbar message to appear and return its text.

        After ``onPrint()`` resolves the component shows ``print.success``;
        on failure it shows ``print.error``.  Tests can assert on either
        without binding to a specific text via the i18n key.
        """
        el = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.SNACKBAR)
        )
        return el.text or ""
