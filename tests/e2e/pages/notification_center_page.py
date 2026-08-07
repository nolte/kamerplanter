"""Page object for the notification centre (bell + drawer, REQ-030).

The notification centre is not a standalone route: it lives in the AppBar as
a bell IconButton (``NotificationBell.tsx``) that opens a right-anchored MUI
Drawer (``NotificationDrawer.tsx``).  This page object encapsulates the bell,
its unread badge, and the drawer's list of notification cards.

Locators reference the data-testid attributes defined in
``src/frontend/src/components/layout/NotificationBell.tsx`` and
``src/frontend/src/components/layout/NotificationDrawer.tsx``.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .base_page import DEFAULT_TIMEOUT, BasePage


class NotificationCenterPage(BasePage):
    """Interact with the notification bell and its drawer."""

    # ── Bell / badge ────────────────────────────────────────────────────
    BELL = (By.CSS_SELECTOR, "[data-testid='notification-bell']")
    BELL_BADGE = (By.CSS_SELECTOR, "[data-testid='notification-bell'] .MuiBadge-badge")

    # ── Drawer ──────────────────────────────────────────────────────────
    DRAWER = (By.CSS_SELECTOR, "[data-testid='notification-drawer']")
    DRAWER_CLOSE = (By.CSS_SELECTOR, "[data-testid='notification-drawer-close']")
    MARK_ALL_READ = (By.CSS_SELECTOR, "[data-testid='mark-all-read-btn']")
    LOAD_MORE = (By.CSS_SELECTOR, "[data-testid='notification-load-more']")

    # ── List / cards ────────────────────────────────────────────────────
    LIST = (By.CSS_SELECTOR, "[data-testid='notification-drawer'] [role='list']")
    LIST_ITEMS = (By.CSS_SELECTOR, "[data-testid='notification-drawer'] [role='listitem']")
    NOTIFICATION_CARDS = (By.CSS_SELECTOR, "[data-testid^='notification-card-']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    # ── Drawer open / close ─────────────────────────────────────────────

    def open_drawer(self) -> NotificationCenterPage:
        """Click the notification bell and wait for the drawer to appear."""
        self.wait_for_element_clickable(self.BELL).click()
        self.wait_for_element_visible(self.DRAWER)
        return self

    def close_drawer(self) -> None:
        """Close the drawer and wait for it to hide.

        The close button sits in the top-right of the drawer header, where the
        AppBar user avatar overlaps its hit-point, so a plain ``.click()`` can be
        intercepted. Fall back to the keyboard: a MUI temporary Drawer closes on
        ``Escape``. This keeps the close robust without touching the layout.
        """
        from selenium.common.exceptions import (
            ElementClickInterceptedException,
            TimeoutException,
        )
        from selenium.webdriver.common.keys import Keys

        try:
            self.wait_for_element_clickable(self.DRAWER_CLOSE).click()
        except ElementClickInterceptedException, TimeoutException:
            self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        try:
            self.wait_for_element_hidden(self.DRAWER)
        except TimeoutException:
            # A late-arriving interception may have swallowed the first attempt —
            # send Escape once more and require the drawer to be gone.
            self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            self.wait_for_element_hidden(self.DRAWER)

    def is_drawer_open(self) -> bool:
        """Return True if the notification drawer is currently visible."""
        elements = self.driver.find_elements(*self.DRAWER)
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Unread badge ────────────────────────────────────────────────────

    def get_unread_badge_count(self) -> int:
        """Return the unread count shown on the bell's badge.

        The badge is ``invisible`` (MUI class ``MuiBadge-invisible``) when the
        count is 0, in which case 0 is returned.  ``max=99`` means counts above
        99 render as ``'99+'``; the trailing ``+`` is stripped and 99 returned.
        """
        badges = self.driver.find_elements(*self.BELL_BADGE)
        if not badges:
            return 0
        badge = badges[0]
        classes = badge.get_attribute("class") or ""
        if "MuiBadge-invisible" in classes:
            return 0
        text = (badge.text or "").strip().rstrip("+")
        if not text:
            return 0
        try:
            return int(text)
        except ValueError:
            return 0

    def is_bell_present(self) -> bool:
        """Return True if the notification bell is rendered in the AppBar."""
        return len(self.driver.find_elements(*self.BELL)) > 0

    # ── Notification cards ──────────────────────────────────────────────

    #: The per-notification "Erledigt" action (``NotificationDrawer.tsx:408``),
    #: rendered once per *actionable* care/task notification.
    ACTION_DONE_BUTTONS = (By.CSS_SELECTOR, "[data-testid^='notification-action-done-']")

    def get_notification_cards(self) -> list[WebElement]:
        """Return all rendered ``notification-card-{key}`` elements."""
        return self.driver.find_elements(*self.NOTIFICATION_CARDS)

    def get_action_done_buttons(self) -> list[WebElement]:
        """Return every actionable 'Erledigt' button, once the drawer has loaded.

        Waiting is the point. ``NotificationDrawer`` refetches on **every**
        opening (a ``useEffect`` on ``open`` calling ``loadNotifications(0,
        false)``, with ``notifications`` starting out as ``[]``), so at the
        instant the drawer becomes visible there are provably no cards yet. A
        bare ``find_elements`` there answers ``[]`` for "the fetch is still in
        flight", which is indistinguishable from "no notification is
        actionable" — TC-REQ-030-014 asserted on exactly that difference and
        failed on all three ``full`` profiles of run 31113673507, once #835
        removed the implicit wait that had been granting the read 3 s.

        An empty list after the full budget is still a genuine negative, so the
        Soll assertion this feeds keeps failing when the feature is absent.
        """
        return self.await_presence(self.ACTION_DONE_BUTTONS)

    @staticmethod
    def _key_from_testid(testid: str) -> str:
        """Extract the notification key from a ``notification-card-{key}`` testid."""
        prefix = "notification-card-"
        return testid[len(prefix) :] if testid.startswith(prefix) else testid

    def get_notification_keys(self) -> list[str]:
        """Return the keys of all rendered notification cards, in DOM order."""
        keys: list[str] = []
        for card in self.get_notification_cards():
            testid = card.get_attribute("data-testid") or ""
            if testid.startswith("notification-card-"):
                keys.append(self._key_from_testid(testid))
        return keys

    def has_notification(self, key: str) -> bool:
        """Return True if a notification card for *key* is rendered."""
        return (
            len(
                self.driver.find_elements(
                    By.CSS_SELECTOR, f"[data-testid='notification-card-{key}']"
                )
            )
            > 0
        )

    def get_notification_card(self, key: str) -> WebElement:
        """Return the notification card element for a specific key."""
        return self.wait_for_element((By.CSS_SELECTOR, f"[data-testid='notification-card-{key}']"))

    def get_notification_text(self, key: str) -> str:
        """Return the visible text of a notification card (title + body + time)."""
        return self.get_notification_card(key).text

    def is_unread(self, key: str) -> bool:
        """Best-effort check whether a notification is unread.

        Unread cards render at full opacity with an ``action.hover`` background
        and a bold title; read cards dim to ~0.7 opacity with a transparent
        background.  This inspects the card's computed ``opacity`` (>= 0.9 is
        treated as unread).  The style-derived signal is heuristic — when a
        reliable answer is required, prefer ``get_unread_badge_count()``, which
        reflects the authoritative server count.
        """
        card = self.get_notification_card(key)
        opacity = self.driver.execute_script(
            "return window.getComputedStyle(arguments[0]).opacity;", card
        )
        try:
            return float(opacity) >= 0.9
        except TypeError, ValueError:
            return True

    def click_notification(self, key: str) -> None:
        """Click a notification's action area (marks it read and navigates)."""
        action = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='notification-action-{key}']")
        )
        self.scroll_and_click(action)

    # ── Bulk / pagination actions ───────────────────────────────────────

    def has_mark_all_read(self) -> bool:
        """Return True if the 'mark all read' button is rendered (unread exist)."""
        return len(self.driver.find_elements(*self.MARK_ALL_READ)) > 0

    def mark_all_read(self) -> None:
        """Click the 'mark all read' button in the drawer header."""
        self.wait_and_click(self.MARK_ALL_READ)

    def has_load_more(self) -> bool:
        """Return True if the 'load more' button is currently rendered."""
        return len(self.driver.find_elements(*self.LOAD_MORE)) > 0

    def load_more(self) -> None:
        """Click the 'load more' button to fetch the next page of notifications."""
        self.scroll_and_click(self.wait_for_element_clickable(self.LOAD_MORE))

    # ── Waits ───────────────────────────────────────────────────────────

    def wait_for_drawer(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the notification drawer is visible."""
        self.wait_for_element_visible(self.DRAWER, timeout=timeout)
