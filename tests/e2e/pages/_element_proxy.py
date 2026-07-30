"""An element reference that re-acquires itself when the DOM moves underneath.

## Why this exists

Every element lookup in this suite is a *capture-then-use*: a ``WebDriverWait``
resolves a ``WebElement``, and the next line clicks or types into it. There are
~459 such sites across the page objects. Between the resolution and the use,
React is free to re-render — and a re-render replaces the DOM node, which kills
the reference. The driver-level implicit wait has been masking this by delaying
every lookup enough that a re-rendering table had usually settled before the
reference was taken (see ``conftest.py``); it is not a property of the code that
the capture survives.

:meth:`BasePage.retry_on_stale` is the existing answer and stays: it re-runs a
whole *action* that re-acquires what it touches. It cannot help the 459 sites,
because those hold a reference the caller has already resolved — which is
exactly the note in its own docstring ("passing a closure over an
already-resolved element would retry the same dead reference"). This module is
the complementary half: the *reference itself* knows how it was obtained and can
obtain itself again. The two compose — a proxy that exhausts its budget raises a
``StaleElementReferenceException`` subclass, so an enclosing ``retry_on_stale``
still sees the exception class it retries on.

## Why it is a ``WebElement`` subclass and not a ``__getattr__`` proxy

A thin wrapper holding ``(locator, condition)`` and forwarding attribute access
is **not implementable** against Selenium. Verified against the installed
4.46.0:

* ``remote/webdriver.py:410-416`` (``_wrap_value``) recognises an element by
  ``isinstance(value, self._web_element_cls)`` and then serialises ``value.id``.
  Anything else falls through to JSON serialisation — a wrapper handed into
  ``execute_script`` would be sent as an object literal, not as an element.
* ``support/expected_conditions.py:459`` and ``:517`` do
  ``if not isinstance(target, WebElement): target = driver.find_element(*target)``
  — a non-``WebElement`` passed to ``element_to_be_clickable`` / ``visibility_of``
  is **unpacked as a locator tuple**, i.e. silently misinterpreted.

So the type identity has to be real. ``isinstance(proxy, WebElement)`` is True
here because the proxy *is* one.

## Where the re-resolution hangs

``remote/webelement.py:507`` (``_execute``) reads the **private** ``self._id``,
not the public ``id`` property (``:475-486``); so do ``__eq__`` (``:489``) and
``__hash__`` (``:559``). Hooking only the public ``id`` property would therefore
miss every element command. Two hooks, one source of truth:

1. ``_id`` stays a plain attribute (making it a property would collide with
   ``WebElement.__init__``'s ``self._id = id_`` at ``:73``) and is **rewritten in
   place** on a successful re-resolution. Everything that reads it —
   ``_execute``, ``id``, ``__eq__``, ``__hash__``, ``__repr__`` — therefore sees
   the fresh element with no second source of truth to drift.
2. :meth:`_execute` catches ``StaleElementReferenceException``, re-resolves, and
   retries the command. This covers every element command; ``submit()``
   (``webelement.py:136``) is the only method that bypasses ``_execute``, and it
   goes through ``execute_script(script, self)`` — i.e. through hook 3.
3. The public :attr:`id` property probes liveness *before* answering. That is
   the marshalling path: ``_wrap_value`` reads ``.id`` to serialise an element
   argument of ``execute_script``, and most of the page objects' 20
   ``execute_script`` call sites hand it a captured element
   (``base_page.py:867``, ``:925``, ``:1259``,
   ``sensor_create_dialog_page.py:110``, …). Without the probe the driver would
   marshal a dead id and the exception would surface out of ``driver``, where no
   proxy can heal it.

## Budget

Bounded twice over, independently, per element command:

* a wall-clock deadline of :data:`RE_RESOLVE_TIMEOUT` seconds, taken once at the
  start of the command and never extended, and
* at most :data:`MAX_RE_RESOLUTIONS` re-resolutions.

There is no unbounded retry loop: a proxy that retried forever would convert a
real failure into a hang, which is strictly worse than the bug it fixes. When
either bound is reached the call raises :class:`ElementReResolutionError` — it
never returns a dead or a substituted-but-unverified element.

## Known limits — deliberately not solved here

* **Plural lookups are not covered.** ``driver.find_elements(...)`` and
  ``proxy.find_element(...)`` both return raw elements (the driver builds them
  via ``create_web_element``), so rows and children do not inherit this
  behaviour. The three row helpers in ``base_page.py`` are covered by
  ``retry_on_stale`` instead.
* **Re-resolution re-runs the locator.** If the locator matches several nodes,
  the replacement may be a different node than the original — the same exposure
  the first capture already had, not a new one.
* **A legitimate "the element is gone" becomes a bounded wait.** That is the
  cost of the mechanism and the reason the budget is 3 s rather than
  ``DEFAULT_TIMEOUT``: a genuine failure must stay fast and loud. Callers that
  deliberately treat staleness as a *verdict* rather than as a transient would
  see the healed element answer instead once they are handed a proxy. Those are
  classified and dealt with where the waits are wired — see the
  "Staleness as a *verdict*" block in ``base_page.py``, which opts the affected
  reads out through ``base_page.raw_reference`` rather than leaving the
  substitution implicit.
* **The marshalling probe narrows the race, it does not close it.** The element
  can still die between the probe and the command the id was marshalled into;
  that residual window is one round trip wide, against the arbitrarily wide one
  it replaces.

## Selenium version dependency

``_execute`` and ``_id`` are not public API. ``requirements.txt`` therefore pins
``selenium>=4.25.0,<5``. A minor upgrade that renamed either would fail loudly
here (``AttributeError`` / ``TypeError`` at import or first use) rather than
silently, but the upper bound is what keeps a major release from being pulled in
unreviewed.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from typing import Any, Protocol

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

__all__ = [
    "MAX_RE_RESOLUTIONS",
    "RE_RESOLVE_TIMEOUT",
    "Condition",
    "ConditionFactory",
    "ElementReResolutionError",
    "Locator",
    "PollFactory",
    "ReResolvingElement",
    "resolve_element",
]

#: A Selenium locator: ``(By.<STRATEGY>, value)``.
#:
#: ``base_page`` declares an identical alias. It is restated rather than
#: imported because ``base_page`` imports *this* module, and the alias is not
#: worth a circular import.
Locator = tuple[str, str]

#: An ``expected_conditions`` predicate: takes the driver, returns the element
#: or a falsy value. Typed loosely because Selenium's own conditions differ in
#: their return unions (``WebElement`` vs ``Literal[False] | WebElement``).
Condition = Callable[[Any], Any]

#: What *builds* a condition from a locator — ``EC.presence_of_element_located``
#: and friends. A factory rather than a ready-made condition on purpose: a
#: condition built from an *element* (``EC.element_to_be_clickable(element)``,
#: which ``expected_conditions.py:495`` accepts) would re-check the very
#: reference that just died. Re-resolution must start from the locator.
ConditionFactory = Callable[[Locator], Condition]

#: Wall-clock budget, in seconds, for *all* re-resolutions inside one element
#: command. Deliberately the same 3 s as ``BasePage.retry_on_stale`` (the
#: mechanism this one complements) and deliberately not ``DEFAULT_TIMEOUT``:
#: re-resolution answers "did the node come back from a re-render", which takes
#: a frame or two, and a 15 s budget would only make a genuine "it is gone"
#: five times slower to surface.
RE_RESOLVE_TIMEOUT = 3

#: Hard cap on re-resolutions inside one element command, independent of the
#: clock. The deadline alone already bounds the wall time, but a DOM that
#: re-renders faster than the round trip could spin the retry loop many
#: thousands of times inside those 3 s. Failing after a small, nameable number
#: of attempts turns "the page never holds still" into a readable message
#: instead of a busy wait.
MAX_RE_RESOLUTIONS = 3


class PollFactory(Protocol):
    """``BasePage.poll`` — a ``WebDriverWait`` carrying the suite's poll contract.

    Injected rather than constructed here so the ``ignored_exceptions`` contract
    stays stated in exactly one place (``base_page.POLL_TRANSIENTS``), and so
    this module can stay free of an import back into ``base_page``.
    """

    def __call__(self, timeout: int, /) -> WebDriverWait: ...


class ElementReResolutionError(StaleElementReferenceException):
    """A :class:`ReResolvingElement` could not re-acquire itself in budget.

    A ``StaleElementReferenceException`` **subclass** on purpose, on two counts:
    the reference really is dead, and the mechanisms already built around that
    class keep working — ``BasePage.retry_on_stale`` still retries the enclosing
    action, and ``POLL_TRANSIENTS`` still treats it as "not yet" inside a poll
    that has its own budget. The distinct type and message are what make it
    diagnosable as *exhaustion* rather than as a first staleness.
    """


class ReResolvingElement(WebElement):
    """A ``WebElement`` that re-runs its own ``(locator, condition)`` when stale.

    Construct it through :func:`resolve_element` — that keeps the condition used
    for the first capture and the condition used for every re-resolution
    structurally identical, so a *clickable* capture can only ever come back as
    a clickable element, never as a merely present one.
    """

    def __init__(
        self,
        parent: WebDriver,
        id_: str,
        *,
        locator: Locator,
        condition: ConditionFactory,
        poll: PollFactory,
        timeout: int = RE_RESOLVE_TIMEOUT,
        max_re_resolutions: int = MAX_RE_RESOLUTIONS,
    ) -> None:
        super().__init__(parent, id_)
        self._locator = locator
        self._condition = condition
        self._poll = poll
        self._re_resolve_timeout = timeout
        self._max_re_resolutions = max_re_resolutions

    # ── Construction ──────────────────────────────────────────────────────

    @classmethod
    def wrapping(
        cls,
        element: WebElement,
        *,
        locator: Locator,
        condition: ConditionFactory,
        poll: PollFactory,
        timeout: int = RE_RESOLVE_TIMEOUT,
    ) -> ReResolvingElement:
        """Return *element* as a re-resolving reference to the same node.

        An element that already is one is returned unchanged — *with its own*
        ``(locator, condition)``, not the ones passed here. Wrapping again would
        leave the outer proxy re-resolving through the inner one's budget as
        well, multiplying the bound this module exists to keep small. This
        matters only for a caller that re-wraps deliberately: the wait helpers
        feed this from ``WebDriverWait.until``, which yields the raw element
        ``driver.find_element`` built, never a proxy.
        """
        if isinstance(element, cls):
            return element
        return cls(
            element.parent,
            # `_id` rather than `.id`: the public property is the liveness-probing
            # one (see the class docstring), and wrapping must not cost a round
            # trip for an element the caller just resolved.
            element._id,
            locator=locator,
            condition=condition,
            poll=poll,
            timeout=timeout,
        )

    # ── Identity ──────────────────────────────────────────────────────────

    @property
    def id(self) -> str:
        """The **live** element id, re-resolving first if the reference died.

        The one place a caller can get the id without executing a command, and
        therefore the one place where a dead id would escape into the driver:
        ``WebDriver._wrap_value`` reads exactly this property when it marshals
        an element argument of ``execute_script`` (``remote/webdriver.py:411``).
        Answering with the id we happen to be holding would hand a dead
        reference to JavaScript; the probe costs one round trip and makes the
        answer true at the moment it is given.
        """
        self._probe_liveness()
        return str(self._id)

    def __eq__(self, other: object) -> bool:
        """Compare on the *currently held* reference, without probing.

        Selenium's own implementation (``webelement.py:489``) reads
        ``other.id``, which for two proxies would fire a liveness probe — and a
        re-resolution — from inside an ``==``. Comparing the raw ids keeps
        equality free of side effects and keeps it consistent with
        :meth:`__hash__`, which cannot probe at all.

        Consistency across a re-resolution follows from ``_id`` being the single
        source of truth: after healing, this proxy compares equal to a freshly
        found element for the same node, and unequal to the node it replaced —
        which is the truth about what it now points at.

        Returns ``False`` rather than ``NotImplemented`` for a non-element, so
        that :meth:`__ne__` can stay a plain negation. Nothing is lost: a
        non-element on the *left* of the comparison has already returned
        ``NotImplemented`` from its own ``__eq__`` by the time this runs.
        """
        if not isinstance(other, WebElement):
            return False
        return bool(self._id == other._id)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Hash the currently held id, exactly as ``WebElement`` does.

        Defined explicitly because a class that overrides ``__eq__`` otherwise
        gets ``__hash__ = None``. It hashes the same value ``__eq__`` compares,
        so ``proxy == raw`` still implies ``hash(proxy) == hash(raw)`` after a
        re-resolution. The flip side is that a proxy is only a sound dict key
        for as long as it has not healed — the same caveat any mutable key has,
        and no worse than the raw element, which would simply be dead.
        """
        return super().__hash__()

    def __repr__(self) -> str:
        """Name the locator as well as the id — and never probe.

        A ``repr`` is what a failing assertion and a pytest traceback print, so
        it has to be free of round trips: firing a command (and possibly a
        re-resolution) while rendering an error message would change the state
        being reported on. It reads the held ``_id`` directly for that reason.
        """
        return (
            f"<{type(self).__name__} locator={self._locator!r} "
            f"element={self._id!r} session={self.parent.session_id!r}>"
        )

    # ── Re-resolution ─────────────────────────────────────────────────────

    def _execute(self, command: str, params: dict[str, Any] | None = None) -> Any:
        """Run an element command, re-acquiring the element if it went stale.

        Every element command funnels through here (``webelement.py:507``), so
        this single override covers ``click``, ``send_keys``, ``text``,
        ``is_displayed``, ``get_attribute`` and the rest. ``super()._execute``
        re-reads ``self._id`` on each pass, so the retry runs against the healed
        element rather than against the dead one.
        """
        deadline = time.monotonic() + self._re_resolve_timeout
        re_resolutions = 0
        while True:
            try:
                return super()._execute(command, params)
            except StaleElementReferenceException as stale:
                re_resolutions += 1
                self._re_resolve(stale, deadline, re_resolutions, command)

    def _re_resolve(
        self,
        stale: StaleElementReferenceException,
        deadline: float,
        attempt: int,
        command: str,
    ) -> None:
        """Point this reference at a fresh element, or fail loudly.

        Both bounds are checked *before* the wait, so neither can be exceeded by
        starting one more poll: the attempt cap is exact, and the wall-clock
        overshoot is bounded by the rounding below plus the wait's own 0.5 s
        poll interval (``support/wait.py:110-121``).
        """
        if attempt > self._max_re_resolutions:
            raise ElementReResolutionError(
                self._failure_message(
                    command,
                    f"went stale {attempt} times in a row -- more than the "
                    f"{self._max_re_resolutions} re-resolutions allowed per command. "
                    "The DOM under this locator is re-rendering faster than a command "
                    "round trip; waiting for it to settle is the caller's job, not "
                    "this reference's.",
                )
            ) from stale

        # Rounded *up* to the whole seconds ``WebDriverWait`` is given here, so
        # the budget is spent rather than truncated away; flooring would hand a
        # 2.99 s remainder a 2 s wait. The overshoot this admits is bounded and
        # small: at most the sub-second remainder, plus the wait's own 0.5 s
        # poll granularity.
        remaining = math.ceil(deadline - time.monotonic())
        if remaining <= 0:
            raise ElementReResolutionError(
                self._failure_message(
                    command,
                    f"went stale and the {self._re_resolve_timeout}s re-resolution "
                    "budget was already spent.",
                )
            ) from stale

        try:
            replacement = self._poll(remaining).until(self._condition(self._locator))
        except TimeoutException as exc:
            raise ElementReResolutionError(
                self._failure_message(
                    command,
                    f"went stale and no element satisfying the same condition came "
                    f"back within {self._re_resolve_timeout}s (attempt {attempt}). "
                    "The element is gone, not merely re-rendered.",
                )
            ) from exc

        if not isinstance(replacement, WebElement):
            raise ElementReResolutionError(
                self._failure_message(
                    command,
                    f"re-resolved to {replacement!r}, which is not a WebElement. The "
                    "condition factory must return an element-returning condition, "
                    "or the retry would substitute an unrelated object for the "
                    "element the caller is holding.",
                )
            ) from stale

        # The single source of truth, rewritten in place: `_execute`, `id`,
        # `__eq__`, `__hash__` and `__repr__` all read this attribute.
        self._id = replacement._id

    def _probe_liveness(self) -> None:
        """Force a re-resolution if the held reference is dead.

        ``isElementEnabled`` is a W3C command defined for *every* element (it is
        specified to answer ``true`` for anything that is not a disabled form
        control), so it is a valid liveness probe regardless of what the element
        is. It is routed through :meth:`_execute` on purpose: the healing path
        is then the same one every other command uses, rather than a second
        implementation of it.
        """
        self._execute(Command.IS_ELEMENT_ENABLED)

    def _failure_message(self, command: str, what: str) -> str:
        return (
            f"{type(self).__name__} for locator {self._locator!r} {what} "
            f"(failing command: {command!r})"
        )


def resolve_element(
    poll: PollFactory,
    locator: Locator,
    condition: ConditionFactory,
    timeout: int,
    *,
    re_resolve_timeout: int = RE_RESOLVE_TIMEOUT,
) -> ReResolvingElement:
    """Wait for *locator* under *condition* and return a re-resolving reference.

    The capture and the re-resolution are built from the same
    ``(locator, condition)`` pair *by construction* rather than by convention,
    which is the point of doing this in one function: a caller cannot wait for
    "clickable" and get back a reference that heals to "merely present".
    """
    element = poll(timeout).until(condition(locator))
    return ReResolvingElement.wrapping(
        element,
        locator=locator,
        condition=condition,
        poll=poll,
        timeout=re_resolve_timeout,
    )
