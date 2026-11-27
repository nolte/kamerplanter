"""The covering-blind click fallbacks are recorded, not yet refused (#3157, step 1).

`BasePage.scroll_and_click` falls back to a JavaScript activation when the driver
refuses the native click, and a JS click reaches the element whatever covers it.
Before that fallback is made to fail, the next nightly has to measure how many
tests rely on it. These pin the measurement against the real helper and the fake
driver:

* a refused click on a **covered** target records ``covered: true`` and names the
  covering element;
* a refused click whose centre hits the target or a **descendant** records
  ``covered: false``;
* a probe that **fails** records ``probe_failed`` -- and the click still happens;
* a click the driver **accepts** records nothing;
* the reporter turns the drained events into one JSON Lines file per profile and
  a summary line, on the controller only.

And in every case the fallback still activates the element exactly once: this
step changes what is *known*, not which clicks happen.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver

from tests.e2e import _click_fallback_report as report_mod
from tests.e2e._click_fallback_report import (
    REPORT_ATTRIBUTE,
    SUMMARY_TAG,
    ClickFallbackReporter,
    profile_name,
    summarize,
)
from tests.e2e.pages import _click_fallback
from tests.e2e.pages.base_page import BasePage
from tests.e2e.pages.notification_center_page import NotificationCenterPage

from .fake_driver import FakeDriver
from .test_row_helpers import Harness, StubConnection, TableDom

SAVE = "[data-testid='form-submit-button']"
SAVE_LOCATOR = (By.CSS_SELECTOR, SAVE)
BOTTOM_NAV = {
    "tag": "button",
    "testid": "bottom-nav-plants",
    "id": None,
    "cls": "MuiBottomNavigationAction-root",
}


@pytest.fixture(autouse=True)
def _no_leftover_events() -> Iterator[None]:
    _click_fallback.drain()
    yield
    _click_fallback.drain()


def page_for(driver: FakeDriver) -> BasePage:
    page = BasePage(driver, "http://app.invalid")  # type: ignore[arg-type]
    # The re-resolving element proxy needs a real driver; what is under test is
    # what happens after the locate step.
    page.wait_for_element_clickable = (  # type: ignore[method-assign]
        lambda locator, timeout=0: driver.find_element(*locator)
    )
    return page


class TestAnInterceptedClick:
    def test_a_covered_target_records_covered_and_names_the_cover(self) -> None:
        driver = FakeDriver(
            {SAVE},
            intercepts={SAVE},
            cover_probe={SAVE: {"relation": "other", "hit": BOTTOM_NAV}},
        )

        page_for(driver).wait_and_click(SAVE_LOCATOR)

        [event] = _click_fallback.drain()
        assert event["covered"] is True
        assert event["relation"] == "other"
        assert event["hit"]["testid"] == "bottom-nav-plants", "the record must name the cover"
        assert event["probe"] == "ok"
        assert event["helper"] == "BasePage.scroll_and_click"
        assert event["activation"] == "js_click"
        assert event["trigger"] == "ElementClickInterceptedException"
        assert "Other element would receive the click" in event["trigger_message"]
        assert event["locator"] == f"css selector: {SAVE}"
        assert event["viewport"] == {"width": 393, "height": 852}
        assert event["rect"]["height"] == 44.0
        assert event["caller"] and "test_click_fallback_record.py" in event["caller"]
        assert driver.clicked == [SAVE], "the JS fallback must still activate it, once"

    @pytest.mark.parametrize("relation", ["self", "descendant"])
    def test_a_centre_that_hits_the_target_records_not_covered(self, relation: str) -> None:
        label = {"tag": "span", "testid": None, "id": None, "cls": "MuiButton-label"}
        hit = label if relation == "descendant" else {"tag": "button", "testid": SAVE}
        driver = FakeDriver(
            {SAVE}, intercepts={SAVE}, cover_probe={SAVE: {"relation": relation, "hit": hit}}
        )
        page = page_for(driver)

        page.scroll_and_click(driver.find_element(*SAVE_LOCATOR))

        [event] = _click_fallback.drain()
        assert event["covered"] is False
        assert event["relation"] == relation
        assert event["locator"] is None, "a raw element without a locator records none"
        assert driver.clicked == [SAVE]

    def test_a_failing_probe_records_probe_failed_and_the_click_still_happens(self) -> None:
        driver = FakeDriver({SAVE}, intercepts={SAVE})

        def broken(script: str, *args: object) -> object:
            if script.startswith("/* coverProbe */"):
                raise RuntimeError("javascript error: elementFromPoint is not a function")
            return FakeDriver.execute_script(driver, script, *args)

        driver.execute_script = broken  # type: ignore[method-assign]

        page_for(driver).wait_and_click(SAVE_LOCATOR)

        [event] = _click_fallback.drain()
        assert event["probe"] == "probe_failed"
        assert "elementFromPoint is not a function" in event["probe_error"]
        assert "covered" not in event, "no verdict may be invented for a failed probe"
        assert driver.clicked == [SAVE], "the fallback click must survive a failed probe"

    def test_an_open_prompt_gets_no_probe_script(self) -> None:
        driver = FakeDriver({SAVE}, intercepts={SAVE})
        page = page_for(driver)
        element = driver.find_element(*SAVE_LOCATOR)
        driver.prompt = "confirm"

        page._record_click_fallback(
            element, helper="BasePage.scroll_and_click", activation="js_click", trigger="t"
        )

        [event] = _click_fallback.drain()
        assert event["probe"] == "probe_failed"
        assert driver.scripts_while_prompt == [] and driver.prompt == "confirm"

    def test_a_mui_select_trigger_records_the_mousedown_activation(self) -> None:
        driver = FakeDriver({SAVE}, intercepts={SAVE})
        page = page_for(driver)
        page.opens_on_mousedown = lambda element: True  # type: ignore[method-assign]
        dispatched: list[object] = []
        page.dispatch_menu_trigger_open = dispatched.append  # type: ignore[method-assign]

        page.wait_and_click(SAVE_LOCATOR)

        [event] = _click_fallback.drain()
        assert event["activation"] == "js_mousedown"
        assert len(dispatched) == 1


@pytest.fixture
def stub_harness() -> Harness:
    """A real `WebDriver` over the row-helper stub DOM -- the tier's model of staleness."""
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


