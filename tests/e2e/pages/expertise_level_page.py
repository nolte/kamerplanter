"""Page object for REQ-021 Experience Level (UI-Erfahrungsstufen) interactions."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import DEFAULT_TIMEOUT, BasePage


class ExpertiseLevelPage(BasePage):
    """Interact with experience-level UI across AccountSettings, Sidebar, and dialogs.

    Covers:
    - ExperienceLevelSwitcher (AccountSettingsPage, tab ``experience``)
    - Navigation tiering in the Sidebar
    - ShowAllFieldsToggle in create dialogs
    - ExpertiseFieldWrapper field visibility
    """

    ACCOUNT_SETTINGS_PATH = "/settings"

    # ── Experience toggle buttons (AccountSettingsPage) ──────────────
    TOGGLE_BEGINNER = (By.CSS_SELECTOR, "[data-testid='experience-toggle-beginner']")
    TOGGLE_INTERMEDIATE = (By.CSS_SELECTOR, "[data-testid='experience-toggle-intermediate']")
    TOGGLE_EXPERT = (By.CSS_SELECTOR, "[data-testid='experience-toggle-expert']")
    TOGGLE_BUTTON_GROUP = (By.CSS_SELECTOR, ".MuiToggleButtonGroup-root")

    # ── AccountSettingsPage ──────────────────────────────────────────
    ACCOUNT_SETTINGS_PAGE = (By.CSS_SELECTOR, "[data-testid='account-settings-page']")
    TAB_BUTTONS = (By.CSS_SELECTOR, ".MuiTab-root")

    # ── Sidebar ──────────────────────────────────────────────────────
    SIDEBAR = (By.CSS_SELECTOR, "[data-testid='sidebar']")
    SIDEBAR_NAV_ITEMS = (By.CSS_SELECTOR, "[data-testid='sidebar'] .MuiListItemButton-root")
    SIDEBAR_SECTION_HEADERS = (By.CSS_SELECTOR, "[data-testid='sidebar'] .MuiListSubheader-root")

    # ── Snackbar ─────────────────────────────────────────────────────
    SNACKBAR_SUCCESS = (
        By.CSS_SELECTOR,
        "#notistack-snackbar, "
        ".SnackbarItem-variantSuccess, "
        "[class*='notistack-MuiContent-success'], "
        "[class*='notistack-MuiContent'] .MuiTypography-root",
    )

    # ── ShowAllFieldsToggle ──────────────────────────────────────────
    SHOW_ALL_FIELDS_BUTTON = (By.CSS_SELECTOR, "button:has(> .MuiSvgIcon-root)")

    # ── Create dialog ────────────────────────────────────────────────
    # SpeciesCreateDialog has data-testid='create-dialog', but
    # PlantingRunCreateDialog does not.  Use a fallback chain.
    CREATE_DIALOG = (By.CSS_SELECTOR, "[data-testid='create-dialog'], div[role='dialog']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")

    # ── Species list page ────────────────────────────────────────────
    SPECIES_LIST_PAGE = (By.CSS_SELECTOR, "[data-testid='species-list-page']")
    SPECIES_CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")

    # ── Planting run list page ───────────────────────────────────────
    PLANTING_RUN_LIST_PAGE = (By.CSS_SELECTOR, "[data-testid='planting-run-list-page']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ───────────────────────────────────────────────────

    def open_experience_tab(self) -> ExpertiseLevelPage:
        """Navigate to AccountSettings with the experience tab selected."""
        self.navigate(f"{self.ACCOUNT_SETTINGS_PATH}#experience")
        self.wait_for_element(self.ACCOUNT_SETTINGS_PAGE)
        self.wait_for_element(self.TOGGLE_BEGINNER)
        return self

    def open_species_list(self) -> ExpertiseLevelPage:
        """Navigate to the species list page."""
        self.navigate("/stammdaten/species")
        self.wait_for_element(self.SPECIES_LIST_PAGE)
        self.wait_for_loading_complete()
        return self

    def open_planting_run_list(self) -> ExpertiseLevelPage:
        """Navigate to the planting run list page."""
        self.navigate("/durchlaeufe/planting-runs")
        self.wait_for_element(self.PLANTING_RUN_LIST_PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Experience level switching ───────────────────────────────────

    def get_active_toggle_level(self) -> str:
        """Return the currently selected experience level ('beginner', 'intermediate', 'expert').

        Detects MUI ToggleButton selected state via the ``Mui-selected`` class.
        """
        for level in ("beginner", "intermediate", "expert"):
            locator = (By.CSS_SELECTOR, f"[data-testid='experience-toggle-{level}']")
            el = self.wait_for_element(locator)
            classes = el.get_attribute("class") or ""
            if "Mui-selected" in classes:
                return level
        return "unknown"

    def click_level(self, level: str) -> None:
        """Click one of the three experience level toggle buttons.

        Args:
            level: One of 'beginner', 'intermediate', 'expert'.
        """
        locator = (By.CSS_SELECTOR, f"[data-testid='experience-toggle-{level}']")
        btn = self.wait_for_element_clickable(locator)
        self.scroll_and_click(btn)

    def is_toggle_visible(self) -> bool:
        """Check if the experience toggle button group is visible."""
        elements = self.driver.find_elements(*self.TOGGLE_BUTTON_GROUP)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Snackbar ─────────────────────────────────────────────────────

    def wait_for_saved_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for a success snackbar and return its text.

        Falls back to a short sleep if the snackbar is not detectable (notistack
        auto-dismiss or non-standard rendering).
        """
        import time

        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SNACKBAR_SUCCESS)
            )
            return el.text
        except Exception:
            # Snackbar may have auto-dismissed or uses a non-matching selector.
            # Brief pause to let the state settle.
            time.sleep(1)
            return ""

    # ── Sidebar / Navigation tiering ─────────────────────────────────

    def get_sidebar_nav_item_labels(self) -> list[str]:
        """Return all visible sidebar navigation item labels (excluding section headers)."""
        items = self.driver.find_elements(*self.SIDEBAR_NAV_ITEMS)
        return [item.text.strip() for item in items if item.is_displayed() and item.text.strip()]

    def get_sidebar_section_headers(self) -> list[str]:
        """Return all visible sidebar section header texts."""
        headers = self.driver.find_elements(*self.SIDEBAR_SECTION_HEADERS)
        return [h.text.strip() for h in headers if h.is_displayed() and h.text.strip()]

    def is_nav_item_visible(self, path: str) -> bool:
        """Check if a sidebar nav item with the given path data-testid is visible."""
        locator = (By.CSS_SELECTOR, f"[data-testid='nav-{path}']")
        elements = self.driver.find_elements(*locator)
        return len(elements) > 0 and elements[0].is_displayed()

    def count_sidebar_nav_items(self) -> int:
        """Count visible sidebar navigation items (ListItemButton elements)."""
        items = self.driver.find_elements(*self.SIDEBAR_NAV_ITEMS)
        return sum(1 for item in items if item.is_displayed())

    # ── Confirm dialog (window.confirm for downgrade) ────────────────

    def accept_confirm_dialog(self) -> None:
        """Accept a browser-native window.confirm dialog."""
        alert = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.alert_is_present()
        )
        alert.accept()

    def dismiss_confirm_dialog(self) -> None:
        """Dismiss (cancel) a browser-native window.confirm dialog."""
        alert = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.alert_is_present()
        )
        alert.dismiss()

    def is_confirm_dialog_present(self) -> bool:
        """Check if a browser-native alert/confirm dialog is present."""
        try:
            WebDriverWait(self.driver, 3).until(EC.alert_is_present())
            return True
        except Exception:
            return False

    # ── ShowAllFieldsToggle ──────────────────────────────────────────

    def find_show_all_fields_button(self) -> WebElement | None:
        """Find the ShowAllFieldsToggle button in the current dialog.

        The button text is either 'Alle Felder anzeigen' or 'Weniger Felder anzeigen' (DE).
        """
        buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.MuiButton-root")
        for btn in buttons:
            text = btn.text.strip()
            if text in ("Alle Felder anzeigen", "Weniger Felder anzeigen",
                        "Show all fields", "Show fewer fields"):
                return btn
        return None

    def click_show_all_fields(self) -> None:
        """Click the ShowAllFieldsToggle button."""
        btn = self.find_show_all_fields_button()
        if btn is None:
            raise ValueError("ShowAllFieldsToggle button not found in the dialog")
        self.scroll_and_click(btn)

    def get_show_all_fields_text(self) -> str:
        """Return the current text of the ShowAllFieldsToggle button."""
        btn = self.find_show_all_fields_button()
        if btn is None:
            return ""
        return btn.text.strip()

    def is_show_all_fields_visible(self) -> bool:
        """Check if the ShowAllFieldsToggle button is visible."""
        btn = self.find_show_all_fields_button()
        return btn is not None and btn.is_displayed()

    # ── Form field visibility ────────────────────────────────────────

    def is_form_field_visible(self, field_name: str) -> bool:
        """Check if a form field with the given name is visible in the current dialog.

        Uses the ``data-testid='form-field-{field_name}'`` pattern.
        """
        locator = (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}']")
        elements = self.driver.find_elements(*locator)
        return len(elements) > 0 and elements[0].is_displayed()

    def get_visible_form_field_names(self) -> list[str]:
        """Return a list of all visible form field names in the current dialog."""
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='form-field-']"
        )
        names = []
        for el in elements:
            if el.is_displayed():
                testid = el.get_attribute("data-testid") or ""
                name = testid.replace("form-field-", "")
                if name:
                    names.append(name)
        return names

    # ── Create dialog interactions ───────────────────────────────────

    def open_species_create_dialog(self) -> None:
        """Open the SpeciesCreateDialog from the species list page."""
        btn = self.wait_for_element_clickable(self.SPECIES_CREATE_BUTTON)
        self.scroll_and_click(btn)
        # SpeciesCreateDialog has data-testid='create-dialog'
        self.wait_for_element_visible(
            (By.CSS_SELECTOR, "[data-testid='create-dialog']")
        )

    def open_planting_run_create_dialog(self) -> None:
        """Open the PlantingRunCreateDialog from the planting run list page."""
        btn = self.wait_for_element_clickable(self.CREATE_BUTTON)
        self.scroll_and_click(btn)
        # PlantingRunCreateDialog uses MUI Dialog without custom data-testid
        self.wait_for_element_visible(
            (By.CSS_SELECTOR, "div[role='dialog']")
        )

    def close_create_dialog(self) -> None:
        """Close an open create dialog via the cancel button."""
        cancel_btn = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")
        )
        self.scroll_and_click(cancel_btn)
        # Wait for any dialog to close
        WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, "div[role='dialog']")
            )
        )

    def is_create_dialog_open(self) -> bool:
        """Check if a create dialog is currently open."""
        # Check for both data-testid and role-based selectors
        for sel in ["[data-testid='create-dialog']", "div[role='dialog']"]:
            elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if elements and elements[0].is_displayed():
                return True
        return False

    # ── Direct URL navigation (for testing no-access-control) ────────

    def navigate_direct(self, path: str) -> None:
        """Navigate to an arbitrary path (for testing direct URL access)."""
        self.navigate(path)
