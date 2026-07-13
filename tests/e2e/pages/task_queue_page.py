"""Page object for the Task Queue page (REQ-006)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage, DEFAULT_TIMEOUT


class TaskQueuePage(BasePage):
    """Interact with the Task Queue page (``/aufgaben/queue``)."""

    PATH = "/aufgaben/queue"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='task-queue-page']")

    # ── Action buttons ─────────────────────────────────────────────────
    CREATE_TASK_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-task-button']")
    GENERATE_REMINDERS_BUTTON = (By.CSS_SELECTOR, "[data-testid='generate-reminders-button']")
    BULK_MODE_BUTTON = (By.CSS_SELECTOR, "[data-testid='bulk-mode-button']")
    EXIT_BULK_MODE = (By.CSS_SELECTOR, "[data-testid='exit-bulk-mode']")

    # ── Bulk action bar ────────────────────────────────────────────────
    BULK_ACTION_BAR = (By.CSS_SELECTOR, "[data-testid='bulk-action-bar']")
    SELECT_ALL_BUTTON = (By.CSS_SELECTOR, "[data-testid='select-all-button']")
    BULK_COMPLETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='bulk-complete-button']")
    BULK_SKIP_BUTTON = (By.CSS_SELECTOR, "[data-testid='bulk-skip-button']")
    BULK_DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='bulk-delete-button']")

    # ── Filters ────────────────────────────────────────────────────────
    FILTER_ALL = (By.CSS_SELECTOR, "[data-testid='filter-all']")
    FILTER_TASKS = (By.CSS_SELECTOR, "[data-testid='filter-tasks']")
    FILTER_CARE = (By.CSS_SELECTOR, "[data-testid='filter-care']")
    FILTER_CATEGORY = (By.CSS_SELECTOR, "[data-testid='filter-category']")
    FILTER_PLANT = (By.CSS_SELECTOR, "[data-testid='filter-plant']")

    # ── Task cards ─────────────────────────────────────────────────────
    TASK_CARD = (By.CSS_SELECTOR, "[data-testid='task-card']")

    # ── Task sections (urgency groups) ─────────────────────────────────
    TASK_SECTION_OVERDUE = (By.CSS_SELECTOR, "[data-testid='task-section-overdue']")
    TASK_SECTION_TODAY = (By.CSS_SELECTOR, "[data-testid='task-section-today']")
    TASK_SECTION_WEEK = (By.CSS_SELECTOR, "[data-testid='task-section-thisWeek']")
    TASK_SECTION_FUTURE = (By.CSS_SELECTOR, "[data-testid='task-section-future']")

    # ── Create dialog (MUI Dialog) ─────────────────────────────────────
    CREATE_DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")

    # ── Snackbar (notistack) ───────────────────────────────────────────
    SNACKBAR = (By.CSS_SELECTOR, "#notistack-snackbar")

    # ── Confirm dialog ─────────────────────────────────────────────────
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_DIALOG_CONFIRM = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_DIALOG_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> TaskQueuePage:
        """Navigate to the task queue and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Task card interactions ─────────────────────────────────────────

    def get_task_cards(self) -> list[WebElement]:
        """Return all visible task card elements."""
        return self.driver.find_elements(*self.TASK_CARD)

    def get_task_card_count(self) -> int:
        """Return the number of visible task cards."""
        return len(self.get_task_cards())

    def get_task_card_by_key(self, key: str) -> WebElement:
        """Return the task card element for a specific task key."""
        return self.wait_for_element(
            (By.CSS_SELECTOR, f"[data-testid='task-card-{key}']")
        )

    def click_task_card(self, key: str) -> None:
        """Click a task card to navigate to its detail page."""
        card = self.get_task_card_by_key(key)
        self.scroll_and_click(card)

    def get_first_task_card(self) -> WebElement | None:
        """Return the first task card, or None if no cards exist."""
        cards = self.get_task_cards()
        return cards[0] if cards else None

    def get_task_keys(self) -> list[str]:
        """Return a list of task keys from the visible task-card-{key} elements."""
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='task-card-']"
        )
        keys = []
        for el in elements:
            testid = el.get_attribute("data-testid") or ""
            if testid.startswith("task-card-"):
                keys.append(testid.replace("task-card-", ""))
        return keys

    @staticmethod
    def _task_card_inner_locator() -> tuple[str, str]:
        """Return a locator for inner task card elements with key-based testids."""
        return (By.CSS_SELECTOR, "[data-testid^='task-card-']")

    # ── Task quick actions ─────────────────────────────────────────────

    def start_task(self, key: str) -> None:
        """Click the start button on a task card."""
        btn = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='start-task-{key}']")
        )
        self.scroll_and_click(btn)

    def complete_task(self, key: str) -> None:
        """Click the complete button on a task card."""
        btn = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='complete-task-{key}']")
        )
        self.scroll_and_click(btn)

    def skip_task(self, key: str) -> None:
        """Click the skip button on a task card."""
        btn = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='skip-task-{key}']")
        )
        self.scroll_and_click(btn)

    # ── Urgency sections ───────────────────────────────────────────────

    def get_visible_sections(self) -> list[str]:
        """Return a list of visible urgency section testids."""
        sections = []
        for name, locator in [
            ("overdue", self.TASK_SECTION_OVERDUE),
            ("today", self.TASK_SECTION_TODAY),
            ("week", self.TASK_SECTION_WEEK),
            ("future", self.TASK_SECTION_FUTURE),
        ]:
            if self.driver.find_elements(*locator):
                sections.append(name)
        return sections

    def get_section_task_count(self, section: str) -> int:
        """Return the number of task cards inside a section."""
        section_el = self.driver.find_elements(
            By.CSS_SELECTOR, f"[data-testid='task-section-{section}']"
        )
        if not section_el:
            return 0
        return len(section_el[0].find_elements(*self.TASK_CARD))

    # ── Filter interactions ────────────────────────────────────────────

    def click_filter_all(self) -> None:
        """Click the 'All' filter toggle button."""
        self.wait_for_element_clickable(self.FILTER_ALL).click()

    def click_filter_tasks(self) -> None:
        """Click the 'Tasks only' filter toggle button."""
        self.wait_for_element_clickable(self.FILTER_TASKS).click()

    def click_filter_care(self) -> None:
        """Click the 'Care only' filter toggle button."""
        self.wait_for_element_clickable(self.FILTER_CARE).click()

    def has_category_filter(self) -> bool:
        """Check whether the category filter dropdown is present."""
        return len(self.driver.find_elements(*self.FILTER_CATEGORY)) > 0

    def select_category_filter(self, category_text: str) -> None:
        """Open the category filter and select an option."""
        dropdown = self.wait_for_element_clickable(self.FILTER_CATEGORY)
        self.scroll_and_click(dropdown)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{category_text}')]")
        )
        option.click()

    # ── Bulk mode ──────────────────────────────────────────────────────

    def enter_bulk_mode(self) -> None:
        """Activate bulk selection mode."""
        self.wait_for_element_clickable(self.BULK_MODE_BUTTON).click()
        self.wait_for_element(self.EXIT_BULK_MODE)

    def exit_bulk_mode(self) -> None:
        """Exit bulk selection mode."""
        self.wait_for_element_clickable(self.EXIT_BULK_MODE).click()

    def is_bulk_mode_active(self) -> bool:
        """Check if bulk mode is active (exit button visible)."""
        return len(self.driver.find_elements(*self.EXIT_BULK_MODE)) > 0

    def select_task_for_bulk(self, key: str) -> None:
        """Toggle the bulk selection checkbox for a task."""
        checkbox = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='bulk-select-{key}']")
        )
        self.scroll_and_click(checkbox)

    def click_select_all(self) -> None:
        """Click the 'Select all' button in bulk action bar."""
        self.wait_for_element_clickable(self.SELECT_ALL_BUTTON).click()

    def click_bulk_complete(self) -> None:
        """Click the bulk complete button."""
        self.wait_for_element_clickable(self.BULK_COMPLETE_BUTTON).click()

    def click_bulk_skip(self) -> None:
        """Click the bulk skip button."""
        self.wait_for_element_clickable(self.BULK_SKIP_BUTTON).click()

    def click_bulk_delete(self) -> None:
        """Click the bulk delete button."""
        self.wait_for_element_clickable(self.BULK_DELETE_BUTTON).click()

    def is_bulk_action_bar_visible(self) -> bool:
        """Check if the bulk action bar is displayed."""
        return len(self.driver.find_elements(*self.BULK_ACTION_BAR)) > 0

    # ── Create task ────────────────────────────────────────────────────

    def click_create_task(self) -> None:
        """Click the create task button and wait for the dialog."""
        self.wait_for_element_clickable(self.CREATE_TASK_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Check whether the create dialog is visible."""
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    # ── Create-task dialog field setters (TaskCreateDialog) ────────────

    TASK_DIALOG = (By.CSS_SELECTOR, "[data-testid='task-create-dialog']")
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_DUE_DATE = (By.CSS_SELECTOR, "[data-testid='form-field-due_date'] input")
    FORM_ENTITY_KEY_INPUT = (By.CSS_SELECTOR, "[data-testid='form-field-entity_key'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")

    def fill_task_name(self, name: str) -> None:
        """Fill the task name field."""
        el = self.wait_for_element_clickable(self.FORM_NAME)
        self.clear_and_fill(el, name)

    def select_task_category(self, category_value: str) -> None:
        """Open the category MUI Select and pick the option by its enum value."""
        self._select_form_option("category", category_value)

    def select_task_priority(self, priority_value: str) -> None:
        """Open the priority MUI Select and pick the option by its enum value."""
        self._select_form_option("priority", priority_value)

    def _select_form_option(self, field_name: str, value: str) -> None:
        """Open a FormSelectField MUI Select and pick the option by its stable value.

        Delegates to the robust BasePage helper, which opens the dropdown via the
        dedicated ``form-field-{name}-trigger`` testid (no brittle
        ``.MuiSelect-select`` class), selects by ``data-value`` (i18n-independent),
        centres+JS-clicks to survive the Popover animation, and closes via the
        option click (no stray body-level ESCAPE that would close the dialog).
        """
        self.choose_select_value(field_name, value)

    def set_due_date_today(self) -> None:
        """Set the due-date input to today's date (native ``<input type='date'>``).

        A native date input's ``.value`` is always ISO (YYYY-MM-DD), but typing
        that ISO string with send_keys fills the *localized* DD.MM.YYYY segments
        left-to-right and produces a garbage date (observed: year 60713 under
        de-DE), which blocks the create-task submit. Assign the value directly via
        the native setter and dispatch input/change so the React controlled field
        picks it up, instead of typing it.
        """
        from datetime import date

        el = self.wait_for_element_clickable(self.FORM_DUE_DATE)
        self.driver.execute_script(
            "var el = arguments[0], v = arguments[1];"
            "var setter = Object.getOwnPropertyDescriptor("
            "window.HTMLInputElement.prototype, 'value').set;"
            "setter.call(el, v);"
            "el.dispatchEvent(new Event('input', {bubbles: true}));"
            "el.dispatchEvent(new Event('change', {bubbles: true}));",
            el,
            date.today().isoformat(),
        )

    def select_task_plant_by_text(self, text: str) -> bool:
        """Type *text* into the plant autocomplete and pick the matching option."""
        import time

        input_el = self.wait_for_element_clickable(self.FORM_ENTITY_KEY_INPUT)
        input_el.click()
        self.clear_and_fill(input_el, text)
        time.sleep(0.4)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        if options:
            options[0].click()
            time.sleep(0.2)
            return True
        return False

    def submit_task_form(self) -> None:
        """Submit the create-task form."""
        self.scroll_and_click(self.wait_for_element_clickable(self.FORM_SUBMIT))

    # ── Task lookup by name (self-provisioning journey) ────────────────

    def find_task_key_by_name(self, name: str) -> str | None:
        """Return the key of the task card whose text contains *name*.

        The outer card carries ``data-testid='task-card-{key}'``; this parses
        the key so the journey can target the correct complete-button without
        relying on card ordering.
        """
        cards = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='task-card-']"
        )
        for card in cards:
            testid = card.get_attribute("data-testid") or ""
            if not testid.startswith("task-card-"):
                continue
            if name in card.text:
                return testid.replace("task-card-", "")
        return None

    def has_task_with_name(self, name: str) -> bool:
        """Return True if any task card text contains *name*."""
        return self.find_task_key_by_name(name) is not None

    # ── Generate reminders ─────────────────────────────────────────────

    def click_generate_reminders(self) -> None:
        """Click the generate care reminders button."""
        self.wait_for_element_clickable(self.GENERATE_REMINDERS_BUTTON).click()

    # ── Confirm dialog ─────────────────────────────────────────────────

    def is_confirm_dialog_open(self) -> bool:
        """Check if a confirm dialog is visible."""
        return len(self.driver.find_elements(*self.CONFIRM_DIALOG)) > 0

    def confirm_dialog_accept(self) -> None:
        """Click the confirm button in the confirm dialog."""
        self.wait_for_element_clickable(self.CONFIRM_DIALOG_CONFIRM).click()

    def confirm_dialog_cancel(self) -> None:
        """Click the cancel button in the confirm dialog."""
        self.wait_for_element_clickable(self.CONFIRM_DIALOG_CANCEL).click()

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

    # ── Element visibility helpers ────────────────────────────────────

    def is_page_visible(self) -> bool:
        """Check whether the task queue page container is displayed."""
        els = self.driver.find_elements(*self.PAGE)
        return len(els) > 0 and els[0].is_displayed()

    def is_create_button_visible(self) -> bool:
        """Check whether the create task button is displayed."""
        els = self.driver.find_elements(*self.CREATE_TASK_BUTTON)
        return len(els) > 0 and els[0].is_displayed()

    def is_generate_reminders_visible(self) -> bool:
        """Check whether the generate reminders button is displayed."""
        els = self.driver.find_elements(*self.GENERATE_REMINDERS_BUTTON)
        return len(els) > 0 and els[0].is_displayed()

    def is_filter_visible(self, locator: tuple[str, str]) -> bool:
        """Check whether a filter toggle element is present."""
        return len(self.driver.find_elements(*locator)) > 0
