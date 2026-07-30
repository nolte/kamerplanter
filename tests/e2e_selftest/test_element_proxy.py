"""Verification of the re-resolving element reference (`tests/e2e/pages/_element_proxy.py`).

## Why these tests live here — and in neither of the two obvious places

**Not under `src/backend/tests/unit/`**, the tier the one required check
(`Static CI Tests`, `pytest tests/unit/` from `src/backend`) runs: that tier
enforces a **no-Selenium rule**. `src/backend/tests/unit/`
`test_gherkin_line_classification.py` asserts `selenium_modules == []`, and
Selenium is not a backend dependency at all. A module importing `selenium`
cannot live there; moving it would break the backend gate, not extend it.

**Not under `tests/e2e/`** either, although that is where the browser suite
lives. `tests/e2e/README.md` states the rule outright — browser-free unit tests
belong here, "deliberately outside this directory so they need no stack and do
not change this suite's collected count" — and the mechanics back it up:
`tests/e2e/conftest.py` makes `screenshot` (`:1250`) and `ensure_authenticated`
(`:1149`) **autouse**, and both request the `browser` fixture. Every test under
`tests/e2e/` therefore opens a real Grid session whether it needs one or not,
and the session-scoped autouse `e2e_seed_data` (`:661`) additionally seeds the
running backend over HTTP. Putting a pure client-side contract test there would
buy 16 browser sessions and a stack dependency for logic that touches neither.

So: this tier — same tier as `src/backend/tests/unit/` by
`spec/project/test-pyramid-foundation/`, different subject (the harness itself).
Run it with `task test:e2e:selftest`. **Do not "helpfully" relocate it.**

## Why there is no browser here

The proxy's whole job is what happens *between* a resolution and its use, and
that is a property of the Selenium client, not of a page. Driving a real browser
to it would mean provoking a React re-render at a precise moment — the flakiest
possible way to assert a deterministic contract.

So the driver is stubbed, but nothing else is: the tests construct a **real**
`selenium.webdriver.remote.webdriver.WebDriver` over a fake command executor.
Every Selenium code path the proxy depends on therefore runs for real —
`_wrap_value`'s element detection, `ErrorHandler.check_response`'s mapping of a
W3C `stale element reference` payload onto the exception class,
`WebDriverWait.until`'s ignored-exception handling and its poll granularity, and
the `expected_conditions` predicates. Only the wire is fake.

That is a different level of fake from this tier's `fake_driver.FakeDriver`,
which duck-types the handful of methods `BasePage` calls. It is not shared with
it for that reason: `BasePage`'s settling logic can be tested above the client,
whereas the proxy *is* an extension of the client and has to be tested through
it. The thing under test is never mocked; if it were, these tests would assert
their own expectations back at themselves, which is precisely the failure mode
this verification exists to rule out.

## What is being defended against

The proxy is about to sit under all 459 capture sites in the E2E suite, so a
wrong one changes behaviour **everywhere and silently**. Two opposite failures
matter equally:

* it fails to heal what it claims to heal (the suite stays as flaky as before,
  but now with a mechanism that says otherwise), and
* it heals what should stay broken (the suite goes green without going true) —
  see `TestGoneStaysGone`, which pins that a genuinely removed element still
  fails, and fails inside the small budget rather than at some outer timeout.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tests.e2e.pages._element_proxy import (
    MAX_RE_RESOLUTIONS,
    RE_RESOLVE_TIMEOUT,
    ElementReResolutionError,
    ReResolvingElement,
    resolve_element,
)
from tests.e2e.pages.base_page import DEFAULT_TIMEOUT, POLL_TRANSIENTS, BasePage

#: The W3C element identifier key. Restated rather than imported because
#: Selenium spells it as a bare literal in `_wrap_value` / `_unwrap_value`
#: (`remote/webdriver.py:411`, `:424`) and exports no constant for it.
W3C_ELEMENT_KEY = "element-6066-11e4-a52e-4f735466cecf"

#: The locator every test captures through. One selector is enough: the proxy's
#: behaviour depends on *whether* the locator still matches, never on what it is.
BUTTON = (By.CSS_SELECTOR, "#btn")

#: How far a re-resolution that has to wait out its whole budget may overshoot
#: it. `WebDriverWait` polls on a 0.5 s grid (`support/wait.py:110-121`) and
#: `_re_resolve` rounds the remaining budget up to whole seconds, so a small
#: overshoot is by design; anything beyond this would mean the bound is not the
#: one the module documents.
BUDGET_SLACK = 1.5


# ── A DOM the tests can move underneath the proxy ────────────────────────────


@dataclass
class StubNode:
    """One element in the stub DOM."""

    element_id: str
    #: False once the node has been replaced or removed — every command against
    #: it then answers with a W3C `stale element reference`, exactly as a real
    #: driver does for a detached node.
    attached: bool = True
    enabled: bool = True
    displayed: bool = True


class StubDom:
    """A DOM with at most one live node per selector, plus the nodes it replaced.

    Deliberately tiny. It models the only two DOM events the proxy reacts to: a
    node is *replaced* by a new one under the same locator (a React re-render,
    which the proxy must heal), and a node is *removed* with nothing taking its
    place (which the proxy must **not** heal).
    """

    def __init__(self) -> None:
        self._nodes: dict[str, StubNode] = {}
        self._live: dict[str, str | None] = {}
        self._visible_from: dict[str, float] = {}
        self._counter = 0

    def render(
        self,
        selector: str,
        *,
        enabled: bool = True,
        displayed: bool = True,
        after: float = 0.0,
    ) -> str:
        """Replace whatever is under *selector* with a fresh node; return its id.

        *after* delays the moment the new node becomes findable, leaving the
        locator matching nothing in between — the re-render gap a capture falls
        into. The **old** node dies immediately either way.
        """
        self._detach_current(selector)
        self._counter += 1
        element_id = f"element-{self._counter}"
        self._nodes[element_id] = StubNode(element_id, enabled=enabled, displayed=displayed)
        self._live[selector] = element_id
        self._visible_from[selector] = time.monotonic() + after
        return element_id

    def remove(self, selector: str) -> None:
        """Detach the node under *selector* and leave the locator matching nothing."""
        self._detach_current(selector)
        self._live[selector] = None

    def match(self, selector: str) -> str | None:
        """Return the id a `findElement` for *selector* would answer with."""
        element_id = self._live.get(selector)
        if element_id is None:
            return None
        if time.monotonic() < self._visible_from.get(selector, 0.0):
            return None
        return element_id

    def node(self, element_id: str) -> StubNode:
        return self._nodes[element_id]

    def is_attached(self, element_id: str) -> bool:
        node = self._nodes.get(element_id)
        return node is not None and node.attached

    def _detach_current(self, selector: str) -> None:
        current = self._live.get(selector)
        if current is not None:
            self._nodes[current].attached = False


def _w3c_error(error: str, message: str) -> dict[str, Any]:
    """Shape a driver error exactly as `RemoteConnection._request` returns one.

    `remote_connection.py:445-446` returns `{"status": <http code>, "value":
    <raw json string>}` for any 4xx, and `ErrorHandler.check_response`
    (`errorhandler.py:155-196`) parses *that* shape to pick the exception class.
    Returning it verbatim is what makes the staleness these tests provoke a
    genuine Selenium-constructed `StaleElementReferenceException` rather than one
    the test raised itself.
    """
    payload = {"value": {"error": error, "message": message, "stacktrace": ""}}
    return {"status": 404, "value": json.dumps(payload)}


class StubConnection:
    """A command executor answering from a `StubDom`, recording every call.

    Stands in for `RemoteConnection` at the only seam `WebDriver` uses it
    through: `execute(command, params) -> dict`. Everything above that seam is
    the real client.
    """

    def __init__(self, dom: StubDom) -> None:
        self.dom = dom
        #: Every `(command, params)` in order — the tests' only source of truth
        #: for *what actually reached the driver*, which is the difference
        #: between "the proxy healed" and "the assertion says it did".
        self.calls: list[tuple[str, dict[str, Any]]] = []
        #: Callbacks fired *before* a command is answered, keyed by command name.
        #: How a test moves the DOM at an exact point in the round trip without
        #: sleeping for it.
        self.before: dict[str, Callable[[dict[str, Any]], None]] = {}

    def count(self, command: str) -> int:
        return sum(1 for name, _ in self.calls if name == command)

    def params_for(self, command: str) -> list[dict[str, Any]]:
        return [params for name, params in self.calls if name == command]

    def execute(self, command: str, params: dict[str, Any]) -> dict[str, Any]:
        if command == Command.NEW_SESSION:
            return {"value": {"sessionId": "stub-session", "capabilities": {}}}

        self.calls.append((command, params))
        hook = self.before.get(command)
        if hook is not None:
            hook(params)

        if command == Command.FIND_ELEMENT:
            found = self.dom.match(params["value"])
            if found is None:
                return _w3c_error("no such element", f"no element matches {params['value']!r}")
            return {"value": {W3C_ELEMENT_KEY: found}}

        element_id = params.get("id")
        if element_id is not None and not self.dom.is_attached(element_id):
            return _w3c_error("stale element reference", f"{element_id} is detached")

        if command == Command.IS_ELEMENT_ENABLED:
            return {"value": self.dom.node(str(element_id)).enabled}
        if command == Command.CLICK_ELEMENT:
            return {"value": None}
        if command == Command.W3C_EXECUTE_SCRIPT:
            return self._run_script(params)

        raise AssertionError(f"stub driver got an unmodelled command: {command}")

    def _run_script(self, params: dict[str, Any]) -> dict[str, Any]:
        """Answer `execute_script`, including Selenium's own `isDisplayed` atom.

        `WebElement.is_displayed` is not a wire command in W3C mode — it ships a
        JavaScript atom, prefixed with an `/* isDisplayed */` marker
        (`remote/webelement.py:308`), and passes the element as an argument.
        `EC.visibility_of` reaches the DOM through this path, so it has to be
        modelled for the clickable condition to mean anything.
        """
        script = params["script"]
        args = params["args"]
        if script.startswith("/* isDisplayed */"):
            target = args[0][W3C_ELEMENT_KEY]
            if not self.dom.is_attached(target):
                return _w3c_error("stale element reference", f"{target} is detached")
            return {"value": self.dom.node(target).displayed}
        return {"value": "script-return-value"}


@dataclass
class Harness:
    """A real `WebDriver` wired to a stub DOM, plus the suite's own poll contract."""

    dom: StubDom
    connection: StubConnection
    driver: WebDriver
    #: The suite's own `BasePage`, so the poll used for re-resolution is the real
    #: one (`POLL_TRANSIENTS` and all) rather than a test-local lookalike.
    page: BasePage = field(init=False)
    #: Every timeout the proxy asked a wait for, in order. Index 0 is the
    #: original capture; the rest are re-resolutions. This is the module's own
    #: seam (`PollFactory`), so what it is called with is directly observable —
    #: which makes "how much budget is this attempt given" assertable without
    #: inferring it from a stopwatch.
    poll_timeouts: list[int] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.page = BasePage(self.driver, "http://stub.invalid")

    def poll(self, timeout: int) -> WebDriverWait:
        self.poll_timeouts.append(timeout)
        return self.page.poll(timeout)

    def capture(
        self,
        condition: Callable[[tuple[str, str]], Any],
        *,
        locator: tuple[str, str] = BUTTON,
        re_resolve_timeout: int = RE_RESOLVE_TIMEOUT,
    ) -> ReResolvingElement:
        """Take a capture the way a page object will once the wait helpers are wired."""
        return resolve_element(
            self.poll, locator, condition, DEFAULT_TIMEOUT, re_resolve_timeout=re_resolve_timeout
        )


