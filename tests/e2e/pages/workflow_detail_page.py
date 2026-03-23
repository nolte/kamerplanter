"""Page object for the Workflow Detail page (REQ-006)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage, DEFAULT_TIMEOUT


class WorkflowDetailPage(BasePage):
    """Interact with the Workflow Detail page (``/aufgaben/workflows/:key``)."""

    PATH_PREFIX = "/aufgaben/workflows"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='workflow-detail-page']")

    # ── Tabs ───────────────────────────────────────────────────────────
    TABS = (By.CSS_SELECTOR, "[role='tablist']")
    TAB_ITEMS = (By.CSS_SELECTOR, "[role='tab']")

    # ── Dialogs ────────────────────────────────────────────────────────
    DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_DIALOG_CONFIRM = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")

    # ── Snackbar (notistack) ───────────────────────────────────────────
    SNACKBAR = (By.CSS_SELECTOR, "#notistack-snackbar")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> WorkflowDetailPage:
        """Navigate to a workflow detail page by key."""
        self.navigate(f"{self.PATH_PREFIX}/{key}")
        self.wait_for_element(self.PAGE)
        return self

    # ── Page title ─────────────────────────────────────────────────────

    def get_workflow_title(self) -> str:
        """Return the page heading (workflow name)."""
        el = self.wait_for_element(
            (By.CSS_SELECTOR, "[data-testid='workflow-detail-page'] h5, [data-testid='workflow-detail-page'] h4")
        )
        return el.text

    # ── Tabs ───────────────────────────────────────────────────────────

    def get_tab_labels(self) -> list[str]:
        """Return all visible tab labels."""
        tabs = self.driver.find_elements(*self.TAB_ITEMS)
        return [t.text for t in tabs if t.text]

    def get_active_tab_label(self) -> str:
        """Return the text of the currently active tab."""
        active = self.driver.find_element(
            By.CSS_SELECTOR, "[role='tab'][aria-selected='true']"
        )
        return active.text

    def click_tab(self, label: str) -> None:
        """Click a tab by its visible label text."""
        tabs = self.driver.find_elements(*self.TAB_ITEMS)
        for t in tabs:
            if t.text == label:
                self.scroll_and_click(t)
                return
        raise ValueError(f"Tab '{label}' not found. Available: {[t.text for t in tabs]}")

    def click_tab_by_index(self, index: int) -> None:
        """Click a tab by its zero-based index."""
        tabs = self.driver.find_elements(*self.TAB_ITEMS)
        if index < len(tabs):
            self.scroll_and_click(tabs[index])
        else:
            raise IndexError(f"Tab index {index} out of range (have {len(tabs)} tabs)")

    def get_tab_count(self) -> int:
        """Return the number of visible tabs."""
        return len(self.driver.find_elements(*self.TAB_ITEMS))

    # ── Confirm dialog ─────────────────────────────────────────────────

    def is_confirm_dialog_open(self) -> bool:
        """Check if a confirm dialog is visible."""
        return len(self.driver.find_elements(*self.CONFIRM_DIALOG)) > 0

    def confirm_dialog_accept(self) -> None:
        """Click the confirm button in the confirm dialog."""
        self.wait_for_element_clickable(self.CONFIRM_DIALOG_CONFIRM).click()

    # ── Snackbar ───────────────────────────────────────────────────────

    def wait_for_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for a notistack snackbar and return its text."""
        el = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.SNACKBAR)
        )
        return el.text

    def has_snackbar(self) -> bool:
        """Check if a snackbar is currently visible."""
        return len(self.driver.find_elements(*self.SNACKBAR)) > 0

    def is_dialog_open(self) -> bool:
        """Check whether any MUI dialog is open."""
        return len(self.driver.find_elements(*self.DIALOG)) > 0
