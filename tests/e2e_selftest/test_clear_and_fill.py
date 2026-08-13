"""Verification of `BasePage.clear_and_fill` / `require_interactable` (#986).

## What #986 reported

`clear_and_fill` performs two writes with *different* preconditions: a JS
write (`execute_script`, which performs no interactability check at all) and a
real `send_keys` (which does, and is what raised
`ElementNotInteractableException` in CI run 31182511811). A caller's own
`wait_for_element_clickable()` only proves interactability at *capture* time —
`DataTable`'s `LoadingSkeleton` (`DataTable.tsx:230`) unmounts the whole
toolbar, search box included, around every refetch, so that guarantee can
expire in the gap `clear_and_fill` itself takes (a `time.sleep(0.15)` between
the two writes). The fix re-asserts interactability, via
`BasePage.require_interactable`, immediately before *each* write.

## Why a real `WebDriver` over a stub command executor, not `fake_driver.FakeDriver`

Same reasoning as `test_element_proxy.py`: the property under test is what
Selenium itself decides is interactable, and the exact exception class that
decision raises. `fake_driver.FakeElement` has no `send_keys` at all and no
notion of "not interactable" distinct from "not displayed" — modelling this
class of bug needs the real client machinery (`WebElement._execute`,
`ErrorHandler.check_response`'s W3C-error-to-exception mapping, and the
`ReResolvingElement` proxy these page objects actually hand `clear_and_fill`).
Only the wire is fake.

## What is modelled, deliberately minimally

`SEND_KEYS_TO_ELEMENT` answers a real W3C `element not interactable` error
whenever the target node is hidden or disabled — exactly ChromeDriver's own
contract, and the one the CI failure actually hit. The JS write is modelled as
what it is: an `execute_script` call that mutates the stub node's `value`
*unconditionally*, i.e. with no interactability gate at all, because that
absence of a gate is the defect this test suite exists to make visible.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pytest
from selenium.common.exceptions import (
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.pages._element_proxy import RE_RESOLVE_TIMEOUT, resolve_element
from tests.e2e.pages.base_page import BasePage

#: The W3C element identifier key (see `test_element_proxy.py`).
W3C_ELEMENT_KEY = "element-6066-11e4-a52e-4f735466cecf"

SEARCH_INPUT = (By.CSS_SELECTOR, "[data-testid='table-search-input'] input")


@dataclass
class StubNode:
    """One `<input>` in the stub DOM."""

    element_id: str
    attached: bool = True
    enabled: bool = True
    displayed: bool = True
    value: str = ""


class StubDom:
    """A DOM with at most one live node under `SEARCH_INPUT`."""

    def __init__(self) -> None:
        self._nodes: dict[str, StubNode] = {}
        self._live: str | None = None
        self._counter = 0

    def render(self, *, enabled: bool = True, displayed: bool = True, value: str = "") -> str:
        if self._live is not None:
            self._nodes[self._live].attached = False
        self._counter += 1
        element_id = f"element-{self._counter}"
        self._nodes[element_id] = StubNode(
            element_id, enabled=enabled, displayed=displayed, value=value
        )
        self._live = element_id
        return element_id

    def remove(self) -> None:
        """Detach the live node for good, leaving the locator matching nothing."""
        if self._live is not None:
            self._nodes[self._live].attached = False
        self._live = None

    def match(self) -> str | None:
        return self._live

    def node(self, element_id: str) -> StubNode:
        return self._nodes[element_id]

    def is_attached(self, element_id: str) -> bool:
        node = self._nodes.get(element_id)
        return node is not None and node.attached


def _w3c_error(error: str, message: str) -> dict[str, Any]:
    """Shape a driver error exactly as `RemoteConnection._request` returns one (see `test_element_proxy.py`)."""
    payload = {"value": {"error": error, "message": message, "stacktrace": ""}}
    return {"status": 404, "value": json.dumps(payload)}


class StubConnection:
    """A command executor answering from a `StubDom`, recording every call."""

    def __init__(self, dom: StubDom) -> None:
        self.dom = dom
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.before: dict[str, Callable[[dict[str, Any]], None]] = {}

    def count(self, command: str) -> int:
        return sum(1 for name, _ in self.calls if name == command)

    def script_calls_matching(self, needle: str) -> int:
        return sum(
            1
            for name, params in self.calls
            if name == Command.W3C_EXECUTE_SCRIPT and needle in params["script"]
        )

    def execute(self, command: str, params: dict[str, Any]) -> dict[str, Any]:
        if command == Command.NEW_SESSION:
            return {"value": {"sessionId": "stub-session", "capabilities": {}}}

        self.calls.append((command, params))
        hook = self.before.get(command)
        if hook is not None:
            hook(params)

        if command == Command.FIND_ELEMENT:
            found = self.dom.match()
            if found is None:
                return _w3c_error("no such element", f"no element matches {params['value']!r}")
            return {"value": {W3C_ELEMENT_KEY: found}}

        element_id = params.get("id")
        if element_id is not None and not self.dom.is_attached(element_id):
            return _w3c_error("stale element reference", f"{element_id} is detached")

        if command == Command.IS_ELEMENT_ENABLED:
            return {"value": self.dom.node(str(element_id)).enabled}
        if command == Command.SEND_KEYS_TO_ELEMENT:
            node = self.dom.node(str(element_id))
            if not (node.displayed and node.enabled):
                return _w3c_error(
                    "element not interactable",
                    f"{element_id} is not currently interactable and may not be manipulated",
                )
            node.value = params["text"]
            return {"value": None}
        if command == Command.W3C_EXECUTE_SCRIPT:
            return self._run_script(params)

        raise AssertionError(f"stub driver got an unmodelled command: {command}")

    def _run_script(self, params: dict[str, Any]) -> dict[str, Any]:
        script = params["script"]
        args = params["args"]

        # Every element argument is resolved (and its staleness checked) before
        # the script runs, exactly as a real driver does.
        resolved: list[StubNode | None] = []
        for arg in args:
            if isinstance(arg, dict) and W3C_ELEMENT_KEY in arg:
                node_id = arg[W3C_ELEMENT_KEY]
                if not self.dom.is_attached(node_id):
                    return _w3c_error("stale element reference", "argument is detached")
                resolved.append(self.dom.node(node_id))
            else:
                resolved.append(None)

        if script.startswith("/* isDisplayed */"):
            assert resolved[0] is not None
            return {"value": resolved[0].displayed}
        if script.startswith("/* getAttribute */"):
            assert resolved[0] is not None
            attribute = args[1]
            return {"value": resolved[0].value if attribute == "value" else None}
        if "nativeInputValueSetter" in script:
            # `clear_and_fill`'s JS half: writes the value directly via the
            # prototype setter and dispatches synthetic events. Deliberately
            # unconditional -- no `displayed`/`enabled` check at all, because
            # that is exactly what a real `execute_script` call does not do
            # either. This is the mechanism #986 is about.
            assert resolved[0] is not None
            resolved[0].value = ""
            return {"value": None}
        raise AssertionError(f"stub driver got an unmodelled script: {script[:60]!r}")


@dataclass
class Harness:
    """A real `WebDriver` wired to a stub single-input DOM, plus the suite's `BasePage`."""

    dom: StubDom
    connection: StubConnection
    driver: WebDriver
    page: BasePage = field(init=False)

    def __post_init__(self) -> None:
        self.page = BasePage(self.driver, "http://stub.invalid")

    def capture(self, re_resolve_timeout: int = RE_RESOLVE_TIMEOUT):
        return resolve_element(
            self.page.poll,
            SEARCH_INPUT,
            EC.element_to_be_clickable,
            15,
            re_resolve_timeout=re_resolve_timeout,
        )


