"""Page object for one feeding event (``/duengung/feeding-events/:key``, REQ-004; read by REQ-053 WP 10.14).

The detail tab is a two-column table without per-cell hooks: the page root (``feeding-event-detail-page``) is the
only ``data-testid``. The reader therefore returns the label -> value pairs of that table, keyed by the visible label,
and fails loudly when the page shows no such table (`test-falsifiability` T3) - an empty mapping never stands for
"nothing recorded".
"""

from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from .base_page import BasePage


class FeedingEventDetailPage(BasePage):
    PATH = "/duengung/feeding-events/{key}"

    PAGE = (By.CSS_SELECTOR, "[data-testid='feeding-event-detail-page']")
    #: The rows of the details tab's table (label cell, value cell).
    ROWS = (By.CSS_SELECTOR, "[data-testid='feeding-event-detail-page'] table tbody tr")

    def open(self, event_key: str) -> FeedingEventDetailPage:
        self.navigate(self.PATH.format(key=event_key))
        self.wait_for_content(self.PAGE, f"feeding event {event_key}", require_no_skeleton=False)
        try:
            self.wait_for_element_visible(self.ROWS)
        except TimeoutException as exc:
            raise AssertionError(f"the feeding event {event_key} shows no detail table") from exc
        return self

    def facts(self) -> dict[str, str]:
        """``{label: value}`` of the detail table; loud when the table has no two-cell row."""
        facts: dict[str, str] = {}
        for row in self.driver.find_elements(*self.ROWS):
            cells = row.find_elements(By.CSS_SELECTOR, "td, th")
            if len(cells) != 2:
                continue
            label, value = (
                " ".join((cell.get_attribute("textContent") or "").split()) for cell in cells
            )
            facts[label] = value
        if not facts:
            raise AssertionError("the feeding event's detail table has no label/value row")
        return facts


__all__ = ["FeedingEventDetailPage"]
