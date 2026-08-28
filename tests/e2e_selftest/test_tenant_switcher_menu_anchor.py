"""`TenantSwitcherPage.get_tenant_names` reads the menu the user sees, not its first frame.

## What this pins

`open_menu` waits for the menu *container* to be visible. That says nothing
about the items inside it: MUI grows the `Menu` paper over ~200 ms, and
`WebElement.text` answers `''` for a node that has not been laid out yet. A read
taken in that window returns a list with an empty string in it, and
TC-REQ-024-020's ``assert name`` fails with the uninformative ``assert ''`` —
the application working correctly, reported as a defect.

That is not hypothetical: it is the 2026-08-21 nightly and, again, run
33195629069 on the `full` profile.

The sibling reader in the same page object already had this fixed.
`wait_for_active_tenant_label` was added after the 2026-08-14 nightly for the
identical mechanism on the trigger button, with the identical anchor shape — a
suppressed poll that never raises. `get_tenant_names` simply never got it. This
module pins the property for both directions so the two cannot drift apart
again.

Two properties:

1. **Labels that arrive late are waited for**, so the names reach the caller.
2. **The anchor never raises.** A menu that renders nothing must still be
   observable as an empty list, and a name that is genuinely empty must still
   reach the caller's own assertion with the caller's own message — not be
   converted into a `TimeoutException` thrown out of a reader.

## Why the driver is a hand-rolled double here

Unlike `test_row_helpers.py` this needs no `DataTable`: the reader touches only
`find_elements`, an element's `.text` and its nested `find_elements`. A double
of exactly that surface makes "the label lands on the third look" expressible as
a number instead of a sleep. `BasePage.poll` builds a real `WebDriverWait` over
whatever object it is handed, so Selenium's own polling still runs.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` — see this package's `README.md`.
"""

from __future__ import annotations

import time

from tests.e2e.pages.tenant_switcher_page import TenantSwitcherPage

NAMES = ["Mein Garten", "Gemeinschaftsgarten Nord"]


class FakeText:
    """The `.MuiListItemText-primary` node inside one menu item."""

    def __init__(self, item: FakeItem) -> None:
        self._item = item

    @property
    def text(self) -> str:
        return self._item.text


class FakeItem:
    """One `li[role='menuitem']`, blank until the menu has been looked at *reveal_at* times."""

    def __init__(self, name: str, driver: FakeMenuDriver, reveal_at: int) -> None:
        self._name = name
        self._driver = driver
        self._reveal_at = reveal_at

    @property
    def text(self) -> str:
        return self._name if self._driver.item_lookups >= self._reveal_at else ""

    def find_elements(self, _by: str, _value: str) -> list[FakeText]:
        return [FakeText(self)]


class FakeMenuDriver:
    """Answers the three lookups the reader makes, and counts the item lookups."""

    def __init__(self, names: list[str], *, reveal_at: int = 1, has_divider: bool = False) -> None:
        self.item_lookups = 0
        self._has_divider = has_divider
        self._items = [FakeItem(name, self, reveal_at) for name in names]

    def find_elements(self, _by: str, value: str) -> list[object]:
        if "MuiDivider-root" in value:
            return [object()] if self._has_divider else []
        self.item_lookups += 1
        return list(self._items)


def _page(driver: FakeMenuDriver, *, budget: int | None = None) -> TenantSwitcherPage:
    page = TenantSwitcherPage(driver, "http://stub.invalid")  # type: ignore[arg-type]
    if budget is not None:
        # Shortened where the test deliberately never satisfies the anchor:
        # what is asserted is the outcome, and the real budget only makes the
        # suite slower.
        page.MENU_LABEL_TIMEOUT = budget  # type: ignore[misc]
    return page


class TestLabelsThatArriveLate:
    """Property 1 — the wait `open_menu`'s container check cannot provide."""

    def test_names_rendered_after_the_first_look_are_still_returned(self) -> None:
        """The shape of the 2026-08-21 and run-33195629069 failures.

        Without the anchor the first scan reads the grow transition and returns
        ``['', '']``, which is what ``assert name`` reported as ``assert ''``.
        """
        driver = FakeMenuDriver(NAMES, reveal_at=3)

        assert _page(driver).get_tenant_names() == NAMES

    def test_a_menu_that_is_ready_immediately_costs_no_extra_wait(self) -> None:
        """The anchor must not turn the common case into a delay."""
        driver = FakeMenuDriver(NAMES, reveal_at=1)

        started = time.time()
        names = _page(driver).get_tenant_names()

        assert names == NAMES
        assert time.time() - started < 2


class TestTheAnchorNeverRaises:
    """Property 2 — anchoring a reader must not cost it the ability to answer."""

    def test_an_empty_menu_is_reported_as_an_empty_list(self) -> None:
        """A menu with no items is a state the caller must be able to observe."""
        driver = FakeMenuDriver([])

        assert _page(driver, budget=1).get_tenant_names() == []

    def test_a_genuinely_blank_label_still_reaches_the_caller(self) -> None:
        """The anchor waits it out and then answers, rather than raising.

        This is the half that keeps property 1 from being a cheat: if the anchor
        converted "still blank" into a `TimeoutException`, TC-REQ-024-020 would
        stop being able to fail on the defect it exists to catch.
        """
        driver = FakeMenuDriver([""], reveal_at=1)

        assert _page(driver, budget=1).get_tenant_names() == [""]

    def test_the_create_org_entry_is_still_trimmed_off(self) -> None:
        """The divider-based trim is unchanged by the anchor."""
        driver = FakeMenuDriver([*NAMES, "Organisation erstellen"], has_divider=True)

        assert _page(driver).get_tenant_names() == NAMES
