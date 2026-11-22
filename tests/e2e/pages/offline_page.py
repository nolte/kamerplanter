"""Page objects for the offline surface of the garden plan (REQ-053 wave 9, WP 9.1-9.4; tested in WP 9.15).

* :class:`OfflinePlanPage` - the plan route read from the IndexedDB plan cache: the read-only view, the
  "Stand von" banner, the geometry lock (``GardenPlanRoute`` / ``ReadOnlyPlanView`` / ``CachedDataBanner``).
* :class:`OfflineFieldMode` - field mode with the offline write buffer: the cached bed sheet, a buffered "Erledigt",
  the note chip and its short form (``FieldBedSheet`` / ``FieldTaskSection`` / ``CareLogDialog``).
* :class:`OfflineSyncHost` - the app-bar host of the buffer: the "n nicht übertragen" chip, the sync progress and
  the conflict dialog (``OfflineSyncHost`` / ``ConflictDialog``).
* :class:`AccountMenu` - "Abmelden" in the app bar's account menu (full mode).

Hooks: ``data-testid`` only, every one of them present in ``src/frontend/src/features/gardenPlanner/offline/``,
``.../field/`` or ``src/layouts/MainLayout.tsx`` (``account-menu-button``, ``account-menu-email``,
``menu-logout``). State-changing helpers read their effect back and fail loudly when it never arrives
(`e2e-test-stability` §D); there is no retry loop and no sleep.
"""

from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage
from .field_mode_page import FieldModePage
from .garden_plan_page import GardenPlanPage


def _tid(testid: str) -> tuple[str, str]:
    return (By.CSS_SELECTOR, f"[data-testid='{testid}']")


def _text(element: WebElement) -> str:
    return " ".join((element.get_attribute("textContent") or "").split())


class OfflinePlanPage(GardenPlanPage):
    """The plan route while (or after) the plan came from the IndexedDB cache."""

    READ_ONLY = _tid("garden-plan-read-only")
    CACHED_BANNER = _tid("offline-cached-banner")
    GEOMETRY_LOCKED = _tid("garden-plan-geometry-locked")
    OFFLINE_MISS = _tid("garden-plan-offline-miss")
    BACK_LINK = _tid("garden-plan-back-link")

    LOGIN_EMAIL = (By.CSS_SELECTOR, "input[type='email']")
    CONNECTIVITY = _tid("connectivity-indicator")

    def reload_plan(self, site_key: str) -> None:
        """Reload the document (the browser's reload) and return once the editor of *site_key* is back."""
        self.driver.refresh()
        self.wait_for_content(self.EDITOR, f"garden plan editor of site {site_key} after a reload")
        self.wait_for_element(self.SVG)

    def reload_offline(self, what: str) -> str:
        """Reload while offline; ``"login"`` or ``"frame"`` - which app shell rendered (never the browser's error page).

        Full mode cannot restore a session offline and shows the login form; light mode shows the app frame with
        the connectivity indicator. Neither exists on Chrome's offline error page.
        """
        self.driver.refresh()
        state = self.wait_for_settled(
            {"login": self.LOGIN_EMAIL, "frame": self.CONNECTIVITY},
            f"{what}: the app shell offline",
            timeout=30,
            require_no_skeleton=False,
        )
        return state.branch

    def manifest_link(self) -> str:
        """The ``href`` of the document's ``<link rel="manifest">``; loud when there is none."""
        href = self.driver.execute_script(
            "var l = document.querySelector(\"link[rel='manifest']\"); return l ? l.href : null;"
        )
        if not href:
            raise AssertionError("the document links no web app manifest")
        return str(href)

    def leave_to_site(self, site_key: str) -> None:
        """ "Zurück zum Standort" (an in-app link); return once the URL left the plan route."""
        self.wait_and_click(self.BACK_LINK)
        try:
            self.poll().until(
                lambda d: d.current_url.rstrip("/").endswith(f"/standorte/sites/{site_key}")
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"'Zurück zum Standort' did not lead to the site page; the URL is {self.driver.current_url!r}"
            ) from exc

    def go_back_to_plan(self, site_key: str) -> None:
        """The browser's Back button: a history step inside the single-page app, no document load."""
        self.driver.back()
        try:
            self.poll().until(
                lambda d: d.current_url.rstrip("/").endswith(f"/standorte/sites/{site_key}/plan")
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"Back did not return to the plan of {site_key}; the URL is {self.driver.current_url!r}"
            ) from exc

    def wait_for_read_only(self, what: str) -> str:
        """Wait for the cached plan's read-only view (or report the offline miss); the banner's text."""
        state = self.wait_for_settled(
            {"read_only": self.READ_ONLY, "miss": self.OFFLINE_MISS},
            f"{what}: the plan route offline",
            require_no_skeleton=False,
        )
        if state.branch != "read_only":
            raise AssertionError(
                f"{what}: the plan route shows the offline miss instead of the cached plan: "
                f"{self.text_of(self.OFFLINE_MISS)!r}"
            )
        return self.text_of(self.CACHED_BANNER)

    def is_read_only(self) -> bool:
        return self.is_present(self.READ_ONLY)

    def has_cached_banner(self) -> bool:
        return self.is_present(self.CACHED_BANNER)

    def wait_for_live_editor(self, what: str) -> None:
        """Wait until the editor replaced the read-only view (the plan was read from the server again)."""
        try:
            self.poll(timeout=30).until(
                lambda d: d.find_elements(*self.EDITOR) and not d.find_elements(*self.READ_ONLY)
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the read-only plan was not replaced by the editor once back online"
            ) from exc

    def drawn_object_keys(self) -> list[str]:
        """``data-plan-key`` of every plan object drawn in the read-only view (no tab stop there, so no role)."""
        view = self.wait_for_element(self.READ_ONLY)
        return self.driver.execute_script(
            "return Array.from(arguments[0].querySelectorAll('[data-plan-key]'))"
            ".filter(function (e) { return e.getAttribute('data-plan-kind') !== 'boundary'; })"
            ".map(function (e) { return e.getAttribute('data-plan-key'); });",
            view,
        )


