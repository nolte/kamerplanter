"""Page object for the Workflow Template List page (REQ-006)."""

from __future__ import annotations

import time
from contextlib import suppress

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage, DEFAULT_TIMEOUT, IMPLICIT_WAIT_EQUIVALENT


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
    DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root [role='dialog']")
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

    #: Unlike the `DataTable` list pages (`FertilizerListPage` et al.), this
    #: card grid renders **no** `data-testid='empty-state'` and **no**
    #: `data-testid='no-search-results'` panel -- both its "no workflows yet"
    #: and its "search matched nothing" branches are a bare, untagged `Box`
    #: (`WorkflowTemplateListPage.tsx`), and its `LoadingSkeletonCards` carries
    #: no `data-testid='loading-skeleton'` either, so `open()`'s
    #: `wait_for_loading_complete()` finds nothing to wait on and returns at
    #: once. `PAGE` still mounts synchronously, before `fetchWorkflows`
    #: resolves, so the same just-navigated pre-fetch window
    #: `wait_for_dashboard_content` was built for
    #: (`pflege_dashboard_page.py`) exists here too -- with only one settled
    #: branch to disjoin over rather than three. `suppress(AssertionError)`
    #: still bounds the truly-empty case to this wait's own budget instead of
    #: hanging, it just always takes that path here (no fast branch to reach
    #: it early), unlike the DataTable pages' empty-state/no-results shortcut.
    def wait_for_list_content(self, timeout: int = IMPLICIT_WAIT_EQUIVALENT) -> None:
        """Wait until the card grid has rendered at least one workflow card.

        Deliberately does not raise: this is an *anchor* for the readers below,
        not an assertion of its own. A tenant with no workflow templates is a
        state the caller's own assertion must still be able to observe -- it
        just costs this wait's full budget to reach, since this page renders
        no dedicated empty-state hook to short-circuit on.
        """
        with suppress(AssertionError):
            self.wait_for_any_present(
                (self.WORKFLOW_CARDS,), "workflow card grid content", timeout=timeout
            )

    def get_workflow_cards(self) -> list[WebElement]:
        """Return all visible workflow card elements."""
        return self.driver.find_elements(*self.WORKFLOW_CARDS)

    def get_card_count(self) -> int:
        """Return the number of visible workflow cards.

        Anchored on :meth:`wait_for_list_content`. Several call sites gate a
        `pytest.skip(...)` or a bidirectional count comparison on this,
        immediately after `open()` -- an unanchored `0` read in the pre-fetch
        window before `open()`'s data has arrived is indistinguishable from a
        tenant that genuinely has no workflow templates, which is the
        `has_care_card` defect class this mirrors (#946).
        """
        self.wait_for_list_content()
        return len(self.get_workflow_cards())

    #: The navigating region of a workflow card. The `Card` root carries the
    #: `workflow-card-<key>` hook but only its `CardActionArea` navigates; the
    #: `CardActions` row below it holds the apply / duplicate / delete
    #: `IconButton`s. Clicking the card's geometric centre therefore bets on
    #: the action row staying below the midpoint. Scoped to the card, so this
    #: is not an unscoped structural selector (`e2e-test-stability` §G); the
    #: product exposes no dedicated hook on the action area.
    CARD_ACTION_AREA = (By.CSS_SELECTOR, ".MuiCardActionArea-root")

    def _card_nav_target(self, card: WebElement) -> WebElement:
        """Return the card's navigating `CardActionArea`, or fail loudly."""
        areas = card.find_elements(*self.CARD_ACTION_AREA)
        if not areas:
            raise AssertionError(
                "Workflow card exposes no .MuiCardActionArea-root, so it has no "
                "unambiguous navigation target; clicking the card itself could "
                "hit the apply/duplicate/delete action row instead."
            )
        return areas[0]

    def click_card(self, index: int = 0) -> None:
        """Open the workflow at *index* via its card action area."""
        cards = self.get_workflow_cards()
        card = self.require_index(cards, index, "workflow card")
        self.scroll_and_click(self._card_nav_target(card))

    def click_card_by_name(self, name: str) -> None:
        """Open the workflow card whose text content contains *name*."""
        cards = self.get_workflow_cards()
        for card in cards:
            if name in card.text:
                self.scroll_and_click(self._card_nav_target(card))
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
        """Type *term* into the search field.

        Unlike the `DataTable` list pages, this page's filter is a plain
        `useMemo` over `searchQuery` React state -- no artificial debounce and
        no `search-chip`/`no-search-results` hook to gate on, so
        `BasePage.wait_for_search_applied`/`wait_for_no_search_results` cannot
        be used here at all (both poll for a testid this page never renders).
        The fixed sleep below is this page's only settling signal; it is far
        larger than the render it is covering for, but it remains a bet
        rather than a read-back (#946 wave 8).
        """
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(term)
        # Allow debounce/filtering to take effect
        time.sleep(0.5)

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
        self.wait_and_click(self.INSTANTIATE_BUTTON)

    def cancel_instantiate_dialog(self) -> None:
        """Cancel the instantiate dialog."""
        self.wait_and_click(self.FORM_CANCEL_BUTTON)

    # ── Confirm dialog ─────────────────────────────────────────────────

    def is_confirm_dialog_open(self) -> bool:
        """Check if a confirm dialog is visible."""
        return len(self.driver.find_elements(*self.CONFIRM_DIALOG)) > 0

    def confirm_dialog_accept(self) -> None:
        """Click the confirm button in the confirm dialog."""
        self.wait_and_click(self.CONFIRM_DIALOG_CONFIRM)

    # ── Snackbar ───────────────────────────────────────────────────────

    def wait_for_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for a notistack snackbar and return its text."""
        el = self.poll(timeout).until(EC.visibility_of_element_located(self.SNACKBAR))
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
