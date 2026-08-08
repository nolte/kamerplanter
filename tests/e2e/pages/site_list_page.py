"""Page object for the Site list page."""

from __future__ import annotations

from contextlib import suppress

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import IMPLICIT_WAIT_EQUIVALENT, BasePage


class SiteListPage(BasePage):
    """Interact with the Sites list (``/standorte/sites``)."""

    PATH = "/standorte/sites"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='site-list-page']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-button']")
    TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> SiteListPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    #: The two states this list settles into: rows or the terminal "no source
    #: data" `EmptyState` (this page-object exposes no `search()`, so the
    #: `no-search-results` panel is not a reachable branch here -- it is still
    #: included in the disjunction below because it is inherited from
    #: `BasePage` and costs nothing to check). `PAGE` mounts synchronously --
    #: before the first fetch resolves -- so a read taken right after `open()`
    #: can land in a frame where neither has committed yet, the same
    #: just-navigated window `wait_for_dashboard_content` was built for
    #: (`pflege_dashboard_page.py`). `wait_for_loading_complete()` cannot close
    #: that window: it is satisfied whenever no skeleton has mounted *yet*,
    #: which is exactly true in that same frame.
    def wait_for_list_content(self, timeout: int = IMPLICIT_WAIT_EQUIVALENT) -> None:
        """Wait until the table has rows or its empty state.

        Deliberately does not raise: this is an *anchor* for the readers below,
        not an assertion of its own. A tenant with no sites is a state the
        caller's own assertion must still be able to observe.
        """
        with suppress(AssertionError):
            self.wait_for_any_present(
                (self.TABLE_ROWS, self.EMPTY_STATE, self.NO_SEARCH_RESULTS),
                "site list content",
                timeout=timeout,
            )

    def get_row_count(self) -> int:
        """Return the number of visible data rows.

        Anchored on :meth:`wait_for_list_content`. `test_req005_hybrid_sensor.py`
        gates a `pytest.skip(...)` on this immediately after `open()` -- an
        unanchored `0` read in the pre-fetch window before `open()`'s data has
        arrived is indistinguishable from a table that genuinely has no rows,
        which is the `has_care_card` defect class this mirrors (#946).
        """
        self.wait_for_list_content()
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_row_texts(self) -> list[str]:
        """Return the text content of every row currently rendered in the table."""
        return [row.text for row in self.driver.find_elements(*self.TABLE_ROWS)]

    def find_row_index_by_text(self, text: str) -> int:
        """Return the index of the first row whose text contains *text*, or -1."""
        for idx, row_text in enumerate(self.get_row_texts()):
            if text in row_text:
                return idx
        return -1

    def click_create(self) -> None:
        self.wait_for_element_clickable(self.CREATE_BUTTON).click()

    #: Column the row is activated through, should this page ever render a
    #: `DataTable`; see `SiteListPageExt` for the accordion-card layout it
    #: actually renders today.
    ROW_CLICK_COLUMN_ID = "name"

    def click_row(self, index: int) -> None:
        """Open the site at *index* via its inert `name` cell."""
        self.click_data_table_row(index, self.ROW_CLICK_COLUMN_ID, self.TABLE_ROWS, "site row")
