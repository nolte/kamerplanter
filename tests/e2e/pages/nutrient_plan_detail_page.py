"""Page object for the Nutrient Plan detail page (REQ-004)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import DEFAULT_TIMEOUT, BasePage


class NutrientPlanDetailPage(BasePage):
    """Interact with a Nutrient Plan detail page (``/duengung/plans/:key``)."""

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='nutrient-plan-detail-page']")
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    # The app's own hook (`NutrientPlanDetailPage.tsx:114`). The XPath that stood
    # here -- `//button[contains(@class, 'MuiButton-colorError')]` -- was
    # unscoped and structural: it matched *any* error-coloured button in the
    # document, so a hit proved nothing about which control was clicked. It also
    # made the miss unreadable, and the miss matters here: the button is rendered
    # conditionally (`{!c.isDeletionProtected && ...}`, UI-NFR-018 R-012), so on
    # a system plan it is legitimately absent -- which is precisely what run
    # 31113673507 hit after the row click opened a seeded plan instead of the
    # freshly created one, and reported as a bare empty `TimeoutException`.
    DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='delete-nutrient-plan-button']")

    # Confirm dialog
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # Tabs (3 tabs: Phase Entries | Validation | Edit)
    TAB_PHASE_ENTRIES = (By.XPATH, "//button[@role='tab'][1]")
    TAB_VALIDATION = (By.XPATH, "//button[@role='tab'][2]")
    TAB_EDIT = (By.XPATH, "//button[@role='tab'][4]")

    # Tab 0: Phase entries
    ADD_ENTRY_BUTTON = (
        By.XPATH,
        "//button[contains(., 'Eintrag') or contains(., 'Entry') or contains(., 'Phase')]",
    )
    ENTRY_CARDS = (By.CSS_SELECTOR, "[data-testid='nutrient-plan-detail-page'] .MuiCard-root")
    # Scoped to the page root: an unscoped ``.MuiAlert-root`` also matches
    # MainLayout's light-mode warning banner (`severity="warning"`), which
    # renders as a sibling of this page's root, not a descendant -- so this
    # scoping alone is enough to exclude it. See #778 A11.
    NO_ENTRIES_ALERT = (By.CSS_SELECTOR, "[data-testid='nutrient-plan-detail-page'] .MuiAlert-root")

    # Tab 1: Validation — cards and alerts
    VALIDATION_SECTION = (
        By.CSS_SELECTOR,
        "[data-testid='nutrient-plan-detail-page'] .MuiCard-root",
    )
    # Scoped to the page root -- see NO_ENTRIES_ALERT above for the rationale.
    COMPLETENESS_ALERT = (
        By.CSS_SELECTOR,
        "[data-testid='nutrient-plan-detail-page'] .MuiAlert-root",
    )

    # Tab 2: Edit form
    FORM_NAME = (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
    FORM_DESCRIPTION = (By.CSS_SELECTOR, "[data-testid='form-field-description'] textarea")
    FORM_AUTHOR = (By.CSS_SELECTOR, "[data-testid='form-field-author'] input")
    FORM_VERSION = (By.CSS_SELECTOR, "[data-testid='form-field-version'] input")
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='form-cancel-button']")

    # Error state
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")
    READONLY_BANNER = (By.CSS_SELECTOR, "[data-testid='nutrient-plan-readonly-banner']")
    LOADING_SPINNER = (By.CSS_SELECTOR, ".MuiCircularProgress-root")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> NutrientPlanDetailPage:
        """Navigate to a nutrient plan detail page and wait for it to load."""
        self.navigate(f"/duengung/plans/{key}")
        self.wait_for_element(self.PAGE, timeout=20)
        self.wait_for_loading_complete(timeout=20)
        return self

    # ── Page info ──────────────────────────────────────────────────────

    def get_page_title_text(self) -> str:
        """Return the text of the page title."""
        el = self.wait_for_element(self.PAGE_TITLE)
        return el.text

    def get_active_tab_text(self) -> str:
        """Return the text of the currently selected tab."""
        active = self.find_present((By.CSS_SELECTOR, "[role='tab'][aria-selected='true']"))
        return active.text

    def get_tab_count(self) -> int:
        """Return the number of tabs rendered on the detail page."""
        return len(self.tab_elements((By.CSS_SELECTOR, "[role='tab']")))

    def is_first_tab_selected(self) -> bool:
        """Return True if the first (Phase Entries) tab is the active tab."""
        first_tab = self.find_present(self.TAB_PHASE_ENTRIES)
        return first_tab.get_attribute("aria-selected") == "true"

    # ── Tab navigation ─────────────────────────────────────────────────

    def click_tab_phase_entries(self) -> None:
        """Click the first tab (Phase Entries)."""
        self.wait_for_element_clickable(self.TAB_PHASE_ENTRIES).click()

    def click_tab_validation(self) -> None:
        """Click the second tab (Validation)."""
        self.wait_for_element_clickable(self.TAB_VALIDATION).click()

    def click_tab_edit(self) -> None:
        """Click the third tab (Edit)."""
        self.wait_for_element_clickable(self.TAB_EDIT).click()

    # ── Tab 0: Phase entries ────────────────────────────────────────────

    def click_add_phase_entry(self) -> None:
        """Click the button to add a new phase entry."""
        # The add entry button is a contained Button in the phase entries tab
        add_btn = self.wait_for_element_clickable(
            (
                By.XPATH,
                "//button[contains(@class, 'MuiButton-contained') and not(contains(@class, 'MuiButton-colorError'))]",
            )
        )
        self.scroll_and_click(add_btn)

    def get_phase_entry_count(self) -> int:
        """Return the number of phase entry cards shown."""
        cards = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='nutrient-plan-detail-page'] .MuiCard-root"
        )
        return len(cards)

    def has_no_entries_message(self) -> bool:
        """Return True if the 'no entries' alert is shown."""
        alerts = self.driver.find_elements(*self.NO_ENTRIES_ALERT)
        for alert in alerts:
            if alert.is_displayed():
                return True
        return False

    def get_entry_phase_chips(self) -> list[str]:
        """Return the text of all phase chips in phase entry cards."""
        chips = self.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-testid='nutrient-plan-detail-page'] .MuiChip-colorPrimary .MuiChip-label",
        )
        return [c.text for c in chips if c.text]

    def click_entry_expand(self, index: int) -> None:
        """Click the expand toggle on the entry at the given index."""
        expand_btns = self.driver.find_elements(
            By.CSS_SELECTOR,
            "[data-testid='nutrient-plan-detail-page'] button svg[data-testid='ExpandMoreIcon']",
        )
        icon = self.require_index(expand_btns, index, "nutrient plan entry expander")
        # Coordinate-free: the target is resolved indirectly (the icon's parent
        # button) and sits in a row of same-sized icon buttons, so a coordinate
        # miss activates a neighbour without raising. The button activates from
        # its own `onClick`, which a dispatched click drives.
        self.click_coordinate_free(icon.find_element(By.XPATH, "./.."))

    # ── Tab 1: Validation ──────────────────────────────────────────────

    def wait_for_validation_loaded(self, timeout: int = 20) -> None:
        """Wait until the circular progress spinner disappears (validation done)."""
        from selenium.webdriver.support import expected_conditions as EC

        self.poll(timeout).until(EC.invisibility_of_element_located(self.LOADING_SPINNER))

    def get_validation_alerts(self) -> list[str]:
        """Return the text content of all visible Alert components."""
        alerts = self.driver.find_elements(*self.COMPLETENESS_ALERT)
        return [a.text for a in alerts if a.is_displayed() and a.text]

    def is_completeness_success(self) -> bool:
        """Return True if the completeness alert has a success severity."""
        # Scoped to the page root -- an unscoped ``.MuiAlert-colorWarning``
        # would also match MainLayout's light-mode warning banner (see
        # NO_ENTRIES_ALERT above), which could otherwise make this method
        # report a false warning while the completeness alert itself is
        # green. See #778 A11.
        alerts = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='nutrient-plan-detail-page'] .MuiAlert-colorSuccess"
        )
        return any(a.is_displayed() for a in alerts)

    def is_completeness_warning(self) -> bool:
        """Return True if the completeness alert has a warning severity."""
        alerts = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='nutrient-plan-detail-page'] .MuiAlert-colorWarning"
        )
        return any(a.is_displayed() for a in alerts)

    # ── Tab 2: Edit form ───────────────────────────────────────────────

    def fill_name(self, name: str) -> None:
        """Fill the plan name field."""
        el = self.wait_for_element_clickable(self.FORM_NAME)
        self.clear_and_fill(el, name)

    def fill_author(self, author: str) -> None:
        """Fill the author field."""
        el = self.wait_for_element_clickable(self.FORM_AUTHOR)
        self.clear_and_fill(el, author)

    def fill_version(self, version: str) -> None:
        """Fill the version field."""
        el = self.wait_for_element_clickable(self.FORM_VERSION)
        self.clear_and_fill(el, version)

    def get_name_field_value(self) -> str:
        """Return the current value of the name input field."""
        el = self.wait_for_element(self.FORM_NAME)
        return el.get_attribute("value") or ""

    def get_author_field_value(self) -> str:
        """Return the current value of the author input field."""
        el = self.wait_for_element(self.FORM_AUTHOR)
        return el.get_attribute("value") or ""

    def is_read_only(self) -> bool:
        """Return True if this plan is origin-protected (read-only).

        Global/system nutrient plans (UI-NFR-018) show a read-only banner and
        render no editable form actions on the edit tab.
        """
        return len(self.driver.find_elements(*self.READONLY_BANNER)) > 0

    def is_submit_button_enabled(self) -> bool:
        """Return True if the submit button is enabled (form is dirty)."""
        el = self.wait_for_element(self.FORM_SUBMIT)
        return el.is_enabled()

    def submit_edit_form(self) -> None:
        """Submit the in-page edit form (coordinate-free; see BasePage)."""
        self.wait_and_click_coordinate_free(self.FORM_SUBMIT)

    def cancel_edit_form(self) -> None:
        """Click cancel to reset the edit form."""
        self.wait_and_click(self.FORM_CANCEL)

    def toggle_is_template(self) -> None:
        """Toggle the is_template switch in the edit form."""
        switch = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-is_template'] input[type='checkbox']")
        )
        self.scroll_and_click(switch)

    def is_template_checked(self) -> bool:
        """Return True if the is_template switch is checked."""
        switch = self.find_present(
            (By.CSS_SELECTOR, "[data-testid='form-field-is_template'] input[type='checkbox']")
        )
        return switch.is_selected()

    # ── Delete ─────────────────────────────────────────────────────────

    def click_delete(self) -> None:
        """Click the delete button to open the confirm dialog."""
        self.wait_and_click(self.DELETE_BUTTON)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def is_confirm_dialog_open(self) -> bool:
        """Return True if the confirm dialog is visible.

        Deliberately instantaneous, not anchored: its *presence* call site
        reads it right after ``click_delete()``, which already runs
        ``wait_for_element_visible(self.CONFIRM_DIALOG)``. For the
        *dismissal* check, use :meth:`wait_for_confirm_dialog_closed` instead:
        MUI's Dialog unmounts only after its exit transition finishes, and
        ``cancel_delete()`` does not itself wait for that, so a raw negated
        read sampled right after cancelling can still see the dialog
        mid-fade-out and report it as open (#946 wave 9 -- the same
        guarded-dismissal gap waves 4-6 fixed on the other detail pages).
        """
        dialogs = self.driver.find_elements(*self.CONFIRM_DIALOG)
        return any(d.is_displayed() for d in dialogs)

    def wait_for_confirm_dialog_closed(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Wait for the delete ConfirmDialog to actually leave the DOM.

        Returns ``False`` (rather than raising) once the budget is spent, so a
        dialog that genuinely never closes still fails the caller's own
        assertion.
        """
        return self.is_absent_within(self.CONFIRM_DIALOG, timeout=timeout)

    def confirm_delete(self) -> None:
        """Click the confirm button in the delete dialog."""
        self.wait_and_click(self.CONFIRM_BUTTON)

    def cancel_delete(self) -> None:
        """Click the cancel button in the delete dialog."""
        self.wait_and_click(self.CONFIRM_CANCEL)

    # ── Error state ────────────────────────────────────────────────────

    def is_error_displayed(self) -> bool:
        """Return True if an error-display component is visible."""
        elements = self.driver.find_elements(*self.ERROR_DISPLAY)
        return len(elements) > 0 and elements[0].is_displayed()
