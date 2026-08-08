"""Unit tests for the LOWER-bucket readers fixed in #946 wave 11.

## Scope

Wave 11 of the #946 absence-check campaign (`.audits/absence-check-campaign/plan.md`)
covers the remaining non-onboarding auth/flow/content page objects:
`DashboardPage`, `AccountSettingsPage`, `ImportPage`,
`NutrientCalculationsPage`, `ExpertiseLevelPage`, `LoginPage`,
`PasswordResetConfirmPage`, `InvitationAcceptPage`, `EmailVerificationPage`.

Most of these turned out already-anchored or fully-safe on inspection (static
forms with no async list refetch, or already routed through an existing
settle-condition wave 4-10 built) -- see the review's chat summary for the
per-page verdicts. Three genuine vacuous-absence/reliability defects were
found and fixed, and this module pins those:

1. **`DashboardPage.get_quick_actions`/`.get_quick_action_count`** -- both were
   a bare `find_elements` read right after `open()`. `QuickActionsWidget` is
   dynamically imported (`widgetRegistry.ts`: `lazy(() => import(...))`) and
   `WidgetFrame.tsx` renders it behind a bare, un-testid'd `<Skeleton>`
   Suspense fallback while that chunk is in flight --
   `wait_for_loading_complete()` cannot observe that fallback (it only polls
   `[data-testid='loading-skeleton']`). Fixed with a new
   `wait_for_quick_actions_widget()` anchor on the widget's own root
   (`[data-testid='widget-quick_actions']`), the same `has_care_card` shape
   wave 7/8 fixed for the DataTable cluster. `get_quick_action_count` also had
   an independent, pre-existing bug fixed in passing: it read through
   `find_all_by_testid("quick-action-")`, an *exact* testid match that no real
   card testid (`quick-action-/stammdaten/species`, ...) ever equals, so it
   always answered `0` regardless of the anchor -- dead code (no call site),
   fixed for correctness rather than for the timing defect.

2. **`AccountSettingsPage.get_display_name`/`.get_email`** -- `ProtectedRoute`
   unblocks the route once `refreshAccessToken` resolves and flips
   `auth.initialized`, **before** the separate `fetchProfile()` dispatch
   `AuthProvider.initAuth` chains after it has itself settled
   (`authSlice.ts`: `refreshAccessToken.fulfilled` sets `initialized` on its
   own). `AccountSettingsPage.tsx` seeds `displayName` from `user` via a
   `useEffect` and reads `user?.email` directly, and `user` is still `null` in
   that window -- so a read right after `open(tab="profile")` can catch both
   fields blank. Every `navigate()` in this suite is a full page reload, so
   this window reopens on *every* `open()` call. Fixed with a new
   `wait_for_profile_loaded()` anchor polling the email field's own value
   (a required field on every authenticated account) for non-empty.

   `AccountSettingsPage.get_linked_providers`/`.is_current_password_visible`
   share a sibling defect: `providers` starts at `[]` and is populated only
   once `loadProviders()`'s `listProviders()` call resolves, with no loading
   indicator of its own. Fixed by routing both through `await_presence` (the
   established `PROVIDER_NAMES` anchor).

3. **`EmailVerificationPage.wait_for_result`** -- new. Four call sites in
   `test_req023_email_verification.py` asserted `is_error_alert_visible()` --
   a bare, unanchored `find_elements` read -- as their **primary** assertion
   right after `open()`, three of them behind a comment claiming to "wait for
   processing to complete" that was never backed by an actual wait.
   `EmailVerificationPage.tsx` seeds `status` at `'loading'` and only flips it
   to `'success'`/`'error'` once its own `verifyEmail(token)` network call
   resolves; `HEADING` mounts unconditionally in the same commit as the
   loading spinner, so `open()`'s wait for it says nothing about the
   round-trip. Mirrors the already-fixed `InvitationAcceptPage.wait_for_result`.

## Why properties 1-2 are only partly measured here

`AccountSettingsPage.wait_for_profile_loaded` polls
`EMAIL_INPUT` (`"[data-testid='profile-email'] input"`), and
`get_linked_providers`/`is_current_password_visible` are anchored on
`PROVIDER_NAMES` (`"[data-testid='account-settings-page'] .MuiListItemText-primary"`)
and (for the latter) also read `CURRENT_PASSWORD_INPUT`
(`"[data-testid='current-password-field'] input"`). All three are compound
descendant selectors -- not a shape `test_row_helpers._matches` resolves (see
that module's docstring and wave 10's own for the identical gap on
`PlantInstanceDetailExt.wait_for_phase_history_content` and
`CompanionPlantingPage.wait_for_companion_data`). Not even the anchor's own
presence poll can observe a late-arriving match against these locators, so
only the bounded "never hangs past budget" property is measured for them;
their "outlives a late render" direction is analytic, built from the same
`poll(...).until(...)`/`await_presence` primitives this module and
`test_row_helpers.py` measure repeatedly elsewhere.

`DashboardPage.get_quick_actions`/`.get_quick_action_count` and
`EmailVerificationPage.wait_for_result` are fully measured: `WIDGET_QUICK_ACTIONS`
and `QUICK_ACTIONS` are an exact and a prefix testid selector respectively, and
`ERROR_ALERT`/`SUCCESS_ALERT` are bare MUI classes -- all shapes `_matches`
resolves directly.

## Why the driver is stubbed and nothing else is

Same technique and same reason as `test_row_helpers.py` and the wave 7-10
files: a **real** `selenium.webdriver.remote.webdriver.WebDriver` runs over a
fake command executor, so `WebDriverWait`, `resolve_settled_branch`/
`wait_for_any_present` and the real page objects all run unmodified. Only the
wire is fake. Provoking a "read one frame too early" race in a real browser
would mean hitting a React commit at a precise instant -- the flakiest
possible way to assert a deterministic contract.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` -- see `tests/e2e_selftest/README.md`.

## Why this is a *separate* file from `test_row_helpers.py` and prior waves' files

Per the wave-11 task brief, matching waves 7-10: `test_row_helpers.py` is
shared across parallel absence-check waves and edits to it collide, and each
prior wave's own file is a sibling PR's file for the same reason. This module
imports the `Harness`/`TableDom`/`StubConnection`/`Command` stub from
`test_row_helpers` and adds no classes to it, and does not touch any other
wave's file either.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver

from tests.e2e.pages.account_settings_page import AccountSettingsPage
from tests.e2e.pages.base_page import DEFAULT_TIMEOUT
from tests.e2e.pages.dashboard_page import DashboardPage
from tests.e2e.pages.email_verification_page import EmailVerificationPage

# The stub itself, not the fixture function -- see wave 7-10's own files for
# why this is a thin local fixture over the same stub rather than a reused
# fixture function (Ruff F811).
from .test_row_helpers import Harness, StubConnection, TableDom


@pytest.fixture
def harness() -> Harness:
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


#: Slack applied to timeout bounds, mirroring `test_row_helpers.BUDGET_SLACK` /
#: wave 7-10's own constant.
BUDGET_SLACK = 1.5

#: How many probes an anchor's polling wait must survive before the content is
#: built, mirroring wave 7-10's own `_render_after`.
PROBES = 3

#: Short enough that the loud-failure/no-hang cases below do not spend
#: `DEFAULT_TIMEOUT`, matching wave 9/10's `SETTLE_TIMEOUT`.
SETTLE_TIMEOUT = 2


def _render_after_find_element(harness: Harness, probes: int, build: Callable[[], None]) -> None:
    """Run *build* once `Command.FIND_ELEMENT` (singular) has been issued `probes` times.

    `wait_for_quick_actions_widget` goes through `BasePage.wait_for_element`,
    which polls via `EC.presence_of_element_located` -- the *singular*
    `driver.find_element`, unlike the plural `find_elements` path
    `wait_for_any_present`/`await_presence` use. Hooked here rather than on
    `FIND_ELEMENTS`, mirroring `test_row_helpers.py`'s own
    `test_is_form_submit_visible_outlives_the_tab_switch`.
    """
    seen: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        seen.append(1)
        if len(seen) == probes:
            build()

    harness.connection.before[Command.FIND_ELEMENT] = hook


def _render_after_find_elements(harness: Harness, probes: int, build: Callable[[], None]) -> None:
    """Run *build* once `Command.FIND_ELEMENTS` (plural) has been issued `probes` times.

    `EmailVerificationPage.wait_for_result` polls through a plain
    `driver.find_elements(...)` lambda, mirroring wave 7-10's own
    `_render_after`.
    """
    seen: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        seen.append(1)
        if len(seen) == probes:
            build()

    harness.connection.before[Command.FIND_ELEMENTS] = hook


def _render_alert(harness: Harness, css_class: str) -> None:
    """Render a single node carrying *css_class*, mirroring a MUI `Alert`.

    `TableDom` has no dedicated "render an alert" helper (only
    `render_dialog`, which never sets a class) -- built directly through the
    same `_new` factory `render()` itself uses for its Chip children.
    """
    node = harness.dom._new("", css_class=css_class)  # noqa: SLF001
    harness.dom.root.children.append(node)


# ── 1. DashboardPage.get_quick_actions / get_quick_action_count ─────────────


class TestDashboardQuickActions:
    """`wait_for_quick_actions_widget` anchors both readers on the widget's
    own root, not its `quick-action-*` children -- see the module docstring.
    """

    def _page(self, harness: Harness) -> DashboardPage:
        return DashboardPage(harness.driver, "http://stub.invalid")

    def _render_widget(self, harness: Harness, paths: list[str]) -> None:
        harness.dom.render_dialog("widget-quick_actions")
        for path in paths:
            harness.dom.render_dialog(f"quick-action-{path}")

    def test_get_quick_actions_outlives_a_late_render_of_the_widget(self, harness: Harness) -> None:
        """Regression pin for `test_quick_actions_present`'s `len(actions) >= 6`
        assertion, read right after `dashboard.open()`.
        """
        paths = ["/a", "/b", "/c", "/d", "/e", "/f"]
        _render_after_find_element(harness, PROBES, lambda: self._render_widget(harness, paths))

        actions = self._page(harness).get_quick_actions()

        assert len(actions) == len(paths)
        assert all(a.startswith("quick-action-") for a in actions)

    def test_get_quick_actions_raises_when_the_widget_never_settles(self, harness: Harness) -> None:
        """`wait_for_element` raises rather than returning an empty list --
        unlike `await_presence`, a widget that never mounts must not be
        reported as "zero quick actions", which the caller's `>= 6` assertion
        would otherwise (mis)report as a plain, informative failure instead of
        a "the page never even loaded" one.
        """
        page = self._page(harness)
        started = time.monotonic()

        with pytest.raises(TimeoutException):
            page.get_quick_actions()

        assert time.monotonic() - started <= DEFAULT_TIMEOUT + BUDGET_SLACK

    def test_get_quick_action_count_outlives_a_late_render_of_the_widget(
        self, harness: Harness
    ) -> None:
        """Also pins the `find_all_by_testid("quick-action-")` exact-match bug
        fixed in passing: this must count every rendered card, not zero.
        """
        paths = ["/a", "/b", "/c"]
        _render_after_find_element(harness, PROBES, lambda: self._render_widget(harness, paths))

        assert self._page(harness).get_quick_action_count() == len(paths)


# ── 2. AccountSettingsPage: profile-load and linked-providers anchors ───────


class TestAccountSettingsProfileLoaded:
    """`wait_for_profile_loaded` / `get_linked_providers` /
    `is_current_password_visible` -- see the module docstring for why only
    the bounded "never hangs past budget" property is measured here.
    """

    def _page(self, harness: Harness) -> AccountSettingsPage:
        return AccountSettingsPage(harness.driver, "http://stub.invalid")

    def test_get_display_name_raises_when_the_profile_never_loads(self, harness: Harness) -> None:
        """Regression pin for `test_profile_tab_displays_user_info`'s
        `assert display_name` right after `open(tab="profile")`: a profile
        that never loads must not silently read back as an empty string.
        """
        page = self._page(harness)
        started = time.monotonic()

        with pytest.raises(TimeoutException):
            page.get_display_name()

        assert time.monotonic() - started <= DEFAULT_TIMEOUT + BUDGET_SLACK

    def test_get_email_raises_when_the_profile_never_loads(self, harness: Harness) -> None:
        page = self._page(harness)
        started = time.monotonic()

        with pytest.raises(TimeoutException):
            page.get_email()

        assert time.monotonic() - started <= DEFAULT_TIMEOUT + BUDGET_SLACK

    def test_get_linked_providers_reports_empty_without_hanging(self, harness: Harness) -> None:
        """`await_presence` catches its own `TimeoutException` and returns
        `[]` -- a genuine negative once the budget is spent, per
        `test_linked_providers_displayed`'s own contract.
        """
        page = self._page(harness)
        started = time.monotonic()

        assert page.get_linked_providers() == []

        assert time.monotonic() - started <= DEFAULT_TIMEOUT + BUDGET_SLACK

    def test_is_current_password_visible_reports_false_without_hanging(
        self, harness: Harness
    ) -> None:
        page = self._page(harness)
        started = time.monotonic()

        assert page.is_current_password_visible() is False

        assert time.monotonic() - started <= DEFAULT_TIMEOUT + BUDGET_SLACK


# ── 3. EmailVerificationPage.wait_for_result ─────────────────────────────────


class TestEmailVerificationWaitForResult:
    """New anchor for the four call sites that asserted `is_error_alert_visible()`
    unwaited, three of them behind a comment claiming to wait that never did.
    """

    def _page(self, harness: Harness) -> EmailVerificationPage:
        return EmailVerificationPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_the_error_alert(self, harness: Harness) -> None:
        """Regression pin for `test_invalid_token_shows_error_alert` and the
        three sibling tests that read `is_error_alert_visible()` as their
        primary/precondition assertion right after `open()`.
        """
        _render_after_find_elements(
            harness, PROBES, lambda: _render_alert(harness, "MuiAlert-colorError")
        )

        assert self._page(harness).wait_for_result() == "error"

    def test_outlives_a_late_render_of_the_success_alert(self, harness: Harness) -> None:
        _render_after_find_elements(
            harness, PROBES, lambda: _render_alert(harness, "MuiAlert-colorSuccess")
        )

        assert self._page(harness).wait_for_result() == "success"

    def test_raises_when_nothing_ever_settles(self, harness: Harness) -> None:
        """A verification call that never resolves must not be reported as a
        settled outcome -- the whole point of replacing the misleading
        "wait for processing" comment with a real wait.
        """
        page = self._page(harness)
        started = time.monotonic()

        with pytest.raises(TimeoutException):
            page.wait_for_result(timeout=SETTLE_TIMEOUT)

        assert time.monotonic() - started <= SETTLE_TIMEOUT + BUDGET_SLACK
