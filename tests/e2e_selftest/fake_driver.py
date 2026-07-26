"""A minimal fake WebDriver for testing `BasePage`'s wait logic without a browser.

Only the surface `BasePage`'s settling helpers touch is implemented:
``execute_script`` (the one-round-trip CSS branch probe), ``find_element`` and
``find_elements``. That is enough because the helpers were deliberately built so
the decision -- which branch won -- is a pure function of "which selectors are
present", with the driver reduced to answering exactly that question.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from selenium.common.exceptions import NoSuchElementException


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
            self._driver.record_click(self.selector)

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

    def record_click(self, selector: str) -> None:
        self.clicked.append(selector)
        if selector in self.nav_targets:
            self.current_url = self.nav_targets[selector]

    # ── DOM ──
    @property
    def present(self) -> frozenset[str]:
        return self.states[min(self.polls, len(self.states) - 1)]

    def _advance(self) -> None:
        self.polls += 1

    # ── WebDriver surface ──
    def execute_script(self, script: str, *args: object) -> object:
        self.script_calls += 1
        if "querySelector" in script and args:
            selectors = args[0]
            assert isinstance(selectors, Sequence)
            snapshot = self.present
            self._advance()
            return [i for i, sel in enumerate(selectors) if sel in snapshot]
        if "scrollIntoView" in script:
            return None
        if ".click()" in script and args and isinstance(args[0], FakeElement):
            self.record_click(args[0].selector)
            return None
        if ".matches(" in script:
            return False
        raise AssertionError(f"FakeDriver got an unexpected script: {script[:60]!r}")

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