@pytest.fixture
def harness() -> Harness:
    dom = StubDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


# ── The bug, reproduced directly against Selenium's own client (no `BasePage`) ──


class TestTheRawBugReproduces:
    """`send_keys` on a hidden-but-attached field raises exactly what CI saw.

    Not through `clear_and_fill` -- through the bare Selenium client, so this
    is independent of whatever `clear_and_fill` does or does not guard. It is
    the baseline the fix is measured against.

    Each field is captured **while genuinely clickable** and hidden only
    afterwards -- mirroring the real bug rather than a field that was never
    usable. `wait_for_element_clickable()`, which every `clear_and_fill` caller
    goes through, cannot resolve a hidden element in the first place (it waits
    on `EC.element_to_be_clickable`, which requires displayed *and* enabled);
    the defect is that this proof expires, not that it was ever false.
    """

    def test_send_keys_on_a_hidden_field_raises_element_not_interactable(
        self, harness: Harness
    ) -> None:
        node_id = harness.dom.render()
        element = harness.capture()
        harness.dom.node(node_id).displayed = False

        with pytest.raises(ElementNotInteractableException, match="not currently interactable"):
            element.send_keys("x")

    def test_the_js_write_succeeds_on_the_very_same_hidden_field(self, harness: Harness) -> None:
        """The concrete claim #986 rests on: a write a user could not make.

        Same node, same hidden state, only the write mechanism differs. Where
        `send_keys` fails loudly, `execute_script` "succeeds" -- it has no
        interactability check to fail.
        """
        node_id = harness.dom.render(value="old")
        element = harness.capture()
        harness.dom.node(node_id).displayed = False

        harness.driver.execute_script(
            "var el = arguments[0];"
            "var nativeInputValueSetter = Object.getOwnPropertyDescriptor("
            "window.HTMLInputElement.prototype, 'value').set;"
            "nativeInputValueSetter.call(el, '');",
            element,
        )

        assert harness.dom.node(node_id).value == "", (
            "the JS write silently cleared a field no real user could have "
            "reached -- reproducing the defect #986 is about"
        )