@pytest.fixture
def harness() -> Iterator[Harness]:
    dom = StubDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    yield Harness(dom, connection, driver)
    # No `driver.quit()`: it would issue a DELETE the stub does not model, and
    # there is no session, process or socket to release.


def _remove_on_retry(harness: Harness) -> Callable[[dict[str, Any]], None]:
    """Remove the element for good once the *retried* command reaches the driver."""
    seen: list[str] = []

    def hook(params: dict[str, Any]) -> None:
        seen.append(str(params.get("id")))
        if len(seen) == 2:
            harness.dom.remove("#btn")

    return hook


# ── The type identity the whole design rests on ──────────────────────────────


class TestTypeIdentity:
    """`isinstance(proxy, WebElement)` is not cosmetic — Selenium branches on it."""

    def test_the_proxy_is_a_real_web_element_and_marshals_as_one(self, harness: Harness) -> None:
        """`_wrap_value` recognises the proxy and serialises its id (webdriver.py:410)."""
        harness.dom.render("#btn")

        proxy = harness.capture(EC.presence_of_element_located)

        assert isinstance(proxy, WebElement)
        assert harness.driver._wrap_value(proxy) == {W3C_ELEMENT_KEY: proxy._id}

    def test_an_expected_condition_treats_the_proxy_as_an_element(self, harness: Harness) -> None:
        """`EC.element_to_be_clickable` must not unpack the proxy as a locator tuple.

        `expected_conditions.py:517` does `if not isinstance(target, WebElement):
        target = driver.find_element(*target)`. The observable consequence of
        getting this right is that the condition answers with the very object it
        was handed and issues **no** lookup of its own.
        """
        harness.dom.render("#btn")
        proxy = harness.capture(EC.element_to_be_clickable)
        finds_before = harness.connection.count(Command.FIND_ELEMENT)

        result = EC.element_to_be_clickable(proxy)(harness.driver)

        assert result is proxy
        assert harness.connection.count(Command.FIND_ELEMENT) == finds_before

    def test_a_forwarding_wrapper_would_be_unpacked_as_a_locator(self, harness: Harness) -> None:
        """The refutation the subclass design rests on, pinned as a test.

        A `__getattr__`-forwarding wrapper — the shape #835 originally proposed —
        is not a `WebElement`, so the same branch feeds it to
        `find_element(*target)`. No amount of attribute forwarding helps: the
        check is on the type. This is why the proxy inherits instead of wrapping.
        """
        harness.dom.render("#btn")
        raw = harness.driver.find_element(*BUTTON)

        class ForwardingWrapper:
            def __init__(self, inner: WebElement) -> None:
                self._inner = inner

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

        with pytest.raises(TypeError, match="must be an iterable"):
            EC.element_to_be_clickable(ForwardingWrapper(raw))(harness.driver)