class TestAStaleProxy:
    """The probe must not heal a re-resolving element in front of the fallback."""

    DIALOG = (By.CSS_SELECTOR, "[data-testid='some-dialog']")

    def test_a_stale_proxy_is_probed_raw_and_recorded_as_probe_failed(
        self, stub_harness: Harness
    ) -> None:
        """Healing in the probe would put the proxy's re-resolution wait before the click.

        With the node gone and a fresh one under the same locator, a healing
        probe would re-run the locator (a FIND_ELEMENT) and answer for the
        replacement. Read raw, the probe sees the staleness and says so; the
        fallback that follows heals exactly as it did before this record existed.
        """
        harness = stub_harness
        harness.dom.render_dialog("some-dialog")
        proxy = harness.proxy_for(self.DIALOG)
        harness.dom.root.children[0].attached = False
        harness.dom.render_dialog("some-dialog")
        finds_before = harness.connection.count(Command.FIND_ELEMENT)

        harness.page._record_click_fallback(
            proxy, helper="BasePage.scroll_and_click", activation="js_click", trigger="t"
        )

        [event] = _click_fallback.drain()
        assert event["probe"] == "probe_failed"
        assert "StaleElementReferenceException" in event["probe_error"]
        assert harness.connection.count(Command.FIND_ELEMENT) == finds_before, "no re-resolution"
        assert event["locator"] == f"css selector: {self.DIALOG[1]}", "the proxy names its locator"


class TestAnAcceptedClick:
    def test_a_native_click_records_nothing(self) -> None:
        driver = FakeDriver({SAVE})

        page_for(driver).wait_and_click(SAVE_LOCATOR)

        assert _click_fallback.drain() == []
        assert driver.cover_probes == 0, "no probe script may reach the page on the happy path"
        assert driver.clicked == [SAVE]


class TestTheNotificationDrawerEscape:
    CLOSE = "[data-testid='notification-drawer-close']"

    def _page(self, driver: FakeDriver, *, closes: bool) -> NotificationCenterPage:
        page = NotificationCenterPage(driver, "http://app.invalid")  # type: ignore[arg-type]
        page.wait_for_element_clickable = (  # type: ignore[method-assign]
            lambda locator, timeout=0: driver.find_element(*locator)
        )
        calls: list[int] = []

        def hidden(locator: object, timeout: int = 0) -> None:
            calls.append(1)
            if not closes and len(calls) == 1:
                raise TimeoutException("drawer still visible")

        page.wait_for_element_hidden = hidden  # type: ignore[method-assign]
        return page

    def test_an_intercepted_close_records_the_escape_fallback(self) -> None:
        driver = FakeDriver(
            {self.CLOSE},
            intercepts={self.CLOSE},
            cover_probe={self.CLOSE: {"relation": "other", "hit": {"tag": "div", "testid": "a"}}},
        )

        self._page(driver, closes=True).close_drawer()

        [event] = _click_fallback.drain()
        assert event["helper"] == "NotificationCenterPage.close_drawer"
        assert event["activation"] == "escape_key"
        assert event["covered"] is True
        assert driver.keys_sent == [("<active-element>", "")], "Escape still goes out once"

    def test_a_native_close_that_leaves_the_drawer_open_records_the_second_escape(self) -> None:
        driver = FakeDriver({self.CLOSE})

        self._page(driver, closes=False).close_drawer()

        [event] = _click_fallback.drain()
        assert event["trigger"] == "drawer_still_open"
        assert event["covered"] is False
        assert driver.clicked == [self.CLOSE]
        assert len(driver.keys_sent) == 1


