"""Page object for the Harvest Batch detail page (REQ-007)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class HarvestBatchDetailPage(BasePage):
    """Interact with the Harvest Batch detail page (``/ernte/batches/:key``)."""

    # -- Page-level locators ------------------------------------------------
    PAGE = (By.CSS_SELECTOR, "[data-testid='harvest-batch-detail-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    QUALITY_CHIP_HEADER = (
        By.CSS_SELECTOR,
        "[data-testid='harvest-batch-detail-page'] > div:first-child .MuiChip-root",
    )

    # -- Tab locators -------------------------------------------------------
    TABS = (By.CSS_SELECTOR, "button[role='tab']")

    # -- Error display ------------------------------------------------------
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")

    # -- Tab 0: Details table -----------------------------------------------
    DETAILS_TABLE = (
        By.CSS_SELECTOR,
        "[data-testid='harvest-batch-detail-page'] table",
    )
    DETAILS_ROWS = (
        By.CSS_SELECTOR,
        "[data-testid='harvest-batch-detail-page'] table tr",
    )

    # -- Tab 1: Quality — display table or create form ----------------------
    QUALITY_TABLE = (By.CSS_SELECTOR, "table[aria-label]")
    QUALITY_FORM = (By.CSS_SELECTOR, "form")
    QUALITY_ASSESSED_BY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-assessed_by'] input",
    )
    QUALITY_APPEARANCE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-appearance_score'] input",
    )
    QUALITY_AROMA = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-aroma_score'] input",
    )
    QUALITY_COLOR = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-color_score'] input",
    )
    QUALITY_DEFECTS = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-defects'] input",
    )
    QUALITY_NOTES = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-notes'] textarea",
    )
    QUALITY_LINEAR_PROGRESS = (By.CSS_SELECTOR, ".MuiLinearProgress-root")

    # -- Tab 2: Yield — display table or create form -----------------------
    YIELD_PER_PLANT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-yield_per_plant_g'] input",
    )
    YIELD_PER_M2 = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-yield_per_m2_g'] input",
    )
    YIELD_TOTAL = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-total_yield_g'] input",
    )
    YIELD_USABLE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-usable_yield_g'] input",
    )
    YIELD_TRIM_WASTE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-trim_waste_percent'] input",
    )

    # -- Tab 3: Edit form --------------------------------------------------
    EDIT_HARVEST_TYPE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-harvest_type'] .MuiSelect-select",
    )
    EDIT_QUALITY_GRADE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-quality_grade'] .MuiSelect-select",
    )
    EDIT_HARVESTER = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-harvester'] input",
    )
    EDIT_WET_WEIGHT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-wet_weight_g'] input",
    )
    EDIT_ESTIMATED_DRY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-estimated_dry_weight_g'] input",
    )
    EDIT_ACTUAL_DRY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-actual_dry_weight_g'] input",
    )
    EDIT_NOTES = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-notes'] textarea",
    )

    # -- Shared form buttons ------------------------------------------------
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # -- Snackbar / notification -------------------------------------------
    SNACKBAR = (
        By.CSS_SELECTOR,
        ".MuiSnackbar-root .MuiAlert-message, .notistack-MuiContent",
    )

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, batch_key: str) -> HarvestBatchDetailPage:
        """Navigate to the harvest batch detail page for *batch_key*."""
        self.navigate(f"/ernte/batches/{batch_key}")
        # Wait for either the page or an error display
        WebDriverWait(self.driver, 15).until(
            lambda d: (
                d.find_elements(*self.PAGE)
                or d.find_elements(*self.ERROR_DISPLAY)
            )
        )
        return self

    def open_and_wait(self, batch_key: str) -> HarvestBatchDetailPage:
        """Navigate and wait specifically for the detail page (not error)."""
        self.navigate(f"/ernte/batches/{batch_key}")
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # -- Page info ----------------------------------------------------------

    def get_page_title_text(self) -> str:
        """Return the page title text (batch ID)."""
        el = self.wait_for_element(self.PAGE_TITLE)
        return el.text

    def get_header_quality_chip(self) -> str | None:
        """Return the text of the quality chip in the page header, or None."""
        chips = self.driver.find_elements(*self.QUALITY_CHIP_HEADER)
        return chips[0].text if chips else None

    def is_page_loaded(self) -> bool:
        """Return True if the detail page testid is visible."""
        return len(self.driver.find_elements(*self.PAGE)) > 0

    # -- Tab navigation -----------------------------------------------------

    def get_tab_labels(self) -> list[str]:
        """Return the labels of all visible tabs."""
        tabs = self.driver.find_elements(*self.TABS)
        return [t.text for t in tabs]

    def click_tab(self, index: int) -> None:
        """Click the tab at *index* (0-based)."""
        tabs = self.driver.find_elements(*self.TABS)
        if index < len(tabs):
            self.scroll_and_click(tabs[index])
        else:
            raise ValueError(
                f"Tab index {index} out of range (found {len(tabs)} tabs)"
            )

    def get_active_tab_index(self) -> int:
        """Return the index of the currently selected tab."""
        tabs = self.driver.find_elements(*self.TABS)
        for i, tab in enumerate(tabs):
            if tab.get_attribute("aria-selected") == "true":
                return i
        return -1

    # -- Tab 0: Details -----------------------------------------------------

    def get_detail_table_text(self) -> str:
        """Return the combined text of the details table."""
        table = self.wait_for_element(self.DETAILS_TABLE)
        return table.text

    def get_detail_field_value(self, field_label: str) -> str:
        """Return the value cell text for a given field label in the details table."""
        rows = self.driver.find_elements(*self.DETAILS_ROWS)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            ths = row.find_elements(By.TAG_NAME, "th")
            if ths and field_label in ths[0].text:
                return cells[0].text if cells else ""
        return ""

    # -- Tab 1: Quality -----------------------------------------------------

    def is_quality_form_visible(self) -> bool:
        """Return True if the quality create form is visible."""
        forms = self.driver.find_elements(*self.QUALITY_FORM)
        return len(forms) > 0

    def is_quality_table_visible(self) -> bool:
        """Return True if a quality assessment display table is visible."""
        tables = self.driver.find_elements(*self.QUALITY_TABLE)
        return len(tables) > 0

    def fill_quality_assessed_by(self, name: str) -> None:
        """Fill the 'assessed_by' field."""
        el = self.wait_for_element_clickable(self.QUALITY_ASSESSED_BY)
        el.clear()
        el.send_keys(name)

    def fill_quality_appearance(self, score: int) -> None:
        """Fill the appearance score field."""
        el = self.wait_for_element_clickable(self.QUALITY_APPEARANCE)
        el.clear()
        el.send_keys(str(score))

    def fill_quality_aroma(self, score: int) -> None:
        """Fill the aroma score field."""
        el = self.wait_for_element_clickable(self.QUALITY_AROMA)
        el.clear()
        el.send_keys(str(score))

    def fill_quality_color(self, score: int) -> None:
        """Fill the color score field."""
        el = self.wait_for_element_clickable(self.QUALITY_COLOR)
        el.clear()
        el.send_keys(str(score))

    def add_defect(self, defect: str) -> None:
        """Add a defect chip by typing and pressing Enter."""
        el = self.wait_for_element_clickable(self.QUALITY_DEFECTS)
        el.send_keys(defect)
        el.send_keys(Keys.ENTER)

    def fill_quality_notes(self, notes: str) -> None:
        """Fill the quality notes textarea."""
        el = self.wait_for_element_clickable(self.QUALITY_NOTES)
        el.clear()
        el.send_keys(notes)

    def get_quality_table_text(self) -> str:
        """Return the full text of the quality assessment table."""
        table = self.wait_for_element(self.QUALITY_TABLE)
        return table.text

    def get_overall_score_color(self) -> str:
        """Return the MUI color class of the overall score LinearProgress."""
        progress_bars = self.driver.find_elements(*self.QUALITY_LINEAR_PROGRESS)
        # The overall score is typically the last (or most prominent) progress bar
        for bar in progress_bars:
            classes = bar.get_attribute("class") or ""
            if "colorSuccess" in classes:
                return "success"
            if "colorWarning" in classes:
                return "warning"
            if "colorError" in classes:
                return "error"
        return "unknown"

    def get_defect_chips(self) -> list[str]:
        """Return the text of all defect chips visible on the quality tab."""
        chips = self.driver.find_elements(
            By.CSS_SELECTOR, ".MuiChip-colorError .MuiChip-label"
        )
        return [c.text for c in chips]

    # -- Tab 2: Yield -------------------------------------------------------

    def is_yield_form_visible(self) -> bool:
        """Return True if the yield create form is visible."""
        forms = self.driver.find_elements(*self.QUALITY_FORM)
        return len(forms) > 0

    def is_yield_table_visible(self) -> bool:
        """Return True if a yield metrics display table is visible."""
        tables = self.driver.find_elements(*self.QUALITY_TABLE)
        return len(tables) > 0

    def fill_yield_per_plant(self, value: float) -> None:
        """Fill yield per plant field."""
        el = self.wait_for_element_clickable(self.YIELD_PER_PLANT)
        el.clear()
        el.send_keys(str(value))

    def fill_yield_per_m2(self, value: float) -> None:
        """Fill yield per m2 field."""
        el = self.wait_for_element_clickable(self.YIELD_PER_M2)
        el.clear()
        el.send_keys(str(value))

    def fill_yield_total(self, value: float) -> None:
        """Fill total yield field."""
        el = self.wait_for_element_clickable(self.YIELD_TOTAL)
        el.clear()
        el.send_keys(str(value))

    def fill_yield_usable(self, value: float) -> None:
        """Fill usable yield field."""
        el = self.wait_for_element_clickable(self.YIELD_USABLE)
        el.clear()
        el.send_keys(str(value))

    def fill_yield_trim_waste(self, value: float) -> None:
        """Fill trim waste percent field."""
        el = self.wait_for_element_clickable(self.YIELD_TRIM_WASTE)
        el.clear()
        el.send_keys(str(value))

    def get_yield_table_text(self) -> str:
        """Return the full text of the yield metrics table."""
        table = self.wait_for_element(self.QUALITY_TABLE)
        return table.text

    # -- Tab 3: Edit --------------------------------------------------------

    def get_edit_harvester_value(self) -> str:
        """Return the current value of the harvester field in the edit form."""
        el = self.wait_for_element(self.EDIT_HARVESTER)
        return el.get_attribute("value") or ""

    def fill_edit_harvester(self, name: str) -> None:
        """Set the harvester field in the edit form."""
        el = self.wait_for_element_clickable(self.EDIT_HARVESTER)
        el.clear()
        el.send_keys(name)

    def fill_edit_wet_weight(self, weight: float) -> None:
        """Set the wet weight field in the edit form."""
        el = self.wait_for_element_clickable(self.EDIT_WET_WEIGHT)
        el.clear()
        el.send_keys(str(weight))

    def fill_edit_estimated_dry(self, weight: float) -> None:
        """Set the estimated dry weight field."""
        el = self.wait_for_element_clickable(self.EDIT_ESTIMATED_DRY)
        el.clear()
        el.send_keys(str(weight))

    def fill_edit_actual_dry(self, weight: float) -> None:
        """Set the actual dry weight field."""
        el = self.wait_for_element_clickable(self.EDIT_ACTUAL_DRY)
        el.clear()
        el.send_keys(str(weight))

    def fill_edit_notes(self, notes: str) -> None:
        """Fill the notes textarea in the edit tab."""
        el = self.wait_for_element_clickable(self.EDIT_NOTES)
        el.clear()
        el.send_keys(notes)

    def select_edit_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select in the edit form and pick an option."""
        field = self.wait_for_element_clickable(
            (
                By.CSS_SELECTOR,
                f"[data-testid='form-field-{field_testid}'] .MuiSelect-select",
            )
        )
        self.scroll_and_click(field)
        option = self.wait_for_element_clickable(
            (
                By.XPATH,
                f"//li[@role='option' and contains(text(), '{value_text}')]",
            )
        )
        option.click()

    def is_submit_disabled(self) -> bool:
        """Return True if the submit/save button is disabled."""
        btn = self.wait_for_element(self.FORM_SUBMIT)
        return not btn.is_enabled()

    # -- Shared form actions ------------------------------------------------

    def submit_form(self) -> None:
        """Click the submit button."""
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_form(self) -> None:
        """Click the cancel button."""
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    # -- Validation errors --------------------------------------------------

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

    # -- Error display ------------------------------------------------------

    def is_error_displayed(self) -> bool:
        """Return True if an error display component is visible."""
        elements = self.driver.find_elements(*self.ERROR_DISPLAY)
        return len(elements) > 0 and elements[0].is_displayed()

    # -- Snackbar -----------------------------------------------------------

    def is_snackbar_visible(self) -> bool:
        """Return True if a success snackbar is visible."""
        els = self.driver.find_elements(*self.SNACKBAR)
        return any(el.is_displayed() for el in els) if els else False