# ── Healing ──────────────────────────────────────────────────────────────────


class TestHealing:
    """A reference that lost its node re-acquires it and finishes the command."""

    def test_a_stale_reference_heals_and_the_command_reaches_the_new_node(
        self, harness: Harness
    ) -> None:
        """The click lands on the replacement, not on the node that died."""
        dead = harness.dom.render("#btn")
        proxy = harness.capture(EC.element_to_be_clickable)
        replacement = harness.dom.render("#btn")
        assert replacement != dead

        proxy.click()

        clicked = [params["id"] for params in harness.connection.params_for(Command.CLICK_ELEMENT)]
        assert clicked == [dead, replacement], (
            "the first click must genuinely hit the dead reference (otherwise the test "
            "is not exercising a real stale error) and the retry must hit the replacement"
        )
        assert proxy._id == replacement

    def test_execute_script_marshals_the_post_heal_element_id(self, harness: Harness) -> None:
        """The liveness probe on the `id` property is what makes this true.

        `execute_script` never goes through `WebElement._execute`: the driver
        reads `proxy.id` while marshalling and sends whatever it gets. Without
        the probe a dead id would reach JavaScript, where no proxy can heal it.
        Live call sites: `base_page.py:867`, `:925`, `:1259`,
        `sensor_create_dialog_page.py:110`.
        """
        dead = harness.dom.render("#btn")
        proxy = harness.capture(EC.presence_of_element_located)
        replacement = harness.dom.render("#btn")

        harness.driver.execute_script("arguments[0].scrollIntoView();", proxy)

        marshalled = [
            arg[W3C_ELEMENT_KEY]
            for params in harness.connection.params_for(Command.W3C_EXECUTE_SCRIPT)
            if not params["script"].startswith("/* isDisplayed */")
            for arg in params["args"]
        ]
        assert marshalled == [replacement]
        assert dead not in marshalled

    def test_a_clickable_capture_only_heals_to_a_clickable_element(self, harness: Harness) -> None:
        """The property `resolve_element` enforces by construction.

        A capture taken as *clickable* must come back as something clickable. The
        replacement here is rendered **disabled** and only becomes enabled after
        two enabledness probes, so a heal that settled for mere presence would be
        observable: it would finish while the node was still disabled.
        """
        harness.dom.render("#btn")
        proxy = harness.capture(EC.element_to_be_clickable)
        replacement = harness.dom.render("#btn", enabled=False)
        probes = 0

        def enable_on_second_probe(params: dict[str, Any]) -> None:
            nonlocal probes
            if params.get("id") != replacement:
                return
            probes += 1
            if probes >= 2:
                harness.dom.node(replacement).enabled = True

        harness.connection.before[Command.IS_ELEMENT_ENABLED] = enable_on_second_probe

        proxy.click()

        assert proxy._id == replacement
        assert probes >= 2, "the heal must have waited out the disabled state, not skipped it"
        assert harness.dom.node(replacement).enabled

    def test_a_presence_capture_heals_to_a_merely_present_element(self, harness: Harness) -> None:
        """The contrast that makes the previous test a measurement, not a wish.

        Same DOM move, same proxy, only the condition differs — and with
        *presence* the very same disabled replacement is accepted immediately.
        The condition is therefore what carries the guarantee, which is why it
        has to travel with the reference instead of being re-chosen at heal time.
        """
        harness.dom.render("#btn")
        proxy = harness.capture(EC.presence_of_element_located)
        replacement = harness.dom.render("#btn", enabled=False)

        proxy.click()

        assert proxy._id == replacement
        assert harness.dom.node(replacement).enabled is False


