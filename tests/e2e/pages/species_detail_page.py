"""Page object for the Species detail page (3 tabs: Edit, Cultivars, Lifecycle)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class SpeciesDetailPage(BasePage):
    """Interact with the Species detail page (``/stammdaten/species/:key``)."""

    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    DELETE_BUTTON = (By.XPATH, "//button[contains(@class, 'MuiButton-colorError')]")
    TABS = (By.CSS_SELECTOR, "button[role='tab']")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # Cultivar tab locators
    CULTIVAR_CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    CULTIVAR_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    CREATE_DIALOG = (By.CSS_SELECTOR, "[data-testid='create-dialog']")

    # Lifecycle tab locators
    LIFECYCLE_FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")

    # Growth phase locators
    PHASE_CREATE_BUTTON = (By.XPATH, "//button[contains(normalize-space(.), 'Phase erstellen')]")
    PHASE_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> SpeciesDetailPage:
        self.navigate(f"/stammdaten/species/{key}")
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    def get_title(self) -> str:
        return self.get_text_stable(self.PAGE_TITLE)

    # ── Tabs ───────────────────────────────────────────────────────────

    def get_tab_labels(self) -> list[str]:
        tabs = self.driver.find_elements(*self.TABS)
        return [t.text for t in tabs]

    def click_tab(self, index: int) -> None:
        tabs = self.driver.find_elements(*self.TABS)
        if index < len(tabs):
            self.scroll_and_click(tabs[index])

    def click_tab_by_label(self, label: str) -> None:
        tabs = self.driver.find_elements(*self.TABS)
        for tab in tabs:
            if tab.text.upper() == label.upper():
                self.scroll_and_click(tab)
                return
        raise ValueError(f"Tab '{label}' not found")

    # ── Edit tab (tab 0) ──────────────────────────────────────────────

    def get_field_value(self, field_name: str) -> str:
        el = self.driver.find_element(
            By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input"
        )
        return el.get_attribute("value") or ""

    def set_field(self, field_name: str, value: str) -> None:
        # Try input first, fall back to textarea (multiline fields)
        locator_input = (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        locator_textarea = (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] textarea:not([aria-hidden])")
        elements = self.driver.find_elements(*locator_input)
        if elements:
            el = self.wait_for_element_clickable(locator_input)
        else:
            el = self.wait_for_element_clickable(locator_textarea)
        el.clear()
        el.send_keys(value)

    def add_chip(self, field_name: str, value: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.send_keys(value)
        el.send_keys(Keys.ENTER)

    def select_option(self, field_name: str, value_text: str) -> None:
        import time

        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()
        # Dismiss MUI Select backdrop/popover to unblock subsequent interactions
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

    def click_save(self) -> None:
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def click_delete(self) -> None:
        self.wait_for_element_clickable(self.DELETE_BUTTON).click()
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_delete(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_BUTTON).click()

    def cancel_delete(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_CANCEL).click()

    def has_delete_button(self) -> bool:
        return len(self.driver.find_elements(*self.DELETE_BUTTON)) > 0

    # ── Cultivar tab (tab 1) ──────────────────────────────────────────

    def get_cultivar_count(self) -> int:
        return len(self.driver.find_elements(*self.CULTIVAR_TABLE_ROWS))

    def get_cultivar_names(self) -> list[str]:
        rows = self.driver.find_elements(*self.CULTIVAR_TABLE_ROWS)
        names = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                names.append(cells[0].text)
        return names

    def click_cultivar_row(self, index: int) -> None:
        rows = self.driver.find_elements(*self.CULTIVAR_TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])

    def click_cultivar_create(self) -> None:
        self.wait_for_element_clickable(self.CULTIVAR_CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def delete_cultivar_at_index(self, index: int) -> None:
        """Click the delete icon in the actions column of a cultivar row."""
        rows = self.driver.find_elements(*self.CULTIVAR_TABLE_ROWS)
        if index < len(rows):
            delete_btn = rows[index].find_element(By.CSS_SELECTOR, "button[aria-label]")
            self.scroll_and_click(delete_btn)
            self.wait_for_element_visible(self.CONFIRM_DIALOG)

    # ── Cultivar create dialog ─────────────────────────────────────────

    def fill_cultivar_form(self, name: str, **kwargs: str) -> None:
        name_el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
        )
        name_el.clear()
        name_el.send_keys(name)

        for field, value in kwargs.items():
            el = self.wait_for_element_clickable(
                (By.CSS_SELECTOR, f"[data-testid='form-field-{field}'] input")
            )
            el.clear()
            el.send_keys(value)

    def submit_cultivar_form(self) -> None:
        self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
        ).click()

    # ── Lifecycle tab (tab 2) ─────────────────────────────────────────

    def get_lifecycle_submit_label(self) -> str:
        el = self.wait_for_element(self.LIFECYCLE_FORM_SUBMIT)
        return el.text

    def set_lifecycle_field(self, field_name: str, value: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.clear()
        el.send_keys(value)

    def select_lifecycle_option(self, field_name: str, value_text: str) -> None:
        self.select_option(field_name, value_text)

    def toggle_lifecycle_switch(self, field_name: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input[type='checkbox']")
        )
        self.scroll_and_click(el)

    def click_lifecycle_save(self) -> None:
        self.wait_for_element_clickable(self.LIFECYCLE_FORM_SUBMIT).click()

    # ── Growth phases (within lifecycle tab) ──────────────────────────

    def has_growth_phase_section(self) -> bool:
        return len(self.driver.find_elements(*self.PHASE_CREATE_BUTTON)) > 0

    def get_phase_count(self) -> int:
        return len(self.driver.find_elements(*self.PHASE_TABLE_ROWS))

    def get_phase_names(self) -> list[str]:
        rows = self.driver.find_elements(*self.PHASE_TABLE_ROWS)
        names = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                names.append(cells[1].text)  # display_name column
        return names

    def click_phase_create(self) -> None:
        self.wait_for_element_clickable(self.PHASE_CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def fill_phase_form(self, name: str, display_name: str, duration: str,
                        order: str, **kwargs: str) -> None:
        self.set_field("name", name)
        self.set_field("display_name", display_name)
        self.set_field("typical_duration_days", duration)
        self.set_field("sequence_order", order)

        for field, value in kwargs.items():
            if field == "stress_tolerance":
                self.select_option(field, value)
            elif field in ("is_terminal", "allows_harvest"):
                self.toggle_lifecycle_switch(field)
            else:
                self.set_field(field, value)

    def submit_phase_form(self) -> None:
        # Target the submit button inside the create-dialog (GrowthPhaseDialog)
        # to avoid hitting the lifecycle config form's submit button
        self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='create-dialog'] [data-testid='form-submit-button']")
        ).click()

    def click_phase_row(self, index: int) -> None:
        rows = self.driver.find_elements(*self.PHASE_TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])

    def delete_phase_at_index(self, index: int) -> None:
        rows = self.driver.find_elements(*self.PHASE_TABLE_ROWS)
        if index < len(rows):
            delete_btn = rows[index].find_element(By.CSS_SELECTOR, "button[aria-label]")
            self.scroll_and_click(delete_btn)
            self.wait_for_element_visible(self.CONFIRM_DIALOG)
