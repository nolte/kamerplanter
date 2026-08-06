"""Verification of the *plural* lookup path: the `DataTable` row helpers.

## What this pins, and why it is a separate module from the proxy's

`test_element_proxy.py` covers the singular path — a reference that re-acquires
itself. This module covers the other half of #835: `driver.find_elements(...)`,
which is **not** wrapped and deliberately never will be (the reasoning is in
`base_page.py`, "Why the *plural* path is not wrapped"). The mechanism there is
`BasePage.retry_on_stale`, which re-runs an action that re-acquires what it
touches, and its entire call population is the three row helpers:
`get_column_texts`, `find_row_by_text` and `click_data_table_row`.

Three properties are measured here, none of which was provable by reading:

1. **The helpers survive a re-render mid-use.** A row reference dying between
   the lookup and the read/click must not escape as a
   `StaleElementReferenceException`.
2. **They survive the *second* signal a re-rendering table emits.** React
   reconciles a surviving row's children in place, and mid-reconciliation the
   row is attached but exposes none of its identifying hooks. That raised an
   `AssertionError`, which `retry_on_stale` does not catch — so it escaped both
   `get_column_texts` and `click_data_table_row` as a hard failure. It was
   measured, not deduced: the first version of these tests failed on exactly
   that, which is why `TableNotSettled` exists.
3. **A row that never renders the column still fails.** The retry must not turn
   a wrongly addressed column into a silent `''`. It stays loud, keeps the
   original message and arrives inside the retry budget.

Plus the two guards that must not regress: the identity-based recovery in
`click_data_table_row` (#871), and the staleness *verdicts*, which answer with
the exception and must therefore never be handed a self-healing reference.

## Why the driver is stubbed and nothing else is

Same technique and same reason as `test_element_proxy.py`: the tests build a
**real** `selenium.webdriver.remote.webdriver.WebDriver` over a fake command
executor, so Selenium's own staleness mapping, `WebDriverWait`, and the real
`BasePage` all run. Only the wire is fake. Provoking these DOM moves in a real
browser would mean hitting a React re-render at a precise instant — the flakiest
possible way to assert a deterministic contract, and one that could not
distinguish "the helper handled it" from "the timing missed the window".

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` — see this package's `README.md` and the module docstring of
`test_element_proxy.py`.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.pages._element_proxy import ReResolvingElement, resolve_element
from tests.e2e.pages.base_page import (
    IMPLICIT_WAIT_EQUIVALENT,
    POLL_TRANSIENTS,
    BasePage,
    TableNotSettled,
)
from tests.e2e.pages.task_detail_page import TaskDetailPage

#: The W3C element identifier key — see `test_element_proxy.py` for why it is
#: restated rather than imported.
W3C_ELEMENT_KEY = "element-6066-11e4-a52e-4f735466cecf"

#: The column every table in this module is addressed by.
COL = "name"

#: How far past `IMPLICIT_WAIT_EQUIVALENT` a bounded retry may run before the
#: bound stops being the one the code documents. `retry_on_stale` checks its
#: deadline only *between* attempts, so one attempt's worth of overshoot is by
#: design.
BUDGET_SLACK = 1.5


# ── A DataTable the tests can re-render underneath a captured row ────────────


class StubNode:
    """One element in the stub DOM."""

    def __init__(self, node_id: str, testid: str, text: str = "", css_class: str = "") -> None:
        self.id = node_id
        self.testid = testid
        self.text = text
        #: Modelled only because MUI expresses a Chip's palette as a class and
        #: `BasePage._chip_colors` therefore has to read one. Nothing here is
        #: *located* by class — see `_matches`.
        self.css_class = css_class
        self.children: list[StubNode] = []
        #: False once a re-render replaced this node. Every command against it
        #: then answers with a W3C `stale element reference`, exactly as a real
        #: driver does for a detached node.
        self.attached = True

    def descendants(self) -> Iterator[StubNode]:
        for child in self.children:
            yield child
            yield from child.descendants()


class TableDom:
    """A `DataTable` whose rows are replaced wholesale by a re-render.

    Models the two states a row can be in that this suite has to survive, and
    keeps them distinct because the helpers must react to them differently:

    * **replaced** — the old row node is detached and a new one takes its place
      under the same locator (`render`), and
    * **mid-render** — the row node exists but has not rendered the cell that
      identifies it (`render_without_cells`), which is what React's in-place
      reconciliation of a surviving row looks like from outside.
    """

    ROW_TESTID = "data-table-row"

    def __init__(self) -> None:
        self.root = StubNode("root", "root")
        self._counter = 0

    def _new(self, testid: str, text: str = "", css_class: str = "") -> StubNode:
        self._counter += 1
        return StubNode(f"element-{self._counter}", testid, text, css_class)

    def render(
        self, names: list[str], *, with_cells: bool = True, chip_palette: str | None = None
    ) -> None:
        """Replace every row with a fresh one; the old nodes die immediately.

        *chip_palette* hangs a MUI Chip inside each identifying cell, which is
        the shape `get_column_chip_texts` / `get_column_chip_colors` read
        through: row -> ``cell-<col>`` scope -> ``.MuiChip-root``. Two levels
        deeper than a cell read, and therefore the longest window in which a
        re-render can kill the captured row.
        """
        for node in self.root.descendants():
            node.attached = False
        self.root.children = []
        for name in names:
            row = self._new(self.ROW_TESTID, name)
            if with_cells:
                cell = self._new(f"cell-{COL}", name)
                if chip_palette is not None:
                    cell.children.append(
                        self._new(
                            f"chip-{name}",
                            name,
                            f"MuiChip-root MuiChip-color{chip_palette.capitalize()}",
                        )
                    )
                row.children.append(cell)
            self.root.children.append(row)

    def render_without_cells(self, names: list[str]) -> None:
        """Render rows that expose no identifying cell yet — the mid-render shape."""
        self.render(names, with_cells=False)

    def fill_in_cells(self) -> None:
        """Give the *existing* rows their identifying cell, leaving them attached.

        The distinction that makes the mid-render tests mean anything: this is
        React reconciling a surviving row's children in place. No reference dies,
        so nothing goes stale — the row simply becomes readable. Using `render`
        instead would detach the rows and exercise the staleness path, which is
        already covered and is *not* the gap `TableNotSettled` closes.
        """
        for row in self.root.children:
            if not any(child.testid == f"cell-{COL}" for child in row.children):
                row.children.append(self._new(f"cell-{COL}", row.text))

    def render_dialog(self, testid: str) -> StubNode:
        """Render a single non-row node (a dialog paper) and return it."""
        node = self._new(testid)
        self.root.children.append(node)
        return node

    def match(self, scope: StubNode, selector: str) -> list[StubNode]:
        return [n for n in scope.descendants() if n.attached and _matches(n, selector)]


def _matches(node: StubNode, selector: str) -> bool:
    """Answer the three selector shapes the helpers under test actually issue.

    Exact testid (`cell-<col>`, the row locator), testid *prefix*
    (`CARD_ANY_CHIP`), and a bare class (`CHIP_ROOT_CSS`) — which the production
    code uses only to separate chips inside an already hook-addressed scope,
    never to locate a column, so modelling it does not smuggle class-based
    location into the stub.

    Anything else is deliberately unmatchable rather than an error: helpers
    legitimately probe for hooks this DOM does not model (`card-field-*`,
    `card-title`, `td`), and an empty result is the correct answer for those.
    """
    exact = "[data-testid='"
    prefix = "[data-testid^='"
    if selector.startswith(prefix) and selector.endswith("']"):
        return node.testid.startswith(selector[len(prefix) : -2])
    if selector.startswith(exact) and selector.endswith("']"):
        return node.testid == selector[len(exact) : -2]
    if selector.startswith(".") and " " not in selector:
        return selector[1:] in node.css_class.split()
    return False


def _w3c_error(error: str, message: str) -> dict[str, Any]:
    """Shape a driver error exactly as `RemoteConnection._request` returns one."""
    payload = {"value": {"error": error, "message": message, "stacktrace": ""}}
    return {"status": 404, "value": json.dumps(payload)}


class StubConnection:
    """A command executor answering from a `TableDom`, recording every call."""

    def __init__(self, dom: TableDom) -> None:
        self.dom = dom
        self.nodes: dict[str, StubNode] = {}
        self.calls: list[tuple[str, dict[str, Any]]] = []
        #: Callbacks fired *before* a command is answered, keyed by command name
        #: — how a test moves the DOM at an exact point in the round trip.
        self.before: dict[str, Callable[[dict[str, Any]], None]] = {}
        #: The identifying text of every node a click reached, in order. The
        #: tests' source of truth for *which record was activated*.
        self.clicked: list[str] = []

    def count(self, command: str) -> int:
        return sum(1 for name, _ in self.calls if name == command)

    def _register(self, nodes: list[StubNode]) -> list[dict[str, str]]:
        for node in nodes:
            self.nodes[node.id] = node
        return [{W3C_ELEMENT_KEY: node.id} for node in nodes]

    def execute(self, command: str, params: dict[str, Any]) -> dict[str, Any]:
        if command == Command.NEW_SESSION:
            return {"value": {"sessionId": "stub-session", "capabilities": {}}}

        self.calls.append((command, params))
        hook = self.before.get(command)
        if hook is not None:
            hook(params)

        node: StubNode | None = None
        if "id" in params:
            node = self.nodes.get(str(params["id"]))
            if node is None or not node.attached:
                return _w3c_error("stale element reference", f"{params['id']} is detached")

        if command == Command.FIND_ELEMENT:
            found = self.dom.match(self.dom.root, params["value"])
            if not found:
                return _w3c_error("no such element", f"nothing matches {params['value']!r}")
            return {"value": self._register(found[:1])[0]}
        if command == Command.FIND_ELEMENTS:
            return {"value": self._register(self.dom.match(self.dom.root, params["value"]))}
        if command == Command.FIND_CHILD_ELEMENTS:
            assert node is not None
            return {"value": self._register(self.dom.match(node, params["value"]))}
        if command == Command.GET_ELEMENT_TEXT:
            assert node is not None
            return {"value": node.text}
        if command == Command.CLICK_ELEMENT:
            assert node is not None
            self.clicked.append(node.text)
            return {"value": None}
        if command == Command.IS_ELEMENT_ENABLED:
            return {"value": True}
        if command == Command.W3C_EXECUTE_SCRIPT:
            return self._run_script(params)

        raise AssertionError(f"stub driver got an unmodelled command: {command}")

    def _run_script(self, params: dict[str, Any]) -> dict[str, Any]:
        """Answer `execute_script`, staleness first.

        Every element argument is checked for attachment before the script is
        answered, whatever the script is. That is what a real driver does — an
        atom is handed an element reference and the reference is resolved before
        the atom runs — and it is what makes the marshalling path (`is_displayed`
        and `get_attribute` are JS atoms in W3C mode, `remote/webelement.py:308`)
        a genuine staleness source rather than a modelled special case.
        """
        script = params["script"]
        for arg in params["args"]:
            if not isinstance(arg, dict) or W3C_ELEMENT_KEY not in arg:
                continue
            node = self.nodes.get(arg[W3C_ELEMENT_KEY])
            if node is None or not node.attached:
                return _w3c_error("stale element reference", "argument is detached")

        if script.startswith("/* isDisplayed */"):
            return {"value": True}
        if script.startswith("/* getAttribute */"):
            node = self.nodes[params["args"][0][W3C_ELEMENT_KEY]]
            attribute = params["args"][1]
            if attribute == "textContent":
                return {"value": node.text}
            if attribute == "class":
                # `None` for a class-less node, as a real driver answers for an
                # absent attribute — `_chip_elements` relies on the `or ""`.
                return {"value": node.css_class or None}
            return {"value": None}
        if "scrollIntoView" in script:
            return {"value": None}
        if ".matches(" in script:
            # `_swallows_row_click`: no cell in this DOM contains an interactive
            # node, so the click target resolves to the cell itself.
            return {"value": False}
        return {"value": "stub-script-value"}


@dataclass
class Harness:
    """A real `WebDriver` wired to a stub `DataTable`, plus the suite's `BasePage`."""

    dom: TableDom
    connection: StubConnection
    driver: WebDriver
    page: BasePage = field(init=False)

    def __post_init__(self) -> None:
        self.page = BasePage(self.driver, "http://stub.invalid")

    def rerender_once(
        self,
        command: str,
        names: list[str],
        *,
        script: str = "",
        chip_palette: str | None = None,
    ) -> None:
        """Re-render the table the first time *command* reaches the driver.

        The point of "once" is that the retry must then be able to finish: a DOM
        that never holds still would exercise the budget, not the recovery.
        """
        fired: list[int] = []

        def hook(params: dict[str, Any]) -> None:
            if fired or (script and script not in params.get("script", "")):
                return
            fired.append(1)
            self.dom.render(names, chip_palette=chip_palette)

        self.connection.before[command] = hook

    def settle_rows_on_second_lookup(self) -> None:
        """Let the *first* row scan see cell-less rows, then reconcile them in place.

        Hooked on the row lookup rather than on the cell read so the ordering is
        exact: scan #1 observes rows that cannot be read, which is the state
        under test; scan #2 — the retry — sees the same, still-attached rows with
        their cells filled in.
        """
        lookups: list[int] = []

        def hook(_params: dict[str, Any]) -> None:
            lookups.append(1)
            if len(lookups) == 2:
                self.dom.fill_in_cells()

        self.connection.before[Command.FIND_ELEMENTS] = hook

    def proxy_for(self, locator: tuple[str, str]) -> ReResolvingElement:
        """Capture *locator* as a self-healing reference, as a wait helper would."""
        return resolve_element(self.page.poll, locator, EC.presence_of_element_located, 5)

    def find_elements_always_returns(self, element: WebElement) -> None:
        """Make every `driver.find_elements` answer with *element*.

        The only way to hand a verdict site a *proxied* element: the site builds
        its own list from `driver.find_elements`, and that path yields raw
        elements today. Overriding it asks the question the opt-out exists for —
        would the verdict still hold if the plural path ever started healing? —
        instead of leaving the guard untested because it is currently inert.
        """
        self.driver.find_elements = lambda *_args, **_kwargs: [element]  # type: ignore[method-assign]


