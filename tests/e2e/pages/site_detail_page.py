"""Page object for the Site detail page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class SiteDetailPage(BasePage):
    """Interact with a Site detail page (``/standorte/sites/:key``).

    Covers REQ-002: Site editing, Location sub-section, Delete flow.
    """

    PATH_PREFIX = "/standorte/sites"

    # ── Page markers ───────────────────────────────────────────────────
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")

    # ── Edit form ─────────────────────────────────────────────────────
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_TYPE = (By.CSS_SELECTOR, "[data-testid='form-field-type']")
    FORM_CLIMATE_ZONE = (By.CSS_SELECTOR, "[data-testid='form-field-climate_zone'] input")
    FORM_TOTAL_AREA = (By.CSS_SELECTOR, "[data-testid='form-field-total_area_m2'] input")
    FORM_TIMEZONE = (By.CSS_SELECTOR, "[data-testid='form-field-timezone'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # ── Delete flow ────────────────────────────────────────────────────
    # The delete button does not have data-testid — select by icon/color pattern
    DELETE_BUTTON = (By.XPATH, "//button[contains(@class, 'MuiButton') and .//svg[contains(@class, 'MuiSvgIcon')]][@color='error' or contains(., 'Löschen') or contains(., 'Delete')]")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_OK = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Location sub-section ──────────────────────────────────────────
    # LocationTreeSection uses MUI SimpleTreeView (TreeItem), not a DataTable.
    LOCATION_TREE_SECTION = (By.CSS_SELECTOR, "[data-testid='add-location-button']")
    LOCATION_TREE_ITEMS = (By.CSS_SELECTOR, "[role='treeitem']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> SiteDetailPage:
        self.navigate(f"{self.PATH_PREFIX}/{key}")
        self.wait_for_element(self.PAGE_TITLE)
        self._wait_for_skeleton_gone()
        return self

    # ── Private helpers ────────────────────────────────────────────────

    def _wait_for_skeleton_gone(self, timeout: int = 15) -> None:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.LOADING_SKELETON)
        )

    # ── Page state ─────────────────────────────────────────────────────

    def get_title(self) -> str:
        return self.wait_for_element_visible(self.PAGE_TITLE).text

    def is_error_shown(self) -> bool:
        elements = self.driver.find_elements(*self.ERROR_DISPLAY)
        if bool(elements) and elements[0].is_displayed():
            return True
        # Also check for the dedicated error page (SPA 404 redirect)
        error_page = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='error-page']")
        if bool(error_page) and error_page[0].is_displayed():
            return True
        # Also check for router error page
        router_error = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='router-error-page']")
        return bool(router_error) and router_error[0].is_displayed()

    # ── Form interactions ──────────────────────────────────────────────

    def get_name_value(self) -> str:
        el = self.wait_for_element(self.FORM_NAME)
        return el.get_attribute("value") or ""

    def set_name(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_NAME)
        self.clear_and_fill(el, value)

    def set_climate_zone(self, value: str) -> None:
        el = self.wait_for_element_clickable(self.FORM_CLIMATE_ZONE)
        el.clear()
        el.send_keys(value)

    def select_type(self, value_text: str) -> None:
        """Open the MUI Select for 'type' and pick an option by visible text."""
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-type'] .MuiSelect-select")
        )
        self.scroll_and_click(select_el)
        option = self.wait_for_element_clickable(
            (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
        )
        option.click()
        # Dismiss MUI Select backdrop/popover
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

    def submit_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_SUBMIT).click()

    def cancel_form(self) -> None:
        self.wait_for_element_clickable(self.FORM_CANCEL).click()

    # ── Delete flow ────────────────────────────────────────────────────

    def click_delete(self) -> None:
        """Click the destructive delete button (MUI error-colored Button)."""
        btn = self.wait_for_element_clickable(
            (By.XPATH, "//button[.//text()='Löschen' or .//text()='Delete']")
        )
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_delete(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_OK).click()

    def cancel_delete(self) -> None:
        self.wait_for_element_clickable(self.CONFIRM_CANCEL).click()
        self.wait_for_element_hidden(self.CONFIRM_DIALOG)

    def is_confirm_dialog_visible(self) -> bool:
        elements = self.driver.find_elements(*self.CONFIRM_DIALOG)
        return bool(elements) and elements[0].is_displayed()

    # ── Location sub-section (MUI SimpleTreeView) ──────────────────────

    def wait_for_location_tree_loaded(self, timeout: int = 10) -> None:
        """Wait until the LocationTreeSection finishes its async load.

        The section shows its own LoadingSkeleton while fetching tree data.
        Wait until either tree items appear OR the empty-state is rendered.
        """
        from selenium.webdriver.support.ui import WebDriverWait

        def _tree_or_empty(driver: WebDriver) -> bool:
            items = driver.find_elements(*self.LOCATION_TREE_ITEMS)
            empty = driver.find_elements(By.CSS_SELECTOR, "[data-testid='empty-state']")
            # Also accept when no skeleton is present (loading finished)
            skeletons = driver.find_elements(*self.LOADING_SKELETON)
            skeleton_visible = any(s.is_displayed() for s in skeletons)
            return bool(items) or bool(empty) or not skeleton_visible

        WebDriverWait(self.driver, timeout).until(_tree_or_empty)

    def get_location_row_count(self) -> int:
        """Count location tree items (TreeItem with role='treeitem')."""
        self.wait_for_location_tree_loaded()
        items = self.driver.find_elements(*self.LOCATION_TREE_ITEMS)
        return len(items)

    def click_location_row(self, index: int) -> None:
        """Click the name-link inside a tree item to navigate to location detail.

        The LocationTreeSection renders each node name as a Typography with
        an onClick handler that navigates to ``/standorte/locations/{key}``.
        """
        items = self.driver.find_elements(*self.LOCATION_TREE_ITEMS)
        if index < len(items):
            # The clickable name is a Typography inside the TreeItem label
            name_el = items[index].find_element(
                By.CSS_SELECTOR, ".MuiTypography-body2"
            )
            self.scroll_and_click(name_el)

    def is_location_section_visible(self) -> bool:
        """Check if the LocationTreeSection is rendered (create button present)."""
        elements = self.driver.find_elements(*self.LOCATION_TREE_SECTION)
        return bool(elements) and elements[0].is_displayed()