# ── Budget ───────────────────────────────────────────────────────────────────


class TestBudget:
    """Both bounds hold on their own, and neither degenerates into a spin."""

    def test_the_wall_clock_budget_bounds_a_replacement_that_never_qualifies(
        self, harness: Harness
    ) -> None:
        """A node that is present but never clickable fails near `RE_RESOLVE_TIMEOUT`.

        Runs against the shipped default rather than an injected one: the value
        that actually bounds the suite is the one worth measuring.
        """
        harness.dom.render("#btn")
        proxy = harness.capture(EC.element_to_be_clickable)
        harness.dom.render("#btn", enabled=False)

        started = time.monotonic()
        with pytest.raises(ElementReResolutionError):
            proxy.click()
        elapsed = time.monotonic() - started

        assert elapsed >= RE_RESOLVE_TIMEOUT - BUDGET_SLACK, (
            "failing far below the budget would mean the wait is not actually being spent"
        )
        assert elapsed <= RE_RESOLVE_TIMEOUT + BUDGET_SLACK
        assert elapsed < DEFAULT_TIMEOUT

    def test_the_attempt_cap_fires_before_the_clock_can_run_out(self, harness: Harness) -> None:
        """A DOM re-rendering faster than a round trip stops on the count, not the clock.

        Every heal here succeeds instantly and the node is replaced again before
        the retried click reaches it, so the wall clock would never expire — the
        loop would spin. It stops after exactly `MAX_RE_RESOLUTIONS`
        re-resolutions, in a small fraction of the time budget.
        """
        harness.dom.render("#btn")
        proxy = harness.capture(EC.element_to_be_clickable)
        finds_before = harness.connection.count(Command.FIND_ELEMENT)
        harness.connection.before[Command.CLICK_ELEMENT] = lambda _: harness.dom.render("#btn")

        started = time.monotonic()
        with pytest.raises(ElementReResolutionError, match="re-resolutions allowed per command"):
            proxy.click()
        elapsed = time.monotonic() - started

        re_resolutions = harness.connection.count(Command.FIND_ELEMENT) - finds_before
        assert re_resolutions == MAX_RE_RESOLUTIONS
        assert harness.connection.count(Command.CLICK_ELEMENT) == MAX_RE_RESOLUTIONS + 1
        assert elapsed < RE_RESOLVE_TIMEOUT, "stopped on the attempt cap, not on the clock"

    def test_the_deadline_is_taken_once_per_command_not_once_per_attempt(
        self, harness: Harness
    ) -> None:
        """Several re-resolutions share one budget instead of each getting a fresh one.

        The node is replaced with a 0.8 s re-render gap, so the first heal spends
        about a second of the budget before succeeding; the retried click then
        finds the node removed for good, forcing a second attempt. What that
        second attempt is *given* is the property under test: a shared deadline
        hands it only the remainder, a per-attempt one would hand it a fresh full
        budget — and `MAX_RE_RESOLUTIONS` of those would make one command cost
        three budgets.

        Asserted on the timeouts the proxy asks its poll factory for rather than
        on a stopwatch: with a re-render this fast the two implementations differ
        by barely a second of wall clock, which is inside the poll granularity —
        a timing assertion there would be a coin flip, not a measurement.

        Uses an injected 2 s budget rather than the default because the property
        — *when* the deadline is taken — is independent of its value, and the
        default would only make the test slower.
        """
        budget = 2
        harness.dom.render("#btn")
        proxy = harness.capture(EC.presence_of_element_located, re_resolve_timeout=budget)
        harness.dom.render("#btn", after=0.8)
        harness.connection.before[Command.CLICK_ELEMENT] = _remove_on_retry(harness)

        started = time.monotonic()
        with pytest.raises(ElementReResolutionError):
            proxy.click()
        elapsed = time.monotonic() - started

        assert harness.connection.count(Command.CLICK_ELEMENT) == 2, (
            "the first heal must have succeeded and the command been retried, so that the "
            "second re-resolution is genuinely a second attempt under the same budget"
        )
        first_attempt, second_attempt = harness.poll_timeouts[1:3]
        assert first_attempt == budget
        assert second_attempt < first_attempt, (
            "the second attempt must inherit what the first one left of the budget; "
            "getting the full budget again would mean the deadline restarts per attempt"
        )
        assert elapsed <= budget + BUDGET_SLACK