class OfflineFieldMode(FieldModePage):
    """Field mode with the offline write buffer (WP 9.4)."""

    SHEET_OFFLINE = _tid("field-sheet-offline")
    SHEET_CACHED_BANNER = _tid("field-sheet-cached-banner")
    SHEET_OFFLINE_MISS = _tid("field-sheet-offline-miss")
    NOTE_DIALOG = _tid("care-log-dialog")
    NOTE_FIELD = _tid("care-log-note")
    NOTE_SUBMIT = _tid("care-log-submit")

    def wait_for_offline_capture_ready(self, what: str) -> None:
        """Wait until the open sheet loaded what an offline capture needs (``data-offline-capture-ready``).

        The buffer's code and the note/photo dialogs are lazy chunks the sheet loads while online
        (``preloadOfflineCapture``); going offline before that would test a race, not the buffer.
        """
        try:
            self.poll(timeout=30).until(
                lambda d: (
                    d.find_element(*self.SHEET).get_attribute("data-offline-capture-ready")
                    == "true"
                )
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the sheet never reported its offline capture code as loaded"
            ) from exc

    def tap_bed_offline(self, bed_key: str, what: str) -> str:
        """Tap a bed row while offline; return the sheet's "Stand von" banner once the cached sheet is shown."""
        self.wait_and_click(_tid(f"field-bed-row-{bed_key}"))
        self.wait_for_element(self.SHEET)
        state = self.wait_for_settled(
            {"cached": self.SHEET_CACHED_BANNER, "miss": self.SHEET_OFFLINE_MISS},
            f"{what}: the bed sheet offline",
            require_no_skeleton=False,
        )
        if state.branch != "cached":
            raise AssertionError(
                f"{what}: the bed sheet has no cached copy offline: "
                f"{_text(self.wait_for_element(self.SHEET_OFFLINE_MISS))!r}"
            )
        self.wait_for_element(self.TASKS)
        return _text(self.wait_for_element(self.SHEET_CACHED_BANNER))

    def snackbar_texts(self) -> list[str]:
        """Every notification snackbar's message on screen, top to bottom (an undo offer may still stand above)."""
        return [
            text for text in (_text(c) for c in self.driver.find_elements(*self.SNACKBAR)) if text
        ]

    def wait_for_snackbar_message(self, fragment: str, what: str, timeout: int = 60) -> str:
        """Wait until any snackbar's message contains *fragment*; that message."""
        found: list[str] = []

        def _shown(_d) -> bool:
            found[:] = [text for text in self.snackbar_texts() if fragment in text]
            return bool(found)

        try:
            self.poll(timeout=timeout).until(_shown)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: no snackbar names {fragment!r}; on screen: {self.snackbar_texts()}"
            ) from exc
        return found[0]

    def sheet_offline_text(self) -> str:
        return _text(self.wait_for_element(self.SHEET_OFFLINE))

    def wait_for_done_queued(self, task_key: str, what: str) -> str:
        """The task row's "Wartet auf Übertragung" (the completion is in the buffer); its text."""
        try:
            return _text(self.wait_for_element(_tid(f"field-done-queued-{task_key}")))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: task {task_key} shows no 'Wartet auf Übertragung' after the buffered completion"
            ) from exc

    def is_done_offered(self, task_key: str) -> bool:
        return self.is_present(_tid(f"field-done-{task_key}"))

    def open_note(self) -> None:
        """The note chip of the quick protocol; return once its short form is open."""
        self.tap_chip("note")
        self.wait_for_element_visible(self.NOTE_DIALOG)

    def submit_note(self, text: str, what: str) -> None:
        """Type *text* into the note field and press "Speichern"; return once the form closed (sent or buffered)."""
        field = self.wait_for_element_clickable(self.NOTE_FIELD)
        self.clear_and_fill(field, text)
        try:
            self.poll().until(lambda _d: (field.get_attribute("value") or "") == text)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the note field should hold {text!r}, it holds {field.get_attribute('value')!r}"
            ) from exc
        self.wait_and_click(self.NOTE_SUBMIT)
        try:
            self.wait_for_element_hidden(self.NOTE_DIALOG)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the note form did not close after 'Speichern'") from exc