# ── `require_interactable`: the guard on its own ─────────────────────────────


class TestRequireInteractable:
    def test_passes_silently_when_displayed_and_enabled(self, harness: Harness) -> None:
        harness.dom.render()
        element = harness.capture()

        harness.page.require_interactable(element, "test")  # must not raise

    def test_raises_and_names_hidden(self, harness: Harness) -> None:
        node_id = harness.dom.render()
        element = harness.capture()
        harness.dom.node(node_id).displayed = False

        with pytest.raises(AssertionError, match="hidden right now"):
            harness.page.require_interactable(element, "clear_and_fill (before send_keys)")

    def test_raises_and_names_disabled(self, harness: Harness) -> None:
        node_id = harness.dom.render()
        element = harness.capture()
        harness.dom.node(node_id).enabled = False

        with pytest.raises(AssertionError, match="disabled right now"):
            harness.page.require_interactable(element, "clear_and_fill (before send_keys)")

    def test_raises_a_diagnosable_error_when_genuinely_gone(self, harness: Harness) -> None:
        """A `ReResolvingElement` that exhausts its own healing budget still fails loudly.

        `require_interactable` must not let `ElementReResolutionError` (a
        `StaleElementReferenceException` subclass) escape as a bare Selenium
        exception with no context attached.
        """
        harness.dom.render()
        element = harness.capture(re_resolve_timeout=1)
        harness.dom.remove()  # nothing left to re-resolve to

        with pytest.raises(AssertionError, match="no longer attached to the DOM"):
            harness.page.require_interactable(element, "clear_and_fill (before send_keys)")

    def test_the_detached_failure_is_both_an_assertion_and_a_staleness(
        self, harness: Harness
    ) -> None:
        """The "gone" branch must be re-acquirable, not merely loud.

        `require_interactable`'s own message tells the caller what to do -- "the
        caller must re-capture the field once it has settled again" -- but a
        plain `AssertionError` gives it no way to: `BasePage.retry_on_stale`,
        the one helper that re-runs an acquisition, catches
        `StaleElementReferenceException` and nothing else. The same reasoning
        `TableNotSettled` was created under; the same fix.

        Both halves are asserted because both are load-bearing: the many
        existing `except AssertionError` sites (and the tests above) must keep
        matching, *and* the retry must see it.
        """
        harness.dom.render()
        element = harness.capture(re_resolve_timeout=1)
        harness.dom.remove()

        with pytest.raises(AssertionError) as caught:
            harness.page.require_interactable(element, "clear_and_fill (before send_keys)")

        assert isinstance(caught.value, StaleElementReferenceException), (
            "a detached field must be catchable by `retry_on_stale`, or the "
            "caller cannot act on the instruction the message gives it"
        )


# ── `clear_and_fill`: the guard wired into the write it protects ────────────


