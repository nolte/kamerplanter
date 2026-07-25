"""Page object for the Plant Instance detail page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class PlantInstanceDetailPage(BasePage):
    """Interact with a Plant Instance detail page."""

    PATH_PREFIX = "/pflanzen/plant-instances"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='plant-instance-detail-page']")
    TRANSITION_BUTTON = (By.CSS_SELECTOR, "[data-testid='transition-button']")
    REMOVE_BUTTON = (By.CSS_SELECTOR, "[data-testid='remove-button']")
    PLANT_INFO_CARD = (By.CSS_SELECTOR, "[data-testid='plant-info-card']")
    PHASE_INFO_CARD = (By.CSS_SELECTOR, "[data-testid='phase-info-card']")
    CURRENT_PHASE = (By.CSS_SELECTOR, "[data-testid='current-phase']")
    PHASE_HISTORY = (By.CSS_SELECTOR, "[data-testid='phase-history']")
    PHASE_HISTORY_ROWS = (By.CSS_SELECTOR, "[data-testid='phase-history'] tbody tr")
    PHASES_TAB = (By.CSS_SELECTOR, "[data-testid='phases-tab']")
    PHASES_TAB_CONTENT = (By.CSS_SELECTOR, "[data-testid='phases-tab-content']")

    # Tab navigation for the Gießprotokoll (#watering-log) and Aufgabenverlauf
    # (#tasks) tabs. The watering-log tab exposes NO dedicated data-testid, so it
    # is reached via the URL hash (useTabUrl maps '#watering-log' -> tab index 3)
    # and the wait is keyed on its durable create-button; the tasks tab carries
    # data-testid='tasks-tab' (hash '#tasks' -> tab index 6).
    TASKS_TAB = (By.CSS_SELECTOR, "[data-testid='tasks-tab']")
    WATERING_LOG_CREATE_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='create-watering-log-button']",
    )
    TASK_CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='plant-task-create-button']")
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    DATA_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # DataTable aria-labels for the two task-history sections (i18n de) — the
    # active table lists pending/in-progress tasks, the done table the completed/
    # cancelled ones. Used to scope row lookups to a single section.
    TASK_ACTIVE_SECTION_LABEL = "Ausstehend & In Bearbeitung"
    TASK_DONE_SECTION_LABEL = "Abgeschlossen & Abgebrochen"
    # Care-reminder task name suffix (em dash + reminder type), e.g.
    # "JOURNEY-004-123456 — watering".
    WATERING_TASK_SUFFIX = "— watering"

    # Transition dialog
    TRANSITION_DIALOG = (By.CSS_SELECTOR, "[data-testid='phase-transition-dialog']")
    #: Presence/visibility locator only — the testid sits on the ``TextField``
    #: FormControl root (label + input + helper text), whose click centre falls
    #: outside the input once the helper text wraps to two lines (393px). Open
    #: the dropdown via ``open_select_by_testid`` instead. See the twin note in
    #: ``phase_transition_page.PlantInstanceDetailExt``.
    TARGET_PHASE_SELECT = (By.CSS_SELECTOR, "[data-testid='target-phase-select']")
    TARGET_PHASE_SELECT_TESTID = "target-phase-select"
    TRANSITION_REASON = (By.CSS_SELECTOR, "[data-testid='transition-reason'] input")
    TRANSITION_CANCEL = (By.CSS_SELECTOR, "[data-testid='transition-cancel']")
    TRANSITION_CONFIRM = (By.CSS_SELECTOR, "[data-testid='transition-confirm']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # Error display locator
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")

    def open(self, key: str) -> PlantInstanceDetailPage:
        """Navigate to the plant instance detail page.

        Waits for either the detail page or an error display to appear,
        so that tests for non-existent keys do not timeout.
        """
        from selenium.webdriver.support.ui import WebDriverWait

        self.navigate(f"{self.PATH_PREFIX}/{key}")
        WebDriverWait(self.driver, 15).until(
            lambda d: (
                d.find_elements(*self.PAGE)
                or d.find_elements(*self.ERROR_DISPLAY)
            )
        )
        return self

    def open_watering_log_tab(self, key: str) -> PlantInstanceDetailPage:
        """Open the plant's Gießprotokoll tab (``#watering-log``) and wait for it.

        The tab has no data-testid, so navigation is by URL hash and the wait is
        condition-based on the tab's durable create-button (only rendered while
        the watering-log tab is active) — never a fixed sleep.
        """
        self.navigate(f"{self.PATH_PREFIX}/{key}#watering-log")
        self.wait_for_element(self.PAGE)
        self.wait_for_element_visible(self.WATERING_LOG_CREATE_BUTTON)
        self.wait_for_loading_complete()
        return self

    def open_tasks_tab(self, key: str) -> PlantInstanceDetailPage:
        """Open the plant's Aufgabenverlauf tab (``#tasks``) and wait for content.

        Navigates via the URL hash (useTabUrl maps '#tasks' -> the tasks tab),
        waits for the tasks-tab marker and the per-plant task fetch to settle,
        then for the populated-tab create-button (this suite always provisions at
        least one task, so the empty state never renders).
        """
        self.navigate(f"{self.PATH_PREFIX}/{key}#tasks")
        self.wait_for_element(self.PAGE)
        self.wait_for_element_visible(self.TASKS_TAB)
        self.wait_for_loading_complete()
        self.wait_for_element_visible(self.TASK_CREATE_BUTTON)
        return self

    def get_watering_log_row_count(self) -> int:
        """Return the number of rows in the (single) watering-log tab DataTable."""
        return len(self.driver.find_elements(*self.DATA_TABLE_ROWS))

    def get_watering_log_rows(self) -> list[WebElement]:
        """Return the watering-log tab DataTable rows (newest first by loggedAt)."""
        return self.driver.find_elements(*self.DATA_TABLE_ROWS)

    def get_task_rows(self, section_label: str) -> list[WebElement]:
        """Return the DataTable rows for a task-history section, layout-tolerantly.

        *section_label* is one of :attr:`TASK_ACTIVE_SECTION_LABEL` /
        :attr:`TASK_DONE_SECTION_LABEL`. Returns ``[]`` when the section is not
        rendered — which is exact rather than silent: both the section heading
        and the DataTable are only mounted while the section holds ≥1 task.

        Below `DataTable`'s ``mobileBreakpoint`` (``sm`` = 600px, i.e. the
        mobile profile) the tasks tab renders `MobileCard`s: there is no
        ``<table>``, hence no ``aria-label`` to scope by, and the previous
        ``table[aria-label='…']`` scope silently yielded ``[]`` for every
        section. Fall back to the section's own heading, which is fed from the
        *same* i18n string as the aria-label and sits as the DataTable's
        preceding sibling in both layouts.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            f"table[aria-label='{section_label}'] [data-testid='data-table-row']",
        )
        if rows:
            return rows
        return self.driver.find_elements(
            By.XPATH,
            f"//*[normalize-space(text())=\"{section_label}\"]"
            "/following-sibling::*[@data-testid='data-table']"
            "//*[@data-testid='data-table-row']",
        )

    #: `MobileCard` slot that carries each section's subtitle, per the tasks-tab
    #: ``mobileCardRenderer`` (PlantInstanceDetailPage.tsx): the active cards
    #: subtitle the relative due date, the archived ones the completion date.
    TASK_CARD_SUBTITLE_COLUMN = {
        TASK_ACTIVE_SECTION_LABEL: "due_date",
        TASK_DONE_SECTION_LABEL: "completed_at",
    }

    def get_task_field(self, row: WebElement, section_label: str, col_id: str) -> str:
        """Return a task row's *col_id* value in both the table and card layout.

        Desktop reads ``[data-testid='cell-<col_id>']``; a cell that exists but
        renders empty is read via ``textContent``, because `DataTable` keeps
        ``hideBelowBreakpoint`` columns (``category``, ``completed_at``,
        ``priority``) mounted with ``display: none`` below ``md``.

        In the card layout there is no ``<td>`` and no per-field testid, so
        only the two `MobileCard` slots the renderer actually fills can be
        read; any other column raises rather than returning a silent ``''``.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        if cells:
            return (cells[0].text or self._text_content(cells[0])).strip()
        if col_id == "name":
            return self.get_card_title(row)
        if col_id == self.TASK_CARD_SUBTITLE_COLUMN.get(section_label):
            return self.get_card_subtitle(row)
        raise AssertionError(
            f"Task column '{col_id}' is not readable in the mobile card layout "
            f"(section '{section_label}' renders only the task name and "
            f"'{self.TASK_CARD_SUBTITLE_COLUMN.get(section_label)}'); the card "
            "exposes no per-field testid to address it by."
        )

    def _is_watering_task(self, row: WebElement, section_label: str) -> bool:
        """Return True if *row* is a ``— watering`` care-reminder task."""
        name = self.get_task_field(row, section_label, "name")
        return name.endswith(self.WATERING_TASK_SUFFIX)

    def count_watering_tasks(self, section_label: str) -> int:
        """Count rows whose name ends with ``— watering`` in a task-history section."""
        return sum(
            1
            for row in self.get_task_rows(section_label)
            if self._is_watering_task(row, section_label)
        )

    def get_watering_task_cell(self, section_label: str, col_id: str) -> str:
        """Return *col_id*'s value for the first ``— watering`` row in a section."""
        for row in self.get_task_rows(section_label):
            if self._is_watering_task(row, section_label):
                return self.get_task_field(row, section_label, col_id)
        return ""

    def get_current_phase(self) -> str:
        """Return the text of the current-phase Chip."""
        el = self.wait_for_element_visible(self.CURRENT_PHASE)
        return el.text

    def get_plant_info_card(self) -> WebElement:
        return self.wait_for_element_visible(self.PLANT_INFO_CARD)

    def get_phase_info_card(self) -> WebElement:
        return self.wait_for_element_visible(self.PHASE_INFO_CARD)

    def initiate_phase_transition(self) -> None:
        """Click the transition button to open the dialog."""
        self.wait_and_click(self.TRANSITION_BUTTON)
        self.wait_for_element_visible(self.TRANSITION_DIALOG)

    def select_target_phase(self, phase_key: str) -> None:
        """Select a target phase from the dropdown in the transition dialog."""
        self.open_select_by_testid(self.TARGET_PHASE_SELECT_TESTID)
        option = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"li[data-value='{phase_key}']")
        )
        self.scroll_and_click(option)
        self.close_mui_dropdown()

    def set_transition_reason(self, reason: str) -> None:
        reason_input = self.wait_for_element_clickable(self.TRANSITION_REASON)
        reason_input.clear()
        reason_input.send_keys(reason)

    def confirm_transition(self) -> None:
        self.wait_and_click(self.TRANSITION_CONFIRM)

    def cancel_transition(self) -> None:
        self.wait_and_click(self.TRANSITION_CANCEL)

    def get_phase_history_count(self) -> int:
        """Return the number of rows in the phase history table."""
        rows = self.driver.find_elements(*self.PHASE_HISTORY_ROWS)
        return len(rows)

    def has_phase_history(self) -> bool:
        """Check if the phase history section is present."""
        elements = self.driver.find_elements(*self.PHASE_HISTORY)
        return len(elements) > 0
