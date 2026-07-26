"""Base page object with common helpers for all pages."""

from __future__ import annotations

import re
import time
from pathlib import Path

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DEFAULT_TIMEOUT = 15

# German ``d.m.Y`` date, tolerant of zero-padded and numeric parts alike.
DE_DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")

# ── Dialog scoping ────────────────────────────────────────────────────────
# A MUI Dialog's paper carries ``role="dialog"`` -- but so does a *temporary*
# MUI Drawer's paper. Below the `md` breakpoint (900px, i.e. BOTH the mobile
# and the tablet profile) the Sidebar renders as `variant="temporary"` with
# `ModalProps={{ keepMounted: true }}`, so its paper is portalled to
# ``document.body`` at app mount and stays in the DOM with
# ``visibility: hidden`` while the drawer is closed.
#
# An unscoped ``div[role='dialog']`` therefore resolves to that invisible
# drawer paper FIRST (document order), and ``visibility_of_element_located``
# -- which uses ``find_element``, i.e. first match only -- never becomes true.
# CSS selector *lists* are no protection either: they also match in document
# order, so a ``[data-testid='x'], div[role='dialog']`` fallback chain still
# picks the drawer.
#
# Always scope dialog lookups to the MuiDialog subtree (or, better, to the
# dialog's own data-testid). The Drawer root is ``.MuiDrawer-root`` and never
# carries ``.MuiDialog-root``, so this scoping is exact.
DIALOG_SELECTOR = ".MuiDialog-root [role='dialog']"
DIALOG_XPATH = "//*[contains(@class, 'MuiDialog-root')]//*[@role='dialog']"