@pytest.fixture
def harness() -> Harness:
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    # No `driver.quit()`: it would issue a DELETE the stub does not model, and
    # there is no session, process or socket to release.
    return Harness(dom, connection, driver)


ROWS = ["alpha", "beta", "gamma"]


# ── 1. The helpers survive a re-render mid-use ───────────────────────────────


class TestSurvivesARerenderMidUse:
    """The property `retry_on_stale` is there for, measured rather than assumed."""

    def test_get_column_texts_survives_a_row_dying_mid_scan(self, harness: Harness) -> None:
        """The row list is re-read as a whole, so no partial result escapes.

        The re-render fires on the first cell read, so the scan genuinely hits a
        dead reference: the assertion on the command count is what separates
        "the helper recovered" from "the test never provoked anything".
        """
        harness.dom.render(ROWS)
        harness.rerender_once(Command.GET_ELEMENT_TEXT, ROWS)

        texts = harness.page.get_column_texts(COL)

        assert texts == ROWS
        assert harness.connection.count(Command.FIND_ELEMENTS) >= 2, (
            "the whole row lookup must have been re-run; a single lookup would mean "
            "the stale reference was never provoked"
        )

    def test_find_row_by_text_survives_a_row_dying_mid_scan(self, harness: Harness) -> None:
        """The scan is retried and the row handed back belongs to the live render."""
        harness.dom.render(ROWS)
        harness.rerender_once(Command.GET_ELEMENT_TEXT, ROWS)

        row = harness.page.find_row_by_text("beta")

        assert row is not None
        # Reading through the returned reference proves it is live: a reference
        # from the render that died would raise here.
        assert row.text == "beta"

    def test_find_row_by_text_still_answers_none_for_a_row_that_is_not_there(
        self, harness: Harness
    ) -> None:
        """The retry must not blur "no such row" into "the table moved"."""
        harness.dom.render(ROWS)

        assert harness.page.find_row_by_text("no-such-row") is None

    def test_click_row_survives_the_row_dying_before_the_click(self, harness: Harness) -> None:
        """The lookup and the click are one retryable unit, so the click lands."""
        harness.dom.render(ROWS)
        harness.rerender_once(Command.W3C_EXECUTE_SCRIPT, ROWS, script="scrollIntoView")

        harness.page.click_data_table_row(0, COL)

        assert harness.connection.clicked == ["alpha"]


