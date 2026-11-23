"""Page object for the Account Settings page (REQ-023)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from .base_page import DEFAULT_TIMEOUT, BasePage


#: Which settings group holds a section (F-11, #2935) -- mirrors
#: ``src/frontend/src/config/settingsGroups.ts``. A section is addressed as
#: ``/settings/<group>#<section>``; the former ``/settings#<tab>`` form is not
#: mapped and lands on the first group.
SECTION_GROUPS: dict[str, str] = {
    "profile": "account",
    "account": "account",
    "experience": "display",
    "kiosk": "display",
    "modules": "display",
    "dashboard": "display",
    "notifications": "notifications",
    "security": "security",
    "sessions": "security",
    "apikeys": "security",
    "connect": "security",
    "ha": "integrations",
    "ha-publish": "integrations",
    "storage": "installation",
    "weather-providers": "installation",
    "ha-connection": "installation",
    "plant-identification": "installation",
    "recognition": "installation",
}


class AccountSettingsPage(BasePage):
    """Interact with the grouped settings page (``/settings``, ``/settings/<group>``)."""

    PATH = "/settings"

    # ── Page-level locators ─────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='account-settings-page']")
    #: Group entries: the desktop side navigation and the phone's group list
    #: carry the same ``settings-group-<key>`` ids.
    GROUP_ENTRIES = (
        By.CSS_SELECTOR,
        "[data-testid^='settings-group-']:not([data-testid^='settings-group-panel-']):not([data-testid='settings-group-title'])",
    )
    GROUP_TITLE = (By.CSS_SELECTOR, "[data-testid='settings-group-title']")
    BACK_BUTTON = (By.CSS_SELECTOR, "[data-testid='settings-back-button']")
    ERROR_ALERT = (By.CSS_SELECTOR, ".MuiAlert-colorError")

    @staticmethod
    def group_entry(group: str) -> tuple[str, str]:
        """Locator of the navigation entry of *group*."""
        return (By.CSS_SELECTOR, f"[data-testid='settings-group-{group}']")

    @staticmethod
    def group_panel(group: str) -> tuple[str, str]:
        """Locator of the open group's content panel."""
        return (By.CSS_SELECTOR, f"[data-testid='settings-group-panel-{group}']")

    @staticmethod
    def section(section: str) -> tuple[str, str]:
        """Locator of a section inside the open group."""
        return (By.CSS_SELECTOR, f"[data-testid='settings-section-{section}']")

    # ── Profile section locators ────────────────────────────────────────────
    DISPLAY_NAME_INPUT = (By.CSS_SELECTOR, "[data-testid='profile-display-name'] input")
    EMAIL_INPUT = (By.CSS_SELECTOR, "[data-testid='profile-email'] input")
    PROFILE_SAVE_BUTTON = (By.CSS_SELECTOR, "[data-testid='profile-save-btn']")
    LOCALE_SELECT = (By.CSS_SELECTOR, "[data-testid='profile-locale']")
    TIMEZONE_INPUT = (By.CSS_SELECTOR, "[data-testid='profile-timezone'] input")

    # ── Security section locators ───────────────────────────────────────────
    CURRENT_PASSWORD_INPUT = (By.CSS_SELECTOR, "[data-testid='current-password-field'] input")
    NEW_PASSWORD_INPUT = (By.CSS_SELECTOR, "[data-testid='new-password-field'] input")
    CHANGE_PASSWORD_BUTTON = (By.CSS_SELECTOR, "[data-testid='change-password-btn']")
    #: The linked-provider list is the page's only `List`/`ListItemText`
    #: (`SecuritySettingsGroup.tsx`), so the page hook scopes it exactly.
    #: Unscoped, `.MuiListItemText-primary` also matched every Sidebar nav
    #: label -- those are `ListItemText`s too, mounted in the same DOM and
    #: displayed at >= `md` -- which inflated the provider list to the whole
    #: navigation.
    PROVIDER_NAMES = (
        By.CSS_SELECTOR,
        "[data-testid='account-settings-page'] .MuiListItemText-primary",
    )

    # ── Experience section locators ─────────────────────────────────────────
    EXPERIENCE_BEGINNER = (By.CSS_SELECTOR, "[data-testid='experience-toggle-beginner']")
    EXPERIENCE_INTERMEDIATE = (By.CSS_SELECTOR, "[data-testid='experience-toggle-intermediate']")
    EXPERIENCE_EXPERT = (By.CSS_SELECTOR, "[data-testid='experience-toggle-expert']")

    # ── Account section locators ────────────────────────────────────────────
    DELETE_ACCOUNT_BUTTON = (By.CSS_SELECTOR, "[data-testid='delete-account-btn']")

    # ── Snackbar ────────────────────────────────────────────────────────
    SNACKBAR_SUCCESS = (By.CSS_SELECTOR, "#notistack-snackbar, .SnackbarItem-variantSuccess")
    SNACKBAR_ERROR = (By.CSS_SELECTOR, ".SnackbarItem-variantError")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Navigation ──────────────────────────────────────────────────────

    def open(self, section: str | None = None) -> AccountSettingsPage:
        """Navigate to the settings page and wait for it to load.

        Args:
            section: Optional section key (profile, security, sessions, ...);
                opens ``/settings/<group>#<section>`` with the group taken from
                :data:`SECTION_GROUPS`. Without it, ``/settings`` -- the first
                group on a desktop, the group list on a phone.
        """
        path = self.PATH
        if section:
            path = f"{self.PATH}/{SECTION_GROUPS[section]}#{section}"
        self.navigate(path)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        if section:
            self.wait_for_element(self.section(section))
        return self

    def open_path(self, path: str, settled: tuple[str, str]) -> None:
        """Load an arbitrary settings *path* and wait for the *settled* element.

        For the routing cases of F-11 (#2935) whose path is deliberately not a
        section the user sees -- an unknown group (404 page), a group the user
        may not open (lands on the first group) or a former ``/settings#<tab>``
        bookmark. Waiting on the expected shape keeps the read that follows from
        racing the lazily loaded route.
        """
        self.navigate_direct(path, settled, what=f"settings route {path}")

    # ── Group navigation (F-11) ─────────────────────────────────────────

    def get_group_keys(self) -> list[str]:
        """Return the keys of the displayed group entries, in navigation order.

        On a desktop these are the side navigation's entries, on a phone the
        group list's -- shown on ``/settings`` only, a group's detail view has
        the back arrow instead.
        """
        entries = self.tab_elements(self.GROUP_ENTRIES)
        return [
            (entry.get_attribute("data-testid") or "").removeprefix("settings-group-")
            for entry in entries
            if entry.is_displayed()
        ]

    def click_group(self, group: str) -> None:
        """Open *group* from the navigation and wait for its panel."""
        self.scroll_and_click(self.wait_for_element_clickable(self.group_entry(group)))
        self.wait_for_element(self.group_panel(group))

    def get_group_title(self) -> str:
        """Return the heading of the open group."""
        return self.wait_for_element_visible(self.GROUP_TITLE).text

    def is_back_button_visible(self) -> bool:
        """Whether the phone's detail view shows its back arrow."""
        elements = self.driver.find_elements(*self.BACK_BUTTON)
        return len(elements) > 0 and elements[0].is_displayed()

    def click_back(self) -> None:
        """Leave a group's detail view for the group list (phone)."""
        self.scroll_and_click(self.wait_for_element_clickable(self.BACK_BUTTON))

    # ── Profile section ─────────────────────────────────────────────────

    def wait_for_profile_loaded(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the profile fields carry the fetched user, not their blank initial state.

        `ProtectedRoute` unblocks this route once `refreshAccessToken` resolves
        and flips `auth.initialized` -- **before** the separate `fetchProfile()`
        dispatch `AuthProvider.initAuth` chains after it has itself settled
        (`authSlice.ts`: `refreshAccessToken.fulfilled` sets `initialized` on its
        own, independent of `fetchProfile`). `AccountSettingsGroup.tsx` seeds
        `displayName` from `user` via a `useEffect` and reads `user?.email`
        directly, and `user` is still `null` in that window -- so
        `profile-display-name`/`profile-email` can both be present in the DOM
        and blank. Every `navigate()` in this suite is a full page reload
        (`driver.get`), so this window reopens on *every* `open()` call, not
        just the first.

        Anchored on the email field rather than the display name: email is a
        required field on every authenticated account, so its value going
        non-empty is a durable "the fetch resolved" signal, whereas a real
        display name could in principle be blank server-side.
        """
        self.poll(timeout).until(
            lambda d: (d.find_element(*self.EMAIL_INPUT).get_attribute("value") or "") != ""
        )

    def get_display_name(self) -> str:
        """Return the current value of the display-name field."""
        self.wait_for_profile_loaded()
        el = self.wait_for_element(self.DISPLAY_NAME_INPUT)
        return el.get_attribute("value") or ""

    def set_display_name(self, name: str) -> None:
        """Clear and type a new display name.

        Uses Ctrl+A instead of .clear() because React controlled inputs
        do not reliably clear with the WebDriver clear() method.
        """
        from selenium.webdriver.common.keys import Keys

        field = self.wait_for_element(self.DISPLAY_NAME_INPUT)
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(name)

    def get_email(self) -> str:
        """Return the (read-only) email value."""
        self.wait_for_profile_loaded()
        el = self.wait_for_element(self.EMAIL_INPUT)
        return el.get_attribute("value") or ""

    def is_email_disabled(self) -> bool:
        """Check if the email field is disabled."""
        el = self.wait_for_element(self.EMAIL_INPUT)
        return el.get_attribute("disabled") == "true"

    def click_profile_save(self) -> None:
        """Click the profile save button."""
        btn = self.wait_for_element_clickable(self.PROFILE_SAVE_BUTTON)
        self.scroll_and_click(btn)

    # ── Security section ────────────────────────────────────────────────

    def is_current_password_visible(self) -> bool:
        """Check if the current-password field is visible (only for local accounts).

        Gated on the same `providers` fetch :meth:`get_linked_providers` is:
        `SecuritySettingsGroup.tsx` derives `hasLocalProvider` from `providers`,
        which starts at `[]` and is populated only once `loadProviders()`'s
        `listProviders()` call resolves. The field carries no loading
        indicator of its own, so a bare read right after `open(section="security")`
        cannot tell "the fetch is still in flight" from "this account has no
        local provider" -- anchored on the linked-provider list settling
        first, the same signal :meth:`get_linked_providers` waits on.
        """
        self.await_presence(self.PROVIDER_NAMES)
        elements = self.driver.find_elements(*self.CURRENT_PASSWORD_INPUT)
        return len(elements) > 0 and elements[0].is_displayed()

    def enter_current_password(self, password: str) -> None:
        """Type into the current-password field."""
        field = self.wait_for_element(self.CURRENT_PASSWORD_INPUT)
        field.clear()
        field.send_keys(password)

    def enter_new_password(self, password: str) -> None:
        """Type into the new-password field."""
        field = self.wait_for_element(self.NEW_PASSWORD_INPUT)
        field.clear()
        field.send_keys(password)

    def click_change_password(self) -> None:
        """Click the change-password button."""
        btn = self.wait_for_element_clickable(self.CHANGE_PASSWORD_BUTTON)
        self.scroll_and_click(btn)

    def is_change_password_button_enabled(self) -> bool:
        """Check if the change-password button is enabled."""
        btn = self.find_present(self.CHANGE_PASSWORD_BUTTON)
        return btn.is_enabled()

    def get_linked_providers(self) -> list[str]:
        """Return the list of linked auth provider names.

        Scoped to the page's own subtree (see :attr:`PROVIDER_NAMES`): the
        unscoped read returned the Sidebar's nav labels as well, so
        "at least one provider is listed" held on the navigation alone and the
        ``len(providers) <= 1`` branch of TC-REQ-023-029 could never be taken.

        Anchored on :meth:`await_presence`: `providers` starts at `[]` and is
        populated only once `loadProviders()`'s `listProviders()` call
        resolves (a `useEffect` fired on every mount), and this page renders
        no loading indicator or empty-state testid for that gap -- a bare
        `find_elements` right after `open(section="security")` cannot tell "the
        fetch is still in flight" from "the demo user genuinely has no linked
        providers", which is exactly what `test_linked_providers_displayed`
        asserts on. An empty list after the full budget is still a genuine
        negative.
        """
        items = self.await_presence(self.PROVIDER_NAMES)
        return [item.text for item in items if item.is_displayed()]

    def get_unlink_buttons(self) -> list[WebElement]:
        """Return all unlink-provider buttons."""
        return self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='unlink-provider-']")

    # ── Snackbar helpers ────────────────────────────────────────────────

    def wait_for_success_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for and return the text of a success snackbar."""
        el = self.poll(timeout).until(EC.visibility_of_element_located(self.SNACKBAR_SUCCESS))
        return el.text

    def wait_for_error_snackbar(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Wait for and return the text of an error snackbar."""
        el = self.poll(timeout).until(EC.visibility_of_element_located(self.SNACKBAR_ERROR))
        return el.text
