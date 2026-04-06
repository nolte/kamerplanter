"""Page object for the Harvest Batch list page (REQ-007)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage


class HarvestBatchListPage(BasePage):
    """Interact with the Harvest Batch list page (``/ernte/batches``)."""

    PATH = "/ernte/batches"

    # -- Page-level locators ------------------------------------------------
    PAGE = (By.CSS_SELECTOR, "[data-testid='harvest-batch-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")
    SORT_CHIP = (By.CSS_SELECTOR, "[data-testid='sort-chip']")
    RESET_FILTERS = (By.CSS_SELECTOR, "[data-testid='reset-filters-button']")
    SHOWING_COUNT = (By.CSS_SELECTOR, "[data-testid='showing-count']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")

    # -- Create dialog locators ---------------------------------------------
    CREATE_DIALOG = (By.CSS_SELECTOR, "div[role='dialog']")

    # -- Create form field locators -----------------------------------------
    FORM_PLANT_KEY = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-plant_key'] .MuiSelect-select",
    )
    FORM_BATCH_ID = (By.CSS_SELECTOR, "[data-testid='form-field-batch_id'] input")
    FORM_HARVEST_TYPE = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-harvest_type'] .MuiSelect-select",
    )
    FORM_WET_WEIGHT = (
        By.CSS_SELECTOR,
        "[data-testid='form-field-wet_weight_g'] input",
    )
    FORM_HARVESTER = (By.CSS_SELECTOR, "[data-testid='form-field-harvester'] input")
    FORM_NOTES = (By.CSS_SELECTOR, "[data-testid='form-field-notes'] textarea")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # -- Snackbar / notification -------------------------------------------
    SNACKBAR = (By.CSS_SELECTOR, ".MuiSnackbar-root .MuiAlert-message, .notistack-MuiContent")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> HarvestBatchListPage:
        """Navigate to the harvest batch list and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # -- Page info ----------------------------------------------------------

    def get_page_title_text(self) -> str:
        """Return the page title text."""
        el = self.wait_for_element(self.PAGE_TITLE)
        return el.text

    def get_intro_text(self) -> str:
        """Return the introductory text below the title."""
        el = self.driver.find_element(
            By.CSS_SELECTOR,
            "[data-testid='harvest-batch-list-page'] .MuiTypography-body2",
        )
        return el.text

    # -- Table interactions -------------------------------------------------

    def get_row_count(self) -> int:
        """Return the number of visible table rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_column_headers(self) -> list[str]:
        """Return all visible column header texts."""
        headers = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table'] th"
        )
        return [h.text for h in headers if h.text]

    def get_row_texts(self) -> list[list[str]]:
        """Return all cell texts for every visible row."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            result.append([c.text for c in cells])
        return result

    def get_first_column_texts(self) -> list[str]:
        """Return the text of the first column for all rows."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        texts = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                texts.append(cells[0].text)
        return texts

    def click_row(self, index: int = 0) -> None:
        """Click the row at *index*."""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if index < len(rows):
            self.scroll_and_click(rows[index])

    def click_column_header(self, header_text: str) -> None:
        """Click a column header by its text to trigger sorting."""
        headers = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table'] th"
        )
        for h in headers:
            if h.text == header_text:
                self.scroll_and_click(h)
                return
        raise ValueError(f"Column header '{header_text}' not found")

    # -- Search and filter --------------------------------------------------

    def search(self, term: str) -> None:
        """Type *term* into the search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(term)

    def clear_search(self) -> None:
        """Clear the search field."""
        search_input = self.wait_for_element_clickable(self.SEARCH_INPUT)
        search_input.clear()
        search_input.send_keys(Keys.BACKSPACE)

    def has_search_chip(self) -> bool:
        """Return True if a search chip is visible."""
        return len(self.driver.find_elements(*self.SEARCH_CHIP)) > 0

    def has_sort_chip(self) -> bool:
        """Return True if a sort chip is visible."""
        return len(self.driver.find_elements(*self.SORT_CHIP)) > 0

    def click_reset_filters(self) -> None:
        """Click the reset filters button."""
        self.wait_for_element_clickable(self.RESET_FILTERS).click()

    def has_reset_filters_button(self) -> bool:
        """Return True if the reset filters button is visible."""
        return len(self.driver.find_elements(*self.RESET_FILTERS)) > 0

    def get_showing_count_text(self) -> str:
        """Return the text of the showing count element."""
        el = self.wait_for_element(self.SHOWING_COUNT)
        return el.text

    def has_empty_state(self) -> bool:
        """Return True if the empty state is visible."""
        return len(self.driver.find_elements(*self.EMPTY_STATE)) > 0

    # -- Quality grade chips ------------------------------------------------

    def get_quality_chips(self) -> list[dict[str, str]]:
        """Return label and MUI color class for quality-grade chips in the table.

        Each entry is ``{"label": "A+", "classes": "MuiChip-colorSuccess ..."}``.
        """
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        chips = []
        for row in rows:
            # Quality grade is in the last column
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                continue
            last_cell = cells[-1]
            chip_els = last_cell.find_elements(By.CSS_SELECTOR, ".MuiChip-root")
            if chip_els:
                chip = chip_els[0]
                chips.append({
                    "label": chip.text,
                    "classes": chip.get_attribute("class") or "",
                })
            else:
                chips.append({"label": last_cell.text, "classes": ""})
        return chips

    # -- Create dialog ------------------------------------------------------

    def click_create(self) -> None:
        """Click the Create button and wait for the dialog."""
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Return True if the create dialog is open."""
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def select_plant(self, label_text: str) -> None:
        """Select a plant from the plant_key dropdown."""
        self.select_option("plant_key", label_text)

    def fill_batch_id(self, batch_id: str) -> None:
        """Fill the batch_id field."""
        el = self.wait_for_element_clickable(self.FORM_BATCH_ID)
        el.clear()
        el.send_keys(batch_id)

    def select_harvest_type(self, label_text: str) -> None:
        """Select a harvest type from the dropdown."""
        self.select_option("harvest_type", label_text)

    def fill_wet_weight(self, weight: float) -> None:
        """Fill the wet_weight_g field."""
        el = self.wait_for_element_clickable(self.FORM_WET_WEIGHT)
        el.clear()
        el.send_keys(str(weight))

    def fill_harvester(self, name: str) -> None:
        """Fill the harvester field."""
        el = self.wait_for_element_clickable(self.FORM_HARVESTER)
        el.clear()
        el.send_keys(name)

    def fill_notes(self, notes: str) -> None:
        """Fill the notes textarea."""
        el = self.wait_for_element_clickable(self.FORM_NOTES)
        el.clear()
        el.send_keys(notes)

    def submit_create_form(self) -> None:
        """Click the submit button inside the create dialog.

        Previous implementation dispatched a raw DOM submit event which
        does not reliably trigger React Hook Form's ``handleSubmit``.
        """
        btn = self.wait_for_element_clickable(self.FORM_SUBMIT)
        self.scroll_and_click(btn)

    def cancel_create_form(self) -> None:
        """Cancel the create dialog."""
        btn = self.wait_for_element(self.FORM_CANCEL)
        self.scroll_and_click(btn)

    def select_option(self, field_testid: str, value_text: str) -> None:
        """Open an MUI Select and pick an option by its visible text."""
        import time

        field = self.wait_for_element_clickable(
            (
                By.CSS_SELECTOR,
                f"[data-testid='form-field-{field_testid}'] .MuiSelect-select",
            )
        )
        self.scroll_and_click(field)
        # If value_text is empty, pick the first available option
        if not value_text:
            option = self.wait_for_element_clickable(
                (By.CSS_SELECTOR, "li[role='option']")
            )
        else:
            option = self.wait_for_element_clickable(
                (
                    By.XPATH,
                    f"//li[@role='option' and contains(text(), '{value_text}')]",
                )
            )
        option.click()
        # Dismiss MUI Select backdrop/popover to unblock subsequent interactions
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

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

    def is_snackbar_visible(self) -> bool:
        """Return True if a success snackbar is visible."""
        els = self.driver.find_elements(*self.SNACKBAR)
        return any(el.is_displayed() for el in els) if els else False

    def is_page_visible(self) -> bool:
        """Check whether the harvest list page container is displayed."""
        els = self.driver.find_elements(*self.PAGE)
        return len(els) > 0 and els[0].is_displayed()

    def is_create_button_visible(self) -> bool:
        """Check whether the create button is displayed."""
        els = self.driver.find_elements(*self.CREATE_BUTTON)
        return len(els) > 0 and els[0].is_displayed()

    def has_any_dialog_error(self) -> bool:
        """Check for any MUI error helper text inside the dialog."""
        from selenium.webdriver.common.by import By

        return len(self.driver.find_elements(
            By.CSS_SELECTOR,
            "div[role='dialog'] .MuiFormHelperText-root.Mui-error",
        )) > 0

    def wait_for_dialog_closed(self, timeout: int = 10) -> None:
        """Wait until the create dialog is no longer visible."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.CREATE_DIALOG)
        )