class TestTheOtherRowOwningReaders:
    """The three helpers #835 P4 brought under the same rule as the first three.

    `retry_on_stale` may sit on any helper that does its own `find_elements`
    **and then reads through the elements it found** — and that clause selects
    six helpers in `base_page.py`, not the three that had it. These are the
    other three: they own their row lookup and then read `.text`, a class
    attribute or a child element off every row, so before P4 a re-render
    mid-scan let a raw `StaleElementReferenceException` out of what eight page
    objects present to their tests as a plain list read.

    Each test asserts the *command count* as well as the result: without it a
    green run cannot be told apart from a scan that never met a dead reference.
    """

    def test_get_all_row_text_fragments_survives_a_row_dying_mid_scan(
        self, harness: Harness
    ) -> None:
        """The `get_visible_*` reader behind harvest batches, tanks, pests and five more."""
        harness.dom.render(ROWS)
        harness.rerender_once(Command.GET_ELEMENT_TEXT, ROWS)

        fragments = harness.page.get_all_row_text_fragments()

        assert fragments == [["alpha"], ["beta"], ["gamma"]]
        assert harness.connection.count(Command.FIND_ELEMENTS) >= 2, (
            "the row lookup must have been re-run; one lookup means the stale "
            "reference was never provoked and the test proves nothing"
        )

    def test_get_column_chip_texts_survives_a_row_dying_mid_scan(self, harness: Harness) -> None:
        """Two levels through the captured row — the longest window of the three."""
        harness.dom.render(ROWS, chip_palette="success")
        harness.rerender_once(Command.GET_ELEMENT_TEXT, ROWS, chip_palette="success")

        assert harness.page.get_column_chip_texts(COL) == ROWS
        assert harness.connection.count(Command.FIND_ELEMENTS) >= 2

    def test_get_column_chip_colors_survives_a_row_dying_mid_scan(self, harness: Harness) -> None:
        """Same scan, killed on the class read rather than on the text read.

        `get_column_chip_colors` never reads text at all, so its only reachable
        staleness source is the `getAttribute` atom — which is a genuine one:
        the driver resolves the element reference before the atom runs.
        """
        harness.dom.render(ROWS, chip_palette="warning")
        harness.rerender_once(
            Command.W3C_EXECUTE_SCRIPT, ROWS, script="getAttribute", chip_palette="warning"
        )

        assert harness.page.get_column_chip_colors(COL) == ["warning"] * len(ROWS)
        assert harness.connection.count(Command.FIND_ELEMENTS) >= 2

    def test_a_table_that_never_settles_still_fails_loudly_and_in_budget(
        self, harness: Harness
    ) -> None:
        """The retry must not become an unbounded wait, and must stay loud.

        A table that re-renders on every read is a real failure, and the wrap
        must leave it one rather than absorbing it. Bounded by
        `retry_on_stale`'s own budget, which it checks *between* attempts —
        hence the slack of one attempt.
        """
        harness.dom.render(ROWS)
        harness.connection.before[Command.GET_ELEMENT_TEXT] = lambda _params: harness.dom.render(
            ROWS
        )

        started = time.monotonic()
        with pytest.raises(StaleElementReferenceException):
            harness.page.get_all_row_text_fragments()
        assert time.monotonic() - started <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK

    def test_a_table_that_empties_answers_with_an_empty_list_and_does_not_retry(
        self, harness: Harness
    ) -> None:
        """The limit of the wrap, pinned because it is easy to mistake for a gap.

        If the rows are gone from the DOM by the time the scan re-runs, the
        comprehension iterates nothing and the helper answers ``[]`` — the retry
        never sees a stale reference to react to. That is required, not
        tolerated: every "the deleted entry is no longer listed" assertion in
        the suite is an emptiness read, and a helper that raised instead of
        answering ``[]`` would break all of them. It is also the residual
        exposure — an empty list is indistinguishable from a table that has not
        rendered its rows *yet*, which is why the callers that care wrap this in
        a poll of their own rather than trusting one reading.

        Behaviour shared with `get_column_texts` and unchanged by #835 P4;
        pinned here so a later reader does not "fix" it.
        """
        harness.dom.render(ROWS)
        for node in harness.dom.root.descendants():
            node.attached = False
        harness.dom.root.children = []

        started = time.monotonic()
        assert harness.page.get_all_row_text_fragments() == []
        assert time.monotonic() - started < 1.0, "an empty table must not cost the retry budget"

    def test_the_readers_that_only_count_are_deliberately_left_alone(
        self, harness: Harness
    ) -> None:
        """The other half of the rule, pinned so the exclusion is not read as an oversight.

        `is_present` reads `len(...)` and never touches an element, so there is
        nothing that can go stale and nothing for a retry to do. Asserted as
        "it answers straight away, even while every element is dead" — the
        observable difference from a wrapped helper, which would spend its
        budget first.
        """
        harness.dom.render(ROWS)
        for node in harness.dom.root.descendants():
            node.attached = False

        started = time.monotonic()
        assert harness.page.is_present(BasePage.DATA_TABLE_ROWS) is False
        assert time.monotonic() - started < 1.0