# ── The failure that must survive the mechanism ──────────────────────────────


class TestGoneStaysGone:
    """A removed element must stay a failure — the masking risk the suite review looks for."""

    def test_a_removed_element_still_fails_and_fails_inside_the_small_budget(
        self, harness: Harness
    ) -> None:
        """Nothing matches the locator any more, so the command fails — and fails *fast*.

        Both halves are one behaviour and are asserted together: a proxy that
        turned "this element is gone" into "wait longer" would be the masking
        failure the suite review looks for, and it would show up either as no
        exception at all or as an exception that arrives at some outer timeout.
        `RE_RESOLVE_TIMEOUT` is deliberately 3 s and not `DEFAULT_TIMEOUT` (15 s)
        precisely so a genuine absence stays cheap; if the two ever converged,
        every real failure in the suite would become five times slower to
        surface.
        """
        harness.dom.render("#btn")
        proxy = harness.capture(EC.presence_of_element_located)
        harness.dom.remove("#btn")

        started = time.monotonic()
        with pytest.raises(ElementReResolutionError):
            proxy.click()
        elapsed = time.monotonic() - started

        assert elapsed <= RE_RESOLVE_TIMEOUT + BUDGET_SLACK
        assert elapsed < DEFAULT_TIMEOUT


# ── Identity across a heal ───────────────────────────────────────────────────


