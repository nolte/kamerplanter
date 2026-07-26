"""Page object for the Companion Planting page."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class CompanionPlantingPage(BasePage):
    """Interact with the Companion Planting page (``/stammdaten/companion-planting``)."""

    PATH = "/stammdaten/companion-planting"

    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    # The main species picker was refactored from a MUI <Select> to a MUI
    # <Autocomplete>, whose clickable trigger is the inner combobox <input>
    # (there is no .MuiSelect-select child). The dialog target picker below is
    # still a real MUI <Select> and is driven by testid through the base helpers.
    SPECIES_SELECT = (By.CSS_SELECTOR, "[data-testid='species-select'] input")
    COMPATIBLE_CARD = (By.XPATH, "//h6[starts-with(normalize-space(text()), 'Kompatible')]/ancestor::div[contains(@class, 'MuiCard-root')]")
    INCOMPATIBLE_CARD = (By.XPATH, "//h6[starts-with(normalize-space(text()), 'Inkompatible')]/ancestor::div[contains(@class, 'MuiCard-root')]")
    ADD_COMPATIBLE_BTN = (By.CSS_SELECTOR, "[data-testid='add-compatible-button']")
    ADD_INCOMPATIBLE_BTN = (By.CSS_SELECTOR, "[data-testid='add-incompatible-button']")

    # Dialog locators -- addressed by the dialog's own data-testid rather than a
    # bare role='dialog'. Below the `md` breakpoint (mobile AND tablet) the
    # sidebar Drawer is `temporary` + `keepMounted`, so its paper also carries
    # role='dialog' and wins the document-order lookup. See base_page.
    DIALOG = (By.CSS_SELECTOR, "[data-testid='companion-planting-dialog']")
    #: The dialog's target picker is a real MUI ``Select``; it is driven through
    #: ``open_select_by_testid`` / ``select_option_by_label`` rather than through
    #: a locator here, because those verify the open and the committed value.
    DIALOG_TARGET_SELECT_TESTID = "target-species-select"
    DIALOG_SCORE_INPUT = (By.CSS_SELECTOR, "[data-testid='score-input'] input")
    DIALOG_REASON_INPUT = (By.CSS_SELECTOR, "[data-testid='reason-input'] textarea")
    DIALOG_CREATE_BTN = (
        By.XPATH,
        "//*[@data-testid='companion-planting-dialog']//button[contains(text(), 'Erstellen')]",
    )
    DIALOG_CANCEL_BTN = (
        By.XPATH,
        "//*[@data-testid='companion-planting-dialog']//button[contains(text(), 'Abbrechen')]",
    )

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> CompanionPlantingPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    def get_title(self) -> str:
        return self.wait_for_element(self.PAGE_TITLE).text

    def select_species(self, species_name: str) -> None:
        """Select a species from the Autocomplete dropdown."""
        from selenium.webdriver.support.ui import WebDriverWait
        self.close_mui_dropdown()
        select = self.wait_for_element_clickable(self.SPECIES_SELECT)
        self.scroll_and_click(select)
        self.wait_for_element_visible((By.CSS_SELECTOR, "li[role='option']"), timeout=10)
        # Autocomplete options render the common name and scientific name in two
        # stacked <Typography> blocks, so o.text is multi-line ("Name\nGenus
        # species"). Match Selenium-side on whitespace-normalised text instead of
        # an XPath contains(): the XPath string-value has no newline, so it would
        # never contain the multi-line label the caller passes back from
        # get_species_options().
        option = self._find_option(species_name)
        self.scroll_and_click(option)
        WebDriverWait(self.driver, 5).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "li[role='option']")) == 0
        )
        time.sleep(1)  # Wait for companion data to load

    def _find_option(self, name: str):
        """Return the open-listbox option matching *name* (whitespace-normalised)."""
        target = " ".join(name.split())
        deadline = time.time() + 10
        while time.time() < deadline:
            for option in self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']"):
                otext = " ".join(option.text.split())
                if otext == target or target in otext or otext in target:
                    return option
            time.sleep(0.2)
        raise AssertionError(f"Option matching '{name}' not found in the dropdown")

    def get_species_options(self) -> list[str]:
        """Return available species names in the dropdown."""
        self.close_mui_dropdown()
        select = self.wait_for_element_clickable(self.SPECIES_SELECT)
        self.scroll_and_click(select)
        self.wait_for_element_visible((By.CSS_SELECTOR, "li[role='option']"), timeout=10)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options if o.text]
        self.close_mui_dropdown()
        return texts

    def get_compatible_species(self) -> list[str]:
        """Return names of compatible species."""
        try:
            cards = self.driver.find_elements(*self.COMPATIBLE_CARD)
            if not cards:
                return []
            items = cards[0].find_elements(By.CSS_SELECTOR, ".MuiListItemText-primary")
            return [i.text for i in items]
        except Exception:
            return []

    def get_incompatible_species(self) -> list[str]:
        try:
            cards = self.driver.find_elements(*self.INCOMPATIBLE_CARD)
            if not cards:
                return []
            items = cards[0].find_elements(By.CSS_SELECTOR, ".MuiListItemText-primary")
            return [i.text for i in items]
        except Exception:
            return []

    def has_compatible_card(self) -> bool:
        """Return True if the 'Kompatible Arten' card is present on the page."""
        return len(self.driver.find_elements(*self.COMPATIBLE_CARD)) > 0

    def has_incompatible_card(self) -> bool:
        """Return True if the 'Inkompatible Arten' card is present on the page."""
        return len(self.driver.find_elements(*self.INCOMPATIBLE_CARD)) > 0

    def get_compatible_card_chip_count(self) -> int:
        """Return the number of MUI Chip badges (e.g. score chips) inside the compatible card."""
        cards = self.driver.find_elements(*self.COMPATIBLE_CARD)
        if not cards:
            return 0
        return len(cards[0].find_elements(By.CSS_SELECTOR, ".MuiChip-root"))

    def has_compatible_empty_state(self) -> bool:
        try:
            cards = self.driver.find_elements(*self.COMPATIBLE_CARD)
            if not cards:
                return False
            return len(cards[0].find_elements(By.CSS_SELECTOR, "[data-testid='empty-state']")) > 0
        except Exception:
            return False

    def has_incompatible_empty_state(self) -> bool:
        try:
            cards = self.driver.find_elements(*self.INCOMPATIBLE_CARD)
            if not cards:
                return False
            return len(cards[0].find_elements(By.CSS_SELECTOR, "[data-testid='empty-state']")) > 0
        except Exception:
            return False

    def click_add_compatible(self) -> None:
        self.close_mui_dropdown()
        time.sleep(0.5)  # Wait for MUI animation to complete before clicking
        btn = self.wait_for_element_clickable(self.ADD_COMPATIBLE_BTN)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.DIALOG)

    def click_add_incompatible(self) -> None:
        self.close_mui_dropdown()
        time.sleep(0.5)  # Wait for MUI animation to complete before clicking
        btn = self.wait_for_element_clickable(self.ADD_INCOMPATIBLE_BTN)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.DIALOG)

    def is_dialog_create_button_enabled(self) -> bool:
        btn = self.driver.find_element(*self.DIALOG_CREATE_BTN)
        return btn.is_enabled()

    def select_dialog_target(self, species_name: str) -> None:
        """Pick the dialog's target species by its rendered label.

        Routed through the verified base helpers. The predecessor was the legacy
        driver in full: ``scroll_and_click`` on a MUI Select trigger (which opens
        only on ``mousedown``), an unscoped ``//li[@role='option']`` XPath keyed
        on the translated label, a coordinate click on a popover that can still
        reposition, and no read-back at all — so every one of those four steps
        could fail while the helper reported success. TC-REQ-001-0xx
        (``test_add_incompatible_species_relationship``, light profile) showed
        the result: the option popover still open over the dialog, with nothing
        committed.

        ``open_select_by_testid`` verifies the menu actually opened (and retries
        with an explicit mousedown pair), and ``select_option_by_label`` resolves
        the label to the option's ``data-value``, clicks it on the resolved
        element and asserts the Select really holds that value afterwards.
        """
        self.close_mui_dropdown()
        self.open_select_by_testid(self.DIALOG_TARGET_SELECT_TESTID)
        self.select_option_by_label(species_name)

    def get_dialog_target_options(self) -> list[str]:
        self.close_mui_dropdown()
        self.open_select_by_testid(self.DIALOG_TARGET_SELECT_TESTID)
        options = self.driver.find_elements(*self.OPTIONS)
        texts = [o.text for o in options if o.text]
        self.close_mui_dropdown()
        return texts

    def set_dialog_score(self, score: str) -> None:
        el = self.wait_for_element_clickable(self.DIALOG_SCORE_INPUT)
        el.clear()
        el.send_keys(score)

    def set_dialog_reason(self, reason: str) -> None:
        el = self.wait_for_element_clickable(self.DIALOG_REASON_INPUT)
        el.clear()
        el.send_keys(reason)

    def click_dialog_create(self) -> None:
        self.close_mui_dropdown()
        btn = self.wait_for_element_clickable(self.DIALOG_CREATE_BTN)
        self.scroll_and_click(btn)

    def click_dialog_cancel(self) -> None:
        self.close_mui_dropdown()
        btn = self.wait_for_element_clickable(self.DIALOG_CANCEL_BTN)
        self.scroll_and_click(btn)