class BasePage:
    """Shared helpers inherited by every page object."""

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    # ── Navigation ────────────────────────────────────────────────────────

    def navigate(self, path: str) -> None:
        """Navigate to *path* relative to the base URL."""
        self.driver.get(f"{self.base_url}{path}")

    # ── Waits ─────────────────────────────────────────────────────────────

    def wait_for_element(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> WebElement:
        """Wait until an element is present in the DOM and return it."""
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))

    def wait_for_element_visible(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> WebElement:
        """Wait until an element is visible and return it."""
        return WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))

    def wait_for_element_clickable(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> WebElement:
        """Wait until an element is clickable and return it."""
        return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(locator))

    def wait_for_element_hidden(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> None:
        """Wait until an element is no longer visible (e.g. MUI Dialog fade-out)."""
        WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located(locator))

    #: The Suspense/query loading placeholder every page renders while its data
    #: (or, for a lazily-imported route, its chunk) is still in flight.
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    #: `ErrorDisplay` — the "this entity could not be loaded" branch of a detail
    #: page. Rendered *instead of* the page root, so it is one of the two
    #: legitimate settled states of a detail route.
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")
    #: `ErrorPage` — the whole-route error/not-found surface (404, 500, ...).
    ERROR_PAGE = (By.CSS_SELECTOR, "[data-testid='error-page']")

    def wait_for_loading_complete(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until no ``[data-testid='loading-skeleton']`` is visible.

        **This is a weak signal and proves nothing about the target content.**
        It is kept because ~340 call sites pair it with a durable wait that does
        the real work (typically ``wait_for_element(self.PAGE)`` in a page
        object's ``open()``); on its own it must not gate a read.

        Two reasons it under-delivers, both observed in this suite:

        * ``invisibility_of_element_located`` is satisfied by an element that is
          **absent**, and it cannot tell "the skeleton has not mounted yet" from
          "the skeleton is gone because loading finished". Right after
          ``navigate()`` the document is loaded but React has not yet reached the
          suspended route, so no skeleton exists and this returns *immediately* —
          `e2e-test-stability` §D calls exactly that ("a poll that can never
          distinguish 'not yet loaded' from 'correctly absent'") an invalid
          assertion. Observed on TC-REQ-001-005, where the body read back held
          nothing but the app chrome (``Mein Garten 16 M``) while
          ``NotFoundPage``'s lazy chunk was still resolving.
        * It says nothing about *which* branch a page then renders. A detail
          route settles into a page root **or** an `ErrorDisplay`; the skeleton
          being gone is common to both and to neither-yet.

        Use :meth:`wait_for_any_present` (or a plain
        :meth:`wait_for_element` on the content itself) to key the read on the
        content that must actually be there.
        """
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(self.LOADING_SKELETON)
        )

    def wait_for_any_present(
        self,
        locators: tuple[tuple[str, str], ...],
        what: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> tuple[str, str]:
        """Wait until at least one of *locators* is in the DOM; return which one.

        The strong sibling of :meth:`wait_for_loading_complete`: it waits for a
        state that *proves the content exists* rather than for the absence of a
        placeholder, and it fails loudly — naming every locator it probed — when
        none appears.

        The disjunction is the point. A route legitimately settles into more
        than one shape (a detail page's own root **or** an `ErrorDisplay` for an
        unknown key), so waiting for just one of them would either time out on a
        valid outcome or, if skipped entirely, read a half-rendered page. This
        lets a caller name every settled state it accepts and still be gated on
        one of them having been reached.
        """
        matched: list[tuple[str, str]] = []

        def _any(driver: WebDriver) -> bool:
            for locator in locators:
                if driver.find_elements(*locator):
                    matched.append(locator)
                    return True
            return False

        try:
            WebDriverWait(self.driver, timeout).until(_any)
        except TimeoutException as exc:
            probed = ", ".join(f"{by}={value!r}" for by, value in locators)
            raise AssertionError(
                f"{what}: none of the expected settled states appeared within "
                f"{timeout}s (probed {probed}). The route is most likely still "
                "resolving its lazily-imported chunk -- reading the page here "
                "would assert against the app chrome alone."
            ) from exc
        return matched[0]

    def wait_for_url_contains(self, fragment: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the current URL contains *fragment*."""
        WebDriverWait(self.driver, timeout).until(EC.url_contains(fragment))

    # ── Queries ───────────────────────────────────────────────────────────

    def find_by_testid(self, testid: str) -> WebElement:
        """Shorthand for finding an element by its ``data-testid``."""
        return self.driver.find_element(By.CSS_SELECTOR, f"[data-testid='{testid}']")

    def find_all_by_testid(self, testid: str) -> list[WebElement]:
        """Return all elements matching the given ``data-testid``."""
        return self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{testid}']")

    def is_present(self, locator: tuple[str, str]) -> bool:
        """Return True if at least one element matching *locator* exists in the DOM."""
        return len(self.driver.find_elements(*locator)) > 0

    def get_text_stable(self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT) -> str:
        """Return text of *locator*, retrying on StaleElementReferenceException."""
        deadline = time.time() + timeout
        while True:
            try:
                el = self.wait_for_element_visible(
                    locator, timeout=min(5, max(1, int(deadline - time.time())))
                )
                return el.text
            except StaleElementReferenceException:
                if time.time() >= deadline:
                    raise
                time.sleep(0.2)

    def get_page_title(self) -> str:
        """Return the text content of the ``[data-testid='page-title']`` element."""
        return self.get_text_stable((By.CSS_SELECTOR, "[data-testid='page-title']"))

    def is_error_displayed(self) -> bool:
        """Check whether ``[data-testid='error-display']`` is visible."""
        elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='error-display']")
        return len(elements) > 0 and elements[0].is_displayed()

    def has_alert_notification(self) -> bool:
        """Check whether any ``[role='alert']`` notification is present (e.g. an error snackbar)."""
        return len(self.driver.find_elements(By.CSS_SELECTOR, "[role='alert']")) > 0

    def get_body_text(self) -> str:
        """Return the full text content of the page body (for keyword assertions)."""
        return self.driver.find_element(By.TAG_NAME, "body").text

    # ── Interactions ─────────────────────────────────────────────────────

    OPTIONS = (By.CSS_SELECTOR, "li[role='option']")
    LISTBOX = (By.CSS_SELECTOR, "[role='listbox']")

    def _wait_options_gone(self, timeout: float) -> bool:
        """Wait (bounded) until no ``li[role='option']`` is left; return the outcome."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*self.OPTIONS)) == 0
            )
            return True
        except TimeoutException:
            return False

    def close_mui_dropdown(self, timeout: int = 5) -> None:
        """Close any open MUI Select dropdown, or fail loudly if it stays open.

        Fails loudly by design: an open popover is a full-screen click-away
        overlay, so returning while it is still up pushes the failure onto the
        *next* interaction, which then reports "button not clickable" for a
        cause that is nowhere near it (observed in
        ``FAILURE_test_ended_cycle_spawns_no_new_instance.png``). The previous
        ``except TimeoutException: pass`` swallowed exactly that.

        The Escape key goes to the listbox rather than to ``<body>``: a blind
        body-level Escape is delivered to whatever modal currently has focus,
        so it closes the *surrounding dialog* when the popover happens to have
        closed itself in the meantime.
        """
        from selenium.webdriver.common.keys import Keys

        if not self.driver.find_elements(*self.OPTIONS):
            return  # Already closed

        # After an option click MUI closes the popover on its own — give the
        # close a bounded moment before touching the keyboard at all.
        if self._wait_options_gone(2):
            return

        # Dropdown is genuinely open (opened without selecting) — close it via
        # Escape on the menu itself, which is where MUI's key handler sits.
        target = next(iter(self.driver.find_elements(*self.LISTBOX)), None)
        if target is None:
            target = next(iter(self.driver.find_elements(*self.OPTIONS)), None)
        if target is None:
            return  # raced to closed between the two lookups
        try:
            target.send_keys(Keys.ESCAPE)
        except (
            ElementNotInteractableException,
            StaleElementReferenceException,
        ):
            self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)

        if not self._wait_options_gone(timeout):
            raise AssertionError(
                f"MUI dropdown did not close within {timeout}s — "
                f"{len(self.driver.find_elements(*self.OPTIONS))} option(s) are "
                "still in the DOM. Its click-away overlay will intercept every "
                "following click."
            )

    #: Controls whose menu/popover opens on ``mousedown`` rather than on
    #: ``click``: the MUI Select display div (``[role='combobox']`` since v5,
    #: ``.MuiSelect-select`` as the legacy class hook).
    MENU_TRIGGER_CSS = "[role='combobox'], .MuiSelect-select"

    def opens_on_mousedown(self, element: WebElement) -> bool:
        """Return True if *element* is a control that opens on ``mousedown``."""
        return bool(
            self.driver.execute_script(
                "return arguments[0].matches(arguments[1]);",
                element,
                self.MENU_TRIGGER_CSS,
            )
        )

    def dispatch_menu_trigger_open(self, element: WebElement) -> None:
        """Dispatch a ``mousedown``/``mouseup`` pair straight onto a menu trigger.

        MUI opens a Select **only** from its ``onMouseDown`` handler -- there is
        no ``onClick`` opener. A JS ``element.click()`` dispatches a lone
        ``click`` event, so it can never open one; it merely *reports* success.
        This sends the pair a real pointer would.

        Deliberately dispatched on the element rather than through
        ``ActionChains``: ActionChains is coordinate-based and, unlike
        ``WebElement.click()``, performs no interactability hit-test, so under
        an overlay it silently delivers the events to the overlay -- the same
        class of silent-success defect this replaces. Also deliberately without
        a trailing ``click``: MUI has already opened the menu on ``mousedown``,
        and a bubbling ``click`` can be read as a click-away.
        """
        self.driver.execute_script(
            "var el = arguments[0];"
            "['mousedown', 'mouseup'].forEach(function (type) {"
            "  el.dispatchEvent(new MouseEvent(type, {"
            "    bubbles: true, cancelable: true, view: window, button: 0,"
            "  }));"
            "});",
            element,
        )

    def scroll_into_view(self, element: WebElement) -> None:
        """Scroll *element* into view, inside **every** scrollable ancestor.

        ``scrollIntoView`` walks the whole ancestor chain, not just the
        document's scrolling element, which is what makes it the right
        primitive for content inside an ``overflow: auto`` container (the
        Sidebar's nav box, a MUI Popover paper).
        """
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            element,
        )

    def is_displayed_in_scroll_container(self, element: WebElement) -> bool:
        """Return whether *element* is displayed once scrolled into view.

        Selenium's displayedness check reports ``False`` both for "not
        rendered" and for "rendered but clipped by a scrollable ancestor", so a
        bare ``is_displayed()`` on content inside an ``overflow: auto``
        container silently answers a question about *rendering* with the
        container's *scroll position*. Scrolling first collapses the two cases
        onto the one the caller actually asks about.

        A stale element is genuinely gone, hence ``False``.
        """
        try:
            self.scroll_into_view(element)
            return element.is_displayed()
        except StaleElementReferenceException:
            return False

    def click_menu_option(self, element: WebElement) -> None:
        """Click an open menu's option coordinate-independently.

        A MUI ``MenuItem`` activates from its ``onClick`` handler, so a
        synthetic ``element.click()`` drives it exactly as a real pointer does.
        This is **not** in tension with :meth:`dispatch_menu_trigger_open`: a
        Select *trigger* opens only from ``onMouseDown``, which a JS ``click()``
        never dispatches, so there the same call would be a silent no-op.

        Coordinate independence is the whole point. A native click resolves the
        element's centre and *then* dispatches at those coordinates; in between,
        the menu can still move — and both motion sources are JavaScript layout
        effects rather than CSS transitions, so no animation or reduced-motion
        setting removes them:

        * ``Menu`` scrolls its paper to the selected item on open
          (``handleEntering`` -> ``MenuList`` under the default
          ``variant='selectedMenu'``). That moves every option while leaving the
          paper's own ``top``/``left``/``height`` bit-identical.
        * ``Popover`` clamps a menu that does not fit below its anchor upward.

        Observed on the mobile profile as a uniform, directional two-option
        offset: clicks aimed at ``FREQ=WEEKLY`` committed ``FREQ=MONTHLY``, and
        one aimed at the last option committed nothing at all. Dispatching on
        the already-resolved element cannot miss.
        """
        self._dispatch_click(element)

    def _dispatch_click(self, element: WebElement) -> None:
        """Dispatch a synthetic ``click`` straight onto the resolved *element*.

        The one place this suite's coordinate-independent clicks go through, so
        the soundness argument lives in exactly one docstring per activation
        model (:meth:`click_menu_option`, :meth:`click_coordinate_free`) instead
        of being re-derived at every call site.
        """
        self.driver.execute_script("arguments[0].click();", element)

    def click_coordinate_free(self, element: WebElement) -> None:
        """Click a ``click``-activated control without going through coordinates.

        Use this for the submit/confirm button of a long in-page form. A native
        ``WebElement.click()`` resolves the element's in-view centre point and
        only *then* dispatches at those coordinates, and on a 393x852 viewport a
        form's action row sits at the very bottom of a page far taller than the
        viewport: ``scrollIntoView({block: 'center'})`` cannot centre it (the
        document is already scrolled to its maximum), so the button ends up
        within a few pixels of the fold, where any residual scrolling between
        the interactability check and the dispatch is enough to put the
        resolved point off the button. Nothing raises when that happens -- the
        hit-test passed, the events went out, and no ``submit`` event was ever
        produced.

        Observed on the mobile profile as the whole ``TestTaskUpdatePropagation``
        class failing with a still-dirty form, an enabled submit button and no
        field errors (run ``20260725_113337``), while every desktop profile
        wrote its eight ``PUT /tasks/{key}`` 200s.

        Sound for a ``<button type='submit'>``: ``HTMLElement.click()`` runs the
        element's default activation behaviour, i.e. it submits the owning form
        exactly as a pointer does. Explicitly **not** sound for a MUI Select
        trigger, which opens only from ``onMouseDown`` -- a lone ``click`` there
        is a silent no-op, so those are rejected here and must go through
        :meth:`dispatch_menu_trigger_open` / :meth:`open_select_in`.

        A disabled control is rejected for the same reason: the browser drops
        the default action, so the call would report success without having
        done anything.
        """
        if self.opens_on_mousedown(element):
            raise AssertionError(
                "click_coordinate_free() was called on a control that opens on "
                "mousedown (a MUI Select trigger). A synthetic click cannot open "
                "it and would silently report success -- use open_select() / "
                "open_select_by_testid() instead."
            )
        self.scroll_into_view(element)
        if not element.is_enabled():
            raise AssertionError(
                "click_coordinate_free() was called on a disabled control: the "
                "browser suppresses its default action, so the click would be a "
                "silent no-op. Wait for the control to become enabled first."
            )
        self._dispatch_click(element)

    def wait_and_click_coordinate_free(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> None:
        """Wait until *locator* is clickable, then click it coordinate-free.

        The counterpart of :meth:`wait_and_click` for form submits; see
        :meth:`click_coordinate_free` for why coordinates are the hazard there.
        """
        self.click_coordinate_free(self.wait_for_element_clickable(locator, timeout=timeout))

    def scroll_and_click(self, element: WebElement) -> None:
        """Scroll an element into view and click it, with a sound JS fallback.

        The fallback is chosen by target: a bare JS ``click()`` is fine for
        buttons and links, but is a *silent no-op* on a MUI Select trigger
        (which opens on ``mousedown``), so those get an explicit
        mousedown/mouseup pair instead — see
        :meth:`dispatch_menu_trigger_open`. Menu *options* never belong here:
        they are clicked coordinate-independently via
        :meth:`click_menu_option`.
        """
        self.scroll_into_view(element)
        try:
            element.click()
        except ElementNotInteractableException, ElementClickInterceptedException:
            if self.opens_on_mousedown(element):
                self.dispatch_menu_trigger_open(element)
            else:
                self._dispatch_click(element)

    def wait_and_click(self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until *locator* is clickable, scroll it into view, then click it.

        The scroll step is not cosmetic: below the `sm` breakpoint MUI dialogs
        render ``fullScreen``, so a form's action row is the last child of a
        scrolling ``DialogContent`` and sits *below the fold*.
        ``element_to_be_clickable`` is satisfied by a displayed+enabled element
        regardless of whether it is inside the viewport, so a naked ``.click()``
        on such a button raises ``ElementNotInteractableException`` (or, once
        ChromeDriver's own scroll puts it under the fixed AppBar,
        ``ElementClickInterceptedException``).

        Use this for every submit/cancel-style action; ``scroll_and_click``
        stays available for callers that already hold the element.

        Exception: the submit button of a **long in-page form** (a detail page's
        edit tab, not a dialog) is scroll-clamped against the bottom of the
        document, where the coordinate dispatch this helper ends in silently
        misses. Those go through :meth:`wait_and_click_coordinate_free`.
        """
        self.scroll_and_click(self.wait_for_element_clickable(locator, timeout=timeout))

    # ── Robust form-select / table helpers (prefer dedicated testids) ──────
    # These replace brittle `.MuiSelect-select` clicks, i18n-fragile
    # `contains(text(), label)` option XPaths, and position-based `cells[N]`
    # access with the dedicated data-testids emitted by FormSelectField and
    # DataTable. They fall back to the legacy selectors so page objects can be
    # migrated incrementally.

    #: Trigger sub-selectors probed inside a select container, in order: the
    #: ARIA display (stable across MUI versions), then the legacy class hook.
    SELECT_TRIGGER_SUBSELECTORS = ("[role='combobox']", ".MuiSelect-select")

    def is_select_open(self, trigger: WebElement) -> bool:
        """Return True while *trigger*'s dropdown is open.

        Keyed on the trigger's own ``aria-expanded`` (durable, and true even for
        a menu that legitimately renders zero options), with the rendered
        listbox as a second signal for triggers that don't carry the attribute
        or that went stale on the re-render the open caused.
        """
        if self._aria_expanded(trigger) == "true":
            return True
        return len(self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")) > 0

    @staticmethod
    def _aria_expanded(trigger: WebElement) -> str:
        """Return *trigger*'s ``aria-expanded``, or ``'<stale>'`` if it unmounted."""
        try:
            return trigger.get_attribute("aria-expanded") or ""
        except StaleElementReferenceException:
            return "<stale>"

    def _settle_listbox(self, timeout: int = 2) -> None:
        """Wait until an opened dropdown's options are queryable.

        ``aria-expanded`` can be observed a beat before the portalled menu's
        ``li[role='option']`` nodes are queryable, which would make an
        immediately following ``find_elements`` return ``[]``. A Select whose
        option list is legitimately empty is not an error condition -- it stays
        open with zero options, so callers that require options assert on them
        and this returns.

        Deliberately no geometry-settling step: the menu's *position* stopped
        mattering once options are clicked on the resolved element rather than
        at resolved coordinates (:meth:`click_menu_option`). The removed guard
        compared the popover paper's ``top``/``left``/``height`` — which is
        blind to the dominant motion source, ``Menu`` scrolling *inside* that
        paper to the selected item, since that leaves the paper's own rect
        bit-identical. A guard that cannot see the motion it was built to catch
        only mis-attributes later failures.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*self.OPTIONS)) > 0
            )
        except TimeoutException:
            return

    def _wait_until_select_open(self, trigger: WebElement, timeout: int = 5) -> bool:
        """Wait (bounded) until *trigger*'s dropdown is open; return the outcome."""
        try:
            WebDriverWait(self.driver, timeout).until(lambda _d: self.is_select_open(trigger))
            return True
        except TimeoutException:
            return False

    def open_select(self, field_name: str) -> None:
        """Open a FormSelectField dropdown and verify that it actually opened."""
        self.open_select_in(f"[data-testid='form-field-{field_name}']", f"field '{field_name}'")

    def open_select_by_testid(self, testid: str) -> None:
        """Open a MUI Select addressed by the data-testid on its TextField root.

        MUI spreads ``...other`` onto the **root** ``FormControl`` (label +
        input + helper text), not onto the ``[role='combobox']`` display div, so
        a click on the root's centre can land on the label or the helper text —
        a silent no-op, because the ``<p>`` is a descendant of the clicked root
        and Chrome therefore raises no interception. Resolve the combobox first.
        """
        self.open_select_in(f"[data-testid='{testid}']", f"select '{testid}'")

    def open_select_in(self, container: str, what: str) -> None:
        """Open the MUI Select inside *container*, or fail loudly.

        Fails loudly by design: a helper that reports success without having
        opened anything pushes the failure to a later, unrelated line (the
        option lookup) and hides the real cause.
        """
        trigger: WebElement | None = None
        for sub in self.SELECT_TRIGGER_SUBSELECTORS:
            locator = (By.CSS_SELECTOR, f"{container} {sub}")
            if self.driver.find_elements(*locator):
                trigger = self.wait_for_element_clickable(locator)
                break
        if trigger is None:
            raise AssertionError(f"Select trigger for {what} not found")

        self.scroll_and_click(trigger)
        if self._wait_until_select_open(trigger):
            self._settle_listbox()
            return
        # The click did not open the menu (e.g. it was swallowed while the
        # trigger was still moving). Retry with the explicit mousedown pair.
        self.dispatch_menu_trigger_open(trigger)
        if self._wait_until_select_open(trigger):
            self._settle_listbox()
            return
        raise AssertionError(
            f"Select for {what} did not open (aria-expanded stayed "
            f"{self._aria_expanded(trigger)!r} and no li[role='option'] appeared)"
        )

    #: The Select display div of the dropdown that is currently open. Captured
    #: *before* the option click so the resulting value can be read back even
    #: when the caller gave no field name.
    OPEN_SELECT_TRIGGER = (
        By.CSS_SELECTOR,
        "[role='combobox'][aria-expanded='true'], .MuiSelect-select[aria-expanded='true']",
    )

    #: Reads the committed value of a MUI Select: its hidden
    #: ``.MuiSelect-nativeInput`` inside the same ``.MuiInputBase-root``.
    _SELECT_VALUE_FROM_TRIGGER = (
        "var el = arguments[0];"
        "var base = el.closest('.MuiInputBase-root') || el.parentElement;"
        "var input = base ? base.querySelector('input, select, textarea') : null;"
        "return input ? input.value : null;"
    )
    _SELECT_VALUE_FROM_CONTAINER = (
        "var root = document.querySelector(arguments[0]);"
        "if (!root) { return null; }"
        "var input = root.querySelector('input, select, textarea');"
        "return input ? input.value : null;"
    )

    def select_option_by_value(self, value: str, field_name: str | None = None) -> None:
        """Click an open dropdown option by its data-value and verify the effect.

        Waits briefly (bounded) for each candidate selector to become
        clickable rather than gating on an instant ``is_present`` check --
        the MUI popover open animation can still be in flight when this runs,
        so an unwaited check can miss an option that renders a beat later.

        The option is clicked via :meth:`click_menu_option` (a JS click on the
        already-resolved element), never at resolved coordinates: an open MUI
        menu still moves under its own layout effects, so a coordinate click
        lands on whichever option slid into that spot.

        Reads the resulting Select value back and raises on a mismatch. Without
        that, this helper returned unconditionally after *dispatching* a click,
        so a click that landed on a neighbouring option was reported as a
        success -- and the two-attempt retry in :meth:`choose_select_value` was
        inert, because nothing ever raised. The expectation is taken from the
        clicked option's own ``data-value``, not from *value*, because the option
        testid suffix and the value differ for the empty option
        (``form-option-<field>-none`` / ``-empty`` both commit ``''``).
        """
        trigger = next(iter(self.driver.find_elements(*self.OPEN_SELECT_TRIGGER)), None)
        selectors = []
        if field_name:
            selectors.append(f"[data-testid='form-option-{field_name}-{value}']")
        selectors.append(f"li[role='option'][data-value='{value}']")
        for selector in selectors:
            locator = (By.CSS_SELECTOR, selector)
            try:
                el = self.wait_for_element_clickable(locator, timeout=3)
            except TimeoutException:
                continue
            expected = el.get_attribute("data-value")
            self.click_menu_option(el)
            self.close_mui_dropdown()
            self._verify_select_committed(trigger, expected, value, field_name)
            return
        raise AssertionError(f"Option with value '{value}' not found in the open dropdown")

    def select_option_by_label(self, label: str) -> None:
        """Pick the open dropdown's option whose visible text matches *label*.

        For a MUI ``Select`` whose ``MenuItem``s carry an entity key as their
        value and a human-readable, translated string as their text (the species
        and family pickers of the companion-planting / crop-rotation dialogs).
        The label is resolved to the option's own ``data-value`` here and the
        actual selection then goes through :meth:`select_option_by_value`, so it
        inherits both guarantees the hand-rolled predecessors lacked: the click
        is dispatched on the resolved element (an open MUI popover still
        repositions, so a coordinate click lands on whichever option slid into
        the spot) and the committed value is read back.

        Matching is whitespace-normalised, because an option renders its label
        across two stacked ``Typography`` blocks (``"Name\\nGenus species"``) —
        which is also why an XPath ``contains(text(), …)`` could not see it: the
        XPath string-value carries no newline. An exact match wins over a
        substring match irrespective of DOM order, so a label that is the prefix
        of another entry cannot shadow the requested one.
        """
        target = " ".join(label.split())
        options = self.driver.find_elements(*self.OPTIONS)
        # ``textContent``, not ``.text``: WebElement.text yields only *rendered*
        # text, so an option scrolled outside the popover's visible area reads
        # back as "". MUI scrolls an open Select to its selected item, which
        # pushes the leading entries out of view -- observed on the tablet
        # profile as ``Rendered options: ['', '', 'Osmosewasser', ...]`` for a
        # dropdown whose first entry was the one being asked for.
        rendered = [" ".join((o.get_attribute("textContent") or "").split()) for o in options]
        exact = [o for o, text in zip(options, rendered) if text == target]
        partial = [
            o
            for o, text in zip(options, rendered)
            if text and text != target and (target in text or text in target)
        ]
        for option in exact + partial:
            value = option.get_attribute("data-value")
            if value is None:
                raise AssertionError(
                    f"The option matching '{label}' carries no data-value, so the "
                    "selection could not be verified. Address a MUI MenuItem "
                    "rendered inside a Select."
                )
            self.select_option_by_value(value)
            return
        raise AssertionError(
            f"No option matching '{label}' in the open dropdown. Rendered options: {rendered}"
        )

    def _read_select_value(self, trigger: WebElement | None, field_name: str | None) -> str | None:
        """Return the committed value of the Select that was just operated on."""
        if field_name:
            value = self.driver.execute_script(
                self._SELECT_VALUE_FROM_CONTAINER,
                f"[data-testid='form-field-{field_name}']",
            )
            if value is not None:
                return str(value)
        if trigger is None:
            return None
        try:
            value = self.driver.execute_script(self._SELECT_VALUE_FROM_TRIGGER, trigger)
        except StaleElementReferenceException:
            return None
        return None if value is None else str(value)

    def _verify_select_committed(
        self,
        trigger: WebElement | None,
        expected: str | None,
        requested: str,
        field_name: str | None,
    ) -> None:
        """Raise unless the clicked option actually became the Select's value."""
        what = f"field '{field_name}'" if field_name else "the open select"
        if expected is None:
            raise AssertionError(
                f"The option clicked for {what} (requested '{requested}') carries "
                "no data-value, so the selection cannot be verified. Address a "
                "MUI MenuItem rendered inside a Select."
            )
        actual = self._read_select_value(trigger, field_name)
        if actual is None:
            raise AssertionError(
                f"Cannot read back the value of {what} after selecting "
                f"'{requested}': no native input was found for it. Verifying the "
                "click is mandatory — an unverified option click silently "
                "selects a neighbouring entry when the popover is still moving."
            )
        # Multi-selects commit a comma-joined list.
        if actual != expected and expected not in actual.split(","):
            raise AssertionError(
                f"Selecting '{requested}' on {what} did not take effect: expected "
                f"the value {expected!r}, but the field holds {actual!r}. The "
                "click most likely landed on a neighbouring option."
            )

    def choose_select_value(self, field_name: str, value: str) -> None:
        """Open a FormSelectField and pick the option with the given value.

        Retries once, re-opening the select, if the listbox never appeared or
        the option click didn't register on the first attempt -- a bounded
        guard against the MUI popover animation racing the option lookup
        (observed as a one-off timeout on an otherwise-passing code path,
        TC-006-J077). The retry spans the *open* too: ``open_select`` verifies
        the dropdown really opened and raises when it did not, and
        ``select_option_by_value`` verifies the clicked option really became
        the value -- so this retry only became reachable once those two started
        raising, rather than reporting success unconditionally.
        """
        from contextlib import suppress

        last_error: AssertionError | None = None
        for _attempt in range(2):
            try:
                self.open_select(field_name)
                self.select_option_by_value(value, field_name)
                return
            except AssertionError as exc:
                last_error = exc
                # Recovery only: a stuck popover here is a *symptom* of the
                # failure being carried in `last_error`, which is the one worth
                # reporting. `close_mui_dropdown` stays loud for every other
                # caller.
                with suppress(AssertionError):
                    self.close_mui_dropdown()
        assert last_error is not None
        raise last_error

    def get_row_cell_text(self, row: WebElement, col_id: str) -> str:
        """Return a DataTable row cell's text addressed by column id (not position).

        Resolves the *same* column id in both layouts: ``cell-<col_id>`` on the
        desktop table, else `MobileCard`'s ``card-field-<col_id>`` /
        ``card-chip-<col_id>``.

        Raises when the row demonstrably *is* a `MobileCard` (it carries a
        ``card-title``) but keys none of them: returning ``''`` there makes an
        assertion like "the supplemental column must be empty" pass without
        ever having read anything.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        if cells:
            return cells[0].text
        field = self.get_card_field(row, col_id)
        if field is not None:
            return field
        chips = row.find_elements(By.CSS_SELECTOR, f"[data-testid='card-chip-{col_id}']")
        if chips:
            return chips[0].text
        if row.find_elements(*self.CARD_TITLE):
            raise AssertionError(
                f"Column '{col_id}' is not readable on this MobileCard: it keys "
                f"neither 'card-field-{col_id}' nor 'card-chip-{col_id}'. Key the "
                "field/chip in the page's mobileCardRenderer, or read the column "
                "on a desktop-only test."
            )
        return ""

    # ── Layout-tolerant DataTable row access ──────────────────────────────
    # `DataTable` emits ``[data-testid='data-table-row']`` in BOTH layouts, but
    # only the desktop table renders ``<td data-testid='cell-<col_id>'>``. Below
    # the table's `mobileBreakpoint` it renders a `MobileCard` inside the same
    # row container. Position-based `cells[0]` access is doubly wrong there: it
    # yields `[]` on mobile, and on desktop it picks whatever column happens to
    # come first (a favourite star, a conditionally prepended chip column, ...)
    # rather than the identifying one.
    #
    # `MobileCard` now carries its own hooks (UI-NFR-022 R-016):
    #   ``card-title``            -- always present
    #   ``card-subtitle``         -- only when the caller sets a subtitle
    #   ``card-field-<col_id>``   -- only when the caller keys the field
    #   ``card-chip-<col_id>``    -- only when the caller keys the chip
    # The last two use exactly the `Column.id` of the column they mirror, so a
    # single key addresses the same value in both layouts (``cell-<id>`` on the
    # desktop table, ``card-field-<id>``/``card-chip-<id>`` on the card).

    DATA_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    #: Container `DataTable` emits *only* in the mobile card layout.
    DATA_TABLE_CARDS = (By.CSS_SELECTOR, "[data-testid='data-table-cards']")

    def is_card_layout(self) -> bool:
        """Return True while a `DataTable` renders its mobile card layout.

        `DataTable` wraps the cards in ``[data-testid='data-table-cards']`` and
        renders that container in no other branch, so this is a durable signal
        -- no viewport arithmetic, no breakpoint duplication in the tests.
        """
        return len(self.driver.find_elements(*self.DATA_TABLE_CARDS)) > 0

    def require_table_layout(self, what: str) -> None:
        """Fail loudly when a column-position-based read is attempted on cards.

        Position-based readers (``cells[N]``) have no meaning in the card
        layout: `MobileCard` renders no ``<td>`` -- it addresses values by
        column id (``card-field-<id>`` / ``card-chip-<id>``), never by
        position -- so such a reader silently yields ``[]``/``""`` there, and
        an assertion like "the deleted entry is no longer listed" then passes
        for the wrong reason. Callers that genuinely need column positions must
        be desktop-only; this guard turns the silent pass into a hard failure.
        """
        if self.is_card_layout():
            raise AssertionError(
                f"{what} reads DataTable cells by column position, but the mobile "
                "card layout is active (no <td> cells). Use a layout-tolerant "
                "reader (get_row_primary_text / get_row_text_fragments) or mark "
                "the test 'requires_desktop'."
            )

    def get_row_text_fragments(self, row: WebElement) -> list[str]:
        """Return a row's readable text fragments in *both* layouts.

        Desktop: one entry per ``<td>``. Mobile card layout: one entry per
        rendered text line of the card, except that the card's title and
        subtitle are taken from their ``card-title``/``card-subtitle`` hooks
        via ``textContent`` -- `MobileCard` renders both ``noWrap``, so the
        *rendered* line drops the ellipsised tail of a long value (e.g. the
        ``— watering`` suffix of a care-reminder task name).

        Reading the remaining lines from the card's rendered text is deliberate
        and not a fallback: it is what keeps this reader complete for the many
        `MobileCard` callers that key no ``card-field-*``/``card-chip-*`` yet.
        Intended for membership assertions ("… is/is not listed").
        """
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells:
            return [c.text for c in cells]
        lines = [line.strip() for line in (row.text or "").splitlines() if line.strip()]
        exact = [
            self._text_content(els[0])
            for locator in (self.CARD_TITLE, self.CARD_SUBTITLE)
            if (els := row.find_elements(*locator))
        ]
        # `MobileCard` renders title and subtitle as the card's first text
        # lines (the optional `leading` slot carries a preview image, no text),
        # so the exact readings replace exactly those leading entries.
        return exact + lines[len(exact) :]

    def get_all_row_text_fragments(self) -> list[list[str]]:
        """Return :meth:`get_row_text_fragments` for every visible DataTable row."""
        return [
            self.get_row_text_fragments(row)
            for row in self.driver.find_elements(*self.DATA_TABLE_ROWS)
        ]

    #: `MobileCard`'s own hooks. ``card-title`` is unconditional, so its
    #: absence means "this row renders no card" -- never "the title is
    #: missing". ``card-subtitle`` is emitted only when a subtitle is set.
    CARD_TITLE = (By.CSS_SELECTOR, "[data-testid='card-title']")
    CARD_SUBTITLE = (By.CSS_SELECTOR, "[data-testid='card-subtitle']")
    #: Any keyed card chip, used to tell an *unadopted* page (no keyed chips at
    #: all) apart from a row whose conditional chip simply is not rendered.
    CARD_ANY_CHIP = (By.CSS_SELECTOR, "[data-testid^='card-chip-']")

    @staticmethod
    def _text_content(element: WebElement) -> str:
        """Return an element's ``textContent``, not its rendered text.

        `MobileCard` renders title and subtitle as ``<Typography noWrap>``
        (``overflow: hidden; text-overflow: ellipsis``), so the tail of a long
        value — e.g. the ``— watering`` suffix of a care-reminder task name —
        is not part of the element's *rendered* text and ``WebElement.text``
        drops it. ``textContent`` carries the full string.
        """
        return (element.get_attribute("textContent") or "").strip()

    def get_card_title(self, row: WebElement) -> str:
        """Return the `MobileCard` title of *row*, or ``''`` outside the card layout."""
        els = row.find_elements(*self.CARD_TITLE)
        return self._text_content(els[0]) if els else ""

    def get_card_subtitle(self, row: WebElement) -> str:
        """Return the `MobileCard` subtitle of *row*, or ``''`` if it has none."""
        els = row.find_elements(*self.CARD_SUBTITLE)
        return self._text_content(els[0]) if els else ""

    def get_card_field(self, row: WebElement, col_id: str) -> str | None:
        """Return the card's ``card-field-<col_id>`` value, or ``None`` if unkeyed.

        ``None`` is the "this caller has not keyed that field yet" signal and
        must be handled by the caller -- returning ``''`` would be
        indistinguishable from a field that is rendered but empty.
        """
        els = row.find_elements(By.CSS_SELECTOR, f"[data-testid='card-field-{col_id}']")
        return self._text_content(els[0]) if els else None

    def get_row_chip_texts(self, row: WebElement) -> list[str]:
        """Return the labels of a row's *keyed* chips, in DOM order.

        Only keyed chips (``card-chip-<col_id>``) count: the previous
        ``.MuiChip-label`` sweep returned every chip of the row, including
        those a caller renders outside the chip slot, so an index into the
        result addressed a different chip per page and per row. Use
        :meth:`get_column_chip_texts` when the column is known -- it is exact.
        """
        return [c.text for c in row.find_elements(*self.CARD_ANY_CHIP)]

    #: MUI Chip palette suffixes, in the order they are probed.
    CHIP_COLORS = ("success", "warning", "error", "info", "secondary", "primary", "default")

    def _column_chip_scopes(self, row: WebElement, col_id: str) -> list[WebElement]:
        """Return the elements holding column *col_id*'s chip(s) in either layout.

        Desktop: the ``cell-<col_id>`` ``<td>``. Card layout: the keyed chip
        ``card-chip-<col_id>`` -- which `MobileCard` clones the hook straight
        onto, so the returned element *is* the Chip.

        Fails loudly when the row exposes neither hook: on the desktop table
        that means the column is not rendered at all, and in the card layout
        that the page's `MobileCard` caller has not keyed its chips yet. The
        previous behaviour -- falling back to *every* chip of the row --
        answered a question about column *A* with the chips of column *B*.

        A row that merely lacks this one conditional chip while carrying other
        keyed chips is a legitimate empty result, not a failure.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        if cells:
            return cells
        chips = row.find_elements(By.CSS_SELECTOR, f"[data-testid='card-chip-{col_id}']")
        if chips:
            return chips
        if not row.find_elements(*self.CARD_ANY_CHIP):
            raise AssertionError(
                f"Column '{col_id}' is not addressable on this row: it renders "
                f"neither a 'cell-{col_id}' <td> (desktop table) nor any keyed "
                "'card-chip-*' (mobile card layout). Either the column is not "
                "rendered at all, or the page's mobileCardRenderer still passes "
                "its chips as a plain node instead of a keyed { id, content } list."
            )
        return []

    CHIP_ROOT_CSS = ".MuiChip-root"

    def _chip_elements(self, scope: WebElement) -> list[WebElement]:
        """Return the Chips *scope* holds, or *scope* itself when it is one.

        `MobileCard` clones ``card-chip-<id>`` straight onto the Chip, so a
        card scope *is* the chip; a desktop ``cell-<id>`` ``<td>`` wraps it.
        ``.MuiChip-root`` is used here only to separate chips from a cell's
        other content **inside an already hook-addressed scope** -- never to
        locate a column, which is what the removed fallbacks did.
        """
        if "MuiChip-root" in (scope.get_attribute("class") or ""):
            return [scope]
        return scope.find_elements(By.CSS_SELECTOR, self.CHIP_ROOT_CSS)

    def get_column_chip_texts(self, col_id: str) -> list[str]:
        """Return the chip labels of column *col_id*, across all visible rows."""
        texts: list[str] = []
        for row in self.driver.find_elements(*self.DATA_TABLE_ROWS):
            for scope in self._column_chip_scopes(row, col_id):
                texts.extend(c.text for c in self._chip_elements(scope))
        return texts

    def get_column_chip_colors(self, col_id: str) -> list[str]:
        """Return the MUI palette name of column *col_id*'s chips, across all rows.

        The palette is only ever expressed as MUI's ``MuiChip-color<Palette>``
        class -- there is no product hook for a chip's colour -- so this reads
        the class by design. What it no longer does is *find* the chip by
        class: the scope comes from ``cell-<col_id>`` / ``card-chip-<col_id>``.
        """
        colors: list[str] = []
        for row in self.driver.find_elements(*self.DATA_TABLE_ROWS):
            for scope in self._column_chip_scopes(row, col_id):
                colors.extend(self._chip_colors(self._chip_elements(scope)))
        return colors

    def _chip_colors(self, chips: list[WebElement]) -> list[str]:
        """Map each Chip onto its MUI palette name (``MuiChip-colorSuccess`` -> ``success``)."""
        colors: list[str] = []
        for chip in chips:
            cls = chip.get_attribute("class") or ""
            colors.append(
                next(
                    (c for c in self.CHIP_COLORS if f"MuiChip-color{c.capitalize()}" in cls),
                    "default",
                )
            )
        return colors

    def get_row_chip_colors(self, row: WebElement) -> list[str]:
        """Return the MUI palette name of each chip in a row, in DOM order."""
        return self._chip_colors(self._chip_elements(row))

    def get_row_primary_text(self, row: WebElement, col_id: str) -> str:
        """Return a row's identifying text, addressed by column id in both layouts.

        Reads ``[data-testid='cell-<col_id>']`` when the desktop table is
        rendered, otherwise the column's ``card-field-<col_id>`` and finally
        the card's ``card-title`` -- fed from the same field the identifying
        column renders on every page using this helper. The card title is
        addressed by its hook rather than as "the first text line", which
        happened to work only as long as no `leading`/`trailing` slot carried
        text.

        Fails loudly in the card layout when the row exposes no ``card-title``
        at all: that is a `MobileCard` that did not render, and returning
        ``''`` there turns "the deleted entry is gone" into a pass for the
        wrong reason.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        if cells:
            return cells[0].text
        field = self.get_card_field(row, col_id)
        if field is not None:
            return field
        titles = row.find_elements(*self.CARD_TITLE)
        if not titles:
            raise AssertionError(
                f"Row exposes neither a 'cell-{col_id}' <td> nor a 'card-field-"
                f"{col_id}' nor a 'card-title' -- it renders no readable "
                "identifier in either layout."
            )
        return self._text_content(titles[0])

    def get_column_texts(self, col_id: str) -> list[str]:
        """Return the identifying text of every visible DataTable row."""
        return [
            self.get_row_primary_text(row, col_id)
            for row in self.driver.find_elements(*self.DATA_TABLE_ROWS)
        ]

    def find_row_by_text(self, needle: str) -> WebElement | None:
        """Return the first DataTable row whose rendered text contains *needle*.

        Layout-tolerant: matches against the row/card text rather than against
        a positional cell, so it behaves identically for the desktop table and
        the mobile card list.
        """
        for row in self.driver.find_elements(*self.DATA_TABLE_ROWS):
            if needle in (row.text or ""):
                return row
        return None

    # ── Guarded row/card activation ───────────────────────────────────────
    # Two defects that kept re-entering the suite as per-page copies:
    #
    #   1. ``self.scroll_and_click(rows[index])`` clicks the row's *geometric
    #      centre*. A `DataTable` row is a click target as a whole, but its
    #      cells routinely contain their own interactive nodes -- a plant chip
    #      rendered as a `RouterLink`, a favourite `IconButton`, an actions
    #      menu -- and every one of them calls ``e.stopPropagation()``, so the
    #      row's own ``onRowClick`` never fires. Whether the centre lands on
    #      such a node is pure geometry: at 1920px the row is wide enough that
    #      it misses, at 820px it hits. Observed on the tablet profile as
    #      TC-REQ-004-J090 landing on the *plant* detail page instead of the
    #      watering-log detail (run ``20260725_173409``) -- the click did
    #      navigate, just to the chip's target.
    #   2. ``if index < len(rows): ...`` with no ``else`` turns an out-of-range
    #      index into a silent no-op that reports success; the assertion that
    #      follows then tests the page the test never left.
    #
    # Both are fixed once, here: address the row through one named, inert
    # column, and fail loudly on an index that does not exist.

    def require_index(self, items: list[WebElement], index: int, what: str) -> WebElement:
        """Return ``items[index]``, or fail loudly naming index and count.

        The loud failure is the point: a guarded interaction that quietly does
        nothing when the index is out of range cannot fail, so the assertion
        after it silently asserts against the previous page.
        """
        if not 0 <= index < len(items):
            raise AssertionError(
                f"{what}: index {index} is out of range -- {len(items)} "
                "element(s) are rendered. Doing nothing here would report "
                "success and leave the following assertion testing the page "
                "the test never left."
            )
        return items[index]

    #: Descendants that swallow a row click. `DataTable` puts ``onRowClick`` on
    #: the row, but a link/button inside a cell handles the click first and
    #: (in every current caller) calls ``stopPropagation``, so the row handler
    #: never runs. A cell containing one of these is not a usable click target.
    ROW_CLICK_SWALLOWERS = (
        "a[href], button, [role='button'], [role='link'], "
        "input, select, textarea, .MuiChip-clickable"
    )

    def _swallows_row_click(self, element: WebElement) -> bool:
        """Return True if *element* is, or contains, a row-click swallower."""
        return bool(
            self.driver.execute_script(
                "var el = arguments[0], sel = arguments[1];"
                "return el.matches(sel) || el.querySelector(sel) !== null;",
                element,
                self.ROW_CLICK_SWALLOWERS,
            )
        )

    def resolve_row_click_target(self, row: WebElement, col_id: str) -> WebElement:
        """Return the inert element through which *row* is activated.

        Resolves the *same* column id in both layouts, exactly as
        :meth:`get_row_primary_text` does its reading: ``cell-<col_id>`` on the
        desktop table, else `MobileCard`'s ``card-field-<col_id>``, else the
        card's unconditional ``card-title``. The click then bubbles to the
        row's own ``onRowClick`` from a point that is not a function of the
        viewport width.

        Fails loudly rather than falling back to the row element, on all three
        conditions that would otherwise reintroduce the geometry bet:

        * the column is not rendered at all (wrong column id for this table),
        * it is rendered but not displayed (a ``hideBelowBreakpoint`` column at
          a narrow viewport -- a JS click would still *fire* on a
          ``display: none`` ``<td>`` and report success, which is exactly the
          unsound-fallback class `e2e-test-stability` §G forbids),
        * it contains an interactive node, i.e. the caller picked a column that
          swallows the row click on some rows.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        source = f"cell-{col_id}"
        if not cells:
            cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='card-field-{col_id}']")
            source = f"card-field-{col_id}"
        if not cells:
            cells = row.find_elements(*self.CARD_TITLE)
            source = "card-title"
        if not cells:
            raise AssertionError(
                f"Row exposes neither a 'cell-{col_id}' <td> (desktop table) "
                f"nor a 'card-field-{col_id}' nor a 'card-title' (mobile card "
                "layout), so there is no column-addressed click target. Name a "
                "column this table actually renders."
            )
        target = next((c for c in cells if c.is_displayed()), None)
        if target is None:
            raise AssertionError(
                f"The click target '{source}' exists but is not displayed. "
                "Most likely the column carries `hideBelowBreakpoint` and this "
                "viewport hides it; pick a column rendered at every breakpoint."
            )
        if self._swallows_row_click(target):
            raise AssertionError(
                f"The click target '{source}' is, or contains, an interactive "
                "node (link, button or clickable chip). Those call "
                "stopPropagation, so the row's own onRowClick would never "
                "fire -- pick a column that renders inert content."
            )
        return target

    def click_row_via_column(self, row: WebElement, col_id: str) -> None:
        """Activate *row* by clicking its inert *col_id* cell.

        Use instead of clicking the row element: see the section comment above
        for why the row's geometric centre is a viewport-dependent bet.

        `scroll_and_click`'s JS fallback is sound for this target class. The
        resolved cell/field has no default activation behaviour of its own --
        the only thing that must happen is that a bubbling ``click`` reaches
        the row's React ``onRowClick``, which ``HTMLElement.click()`` produces
        exactly as a pointer does. It matters in the card layout, where a
        ``noWrap`` title can render wider than its clipping parent and the
        native click point can therefore fall outside it; Chrome then raises
        `ElementClickInterceptedException` and the fallback dispatches on the
        already-resolved element instead of guessing at coordinates.
        """
        self.scroll_and_click(self.resolve_row_click_target(row, col_id))

    def click_data_table_row(
        self,
        index: int,
        col_id: str,
        rows_locator: tuple[str, str] | None = None,
        what: str = "DataTable row",
    ) -> None:
        """Activate the *index*-th `DataTable` row through its *col_id* cell."""
        rows = self.driver.find_elements(*(rows_locator or self.DATA_TABLE_ROWS))
        self.click_row_via_column(self.require_index(rows, index, what), col_id)

    def clear_and_fill(self, element: WebElement, value: str) -> None:
        """Reliably clear an input element and type a new value.

        Uses JavaScript to clear the field value and dispatch native input/change
        events so that React controlled components pick up the change.  After
        the JS clear, verifies the field is actually empty — if React restored
        the old value, falls back to Ctrl+A to select all before typing so
        the new value replaces whatever is in the field.
        """
        from selenium.webdriver.common.keys import Keys

        self.driver.execute_script(
            "var el = arguments[0];"
            "var proto = el.tagName === 'TEXTAREA'"
            "  ? window.HTMLTextAreaElement.prototype"
            "  : window.HTMLInputElement.prototype;"
            "var nativeInputValueSetter = Object.getOwnPropertyDescriptor(proto, 'value').set;"
            "nativeInputValueSetter.call(el, '');"
            "el.dispatchEvent(new Event('input', {bubbles: true}));"
            "el.dispatchEvent(new Event('change', {bubbles: true}));",
            element,
        )
        time.sleep(0.15)

        # Verify the field was actually cleared — React may have restored the
        # old value from state before send_keys runs.
        current = element.get_attribute("value") or ""
        if current:
            element.send_keys(Keys.CONTROL + "a")
            time.sleep(0.05)

        element.send_keys(value)

    # ── Sidebar navigation ─────────────────────────────────────────────────

    SIDEBAR_ROOT = (By.CSS_SELECTOR, "[data-testid='sidebar']")
    SIDEBAR_TOGGLE = (By.CSS_SELECTOR, "[data-testid='sidebar-toggle']")
    SIDEBAR_PAPER = (By.CSS_SELECTOR, "[data-testid='sidebar'] .MuiDrawer-paper")

    def is_sidebar_open(self) -> bool:
        """Return True if the sidebar drawer's paper is actually visible."""
        papers = self.driver.find_elements(*self.SIDEBAR_PAPER)
        return len(papers) > 0 and papers[0].is_displayed()

    def ensure_sidebar_open(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Open the sidebar drawer if it is closed, and wait until it is visible.

        Viewport-aware and idempotent. Below the `md` breakpoint (900px --
        i.e. BOTH the mobile and the tablet profile) the Sidebar renders as a
        *temporary* Drawer with ``ModalProps={{ keepMounted: true }}``, so its
        nav items stay in the DOM while the drawer is closed, merely hidden via
        ``visibility: hidden``. `uiSlice` seeds ``sidebarOpen`` from
        ``window.innerWidth >= 768``, so at 393px the drawer starts closed.

        Any assertion on nav-item *visibility* must therefore open the drawer
        first -- a presence-only wait on the sidebar stays green and masks the
        closed drawer. Returns immediately when the paper is already visible
        (desktop `persistent` variant, or the tablet width where the drawer
        starts open).

        No-ops when no sidebar is mounted at all (e.g. the login route, which
        renders outside `MainLayout`) -- "the sidebar is missing" is a distinct
        condition that the caller's own assertion reports.
        """
        if self.is_sidebar_open() or not self.is_present(self.SIDEBAR_ROOT):
            return
        toggle = self.wait_for_element_clickable(self.SIDEBAR_TOGGLE, timeout=timeout)
        self.scroll_and_click(toggle)
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.SIDEBAR_PAPER)
        )

    def navigate_via_sidebar(self, path: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Navigate by clicking a sidebar link, simulating real user behavior.

        Falls back to direct URL navigation if the sidebar item is not visible
        (e.g. hidden by expertise level).
        """
        locator = (By.CSS_SELECTOR, f"[data-testid='nav-{path}']")
        items = self.driver.find_elements(*locator)
        if items and items[0].is_displayed():
            self.scroll_and_click(items[0])
            WebDriverWait(self.driver, timeout).until(EC.url_contains(path))
        else:
            self.navigate(path)

    # ── Expertise level helpers ─────────────────────────────────────────────

    SHOW_ALL_FIELDS_TOGGLE = (By.CSS_SELECTOR, "[data-testid='show-all-fields-toggle']")

    def expand_all_fields(self, timeout: int = 5) -> None:
        """Click the 'Show all fields' toggle if present (for beginner mode)."""
        toggles = self.driver.find_elements(*self.SHOW_ALL_FIELDS_TOGGLE)
        if toggles and toggles[0].is_displayed():
            self.scroll_and_click(toggles[0])
            time.sleep(0.3)

    # ── Browser environment ───────────────────────────────────────────────

    def get_browser_today(self) -> tuple[int, int, int]:
        """Return today's ``(day, month, year)`` as the *browser* renders it (de-DE).

        Resolved inside the browser (``toLocaleDateString('de-DE')``) rather than
        from the test runner's ``datetime``: browser and runner can sit in
        different timezones in the containerised stack, and a date cell rendered
        by the frontend must be compared against the browser's own notion of
        today. Zero-padding is normalised away, so the result compares equal to a
        parsed cell value regardless of which formatter produced it.

        Raises ``ValueError`` if the browser returns something that is not a
        German ``d.m.Y`` date — that would mean the page ran under a different
        locale and any comparison against it would be meaningless.
        """
        rendered = self.driver.execute_script("return new Date().toLocaleDateString('de-DE');")
        match = DE_DATE_RE.search(rendered or "")
        if not match:
            raise ValueError(
                f"Browser did not return a German d.m.Y date for today (got {rendered!r})"
            )
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    # ── Screenshots ───────────────────────────────────────────────────────

    def take_screenshot(self, name: str, output_dir: Path) -> Path:
        """Save a PNG screenshot and return the file path."""
        filepath = output_dir / f"{name}.png"
        self.driver.save_screenshot(str(filepath))
        return filepath