class TestIdentityAcrossAHeal:
    """`==` and `hash` keep telling the truth about what the reference points at."""

    def test_equality_and_hash_follow_the_healed_reference(self, harness: Harness) -> None:
        dead = harness.dom.render("#btn")
        proxy = harness.capture(EC.presence_of_element_located)
        before_heal = harness.driver.find_element(*BUTTON)
        assert proxy == before_heal
        assert hash(proxy) == hash(before_heal)

        replacement = harness.dom.render("#btn")
        proxy.click()
        after_heal = harness.driver.find_element(*BUTTON)

        assert after_heal._id == replacement
        assert proxy == after_heal
        assert hash(proxy) == hash(after_heal)
        assert proxy != before_heal
        assert before_heal._id == dead, "the pre-heal reference still names the node that died"

    def test_the_reverse_comparison_is_answered_by_the_proxy_itself(self, harness: Harness) -> None:
        """`raw == proxy` does **not** reach `WebElement.__eq__`.

        Worth pinning because it is easy to assume the opposite. Selenium's own
        `__eq__` (`webelement.py:489`) reads `element.id`, which on a proxy would
        fire a liveness probe — a round trip, and possibly a re-resolution — from
        inside an `==`. Python's reflected-operand rule prevents that:
        `ReResolvingElement` is a proper subclass of `WebElement` and overrides
        `__eq__`, so the *right* operand's implementation is tried first. Both
        directions therefore run the proxy's side-effect-free comparison, and the
        observable proof is that comparing issues no driver command at all.
        """
        harness.dom.render("#btn")
        proxy = harness.capture(EC.presence_of_element_located)
        replacement = harness.dom.render("#btn")
        proxy.click()
        after_heal = harness.driver.find_element(*BUTTON)
        calls_before = len(harness.connection.calls)

        assert after_heal == proxy
        assert not (proxy != after_heal)

        assert len(harness.connection.calls) == calls_before, (
            "comparing must not talk to the driver — a probing __eq__ could heal, or "
            "raise, from inside a comparison"
        )
        assert proxy._id == replacement

    def test_comparing_two_proxies_neither_probes_nor_heals(self, harness: Harness) -> None:
        """The case Selenium's own `__eq__` would turn into a re-resolution.

        `WebElement.__eq__` reads `other.id`; with a proxy on the right that is
        the liveness-probing property, so `==` would issue a round trip and could
        *heal one of the two operands mid-comparison* — after which two
        references to the same (now dead) node compare **unequal**, because one
        moved on and the other did not. The proxy's own `__eq__` compares the
        held ids instead, so a comparison stays a question rather than an action.
        """
        harness.dom.render("#btn")
        one = harness.capture(EC.presence_of_element_located)
        other = harness.capture(EC.presence_of_element_located)
        assert one is not other
        harness.dom.render("#btn")  # both references are stale from here on
        calls_before = len(harness.connection.calls)

        assert one == other

        assert len(harness.connection.calls) == calls_before
        assert one._id == other._id, "neither operand may have been healed by the comparison"


