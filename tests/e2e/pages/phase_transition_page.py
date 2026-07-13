"""Page object for Phase-Transition related interactions (REQ-003).

Combines navigation helpers for the PlantInstance list and detail page,
plus the PhaseTransitionDialog interaction, into one cohesive page object.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class PlantInstanceListExt(BasePage):
    """Extended plant instance list page object for REQ-003 tests."""

    PATH = "/pflanzen/plant-instances"

    PAGE = (By.CSS_SELECTOR, "[data-testid='plant-instance-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> PlantInstanceListExt:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    def get_row_count(self) -> int:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def has_table(self) -> bool:
        return len(self.driver.find_elements(*self.TABLE)) > 0

    def is_table_visible(self) -> bool:
        elements = self.driver.find_elements(*self.TABLE)
        return len(elements) > 0 and elements[0].is_displayed()

    def has_empty_state(self) -> bool:
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    def get_first_column_texts(self) -> list[str]:
        """Return the Instance-ID column for all visible rows.

        A leading cover-photo column (empty text) was inserted at index 0, so the
        Instance-ID is now the second column (index 1).
        """
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        result: list[str] = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                result.append(cells[1].text)
        return result

    def get_phase_column_texts(self) -> list[str]:
        """Return the current-phase chip text for all visible rows (column index 3)."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        result: list[str] = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:
                result.append(cells[3].text)
        return result

    def click_row(self, index: int) -> None:
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])

    def search(self, term: str) -> None:
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(term)

    def has_search_chip(self) -> bool:
        return len(self.driver.find_elements(*self.SEARCH_CHIP)) > 0

    def has_sort_chip(self) -> bool:
        return len(self.driver.find_elements(*self.SORT_CHIP)) > 0

    def click_column_header(self, header_text: str) -> None:
        headers = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table'] th"
        )
        for h in headers:
            if h.text == header_text:
                self.scroll_and_click(h)
                return
        raise ValueError(f"Column header '{header_text}' not found")

    def get_column_headers(self) -> list[str]:
        headers = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table'] th"
        )
        return [h.text for h in headers if h.text]

    def click_reset_filters(self) -> None:
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def get_showing_count_text(self) -> str:
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text


