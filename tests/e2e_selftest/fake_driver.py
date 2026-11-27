"""A minimal fake WebDriver for testing `BasePage`'s wait logic without a browser.

Only the surface `BasePage`'s settling helpers touch is implemented:
``execute_script`` (the one-round-trip CSS branch probe), ``find_element`` and
``find_elements``. That is enough because the helpers were deliberately built so
the decision -- which branch won -- is a pure function of "which selectors are
present", with the driver reduced to answering exactly that question.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoAlertPresentException,
    NoSuchElementException,
    UnexpectedAlertPresentException,
)


class FakeElement:
    """Stand-in for a `WebElement`, carrying only what the helpers read."""

    def __init__(
        self,
        selector: str,
        *,
        displayed: bool = True,
        text: str = "",
        driver: FakeDriver | None = None,
    ) -> None:
        self.selector = selector
        self._displayed = displayed
        self._text = text
        self._driver = driver

    def is_displayed(self) -> bool:
        return self._displayed

    def is_enabled(self) -> bool:
        return True

    def click(self) -> None:
        if self._driver is not None:
            if self.selector in self._driver.intercepts:
                raise ElementClickInterceptedException(
                    f"element click intercepted: {self.selector} is not clickable at point "
                    f"(196, 812). Other element would receive the click: <nav ...>"
                )
            self._driver.record_click(self.selector, native=True)

    def send_keys(self, *keys: str) -> None:
        if self._driver is not None:
            self._driver.keys_sent.append((self.selector, "".join(keys)))

    def get_attribute(self, name: str) -> str | None:
        return self._text if name == "textContent" else None

    @property
    def text(self) -> str:
        return self._text if self._displayed else ""


class FakeDriver:
    """A driver whose DOM is a list of selector sets, advanced one poll at a time.

    *states* is the sequence of DOM snapshots the driver reports on successive
    polls; the last snapshot repeats forever. That is what makes "the wait
    actually waited" testable: a helper that returns before the content exists
    reads snapshot 0 and reports the wrong branch, while a correct helper keeps
    polling until the snapshot that contains it.
    """

    def __init__(
        self,
        *states: Iterable[str],
        texts: dict[str, str] | None = None,
        hidden: Iterable[str] = (),
        current_url: str = "http://app.invalid/",
        nav_targets: dict[str, str] | None = None,
        press_lands_outside: Iterable[str] = (),
        moves_after_scroll: Iterable[str] = (),
        opens_prompt_on_click: Iterable[str] = (),
        intercepts: Iterable[str] = (),
        cover_probe: dict[str, dict[str, object]] | None = None,
    ) -> None:
        self.states: list[frozenset[str]] = [frozenset(s) for s in states] or [frozenset()]
        self.polls = 0
        self.script_calls = 0
        self.find_elements_calls = 0
        self.texts = texts or {}
        #: Selectors that are in the DOM but report ``is_displayed() == False``
        #: even after a scroll -- e.g. a nav item the expertise level hides.
        self.hidden = frozenset(hidden)
        self.current_url = current_url
        #: Selector -> URL the app routes to when that element is clicked, so a
        #: click-driven navigation is observable exactly as it is in the browser.
        self.nav_targets = nav_targets or {}
        self.clicked: list[str] = []
        #: Selectors whose *native* click presses something else -- the layout
        #: moved between the driver's hit-test and the press (#3065).
        self.press_lands_outside = frozenset(press_lands_outside)
        #: Selectors whose first frame-settled hit-test after a scroll misses,
        #: as when the scroll itself re-laid-out the content around them.
        self.moves_after_scroll = set(moves_after_scroll)
        self.scrolls = 0
        self.settled_hit_checks = 0
        self._armed: str | None = None
        self._pressed: str | None = None
        #: Selectors whose click opens a native ``window.confirm``.
        self.opens_prompt_on_click = frozenset(opens_prompt_on_click)
        #: The text of the open user prompt, ``None`` when none is open.
        self.prompt: str | None = None
        #: Scripts that reached the driver while a prompt was open. WebDriver's
        #: default unhandled-prompt behaviour dismisses the prompt on each one.
        self.scripts_while_prompt: list[str] = []
        #: Selectors whose *native* click the driver refuses with
        #: ``ElementClickInterceptedException`` -- something covers the hit point.
        self.intercepts = frozenset(intercepts)
        #: Selector -> what the ``/* coverProbe */`` script answers for it (#3157).
        #: A selector not listed answers "the centre hits the element itself".
        self.cover_probe = cover_probe or {}
        self.cover_probes = 0
        #: ``(selector, keys)`` for every ``send_keys``.
        self.keys_sent: list[tuple[str, str]] = []
        self.switch_to = _FakeSwitchTo(self)

    def record_click(self, selector: str, *, native: bool = False) -> None:
        self.clicked.append(selector)
        if native and self._armed == selector:
            self._pressed = selector
        if selector in self.opens_prompt_on_click:
            self.prompt = "confirm"
        if selector in self.nav_targets:
            self.current_url = self.nav_targets[selector]

    # ── DOM ──
    @property
    def present(self) -> frozenset[str]:
        return self.states[min(self.polls, len(self.states) - 1)]

    def _advance(self) -> None:
        self.polls += 1

    # ── WebDriver surface ──
    def _unhandled_prompt(self, script: str) -> None:
        """WebDriver's default for a command sent while a prompt is open: dismiss, then raise."""
        if self.prompt is not None:
            self.scripts_while_prompt.append(script)
            self.prompt = None
            raise UnexpectedAlertPresentException("unexpected alert open: dismissed")

    def execute_script(self, script: str, *args: object) -> object:
        self._unhandled_prompt(script)
        self.script_calls += 1
        if "querySelector" in script and args:
            selectors = args[0]
            assert isinstance(selectors, Sequence)
            snapshot = self.present
            self._advance()
            return [i for i, sel in enumerate(selectors) if sel in snapshot]
        if "scrollIntoView" in script:
            self.scrolls += 1
            return None
        if script.startswith("/* armPressProbe */") and args and isinstance(args[0], FakeElement):
            self._armed, self._pressed = args[0].selector, None
            return None
        if script.startswith("/* readPressProbe */"):
            armed, pressed = self._armed, self._pressed
            self._armed = self._pressed = None
            if armed is None:
                return None
            if pressed is None:
                return {"pressed": False, "inside": None, "at": None, "element": armed}
            outside = pressed in self.press_lands_outside
            return {
                "pressed": True,
                "inside": not outside,
                "at": "div.MuiDialogContent-root" if outside else pressed,
                "element": pressed,
            }
        if script.startswith("/* coverProbe */") and args and isinstance(args[0], FakeElement):
            self.cover_probes += 1
            selector = args[0].selector
            target = {"tag": "button", "testid": selector, "id": None, "cls": "MuiButton-root"}
            answer = self.cover_probe.get(selector, {"relation": "self", "hit": target})
            return {
                "target": target,
                "rect": {"x": 150.0, "y": 790.0, "width": 92.0, "height": 44.0},
                "point": {"x": 196.0, "y": 812.0},
                "viewport": {"width": 393, "height": 852},
                **answer,
            }
        if ".click()" in script and args and isinstance(args[0], FakeElement):
            self.record_click(args[0].selector)
            return None
        if ".matches(" in script:
            return False
        raise AssertionError(f"FakeDriver got an unexpected script: {script[:60]!r}")

    def execute_async_script(self, script: str, *args: object) -> object:
        self._unhandled_prompt(script)
        if script.startswith("/* settledHit */") and args and isinstance(args[0], FakeElement):
            self.settled_hit_checks += 1
            selector = args[0].selector
            if selector in self.moves_after_scroll:
                self.moves_after_scroll.discard(selector)
                return {"hit": False, "at": "div.MuiDialogContent-root"}
            return {"hit": True, "at": selector}
        raise AssertionError(f"FakeDriver got an unexpected async script: {script[:60]!r}")

    def find_elements(self, _by: str, value: str) -> list[FakeElement]:
        self.find_elements_calls += 1
        snapshot = self.present
        if value not in snapshot:
            self._advance()
            return []
        return [
            FakeElement(
                value,
                displayed=value not in self.hidden,
                text=self.texts.get(value, ""),
                driver=self,
            )
        ]

    def find_element(self, by: str, value: str) -> FakeElement:
        found = self.find_elements(by, value)
        if not found:
            raise NoSuchElementException(value)
        return found[0]


class _FakeAlert:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeSwitchTo:
    """``driver.switch_to``: only ``alert``, which -- as in WebDriver -- never dismisses."""

    def __init__(self, driver: FakeDriver) -> None:
        self._driver = driver

    @property
    def active_element(self) -> FakeElement:
        return FakeElement("<active-element>", driver=self._driver)

    @property
    def alert(self) -> _FakeAlert:
        if self._driver.prompt is None:
            raise NoAlertPresentException("no such alert")
        return _FakeAlert(self._driver.prompt)
