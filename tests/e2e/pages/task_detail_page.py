"""Page object for the Task Detail page (REQ-006)."""

from __future__ import annotations

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage, DEFAULT_TIMEOUT, raw_reference


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
    DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='delete-task-button']")
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
        el = self.wait_for_element((By.CSS_SELECTOR, "[data-testid='page-title']"))
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
        active = self.find_present((By.CSS_SELECTOR, "[role='tab'][aria-selected='true']"))
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
        el = self.poll(timeout).until(EC.visibility_of_element_located(self.SNACKBAR))
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

    #: Inline validation errors MUI renders under a rejected field.
    FORM_FIELD_ERRORS = (By.CSS_SELECTOR, ".MuiFormHelperText-root.Mui-error")

    #: Budget for the "did the submit register?" post-condition.
    #:
    #: Sized when each negative poll paid the session's implicit wait for the
    #: absent snackbar, so 8 s was "more than one iteration". #835 removed that
    #: wait and the arithmetic behind this number went with it -- an absent
    #: snackbar is an instant answer now.
    #:
    #: Left at 8 s deliberately. Cutting it can only be justified by measuring
    #: what the post-condition now costs across the profiles, and the value is
    #: not on the failure path of the removal: too *generous* a budget costs
    #: seconds on a genuine failure and nothing at all on a pass. Re-cutting it
    #: on the same commit that removed the wait would also confound the two
    #: effects in precisely the run that has to tell them apart.
    SUBMIT_REGISTERED_TIMEOUT = 8

    def _get_field_errors(self) -> list[str]:
        """Return the inline validation errors currently rendered on the form."""
        return [e.text for e in self.driver.find_elements(*self.FORM_FIELD_ERRORS) if e.text]

    def _submit_registered(self) -> bool:
        """Return whether the click actually handed the form over to ``onSave``.

        ``FormActions`` renders the submit button as
        ``disabled={loading || disabled}``, and the edit tab feeds it
        ``loading={saving}`` / ``disabled={!isDirty}``. So *every* state that
        follows a registered submit disables the button -- the in-flight PUT
        (``saving``), and the ``resetEdit()`` that ``load()`` performs afterwards
        (``!isDirty``) -- while a click that never reached the button leaves it
        enabled on a still-dirty form. A form that unmounted (the reload's
        loading state) or a stale reference likewise means the submit ran.

        A visible snackbar also counts: on a *rejected* save the error handler
        toasts and the form goes dirty-and-enabled again, which the button state
        alone cannot tell apart from a swallowed click. It is probed *last*
        because it used to cost the full implicit wait when absent, while the
        button state is a present-element read and therefore instant. #835
        removed that wait, so the two probes now cost the same; the order is
        kept because it is also the right one on meaning — the button state is
        the direct evidence and the snackbar is the corroborating signal.

        **This is the suite's only staleness verdict whose answer is a success
        signal**, so it is the one place where a self-healing reference would not
        merely change an answer but manufacture a pass: the healed replacement
        would report on the re-rendered form, and "the form I clicked is gone"
        would become "wait, then read the new one". `raw_reference` strips the
        healing before the read (#835 P4). It is a no-op on the raw element
        `find_elements` yields today and stays correct if that ever changes --
        the verdict must not depend on which lookup paths happen to be wrapped.
        """
        buttons = self.driver.find_elements(*self.FORM_SUBMIT)
        if not buttons:
            return True
        try:
            if not raw_reference(buttons[0]).is_enabled():
                return True
        except StaleElementReferenceException:
            return True
        return self.has_snackbar()

    def save_edit(self) -> None:
        """Submit the edit form and wait for the save to be confirmed.

        The submit is clicked coordinate-free
        (:meth:`BasePage.click_coordinate_free`). This form's action row is the
        last child of a page roughly two viewports tall on the mobile profile,
        so it is scroll-clamped against the bottom of the document and a
        coordinate dispatch lands next to it without raising -- the whole
        ``TestTaskUpdatePropagation`` class failed that way (run
        ``20260725_113337``: still-dirty form, enabled submit, no field errors,
        no ``PUT /api/v1/t/{slug}/tasks/{key}`` in the backend log) while every
        desktop profile passed.

        Then two post-conditions, in order of increasing strength:

        1. the submit *registered* -- otherwise the click was swallowed or
           react-hook-form rejected the input, which is a different defect from
           a missing snackbar and now says so by name;
        2. ``onSave`` reported an outcome through notistack -- it toasts on every
           branch (success message, or the error handler's), so the absence of a
           snackbar means the request never resolved into user-visible feedback.

        Both fail loudly. The predecessor's ``except Exception: pass`` made a
        non-submitting form look like a successful save and pushed the failure
        into a later, misleading "the value did not change" assertion.
        """
        self.wait_and_click_coordinate_free(self.FORM_SUBMIT)
        try:
            self.poll(self.SUBMIT_REGISTERED_TIMEOUT).until(lambda _d: self._submit_registered())
        except TimeoutException:
            raise AssertionError(
                "Task edit form: the click on form-submit-button did not register "
                "— the button is still enabled, i.e. the form is still dirty and "
                "no save is in flight. Either the click never reached the button, "
                "or react-hook-form rejected the input "
                f"(field_errors={self._get_field_errors()})"
            ) from None
        try:
            self.wait_for_snackbar(timeout=10)
        except TimeoutException:
            submit = self.driver.find_elements(*self.FORM_SUBMIT)
            raise AssertionError(
                "Task edit form: the submit registered but no snackbar appeared "
                "within 10s — onSave reported neither success nor an error "
                f"(submit_enabled={submit[0].is_enabled() if submit else None}, "
                f"field_errors={self._get_field_errors()})"
            ) from None

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
                    text = text[len(label) :]
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

        Addressed by its own hook (``delete-task-button``,
        `TaskDetailPage.tsx:696`), like its siblings in the same action group.
        This replaces a hand-rolled XPath that coupled to *both* MUI's
        colour classes (``MuiButton-colorError``/``MuiButton-outlinedError``)
        and the translated label -- so a variant change or a copy edit in
        either locale silently stopped resolving the button.
        """
        self.wait_and_click(self.DELETE_BUTTON)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)
        self.scroll_and_click(self.wait_for_element_clickable(self.CONFIRM_DIALOG_CONFIRM))
