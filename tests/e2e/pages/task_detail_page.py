"""Page object for the Task Detail page (REQ-006)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage, DEFAULT_TIMEOUT


class TaskDetailPage(BasePage):
    """Interact with the Task Detail page (``/aufgaben/tasks/:key``)."""

    PATH_PREFIX = "/aufgaben/tasks"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='task-detail-page']")

    # ── Action buttons ─────────────────────────────────────────────────
    START_BUTTON = (By.CSS_SELECTOR, "[data-testid='start-task-button']")
    SKIP_BUTTON = (By.CSS_SELECTOR, "[data-testid='skip-task-button']")
    REOPEN_BUTTON = (By.CSS_SELECTOR, "[data-testid='reopen-task-button']")
    CLONE_BUTTON = (By.CSS_SELECTOR, "[data-testid='clone-task-button']")
    COMPLETE_SUBMIT = (By.CSS_SELECTOR, "[data-testid='complete-task-submit']")

    # ── Navigation links ───────────────────────────────────────────────
    PLANT_LINK = (By.CSS_SELECTOR, "[data-testid='plant-link']")

    # ── Tabs ───────────────────────────────────────────────────────────
    TABS = (By.CSS_SELECTOR, "[role='tablist']")
    TAB_ITEMS = (By.CSS_SELECTOR, "[role='tab']")

    # ── Confirm dialog ─────────────────────────────────────────────────
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_DIALOG_CONFIRM = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_DIALOG_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Snackbar (notistack) ───────────────────────────────────────────
    SNACKBAR = (By.CSS_SELECTOR, "#notistack-snackbar")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> TaskDetailPage:
        """Navigate to a task detail page by key."""
        self.navigate(f"{self.PATH_PREFIX}/{key}")
        self.wait_for_element(self.PAGE)
        return self

    # ── Page title ─────────────────────────────────────────────────────

    def get_task_title(self) -> str:
        """Return the page heading (task name) from the Typography h5/h6."""
        el = self.wait_for_element(
            (By.CSS_SELECTOR, "[data-testid='page-title']")
        )
        return el.text

    def get_page_text(self) -> str:
        """Return the visible text content of the page container."""
        el = self.wait_for_element(self.PAGE)
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

    # ── Action buttons ─────────────────────────────────────────────────

    def has_start_button(self) -> bool:
        """Check if the start button is visible."""
        return len(self.driver.find_elements(*self.START_BUTTON)) > 0

    def click_start(self) -> None:
        """Click the 'Start task' button."""
        self.wait_for_element_clickable(self.START_BUTTON).click()

    def has_skip_button(self) -> bool:
        """Check if the skip button is visible."""
        return len(self.driver.find_elements(*self.SKIP_BUTTON)) > 0

    def click_skip(self) -> None:
        """Click the 'Skip task' button."""
        self.wait_for_element_clickable(self.SKIP_BUTTON).click()

    def has_reopen_button(self) -> bool:
        """Check if the reopen button is visible."""
        return len(self.driver.find_elements(*self.REOPEN_BUTTON)) > 0

    def click_reopen(self) -> None:
        """Click the 'Reopen task' button."""
        self.wait_for_element_clickable(self.REOPEN_BUTTON).click()

    def has_clone_button(self) -> bool:
        """Check if the clone button is visible."""
        return len(self.driver.find_elements(*self.CLONE_BUTTON)) > 0

    def click_clone(self) -> None:
        """Click the 'Clone task' button."""
        self.wait_for_element_clickable(self.CLONE_BUTTON).click()

    def has_complete_submit(self) -> bool:
        """Check if the complete submit button is present."""
        return len(self.driver.find_elements(*self.COMPLETE_SUBMIT)) > 0

    def click_complete_submit(self) -> None:
        """Click the 'Complete' submit button in the complete tab."""
        self.wait_for_element_clickable(self.COMPLETE_SUBMIT).click()

    # ── Plant link ─────────────────────────────────────────────────────

    def has_plant_link(self) -> bool:
        """Check if a plant link is present on the detail page."""
        return len(self.driver.find_elements(*self.PLANT_LINK)) > 0

    def click_plant_link(self) -> None:
        """Click the plant link to navigate to the plant detail page."""
        self.wait_for_element_clickable(self.PLANT_LINK).click()

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