class OfflineSyncHost(BasePage):
    """The buffer's chip in the app bar, the sync progress and the conflict dialog."""

    QUEUE_CHIP = _tid("offline-queue-chip")
    PROGRESS = _tid("offline-sync-progress")
    CONFLICT_DIALOG = _tid("offline-conflict-dialog")
    CONFLICT_EMPTY = _tid("offline-conflict-empty")
    CONFLICT_CLOSE = _tid("offline-conflict-close")
    ENTRIES = (By.CSS_SELECTOR, "[data-testid='offline-conflict-dialog'] li[data-status]")

    def queue_chip_text(self) -> str | None:
        """The chip's accessible name, ``None`` while the buffer holds nothing unsent (no chip then).

        The name, not the visible text: below ``sm`` the chip shows only the number next to its icon (#2815), its
        name stays "2 nicht übertragen".
        """
        found = self.driver.find_elements(*self.QUEUE_CHIP)
        return (found[0].get_attribute("aria-label") or _text(found[0])) if found else None

    def assert_app_bar_fits(self, what: str) -> None:
        """No horizontal overflow of the page or the app bar at the current width (#2815, 390 px)."""
        sizes = self.driver.execute_script(
            "const bar = document.querySelector('header .MuiToolbar-root');"
            "return {page: document.documentElement.scrollWidth, view: window.innerWidth,"
            " bar: bar ? bar.scrollWidth : 0, barView: bar ? bar.clientWidth : 0};"
        )
        assert sizes["page"] <= sizes["view"] and sizes["bar"] <= sizes["barView"], (
            f"{what}: the app bar overflows: {sizes}"
        )

    def wait_for_queue_chip(self, expected: str, what: str) -> str:
        try:
            self.poll().until(lambda _d: self.queue_chip_text() == expected)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the app bar should read {expected!r}, the chip reads {self.queue_chip_text()!r}"
            ) from exc
        return expected

    def wait_for_queue_chip_gone(self, what: str, timeout: int = 60) -> None:
        """Wait until the chip is gone (every entry sent or decided) - the sync's own end state."""
        try:
            self.poll(timeout=timeout).until(lambda _d: self.queue_chip_text() is None)
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: the buffer chip still reads {self.queue_chip_text()!r}"
            ) from exc

    def wait_for_conflict_entries(self, what: str, timeout: int = 60) -> list[dict[str, str]]:
        """Wait for the conflict dialog with at least one entry; ``[{id, status, text, reason}]`` of its entries."""
        try:
            self.poll(timeout=timeout).until(lambda d: d.find_elements(*self.ENTRIES))
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the conflict dialog did not open with an entry") from exc
        entries: list[dict[str, str]] = []
        for row in self.driver.find_elements(*self.ENTRIES):
            entry_id = (row.get_attribute("data-testid") or "")[len("offline-entry-") :]
            entries.append(
                {
                    "id": entry_id,
                    "status": row.get_attribute("data-status") or "",
                    "text": _text(row),
                    "reason": _text(row.find_element(*_tid(f"offline-entry-reason-{entry_id}"))),
                }
            )
        return entries

    def discard(self, entry_id: str, what: str) -> None:
        """ "Verwerfen" of one entry; return once it left the dialog (taken out of the buffer)."""
        self.wait_and_click(_tid(f"offline-entry-discard-{entry_id}"))
        try:
            self.wait_for_element_hidden(_tid(f"offline-entry-{entry_id}"))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: entry {entry_id} is still listed after 'Verwerfen'"
            ) from exc

    def close_conflicts(self) -> None:
        self.wait_and_click(self.CONFLICT_CLOSE)
        self.wait_for_element_hidden(self.CONFLICT_DIALOG)

    def is_conflict_dialog_open(self) -> bool:
        return self.is_present(self.CONFLICT_DIALOG)


