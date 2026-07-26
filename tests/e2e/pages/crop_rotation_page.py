"""Page object for the Crop Rotation page."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class CropRotationPage(BasePage):
    """Interact with the Crop Rotation page (``/stammdaten/crop-rotation``)."""

    PATH = "/stammdaten/crop-rotation"

    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    # The main family picker was refactored from a MUI <Select> to a MUI
    # <Autocomplete>; its clickable trigger is the inner combobox <input>.
    # Scope by the testid — the page has a second combobox (filter-nutrient-
    # demand) so a bare role='combobox' locator would be ambiguous. The dialog
    # target picker below is still a real MUI <Select>.
    FAMILY_SELECT = (By.CSS_SELECTOR, "[data-testid='from-family-select'] input")
    SUCCESSOR_LIST = (By.CSS_SELECTOR, ".MuiList-root .MuiListItem-root")
    ADD_SUCCESSOR_BTN = (By.CSS_SELECTOR, "[data-testid='add-successor-button']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # Dialog locators -- addressed by the dialog's own data-testid rather than a
    # bare role='dialog'. Below the `md` breakpoint (mobile AND tablet) the
    # sidebar Drawer is `temporary` + `keepMounted`, so its paper also carries
    # role='dialog' and wins the document-order lookup. See base_page.
    DIALOG = (By.CSS_SELECTOR, "[data-testid='crop-rotation-dialog']")
    #: The dialog's target picker is a real MUI ``Select``; it is driven through
    #: ``open_select_by_testid`` / ``select_option_by_label`` rather than through
    #: a locator here, because those verify the open and the committed value.
    DIALOG_TARGET_SELECT_TESTID = "to-family-select"
    DIALOG_WAIT_YEARS = (By.CSS_SELECTOR, "[data-testid='wait-years-input'] input")
    DIALOG_CREATE_BTN = (
        By.XPATH,
        "//*[@data-testid='crop-rotation-dialog']//button[contains(text(), 'Erstellen')]",
    )
    DIALOG_CANCEL_BTN = (
        By.XPATH,
        "//*[@data-testid='crop-rotation-dialog']//button[contains(text(), 'Abbrechen')]",
    )

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> CropRotationPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    def get_title(self) -> str:
        return self.wait_for_element(self.PAGE_TITLE).text

    def select_family(self, family_name: str) -> None:
        from selenium.webdriver.support.ui import WebDriverWait

        self.close_mui_dropdown()
        select = self.wait_for_element_clickable(self.FAMILY_SELECT)
        self.scroll_and_click(select)
        self.wait_for_element_visible((By.CSS_SELECTOR, "li[role='option']"), timeout=10)
        # Autocomplete options render family name + scientific name in stacked
        # <Typography> blocks (multi-line o.text), so match Selenium-side on
        # normalised text rather than an XPath contains() that can't see the
        # newline. See _find_option.
        option = self._find_option(family_name)
        self.click_menu_option(option)
        # Wait for options to be removed from DOM (natural close after selection)
        WebDriverWait(self.driver, 5).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "li[role='option']")) == 0
        )
        time.sleep(1)  # Wait for successors to load

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

    def get_family_options(self) -> list[str]:
        self.close_mui_dropdown()
        select = self.wait_for_element_clickable(self.FAMILY_SELECT)
        self.scroll_and_click(select)
        self.wait_for_element_visible((By.CSS_SELECTOR, "li[role='option']"), timeout=10)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        texts = [o.text for o in options if o.text]
        self.close_mui_dropdown()
        return texts

    def get_successor_count(self) -> int:
        return len(self.driver.find_elements(*self.SUCCESSOR_LIST))

    def get_successor_names(self) -> list[str]:
        items = self.driver.find_elements(*self.SUCCESSOR_LIST)
        return [i.find_element(By.CSS_SELECTOR, ".MuiListItemText-primary").text for i in items]

    def has_empty_state(self) -> bool:
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    def click_add_successor(self) -> None:
        self.close_mui_dropdown()
        time.sleep(0.5)  # Wait for MUI animation to complete before clicking
        btn = self.wait_for_element_clickable(self.ADD_SUCCESSOR_BTN)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.DIALOG)

    def is_dialog_create_button_enabled(self) -> bool:
        btn = self.driver.find_element(*self.DIALOG_CREATE_BTN)
        return btn.is_enabled()

    def select_dialog_target(self, family_name: str) -> None:
        """Pick the dialog's target family by its rendered label.

        Structurally identical to `CompanionPlantingPage.select_dialog_target`
        (same `TextField select` with ``MenuItem value={key}``), and migrated for
        the same reason: the predecessor opened a mousedown-only Select with a
        coordinate click, matched an unscoped ``li[role='option']`` on the
        translated label, clicked a possibly-repositioning popover at
        coordinates, and verified nothing.
        """
        self.close_mui_dropdown()
        self.open_select_by_testid(self.DIALOG_TARGET_SELECT_TESTID)
        self.select_option_by_label(family_name)

    def get_dialog_target_options(self) -> list[str]:
        self.close_mui_dropdown()
        self.open_select_by_testid(self.DIALOG_TARGET_SELECT_TESTID)
        # Keeps the predecessor's 10s budget for the options to render, and its
        # loud failure when none ever do: `open_select_in` deliberately tolerates
        # a legitimately empty listbox (2s), which would turn a slow render into
        # an empty read and let the caller skip for the wrong reason.
        self.wait_for_element_visible(self.OPTIONS, timeout=10)
        options = self.driver.find_elements(*self.OPTIONS)
        texts = [o.text for o in options if o.text]
        self.close_mui_dropdown()
        return texts

    def set_dialog_wait_years(self, years: str) -> None:
        # MUI controlled number input + useState default: el.clear() drops the
        # DOM value but React-state survives, so plain send_keys() concatenates
        # ("3" + "4" = "34"). clear_and_fill() syncs the React state via the
        # native value-setter + input/change events.
        el = self.wait_for_element_clickable(self.DIALOG_WAIT_YEARS)
        self.clear_and_fill(el, years)

    def get_dialog_wait_years_value(self) -> str:
        """Return the current value of the wait-years input in the successor dialog."""
        el = self.driver.find_element(*self.DIALOG_WAIT_YEARS)
        return el.get_attribute("value") or ""

    def click_dialog_create(self) -> None:
        self.close_mui_dropdown()
        btn = self.wait_for_element_clickable(self.DIALOG_CREATE_BTN)
        self.scroll_and_click(btn)

    def click_dialog_cancel(self) -> None:
        self.close_mui_dropdown()
        btn = self.wait_for_element_clickable(self.DIALOG_CANCEL_BTN)
        self.scroll_and_click(btn)
