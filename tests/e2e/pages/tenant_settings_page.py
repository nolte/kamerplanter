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

    # -- Members / invitations tables --------------------------------------
    # Both tabs render a `DataTable`, and only one tab is mounted at a time, so
    # the durable ``data-table``/``data-table-row`` testids are an exact scope
    # without an aria-label. They also survive the layout switch: the members
    # table passes a ``mobileCardRenderer``, so below `DataTable`'s ``sm``
    # breakpoint it renders `MobileCard`s with no ``<table>`` and no
    # ``<tbody><tr>`` at all — where ``table[aria-label] tbody tr`` silently
    # counted zero members instead of failing.
    MEMBERS_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    MEMBERS_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    # Deliberately scoped *within* a row (see get_member_role_chips), not to
    # the page: the members table currently renders exactly one Chip per row
    # (the role), so this is unambiguous today. It is still class-based rather
    # than a keyed `card-chip-role` hook, so a second per-row chip would make
    # ``get_member_role_chips`` pick whichever renders first -- a proper fix
    # would key the chip in `mobileCardRenderer` (a product rendering change
    # with mobile-layout implications) and migrate to
    # ``BasePage.get_column_chip_texts("role")``. Left as a follow-up; see
    # #778 A11.
    MEMBER_ROLE_CHIP = (By.CSS_SELECTOR, ".MuiChip-root")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # -- Invitations tab locators ------------------------------------------
    INVITE_EMAIL_FIELD = (By.CSS_SELECTOR, "[data-testid='invite-email-field'] input")
    SEND_INVITATION_BTN = (By.CSS_SELECTOR, "[data-testid='send-invitation-btn']")
    CREATE_LINK_BTN = (By.CSS_SELECTOR, "[data-testid='create-link-btn']")
    INVITATIONS_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    INVITATIONS_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

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
        tabs = self.tab_elements((By.CSS_SELECTOR, ".MuiTabs-root button"))
        return [t.text for t in tabs if t.text]

    def is_tab_visible(self, label: str) -> bool:
        """Check if a tab with the given label is visible."""
        return label in self.get_tab_labels()

    def get_active_tab_index(self) -> int:
        """Return the index of the currently active tab (0-based)."""
        tabs = self.tab_elements((By.CSS_SELECTOR, ".MuiTabs-root button"))
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

    #: Column id of the members table's identifying column (TenantSettingsPage).
    MEMBER_NAME_COLUMN_ID = "display_name"

    def get_member_names(self) -> list[str]:
        """Return the display names from the members table.

        Addressed by column id, not by position: the members DataTable renders
        `MobileCard`s (title = display name) below its mobile breakpoint, where
        there is no ``<td>`` to read.
        """
        return [
            self.get_row_primary_text(row, self.MEMBER_NAME_COLUMN_ID)
            for row in self.driver.find_elements(*self.MEMBERS_TABLE_ROWS)
        ]

    def get_member_role_chips(self) -> list[str]:
        """Return the role chip texts from the members table."""
        rows = self.driver.find_elements(*self.MEMBERS_TABLE_ROWS)
        chips = []
        for row in rows:
            chip_els = row.find_elements(*self.MEMBER_ROLE_CHIP)
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
        elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='remove-member-']")
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
        btn = self.find_present(self.SEND_INVITATION_BTN)
        return btn.is_enabled()

    def click_create_link(self) -> None:
        """Click the Create Link button."""
        btn = self.wait_for_element_clickable(self.CREATE_LINK_BTN)
        self.scroll_and_click(btn)

    def is_invite_email_field_present(self) -> bool:
        """Check if the invite-email input field is present on the Invitations tab."""
        return self.is_present(self.INVITE_EMAIL_FIELD)

    def is_create_link_button_visible(self) -> bool:
        """Check if the Create Link button is present and displayed (admin indicator).

        Waits for the button to appear first: the only caller reads it directly
        after :meth:`click_tab_invitations`, which waits for the *tab* to be
        clickable and says nothing about the tab **panel** having rendered. The
        bare ``find_elements`` this replaces therefore answered ``False`` for
        "the panel is still mounting" — TC-REQ-024-016 failed that way on the
        ``full-mobile`` profile of run 31113673507. ``False`` after the full
        budget is still a genuine "no create-link button for this role".
        """
        return self.is_visible_within(self.CREATE_LINK_BTN)

    def get_invitation_count(self) -> int:
        """Return the number of invitations in the table."""
        rows = self.driver.find_elements(*self.INVITATIONS_TABLE_ROWS)
        return len(rows)

    def get_invitation_row_texts(self) -> list[list[str]]:
        """Return the readable text fragments of every visible invitation row."""
        return [
            self.get_row_text_fragments(row)
            for row in self.driver.find_elements(*self.INVITATIONS_TABLE_ROWS)
        ]

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
