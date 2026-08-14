"""`TenantSwitcherPage.get_active_tenant_name()` must answer about a rendered switcher.

## The failure this comes from

`test_tenant_persists_after_reload` (TC-024-010) failed in the 2026-08-14
nightly on the `full` profile:

    TC-REQ-024-026 FAIL: Expected tenant '' to persist, got: 'Mein Garten'

Read the direction: the value that failed to "persist" was the **empty string**.
The test captured the active tenant, reloaded, and captured it again -- and only
the second capture had a wait in front of it
(`wait_for_element(TRIGGER_BUTTON_ALT, timeout=20)`). The first one read an
unanchored

    elements = self.driver.find_elements(*self.TRIGGER_BUTTON_ALT)
    if elements and elements[0].is_displayed():
        return elements[0].text
    return ""

right after `_ensure_logged_in(...)`, i.e. while the App Bar was still resolving
its tenant query. So the assertion compared "not loaded yet" against the real
name and reported it as a persistence defect in the application.

`""` is never a legitimate answer here: all four call sites want a name -- one
asserts `assert name`, the others compare it against a tenant they switched to
or expect to survive a reload. That is what makes waiting for a non-empty label
the right anchor rather than a way of hiding an empty one.

## The two shapes that produce `""`

Both are "not yet" and both are modelled below, because the fix has to cover
them together: the trigger can be **absent** (the App Bar has not mounted the
switcher) or **present with no text** (`TenantSwitcher` renders the button
before its query resolves). An anchor keyed only on presence would still return
`""` for the second one -- which is the shape a plain
`wait_for_element(TRIGGER_BUTTON_ALT)` covers and the failing test's *second*
capture happened to get away with.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` -- see `tests/e2e_selftest/README.md`.
"""

from __future__ import annotations

import time
from typing import Any

import pytest
from selenium.common.exceptions import StaleElementReferenceException

from tests.e2e.pages.tenant_switcher_page import TenantSwitcherPage

#: Short enough that the "never arrives" cases do not spend `DEFAULT_TIMEOUT`,
#: long enough for several `WebDriverWait` poll cycles.
SETTLE_TIMEOUT = 2

TENANT = "Mein Garten"


class FakeLabel:
    """The Typography inside the switcher's trigger button."""

    def __init__(self, driver: FakeSwitcherDriver) -> None:
        self._driver = driver

    def is_displayed(self) -> bool:
        if self._driver.stale:
            raise StaleElementReferenceException("the App Bar re-rendered")
        return True

    @property
    def text(self) -> str:
        return self._driver.label


class FakeSwitcherDriver:
    """A switcher that mounts, and then fills in its label, after N reads.

    *mounts_after* and *labels_after* are counted in ``find_elements`` calls, so
    "the button is not there yet" and "the button is there but empty" are
    separate, orderable states -- which is what the reader has to survive.
    """

    def __init__(
        self,
        *,
        mounts_after: int = 0,
        labels_after: int = 0,
        stale: bool = False,
    ) -> None:
        self.mounts_after = mounts_after
        self.labels_after = labels_after
        self.stale = stale
        self.reads = 0

    @property
    def label(self) -> str:
        return TENANT if self.reads > self.labels_after else ""

    def find_elements(self, _by: str, _value: str) -> list[FakeLabel]:
        self.reads += 1
        if self.reads <= self.mounts_after:
            return []
        return [FakeLabel(self)]

    # `BasePage.poll` builds a WebDriverWait over this object; nothing else of
    # the driver surface is touched by the reader under test.
    def execute_script(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("the reader must not need a script round-trip")


def page(driver: FakeSwitcherDriver) -> TenantSwitcherPage:
    return TenantSwitcherPage(driver, "http://stub.invalid")


class TestGetActiveTenantName:
    """Outlive both "not yet" shapes, still report a genuine absence."""

    def test_outlives_a_switcher_that_mounts_late(self) -> None:
        """The App Bar has not rendered the trigger yet -- the nightly's shape."""
        driver = FakeSwitcherDriver(mounts_after=3)

        assert page(driver).get_active_tenant_name() == TENANT

    def test_outlives_a_trigger_whose_label_is_still_empty(self) -> None:
        """The button is mounted, the tenant query has not resolved.

        The half a presence-only wait does not cover: `wait_for_element`
        succeeds on this frame and the read still comes back `""`.
        """
        driver = FakeSwitcherDriver(labels_after=3)

        assert page(driver).get_active_tenant_name() == TENANT

    def test_returns_at_once_when_the_label_is_already_there(self) -> None:
        """The normal case must not pay for the anchor."""
        driver = FakeSwitcherDriver()

        started = time.monotonic()
        assert page(driver).get_active_tenant_name() == TENANT
        assert time.monotonic() - started < 1.0

    def test_still_answers_empty_when_the_label_never_arrives(self) -> None:
        """Bounded, and an answer rather than an exception.

        Every call site asserts on the *name*, so a switcher that never renders
        has to reach those assertions as `""` -- with their own message -- and
        not as a timeout raised out of a reader.
        """
        driver = FakeSwitcherDriver(mounts_after=10**9)

        started = time.monotonic()
        assert page(driver).get_active_tenant_name() == ""
        assert time.monotonic() - started <= SETTLE_TIMEOUT + 1.5

    def test_a_reference_that_dies_mid_read_is_not_an_exception(self) -> None:
        """The App Bar re-rendering under the read answers, it does not raise.

        `MainLayout` re-renders the header on every tenant change, so this
        reader can be handed a node that dies between the lookup and the text
        read -- the staleness *verdict* shape `BasePage.is_any_displayed`
        records for dialogs.
        """
        driver = FakeSwitcherDriver(stale=True)

        assert page(driver).get_active_tenant_name() == ""


@pytest.fixture(autouse=True)
def _short_anchor_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the anchor on `SETTLE_TIMEOUT` instead of `DEFAULT_TIMEOUT`.

    The contract under test is "it waits, bounded, and then answers"; the exact
    budget is not, and paying 15 s per not-arriving case in a tier that gates
    every PR is the cost this module refuses.
    """
    monkeypatch.setattr(TenantSwitcherPage, "ACTIVE_LABEL_TIMEOUT", SETTLE_TIMEOUT)
