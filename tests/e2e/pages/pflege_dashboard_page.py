"""Page object for the Pflege Dashboard page (REQ-022).

The /pflege route redirects to /aufgaben/queue (TaskQueuePage) which
integrates both regular tasks and care-reminder cards in a unified view.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

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

    # ── Generic ConfirmDialog (e.g. preset-reset confirmation) ─────────
    GENERIC_CONFIRM_CONFIRM = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    GENERIC_CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

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
    AUTO_CREATE_WATERING_SWITCH = (
        By.CSS_SELECTOR,
        "[data-testid='auto-create-watering-task-switch']",
    )
    AUTO_CREATE_FERTILIZING_SWITCH = (
        By.CSS_SELECTOR,
        "[data-testid='auto-create-fertilizing-task-switch']",
    )
    AUTO_CREATE_REPOTTING_SWITCH = (
        By.CSS_SELECTOR,
        "[data-testid='auto-create-repotting-task-switch']",
    )
    AUTO_CREATE_PEST_CHECK_SWITCH = (
        By.CSS_SELECTOR,
        "[data-testid='auto-create-pest-check-task-switch']",
    )

    SAVE_PROFILE_BUTTON = (By.CSS_SELECTOR, "[data-testid='save-profile-button']")
    CANCEL_BUTTON = (By.CSS_SELECTOR, "[data-testid='cancel-button']")
    RESET_PROFILE_BUTTON = (By.CSS_SELECTOR, "[data-testid='reset-profile-button']")

    # ── Snackbar ──────────────────────────────────────────────────────
    # Notifications go through notistack (`useNotification`), whose default
    # renderer emits `#notistack-snackbar` inside `.notistack-MuiContent-<variant>`
    # -- NOT a MUI `Alert`. The MuiAlert-only selector this used to carry never
    # matched, which is why the only caller had to wrap it in a try/except.
    SNACKBAR = (
        By.CSS_SELECTOR,
        "#notistack-snackbar, [class*='notistack-MuiContent'], .MuiSnackbar-root .MuiAlert-message",
    )
    SNACKBAR_ERROR = (
        By.CSS_SELECTOR,
        "[class*='notistack-MuiContent-error'], .MuiSnackbar-root .MuiAlert-colorError",
    )

    # ── MUI Dialog (generic) ─────────────────────────────────────────
    MUI_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root [role='dialog']")

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

    def has_task_cards(self) -> bool:
        """Return True if any task card is rendered.

        The Pflege route is currently merged into the TaskQueue page; task
        cards (``[data-testid='task-card']``) sharing the page indicate the
        page is populated by REQ-006 seed data even when no care reminders
        exist for the tenant.
        """
        elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='task-card']")
        return any(el.is_displayed() for el in elements)

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

    def get_cards_in_section(self, urgency: str) -> list[WebElement]:
        """Return the care-card elements nested inside a given urgency section."""
        testid = self._urgency_section_testid(urgency)
        section_locator = (By.CSS_SELECTOR, f"[data-testid='{testid}']")
        sections = self.driver.find_elements(*section_locator)
        if not sections:
            return []
        return sections[0].find_elements(By.CSS_SELECTOR, "[data-testid^='care-card-']")

    def get_section_total_card_count(self, urgency: str) -> int:
        """Return the total number of MUI Card elements (task + care) in a section."""
        testid = self._urgency_section_testid(urgency)
        section_locator = (By.CSS_SELECTOR, f"[data-testid='{testid}']")
        sections = self.driver.find_elements(*section_locator)
        if not sections:
            return 0
        return len(sections[0].find_elements(By.CSS_SELECTOR, ".MuiCard-root"))

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
        elements = self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{testid}']")
        return len(elements) > 0

    def count_care_cards_for_plant(self, plant_key: str, reminder_type: str | None = None) -> int:
        """Return how many care cards a plant currently renders on the dashboard.

        When *reminder_type* is given, counts only cards with the exact
        ``care-card-care-{plant_key}-{reminder_type}`` testid (a value > 1 would
        indicate a duplicate reminder for the same period); otherwise counts all
        care cards for the plant regardless of type.
        """
        if reminder_type is not None:
            selector = f"[data-testid='care-card-care-{plant_key}-{reminder_type}']"
        else:
            selector = f"[data-testid^='care-card-care-{plant_key}-']"
        return len(self.driver.find_elements(By.CSS_SELECTOR, selector))

    def get_card_urgency_indicator(self, card: WebElement) -> str:
        """Determine urgency from the card's parent section testid.

        TaskQueuePage care cards don't have individual urgency chips.
        Instead, urgency is conveyed by which section the card belongs to.
        Returns 'error' for overdue, 'warning' for today, 'info' for thisWeek,
        or 'default' if the section cannot be determined.
        """
        # Walk up to find the parent section. The section wrapper is a
        # <Box component="section"> (not a <div>), so match any element type.
        parent_section = card.find_element(
            By.XPATH, "ancestor::*[@data-testid][starts-with(@data-testid, 'task-section-')]"
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

    def get_card_action_button_count(self, card: WebElement) -> int:
        """Return the number of MUI IconButton action controls inside a care card."""
        return len(card.find_elements(By.CSS_SELECTOR, "button.MuiIconButton-root"))

    def get_card_plant_name(self, card: WebElement) -> str:
        """Return the plant name shown on a card.

        In TaskQueuePage the plant name is inside a MuiLink (caption variant).
        """
        # Try the link first (TaskQueuePage care card layout)
        links = card.find_elements(By.CSS_SELECTOR, "a.MuiLink-root")
        if links:
            return links[0].text.strip()
        # Fallback to subtitle typography
        subs = card.find_elements(
            By.CSS_SELECTOR, ".MuiTypography-subtitle1, .MuiTypography-subtitle2"
        )
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

        Targets the product's ``care-confirm-<id>`` testid; falls back to the
        success-coloured IconButton and then to positional order (edit,
        confirm, snooze) only if that testid is missing.
        """
        card = self.get_care_card(plant_key, reminder_type)
        btns = card.find_elements(
            By.CSS_SELECTOR, f"[data-testid='care-confirm-care-{plant_key}-{reminder_type}']"
        )
        if btns:
            self.scroll_and_click(btns[0])
            return
        # Fallback: find the confirm button via its success colour
        btns = card.find_elements(
            By.CSS_SELECTOR,
            "button.MuiIconButton-root[color='success'], button.MuiIconButton-colorSuccess",
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

        Targets the product's ``care-snooze-<id>`` testid; falls back to the
        card's 3rd/last IconButton (edit, confirm, snooze) only if that testid
        is missing.
        """
        card = self.get_care_card(plant_key, reminder_type)
        btns = card.find_elements(
            By.CSS_SELECTOR, f"[data-testid='care-snooze-care-{plant_key}-{reminder_type}']"
        )
        if btns:
            self.scroll_and_click(btns[0])
            return
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

    #: Urgency groups a card sits in while it still needs attention today.
    DUE_URGENCY_SECTIONS = ("overdue", "today")

    def get_care_card_urgency_group(self, plant_key: str, reminder_type: str) -> str | None:
        """Return the urgency group a care card currently sits in.

        One of ``overdue`` / ``today`` / ``thisWeek`` / ``future`` (the
        ``task-section-<group>`` testid `TaskQueuePage` emits), or ``None``
        when the card is no longer on the dashboard at all.
        """
        cards = self.driver.find_elements(
            By.CSS_SELECTOR, f"[data-testid='care-card-care-{plant_key}-{reminder_type}']"
        )
        if not cards:
            return None
        sections = cards[0].find_elements(
            By.XPATH,
            "ancestor::*[@data-testid][starts-with(@data-testid, 'task-section-')]",
        )
        if not sections:
            return None
        return (sections[0].get_attribute("data-testid") or "").removeprefix("task-section-")

    def wait_until_care_card_not_due(
        self, plant_key: str, reminder_type: str, timeout: int = DEFAULT_TIMEOUT
    ) -> str | None:
        """Wait until a care card has left the overdue/due-today sections.

        A successful snooze sets the reminder's due date to *tomorrow*
        (``care_reminder_engine``: ``confirmed_at + snooze_days``, default 1),
        so the dashboard refetch that follows the request must re-group the
        card into ``thisWeek`` -- or drop it from the dashboard entirely. This
        is the observable post-condition of the snooze; it cannot be satisfied
        by a request that never left the browser.

        Returns the card's resulting urgency group (``None`` if it is gone).
        """
        self.poll(timeout).until(
            lambda _d: (
                self.get_care_card_urgency_group(plant_key, reminder_type)
                not in self.DUE_URGENCY_SECTIONS
            )
        )
        return self.get_care_card_urgency_group(plant_key, reminder_type)

    def click_edit_profile_on_card(self, plant_key: str) -> None:
        """Click the edit-profile (pencil) button on a care card.

        Targets the product's ``care-edit-profile-<id>`` testid on any care card
        for this plant; falls back to the card's first IconButton (edit,
        confirm, snooze order) only if that testid is missing.
        """
        # Find a care card for this plant_key (any reminder type)
        cards = self.driver.find_elements(
            By.CSS_SELECTOR, f"[data-testid^='care-card-care-{plant_key}-']"
        )
        if not cards:
            raise AssertionError(f"No care card found for plant_key={plant_key}")
        card = cards[0]
        btns = card.find_elements(
            By.CSS_SELECTOR, f"[data-testid^='care-edit-profile-care-{plant_key}-']"
        )
        if btns:
            self.scroll_and_click(btns[0])
            return
        all_btns = card.find_elements(By.CSS_SELECTOR, "button.MuiIconButton-root")
        if all_btns:
            self.scroll_and_click(all_btns[0])
        else:
            raise AssertionError(f"Could not find edit-profile button on care card for {plant_key}")

    # ── CareConfirmDialog interactions ────────────────────────────────

    def wait_for_confirm_dialog(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the MUI dialog with confirm fields is visible."""
        self.poll(timeout).until(EC.visibility_of_element_located(self.MUI_DIALOG))

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
        self.wait_and_click(self.CONFIRM_DIALOG_SUBMIT)

    def cancel_confirm_dialog(self) -> None:
        """Click the cancel button in the confirm dialog."""
        self.wait_and_click(self.CONFIRM_DIALOG_CANCEL)

    # ── CareProfileEditDialog interactions ────────────────────────────

    def wait_for_profile_dialog(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the CareProfileEditDialog is visible."""
        self.poll(timeout).until(EC.visibility_of_element_located(self.PROFILE_DIALOG))

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
        self.open_select_by_testid("care-style-select")
        option = self._find_care_style_option(style_label)
        self.click_menu_option(option)
        # MUI auto-closes on option click; ensure the popover is fully gone
        self.close_mui_dropdown()

    def _find_care_style_option(self, label: str):
        """Return the open care-style dropdown's option matching *label*.

        Resolved via ``textContent``, not an XPath ``contains(text(), …)``:
        the latter only sees an option's first text node and misses one
        scrolled out of the popover's visible area (MUI scrolls to the
        selected item on open). Deliberately does not go through
        ``BasePage.select_option_by_value`` -- selecting some presets here
        interrupts the commit with a confirmation dialog
        (:meth:`select_care_style_with_confirm`) instead of applying it
        immediately, so an unconditional read-back would misreport that as a
        mis-click.
        """
        target = " ".join(label.split())
        candidates = [
            (opt, " ".join((opt.get_attribute("textContent") or "").split()))
            for opt in self.driver.find_elements(*self.OPTIONS)
        ]
        for opt, text in candidates:
            if text == target:
                return opt
        for opt, text in candidates:
            if text and (target in text or text in target):
                return opt
        raise AssertionError(
            f"No option matching '{label}' in the open dropdown. Rendered "
            f"options: {[text for _, text in candidates]}"
        )

    def click_save_profile(self) -> None:
        """Click the save button in the profile dialog."""
        self.wait_and_click(self.SAVE_PROFILE_BUTTON)

    def click_cancel_profile(self) -> None:
        """Click the cancel button in the profile dialog."""
        self.wait_and_click(self.CANCEL_BUTTON)

    def click_reset_profile(self) -> None:
        """Click the reset-to-defaults button in the profile dialog."""
        self.wait_and_click(self.RESET_PROFILE_BUTTON)

    def expand_advanced_accordion(self) -> None:
        """Expand the "Erweitert" (Advanced) accordion in the profile dialog, if present."""
        locator = (
            By.CSS_SELECTOR,
            "[data-testid='care-profile-edit-dialog'] .MuiAccordionSummary-root",
        )
        accordions = self.driver.find_elements(*locator)
        if accordions:
            self.scroll_and_click(accordions[0])
            self.wait_for_loading_complete()

    def get_open_dropdown_option_texts(self) -> list[str]:
        """Return the visible label texts of an already-open MUI Select dropdown."""
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        return [opt.text for opt in options]

    def is_humidity_check_enabled(self) -> bool:
        """Return True if the humidity check switch is on."""
        el = self.find_present(self.HUMIDITY_CHECK_SWITCH)
        checkbox = el.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        return checkbox.is_selected()

    def toggle_humidity_check(self) -> None:
        """Toggle the humidity check switch."""
        el = self.wait_for_element_clickable(self.HUMIDITY_CHECK_SWITCH)
        self.scroll_and_click(el)

    def is_location_check_enabled(self) -> bool:
        """Return True if the location check switch is on."""
        el = self.find_present(self.LOCATION_CHECK_SWITCH)
        checkbox = el.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        return checkbox.is_selected()

    def toggle_location_check(self) -> None:
        """Toggle the location check switch."""
        el = self.wait_for_element_clickable(self.LOCATION_CHECK_SWITCH)
        self.scroll_and_click(el)

    def is_adaptive_learning_enabled(self) -> bool:
        """Return True if the adaptive learning switch is on."""
        el = self.find_present(self.ADAPTIVE_LEARNING_SWITCH)
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
        """Return the list of currently selected fertilizing active months.

        Each ToggleButton carries ``data-testid='fertilizing-month-{n}'`` --
        parse the month number from that suffix rather than ``.text``, which
        now renders a two-line "MMM\\n{n}" label (CareProfileForm.tsx:513-525)
        and is no longer a plain ``int()``-parseable string.
        """
        container = self.find_present(self.FERTILIZING_ACTIVE_MONTHS)
        buttons = container.find_elements(By.CSS_SELECTOR, "button.Mui-selected")
        months: list[int] = []
        for btn in buttons:
            suffix = (btn.get_attribute("data-testid") or "").rsplit("-", 1)[-1]
            if suffix.isdigit():
                months.append(int(suffix))
        return months

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

    # ── Interval controls (slider ⇆ custom numeric TextField) ──────────

    def set_interval_slider(self, testid: str, target_value: int) -> None:
        """Set an interval control identified by *testid* to *target_value*.

        The control has two render modes sharing the same testid:

        1. ``isCustom`` mode: a numeric ``<input type='number'>`` TextField.
           The value is cleared and re-entered, dispatching a ``change`` event
           so the React controlled field picks it up.
        2. Otherwise a MUI ``Slider``: the root carries the testid and the
           thumb exposes ``role='slider'`` with a hidden ``<input>``.  The value
           is set on the hidden input via the native setter plus input/change
           dispatch; if that does not take, a keyboard fallback focuses the
           thumb and positions it (``Home`` then n×``ArrowRight``).

        The numeric-field probe runs first: if an ``input[type=number]`` exists
        under the testid it is mode 1, else mode 2.
        """
        from selenium.webdriver.common.keys import Keys

        root_sel = f"[data-testid='{testid}']"

        # ── Mode 1: custom numeric TextField ──
        number_inputs = self.driver.find_elements(
            By.CSS_SELECTOR, f"{root_sel} input[type='number']"
        )
        if number_inputs:
            el = number_inputs[0]
            self.clear_and_fill(el, str(target_value))
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                el,
            )
            return

        # ── Mode 2: MUI Slider ──
        roots = self.driver.find_elements(By.CSS_SELECTOR, root_sel)
        if not roots:
            raise AssertionError(f"Interval control '{testid}' not found")
        root = roots[0]

        hidden_inputs = root.find_elements(By.CSS_SELECTOR, "input")
        if hidden_inputs:
            inp = hidden_inputs[0]
            self.driver.execute_script(
                "var el = arguments[0], v = arguments[1];"
                "var setter = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype, 'value').set;"
                "setter.call(el, v);"
                "el.dispatchEvent(new Event('input', {bubbles: true}));"
                "el.dispatchEvent(new Event('change', {bubbles: true}));",
                inp,
                str(target_value),
            )
            if str(inp.get_attribute("value")) == str(target_value):
                return

        # ── Keyboard fallback: focus thumb, home, then step right ──
        slider_els = root.find_elements(By.CSS_SELECTOR, "[role='slider']")
        slider_el = slider_els[0] if slider_els else root.find_element(By.CSS_SELECTOR, "input")
        self.scroll_and_click(slider_el)
        try:
            min_val = int(slider_el.get_attribute("aria-valuemin") or 0)
        except TypeError, ValueError:
            min_val = 0
        slider_el.send_keys(Keys.HOME)
        for _ in range(max(0, int(target_value) - min_val)):
            slider_el.send_keys(Keys.ARROW_RIGHT)

    def set_watering_interval(self, days: int) -> None:
        """Convenience wrapper: set the watering interval control to *days*."""
        self.set_interval_slider("watering-interval-slider", days)

    def get_interval_slider_value(self, testid: str) -> int:
        """Return the current value of an interval control (slider or custom field).

        Reads the numeric field's ``value`` in custom mode, otherwise the
        slider thumb's ``aria-valuenow`` (falling back to the hidden input's
        ``value``).
        """
        root_sel = f"[data-testid='{testid}']"
        number_inputs = self.driver.find_elements(
            By.CSS_SELECTOR, f"{root_sel} input[type='number']"
        )
        if number_inputs:
            return int(number_inputs[0].get_attribute("value") or 0)

        roots = self.driver.find_elements(By.CSS_SELECTOR, root_sel)
        if not roots:
            raise AssertionError(f"Interval control '{testid}' not found")
        root = roots[0]

        slider_els = root.find_elements(By.CSS_SELECTOR, "[role='slider']")
        if slider_els:
            now = slider_els[0].get_attribute("aria-valuenow")
            if now is not None:
                return int(now)
        inputs = root.find_elements(By.CSS_SELECTOR, "input")
        if inputs:
            return int(inputs[0].get_attribute("value") or 0)
        raise AssertionError(f"Could not read value of interval control '{testid}'")

    def select_care_style_with_confirm(self, label: str) -> None:
        """Select a care style by label and accept the preset-reset confirm dialog.

        Opens ``care-style-select`` and clicks the option matching *label*.
        Selecting a preset may raise a generic ``ConfirmDialog`` warning that
        stored customizations will be reset; if it appears, its
        ``confirm-dialog-confirm`` button is clicked.  Unlike ``select_care_style``
        this does not send a body-level ESCAPE (which would cancel the confirm
        dialog).
        """
        import time

        self.open_select_by_testid("care-style-select")
        option = self._find_care_style_option(label)
        self.click_menu_option(option)
        time.sleep(0.3)
        confirms = self.driver.find_elements(*self.GENERIC_CONFIRM_CONFIRM)
        if confirms and any(c.is_displayed() for c in confirms):
            self.scroll_and_click(self.wait_for_element_clickable(self.GENERIC_CONFIRM_CONFIRM))

    # ── Snackbar ──────────────────────────────────────────────────────

    def wait_for_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for a snackbar to appear and return its text."""
        el = self.poll(timeout).until(EC.visibility_of_element_located(self.SNACKBAR))
        return el.text

    def has_snackbar(self) -> bool:
        """Return True if any snackbar is currently visible."""
        elements = self.driver.find_elements(*self.SNACKBAR)
        return len(elements) > 0 and elements[0].is_displayed()

    def has_error_snackbar(self) -> bool:
        """Return True if the visible snackbar reports an error.

        A failed care action routes through ``handleError``, which enqueues the
        *error* notistack variant; the happy path enqueues info/success. Both
        render the same message node, so the variant is what distinguishes
        "it worked" from "the request came back 4xx/5xx".
        """
        elements = self.driver.find_elements(*self.SNACKBAR_ERROR)
        return any(el.is_displayed() for el in elements)

    # ── Dialog closed waiter ──────────────────────────────────────────

    def wait_for_dialog_closed(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until all MUI dialogs are closed."""
        self.poll(timeout).until(EC.invisibility_of_element_located(self.MUI_DIALOG))
