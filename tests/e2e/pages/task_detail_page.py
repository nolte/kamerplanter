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

    # ── Edit-tab form fields (rendered inside the last "Bearbeiten" tab) ──
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_DUE_DATE = (By.CSS_SELECTOR, "[data-testid='form-field-due_date'] input")
    FORM_ASSIGNED_TO = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-assigned_to_user_key'] input",
    )
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")

    # ── Detail-tab MetaItem labels (no dedicated testid; matched by text) ──
    _RECURRENCE_LABELS = ("Wiederholung", "Recurrence")
    _DUE_DATE_LABELS = ("Fälligkeitsdatum", "Due Date")
    _ASSIGNED_LABELS = ("Zugewiesen an", "Assigned To")

    # ── Delete button (no data-testid; MUI error-coloured button) ─────────
    _DELETE_LABELS = ("Löschen", "Delete")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> TaskDetailPage:
        """Navigate to a task detail page by key."""
        self.navigate(f"{self.PATH_PREFIX}/{key}")
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
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
        self.wait_and_click(self.START_BUTTON)

    def has_skip_button(self) -> bool:
        """Check if the skip button is visible."""
        return len(self.driver.find_elements(*self.SKIP_BUTTON)) > 0

    def click_skip(self) -> None:
        """Click the 'Skip task' button."""
        self.wait_and_click(self.SKIP_BUTTON)

    def has_reopen_button(self) -> bool:
        """Check if the reopen button is visible."""
        return len(self.driver.find_elements(*self.REOPEN_BUTTON)) > 0

    def click_reopen(self) -> None:
        """Click the 'Reopen task' button."""
        self.wait_and_click(self.REOPEN_BUTTON)

    def has_clone_button(self) -> bool:
        """Check if the clone button is visible."""
        return len(self.driver.find_elements(*self.CLONE_BUTTON)) > 0

    def click_clone(self) -> None:
        """Click the 'Clone task' button."""
        self.wait_and_click(self.CLONE_BUTTON)

    def has_complete_submit(self) -> bool:
        """Check if the complete submit button is present."""
        return len(self.driver.find_elements(*self.COMPLETE_SUBMIT)) > 0

    def click_complete_submit(self) -> None:
        """Click the 'Complete' submit button in the complete tab."""
        self.wait_and_click(self.COMPLETE_SUBMIT)

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
        self.wait_and_click(self.CONFIRM_DIALOG_CONFIRM)

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

    # ── Edit tab ───────────────────────────────────────────────────────

    def open_edit_tab(self) -> None:
        """Open the 'Bearbeiten' (edit) tab.

        The edit tab (i18n label ``common.edit``) is always rendered as the
        last tab regardless of the task's actionable state, so it is targeted
        by its trailing index via the existing ``click_tab_by_index`` logic.
        """
        self.click_tab_by_index(self.get_tab_count() - 1)
        self.wait_for_element_visible(self.FORM_NAME)

    def set_name(self, value: str) -> None:
        """Clear and refill the task name field in the edit tab."""
        el = self.wait_for_element_clickable(self.FORM_NAME)
        self.clear_and_fill(el, value)

    def set_due_date(self, value: str) -> None:
        """Set the due-date field (native ``<input type='date'>``) to an ISO date.

        Accepts an ISO ``YYYY-MM-DD`` string.  A native date input's ``.value``
        is always ISO, but typing the ISO string with send_keys fills the
        *localized* DD.MM.YYYY segments left-to-right and produces a garbage
        date under de-DE.  Assign the value directly via the native setter and
        dispatch input/change so the React controlled field picks it up
        (mirrors ``TaskQueuePage.set_due_date_today``).
        """
        el = self.wait_for_element_clickable(self.FORM_DUE_DATE)
        self.driver.execute_script(
            "var el = arguments[0], v = arguments[1];"
            "var setter = Object.getOwnPropertyDescriptor("
            "window.HTMLInputElement.prototype, 'value').set;"
            "setter.call(el, v);"
            "el.dispatchEvent(new Event('input', {bubbles: true}));"
            "el.dispatchEvent(new Event('change', {bubbles: true}));",
            el,
            value,
        )

    def set_priority(self, value: str) -> None:
        """Open the priority FormSelectField and pick the option by enum value."""
        self.choose_select_value("priority", value)

    def set_category(self, value: str) -> None:
        """Open the category FormSelectField and pick the option by enum value."""
        self.choose_select_value("category", value)

    def set_recurrence_rule(self, value: str) -> None:
        """Open the recurrence FormSelectField and pick the option by its value.

        Valid values (dropdown-only, no free-form cron): ``''`` (none),
        ``'FREQ=DAILY'``, ``'FREQ=WEEKLY'``, ``'FREQ=WEEKLY;INTERVAL=2'`` and
        ``'FREQ=MONTHLY'``.  The empty value maps to the option testid
        ``form-option-recurrence_rule-`` and ``data-value=''``.
        """
        self.choose_select_value("recurrence_rule", value)

    def set_assigned_to(self, value: str) -> None:
        """Clear and refill the free-text 'assigned to' field."""
        el = self.wait_for_element_clickable(self.FORM_ASSIGNED_TO)
        self.clear_and_fill(el, value)

    def save_edit(self) -> None:
        """Submit the edit form and wait for confirmation.

        Clicks the ``form-submit-button``; on success a notistack snackbar is
        shown and the page reloads back into the details view.  Waits briefly
        for the snackbar as a completion signal (best effort — a missing
        snackbar does not raise).
        """
        self.scroll_and_click(self.wait_for_element_clickable(self.FORM_SUBMIT))
        try:
            self.wait_for_snackbar(timeout=5)
        except Exception:
            pass

    # ── Detail-tab value readback ──────────────────────────────────────

    def _get_detail_meta_text(self, label_variants: tuple[str, ...]) -> str:
        """Return a MetaItem value from the details tab, matched by its label.

        The details grid renders each field as a ``MetaItem``: a
        ``MuiTypography-caption`` label followed by the value node, without a
        dedicated testid.  This locates the caption whose text matches one of
        the (localized) label variants and returns the surrounding container's
        text with the label line stripped.  Returns ``''`` when the field is
        not rendered (values render conditionally).
        """
        for label in label_variants:
            els = self.driver.find_elements(
                By.XPATH,
                "//*[@data-testid='task-detail-page']"
                "//*[contains(@class, 'MuiTypography-caption')"
                f" and normalize-space()='{label}']",
            )
            if els:
                container = els[0].find_element(By.XPATH, "./..")
                text = container.text.strip()
                if text.startswith(label):
                    text = text[len(label):]
                return text.strip()
        return ""

    def get_detail_recurrence_text(self) -> str:
        """Return the recurrence value shown on the details tab (or '')."""
        return self._get_detail_meta_text(self._RECURRENCE_LABELS)

    def get_detail_due_text(self) -> str:
        """Return the due-date value shown on the details tab (or '')."""
        return self._get_detail_meta_text(self._DUE_DATE_LABELS)

    def get_detail_assigned_text(self) -> str:
        """Return the 'assigned to' value shown on the details tab (or '')."""
        return self._get_detail_meta_text(self._ASSIGNED_LABELS)

    # ── Delete ─────────────────────────────────────────────────────────

    def delete_task(self) -> None:
        """Delete the task via the header delete button and confirm dialog.

        The header delete button carries no data-testid; it is the MUI
        ``color='error'`` button in the detail header (i18n text
        ``common.delete``).  It is located robustly by its error colour class
        combined with its label text, then the generic ``ConfirmDialog`` is
        accepted via ``confirm-dialog-confirm``.
        """
        text_predicate = " or ".join(
            f"normalize-space()='{label}'" for label in self._DELETE_LABELS
        )
        button = self.wait_for_element_clickable(
            (
                By.XPATH,
                "//*[@data-testid='task-detail-page']//button["
                "(contains(@class, 'MuiButton-colorError')"
                " or contains(@class, 'MuiButton-outlinedError'))"
                f" and ({text_predicate})]",
            )
        )
        self.scroll_and_click(button)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)
        self.scroll_and_click(
            self.wait_for_element_clickable(self.CONFIRM_DIALOG_CONFIRM)
        )