def _event(nodeid: str, *, covered: bool | None, testid: str = "bottom-nav-plants") -> dict:
    return {
        "nodeid": nodeid,
        "helper": "BasePage.scroll_and_click",
        "activation": "js_click",
        "trigger": "ElementClickInterceptedException",
        "probe": "ok",
        "relation": "other" if covered else "self",
        "covered": covered,
        "hit": {"tag": "button", "testid": testid, "id": None, "cls": ""},
    }


class TestTheReporter:
    def _config(self, tmp_path: Path | None, *, worker: bool = False) -> Any:
        options = {"--app-mode": "light", "--device": "mobile"}
        config = SimpleNamespace(
            getoption=lambda name, default=None: options.get(name, default),
            _protocol_output_dir=tmp_path,
        )
        if worker:
            config.workerinput = {}
        return config

    def test_the_profile_is_named_as_run_e2e_names_it(self) -> None:
        assert profile_name("light", "desktop") == "light"
        assert profile_name("light", "mobile") == "mobile"
        assert profile_name("full", "desktop") == "full"
        assert profile_name("full", "tablet") == "full-tablet"
        assert profile_name("light", "desktop", "smoke") == "smoke"

    def test_the_phase_events_reach_the_report(self) -> None:
        reporter = ClickFallbackReporter(self._config(None, worker=True))
        report = SimpleNamespace()
        hook = reporter.pytest_runtest_makereport(item=None)  # type: ignore[arg-type]
        next(hook)
        _click_fallback.record_fallback(helper="h", activation="js_click", trigger="t")
        with pytest.raises(StopIteration):
            hook.send(SimpleNamespace(get_result=lambda: report))

        assert [e["helper"] for e in getattr(report, REPORT_ATTRIBUTE)] == ["h"]
        assert _click_fallback.drain() == [], "drained, so the next phase starts empty"

    def test_the_controller_writes_one_jsonl_per_profile_and_the_worker_does_not(
        self, tmp_path: Path
    ) -> None:
        report = SimpleNamespace(nodeid="test_a.py::test_x", when="call")
        setattr(report, REPORT_ATTRIBUTE, [_event("provisional", covered=True)])

        ClickFallbackReporter(self._config(tmp_path, worker=True)).pytest_runtest_logreport(
            report  # type: ignore[arg-type]
        )
        assert not list(tmp_path.iterdir()), "a worker must leave the writing to the controller"

        controller = ClickFallbackReporter(self._config(tmp_path))
        controller.pytest_runtest_logreport(report)  # type: ignore[arg-type]
        controller.pytest_runtest_logreport(report)  # type: ignore[arg-type]

        lines = (tmp_path / "click-fallbacks-mobile.jsonl").read_text().splitlines()
        assert len(lines) == 2
        first = json.loads(lines[0])
        assert first["nodeid"] == "test_a.py::test_x", "the report's nodeid is authoritative"
        assert first["phase"] == "call" and first["profile"] == "mobile"

    def test_the_summary_counts_and_ranks_the_covering_elements(self) -> None:
        events = [
            _event("t1", covered=True),
            _event("t1", covered=True),
            _event("t2", covered=True, testid="snackbar"),
            _event("t3", covered=False),
            {**_event("t4", covered=None), "probe": "probe_failed"},
        ]

        lines = summarize(events, "mobile", Path("x/click-fallbacks-mobile.jsonl"))

        assert lines[0] == (
            f"{SUMMARY_TAG} profile=mobile fallbacks=5 tests=4 covered=3 covered_tests=2 "
            "uncovered=1 no_verdict=0 probe_failed=1 file=x/click-fallbacks-mobile.jsonl"
        )
        covering = lines[lines.index("top covering elements (of 3 covered fallbacks):") + 1]
        assert covering.split() == ["2x", "button[data-testid='bottom-nav-plants']", "(other)"]

    def test_a_run_without_fallbacks_still_prints_the_line(self) -> None:
        assert summarize([], "light", None) == [
            f"{SUMMARY_TAG} profile=light fallbacks=0 tests=0 covered=0 covered_tests=0 "
            "uncovered=0 no_verdict=0 probe_failed=0 file=-"
        ]

    def test_the_module_is_the_one_the_conftest_registers(self) -> None:
        source = (Path(report_mod.__file__).parent / "conftest.py").read_text()
        assert "config.pluginmanager.register(ClickFallbackReporter(config)" in source
