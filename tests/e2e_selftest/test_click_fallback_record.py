"""A covered control fails the guarded click; everything else is recorded (#3157).

`BasePage.scroll_and_click` falls back to a JavaScript activation when the driver
refuses the native click, and a JS click reaches the element whatever covers it.
Step 1 recorded every such fallback; the measuring nightly found each of them on
a covered control. Step 2 refuses those. These pin, against the real helper and
the fake driver:

* a refused click on a **covered** target raises, naming the covering element,
  the target locator, both boxes and the viewport -- and sends **no** click;
* a refused click whose centre hits the target or a **descendant** still takes
  the JS fallback, recorded as ``js_fallback``;
* the **opt-out** ``covered_ok="<reason>"`` clicks and records the reason;
* a probe that **fails** keeps the fallback and records ``probe_failed``;
* a click the driver **accepts** records nothing;
* the notification drawer is closed by its button, never by ``Escape``;
* snackbars over a control are closed with their own button before the click;
* the reporter turns the drained events into one JSON Lines file per profile and
  a summary line that counts the raised clicks, on the controller only.
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
    DIRECT_TAG,
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


BOTTOM_NAV_RECT = {"x": 0.0, "y": 796.0, "width": 393.0, "height": 56.0}


class TestAnInterceptedClick:
    @pytest.mark.parametrize("relation", ["other", "ancestor"])
    def test_a_covered_target_raises_naming_the_cover_and_sends_no_click(
        self, relation: str
    ) -> None:
        driver = FakeDriver(
            {SAVE},
            intercepts={SAVE},
            cover_probe={
                SAVE: {"relation": relation, "hit": BOTTOM_NAV, "hit_rect": BOTTOM_NAV_RECT}
            },
        )

        with pytest.raises(AssertionError) as raised:
            page_for(driver).wait_and_click(SAVE_LOCATOR)

        message = str(raised.value)
        assert "button[data-testid='bottom-nav-plants']" in message, "the cover is named"
        assert "MuiBottomNavigationAction-root" in message, "with its class"
        assert f"css selector: {SAVE}" in message, "the target locator is named"
        assert "Control box x=150 y=790 w=92 h=44" in message
        assert "covering box x=0 y=796 w=393 h=56" in message
        assert "viewport 393x852" in message
        assert "covered_ok=" in message, "the message names the opt-out"
        assert driver.clicked == [], "a covered control must not be clicked through"
        [event] = _click_fallback.drain()
        assert event["outcome"] == "raised" and "covered_ok" not in event
        assert event["covered"] is True and event["relation"] == relation
        assert event["hit"]["testid"] == "bottom-nav-plants", "the record must name the cover"
        assert event["hit_rect"] == BOTTOM_NAV_RECT
        assert event["probe"] == "ok"
        assert event["kind"] == "fallback"
        assert event["helper"] == "BasePage.scroll_and_click"
        assert event["activation"] == "js_click"
        assert event["trigger"] == "ElementClickInterceptedException"
        assert "Other element would receive the click" in event["trigger_message"]
        assert event["locator"] == f"css selector: {SAVE}"
        assert event["viewport"] == {"width": 393, "height": 852}
        assert event["rect"]["height"] == 44.0
        assert event["caller"] and "test_click_fallback_record.py" in event["caller"]

    def test_the_opt_out_clicks_a_covered_target_and_records_the_reason(self) -> None:
        driver = FakeDriver(
            {SAVE}, intercepts={SAVE}, cover_probe={SAVE: {"relation": "other", "hit": BOTTOM_NAV}}
        )
        reason = "the bar is translucent here and a user taps through it"

        page_for(driver).wait_and_click(SAVE_LOCATOR, covered_ok=reason)

        [event] = _click_fallback.drain()
        assert event["outcome"] == "covered_ok"
        assert event["covered_ok"] == reason
        assert event["covered"] is True
        assert driver.clicked == [SAVE], "the opt-out activates it, once"

    @pytest.mark.parametrize("reason", ["", "   "])
    def test_an_opt_out_without_a_reason_is_refused(self, reason: str) -> None:
        driver = FakeDriver({SAVE})

        with pytest.raises(ValueError, match="needs a reason"):
            page_for(driver).wait_and_click(SAVE_LOCATOR, covered_ok=reason)
        assert driver.clicked == []

    def test_the_opt_out_is_not_recorded_where_nothing_covers(self) -> None:
        driver = FakeDriver({SAVE}, intercepts={SAVE})

        page_for(driver).wait_and_click(SAVE_LOCATOR, covered_ok="expected cover")

        [event] = _click_fallback.drain()
        assert event["outcome"] == "js_fallback" and "covered_ok" not in event
        assert driver.clicked == [SAVE]

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
        assert event["outcome"] == "js_fallback"
        assert event["locator"] is None, "a raw element without a locator records none"
        assert driver.clicked == [SAVE], "an uncovered control still gets the JS click"

    @pytest.mark.parametrize("relation", ["outside_viewport", "detached"])
    def test_no_verdict_keeps_the_fallback(self, relation: str) -> None:
        driver = FakeDriver(
            {SAVE}, intercepts={SAVE}, cover_probe={SAVE: {"relation": relation, "hit": None}}
        )

        page_for(driver).wait_and_click(SAVE_LOCATOR)

        [event] = _click_fallback.drain()
        assert event["covered"] is None and event["outcome"] == "js_fallback"
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
        assert event["outcome"] == "js_fallback"
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

    def test_a_covered_mui_select_trigger_raises_without_the_mousedown_pair(self) -> None:
        driver = FakeDriver(
            {SAVE}, intercepts={SAVE}, cover_probe={SAVE: {"relation": "other", "hit": BOTTOM_NAV}}
        )
        page = page_for(driver)
        page.opens_on_mousedown = lambda element: True  # type: ignore[method-assign]
        dispatched: list[object] = []
        page.dispatch_menu_trigger_open = dispatched.append  # type: ignore[method-assign]

        with pytest.raises(AssertionError, match="bottom-nav-plants"):
            page.wait_and_click(SAVE_LOCATOR)

        [event] = _click_fallback.drain()
        assert event["activation"] == "js_mousedown" and event["outcome"] == "raised"
        assert dispatched == [], "no mousedown may reach a covered trigger"


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


class TestADirectCoordinateFreeClick:
    """`click_coordinate_free` never tries a native click; every call is measured."""

    def test_a_covered_submit_records_a_direct_event_naming_the_cover(self) -> None:
        driver = FakeDriver({SAVE}, cover_probe={SAVE: {"relation": "other", "hit": BOTTOM_NAV}})

        page_for(driver).wait_and_click_coordinate_free(SAVE_LOCATOR)

        [event] = _click_fallback.drain()
        assert event["kind"] == "direct"
        assert event["trigger"] == "direct" and event["trigger_message"] == ""
        assert event["helper"] == "BasePage.click_coordinate_free"
        assert event["activation"] == "js_click"
        assert event["covered"] is True
        assert event["hit"]["testid"] == "bottom-nav-plants"
        assert event["locator"] == f"css selector: {SAVE}"
        assert driver.clicked == [SAVE], "still exactly one JS click"

    def test_a_centre_on_the_control_records_not_covered(self) -> None:
        driver = FakeDriver({SAVE})

        page_for(driver).click_coordinate_free(driver.find_element(*SAVE_LOCATOR))

        [event] = _click_fallback.drain()
        assert event["kind"] == "direct" and event["relation"] == "self"
        assert event["covered"] is False
        assert driver.clicked == [SAVE]

    def test_a_centre_below_the_fold_records_outside_viewport_without_a_verdict(self) -> None:
        driver = FakeDriver(
            {SAVE}, cover_probe={SAVE: {"relation": "outside_viewport", "hit": None}}
        )

        page_for(driver).wait_and_click_coordinate_free(SAVE_LOCATOR)

        [event] = _click_fallback.drain()
        assert event["relation"] == "outside_viewport"
        assert event["covered"] is None, "off the fold is not covered -- and not uncovered"
        assert driver.clicked == [SAVE]

    def test_a_failing_probe_still_clicks(self) -> None:
        driver = FakeDriver({SAVE})

        def broken(script: str, *args: object) -> object:
            if script.startswith("/* coverProbe */"):
                raise RuntimeError("javascript error: probe broke")
            return FakeDriver.execute_script(driver, script, *args)

        driver.execute_script = broken  # type: ignore[method-assign]

        page_for(driver).wait_and_click_coordinate_free(SAVE_LOCATOR)

        [event] = _click_fallback.drain()
        assert event["kind"] == "direct" and event["probe"] == "probe_failed"
        assert driver.clicked == [SAVE]

    def test_the_probe_sees_the_layout_after_the_scroll(self) -> None:
        """Measured where the click happens: after `scroll_into_view`, before the dispatch."""
        driver = FakeDriver({SAVE})
        scrolls_at_probe: list[int] = []

        def spy(script: str, *args: object) -> object:
            if script.startswith("/* coverProbe */"):
                scrolls_at_probe.append(driver.scrolls)
                assert driver.clicked == [], "the probe must run before the click"
            return FakeDriver.execute_script(driver, script, *args)

        driver.execute_script = spy  # type: ignore[method-assign]

        page_for(driver).wait_and_click_coordinate_free(SAVE_LOCATOR)

        assert scrolls_at_probe == [1]
        assert driver.clicked == [SAVE]

    def test_an_open_prompt_gets_no_probe_and_the_click_still_goes_out(self) -> None:
        driver = FakeDriver({SAVE})
        element = driver.find_element(*SAVE_LOCATOR)
        page = page_for(driver)
        page.scroll_into_view = lambda el: None  # type: ignore[method-assign]
        page.opens_on_mousedown = lambda el: False  # type: ignore[method-assign]
        page._dispatch_click = lambda el: driver.record_click(el.selector)  # type: ignore[method-assign]
        driver.prompt = "confirm"

        page.click_coordinate_free(element)

        [event] = _click_fallback.drain()
        assert event["probe"] == "probe_failed"
        assert driver.scripts_while_prompt == [] and driver.prompt == "confirm"
        assert driver.clicked == [SAVE]


class TestAnAcceptedClick:
    def test_a_native_click_records_nothing(self) -> None:
        driver = FakeDriver({SAVE})

        page_for(driver).wait_and_click(SAVE_LOCATOR)

        assert _click_fallback.drain() == []
        assert driver.cover_probes == 0, "no probe script may reach the page on the happy path"
        assert driver.clicked == [SAVE]


class TestTheNotificationDrawerClose:
    """`close_drawer` clicks the button like a user; no `Escape` stands in for it any more."""

    CLOSE = "[data-testid='notification-drawer-close']"

    def _page(self, driver: FakeDriver, *, closes: bool) -> NotificationCenterPage:
        page = NotificationCenterPage(driver, "http://app.invalid")  # type: ignore[arg-type]
        page.wait_for_element_clickable = (  # type: ignore[method-assign]
            lambda locator, timeout=0: driver.find_element(*locator)
        )

        def hidden(locator: object, timeout: int = 0) -> None:
            if not closes:
                raise TimeoutException("drawer still visible")

        page.wait_for_element_hidden = hidden  # type: ignore[method-assign]
        return page

    def test_the_close_button_is_clicked_natively(self) -> None:
        driver = FakeDriver({self.CLOSE})

        self._page(driver, closes=True).close_drawer()

        assert driver.clicked == [self.CLOSE]
        assert driver.keys_sent == [], "no Escape"
        assert _click_fallback.drain() == []

    def test_a_covered_close_button_fails_naming_the_cover_and_sends_no_escape(self) -> None:
        avatar = {"tag": "div", "testid": None, "id": None, "cls": "MuiAvatar-root"}
        driver = FakeDriver(
            {self.CLOSE},
            intercepts={self.CLOSE},
            cover_probe={self.CLOSE: {"relation": "other", "hit": avatar}},
        )

        with pytest.raises(AssertionError, match="MuiAvatar-root"):
            self._page(driver, closes=True).close_drawer()

        assert driver.clicked == [] and driver.keys_sent == []
        [event] = _click_fallback.drain()
        assert event["outcome"] == "raised"

    def test_a_drawer_that_stays_open_fails_instead_of_pressing_escape(self) -> None:
        driver = FakeDriver({self.CLOSE})

        with pytest.raises(AssertionError, match="stayed open"):
            self._page(driver, closes=False).close_drawer()

        assert driver.clicked == [self.CLOSE]
        assert driver.keys_sent == []


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
            "uncovered=1 no_verdict=0 probe_failed=1 raised=0 covered_ok=0 "
            "file=x/click-fallbacks-mobile.jsonl"
        )
        covering = lines[lines.index("top covering elements (of 3 covered fallbacks):") + 1]
        assert covering.split() == ["2x", "button[data-testid='bottom-nav-plants']", "(other)"]

    def test_the_fallback_line_counts_raised_clicks_and_lists_the_opt_outs(self) -> None:
        events = [
            {**_event("t1", covered=True), "outcome": "raised"},
            {**_event("t2", covered=True), "outcome": "raised"},
            {
                **_event("t3", covered=True),
                "outcome": "covered_ok",
                "covered_ok": "a reason",
                "caller": "pages/x.py:1 X.y",
            },
            {**_event("t4", covered=False), "outcome": "js_fallback"},
        ]

        lines = summarize(events, "full", None)

        assert lines[0] == (
            f"{SUMMARY_TAG} profile=full fallbacks=4 tests=4 covered=3 covered_tests=3 "
            "uncovered=1 no_verdict=0 probe_failed=0 raised=2 covered_ok=1 file=-"
        )
        opt_outs = lines[lines.index("covered_ok opt-outs (1):") + 1]
        assert opt_outs.split(None, 1) == ["1x", "pages/x.py:1 X.y: a reason"]

    def test_a_run_without_fallbacks_still_prints_both_lines(self) -> None:
        assert summarize([], "light", None) == [
            f"{SUMMARY_TAG} profile=light fallbacks=0 tests=0 covered=0 covered_tests=0 "
            "uncovered=0 no_verdict=0 probe_failed=0 raised=0 covered_ok=0 file=-",
            f"{DIRECT_TAG} profile=light clicks=0 tests=0 covered=0 covered_tests=0 "
            "uncovered=0 outside_viewport=0 no_verdict=0 probe_failed=0",
        ]

    def test_direct_clicks_are_counted_apart_from_the_fallbacks(self) -> None:
        def direct(nodeid: str, relation: str, covered: bool | None, testid: str) -> dict:
            return {
                **_event(nodeid, covered=covered, testid=testid),
                "kind": "direct",
                "helper": "BasePage.click_coordinate_free",
                "trigger": "direct",
                "relation": relation,
                "target": {"tag": "button", "testid": "form-submit-button"},
            }

        events = [
            _event("f1", covered=True),
            direct("d1", "other", True, "bottom-nav"),
            direct("d1", "other", True, "bottom-nav"),
            direct("d2", "self", False, "x"),
            direct("d3", "outside_viewport", None, "x"),
            direct("d4", "detached", None, "x"),
        ]

        lines = summarize(events, "mobile", None)

        assert lines[0].startswith(f"{SUMMARY_TAG} profile=mobile fallbacks=1 tests=1 covered=1 ")
        assert lines[1] == (
            f"{DIRECT_TAG} profile=mobile clicks=5 tests=4 covered=2 covered_tests=1 "
            "uncovered=1 outside_viewport=1 no_verdict=1 probe_failed=0"
        )
        covering = lines[lines.index("top covering elements (of 2 covered direct clicks):") + 1]
        assert covering.split() == ["2x", "button[data-testid='bottom-nav']", "(other)"]
        offscreen = lines[lines.index("top targets outside the viewport (of 1 direct clicks):") + 1]
        assert offscreen.split() == ["1x", "button[data-testid='form-submit-button']"]

    def test_the_module_is_the_one_the_conftest_registers(self) -> None:
        source = (Path(report_mod.__file__).parent / "conftest.py").read_text()
        assert "config.pluginmanager.register(ClickFallbackReporter(config)" in source