# ── 2. The second signal: a row that is attached but not yet rendered ────────


class TestTheRowThatHasNotRenderedYet:
    """`TableNotSettled` — the gap #835 P4 actually closed.

    Before it, `retry_on_stale` covered only half of what a re-rendering table
    emits. A row whose children React reconciles in place stays attached, so
    nothing goes stale; it simply exposes no `cell-<col>` for a frame, and
    `get_row_primary_text` raises `AssertionError` — which `retry_on_stale` does
    not catch. Both helpers below failed on exactly this when these tests were
    first written.
    """

    def test_it_is_the_class_the_existing_retry_already_acts_on(self) -> None:
        """The reason for subclassing, stated as a check rather than as a comment."""
        assert issubclass(TableNotSettled, StaleElementReferenceException)
        assert issubclass(TableNotSettled, POLL_TRANSIENTS)

    def test_get_column_texts_waits_out_a_row_without_its_cell(self, harness: Harness) -> None:
        """A mid-render row is retried, not answered — and never answered with ``''``.

        No row goes stale anywhere in this test: the rows stay attached
        throughout and merely become readable. That is what separates this from
        the staleness tests above — and what the pre-P4 code failed on, because
        `retry_on_stale` had nothing to catch.
        """
        harness.dom.render_without_cells(ROWS)
        harness.settle_rows_on_second_lookup()

        assert harness.page.get_column_texts(COL) == ROWS

    def test_click_row_waits_out_a_row_without_its_cell(self, harness: Harness) -> None:
        """Same signal on the identity read, where it used to abort the click."""
        harness.dom.render_without_cells(ROWS)
        harness.settle_rows_on_second_lookup()

        harness.page.click_data_table_row(0, COL)

        assert harness.connection.clicked == ["alpha"]

    def test_a_column_that_never_renders_still_fails_loudly_and_in_budget(
        self, harness: Harness
    ) -> None:
        """The other half of the trade: an unreadable row is not silently tolerated.

        A wrongly addressed column looks exactly like a mid-render row at any one
        instant, so it now costs the retry budget before it surfaces. What must
        not change is that it *does* surface, that it keeps the original
        assertion's message — the sentence that names which hooks were looked for
        — and that it names both hypotheses so the reader can tell them apart.
        """
        harness.dom.render_without_cells(ROWS)

        started = time.monotonic()
        with pytest.raises(TableNotSettled) as raised:
            harness.page.get_column_texts(COL)
        elapsed = time.monotonic() - started

        message = str(raised.value)
        assert f"cell-{COL}" in message
        assert "the column id is wrong for this table" in message
        assert isinstance(raised.value.__cause__, AssertionError), (
            "the original assertion must survive as the cause, or the diagnosis is lost"
        )
        assert elapsed <= IMPLICIT_WAIT_EQUIVALENT + BUDGET_SLACK

    def test_the_scan_never_answers_an_unreadable_row_with_an_empty_string(
        self, harness: Harness
    ) -> None:
        """The failure mode the loud path exists to prevent.

        Returning ``''`` for a row that could not be read would make "the deleted
        entry is no longer listed" pass for the wrong reason — the silent-pass
        class `e2e-test-stability` §G forbids. Pinned as "it raises instead",
        because that is the only observable difference.
        """
        harness.dom.render_without_cells(["alpha"])

        with pytest.raises(TableNotSettled):
            harness.page.get_column_texts(COL)


