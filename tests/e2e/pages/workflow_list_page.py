"""Page object for the Workflow Template List page (REQ-006)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage, DEFAULT_TIMEOUT


class WorkflowListPage(BasePage):
    """Interact with the Workflow Template List page (``/aufgaben/workflows``)."""

    PATH = "/aufgaben/workflows"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='workflow-template-list-page']")

    # ── Action buttons ─────────────────────────────────────────────────
    GENERATE_WORKFLOW_BUTTON = (By.CSS_SELECTOR, "[data-testid='generate-workflow-button']")
    CREATE_WORKFLOW_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-workflow-button']")

    # ── DataTable locators (shared with other list pages) ──────────────
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # ── Dialogs ────────────────────────────────────────────────────────
    DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_DIALOG_CONFIRM = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_DIALOG_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Instantiate dialog ─────────────────────────────────────────────
    PLANT_SELECT = (By.CSS_SELECTOR, "[data-testid='plant-select']")
    INSTANTIATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='instantiate-button']")
    FORM_CANCEL_BUTTON = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # ── Snackbar (notistack) ───────────────────────────────────────────
    SNACKBAR = (By.CSS_SELECTOR, "#notistack-snackbar")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> WorkflowListPage:
        """Navigate to the workflow template list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Table interactions ─────────────────────────────────────────────

    def get_row_count(self) -> int:
        """Return the number of visible table rows."""
        return len(self.driver.find_elements(*self.TABLE_ROWS))

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table'] th"
        )
        return [h.text for h in headers if h.text]

    def click_row(self, index: int = 0) -> None:
        """Click a row by index."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])

    def click_row_by_name(self, name: str) -> None:
        """Click a row whose first cell matches *name*."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells and name in cells[0].text:
                self.scroll_and_click(row)
                return
        raise ValueError(f"Row with name '{name}' not found in workflow table")

    def get_first_column_texts(self) -> list[str]:
        """Return the text of the Name column for all rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        texts = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                texts.append(cells[0].text)
        return texts

    def get_row_texts(self) -> list[list[str]]:
        """Return all cell texts for every visible row."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            result.append([c.text for c in cells])
        return result

    # ── Search ─────────────────────────────────────────────────────────

    def search(self, term: str) -> None:
        """Type *term* into the search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(term)

    def has_search_chip(self) -> bool:
        """Check if the search chip is visible."""
        return len(self.driver.find_elements(*self.SEARCH_CHIP)) > 0

    def has_empty_state(self) -> bool:
        """Check if the empty state illustration is shown."""
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    def get_showing_count_text(self) -> str:
        """Return the 'Showing X of Y' text."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    # ── Buttons ────────────────────────────────────────────────────────

    def click_generate_workflow(self) -> None:
        """Click the 'Generate from species' button."""
        self.wait_for_element_clickable(self.GENERATE_WORKFLOW_BUTTON).click()
        self.wait_for_element_visible(self.DIALOG)

    def click_create_workflow(self) -> None:
        """Click the 'Create workflow' button."""
        self.wait_for_element_clickable(self.CREATE_WORKFLOW_BUTTON).click()
        self.wait_for_element_visible(self.DIALOG)

    def has_generate_button(self) -> bool:
        """Check if the generate workflow button is present."""
        return len(self.driver.find_elements(*self.GENERATE_WORKFLOW_BUTTON)) > 0

    def has_create_button(self) -> bool:
        """Check if the create workflow button is present."""
        return len(self.driver.find_elements(*self.CREATE_WORKFLOW_BUTTON)) > 0

    # ── Instantiate dialog ─────────────────────────────────────────────

    def is_instantiate_dialog_open(self) -> bool:
        """Check if the instantiate dialog is visible."""
        return len(self.driver.find_elements(*self.INSTANTIATE_BUTTON)) > 0

    def click_instantiate_button(self) -> None:
        """Click the 'Apply' / 'Instantiate' button in the dialog."""
        self.wait_for_element_clickable(self.INSTANTIATE_BUTTON).click()

    def cancel_instantiate_dialog(self) -> None:
        """Cancel the instantiate dialog."""
        self.wait_for_element_clickable(self.FORM_CANCEL_BUTTON).click()

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
