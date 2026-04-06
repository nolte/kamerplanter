"""Page object for the Pflege Dashboard page (REQ-022).

The /pflege route redirects to /aufgaben/queue (TaskQueuePage) which
integrates both regular tasks and care-reminder cards in a unified view.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import DEFAULT_TIMEOUT, BasePage


class PflegeDashboardPage(BasePage):
    """Interact with the care-reminder section of the Task Queue page (``/aufgaben/queue``)."""

    PATH = "/aufgaben/queue"

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='task-queue-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")

    # ── Urgency sections (TaskQueuePage uses 'task-section-*') ────────
    SECTION_OVERDUE = (By.CSS_SELECTOR, "[data-testid='task-section-overdue']")
    SECTION_DUE_TODAY = (By.CSS_SELECTOR, "[data-testid='task-section-today']")
    SECTION_UPCOMING = (By.CSS_SELECTOR, "[data-testid='task-section-thisWeek']")

    # ── Empty state ────────────────────────────────────────────────────
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # ── Care cards (testid is 'care-card-care-{plant_key}-{type}') ───
    CARE_CARDS = (By.CSS_SELECTOR, "[data-testid^='care-card-care-']")

    # ── CareConfirmDialog ─────────────────────────────────────────────
    CONFIRM_DIALOG_SUBMIT = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-submit']")
    CONFIRM_DIALOG_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")
    CONFIRM_NOTES_FIELD = (By.CSS_SELECTOR, "[data-testid='confirm-notes-field']")
    CONFIRM_VOLUME_FIELD = (By.CSS_SELECTOR, "[data-testid='confirm-volume-field']")
    CONFIRM_EC_FIELD = (By.CSS_SELECTOR, "[data-testid='confirm-ec-field']")
    CONFIRM_PH_FIELD = (By.CSS_SELECTOR, "[data-testid='confirm-ph-field']")

    # ── CareProfileEditDialog ─────────────────────────────────────────
    PROFILE_DIALOG = (By.CSS_SELECTOR, "[data-testid='care-profile-edit-dialog']")
    CARE_STYLE_SELECT = (By.CSS_SELECTOR, "[data-testid='care-style-select']")
    WATERING_INTERVAL_SLIDER = (By.CSS_SELECTOR, "[data-testid='watering-interval-slider']")
    WATERING_METHOD_SELECT = (By.CSS_SELECTOR, "[data-testid='watering-method-select']")
    FERTILIZING_INTERVAL_SLIDER = (By.CSS_SELECTOR, "[data-testid='fertilizing-interval-slider']")
    REPOTTING_INTERVAL_SLIDER = (By.CSS_SELECTOR, "[data-testid='repotting-interval-slider']")
    PEST_CHECK_INTERVAL_SLIDER = (By.CSS_SELECTOR, "[data-testid='pest-check-interval-slider']")
    HUMIDITY_CHECK_SWITCH = (By.CSS_SELECTOR, "[data-testid='humidity-check-switch']")
    HUMIDITY_INTERVAL_SLIDER = (By.CSS_SELECTOR, "[data-testid='humidity-interval-slider']")
    LOCATION_CHECK_SWITCH = (By.CSS_SELECTOR, "[data-testid='location-check-switch']")
    LOCATION_CHECK_MONTHS = (By.CSS_SELECTOR, "[data-testid='location-check-months']")
    ADAPTIVE_LEARNING_SWITCH = (By.CSS_SELECTOR, "[data-testid='adaptive-learning-switch']")
    WINTER_WATERING_FIELD = (By.CSS_SELECTOR, "[data-testid='winter-watering-multiplier-field']")
    WATER_QUALITY_HINT_FIELD = (By.CSS_SELECTOR, "[data-testid='water-quality-hint-field']")
    CARE_NOTES_FIELD = (By.CSS_SELECTOR, "[data-testid='care-notes-field']")
    WATERING_LEARNED_CHIP = (By.CSS_SELECTOR, "[data-testid='watering-learned']")
    FERTILIZING_LEARNED_CHIP = (By.CSS_SELECTOR, "[data-testid='fertilizing-learned']")
    FERTILIZING_ACTIVE_MONTHS = (By.CSS_SELECTOR, "[data-testid='fertilizing-active-months']")

    # Task type toggle switches
    AUTO_CREATE_WATERING_SWITCH = (By.CSS_SELECTOR, "[data-testid='auto-create-watering-task-switch']")
    AUTO_CREATE_FERTILIZING_SWITCH = (By.CSS_SELECTOR, "[data-testid='auto-create-fertilizing-task-switch']")
    AUTO_CREATE_REPOTTING_SWITCH = (By.CSS_SELECTOR, "[data-testid='auto-create-repotting-task-switch']")
    AUTO_CREATE_PEST_CHECK_SWITCH = (By.CSS_SELECTOR, "[data-testid='auto-create-pest-check-task-switch']")

    SAVE_PROFILE_BUTTON = (By.CSS_SELECTOR, "[data-testid='save-profile-button']")
    CANCEL_BUTTON = (By.CSS_SELECTOR, "[data-testid='cancel-button']")
    RESET_PROFILE_BUTTON = (By.CSS_SELECTOR, "[data-testid='reset-profile-button']")

    # ── Snackbar ──────────────────────────────────────────────────────
    SNACKBAR = (By.CSS_SELECTOR, ".MuiSnackbar-root .MuiAlert-message")

    # ── MUI Dialog (generic) ─────────────────────────────────────────
    MUI_DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ─────────────────────────────────────────────────────

    def open(self) -> PflegeDashboardPage:
        """Navigate to the Pflege dashboard and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Page state queries ─────────────────────────────────────────────

    def is_page_displayed(self) -> bool:
        """Return True if the dashboard page container is visible."""
        elements = self.driver.find_elements(*self.PAGE)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_title_text(self) -> str:
        """Return the page title text."""
        return self.wait_for_element(self.PAGE_TITLE).text

    def has_empty_state(self) -> bool:
        """Return True if the 'Alle Pflanzen versorgt' empty state is shown."""
        elements = self.driver.find_elements(*self.EMPTY_STATE)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Urgency sections ──────────────────────────────────────────────

    def has_overdue_section(self) -> bool:
        """Return True if the overdue urgency section is visible."""
        elements = self.driver.find_elements(*self.SECTION_OVERDUE)
        return len(elements) > 0 and elements[0].is_displayed()

    def has_due_today_section(self) -> bool:
        """Return True if the due-today urgency section is visible."""
        elements = self.driver.find_elements(*self.SECTION_DUE_TODAY)
        return len(elements) > 0 and elements[0].is_displayed()

    def has_upcoming_section(self) -> bool:
        """Return True if the upcoming urgency section is visible."""
        elements = self.driver.find_elements(*self.SECTION_UPCOMING)
        return len(elements) > 0 and elements[0].is_displayed()

    def _urgency_section_testid(self, urgency: str) -> str:
        """Map logical urgency names to TaskQueuePage section testids."""
        mapping = {
            "overdue": "task-section-overdue",
            "due_today": "task-section-today",
            "today": "task-section-today",
            "upcoming": "task-section-thisWeek",
            "thisWeek": "task-section-thisWeek",
            "future": "task-section-future",
        }
        return mapping.get(urgency, f"task-section-{urgency}")

    def get_section_card_count(self, urgency: str) -> int:
        """Return the number of care cards in a given urgency section."""
        testid = self._urgency_section_testid(urgency)
        section_locator = (By.CSS_SELECTOR, f"[data-testid='{testid}']")
        sections = self.driver.find_elements(*section_locator)
        if not sections:
            return 0
        cards = sections[0].find_elements(By.CSS_SELECTOR, "[data-testid^='care-card-care-']")
        return len(cards)

    def get_section_count_chip_text(self, urgency: str) -> str:
        """Return the text of the count chip in a given urgency section header."""
        testid = self._urgency_section_testid(urgency)
        section_locator = (By.CSS_SELECTOR, f"[data-testid='{testid}']")
        section = self.wait_for_element(section_locator)
        chip = section.find_element(By.CSS_SELECTOR, ".MuiChip-label")
        return chip.text

    # ── Care cards ────────────────────────────────────────────────────

    def get_all_care_cards(self) -> list[WebElement]:
        """Return all visible care card elements."""
        return self.driver.find_elements(*self.CARE_CARDS)

    def get_care_card_count(self) -> int:
        """Return the total number of care cards on the page."""
        return len(self.get_all_care_cards())

    def get_care_card(self, plant_key: str, reminder_type: str) -> WebElement:
        """Return the specific care card for a plant/reminder combination."""
        testid = f"care-card-care-{plant_key}-{reminder_type}"
        locator = (By.CSS_SELECTOR, f"[data-testid='{testid}']")
        return self.wait_for_element(locator)

    def has_care_card(self, plant_key: str, reminder_type: str) -> bool:
        """Return True if a care card for the given plant/type exists."""
        testid = f"care-card-care-{plant_key}-{reminder_type}"
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, f"[data-testid='{testid}']"
        )
        return len(elements) > 0

    def get_card_urgency_indicator(self, card: WebElement) -> str:
        """Determine urgency from the card's parent section testid.

        TaskQueuePage care cards don't have individual urgency chips.
        Instead, urgency is conveyed by which section the card belongs to.
        Returns 'error' for overdue, 'warning' for today, 'info' for thisWeek,
        or 'default' if the section cannot be determined.
        """
        # Walk up to find the parent section
        parent_section = card.find_element(
            By.XPATH, "ancestor::div[@data-testid][starts-with(@data-testid, 'task-section-')]"
        )
        testid = parent_section.get_attribute("data-testid") or ""
        if "overdue" in testid:
            return "error"
        if "today" in testid:
            return "warning"
        if "thisWeek" in testid:
            return "info"
        return "default"

    # Keep legacy names as aliases for test compatibility
    def get_card_urgency_chip_color(self, card: WebElement) -> str:
        """Return the urgency color for a card based on its section.

        TaskQueuePage care cards use section-based urgency (no per-card chip).
        """
        return self.get_card_urgency_indicator(card)

    def get_card_urgency_chip_text(self, card: WebElement) -> str:
        """Return urgency text derived from the card's section.

        TaskQueuePage care cards have no per-card urgency chip. This method
        returns the section header text instead, or the due-date caption.
        """
        # Try to get the due-date text from the card (caption or body2 element)
        captions = card.find_elements(
            By.CSS_SELECTOR, ".MuiTypography-caption, .MuiTypography-body2"
        )
        for cap in captions:
            text = cap.text.strip()
            if text and any(c.isdigit() for c in text):
                return text
        return ""

    def get_card_plant_name(self, card: WebElement) -> str:
        """Return the plant name shown on a card.

        In TaskQueuePage the plant name is inside a MuiLink (caption variant).
        """
        # Try the link first (TaskQueuePage care card layout)
        links = card.find_elements(By.CSS_SELECTOR, "a.MuiLink-root")
        if links:
            return links[0].text.strip()
        # Fallback to subtitle typography
        subs = card.find_elements(By.CSS_SELECTOR, ".MuiTypography-subtitle1, .MuiTypography-subtitle2")
        if subs:
            return subs[0].text.strip()
        return ""

    # ── Card actions ──────────────────────────────────────────────────

    def _get_care_card_action_buttons(self, plant_key: str, reminder_type: str) -> list[WebElement]:
        """Return the action IconButtons inside a care card (edit, confirm, snooze order)."""
        card = self.get_care_card(plant_key, reminder_type)
        return card.find_elements(By.CSS_SELECTOR, "button.MuiIconButton-root")

    def click_confirm_on_card(self, plant_key: str, reminder_type: str) -> None:
        """Click the confirm (check-circle) button on a specific care card.

        In TaskQueuePage the action buttons are ordered: edit, confirm, snooze.
        The confirm button is identified by its CheckCircleIcon (2nd button).
        """
        card = self.get_care_card(plant_key, reminder_type)
        # Find the confirm button via its CheckCircleIcon SVG data-testid
        btns = card.find_elements(
            By.CSS_SELECTOR, "button.MuiIconButton-root[color='success'], button.MuiIconButton-colorSuccess"
        )
        if not btns:
            # Fallback: action buttons are ordered edit(0), confirm(1), snooze(2)
            all_btns = card.find_elements(By.CSS_SELECTOR, "button.MuiIconButton-root")
            if len(all_btns) >= 2:
                btns = [all_btns[1]]
        if btns:
            self.scroll_and_click(btns[0])
        else:
            raise AssertionError(
                f"Could not find confirm button on care card care-{plant_key}-{reminder_type}"
            )

    def click_snooze_on_card(self, plant_key: str, reminder_type: str) -> None:
        """Click the snooze button on a specific care card.

        In TaskQueuePage the action buttons are ordered: edit, confirm, snooze.
        The snooze button is the 3rd (last) IconButton in the card.
        """
        card = self.get_care_card(plant_key, reminder_type)
        all_btns = card.find_elements(By.CSS_SELECTOR, "button.MuiIconButton-root")
        if len(all_btns) >= 3:
            self.scroll_and_click(all_btns[2])
        elif all_btns:
            # Fallback to last button
            self.scroll_and_click(all_btns[-1])
        else:
            raise AssertionError(
                f"Could not find snooze button on care card care-{plant_key}-{reminder_type}"
            )

    def click_edit_profile_on_card(self, plant_key: str) -> None:
        """Click the edit-profile (pencil) button on a care card.

        In TaskQueuePage the edit button is the 1st IconButton in the card.
        We find any care card for this plant_key and click the first button.
        """
        # Find a care card for this plant_key (any reminder type)
        cards = self.driver.find_elements(
            By.CSS_SELECTOR, f"[data-testid^='care-card-care-{plant_key}-']"
        )
        if not cards:
            raise AssertionError(f"No care card found for plant_key={plant_key}")
        card = cards[0]
        all_btns = card.find_elements(By.CSS_SELECTOR, "button.MuiIconButton-root")
        if all_btns:
            self.scroll_and_click(all_btns[0])
        else:
            raise AssertionError(
                f"Could not find edit-profile button on care card for {plant_key}"
            )

    # ── CareConfirmDialog interactions ────────────────────────────────

    def wait_for_confirm_dialog(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the MUI dialog with confirm fields is visible."""
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.MUI_DIALOG)
        )

    def is_confirm_dialog_open(self) -> bool:
        """Return True if a MUI dialog is currently open."""
        elements = self.driver.find_elements(*self.MUI_DIALOG)
        return len(elements) > 0

    def fill_confirm_notes(self, text: str) -> None:
        """Fill the notes field in the confirm dialog."""
        field = self.wait_for_element_clickable(self.CONFIRM_NOTES_FIELD)
        textarea = field.find_element(By.TAG_NAME, "textarea")
        textarea.clear()
        textarea.send_keys(text)

    def submit_confirm_dialog(self) -> None:
        """Click the submit button in the confirm dialog."""
        self.wait_for_element_clickable(self.CONFIRM_DIALOG_SUBMIT).click()

    def cancel_confirm_dialog(self) -> None:
        """Click the cancel button in the confirm dialog."""
        self.wait_for_element_clickable(self.CONFIRM_DIALOG_CANCEL).click()

    # ── CareProfileEditDialog interactions ────────────────────────────

    def wait_for_profile_dialog(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the CareProfileEditDialog is visible."""
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.PROFILE_DIALOG)
        )

    def is_profile_dialog_open(self) -> bool:
        """Return True if the care profile edit dialog is visible."""
        elements = self.driver.find_elements(*self.PROFILE_DIALOG)
        return len(elements) > 0

    def get_care_style_value(self) -> str:
        """Return the currently selected care style value."""
        el = self.wait_for_element(self.CARE_STYLE_SELECT)
        # MUI Select renders its value inside a child div
        return el.text

    def select_care_style(self, style_label: str) -> None:
        """Open the care style dropdown and select by visible label."""
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(self.CARE_STYLE_SELECT)
        self.scroll_and_click(select_el)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{style_label}')]")
        )
        option.click()
        # Dismiss MUI Select backdrop/popover
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

    def click_save_profile(self) -> None:
        """Click the save button in the profile dialog."""
        self.wait_for_element_clickable(self.SAVE_PROFILE_BUTTON).click()

    def click_cancel_profile(self) -> None:
        """Click the cancel button in the profile dialog."""
        self.wait_for_element_clickable(self.CANCEL_BUTTON).click()

    def click_reset_profile(self) -> None:
        """Click the reset-to-defaults button in the profile dialog."""
        self.wait_for_element_clickable(self.RESET_PROFILE_BUTTON).click()

    def is_humidity_check_enabled(self) -> bool:
        """Return True if the humidity check switch is on."""
        el = self.driver.find_element(*self.HUMIDITY_CHECK_SWITCH)
        checkbox = el.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        return checkbox.is_selected()

    def toggle_humidity_check(self) -> None:
        """Toggle the humidity check switch."""
        el = self.wait_for_element_clickable(self.HUMIDITY_CHECK_SWITCH)
        self.scroll_and_click(el)

    def is_location_check_enabled(self) -> bool:
        """Return True if the location check switch is on."""
        el = self.driver.find_element(*self.LOCATION_CHECK_SWITCH)
        checkbox = el.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        return checkbox.is_selected()

    def toggle_location_check(self) -> None:
        """Toggle the location check switch."""
        el = self.wait_for_element_clickable(self.LOCATION_CHECK_SWITCH)
        self.scroll_and_click(el)

    def is_adaptive_learning_enabled(self) -> bool:
        """Return True if the adaptive learning switch is on."""
        el = self.driver.find_element(*self.ADAPTIVE_LEARNING_SWITCH)
        checkbox = el.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        return checkbox.is_selected()

    def toggle_adaptive_learning(self) -> None:
        """Toggle the adaptive learning switch."""
        el = self.wait_for_element_clickable(self.ADAPTIVE_LEARNING_SWITCH)
        self.scroll_and_click(el)

    def is_humidity_interval_visible(self) -> bool:
        """Return True if the humidity interval slider is in the DOM and visible."""
        elements = self.driver.find_elements(*self.HUMIDITY_INTERVAL_SLIDER)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_location_check_months_visible(self) -> bool:
        """Return True if the location check months toggle buttons are visible."""
        elements = self.driver.find_elements(*self.LOCATION_CHECK_MONTHS)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_fertilizing_active_month_values(self) -> list[int]:
        """Return the list of currently selected fertilizing active months."""
        container = self.driver.find_element(*self.FERTILIZING_ACTIVE_MONTHS)
        buttons = container.find_elements(By.CSS_SELECTOR, "button.Mui-selected")
        return [int(btn.text) for btn in buttons]

    def click_fertilizing_month(self, month: int) -> None:
        """Click a specific month toggle button in the fertilizing active months."""
        btn = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='fertilizing-month-{month}']")
        )
        self.scroll_and_click(btn)

    def has_watering_learned_chip(self) -> bool:
        """Return True if the watering learned interval chip is visible."""
        elements = self.driver.find_elements(*self.WATERING_LEARNED_CHIP)
        return len(elements) > 0

    def has_fertilizing_learned_chip(self) -> bool:
        """Return True if the fertilizing learned interval chip is visible."""
        elements = self.driver.find_elements(*self.FERTILIZING_LEARNED_CHIP)
        return len(elements) > 0

    # ── Snackbar ──────────────────────────────────────────────────────

    def wait_for_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for a snackbar to appear and return its text."""
        el = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.SNACKBAR)
        )
        return el.text

    def has_snackbar(self) -> bool:
        """Return True if any snackbar is currently visible."""
        elements = self.driver.find_elements(*self.SNACKBAR)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Dialog closed waiter ──────────────────────────────────────────

    def wait_for_dialog_closed(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until all MUI dialogs are closed."""
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.MUI_DIALOG)
        )
