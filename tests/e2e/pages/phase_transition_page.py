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

    #: Column id of the identifying column (PlantInstanceListPage `columns`).
    INSTANCE_ID_COLUMN_ID = "instanceId"
    #: Column id carrying the current-phase chip.
    PHASE_COLUMN_ID = "currentPhase"

    def get_first_column_texts(self) -> list[str]:
        """Return each visible row's identifying text.

        Addressed by column id, not by position: the leading ``<td>`` is the
        cover-photo column (empty text) and the mobile card layout has no
        ``<td>`` at all. In the card layout this resolves to the card title,
        i.e. the plant's display name (the instance id is only the subtitle when
        it differs) -- both callers use it as an identifying string, not as an
        exact instance id.
        """
        return self.get_column_texts(self.INSTANCE_ID_COLUMN_ID)

    def get_phase_column_texts(self) -> list[str]:
        """Return each visible row's current-phase label.

        Addressed by column id in both layouts: the previous ``cells[3]`` read
        the *location* column, so TC-REQ-003-005 asserted on the wrong column
        on the desktop table and on nothing at all in the mobile card layout.

        `PlantInstanceListPage` keys its card chips, so the card layout reads
        ``card-chip-currentPhase`` -- the same column id the desktop cell uses.
        The previous "the phase chip is the row's *first* chip" heuristic held
        only as long as the phase chip stayed conditional-but-first; it would
        have reported the planting-run chip for any plant without a phase.
        `MobileCard` omits the chip entirely in that case, which this reports
        as the empty string, exactly as the desktop cell does.
        """
        result: list[str] = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(
                By.CSS_SELECTOR, f"[data-testid='cell-{self.PHASE_COLUMN_ID}']"
            )
            if cells:
                result.append(cells[0].text)
                continue
            chips = row.find_elements(
                By.CSS_SELECTOR, f"[data-testid='card-chip-{self.PHASE_COLUMN_ID}']"
            )
            result.append(chips[0].text if chips else "")
        return result

    #: Column the row is activated through -- see `PlantInstanceListPage`: the
    #: row carries location/planting-run links and an actions button, all of
    #: which `stopPropagation`, so the row's geometric centre is not a safe
    #: target. `instanceId` is inert at every breakpoint.
    ROW_CLICK_COLUMN_ID = INSTANCE_ID_COLUMN_ID

    def click_row(self, index: int) -> None:
        """Open the plant instance at *index* via its inert id cell."""
        self.click_data_table_row(
            index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "plant instance row"
        )

    def search(self, term: str) -> None:
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(term)

    def get_column_headers(self) -> list[str]:
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
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
    PHASE_HISTORY = (
        By.CSS_SELECTOR,
        "[data-testid='phases-tab-content'] [data-testid='data-table']",
    )
    PHASE_HISTORY_ROWS = (
        By.CSS_SELECTOR,
        "[data-testid='phases-tab-content'] [data-testid='data-table-row']",
    )

    # ── Phase Transition Dialog (PhaseTransitionDialog.tsx) ────────────
    TRANSITION_DIALOG = (By.CSS_SELECTOR, "[data-testid='phase-transition-dialog']")
    #: Root of the target-phase ``<TextField select>``. MUI spreads the testid
    #: onto the FormControl **root** (label + input + helper text), so this is a
    #: presence/visibility locator only -- never click it: at 393px the helper
    #: text wraps to two lines, the root grows to 83px and its click centre
    #: (41.5px) lands 1.5px BELOW the 40px input, on the helper ``<p>``. That
    #: ``<p>`` is a descendant of the clicked root, so Chrome raises no
    #: interception and the click is a silent no-op. Open it via
    #: :meth:`open_target_phase_select`, which resolves the combobox.
    TARGET_PHASE_SELECT = (By.CSS_SELECTOR, "[data-testid='target-phase-select']")
    TARGET_PHASE_SELECT_TESTID = "target-phase-select"
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
        from selenium.webdriver.support import expected_conditions as EC

        self.poll(timeout).until(EC.invisibility_of_element_located(self.LOADING_SKELETON))

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

    # Both readers wait for the card to appear before answering. Every caller is
    # a positive assertion reached straight after a client-side navigation, so
    # the bare ``find_elements`` they replace could not tell "React has not
    # committed the detail route yet" from "the card is absent" — TC-REQ-001-J080
    # failed on exactly that on run 31113673507, once #835 removed the implicit
    # wait. `False` still means absent, it just now means absent after waiting.

    def is_phase_info_card_visible(self) -> bool:
        return self.is_visible_within(self.PHASE_INFO_CARD)

    def is_plant_info_card_visible(self) -> bool:
        return self.is_visible_within(self.PLANT_INFO_CARD)

    def has_phase_history(self) -> bool:
        elements = self.driver.find_elements(*self.PHASE_HISTORY)
        return bool(elements)

    def get_phase_history_count(self) -> int:
        rows = self.driver.find_elements(*self.PHASE_HISTORY_ROWS)
        return len(rows)

    # ── Transition button / state ──────────────────────────────────────

    def is_transition_button_enabled(self) -> bool:
        return self.is_header_action_enabled("transition-button")

    def is_remove_button_enabled(self) -> bool:
        # Asked through the header helper, not through the locator: on `xs` the
        # remove action is an overflow entry (#832), where the plain locator
        # matches nothing and `is_enabled()` would not mean what it says.
        return self.is_header_action_enabled("remove-button")

    # ── Phase Transition Dialog ────────────────────────────────────────

    def initiate_phase_transition(self) -> None:
        """Click the 'Phasenübergang' button and wait for the dialog to open."""
        self.click_header_action("transition-button")
        self.wait_for_element_visible(self.TRANSITION_DIALOG)

    def is_transition_dialog_open(self) -> bool:
        # Stale-safe: an element unmounting mid fade-out is by definition gone.
        # The verdict (and the opt-out that keeps it one) lives in
        # `BasePage.is_any_displayed` -- see the "Staleness as a *verdict*" block
        # in `base_page.py` for why it must not be allowed to heal.
        return self.is_any_displayed(self.TRANSITION_DIALOG)

    def open_target_phase_select(self) -> None:
        """Open the target-phase dropdown (combobox-scoped, verified, loud)."""
        self.open_select_by_testid(self.TARGET_PHASE_SELECT_TESTID)

    def get_target_phase_options(self) -> list[str]:
        """Return the text of all available phase options in the select.

        Opens the MUI Select, collects option texts, then closes without selecting.
        """
        self.open_target_phase_select()
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options if o.is_displayed()]
        # Close the dropdown (guarded: waits for auto-close, only ESCapes if
        # still open, then waits for the popover to actually disappear).
        self.close_mui_dropdown()
        return texts

    def select_target_phase(self, phase_key: str) -> None:
        """Select a target phase by its data-value attribute."""
        self.open_target_phase_select()
        option = self.wait_for_element_clickable((By.CSS_SELECTOR, f"li[data-value='{phase_key}']"))
        # click_menu_option, not a coordinate click: a long phase list scrolls
        # inside the popover, and `Menu` scrolls that paper to the selected item
        # on open -- which moves every option after `element_to_be_clickable` is
        # already satisfied, so a click resolved at coordinates picks a
        # neighbour.
        self.click_menu_option(option)
        # MUI auto-closes on option click; ensure the popover is fully gone
        self.close_mui_dropdown()

    def select_target_phase_by_text(self, text: str) -> None:
        """Select a target phase by its visible label text.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        """
        self.open_target_phase_select()
        self.select_option_by_label(text)

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
        self.wait_and_click(self.TRANSITION_CONFIRM)

    def cancel_transition(self) -> None:
        """Click the 'Abbrechen' button and wait for the transition dialog to close."""
        self.wait_and_click(self.TRANSITION_CANCEL)
        self.wait_for_element_hidden(self.TRANSITION_DIALOG)

    def is_confirm_button_enabled(self) -> bool:
        btn = self.wait_for_element(self.TRANSITION_CONFIRM)
        return btn.is_enabled() and not btn.get_attribute("disabled")

    # ── Remove plant flow ──────────────────────────────────────────────

    def initiate_remove(self) -> None:
        """Click the 'Entfernen' button and wait for the confirm dialog."""
        self.click_header_action("remove-button")
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_remove(self) -> None:
        self.wait_and_click(self.CONFIRM_OK)

    def cancel_remove(self) -> None:
        self.wait_and_click(self.CONFIRM_CANCEL_BTN)
        self.wait_for_element_hidden(self.CONFIRM_DIALOG)

    def is_confirm_dialog_visible(self) -> bool:
        # Stale-safe: the termination dialog animates out on cancel, so an element
        # can go stale between find and is_displayed() — treat that as "gone".
        return self.is_any_displayed(self.CONFIRM_DIALOG)

    # ── Core-lifecycle-journey helpers (self-provisioning) ─────────────

    def get_target_phase_option_keys(self) -> list[str]:
        """Open the target-phase select and return the option ``data-value`` keys.

        Keys equal the growth-phase keys and preserve the lifecycle's
        sequence order, so callers can drive a plant forward (later index)
        or backward (earlier index) without hard-coding species-specific
        phase names.
        """
        # open_select_by_testid waits for the dropdown to actually open and
        # raises when it does not -- so no silent ``except: pass`` around the
        # option wait, and no empty option list reported as "no phases".
        self.open_target_phase_select()
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        keys = [o.get_attribute("data-value") or "" for o in options]
        self.close_mui_dropdown()
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
        from selenium.webdriver.support import expected_conditions as EC

        self.poll(timeout).until(EC.invisibility_of_element_located(self.TRANSITION_DIALOG))

    def has_alert(self) -> bool:
        """Return True if any ``[role='alert']`` notification is present."""
        return len(self.driver.find_elements(*self.ALERT)) > 0

    # ── Phase history / tab ────────────────────────────────────────────

    def open_phases_tab(self) -> None:
        """Click the 'Phasen' tab and wait for its content."""
        self.wait_for_element_clickable(self.PHASES_TAB).click()
        self.wait_for_element_visible((By.CSS_SELECTOR, "[data-testid='phases-tab-content']"))

    def open_tasks_tab(self) -> None:
        """Click the 'Aufgaben' (task history) tab."""
        self.wait_for_element_clickable(self.TASKS_TAB).click()
        self.wait_for_loading_complete()

    def get_body_text(self) -> str:
        """Return the full page body text (keyword assertions)."""
        return self.find_present((By.TAG_NAME, "body")).text

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
        """Submit the edit form (Speichern), coordinate-free.

        The plant-instance edit tab is a long *in-page* form, not a dialog, so
        its action row is scroll-clamped against the bottom of the document --
        the documented exception in `BasePage.wait_and_click`, where a
        coordinate dispatch lands next to the button and nothing raises (the
        same mechanism that took out `TaskDetailPage.save_edit` on the mobile
        profile, run 20260725_113337).
        """
        self.wait_and_click_coordinate_free(self.EDIT_SUBMIT)
