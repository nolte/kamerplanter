"""Page object for the TenantSwitcher component in the App Bar (REQ-024)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage, DEFAULT_TIMEOUT


class TenantSwitcherPage(BasePage):
    """Interact with the TenantSwitcher dropdown in the App Bar."""

    # -- Locators ----------------------------------------------------------
    # The trigger button displays the active tenant name + dropdown arrow
    TRIGGER_BUTTON = (By.CSS_SELECTOR, "header button[aria-haspopup='menu']")
    # Fallback: find by the ArrowDropDown icon in the header
    TRIGGER_BUTTON_ALT = (
        By.CSS_SELECTOR,
        "header button .MuiTypography-body2",
    )
    # The dropdown menu
    MENU = (By.CSS_SELECTOR, ".MuiMenu-paper")
    MENU_ITEMS = (By.CSS_SELECTOR, ".MuiMenu-paper li[role='menuitem']")
    # Active tenant has the 'selected' class
    SELECTED_ITEM = (By.CSS_SELECTOR, ".MuiMenu-paper li.Mui-selected")
    # Check icon next to active tenant
    CHECK_ICON = (By.CSS_SELECTOR, ".MuiMenu-paper li.Mui-selected [data-testid='CheckIcon']")
    # Type icons
    PERSON_ICON = (By.CSS_SELECTOR, "[data-testid='PersonIcon']")
    GROUPS_ICON = (By.CSS_SELECTOR, "[data-testid='GroupsIcon']")
    # The "Create organization" menu item (last, after divider)
    CREATE_ORG_ITEM = (By.CSS_SELECTOR, ".MuiMenu-paper li:last-child")
    # Divider before create item
    DIVIDER = (By.CSS_SELECTOR, ".MuiMenu-paper .MuiDivider-root")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # -- Interactions ------------------------------------------------------

    def open_menu(self) -> None:
        """Click the tenant switcher trigger to open the dropdown menu."""
        # Try the primary locator first, fall back to finding any button in header
        # that has a Typography child
        buttons = self.driver.find_elements(*self.TRIGGER_BUTTON)
        if buttons and buttons[0].is_displayed():
            self.scroll_and_click(buttons[0])
        else:
            # Fallback: find the button containing the tenant name Typography
            parent = self.wait_for_element(self.TRIGGER_BUTTON_ALT)
            btn = parent.find_element(By.XPATH, "./..")
            self.scroll_and_click(btn)
        # Wait for the menu to appear
        self.wait_for_element_visible(self.MENU)

    def close_menu(self) -> None:
        """Close the dropdown by pressing Escape."""
        from selenium.webdriver.common.keys import Keys

        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.invisibility_of_element_located(self.MENU)
        )

    def is_menu_open(self) -> bool:
        """Check if the tenant switcher menu is currently open."""
        elements = self.driver.find_elements(*self.MENU)
        return len(elements) > 0 and elements[0].is_displayed()

    # -- Queries -----------------------------------------------------------

    def get_active_tenant_name(self) -> str:
        """Return the name displayed on the trigger button (active tenant)."""
        elements = self.driver.find_elements(*self.TRIGGER_BUTTON_ALT)
        if elements and elements[0].is_displayed():
            return elements[0].text
        return ""

    def get_tenant_names(self) -> list[str]:
        """Return the names of all tenants in the open dropdown.

        Excludes the last "Create organization" item after the divider.
        """
        items = self.driver.find_elements(*self.MENU_ITEMS)
        names = []
        for item in items:
            # The last item after divider is the create-org item; skip it
            text_els = item.find_elements(By.CSS_SELECTOR, ".MuiListItemText-primary")
            if text_els:
                names.append(text_els[0].text)
            else:
                names.append(item.text.strip())
        # Remove the last entry if it's the create-org button
        if names and self._has_divider():
            names = names[:-1]
        return names

    def get_tenant_count(self) -> int:
        """Return the number of tenant entries (excluding create-org item)."""
        return len(self.get_tenant_names())

    def get_selected_tenant_name(self) -> str:
        """Return the name of the currently selected (active) tenant in the menu."""
        elements = self.driver.find_elements(*self.SELECTED_ITEM)
        if elements:
            text_els = elements[0].find_elements(
                By.CSS_SELECTOR, ".MuiListItemText-primary"
            )
            if text_els:
                return text_els[0].text
            return elements[0].text.strip()
        return ""

    def has_check_icon_for_selected(self) -> bool:
        """Check if the selected tenant has a check icon."""
        selected = self.driver.find_elements(*self.SELECTED_ITEM)
        if not selected:
            return False
        icons = selected[0].find_elements(By.CSS_SELECTOR, "[data-testid='CheckIcon']")
        return len(icons) > 0

    def get_tenant_type_icon(self, tenant_name: str) -> str | None:
        """Return 'personal' or 'organization' based on the icon next to a tenant.

        Returns None if the tenant is not found.
        """
        items = self.driver.find_elements(*self.MENU_ITEMS)
        for item in items:
            text_els = item.find_elements(By.CSS_SELECTOR, ".MuiListItemText-primary")
            name = text_els[0].text if text_els else item.text.strip()
            if name == tenant_name:
                person = item.find_elements(By.CSS_SELECTOR, "[data-testid='PersonIcon']")
                groups = item.find_elements(By.CSS_SELECTOR, "[data-testid='GroupsIcon']")
                if person:
                    return "personal"
                if groups:
                    return "organization"
                return None
        return None

    def has_create_org_item(self) -> bool:
        """Check if the 'Create organization' menu item is present."""
        return self._has_divider()

    # -- Interactions: Switching -------------------------------------------

    def switch_to_tenant(self, tenant_name: str) -> None:
        """Click a tenant by name in the open dropdown to switch to it.

        Note: The TenantSwitcher triggers window.location.reload() on switch,
        so the caller should wait for the page to reload afterwards.
        """
        items = self.driver.find_elements(*self.MENU_ITEMS)
        for item in items:
            text_els = item.find_elements(By.CSS_SELECTOR, ".MuiListItemText-primary")
            name = text_els[0].text if text_els else item.text.strip()
            if name == tenant_name:
                self.scroll_and_click(item)
                return
        raise ValueError(f"Tenant '{tenant_name}' not found in switcher menu")

    def click_create_organization(self) -> None:
        """Click the 'Create organization' item at the bottom of the menu."""
        btn = self.wait_for_element_clickable(self.CREATE_ORG_ITEM)
        self.scroll_and_click(btn)

    # -- Private helpers ---------------------------------------------------

    def _has_divider(self) -> bool:
        """Check if a divider is present in the menu (separates tenants from create-org)."""
        elements = self.driver.find_elements(*self.DIVIDER)
        return len(elements) > 0
