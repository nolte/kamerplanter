"""`SpeciesListPage.click_row_by_name` waits for the filtered row, and still says no.

## What this pins

`click_row_by_name` searches, then scans the rendered rows for an exact name.
Its scan was wrapped in `retry_on_stale`, which catches
`StaleElementReferenceException` and nothing else — so the one state the scan is
most likely to hit, *the filtered render has not landed yet*, raised `ValueError`
on the very first frame and escaped. `search()` cannot close that window on its
own: it sleeps out the 300 ms debounce and then calls
`wait_for_loading_complete()`, which waits for a `LoadingSkeleton` to **unmount**
— and a refetch that resolves before one ever renders leaves it nothing to wait
for.

That is not hypothetical. The 2026-08-28 `light` nightly failed here with
``Row with name 'Solanum journey315634' not found`` on a species whose create had
just succeeded, in a test that had passed the four nights before.

Two properties, and the second is what keeps the first from being a cheat:

1. **A row that arrives late is waited for**, not answered "not found".
2. **A row that never arrives is still refused** — as `ValueError`, inside the
   budget, and now naming what the list *did* render. The exception type is part
   of the contract: `test_req001_cross_entity` falls back to the first row on it
   and `test_req001_species` skips on it. Removing this race must not silently
   re-route those two branches.

## Why the driver is stubbed and nothing else is

Same technique and reason as `test_row_helpers.py`: a **real** `WebDriver` over a
fake command executor, so Selenium's own `WebDriverWait` and the real page object
run — only the wire is fake. Provoking "the row appears one poll late" in a real
browser would mean hitting a React render at a precise instant, which is the
flakiest possible way to assert a deterministic contract.

`search()` is stubbed out because it is not what is under test here and would
need the whole toolbar modelled; the scan that follows it is.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` — see this package's `README.md`.
"""

from __future__ import annotations

import time
from typing import Any

import pytest
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver

from tests.e2e.pages import species_list_page as species_module
from tests.e2e.pages.species_list_page import SpeciesListPage

from .test_row_helpers import COL, StubConnection, TableDom

#: The species this suite provisions and then clicks, in the shape the failing
#: nightly used: unique per run, so no seeded row can satisfy the lookup.
TARGET = "Solanum journey315634"

#: What the pre-filter render shows instead — the state the scan used to read.
BEFORE_FILTER = ["Abelia grandiflora", "Zamioculcas zamiifolia"]


@pytest.fixture
def page(monkeypatch: pytest.MonkeyPatch) -> tuple[SpeciesListPage, TableDom, StubConnection]:
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    listing = SpeciesListPage(driver, "http://stub.invalid")
    # The stub table is addressed by one column id; the page's own is irrelevant
    # to the property under test and would need a second TableDom.
    monkeypatch.setattr(listing, "NAME_COLUMN_ID", COL)
    # Not under test, and modelling the toolbar would only add ways to fail.
    monkeypatch.setattr(listing, "search", lambda _query: None)
    return listing, dom, connection


def _render_on_nth_row_lookup(
    connection: StubConnection, dom: TableDom, nth: int, names: list[str]
) -> None:
    """Let the filtered render land only on the *nth* row scan.

    Hooked on the lookup rather than on a timer so the ordering is exact: scans
    1..nth-1 observe the pre-filter table, which is the state under test, and the
    nth observes the filtered one.
    """
    lookups: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        lookups.append(1)
        if len(lookups) == nth:
            dom.render(names)

    connection.before[Command.FIND_ELEMENTS] = hook


class TestTheRowThatArrivesLate:
    """Property 1 — the wait the `StaleElementReferenceException`-only retry lacked."""

    def test_a_row_rendered_after_the_first_scan_is_still_clicked(
        self, page: tuple[SpeciesListPage, TableDom, StubConnection]
    ) -> None:
        """The exact shape of the 2026-08-28 failure, made deterministic.

        Before the poll, scan #1 read `BEFORE_FILTER`, found no match and raised
        `ValueError` — with the row one render away.
        """
        listing, dom, connection = page
        dom.render(BEFORE_FILTER)
        _render_on_nth_row_lookup(connection, dom, 2, [TARGET])

        listing.click_row_by_name(TARGET)

        assert connection.clicked == [TARGET]

    def test_it_survives_several_frames_of_the_pre_filter_render(
        self, page: tuple[SpeciesListPage, TableDom, StubConnection]
    ) -> None:
        """One late frame could be luck; the wait has to hold across a few."""
        listing, dom, connection = page
        dom.render(BEFORE_FILTER)
        _render_on_nth_row_lookup(connection, dom, 4, [TARGET])

        listing.click_row_by_name(TARGET)

        assert connection.clicked == [TARGET]


class TestTheRowThatNeverArrives:
    """Property 2 — waiting must not have cost the ability to say no."""

    def test_it_still_raises_value_error_and_names_what_was_rendered(
        self,
        page: tuple[SpeciesListPage, TableDom, StubConnection],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """`ValueError`, not a timeout: two callers branch on that type.

        The budget is shortened rather than waited out — what is asserted is the
        outcome and the message, and the real 15 s only makes the suite slower.
        """
        listing, dom, connection = page
        monkeypatch.setattr(species_module, "DEFAULT_TIMEOUT", 1)
        dom.render(BEFORE_FILTER)

        started = time.time()
        with pytest.raises(ValueError) as excinfo:
            listing.click_row_by_name(TARGET)
        elapsed = time.time() - started

        assert connection.clicked == []
        message = str(excinfo.value)
        # The name that was looked for, and — the part the old message lacked —
        # what the list actually held instead, so a real miss is readable.
        assert TARGET in message
        assert all(name in message for name in BEFORE_FILTER), message
        assert elapsed < 10, f"the refusal took {elapsed:.1f}s, so the budget is not honoured"