# ── 3. The identity-based row recovery (#871) ────────────────────────────────


class TestTheIdentityGuard:
    """`click_data_table_row` re-finds by identifying cell and refuses the index."""

    def test_the_retry_re_finds_by_identity_not_by_index(self, harness: Harness) -> None:
        """The row is reordered mid-click; the click must still reach *that record*.

        This is the #871 regression in its sharpest form: after the re-render,
        index 0 is `gamma`. An index-based recovery would click it and report
        success, and the assertion that follows would test the wrong record.
        """
        harness.dom.render(ROWS)
        harness.rerender_once(
            Command.W3C_EXECUTE_SCRIPT, ["gamma", "beta", "alpha"], script="scrollIntoView"
        )

        harness.page.click_data_table_row(0, COL)

        assert harness.connection.clicked == ["alpha"], (
            "the retry re-selected by index instead of by identity — the exact defect #871 removed"
        )

    def test_it_refuses_the_index_when_the_identified_row_does_not_come_back(
        self, harness: Harness
    ) -> None:
        """A row that is genuinely gone fails; it does not activate a substitute."""
        harness.dom.render(ROWS)
        harness.rerender_once(
            Command.W3C_EXECUTE_SCRIPT, ["delta", "epsilon"], script="scrollIntoView"
        )

        with pytest.raises(TimeoutException) as raised:
            harness.page.click_data_table_row(0, COL)

        assert "Refusing to fall back to index 0" in str(raised.value)
        assert harness.connection.clicked == [], (
            "nothing may have been activated: the re-render lands before the click, so "
            "a substitute row from the new render is the only thing that could have "
            "been clicked here — and `delta` now sits at index 0"
        )

    def test_the_guard_does_not_extend_to_the_very_first_identity_read(
        self, harness: Harness
    ) -> None:
        """The measured boundary of the guard, pinned so the docstring cannot overclaim.

        If the table re-renders *during* the first identity read, the identity is
        never captured, the attempt is retried and the index is resolved against
        the new render — so a reorder in that window activates a different
        record. It is not fixable at this layer: before the first read there is
        no identity to re-find by, and the caller's index was derived from a
        render this method never saw.

        Pinned as it behaves, not as one would wish. Should a later change close
        it, this test fails and is the place to record how.
        """
        harness.dom.render(ROWS)
        harness.rerender_once(Command.GET_ELEMENT_TEXT, ["gamma", "beta", "alpha"])

        harness.page.click_data_table_row(0, COL)

        assert harness.connection.clicked == ["gamma"]


