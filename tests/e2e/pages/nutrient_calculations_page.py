"""Page object for the Nutrient Calculations page (REQ-004)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class NutrientCalculationsPage(BasePage):
    """Interact with the Nutrient Calculations page (``/duengung/calculations``).

    The page contains four independent calculation panels:
    - Mixing Protocol
    - Flushing
    - Runoff Analysis
    - Mixing Safety
    """

    PATH = "/duengung/calculations"

    # Locators — the page has no wrapper data-testid, but PageTitle is present
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")

    # ── Mixing Protocol panel ─────────────────────────────────────────
    # MUI TextField inputs identified by their label text via aria-label or
    # by position within the first Grid card.  The NutrientCalculationsPage
    # does NOT use FormTextField (no data-testid on inputs), so we locate by
    # input[type='number'] order within each card.

    # We locate all cards by their h6 heading text.
    # Card 1: Mixing Protocol (first in left column)
    # Card 2: Flushing        (first in right column)
    # Card 3: Runoff Analysis (second in left column)
    # Card 4: Mixing Safety   (second in right column)

    ALL_CARDS = (By.CSS_SELECTOR, ".MuiCard-root")

    # Within each card:  number inputs in order of appearance
    # Mixing Protocol card inputs (index 0..5 = volume, targetEc, targetPh, baseEc, basePh)
    # Flushing card inputs (index 0..1 = currentEc, daysUntilHarvest)
    # Runoff card inputs (index 0..5 = inputEc, runoffEc, inputPh, runoffPh, inputVol, runoffVol)
    # Mixing Safety card has a text input (fertilizer keys)

    CALCULATE_BUTTONS = (By.CSS_SELECTOR, ".MuiCard-root .MuiButton-contained")

    # Result areas — Alert elements inside each card
    ALERTS = (By.CSS_SELECTOR, ".MuiAlert-root")

    # Data tables rendered by the mixing-protocol results
    RESULT_TABLES = (By.CSS_SELECTOR, "[data-testid='data-table']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> NutrientCalculationsPage:
        """Navigate to the nutrient calculations page and wait for the title."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE_TITLE)
        return self

    # ── Internal helpers ───────────────────────────────────────────────

    def _get_card_by_heading(self, heading_text: str):
        """Return the MUI Card element whose h6 contains *heading_text*."""
        cards = self.driver.find_elements(*self.ALL_CARDS)
        for card in cards:
            headings = card.find_elements(By.TAG_NAME, "h6")
            if any(heading_text.lower() in h.text.lower() for h in headings):
                return card
        raise ValueError(f"Card with heading '{heading_text}' not found")

    def _fill_number_input_in_card(self, card, input_index: int, value: float) -> None:
        """Clear and fill the Nth number input within a card."""
        inputs = card.find_elements(By.CSS_SELECTOR, "input[type='number']")
        if input_index >= len(inputs):
            raise IndexError(
                f"Card has only {len(inputs)} number inputs, requested index {input_index}"
            )
        el = inputs[input_index]
        self.scroll_and_click(el)
        # Triple-click to select all, then overwrite
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(self.driver).triple_click(el).perform()
        el.send_keys(str(value))

    def _fill_text_input_in_card(self, card, value: str) -> None:
        """Clear and fill the first text input (non-number) within a card."""
        inputs = card.find_elements(By.CSS_SELECTOR, "input:not([type='number'])")
        if not inputs:
            raise ValueError("No text input found in card")
        el = inputs[0]
        self.scroll_and_click(el)
        el.clear()
        el.send_keys(value)

    def _click_button_in_card(self, card) -> None:
        """Click the contained Button inside a card."""
        btn = card.find_element(By.CSS_SELECTOR, ".MuiButton-contained")
        self.scroll_and_click(btn)

    def _get_alert_texts_in_card(self, card) -> list[str]:
        """Return the text of all Alert elements within a card."""
        alerts = card.find_elements(By.CSS_SELECTOR, ".MuiAlert-root")
        return [a.text for a in alerts if a.is_displayed() and a.text]

    # ── Mixing Protocol ────────────────────────────────────────────────

    def fill_mixing_protocol(
        self,
        volume: float = 10.0,
        target_ec: float = 1.8,
        target_ph: float = 6.0,
        base_ec: float = 0.3,
        base_ph: float = 7.2,
        fertilizer_keys: str = "",
    ) -> None:
        """Fill all input fields in the Mixing Protocol panel."""
        card = self._get_card_by_heading("Mischprotokoll")
        # Number inputs in order: volume, targetEc, targetPh, baseEc, basePh
        for idx, val in enumerate([volume, target_ec, target_ph, base_ec, base_ph]):
            self._fill_number_input_in_card(card, idx, val)
        # Fertilizer keys text field
        text_inputs = card.find_elements(By.CSS_SELECTOR, "input:not([type='number'])")
        if text_inputs:
            el = text_inputs[0]
            self.scroll_and_click(el)
            el.clear()
            el.send_keys(fertilizer_keys)

    def click_calculate_mixing_protocol(self) -> None:
        """Click the calculate button in the Mixing Protocol panel."""
        card = self._get_card_by_heading("Mischprotokoll")
        self._click_button_in_card(card)

    def get_mixing_protocol_alerts(self) -> list[str]:
        """Return Alert texts from the Mixing Protocol result area."""
        card = self._get_card_by_heading("Mischprotokoll")
        return self._get_alert_texts_in_card(card)

    def mixing_protocol_has_result_table(self) -> bool:
        """Return True if a data table appeared in the Mixing Protocol card."""
        card = self._get_card_by_heading("Mischprotokoll")
        tables = card.find_elements(By.CSS_SELECTOR, "[data-testid='data-table']")
        return len(tables) > 0

    def mixing_protocol_has_instructions(self) -> bool:
        """Return True if step-numbered instructions appeared."""
        card = self._get_card_by_heading("Mischprotokoll")
        paragraphs = card.find_elements(By.TAG_NAME, "p")
        return any(p.text.strip().startswith(("1.", "2.", "3.")) for p in paragraphs)

    # ── Flushing ───────────────────────────────────────────────────────

    def fill_flushing(
        self,
        current_ec: float = 1.5,
        days_until_harvest: int = 14,
    ) -> None:
        """Fill all input fields in the Flushing panel."""
        card = self._get_card_by_heading("Aussp")  # "Ausspülung" / "Flushing"
        self._fill_number_input_in_card(card, 0, current_ec)
        self._fill_number_input_in_card(card, 1, float(days_until_harvest))

    def click_calculate_flushing(self) -> None:
        """Click the calculate button in the Flushing panel."""
        card = self._get_card_by_heading("Aussp")
        self._click_button_in_card(card)

    def get_flushing_alerts(self) -> list[str]:
        """Return Alert texts from the Flushing result area."""
        card = self._get_card_by_heading("Aussp")
        return self._get_alert_texts_in_card(card)

    def flushing_has_schedule_table(self) -> bool:
        """Return True if a schedule data table appeared in the Flushing card."""
        card = self._get_card_by_heading("Aussp")
        tables = card.find_elements(By.CSS_SELECTOR, "[data-testid='data-table']")
        return len(tables) > 0

    # ── Runoff Analysis ────────────────────────────────────────────────

    def fill_runoff_analysis(
        self,
        input_ec: float = 1.8,
        runoff_ec: float = 2.5,
        input_ph: float = 6.0,
        runoff_ph: float = 5.5,
        input_vol: float = 1.0,
        runoff_vol: float = 0.2,
    ) -> None:
        """Fill all input fields in the Runoff Analysis panel."""
        card = self._get_card_by_heading("Abfluss")
        for idx, val in enumerate([input_ec, runoff_ec, input_ph, runoff_ph, input_vol, runoff_vol]):
            self._fill_number_input_in_card(card, idx, val)

    def click_calculate_runoff(self) -> None:
        """Click the calculate button in the Runoff Analysis panel."""
        card = self._get_card_by_heading("Abfluss")
        self._click_button_in_card(card)

    def get_runoff_alerts(self) -> list[str]:
        """Return Alert texts from the Runoff Analysis result area."""
        card = self._get_card_by_heading("Abfluss")
        return self._get_alert_texts_in_card(card)

    def runoff_health_is(self, health: str) -> bool:
        """Return True if the overall-health Alert with the given class is present.

        *health* should be one of 'success', 'warning', 'error'.
        """
        card = self._get_card_by_heading("Abfluss")
        alerts = card.find_elements(By.CSS_SELECTOR, f".MuiAlert-color{health.capitalize()}")
        return any(a.is_displayed() for a in alerts)

    # ── Mixing Safety ──────────────────────────────────────────────────

    def fill_mixing_safety(self, fertilizer_keys: str) -> None:
        """Fill the fertilizer keys input in the Mixing Safety panel."""
        card = self._get_card_by_heading("Mischsicherheit")
        self._fill_text_input_in_card(card, fertilizer_keys)

    def click_validate_mixing_safety(self) -> None:
        """Click the validate button in the Mixing Safety panel."""
        card = self._get_card_by_heading("Mischsicherheit")
        self._click_button_in_card(card)

    def get_mixing_safety_alerts(self) -> list[str]:
        """Return Alert texts from the Mixing Safety result area."""
        card = self._get_card_by_heading("Mischsicherheit")
        return self._get_alert_texts_in_card(card)

    def mixing_safety_result_is_safe(self) -> bool:
        """Return True if the mixing safety result shows a success alert."""
        card = self._get_card_by_heading("Mischsicherheit")
        alerts = card.find_elements(By.CSS_SELECTOR, ".MuiAlert-colorSuccess")
        return any(a.is_displayed() for a in alerts)

    def mixing_safety_result_is_unsafe(self) -> bool:
        """Return True if the mixing safety result shows an error alert."""
        card = self._get_card_by_heading("Mischsicherheit")
        alerts = card.find_elements(By.CSS_SELECTOR, ".MuiAlert-colorError")
        return any(a.is_displayed() for a in alerts)

    # ── General page helpers ───────────────────────────────────────────

    def get_all_card_headings(self) -> list[str]:
        """Return h6 heading texts of all visible cards."""
        headings = self.driver.find_elements(By.CSS_SELECTOR, ".MuiCard-root h6")
        return [h.text for h in headings if h.text]

    def get_page_title_text(self) -> str:
        """Return the page title text."""
        el = self.wait_for_element(self.PAGE_TITLE)
        return el.text