# ── Interaction with the enclosing poll (documented as-is) ───────────────────


class TestExhaustionInsideAPoll:
    """What an exhausted budget actually does when it happens inside `BasePage.poll`.

    Pinned **as it behaves**, not as one might wish it behaved, so the Python
    review can judge the trade-off on evidence. Do not "fix" the module to make
    this test read better — that decision belongs to the review, not here.

    `ElementReResolutionError` subclasses `StaleElementReferenceException` on
    purpose, so that `retry_on_stale` and `POLL_TRANSIENTS` keep working. But
    `POLL_TRANSIENTS` (`base_page.py:50`) contains exactly that class — so an
    exhaustion *inside* a poll is treated as "not yet", its diagnostic is
    dropped, and the caller eventually sees a bare `TimeoutException`. The
    exhaustion message, which names the locator, the command and which bound was
    hit, does not survive.
    """

    def test_the_error_is_of_the_class_the_poll_contract_swallows(self) -> None:
        assert issubclass(ElementReResolutionError, StaleElementReferenceException)
        assert issubclass(ElementReResolutionError, POLL_TRANSIENTS)

    def test_an_exhausted_budget_inside_a_poll_surfaces_as_a_bare_timeout(
        self, harness: Harness
    ) -> None:
        outer_timeout = 2
        harness.dom.render("#btn")
        proxy = harness.capture(EC.presence_of_element_located, re_resolve_timeout=1)
        harness.dom.remove("#btn")

        with pytest.raises(TimeoutException) as raised:
            harness.page.poll(outer_timeout).until(lambda _: proxy.is_enabled())

        assert not isinstance(raised.value, ElementReResolutionError)
        assert "budget" not in str(raised.value)
        assert str(BUTTON) not in str(raised.value), (
            "the exhaustion diagnostic — locator, command, which bound was hit — is gone "
            "by the time the caller sees the failure"
        )
        # In the suite the outer poll is DEFAULT_TIMEOUT (15 s), so the real cost
        # of the swallow is a 15 s wait reported as a generic timeout.
        assert outer_timeout < DEFAULT_TIMEOUT