class AccountMenu(BasePage):
    """The account menu of the app bar (full mode): "Abmelden"."""

    MENU_BUTTON = _tid("account-menu-button")
    LOGOUT_ITEM = _tid("menu-logout")
    LOGIN_EMAIL = (By.CSS_SELECTOR, "input[type='email']")

    EMAIL = _tid("account-menu-email")

    def signed_in_email(self) -> str:
        """The e-mail the account menu names (the signed-in user); the menu is closed again (Escape)."""
        self.wait_and_click(self.MENU_BUTTON)
        try:
            self.wait_for_element_visible(self.LOGOUT_ITEM)
        except TimeoutException as exc:
            raise AssertionError("the account menu did not open") from exc
        email = _text(self.wait_for_element(self.EMAIL))
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        try:
            self.wait_for_element_hidden(self.LOGOUT_ITEM)
        except TimeoutException as exc:
            raise AssertionError("the account menu did not close on Escape") from exc
        return str(email or "")

    def logout(self, what: str) -> None:
        """Open the account menu, choose "Abmelden"; return once the login form is on screen."""
        self.wait_and_click(self.MENU_BUTTON)
        try:
            item = self.wait_for_element_visible(self.LOGOUT_ITEM)
        except TimeoutException as exc:
            raise AssertionError(f"{what}: the account menu did not open with 'Abmelden'") from exc
        if _text(item) != "Abmelden":
            raise AssertionError(f"{what}: the logout item reads {_text(item)!r}, not 'Abmelden'")
        self.click_menu_option(item)
        try:
            self.poll(timeout=30).until(
                lambda d: "/login" in d.current_url and d.find_elements(*self.LOGIN_EMAIL)
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: 'Abmelden' did not end on the login form; the URL is {self.driver.current_url!r}"
            ) from exc


__all__ = ["AccountMenu", "OfflineFieldMode", "OfflinePlanPage", "OfflineSyncHost"]