# ── 4. Staleness verdicts stay verdicts ──────────────────────────────────────


class TestVerdictsStayVerdicts:
    """The reads that *answer* with a stale reference must never heal.

    All of them build their element from `driver.find_elements`, which is not
    wrapped — so today they cannot be handed a proxy at all. These tests hand
    them one anyway. An opt-out that is only correct because nothing currently
    exercises it is not a guard, it is a coincidence; and this classification has
    already been derived twice and reversed once during #835.
    """

    DIALOG = (By.CSS_SELECTOR, "[data-testid='some-dialog']")

    def test_is_any_displayed_reports_gone_when_the_reference_dies(self, harness: Harness) -> None:
        """The plain case: a dialog unmounting mid fade-out is not displayed."""
        node = harness.dom.render_dialog("some-dialog")
        elements = harness.driver.find_elements(*self.DIALOG)
        node.attached = False
        harness.find_elements_always_returns(elements[0])

        assert harness.page.is_any_displayed(self.DIALOG) is False

    def test_is_any_displayed_refuses_to_heal_a_proxied_reference(self, harness: Harness) -> None:
        """A replacement under the same locator must not answer for the node that left.

        Without the `raw_reference` strip the proxy's re-resolution would find
        the fresh dialog and report ``True`` — turning "the dialog closed" into
        "a dialog is open" and hanging every close assertion in the suite on a
        node the test never saw close.
        """
        harness.dom.render_dialog("some-dialog")
        proxy = harness.proxy_for(self.DIALOG)
        # The captured node dies, but the locator still matches a fresh one —
        # exactly the situation the proxy exists to heal, and must not here.
        harness.dom.root.children[0].attached = False
        harness.dom.render_dialog("some-dialog")
        harness.find_elements_always_returns(proxy)

        assert harness.page.is_any_displayed(self.DIALOG) is False

    def test_is_displayed_in_scroll_container_refuses_to_heal_a_proxied_reference(
        self, harness: Harness
    ) -> None:
        """Same guard, the other `base_page` verdict: hidden must stay hidden.

        Both callers drive a *hidden*-ness decision from this, so a healed
        ``True`` would report "the app fails to hide this nav item" — or, in
        `navigate_via_sidebar`, silently skip the drawer it was meant to exercise.
        """
        harness.dom.render_dialog("some-dialog")
        proxy = harness.proxy_for(self.DIALOG)
        harness.dom.root.children[0].attached = False
        harness.dom.render_dialog("some-dialog")

        assert harness.page.is_displayed_in_scroll_container(proxy) is False

    def test_read_select_value_refuses_to_heal_a_proxied_trigger(self, harness: Harness) -> None:
        """The verdict whose ``None`` is what makes the click-verification loud.

        A healed trigger would let `_verify_select_committed` read a value back
        off the re-rendered Select instead of reporting that it could not read
        one — which is the whole point of the mechanism.
        """
        harness.dom.render_dialog("some-dialog")
        proxy = harness.proxy_for(self.DIALOG)
        harness.dom.root.children[0].attached = False
        harness.dom.render_dialog("some-dialog")

        assert harness.page._read_select_value(proxy, None) is None

    def test_submit_registered_refuses_to_heal_the_submit_button(self, harness: Harness) -> None:
        """The one verdict whose answer is a *success* signal, so the costliest to heal.

        `_submit_registered` returning ``True`` means "the click handed the form
        over to onSave". A healed reference would read the *re-rendered* submit
        button — which is enabled again on a form that never submitted — and the
        verdict would fall through to the snackbar probe, or, worse, report on a
        form the click never reached. Pinned by asserting that the snackbar is
        never consulted: reaching it would prove the stale branch was skipped.
        """
        page = TaskDetailPage(harness.driver, "http://stub.invalid")
        harness.dom.render_dialog("some-dialog")
        proxy = harness.proxy_for(self.DIALOG)
        harness.dom.root.children[0].attached = False
        harness.dom.render_dialog("some-dialog")
        harness.find_elements_always_returns(proxy)
        snackbar_probes: list[int] = []
        page.has_snackbar = lambda: bool(snackbar_probes.append(1))  # type: ignore[method-assign]

        assert page._submit_registered() is True
        assert snackbar_probes == [], (
            "the stale reference must have decided the verdict; consulting the "
            "snackbar means the reference healed and answered for the new form"
        )
