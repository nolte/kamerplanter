"""Page object for the Plant Instance detail page."""

from __future__ import annotations

import re

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

    # Overdue/Active/Done summary bar above the two task tables. Each chip
    # renders "<translated label>: <count>", so only the trailing integer is
    # read — the prefix is i18n text and must never be matched on.
    TASK_SUMMARY_BAR = (By.CSS_SELECTOR, "[data-testid='task-summary-bar']")
    TASK_SUMMARY_CHIPS = {
        "overdue": (By.CSS_SELECTOR, "[data-testid='task-summary-overdue']"),
        "active": (By.CSS_SELECTOR, "[data-testid='task-summary-active']"),
        "done": (By.CSS_SELECTOR, "[data-testid='task-summary-done']"),
    }
    # Trailing integer of a summary chip, e.g. "Überfällig: 2" / "Overdue: 2".
    _SUMMARY_COUNT_RE = re.compile(r"(\d+)\s*$")
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    DATA_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # `DataTable.sectionTestId` values for the two task-history sections — the
    # active table lists pending/in-progress tasks, the done table the
    # completed/cancelled ones. `DataTable` emits them as the plain attribute
    # ``data-table-section`` on its Paper root in BOTH layouts, so a section is
    # addressable without the previous detour over the German section heading.
    TASK_ACTIVE_SECTION = "plant-tasks-active"
    TASK_DONE_SECTION = "plant-tasks-done"
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
            lambda d: d.find_elements(*self.PAGE) or d.find_elements(*self.ERROR_DISPLAY)
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

    def get_watering_log_row_cell(self, index: int, col_id: str) -> str:
        """Return the *col_id* cell text of watering-log row *index* (0 = newest).

        Addresses the cell by column id rather than by position, mirroring
        :meth:`WateringLogListPage.get_row_cell` for the instance-scoped
        ``#watering-log`` tab.

        Raises ``IndexError`` when *index* is out of range — a missing row is a
        different failure than an empty cell, and a silent ``""`` would surface
        downstream as a confusing value mismatch.
        """
        rows = self.get_watering_log_rows()
        if not -len(rows) <= index < len(rows):
            raise IndexError(
                f"Watering-log row index {index} out of range (tab has {len(rows)} rows)"
            )
        return self.get_row_cell_text(rows[index], col_id)

    #: A `DataTable` scoped to one task-history section. ``data-table-section``
    #: is a plain attribute on the Paper root (not a data-testid) and is present
    #: in BOTH the table and the card layout, which is exactly what the previous
    #: ``table[aria-label='…']`` scope was not: below `DataTable`'s
    #: ``mobileBreakpoint`` there is no ``<table>`` and hence no ``aria-label``,
    #: so that scope silently yielded ``[]`` for every section and the fallback
    #: had to match the German section heading as a text node.
    SECTION_TABLE_CSS = "[data-testid='data-table'][data-table-section='{section}']"

    def get_task_rows(self, section: str) -> list[WebElement]:
        """Return the DataTable rows for a task-history section, layout-tolerantly.

        *section* is one of :attr:`TASK_ACTIVE_SECTION` /
        :attr:`TASK_DONE_SECTION`. Returns ``[]`` when the section is not
        rendered — which is exact rather than silent: the whole section, its
        heading included, is only mounted while it holds ≥1 task.

        Note that ``data-table-section`` is absent from `DataTable`'s early
        returns (loading skeleton, empty state, no-filter-results), so this is
        a row reader and never a wait anchor for the loading state.
        """
        return self.driver.find_elements(
            By.CSS_SELECTOR,
            f"{self.SECTION_TABLE_CSS.format(section=section)} [data-testid='data-table-row']",
        )

    #: `MobileCard` slot that carries each section's subtitle, per the tasks-tab
    #: ``mobileCardRenderer`` (PlantInstanceDetailPage.tsx): the active cards
    #: subtitle the relative due date, the archived ones the completion date.
    #: Neither is keyed as a ``card-field-*``, because both are the card's
    #: subtitle rather than a field of its grid.
    TASK_CARD_SUBTITLE_COLUMN = {
        TASK_ACTIVE_SECTION: "due_date",
        TASK_DONE_SECTION: "completed_at",
    }

    def get_task_field(self, row: WebElement, section: str, col_id: str) -> str:
        """Return a task row's *col_id* value in both the table and card layout.

        Desktop reads ``[data-testid='cell-<col_id>']``; a cell that exists but
        renders empty is read via ``textContent``, because `DataTable` keeps
        ``hideBelowBreakpoint`` columns (``category``, ``completed_at``,
        ``priority``) mounted with ``display: none`` below ``md``.

        In the card layout the same column ids resolve through `MobileCard`'s
        own hooks — ``card-chip-status``/``card-chip-category`` and (active
        section only) ``card-field-priority`` — plus the two slots the renderer
        fills with the task name and the section's date. A column the card
        renders nothing for raises rather than returning a silent ``''``.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        if cells:
            return (cells[0].text or self._text_content(cells[0])).strip()
        if col_id == "name":
            return self.get_card_title(row)
        if col_id == self.TASK_CARD_SUBTITLE_COLUMN.get(section):
            return self.get_card_subtitle(row)
        field = self.get_card_field(row, col_id)
        if field is not None:
            return field
        chips = row.find_elements(By.CSS_SELECTOR, f"[data-testid='card-chip-{col_id}']")
        if chips:
            return chips[0].text.strip()
        raise AssertionError(
            f"Task column '{col_id}' is not readable in the mobile card layout: "
            f"section '{section}' renders neither a 'card-field-{col_id}' nor a "
            f"'card-chip-{col_id}', and it is not the card's title or subtitle "
            f"('{self.TASK_CARD_SUBTITLE_COLUMN.get(section)}')."
        )

    def _is_watering_task(self, row: WebElement, section: str) -> bool:
        """Return True if *row* is a ``— watering`` care-reminder task."""
        name = self.get_task_field(row, section, "name")
        return name.endswith(self.WATERING_TASK_SUFFIX)

    def count_watering_tasks(self, section: str) -> int:
        """Count rows whose name ends with ``— watering`` in a task-history section."""
        return sum(1 for row in self.get_task_rows(section) if self._is_watering_task(row, section))

    def get_watering_task_cell(self, section: str, col_id: str) -> str:
        """Return *col_id*'s value for the first ``— watering`` row in a section."""
        for row in self.get_task_rows(section):
            if self._is_watering_task(row, section):
                return self.get_task_field(row, section, col_id)
        return ""

    def get_task_summary_counts(self) -> dict[str, int]:
        """Return the Overdue/Active/Done counts of the task-tab summary bar.

        Reads the trailing integer off each ``task-summary-*`` chip, so the
        translated label prefix ("Überfällig"/"Overdue", …) is irrelevant and the
        method works in either UI language.

        The overdue chip is rendered only while at least one task is overdue, so
        a missing chip is reported as ``0`` rather than as an absent key — the
        frontend expresses "nothing overdue" by omitting it.

        Returns:
            ``{"overdue": int, "active": int, "done": int}``.

        Raises:
            AssertionError: If the summary bar is not on screen (the tasks tab
                is not open, or it is showing its empty state), or if a chip's
                text carries no trailing count — both are page-state failures a
                silent ``0`` would disguise as an unmet expectation.
        """
        self.wait_for_element_visible(self.TASK_SUMMARY_BAR)
        counts: dict[str, int] = {}
        for name, locator in self.TASK_SUMMARY_CHIPS.items():
            elements = self.driver.find_elements(*locator)
            if not elements:
                if name == "overdue":
                    counts[name] = 0
                    continue
                raise AssertionError(f"Task summary chip '{name}' is missing from the summary bar")
            text = elements[0].text
            match = self._SUMMARY_COUNT_RE.search(text)
            if match is None:
                raise AssertionError(
                    f"Task summary chip '{name}' carries no trailing count (text={text!r})"
                )
            counts[name] = int(match.group(1))
        return counts

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
        option = self.wait_for_element_clickable((By.CSS_SELECTOR, f"li[data-value='{phase_key}']"))
        # Coordinate-independent (see BasePage.click_menu_option): the open
        # `Menu` scrolls its paper to the selected item, moving every option.
        self.click_menu_option(option)
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
