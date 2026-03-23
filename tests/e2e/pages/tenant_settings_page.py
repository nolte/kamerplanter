"""Page object for the Tenant Settings page (REQ-024)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage, DEFAULT_TIMEOUT


class TenantSettingsPage(BasePage):
    """Interact with the Tenant Settings page (``/tenants/settings``)."""

    PATH = "/tenants/settings"

    # -- Page-level locators -----------------------------------------------
    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    TABS = (By.CSS_SELECTOR, ".MuiTabs-root")
    TAB_MEMBERS = (By.CSS_SELECTOR, ".MuiTabs-root button:first-child")
    TAB_INVITATIONS = (By.CSS_SELECTOR, ".MuiTabs-root button:nth-child(2)")

    # -- Members tab locators ----------------------------------------------
    MEMBERS_TABLE = (By.CSS_SELECTOR, "table[aria-label]")
    MEMBERS_TABLE_ROWS = (By.CSS_SELECTOR, "table[aria-label] tbody tr")
    MEMBER_ROLE_CHIP = (By.CSS_SELECTOR, ".MuiChip-root")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")
    # Mobile view
    MEMBER_MOBILE_CARDS = (By.CSS_SELECTOR, ".MuiCard-root")

    # -- Invitations tab locators ------------------------------------------
    INVITE_EMAIL_FIELD = (By.CSS_SELECTOR, "[data-testid='invite-email-field'] input")
    SEND_INVITATION_BTN = (By.CSS_SELECTOR, "[data-testid='send-invitation-btn']")
    CREATE_LINK_BTN = (By.CSS_SELECTOR, "[data-testid='create-link-btn']")
    INVITATIONS_TABLE = (By.CSS_SELECTOR, "table[aria-label]")
    INVITATIONS_TABLE_ROWS = (By.CSS_SELECTOR, "table[aria-label] tbody tr")

    # -- Snackbar ----------------------------------------------------------
    SNACKBAR = (By.CSS_SELECTOR, "#notistack-snackbar")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # -- Navigation --------------------------------------------------------

    def open(self) -> TenantSettingsPage:
        """Navigate to the tenant settings page and wait for it to load."""
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE_TITLE)
        return self

    # -- Queries: Page level -----------------------------------------------

    def get_page_title_text(self) -> str:
        """Return the page title text."""
        return self.wait_for_element(self.PAGE_TITLE).text

    def get_tab_labels(self) -> list[str]:
        """Return the labels of all visible tabs."""
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".MuiTabs-root button")
        return [t.text for t in tabs if t.text]

    def is_tab_visible(self, label: str) -> bool:
        """Check if a tab with the given label is visible."""
        return label in self.get_tab_labels()

    def get_active_tab_index(self) -> int:
        """Return the index of the currently active tab (0-based)."""
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".MuiTabs-root button")
        for i, tab in enumerate(tabs):
            if "Mui-selected" in (tab.get_attribute("class") or ""):
                return i
        return -1

    # -- Interactions: Tabs ------------------------------------------------

    def click_tab_members(self) -> None:
        """Click the Members tab."""
        tab = self.wait_for_element_clickable(self.TAB_MEMBERS)
        self.scroll_and_click(tab)

    def click_tab_invitations(self) -> None:
        """Click the Invitations tab."""
        tab = self.wait_for_element_clickable(self.TAB_INVITATIONS)
        self.scroll_and_click(tab)

    # -- Queries: Members tab ----------------------------------------------

    def get_member_count(self) -> int:
        """Return the number of members displayed in the table."""
        rows = self.driver.find_elements(*self.MEMBERS_TABLE_ROWS)
        return len(rows)

    def get_member_names(self) -> list[str]:
        """Return the display names from the members table."""
        rows = self.driver.find_elements(*self.MEMBERS_TABLE_ROWS)
        names = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                names.append(cells[0].text)
        return names

    def get_member_role_chips(self) -> list[str]:
        """Return the role chip texts from the members table."""
        rows = self.driver.find_elements(*self.MEMBERS_TABLE_ROWS)
        chips = []
        for row in rows:
            chip_els = row.find_elements(By.CSS_SELECTOR, ".MuiChip-root")
            if chip_els:
                chips.append(chip_els[0].text)
        return chips

    def has_remove_button_for_member(self, member_key: str) -> bool:
        """Check if a remove button exists for the given member key."""
        locator = (By.CSS_SELECTOR, f"[data-testid='remove-member-{member_key}']")
        elements = self.driver.find_elements(*locator)
        return len(elements) > 0 and elements[0].is_displayed()

    def click_remove_member(self, member_key: str) -> None:
        """Click the remove button for a specific member."""
        locator = (By.CSS_SELECTOR, f"[data-testid='remove-member-{member_key}']")
        btn = self.wait_for_element_clickable(locator)
        self.scroll_and_click(btn)

    def has_empty_state(self) -> bool:
        """Check if the empty state message is displayed."""
        elements = self.driver.find_elements(*self.EMPTY_STATE)
        return len(elements) > 0 and elements[0].is_displayed()

    def has_any_remove_buttons(self) -> bool:
        """Check if any remove-member buttons are visible (admin indicator)."""
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid^='remove-member-']"
        )
        return any(e.is_displayed() for e in elements) if elements else False

    # -- Interactions: Invitations tab -------------------------------------

    def enter_invite_email(self, email: str) -> None:
        """Type an email address into the invite field."""
        field = self.wait_for_element(self.INVITE_EMAIL_FIELD)
        field.clear()
        field.send_keys(email)

    def click_send_invitation(self) -> None:
        """Click the Send Invitation button."""
        btn = self.wait_for_element_clickable(self.SEND_INVITATION_BTN)
        self.scroll_and_click(btn)

    def is_send_invitation_enabled(self) -> bool:
        """Check if the Send Invitation button is enabled."""
        btn = self.driver.find_element(*self.SEND_INVITATION_BTN)
        return btn.is_enabled()

    def click_create_link(self) -> None:
        """Click the Create Link button."""
        btn = self.wait_for_element_clickable(self.CREATE_LINK_BTN)
        self.scroll_and_click(btn)

    def get_invitation_count(self) -> int:
        """Return the number of invitations in the table."""
        rows = self.driver.find_elements(*self.INVITATIONS_TABLE_ROWS)
        return len(rows)

    def get_invitation_row_texts(self) -> list[list[str]]:
        """Return all cell texts for every visible invitation row."""
        rows = self.driver.find_elements(*self.INVITATIONS_TABLE_ROWS)
        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            result.append([c.text for c in cells])
        return result

    def has_revoke_button_for_invitation(self, inv_key: str) -> bool:
        """Check if a revoke button exists for the given invitation key."""
        locator = (By.CSS_SELECTOR, f"[data-testid='revoke-invitation-{inv_key}']")
        elements = self.driver.find_elements(*locator)
        return len(elements) > 0 and elements[0].is_displayed()

    def click_revoke_invitation(self, inv_key: str) -> None:
        """Click the revoke button for a specific invitation."""
        locator = (By.CSS_SELECTOR, f"[data-testid='revoke-invitation-{inv_key}']")
        btn = self.wait_for_element_clickable(locator)
        self.scroll_and_click(btn)

    # -- Snackbar ----------------------------------------------------------

    def wait_for_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for a notistack snackbar and return its text."""
        el = self.wait_for_element_visible(self.SNACKBAR, timeout=timeout)
        return el.text

    def has_snackbar(self) -> bool:
        """Check if a snackbar is currently visible."""
        elements = self.driver.find_elements(*self.SNACKBAR)
        return len(elements) > 0 and elements[0].is_displayed()
