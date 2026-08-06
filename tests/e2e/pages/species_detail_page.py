"""Page object for the Species detail page.

Tabs (label-based navigation via ``click_tab_by_label``): Übersicht, Aussaat &
Ernte, Sorten (cultivars), Lebenszyklus-Konfiguration, Workflows, Bearbeiten
(plus expert-only Mischkultur / Fruchtfolge). Navigate by label, not index — the
tab set and order vary with experience level.
"""

from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import IMPLICIT_WAIT_EQUIVALENT, BasePage


class SpeciesDetailPage(BasePage):
    """Interact with the Species detail page (``/stammdaten/species/:key``)."""

    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    # Addressed by data-testid, not by the MUI error colour class: on `xs` the
    # delete action is an overflow menu entry, which carries neither the class
    # nor the `button` tag the old XPath required (#832). Matches both the
    # visible button and its `-menu-item` counterpart.
    DELETE_BUTTON = (
        By.CSS_SELECTOR,
        "[data-testid='delete-species-button'], [data-testid='delete-species-button-menu-item']",
    )
    READONLY_BANNER = (By.CSS_SELECTOR, "[data-testid='species-readonly-banner']")
    TABS = (By.CSS_SELECTOR, "button[role='tab']")
    # This is genuinely the *in-page* "Bearbeiten" tab's submit button (no
    # dialog wraps this tab), left unscoped on purpose: it is the element
    # LIFECYCLE_FORM_SUBMIT below used to collide with (see #778 A5).
    FORM_SUBMIT = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # Cultivar tab locators
    CULTIVAR_CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    CULTIVAR_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    # The Cultivar tab opens CultivarCreateDialog (cultivar-create-dialog),
    # the Lifecycle tab opens GrowthPhaseDialog (growth-phase-dialog).
    # Both are modal: at most one is open at a time.
    CREATE_DIALOG = (
        By.CSS_SELECTOR,
        "[data-testid='cultivar-create-dialog'], [data-testid='growth-phase-dialog']",
    )

    # Lifecycle tab locators
    # Scoped to the lifecycle tab's own section, not to a dialog: this is the
    # inline form the tab renders (`LifecycleConfigSection`), and its submit is
    # what `get_lifecycle_submit_label` reads. The scope is needed because
    # several `form-submit-button` testids coexist in this page's DOM -- the
    # edit tab's inline form, this one, and the growth-phase dialog MUI portals
    # to the end of <body> -- so an unscoped lookup resolves to whichever comes
    # first in document order (#778 A5). The section marker was added to the
    # product for this; there was no scope available before.
    LIFECYCLE_FORM_SUBMIT = (
        By.CSS_SELECTOR,
        "[data-testid='lifecycle-config-section'] [data-testid='form-submit-button']",
    )

    # Growth phase locators
    PHASE_CREATE_BUTTON = (By.XPATH, "//button[contains(normalize-space(.), 'Phase erstellen')]")
    # Section heading — present for every species with a lifecycle config,
    # including system/managed species, which hide the create button.
    PHASE_SECTION_TITLE = (By.XPATH, "//h6[normalize-space()='Wachstumsphasen']")
    PHASE_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, key: str) -> SpeciesDetailPage:
        self.navigate(f"/stammdaten/species/{key}")
        self.wait_for_element(self.PAGE_TITLE)
        self.wait_for_loading_complete()
        return self

    def get_title(self) -> str:
        return self.get_text_stable(self.PAGE_TITLE)

    # ── Tabs ───────────────────────────────────────────────────────────

    def get_tab_labels(self) -> list[str]:
        tabs = self.tab_elements(self.TABS)
        return [t.text for t in tabs]

    def click_tab(self, index: int) -> None:
        tabs = self.tab_elements(self.TABS)
        self.scroll_and_click(self.require_index(tabs, index, "species detail tab"))

    def click_tab_by_label(self, label: str) -> None:
        import time

        # `tab_elements` carries the "wait for the strip to render" half that was
        # a separate `wait_for_element(self.TABS)` here. This page object had
        # found the defect the whole suite has now been swept for, and fixed it
        # in this one method; the wait is no longer this method's business.
        #
        # The sleep stays, and is a different concern: MUI mounts the strip
        # before every `Tab` has its label laid out, and this reader matches on
        # label text rather than on presence.
        time.sleep(0.5)
        tabs = self.tab_elements(self.TABS)
        for tab in tabs:
            if tab.text.upper() == label.upper():
                self.scroll_and_click(tab)
                return
        tab_labels = [t.text for t in tabs]
        raise ValueError(f"Tab '{label}' not found among {tab_labels}")

    # ── Edit tab (tab 0) ──────────────────────────────────────────────

    def get_field_value(self, field_name: str) -> str:
        el = self.find_present((By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input"))
        return el.get_attribute("value") or ""

    def set_field(self, field_name: str, value: str) -> None:
        # Try input first, fall back to textarea (multiline fields)
        locator_input = (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        locator_textarea = (
            By.CSS_SELECTOR,
            f"[data-testid='form-field-{field_name}'] textarea:not([aria-hidden])",
        )
        elements = self.driver.find_elements(*locator_input)
        if elements:
            el = self.wait_for_element_clickable(locator_input)
        else:
            el = self.wait_for_element_clickable(locator_textarea)
        el.clear()
        el.send_keys(value)

    def add_chip(self, field_name: str, value: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.send_keys(value)
        el.send_keys(Keys.ENTER)

    def select_option(self, field_name: str, value_text: str) -> None:
        """Open an MUI Select and pick an option by its visible text.

        Routed through the shared, verified select helpers -- see
        ``BotanicalFamilyListPage.select_option`` for the rationale.
        """
        self.open_select(field_name)
        self.select_option_by_label(value_text)

    def click_save(self) -> None:
        self.wait_and_click(self.FORM_SUBMIT)

    def click_delete(self) -> None:
        # Routed through the shared helper so the action is reachable whether it
        # is a header button (`sm`+) or an overflow entry (`xs`).
        self.click_header_action("delete-species-button")
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_delete(self) -> None:
        self.wait_and_click(self.CONFIRM_BUTTON)

    def cancel_delete(self) -> None:
        self.wait_and_click(self.CONFIRM_CANCEL)

    def has_delete_button(self) -> bool:
        """Whether the delete action exists at all.

        UI-NFR-018 R-012 omits it for system data rather than disabling it, so
        absence is the assertion. On `xs` it lives in the overflow menu, which
        has to be opened before its entry exists in the DOM.
        """
        if self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='delete-species-button']"):
            return True
        trigger = self.driver.find_elements(*self.PAGE_HEADER_OVERFLOW)
        if not trigger:
            return False
        self.scroll_and_click(trigger[0])
        found = bool(
            self.driver.find_elements(
                By.CSS_SELECTOR, "[data-testid='delete-species-button-menu-item']"
            )
        )
        self.close_mui_dropdown()
        return found

    def is_read_only(self) -> bool:
        """Return True if this species is origin-protected (read-only).

        Global/system species (UI-NFR-018) show a read-only banner, render no
        editable form actions on the edit tab, and — being deletion-protected —
        no delete button.
        """
        return len(self.driver.find_elements(*self.READONLY_BANNER)) > 0

    # ── Cultivar tab ("Sorten") ───────────────────────────────────────

    def get_cultivar_count(self) -> int:
        return len(self.driver.find_elements(*self.CULTIVAR_TABLE_ROWS))

    #: Column id of the cultivar table's identifying column (CultivarListSection).
    CULTIVAR_NAME_COLUMN_ID = "name"
    #: Row-scoped delete action, emitted per cultivar key in BOTH layouts.
    CULTIVAR_DELETE_ACTION = (By.CSS_SELECTOR, "[data-testid^='cultivar-delete-']")

    def get_cultivar_names(self) -> list[str]:
        """Return the name of every listed cultivar.

        Addressed by column id, not by position: below the DataTable's mobile
        breakpoint `CultivarListSection` renders `MobileCard`s with no ``<td>``
        at all, so a ``By.TAG_NAME, 'td'`` scan returned an empty list there and
        an "is the new cultivar listed?" assertion failed for the wrong reason
        (TC-REQ-001-J079).

        Gated on the table having rows, on the short `IMPLICIT_WAIT_EQUIVALENT`
        budget. The dialog closing proves the cultivar exists server-side, but
        `CultivarListSection` then refetches, and during that refetch the table
        renders nothing -- so the reader's single call site could still read
        ``[]`` for a cultivar that was created. If no row ever arrives the list
        is returned empty exactly as before and the caller's assertion still
        fails, naming what it saw.
        """
        self.await_presence(self.DATA_TABLE_ROWS, IMPLICIT_WAIT_EQUIVALENT)
        return self.get_column_texts(self.CULTIVAR_NAME_COLUMN_ID)

    def get_trait_chip_texts(self) -> list[str]:
        """Return the text of all MUI Chip labels currently rendered (e.g. cultivar traits)."""
        chips = self.driver.find_elements(By.CSS_SELECTOR, ".MuiChip-label")
        return [c.text for c in chips]

    def click_cultivar_row(self, index: int) -> None:
        """Open the cultivar at *index* via its inert `name` cell.

        Not the row centre: `CultivarListSection` renders an `actions` column
        whose delete `IconButton` calls `stopPropagation`, so where the row's
        midpoint lands decides whether the row navigates or a delete dialog
        opens.
        """
        self.click_data_table_row(
            index,
            self.CULTIVAR_NAME_COLUMN_ID,
            self.CULTIVAR_TABLE_ROWS,
            "cultivar row",
        )

    def click_cultivar_create(self) -> None:
        # The cultivar create button lives under the "Sorten" tab of the (now
        # 6-tab) species detail page. Switch to it by label first — robust to
        # tab reordering (cultivars is no longer at a fixed low index).
        self.click_tab_by_label("Sorten")
        self.wait_and_click(self.CULTIVAR_CREATE_BUTTON)
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def is_create_dialog_open(self) -> bool:
        """Check whether the cultivar/growth-phase create dialog is present."""
        return len(self.driver.find_elements(*self.CREATE_DIALOG)) > 0

    def delete_cultivar_at_index(self, index: int) -> None:
        """Click the delete action of the cultivar row at *index*.

        Targets the product's own ``cultivar-delete-<key>`` testid (row-scoped,
        so the key need not be known here) instead of "the first button with an
        aria-label" -- the latter is position-dependent and, in the mobile card
        layout, would pick whatever button the card happens to render first.

        Clicked coordinate-free for the same reason as
        :meth:`delete_phase_at_index`: the row itself is clickable, so a
        coordinate dispatch that misses the IconButton silently activates the
        row's navigation/edit handler instead of raising.
        """
        rows = self.driver.find_elements(*self.CULTIVAR_TABLE_ROWS)
        if index >= len(rows):
            raise ValueError(
                f"Cultivar row {index} requested, but only {len(rows)} rows are listed"
            )
        buttons = rows[index].find_elements(*self.CULTIVAR_DELETE_ACTION)
        if not buttons:
            raise ValueError(f"No cultivar-delete action found in cultivar row {index}")
        self.click_coordinate_free(buttons[0])
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    # ── Cultivar create dialog ─────────────────────────────────────────

    def fill_cultivar_form(self, name: str, **kwargs: str) -> None:
        name_el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, "[data-testid='form-field-name'] input")
        )
        name_el.clear()
        name_el.send_keys(name)

        for field, value in kwargs.items():
            el = self.wait_for_element_clickable(
                (By.CSS_SELECTOR, f"[data-testid='form-field-{field}'] input")
            )
            el.clear()
            el.send_keys(value)

    CULTIVAR_CREATE_DIALOG = (By.CSS_SELECTOR, "[data-testid='cultivar-create-dialog']")

    def submit_cultivar_form(self) -> None:
        """Submit the cultivar-create dialog and wait for it to close.

        Scoped to the cultivar dialog -- the same ``[data-testid='form-
        submit-button']`` this used to address unscoped also matches the
        in-page "Bearbeiten" tab's FORM_SUBMIT and the growth-phase dialog's
        LIFECYCLE_FORM_SUBMIT (see #778 A5).

        The dialog closing is the post-condition, and an exact one:
        ``CultivarCreateDialog.onSubmit`` calls ``onCreated()`` -- which closes
        it -- only after ``await api.createCultivar(...)`` resolves. Without it
        the caller carried on into the refetch the create triggers, which is how
        TC-REQ-001-J079 read ``[]`` off the Cultivars table for a cultivar the
        backend had already answered ``201`` for (#835).
        """
        self.wait_and_click(
            (
                By.CSS_SELECTOR,
                "[data-testid='cultivar-create-dialog'] [data-testid='form-submit-button']",
            )
        )
        self.wait_for_element_hidden(self.CULTIVAR_CREATE_DIALOG)

    # ── Lifecycle tab (tab 2) ─────────────────────────────────────────

    def get_lifecycle_submit_label(self) -> str:
        el = self.wait_for_element(self.LIFECYCLE_FORM_SUBMIT)
        return el.text

    def set_lifecycle_field(self, field_name: str, value: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input")
        )
        el.clear()
        el.send_keys(value)

    def select_lifecycle_option(self, field_name: str, value_text: str) -> None:
        self.select_option(field_name, value_text)

    def toggle_lifecycle_switch(self, field_name: str) -> None:
        el = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='form-field-{field_name}'] input[type='checkbox']")
        )
        self.scroll_and_click(el)

    def click_lifecycle_save(self) -> None:
        self.wait_and_click(self.LIFECYCLE_FORM_SUBMIT)

    # ── Growth phases (within lifecycle tab) ──────────────────────────

    def has_growth_phase_section(self, timeout: int = 10) -> bool:
        # Anchor on the section heading, not the create button: managed
        # (system) species render the section read-only without the button.
        # The section loads asynchronously after the lifecycle form; poll
        # instead of a single unwaited find_elements, which races the fetch
        # on slower machines (e.g. CI runners).
        return self._poll_present(self.PHASE_SECTION_TITLE, timeout)

    def can_create_growth_phase(self, timeout: int = 10) -> bool:
        # Editable (non-managed) species only — the create button is hidden
        # for system species even though the section itself is visible.
        return self._poll_present(self.PHASE_CREATE_BUTTON, timeout)

    def _poll_present(self, locator: tuple[str, str], timeout: int) -> bool:
        try:
            self.poll(timeout).until(lambda d: len(d.find_elements(*locator)) > 0)
        except TimeoutException:
            return False
        return True

    def get_phase_count(self) -> int:
        return len(self.driver.find_elements(*self.PHASE_TABLE_ROWS))

    #: Column id of the growth-phase table's identifying column
    #: (GrowthPhaseListSection -- renders `displayName`).
    PHASE_NAME_COLUMN_ID = "name"
    #: Row-scoped delete action, emitted per phase key in BOTH layouts.
    PHASE_DELETE_ACTION = (By.CSS_SELECTOR, "[data-testid^='phase-delete-']")
    #: Row-scoped "open profiles" action, emitted per phase key in BOTH layouts
    #: (`GrowthPhaseListSection.tsx:191/219`). Keyed rather than positional so a
    #: managed species -- which renders no actions column at all -- is
    #: distinguishable from "the profile button moved".
    PHASE_PROFILE_ACTION = (By.CSS_SELECTOR, "[data-testid^='phase-profile-']")

    def get_phase_profile_keys(self) -> list[str]:
        """Return the phase key behind every visible "open profiles" action."""
        prefix = "phase-profile-"
        keys = []
        for el in self.driver.find_elements(*self.PHASE_PROFILE_ACTION):
            testid = el.get_attribute("data-testid") or ""
            if testid.startswith(prefix):
                keys.append(testid[len(prefix) :])
        return keys

    def get_phase_names(self) -> list[str]:
        """Return the display name of every listed growth phase.

        Addressed by column id, not by position: the leading ``<td>`` is the
        sequence-order column, and the mobile card layout has no ``<td>`` at all.
        """
        return self.get_column_texts(self.PHASE_NAME_COLUMN_ID)

    def click_phase_create(self) -> None:
        # scroll_and_click: a still-collapsing notistack snackbar can overlay
        # the bottom-right button and intercept a plain .click().
        self.scroll_and_click(self.wait_for_element_clickable(self.PHASE_CREATE_BUTTON))
        self.wait_for_element_visible(self.CREATE_DIALOG)

    def fill_phase_form(
        self, name: str, display_name: str, duration: str, order: str, **kwargs: str
    ) -> None:
        self.set_field("name", name)
        self.set_field("display_name", display_name)
        self.set_field("typical_duration_days", duration)
        self.set_field("sequence_order", order)

        for field, value in kwargs.items():
            if field == "stress_tolerance":
                self.select_option(field, value)
            elif field in ("is_terminal", "allows_harvest"):
                self.toggle_lifecycle_switch(field)
            else:
                self.set_field(field, value)

    def submit_phase_form(self) -> None:
        # Target the submit button inside the create-dialog (GrowthPhaseDialog)
        # to avoid hitting the lifecycle config form's submit button
        self.wait_and_click(
            (
                By.CSS_SELECTOR,
                "[data-testid='growth-phase-dialog'] [data-testid='form-submit-button']",
            )
        )

    def click_phase_row(self, index: int) -> None:
        """Open the growth phase at *index* via its inert `name` cell.

        Not the row centre: `GrowthPhaseListSection` renders an `actions`
        column holding an edit and a *delete* `IconButton`, both of which
        `stopPropagation`.
        """
        self.click_data_table_row(
            index,
            self.PHASE_NAME_COLUMN_ID,
            self.PHASE_TABLE_ROWS,
            "growth phase row",
        )

    def delete_phase_at_index(self, index: int) -> None:
        """Click the delete action of the growth-phase row at *index*.

        Targets the product's own ``phase-delete-<key>`` testid (row-scoped, so
        the key need not be known here). The previous "last MuiIconButton in the
        row" heuristic failed outright in the mobile card layout ("No IconButton
        found in phase row 0"), because the desktop actions column is not
        rendered there at all -- `GrowthPhaseListSection` now supplies the same
        actions via the card's ``trailing`` slot.

        Clicked coordinate-free. ``e.stopPropagation()`` on the button's own
        ``onClick`` (`GrowthPhaseListSection.tsx:198/225`) only protects a click
        that actually *lands on* the 40px IconButton -- it says nothing about a
        coordinate dispatch that misses it and reaches the row instead, where
        `DataTable`'s ``onRowClick`` (`:259`) opens the *edit* dialog. That is
        what the failure screenshot of TC-REQ-001-060 shows: the edit dialog,
        carrying the phase's name, on the light and full profiles. Since both
        handlers cannot fire from one event, the click never reached the button.
        A dispatch on the resolved element has no coordinates to miss with, and
        the IconButton activates from its `onClick` handler, so it is sound.

        The confirm-dialog wait is a post-condition for having hit *this*
        action -- the edit dialog carries a different testid -- but it is not, as
        this docstring previously claimed, what "confirms the click landed": a
        miss leaves it to time out and report the absence of a dialog rather than
        the wrong-target click that caused it.
        """
        rows = self.driver.find_elements(*self.PHASE_TABLE_ROWS)
        if index >= len(rows):
            raise ValueError(f"Phase row {index} requested, but only {len(rows)} rows are listed")
        buttons = rows[index].find_elements(*self.PHASE_DELETE_ACTION)
        if not buttons:
            raise ValueError(
                f"No phase-delete action found in phase row {index} -- the phase list "
                "is read-only (managed by a phase sequence) or the row failed to render"
            )
        self.click_coordinate_free(buttons[0])
        self.wait_for_element_visible(self.CONFIRM_DIALOG, timeout=10)
