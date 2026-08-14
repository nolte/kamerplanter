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

## What the component can and cannot do

The first draft of this module justified the fix with a second "not yet" state:
a mounted trigger whose label had not filled in. **That state does not exist.**
`TenantSwitcher.tsx` returns `null` while `myTenants` is empty, and
`tenantSlice` sets `myTenants` and `activeTenant` in one reducer, so the button
never renders without a name. A test for it would have certified an impossible
DOM shape -- green, and covering nothing.

What the component *does* produce is a label that reads
`t('pages.tenants.selectTenant')` ("Garten wählen") whenever `activeTenant` is
null while tenants exist -- the stale-slug recovery `clearActiveTenant` performs
in `store.ts`. A reader keyed on "non-empty text" accepts that placeholder as a
tenant name, which is why the component now marks the label with
`data-tenant-selected` and the reader is scoped to the selected case.

So the two states the anchor has to survive are: the switcher is **absent**
(the nightly's shape), and it is present but **unselected**.

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
    """The switcher as the reader can observe it, one `find_elements` at a time.

    *mounts_after* delays the trigger, which is the nightly's shape. *selected*
    models the component's own scoping: the reader's locator carries
    ``[data-tenant-selected='true']``, so an unselected switcher matches
    *nothing* -- the placeholder is not a shorter name, it is not a name.
    *dies_after_poll* kills the node once the poll has already seen it, which is
    the window a second read would fall into.
    """

    def __init__(
        self,
        *,
        mounts_after: int = 0,
        selected: bool = True,
        stale: bool = False,
        dies_after_poll: bool = False,
    ) -> None:
        self.mounts_after = mounts_after
        self.selected = selected
        self.stale = stale
        self.dies_after_poll = dies_after_poll
        self.reads = 0

    @property
    def label(self) -> str:
        return TENANT

    def find_elements(self, _by: str, _value: str) -> list[FakeLabel]:
        self.reads += 1
        if not self.selected or self.reads <= self.mounts_after:
            return []
        if self.dies_after_poll and self.reads > 1:
            # The poll saw it on read 1; everything after that is the re-render.
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

    def test_does_not_read_the_pick_a_tenant_placeholder_as_a_name(self) -> None:
        """An unselected switcher has no name to report, however much text it shows.

        `assert name` at `test_req024_tenant_switcher.py:81` would otherwise pass
        on "Garten wählen", and TC-024-010 would compare that string against the
        real tenant across the reload.
        """
        driver = FakeSwitcherDriver(selected=False)

        assert page(driver).get_active_tenant_name() == ""

    def test_returns_the_text_the_anchor_itself_observed(self) -> None:
        """No second read: the DOM may move between the poll and the return.

        `handleSwitch` triggers `window.location.reload()`, so the node that
        satisfied the poll can be gone one command later. Re-reading there would
        answer `""` -- the exact failure the anchor exists to remove, just one
        line further down.
        """
        driver = FakeSwitcherDriver(dies_after_poll=True)

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
