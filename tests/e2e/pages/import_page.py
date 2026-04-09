"""Page object for the Stammdaten-Import page (REQ-012).

Three-step stepper: Upload (step 0) -> Preview (step 1) -> Result (step 2).
"""

from __future__ import annotations

import os
import tempfile

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage, DEFAULT_TIMEOUT


class ImportPage(BasePage):
    """Interact with the Stammdaten-Import page (``/stammdaten/import``)."""

    PATH = "/stammdaten/import"

    # ── Step containers ─────────────────────────────────────────────────
    STEP_UPLOAD = (By.CSS_SELECTOR, "[data-testid='import-step-upload']")
    STEP_PREVIEW = (By.CSS_SELECTOR, "[data-testid='import-step-preview']")
    STEP_RESULT = (By.CSS_SELECTOR, "[data-testid='import-step-result']")

    # ── Stepper ─────────────────────────────────────────────────────────
    STEPPER = (By.CSS_SELECTOR, ".MuiStepper-root")
    STEPPER_STEPS = (By.CSS_SELECTOR, ".MuiStep-root")
    ACTIVE_STEP_ICON = (By.CSS_SELECTOR, ".MuiStepIcon-root.Mui-active")

    # ── Upload step (step 0) ────────────────────────────────────────────
    ENTITY_TYPE_SELECT = (By.CSS_SELECTOR, "[data-testid='import-entity-type']")
    DUPLICATE_STRATEGY_SELECT = (By.CSS_SELECTOR, "[data-testid='import-duplicate-strategy']")
    FILE_SELECT_BUTTON = (By.CSS_SELECTOR, "[data-testid='import-file-select']")
    FILE_INPUT = (By.CSS_SELECTOR, "[data-testid='import-file-select'] input[type='file']")
    DOWNLOAD_TEMPLATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='import-download-template']")
    UPLOAD_BUTTON = (By.CSS_SELECTOR, "[data-testid='import-upload-button']")
    ERROR_ALERT = (By.CSS_SELECTOR, "[data-testid='import-error']")

    # ── Preview step (step 1) ──────────────────────────────────────────
    PREVIEW_TABLE = (By.CSS_SELECTOR, "[data-testid='import-step-preview'] table")
    PREVIEW_ROWS = (By.CSS_SELECTOR, "[data-testid='import-step-preview'] table tbody tr")
    BACK_BUTTON = (By.CSS_SELECTOR, "[data-testid='import-back-button']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='import-confirm-button']")

    # ── Result step (step 2) ───────────────────────────────────────────
    NEW_IMPORT_BUTTON = (By.CSS_SELECTOR, "[data-testid='import-new-button']")
    RESULT_CHIPS = (By.CSS_SELECTOR, "[data-testid='import-step-result'] .MuiChip-root")
    RESULT_WARNING = (By.CSS_SELECTOR, "[data-testid='import-step-result'] .MuiAlert-standardWarning")

    # ── Generic chip locators ──────────────────────────────────────────
    STATUS_CHIP_VALID = (By.CSS_SELECTOR, ".MuiChip-colorSuccess")
    STATUS_CHIP_INVALID = (By.CSS_SELECTOR, ".MuiChip-colorError")
    STATUS_CHIP_DUPLICATE = (By.CSS_SELECTOR, ".MuiChip-colorWarning")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self) -> ImportPage:
        """Navigate to the import page and wait for the upload step."""
        self.navigate(self.PATH)
        self.wait_for_element(self.STEPPER)
        return self

    # ── Stepper queries ─────────────────────────────────────────────────

    def get_step_labels(self) -> list[str]:
        """Return the text labels of all stepper steps."""
        steps = self.driver.find_elements(*self.STEPPER_STEPS)
        return [s.text.strip() for s in steps if s.text.strip()]

    def get_active_step_index(self) -> int:
        """Return the 0-based index of the currently active step."""
        steps = self.driver.find_elements(*self.STEPPER_STEPS)
        for i, step in enumerate(steps):
            icons = step.find_elements(By.CSS_SELECTOR, ".MuiStepIcon-root.Mui-active")
            if icons:
                return i
        return -1

    def is_step_upload_visible(self) -> bool:
        """Return True if the upload step container is displayed."""
        elements = self.driver.find_elements(*self.STEP_UPLOAD)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_step_preview_visible(self) -> bool:
        """Return True if the preview step container is displayed."""
        elements = self.driver.find_elements(*self.STEP_PREVIEW)
        return len(elements) > 0 and elements[0].is_displayed()

    def is_step_result_visible(self) -> bool:
        """Return True if the result step container is displayed."""
        elements = self.driver.find_elements(*self.STEP_RESULT)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Page title ──────────────────────────────────────────────────────

    def get_title_text(self) -> str:
        """Return the import page heading text."""
        heading = self.wait_for_element((By.CSS_SELECTOR, "h1, h4"))
        return heading.text

    # ── Entity type dropdown ────────────────────────────────────────────

    def get_entity_type_value(self) -> str:
        """Return the currently selected entity type value (internal).

        MUI v7 Select renders the value in a ``MuiSelect-nativeInput`` text input
        (previously ``input[type='hidden']`` in MUI v5/v6).
        """
        self.wait_for_element(self.ENTITY_TYPE_SELECT)
        native = self.driver.find_element(
            By.CSS_SELECTOR, "[data-testid='import-entity-type'] input.MuiSelect-nativeInput"
        )
        return native.get_attribute("value") or ""

    def select_entity_type(self, value_text: str) -> None:
        """Open the entity type dropdown and select an option by visible text."""
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(self.ENTITY_TYPE_SELECT)
        self.scroll_and_click(select_el)
        option = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
            )
        )
        option.click()
        # Wait for dropdown to close and dismiss any lingering backdrop
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

    def get_entity_type_options(self) -> list[str]:
        """Open the entity type dropdown and return all option texts."""
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(self.ENTITY_TYPE_SELECT)
        self.scroll_and_click(select_el)
        options = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[role='option']"))
        )
        texts = [o.text for o in options]
        # Close dropdown by pressing Escape
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.5)  # Wait for backdrop to fully dismiss
        return texts

    # ── Duplicate strategy dropdown ─────────────────────────────────────

    def get_duplicate_strategy_value(self) -> str:
        """Return the currently selected duplicate strategy value.

        MUI v7 Select renders the value in a ``MuiSelect-nativeInput`` text input.
        """
        native = self.driver.find_element(
            By.CSS_SELECTOR, "[data-testid='import-duplicate-strategy'] input.MuiSelect-nativeInput"
        )
        return native.get_attribute("value") or ""

    def select_duplicate_strategy(self, value_text: str) -> None:
        """Open the duplicate strategy dropdown and select an option."""
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(self.DUPLICATE_STRATEGY_SELECT)
        self.scroll_and_click(select_el)
        option = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//li[@role='option' and contains(text(), '{value_text}')]")
            )
        )
        option.click()
        # Wait for dropdown to close and dismiss any lingering backdrop
        time.sleep(0.3)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.3)

    def get_duplicate_strategy_options(self) -> list[str]:
        """Open the duplicate strategy dropdown and return all option texts."""
        import time
        from selenium.webdriver.common.keys import Keys

        select_el = self.wait_for_element_clickable(self.DUPLICATE_STRATEGY_SELECT)
        self.scroll_and_click(select_el)
        options = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[role='option']"))
        )
        texts = [o.text for o in options]
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.5)  # Wait for backdrop to fully dismiss
        return texts

    # ── File selection ──────────────────────────────────────────────────

    def select_file(self, file_path: str) -> None:
        """Send a file path to the hidden file input element.

        The MUI ``<input hidden>`` renders as ``display: none``, which some
        Selenium/WebDriver combinations reject for ``send_keys``.  We
        temporarily make the input visible via JavaScript before interacting.
        """
        file_input = self.driver.find_element(*self.FILE_INPUT)
        # Make the hidden input visible so Selenium can interact with it
        self.driver.execute_script(
            "arguments[0].style.display = 'block';"
            "arguments[0].style.visibility = 'visible';"
            "arguments[0].style.height = '1px';"
            "arguments[0].style.width = '1px';"
            "arguments[0].style.opacity = '0.01';",
            file_input,
        )
        file_input.send_keys(file_path)

    def get_file_button_text(self) -> str:
        """Return the text displayed on the file-select button."""
        el = self.wait_for_element(self.FILE_SELECT_BUTTON)
        return el.text

    # ── Upload button ───────────────────────────────────────────────────

    def is_upload_button_enabled(self) -> bool:
        """Return True if the upload button is enabled (not disabled)."""
        el = self.wait_for_element(self.UPLOAD_BUTTON)
        return el.is_enabled()

    def click_upload(self) -> None:
        """Click the upload button and wait for the preview step to appear."""
        btn = self.wait_for_element_clickable(self.UPLOAD_BUTTON)
        self.scroll_and_click(btn)

    def click_upload_and_wait_preview(self, timeout: int = 30) -> None:
        """Click upload and wait until the preview step container appears."""
        import time

        btn = self.wait_for_element_clickable(self.UPLOAD_BUTTON)
        self.scroll_and_click(btn)
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(self.STEP_PREVIEW)
        )
        # Wait for preview content to render (table rows)
        time.sleep(0.5)

    def click_upload_and_wait_error(self, timeout: int = 30) -> None:
        """Click upload and wait until the error alert or snackbar appears."""
        btn = self.wait_for_element_clickable(self.UPLOAD_BUTTON)
        self.scroll_and_click(btn)
        # Wait for either in-page error alert or a snackbar error
        WebDriverWait(self.driver, timeout).until(
            lambda d: (
                len(d.find_elements(*self.ERROR_ALERT)) > 0
                or len(d.find_elements(By.CSS_SELECTOR, ".MuiSnackbar-root")) > 0
            )
        )

    # ── Download template ───────────────────────────────────────────────

    def is_download_template_visible(self) -> bool:
        """Return True if the download template button is visible."""
        elements = self.driver.find_elements(*self.DOWNLOAD_TEMPLATE_BUTTON)
        return len(elements) > 0 and elements[0].is_displayed()

    def click_download_template(self) -> None:
        """Click the download template button."""
        self.wait_for_element_clickable(self.DOWNLOAD_TEMPLATE_BUTTON).click()

    # ── Error alert ─────────────────────────────────────────────────────

    def is_error_alert_visible(self) -> bool:
        """Return True if the import error alert or a snackbar error is displayed."""
        elements = self.driver.find_elements(*self.ERROR_ALERT)
        if len(elements) > 0 and elements[0].is_displayed():
            return True
        # Fallback: check for snackbar error
        snackbars = self.driver.find_elements(By.CSS_SELECTOR, ".MuiSnackbar-root")
        return any(s.is_displayed() for s in snackbars)

    def get_error_alert_text(self) -> str:
        """Return the text of the error alert or snackbar error."""
        elements = self.driver.find_elements(*self.ERROR_ALERT)
        if elements and elements[0].is_displayed():
            return elements[0].text
        # Fallback: snackbar text
        snackbars = self.driver.find_elements(By.CSS_SELECTOR, ".MuiSnackbar-root")
        for s in snackbars:
            if s.is_displayed() and s.text:
                return s.text
        return ""

    # ── Preview table ───────────────────────────────────────────────────

    def get_preview_row_count(self) -> int:
        """Return the number of rows in the preview table."""
        rows = self.driver.find_elements(*self.PREVIEW_ROWS)
        return len(rows)

    def get_preview_file_info(self) -> str:
        """Return the file info text shown above the preview table (filename + row count)."""
        # Try multiple typography variants that might contain file info
        for variant in ("subtitle1", "subtitle2", "body1", "body2", "h6"):
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, f"[data-testid='import-step-preview'] .MuiTypography-{variant}"
            )
            for el in elements:
                if el.is_displayed() and el.text:
                    return el.text
        # Fallback: any text in the preview step
        step = self.driver.find_element(*self.STEP_PREVIEW)
        return step.text

    def get_preview_row_statuses(self) -> list[str]:
        """Return the status chip text for each preview row."""
        rows = self.driver.find_elements(*self.PREVIEW_ROWS)
        statuses = []
        for row in rows:
            chips = row.find_elements(By.CSS_SELECTOR, ".MuiChip-root")
            if chips:
                # First chip in the Status column
                statuses.append(chips[0].text.lower())
            else:
                statuses.append("")
        return statuses

    def get_preview_row_error_chips(self) -> list[str]:
        """Return the error chip text for each row (empty string if no errors)."""
        rows = self.driver.find_elements(*self.PREVIEW_ROWS)
        error_texts = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:
                # Errors column is the 4th cell
                error_cell = cells[3]
                chips = error_cell.find_elements(By.CSS_SELECTOR, ".MuiChip-root")
                error_texts.append(chips[0].text if chips else "")
            else:
                error_texts.append("")
        return error_texts

    def count_valid_rows(self) -> int:
        """Count preview rows with 'valid' status chip (green)."""
        rows = self.driver.find_elements(*self.PREVIEW_ROWS)
        count = 0
        for row in rows:
            chips = row.find_elements(By.CSS_SELECTOR, ".MuiChip-colorSuccess")
            if chips:
                count += 1
        return count

    def count_invalid_rows(self) -> int:
        """Count preview rows with 'invalid' status chip (red)."""
        rows = self.driver.find_elements(*self.PREVIEW_ROWS)
        count = 0
        for row in rows:
            chips = row.find_elements(By.CSS_SELECTOR, ".MuiChip-colorError")
            if chips:
                count += 1
        return count

    def count_duplicate_rows(self) -> int:
        """Count preview rows with 'duplicate' status chip (yellow)."""
        rows = self.driver.find_elements(*self.PREVIEW_ROWS)
        count = 0
        for row in rows:
            chips = row.find_elements(By.CSS_SELECTOR, ".MuiChip-colorWarning")
            if chips:
                count += 1
        return count

    # ── Preview actions ─────────────────────────────────────────────────

    def click_back(self) -> None:
        """Click the back button to return to step 1."""
        btn = self.wait_for_element_clickable(self.BACK_BUTTON)
        self.scroll_and_click(btn)
        WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located(self.STEP_UPLOAD)
        )

    def is_confirm_button_enabled(self) -> bool:
        """Return True if the confirm import button is enabled."""
        el = self.wait_for_element(self.CONFIRM_BUTTON)
        return el.is_enabled()

    def click_confirm(self) -> None:
        """Click the confirm import button."""
        btn = self.wait_for_element_clickable(self.CONFIRM_BUTTON)
        self.scroll_and_click(btn)

    def click_confirm_and_wait_result(self, timeout: int = 30) -> None:
        """Click confirm and wait for the result step to appear."""
        import time

        btn = self.wait_for_element_clickable(self.CONFIRM_BUTTON)
        self.scroll_and_click(btn)
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(self.STEP_RESULT)
        )
        time.sleep(0.5)  # Wait for result content to render

    # ── Result step ─────────────────────────────────────────────────────

    def get_result_chip_texts(self) -> list[str]:
        """Return all chip texts on the result page."""
        chips = self.driver.find_elements(*self.RESULT_CHIPS)
        return [c.text for c in chips]

    def get_result_chip_by_label(self, label_fragment: str) -> str | None:
        """Find a result chip whose text contains *label_fragment* and return its text."""
        chips = self.driver.find_elements(*self.RESULT_CHIPS)
        for c in chips:
            if label_fragment.lower() in c.text.lower():
                return c.text
        return None

    def is_result_warning_visible(self) -> bool:
        """Return True if a warning alert is shown on the result page."""
        elements = self.driver.find_elements(*self.RESULT_WARNING)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_result_warning_text(self) -> str:
        """Return the warning alert text on the result page."""
        el = self.wait_for_element(self.RESULT_WARNING)
        return el.text

    def click_new_import(self) -> None:
        """Click 'New Import' button and wait for upload step."""
        btn = self.wait_for_element_clickable(self.NEW_IMPORT_BUTTON)
        self.scroll_and_click(btn)
        WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located(self.STEP_UPLOAD)
        )

    # ── CSV test data helpers ───────────────────────────────────────────

    @staticmethod
    def create_test_csv(
        filename: str,
        header: str,
        rows: list[str],
        encoding: str = "utf-8",
        delimiter: str = ",",
        bom: bool = False,
    ) -> str:
        """Create a temporary CSV file and return its absolute path.

        The file is placed in a temp directory and will persist until the OS
        cleans up the temp folder (or the caller deletes it).
        """
        # Use $HOME/.cache if writable (snap-confined Chromium), else /tmp
        home_cache = os.path.join(os.path.expanduser("~"), ".cache", "kp_e2e_import")
        try:
            os.makedirs(home_cache, exist_ok=True)
            base = home_cache
        except OSError:
            base = tempfile.gettempdir()
        tmpdir = tempfile.mkdtemp(prefix="csv_", dir=base)
        filepath = os.path.join(tmpdir, filename)
        content = delimiter.join(header.split(",")) + "\n"
        for row in rows:
            content += delimiter.join(row.split(",")) + "\n"
        with open(filepath, "w", encoding=encoding, newline="") as f:
            if bom:
                f.write("\ufeff")
            f.write(content)
        return filepath

    @staticmethod
    def create_empty_csv(filename: str = "empty.csv") -> str:
        """Create an empty CSV file and return its path."""
        home_cache = os.path.join(os.path.expanduser("~"), ".cache", "kp_e2e_import")
        try:
            os.makedirs(home_cache, exist_ok=True)
            base = home_cache
        except OSError:
            base = tempfile.gettempdir()
        tmpdir = tempfile.mkdtemp(prefix="csv_", dir=base)
        filepath = os.path.join(tmpdir, filename)
        with open(filepath, "w"):
            pass  # empty file
        return filepath

    @staticmethod
    def create_large_csv(filename: str = "large.csv", size_mb: int = 11) -> str:
        """Create a CSV file exceeding *size_mb* megabytes."""
        home_cache = os.path.join(os.path.expanduser("~"), ".cache", "kp_e2e_import")
        try:
            os.makedirs(home_cache, exist_ok=True)
            base = home_cache
        except OSError:
            base = tempfile.gettempdir()
        tmpdir = tempfile.mkdtemp(prefix="csv_", dir=base)
        filepath = os.path.join(tmpdir, filename)
        header = "scientific_name,common_names,family,genus\n"
        row = "Solanum lycopersicum,Tomate,Solanaceae,Solanum\n"
        target_bytes = size_mb * 1024 * 1024
        with open(filepath, "w") as f:
            f.write(header)
            written = len(header)
            while written < target_bytes:
                f.write(row)
                written += len(row)
        return filepath