class PlantInstanceDetailExt(BasePage):
    """Extended plant instance detail page object for REQ-003 tests.

    Covers:
    - Phase info card and current-phase Chip
    - Transition button → PhaseTransitionDialog
    - Phase history table
    - Remove-plant flow
    - Tab navigation (Info / Nährstoffplan / Feeding / Edit)
    """

    PATH_PREFIX = "/pflanzen/plant-instances"

    # ── Page root ──────────────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='plant-instance-detail-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")

    # ── Action buttons ─────────────────────────────────────────────────
    TRANSITION_BUTTON = (By.CSS_SELECTOR, "[data-testid='transition-button']")
    REMOVE_BUTTON = (By.CSS_SELECTOR, "[data-testid='remove-button']")

    # ── Phase info ─────────────────────────────────────────────────────
    PLANT_INFO_CARD = (By.CSS_SELECTOR, "[data-testid='plant-info-card']")
    PHASE_INFO_CARD = (By.CSS_SELECTOR, "[data-testid='phase-info-card']")
    CURRENT_PHASE_CHIP = (By.CSS_SELECTOR, "[data-testid='current-phase']")
    # The "Phasenverlauf" table no longer has a dedicated data-testid='phase-history'
    # container — PhaseHistoryTable now delegates to the shared DataTable, which
    # renders [data-testid='data-table'] with [data-testid='data-table-row'] rows.
    # Scope to the phases-tab-content panel so these don't match other tables.
    PHASE_HISTORY = (By.CSS_SELECTOR, "[data-testid='phases-tab-content'] [data-testid='data-table']")
    PHASE_HISTORY_ROWS = (By.CSS_SELECTOR, "[data-testid='phases-tab-content'] [data-testid='data-table-row']")

    # ── Phase Transition Dialog (PhaseTransitionDialog.tsx) ────────────
    TRANSITION_DIALOG = (By.CSS_SELECTOR, "[data-testid='phase-transition-dialog']")
    TARGET_PHASE_SELECT = (By.CSS_SELECTOR, "[data-testid='target-phase-select']")
    TRANSITION_REASON = (By.CSS_SELECTOR, "[data-testid='transition-reason'] input")
    TRANSITION_CANCEL = (By.CSS_SELECTOR, "[data-testid='transition-cancel']")
    TRANSITION_CONFIRM = (By.CSS_SELECTOR, "[data-testid='transition-confirm']")

    # ── Remove confirm dialog ──────────────────────────────────────────
    # The "Pflanze entfernen" button now opens the richer TerminationDialog
    # (not the generic ConfirmDialog), so target its termination-* testids.
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='termination-dialog']")
    CONFIRM_OK = (By.CSS_SELECTOR, "[data-testid='termination-confirm']")
    CONFIRM_CANCEL_BTN = (By.CSS_SELECTOR, "[data-testid='termination-cancel']")

    # ── Correction ("force") mode ──────────────────────────────────────
    FORCE_SWITCH = (By.CSS_SELECTOR, "[data-testid='force-transition-switch']")
    FORCE_SWITCH_INPUT = (
        By.CSS_SELECTOR,
        "[data-testid='force-transition-switch'] input[type='checkbox']",
    )

    # ── Tabs ───────────────────────────────────────────────────────────
    PHASES_TAB = (By.CSS_SELECTOR, "[data-testid='phases-tab']")
    TASKS_TAB = (By.CSS_SELECTOR, "[data-testid='tasks-tab']")
    WATERING_CARD = (By.CSS_SELECTOR, "[data-testid='watering-card']")
    EDIT_TAB = (By.CSS_SELECTOR, "[data-testid='edit-tab']")
    EDIT_PLANT_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-plant_name'] input")
    EDIT_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")

    # ── Snackbar / notifications ───────────────────────────────────────
    SNACKBAR = (By.CSS_SELECTOR, "#notistack-snackbar")
    ALERT = (By.CSS_SELECTOR, "[role='alert']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> PlantInstanceDetailExt:
        self.navigate(f"{self.PATH_PREFIX}/{key}")
        self.wait_for_element(self.PAGE)
        self._wait_for_skeleton_gone()
        return self

    def _wait_for_skeleton_gone(self, timeout: int = 15) -> None:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.LOADING_SKELETON)
        )

    # ── Page state ─────────────────────────────────────────────────────

    def get_title(self) -> str:
        return self.wait_for_element_visible(self.PAGE_TITLE).text

    def is_error_shown(self) -> bool:
        elements = self.driver.find_elements(*self.ERROR_DISPLAY)
        return bool(elements) and elements[0].is_displayed()

    # ── Phase info ─────────────────────────────────────────────────────

    def get_current_phase(self) -> str:
        """Return the text label of the current-phase Chip."""
        el = self.wait_for_element_visible(self.CURRENT_PHASE_CHIP)
        return el.text

    def get_plant_info_card(self) -> WebElement:
        return self.wait_for_element_visible(self.PLANT_INFO_CARD)

    def get_phase_info_card(self) -> WebElement:
        return self.wait_for_element_visible(self.PHASE_INFO_CARD)

    def is_phase_info_card_visible(self) -> bool:
        elements = self.driver.find_elements(*self.PHASE_INFO_CARD)
        return bool(elements) and elements[0].is_displayed()

    def is_plant_info_card_visible(self) -> bool:
        elements = self.driver.find_elements(*self.PLANT_INFO_CARD)
        return bool(elements) and elements[0].is_displayed()

    def has_phase_history(self) -> bool:
        elements = self.driver.find_elements(*self.PHASE_HISTORY)
        return bool(elements)

    def get_phase_history_count(self) -> int:
        rows = self.driver.find_elements(*self.PHASE_HISTORY_ROWS)
        return len(rows)

    # ── Transition button / state ──────────────────────────────────────

    def is_transition_button_enabled(self) -> bool:
        btn = self.wait_for_element(self.TRANSITION_BUTTON)
        return btn.is_enabled() and not btn.get_attribute("disabled")

    def is_remove_button_enabled(self) -> bool:
        btn = self.wait_for_element(self.REMOVE_BUTTON)
        return btn.is_enabled() and not btn.get_attribute("disabled")

    # ── Phase Transition Dialog ────────────────────────────────────────

    def initiate_phase_transition(self) -> None:
        """Click the 'Phasenübergang' button and wait for the dialog to open."""
        self.wait_for_element_clickable(self.TRANSITION_BUTTON).click()
        self.wait_for_element_visible(self.TRANSITION_DIALOG)

    def is_transition_dialog_open(self) -> bool:
        elements = self.driver.find_elements(*self.TRANSITION_DIALOG)
        return bool(elements) and elements[0].is_displayed()

    def get_target_phase_options(self) -> list[str]:
        """Return the text of all available phase options in the select.

        Opens the MUI Select, collects option texts, then closes without selecting.
        """
        select_el = self.wait_for_element_clickable(self.TARGET_PHASE_SELECT)
        self.scroll_and_click(select_el)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options if o.is_displayed()]
        # Close the dropdown by pressing Escape
        from selenium.webdriver.common.keys import Keys
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        return texts

    def select_target_phase(self, phase_key: str) -> None:
        """Select a target phase by its data-value attribute."""
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(self.TARGET_PHASE_SELECT)
        self.scroll_and_click(select_el)
        option = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"li[data-value='{phase_key}']")
        )
        option.click()
        # Dismiss MUI Select backdrop/popover
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

    def select_target_phase_by_text(self, text: str) -> None:
        """Select a target phase by its visible label text."""
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(self.TARGET_PHASE_SELECT)
        self.scroll_and_click(select_el)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{text}')]")
        )
        option.click()
        # Dismiss MUI Select backdrop/popover
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

    def set_transition_reason(self, reason: str) -> None:
        # The reason field is pre-populated with 'manual' by default; el.clear()
        # does not reliably clear a React controlled input, so use clear_and_fill
        # (JS clear + native events, Ctrl+A fallback) to replace rather than append.
        el = self.wait_for_element_clickable(self.TRANSITION_REASON)
        self.clear_and_fill(el, reason)

    def get_transition_reason_value(self) -> str:
        el = self.wait_for_element(self.TRANSITION_REASON)
        return el.get_attribute("value") or ""

    def confirm_transition(self) -> None:
        """Click the 'Bestätigen' button to execute the phase transition."""
        self.wait_for_element_clickable(self.TRANSITION_CONFIRM).click()

    def cancel_transition(self) -> None:
        """Click the 'Abbrechen' button in the transition dialog."""
        self.wait_for_element_clickable(self.TRANSITION_CANCEL).click()

    def is_confirm_button_enabled(self) -> bool:
        btn = self.wait_for_element(self.TRANSITION_CONFIRM)
        return btn.is_enabled() and not btn.get_attribute("disabled")

    # ── Remove plant flow ──────────────────────────────────────────────

    def initiate_remove(self) -> None:
        """Click the 'Entfernen' button and wait for the confirm dialog."""
        self.wait_for_element_clickable(self.REMOVE_BUTTON).click()
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_remove(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_OK).click()

    def cancel_remove(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_CANCEL_BTN).click()

    def is_confirm_dialog_visible(self) -> bool:
        elements = self.driver.find_elements(*self.CONFIRM_DIALOG)
        return bool(elements) and elements[0].is_displayed()

    # ── Core-lifecycle-journey helpers (self-provisioning) ─────────────

    def get_target_phase_option_keys(self) -> list[str]:
        """Open the target-phase select and return the option ``data-value`` keys.

        Keys equal the growth-phase keys and preserve the lifecycle's
        sequence order, so callers can drive a plant forward (later index)
        or backward (earlier index) without hard-coding species-specific
        phase names.
        """
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(self.TARGET_PHASE_SELECT)
        self.scroll_and_click(select_el)
        time.sleep(0.2)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        keys = [o.get_attribute("data-value") or "" for o in options]
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.2)
        return [k for k in keys if k]

    def transition_to_phase_key(self, phase_key: str, reason: str = "manual") -> None:
        """Open the dialog (assumed already open), select *phase_key*, set the
        reason and confirm the transition."""
        self.select_target_phase(phase_key)
        if reason:
            self.set_transition_reason(reason)
        self.confirm_transition()

    def toggle_force_mode(self) -> None:
        """Toggle the 'Phase korrigieren (Fehlanlage)' correction switch."""
        el = self.wait_for_element_clickable(self.FORCE_SWITCH)
        self.scroll_and_click(el)

    def is_force_mode_enabled(self) -> bool:
        """Return True if the correction (force) switch is currently on."""
        elements = self.driver.find_elements(*self.FORCE_SWITCH_INPUT)
        return bool(elements) and elements[0].is_selected()

    def wait_for_transition_dialog_closed(self, timeout: int = 15) -> None:
        """Wait until the phase transition dialog is no longer visible."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.TRANSITION_DIALOG)
        )

    def has_alert(self) -> bool:
        """Return True if any ``[role='alert']`` notification is present."""
        return len(self.driver.find_elements(*self.ALERT)) > 0

    # ── Phase history / tab ────────────────────────────────────────────

    def open_phases_tab(self) -> None:
        """Click the 'Phasen' tab and wait for its content."""
        self.wait_for_element_clickable(self.PHASES_TAB).click()
        self.wait_for_element_visible(
            (By.CSS_SELECTOR, "[data-testid='phases-tab-content']")
        )

    def open_tasks_tab(self) -> None:
        """Click the 'Aufgaben' (task history) tab."""
        self.wait_for_element_clickable(self.TASKS_TAB).click()
        self.wait_for_loading_complete()

    def get_body_text(self) -> str:
        """Return the full page body text (keyword assertions)."""
        return self.driver.find_element(By.TAG_NAME, "body").text

    # ── Edit tab (TC-001-081) ──────────────────────────────────────────

    def open_edit_tab(self) -> None:
        """Click the 'Bearbeiten' tab and wait for the plant_name field."""
        self.wait_for_element_clickable(self.EDIT_TAB).click()
        self.wait_for_element_visible(self.EDIT_PLANT_NAME)

    def set_edit_plant_name(self, name: str) -> None:
        """Set the plant display name on the edit tab."""
        el = self.wait_for_element_clickable(self.EDIT_PLANT_NAME)
        self.clear_and_fill(el, name)

    def submit_edit(self) -> None:
        """Submit the edit form (Speichern)."""
        self.scroll_and_click(self.wait_for_element_clickable(self.EDIT_SUBMIT))
