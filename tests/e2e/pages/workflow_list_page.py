"""Page object for the Workflow Template List page (REQ-006)."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage, DEFAULT_TIMEOUT


class WorkflowListPage(BasePage):
    """Interact with the Workflow Template List page (``/aufgaben/workflows``).

    The page uses a card-based grid layout (not a DataTable).
    Each workflow is rendered as a ``Card`` with ``data-testid='workflow-card-{key}'``.
    """

    PATH = "/aufgaben/workflows"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='workflow-template-list-page']")

    # ── Action buttons ─────────────────────────────────────────────────
    CREATE_WORKFLOW_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-workflow-button']")

    # ── Search ─────────────────────────────────────────────────────────
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='workflow-search'] input")

    # ── Workflow cards ─────────────────────────────────────────────────
    WORKFLOW_CARDS = (By.CSS_SELECTOR, "[data-testid^='workflow-card-']")

    # ── Empty state ────────────────────────────────────────────────────
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

    # ── Card interactions ──────────────────────────────────────────────

    def get_workflow_cards(self) -> list[WebElement]:
        """Return all visible workflow card elements."""
        return self.driver.find_elements(*self.WORKFLOW_CARDS)

    def get_card_count(self) -> int:
        """Return the number of visible workflow cards."""
        return len(self.get_workflow_cards())

    def click_card(self, index: int = 0) -> None:
        """Click a workflow card by index."""
        cards = self.get_workflow_cards()
        if index < len(cards):
            self.scroll_and_click(cards[index])

    def click_card_by_name(self, name: str) -> None:
        """Click a workflow card whose text content contains *name*."""
        cards = self.get_workflow_cards()
        for card in cards:
            if name in card.text:
                self.scroll_and_click(card)
                return
        raise ValueError(f"Card with name '{name}' not found in workflow list")

    def get_card_titles(self) -> list[str]:
        """Return the title text from each workflow card.

        Extracts the first Typography/heading text from each card.
        """
        cards = self.get_workflow_cards()
        titles: list[str] = []
        for card in cards:
            # Card titles are rendered as Typography variant="subtitle1" or similar
            # Fall back to the first line of the card text
            text = card.text.strip()
            if text:
                titles.append(text.split("\n")[0])
            else:
                titles.append("")
        return titles

    # ── Search ─────────────────────────────────────────────────────────

    def search(self, term: str) -> None:
        """Type *term* into the search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(term)
        # Allow debounce/filtering to take effect
        time.sleep(0.5)

    def has_empty_state(self) -> bool:
        """Check if the empty state illustration is shown."""
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    # ── Buttons ────────────────────────────────────────────────────────

    def click_create_workflow(self) -> None:
        """Click the 'Create workflow' button."""
        self.wait_for_element_clickable(self.CREATE_WORKFLOW_BUTTON).click()
        self.wait_for_element_visible(self.DIALOG)

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

    def is_page_visible(self) -> bool:
        """Check whether the workflow list page container is displayed."""
        els = self.driver.find_elements(*self.PAGE)
        return len(els) > 0 and els[0].is_displayed()