class TestClearAndFill:
    def test_happy_path_still_works(self, harness: Harness) -> None:
        """The fix must not change behaviour when nothing goes wrong."""
        node_id = harness.dom.render(value="old")
        element = harness.capture()

        harness.page.clear_and_fill(element, "new value")

        assert harness.dom.node(node_id).value == "new value"

    def test_refuses_before_the_js_write_when_hidden_before_the_call(
        self, harness: Harness
    ) -> None:
        """Decision #2: the JS half now refuses too, instead of writing through.

        Captured while clickable, then hidden before `clear_and_fill` is even
        called. Without this guard the JS write below would have silently
        succeeded (see `TestTheRawBugReproduces`); with it, `clear_and_fill`
        must fail *before* ever touching the field, and the write must be
        observably never attempted.
        """
        node_id = harness.dom.render(value="old")
        element = harness.capture()
        harness.dom.node(node_id).displayed = False

        with pytest.raises(AssertionError, match=r"before JS clear.*hidden right now"):
            harness.page.clear_and_fill(element, "new value")

        assert harness.connection.script_calls_matching("nativeInputValueSetter") == 0, (
            "the JS write must never have been attempted once the pre-check failed"
        )

    def test_refuses_before_send_keys_when_the_field_disappears_in_the_gap(
        self, harness: Harness
    ) -> None:
        """The exact race #986 reports: interactable at capture, gone by `send_keys`.

        The field is displayed when `clear_and_fill` starts (so the JS write
        runs and "succeeds"), and is hidden -- via a `before` hook firing on
        the *second* `isDisplayed` probe -- in the `time.sleep(0.15)` window
        between the JS write and `send_keys`. This is `DataTable`'s
        `LoadingSkeleton` swap, modelled at the one instant that matters.
        """
        node_id = harness.dom.render(displayed=True, value="old")
        element = harness.capture()
        probes = 0

        def hide_on_second_is_displayed_probe(params: dict[str, Any]) -> None:
            nonlocal probes
            if not params["script"].startswith("/* isDisplayed */"):
                return
            probes += 1
            if probes == 2:
                harness.dom.node(node_id).displayed = False

        harness.connection.before[Command.W3C_EXECUTE_SCRIPT] = hide_on_second_is_displayed_probe

        with pytest.raises(AssertionError, match=r"before send_keys.*hidden right now"):
            harness.page.clear_and_fill(element, "new value")

        assert harness.connection.script_calls_matching("nativeInputValueSetter") == 1, (
            "the JS write must have run exactly once -- it is not what this test refuses"
        )
        assert harness.dom.node(node_id).value == "", (
            "the JS write's own effect must be observable, so this is genuinely "
            "the write-then-vanish race and not the guard firing before anything "
            "was ever attempted (that shape is TestTheRawBugReproduces below)"
        )
        assert harness.connection.count(Command.SEND_KEYS_TO_ELEMENT) == 0, (
            "send_keys must never have been dispatched once the pre-check caught the gap"
        )


# ── `fill_table_search`: the caller-side half of the same race ──────────────


class TestFillTableSearch:
    """The toolbar can die between the capture and the write; the caller re-captures.

    `require_interactable` closes the "write through the gap" half: it refuses
    to enter a value into a field the user could not have typed into. What it
    cannot do is *make the write happen* -- by design, since a retry inside
    `clear_and_fill` would re-enter the window it just failed in.

    The 2026-08-13 nightly showed the other half is missing. `search()` on the
    `DataTable` list pages captures the search box and writes to it, and every
    caller that searches right after a mutation hands it the one moment the box
    is guaranteed to move: `DataTable`'s `LoadingSkeleton` unmounts the whole
    toolbar around the refetch. `test_view_profiles_for_growth_phase` and
    `test_delete_growth_phase` both failed there, in
    `_provision_species_with_phase` -> `click_row_by_name` -> `search` ->
    `clear_and_fill`.

    The race is modelled exactly as it happens, and it is *not* one a
    `ReResolvingElement` can heal: the liveness probe in the proxy's `id`
    property answers for a node that is still attached, and the node dies
    between that probe and the script it was marshalled into. Healing happens
    inside `_execute`; this exception comes out of `driver.execute_script`.
    """

    def _kill_the_toolbar_on_first_read(self, harness: Harness) -> None:
        """Replace the live node the first time an `isDisplayed` probe is dispatched.

        Fires *inside* the command, i.e. after the element argument has already
        been marshalled -- which is what makes this the un-healable window
        rather than a re-render the proxy absorbs.
        """
        fired: list[int] = []

        def hook(params: dict[str, Any]) -> None:
            if fired or "/* isDisplayed */" not in params.get("script", ""):
                return
            fired.append(1)
            harness.dom.render()  # detaches the captured node, mounts a fresh one

        harness.connection.before[Command.W3C_EXECUTE_SCRIPT] = hook

    def test_happy_path_writes_the_term(self, harness: Harness) -> None:
        harness.dom.render(value="old")

        harness.page.fill_table_search(SEARCH_INPUT, "tomato")

        live = harness.dom.match()
        assert live is not None
        assert harness.dom.node(live).value == "tomato"

    def test_a_toolbar_remount_mid_write_is_re_captured(self, harness: Harness) -> None:
        """The term lands in the *replacement*, not in the node that left."""
        first = harness.dom.render(value="old")
        self._kill_the_toolbar_on_first_read(harness)

        harness.page.fill_table_search(SEARCH_INPUT, "tomato")

        live = harness.dom.match()
        assert live is not None and live != first, (
            "the DOM must genuinely have moved underneath, or this test proves nothing"
        )
        assert harness.dom.node(live).value == "tomato"

    def test_a_search_box_that_never_comes_back_still_fails(self, harness: Harness) -> None:
        """The retry re-acquires; it does not paper over an absent toolbar.

        The negative half of the contract. Without it a helper that swallowed
        the failure and returned would satisfy every assertion above.
        """
        harness.dom.render()
        harness.dom.remove()

        with pytest.raises(TimeoutException):
            harness.page.fill_table_search(SEARCH_INPUT, "tomato", timeout=1)
