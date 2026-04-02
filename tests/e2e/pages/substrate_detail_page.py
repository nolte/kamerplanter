"""Page object for the Substrate detail page (REQ-019)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class SubstrateDetailPage(BasePage):
    """Interact with the Substrate detail page (``/standorte/substrates/:key``)."""

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='substrate-detail-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")

    # ── Delete button ──────────────────────────────────────────────────
    DELETE_BUTTON = (By.XPATH, "//button[contains(@class, 'MuiButton-colorError')]")

    # ── ConfirmDialog ──────────────────────────────────────────────────
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Edit form field locators ───────────────────────────────────────
    FORM_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-type'] .MuiSelect-select")
    FORM_BRAND = (By.CSS_SELECTOR, "[data-testid='form-field-brand'] input")
    FORM_NAME_DE = (By.CSS_SELECTOR, "[data-testid='form-field-name_de'] input")
    FORM_NAME_EN = (By.CSS_SELECTOR, "[data-testid='form-field-name_en'] input")
    FORM_PH_BASE = (By.CSS_SELECTOR, "[data-testid='form-field-ph_base'] input")
    FORM_EC_BASE = (By.CSS_SELECTOR, "[data-testid='form-field-ec_base_ms'] input")
    FORM_WATER_RETENTION = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-water_retention'] .MuiSelect-select",
    )
    FORM_AIR_POROSITY = (By.CSS_SELECTOR, "[data-testid='form-field-air_porosity_percent'] input")
    FORM_BUFFER_CAPACITY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-buffer_capacity'] .MuiSelect-select",
    )
    FORM_REUSABLE = (By.CSS_SELECTOR, "[data-testid='form-field-reusable'] .MuiSwitch-root")
    FORM_MAX_REUSE = (By.CSS_SELECTOR, "[data-testid='form-field-max_reuse_cycles'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # ── Section cards ──────────────────────────────────────────────────
    SECTION_CARDS = (By.CSS_SELECTOR, "[data-testid='substrate-detail-page'] .MuiCard-root")

    # ── Batches section ────────────────────────────────────────────────
    BATCH_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    BATCH_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # ── Alert banner ───────────────────────────────────────────────────
    ALERTS = (By.CSS_SELECTOR, ".MuiAlert-root")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, substrate_key: str) -> SubstrateDetailPage:
        """Navigate to the substrate detail page for *substrate_key*."""
        self.navigate(f"/standorte/substrates/{substrate_key}")
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Page info ──────────────────────────────────────────────────────

    def get_title(self) -> str:
        """Return the substrate name from the page title."""
        return self.get_text_stable(self.PAGE_TITLE)

    def get_section_card_count(self) -> int:
        """Return the number of section cards on the detail page."""
        return len(self.driver.find_elements(*self.SECTION_CARDS))

    # ── Edit form values ───────────────────────────────────────────────

    def get_field_value(self, field_name: str) -> str:
        """Return the current value of an input field by its data-testid name."""
        locator = (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        el = self.wait_for_element(locator)
        return el.get_attribute("value") or ""

    def get_select_value(self, field_name: str) -> str:
        """Return the visible text of an MUI Select field."""
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] .MuiSelect-select",
        )
        el = self.wait_for_element(locator)
        return el.text

    def get_ph_base_value(self) -> str:
        """Return the current pH base value."""
        return self.get_field_value("ph_base")

    def get_ec_base_value(self) -> str:
        """Return the current EC base value."""
        return self.get_field_value("ec_base_ms")

    def get_name_de_value(self) -> str:
        """Return the current Name (DE) value."""
        return self.get_field_value("name_de")

    def get_name_en_value(self) -> str:
        """Return the current Name (EN) value."""
        return self.get_field_value("name_en")

    def get_brand_value(self) -> str:
        """Return the current Brand value."""
        return self.get_field_value("brand")

    def get_type_value(self) -> str:
        """Return the selected substrate type text."""
        return self.get_select_value("type")

    def get_water_retention_value(self) -> str:
        """Return the selected water retention text."""
        return self.get_select_value("water_retention")

    def get_air_porosity_value(self) -> str:
        """Return the current air porosity value."""
        return self.get_field_value("air_porosity_percent")

    def get_buffer_capacity_value(self) -> str:
        """Return the selected buffer capacity text."""
        return self.get_select_value("buffer_capacity")

    def is_reusable_checked(self) -> bool:
        """Return True if the reusable switch is checked."""
        el = self.driver.find_element(
            By.CSS_SELECTOR, "[data-testid='form-field-reusable'] input[type='checkbox']"
        )
        return el.is_selected()

    def get_max_reuse_value(self) -> str:
        """Return the current max reuse cycles value."""
        return self.get_field_value("max_reuse_cycles")

    # ── Edit form interactions ─────────────────────────────────────────

    def fill_ph_base(self, value: float) -> None:
        """Set the pH base field."""
        el = self.wait_for_element_clickable(self.FORM_PH_BASE)
        self.clear_and_fill(el, str(value))

    def fill_ec_base(self, value: float) -> None:
        """Set the EC base field."""
        el = self.wait_for_element_clickable(self.FORM_EC_BASE)
        self.clear_and_fill(el, str(value))

    def fill_name_de(self, value: str) -> None:
        """Set the Name (DE) field."""
        el = self.wait_for_element_clickable(self.FORM_NAME_DE)
        self.clear_and_fill(el, value)

    def fill_name_en(self, value: str) -> None:
        """Set the Name (EN) field."""
        el = self.wait_for_element_clickable(self.FORM_NAME_EN)
        self.clear_and_fill(el, value)

    def fill_brand(self, value: str) -> None:
        """Set the Brand field."""
        el = self.wait_for_element_clickable(self.FORM_BRAND)
        self.clear_and_fill(el, value)

    def fill_air_porosity(self, value: float) -> None:
        """Set the air porosity field."""
        el = self.wait_for_element_clickable(self.FORM_AIR_POROSITY)
        self.clear_and_fill(el, str(value))

    def fill_max_reuse_cycles(self, value: int) -> None:
        """Set the max reuse cycles field."""
        el = self.wait_for_element_clickable(self.FORM_MAX_REUSE)
        self.clear_and_fill(el, str(value))

    def select_type(self, label_text: str) -> None:
        """Select a substrate type by its visible label in the edit form."""
        self._select_option("type", label_text)

    def select_water_retention(self, label_text: str) -> None:
        """Select a water retention value by its visible label."""
        self._select_option("water_retention", label_text)

    def select_buffer_capacity(self, label_text: str) -> None:
        """Select a buffer capacity by its visible label."""
        self._select_option("buffer_capacity", label_text)

    def toggle_reusable(self) -> None:
        """Toggle the reusable switch."""
        el = self.wait_for_element_clickable(self.FORM_REUSABLE)
        self.scroll_and_click(el)

    def submit_form(self) -> None:
        """Submit the edit form."""
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_form(self) -> None:
        """Cancel the edit form (navigates back)."""
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    # ── Delete ─────────────────────────────────────────────────────────

    def click_delete(self) -> None:
        """Click the Delete button and wait for the ConfirmDialog."""
        btn = self.wait_for_element_clickable(self.DELETE_BUTTON)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_delete(self) -> None:
        """Confirm deletion in the ConfirmDialog."""
        self.wait_for_element_clickable(self.CONFIRM_BUTTON).click()

    def cancel_delete(self) -> None:
        """Cancel the delete confirmation dialog."""
        self.wait_for_element_clickable(self.CONFIRM_CANCEL).click()

    def is_confirm_dialog_open(self) -> bool:
        """Return True if the confirm dialog is open."""
        return len(self.driver.find_elements(*self.CONFIRM_DIALOG)) > 0

    # ── Batches ────────────────────────────────────────────────────────

    def get_batch_row_count(self) -> int:
        """Return the number of batch rows."""
        return len(self.driver.find_elements(*self.BATCH_ROWS))

    # ── Error display ──────────────────────────────────────────────────

    def get_alert_messages(self) -> list[str]:
        """Return the text of all visible alert banners."""
        alerts = self.driver.find_elements(*self.ALERTS)
        return [a.text for a in alerts if a.is_displayed()]

    # ── Validation errors ──────────────────────────────────────────────

    def get_validation_error(self, field_name: str) -> str:
        """Return the validation error text for a form field."""
        locator = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] .MuiFormHelperText-root.Mui-error",
        )
        elements = self.driver.find_elements(*locator)
        return elements[0].text if elements else ""

    def has_validation_error(self, field_name: str) -> bool:
        """Return True if a validation error is visible for *field_name*."""
        return bool(self.get_validation_error(field_name))

    # ── Private helpers ────────────────────────────────────────────────

    def _select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select and pick an option by its visible text."""
        field = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_testid}'] .MuiSelect-select")
        )
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()
        self.close_mui_dropdown()
