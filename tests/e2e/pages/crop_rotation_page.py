"""Page object for the Crop Rotation page."""

from __future__ import annotations

import time
from contextlib import suppress

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import BasePage, IMPLICIT_WAIT_EQUIVALENT


class CropRotationPage(BasePage):
    """Interact with the Crop Rotation page (``/stammdaten/crop-rotation``)."""

    PATH = "/stammdaten/crop-rotation"

    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    # The main family picker was refactored from a MUI <Select> to a MUI
    # <Autocomplete>; its clickable trigger is the inner combobox <input>.
    # Scope by the testid — the page has a second combobox (filter-nutrient-
    # demand) so a bare role='combobox' locator would be ambiguous. The dialog
    # target picker below is still a real MUI <Select>.
    FAMILY_SELECT = (By.CSS_SELECTOR, "[data-testid='from-family-select'] input")
    SUCCESSOR_LIST = (By.CSS_SELECTOR, ".MuiList-root .MuiListItem-root")
    #: The successor rows addressed by the product's own per-successor testid
    #: (`CropRotationPage.tsx`: ``successor-family-link-<family_key>``) instead
    #: of by MUI class structure. :data:`SUCCESSOR_LIST` matches *any* MUI list
    #: item on the page and says nothing about what it is; this one cannot
    #: resolve to anything but a successor.
    SUCCESSOR_ITEMS = (By.CSS_SELECTOR, "[data-testid^='successor-family-link-']")
    ADD_SUCCESSOR_BTN = (By.CSS_SELECTOR, "[data-testid='add-successor-button']")
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # Dialog locators -- addressed by the dialog's own data-testid rather than a
    # bare role='dialog'. Below the `md` breakpoint (mobile AND tablet) the
    # sidebar Drawer is `temporary` + `keepMounted`, so its paper also carries
    # role='dialog' and wins the document-order lookup. See base_page.
    DIALOG = (By.CSS_SELECTOR, "[data-testid='crop-rotation-dialog']")
    #: The dialog's target picker is a real MUI ``Select``; it is driven through
    #: ``open_select_by_testid`` / ``select_option_by_label`` rather than through
    #: a locator here, because those verify the open and the committed value.
    DIALOG_TARGET_SELECT_TESTID = "to-family-select"
    DIALOG_WAIT_YEARS = (By.CSS_SELECTOR, "[data-testid='wait-years-input'] input")
    DIALOG_CREATE_BTN = (
        By.XPATH,
        "//*[@data-testid='crop-rotation-dialog']//button[contains(text(), 'Erstellen')]",
    )
    DIALOG_CANCEL_BTN = (
        By.XPATH,
        "//*[@data-testid='crop-rotation-dialog']//button[contains(text(), 'Abbrechen')]",
    )

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> CropRotationPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    def get_title(self) -> str:
        return self.wait_for_element(self.PAGE_TITLE).text

    def select_family(self, family_name: str) -> None:

        self.close_mui_dropdown()
        select = self.wait_for_element_clickable(self.FAMILY_SELECT)
        self.scroll_and_click(select)
        self.wait_for_element_visible((By.CSS_SELECTOR, "li[role='option']"), timeout=10)
        # Autocomplete options render family name + scientific name in stacked
        # <Typography> blocks (multi-line o.text), so match Selenium-side on
        # normalised text rather than an XPath contains() that can't see the
        # newline. See _find_option.
        option = self._find_option(family_name)
        self.click_menu_option(option)
        # Wait for options to be removed from DOM (natural close after selection)
        self.poll(5).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "li[role='option']")) == 0
        )
        self.wait_for_successor_content()

    #: `CropRotationPage.tsx` derives `successorsPending = selectedKey !== '' &&
    #: selectedKey !== loadedKey`, so selecting a family genuinely unmounts the
    #: successor list behind a `LoadingSkeleton` for the length of the fetch --
    #: it re-mounts as either `SUCCESSOR_ITEMS` (>=1 row) or `EMPTY_STATE`
    #: (`successors.length === 0`), never neither. This used to be a fixed
    #: `time.sleep(1)`, the forbidden pattern `e2e-test-stability` singles out:
    #: too short on a loaded CI runner leaves callers reading the *previous*
    #: family's successors (or a bare skeleton), too long wastes the same
    #: second on every single selection.
    def wait_for_successor_content(self, timeout: int = IMPLICIT_WAIT_EQUIVALENT) -> None:
        """Wait until the successor list for the selected family has settled.

        Deliberately does not raise -- an *anchor*, not an assertion; a family
        with no rotation successors at all must still be observable through
        `EMPTY_STATE` rather than turned into a timeout.
        """
        with suppress(AssertionError):
            self.wait_for_any_present(
                (self.SUCCESSOR_ITEMS, self.EMPTY_STATE),
                "crop rotation successor list",
                timeout=timeout,
            )

    def _find_option(self, name: str):
        """Return the open-listbox option matching *name* (whitespace-normalised)."""
        target = " ".join(name.split())
        deadline = time.time() + 10
        while time.time() < deadline:
            for option in self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']"):
                # ``textContent``, not ``.text``: WebElement.text yields only
                # *rendered* text, so an option scrolled outside the popover's
                # visible area (MUI auto-scrolls an open Select to its selected
                # item, pushing leading entries out of view) reads back as ""
                # and would never match. See base_page.select_option_by_label.
                otext = " ".join((option.get_attribute("textContent") or "").split())
                if otext == target or target in otext or otext in target:
                    return option
            time.sleep(0.2)
        raise AssertionError(f"Option matching '{name}' not found in the dropdown")

    def get_family_options(self) -> list[str]:
        self.close_mui_dropdown()
        select = self.wait_for_element_clickable(self.FAMILY_SELECT)
        self.scroll_and_click(select)
        self.wait_for_element_visible((By.CSS_SELECTOR, "li[role='option']"), timeout=10)
        options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
        # ``textContent``, not ``.text``: an option scrolled outside the open
        # popover's visible area reads back as "" via WebElement.text (MUI
        # scrolls to the selected item, pushing leading entries out of view).
        # The old ``if o.text`` filter silently dropped those entries from the
        # result instead of surfacing them -- see #801.
        texts = [" ".join((o.get_attribute("textContent") or "").split()) for o in options]
        self.close_mui_dropdown()
        return texts

    def get_successor_count(self) -> int:
        """Return the number of rows in the successor list.

        Anchored on :meth:`wait_for_successor_content` -- every current call
        site already reaches it anchored, via :meth:`select_family`, but the
        reader carries its own wait too rather than depending on that
        discipline: :meth:`wait_for_any_present` returns at once when the
        content has already settled, so this costs nothing on the happy path.
        """
        self.wait_for_successor_content()
        return len(self.driver.find_elements(*self.SUCCESSOR_LIST))

    def get_successor_names(self) -> list[str]:
        """Return the rendered text of every listed rotation successor.

        Read off the product's own ``successor-family-link-*`` element, one line
        per successor, joined into a single string per row.

        The predecessor read ``.MuiListItemText-primary`` inside every
        `SUCCESSOR_LIST` item -- and `CropRotationPage` renders **no**
        `ListItemText` at all: its successor rows are a `ListItemButton` holding
        plain `Typography`. Every call therefore raised
        ``NoSuchElementException`` as soon as the list had a row, i.e. exactly
        when the caller had something to check. That is a reader that cannot
        address its target, not a list that is empty, and the difference is the
        whole point of reading it (#956).
        """
        return self.retry_on_stale(
            lambda: [
                " ".join((item.get_attribute("textContent") or "").split())
                for item in self.driver.find_elements(*self.SUCCESSOR_ITEMS)
            ]
        )

    def click_add_successor(self) -> None:
        self.close_mui_dropdown()
        time.sleep(0.5)  # Wait for MUI animation to complete before clicking
        btn = self.wait_for_element_clickable(self.ADD_SUCCESSOR_BTN)
        self.scroll_and_click(btn)
        self.wait_for_element_visible(self.DIALOG)

    def is_dialog_create_button_enabled(self) -> bool:
        btn = self.find_present(self.DIALOG_CREATE_BTN)
        return btn.is_enabled()

    def select_dialog_target(self, family_name: str) -> None:
        """Pick the dialog's target family by its rendered label.

        Structurally identical to `CompanionPlantingPage.select_dialog_target`
        (same `TextField select` with ``MenuItem value={key}``), and migrated for
        the same reason: the predecessor opened a mousedown-only Select with a
        coordinate click, matched an unscoped ``li[role='option']`` on the
        translated label, clicked a possibly-repositioning popover at
        coordinates, and verified nothing.
        """
        self.close_mui_dropdown()
        self.open_select_by_testid(self.DIALOG_TARGET_SELECT_TESTID)
        self.select_option_by_label(family_name)

    def get_dialog_target_options(self) -> list[str]:
        self.close_mui_dropdown()
        self.open_select_by_testid(self.DIALOG_TARGET_SELECT_TESTID)
        # Keeps the predecessor's 10s budget for the options to render, and its
        # loud failure when none ever do: `open_select_in` deliberately tolerates
        # a legitimately empty listbox (2s), which would turn a slow render into
        # an empty read and let the caller skip for the wrong reason.
        self.wait_for_element_visible(self.OPTIONS, timeout=10)
        options = self.driver.find_elements(*self.OPTIONS)
        # ``textContent``, not ``.text`` -- see get_family_options above.
        texts = [" ".join((o.get_attribute("textContent") or "").split()) for o in options]
        self.close_mui_dropdown()
        return texts

    def set_dialog_wait_years(self, years: str) -> None:
        # MUI controlled number input + useState default: el.clear() drops the
        # DOM value but React-state survives, so plain send_keys() concatenates
        # ("3" + "4" = "34"). clear_and_fill() syncs the React state via the
        # native value-setter + input/change events.
        el = self.wait_for_element_clickable(self.DIALOG_WAIT_YEARS)
        self.clear_and_fill(el, years)

    def get_dialog_wait_years_value(self) -> str:
        """Return the current value of the wait-years input in the successor dialog."""
        el = self.find_present(self.DIALOG_WAIT_YEARS)
        return el.get_attribute("value") or ""

    def click_dialog_create(self) -> None:
        self.close_mui_dropdown()
        btn = self.wait_for_element_clickable(self.DIALOG_CREATE_BTN)
        self.scroll_and_click(btn)

    def click_dialog_cancel(self) -> None:
        self.close_mui_dropdown()
        btn = self.wait_for_element_clickable(self.DIALOG_CANCEL_BTN)
        self.scroll_and_click(btn)
