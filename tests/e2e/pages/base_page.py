"""Base page object with common helpers for all pages."""

from __future__ import annotations

import re
import time
import warnings
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ._element_proxy import ReResolvingElement, resolve_element

DEFAULT_TIMEOUT = 15

#: The grace period the driver-level implicit wait used to grant *every*
#: ``find_element`` call before #835 removed it. The singular finders that were
#: relying on it now ask for it explicitly (``find_present``), so the removal
#: changes no test's timing — while every *absence* check stopped paying it,
#: which is where the cost actually sat: 29 ``is_present`` call sites blocked
#: the full budget on every negative answer (31 counting the two that reach
#: `PrintButtonPage`'s same-named, argument-less helper, which is the same
#: ``find_elements`` shape).
#:
#: Those figures are AST call counts, not grep hits, and the difference is not
#: pedantry: a grep for the bare name reports 39 here. It picks up the two
#: definitions, five ``def test_..._is_present`` *test names*, and three
#: ``EC.alert_is_present()`` calls — a different Selenium API entirely. The 41
#: this docstring carried before #835 P6 came from exactly that over-count, and
#: so did the 49 that :meth:`find_present` carried.
#:
#: Deliberately not ``DEFAULT_TIMEOUT``. These are lookups of something the
#: caller believes is already rendered, not waits for a transition; raising the
#: budget to 15 s would make every genuine failure five times slower to surface
#: and buy nothing.
IMPLICIT_WAIT_EQUIVALENT = 3

#: States a *poll* must treat as "not yet", never as a verdict.
#:
#: Selenium's default is ``(NoSuchElementException,)`` alone, which makes a
#: stale reference mid-poll fatal — even though it means precisely "the DOM moved
#: under me, look again", which is what polling is for. The removed implicit wait
#: had been hiding that narrow default: it delayed every lookup just enough that
#: a re-rendering React table was usually settled by the time the reference was
#: taken. Removing it surfaced 7 `StaleElementReferenceException` failures in the
#: smoke suite (#835) — a latent defect the implicit wait had masked, not one the
#: removal created.
POLL_TRANSIENTS = (NoSuchElementException, StaleElementReferenceException)

#: A Selenium locator: ``(By.<STRATEGY>, value)``.
Locator = tuple[str, str]


class TableNotSettled(StaleElementReferenceException):
    """A `DataTable` row is in the DOM but has not rendered its identifying cell.

    The second signal a re-rendering table emits, and the one the retry did not
    cover before #835 P4. React replaces a row wholesale when its key changes --
    that is the reference dying, i.e. ``StaleElementReferenceException``. But it
    also *reconciles a surviving row's children in place*, and mid-reconciliation
    that row exposes neither its ``cell-<col_id>`` nor its ``card-title``. The
    reference is then perfectly alive and :meth:`BasePage.get_row_primary_text`
    raises ``AssertionError`` -- which :meth:`BasePage.retry_on_stale` does not
    catch, so it escaped the three row helpers as a hard failure.

    That the shape is real was never in doubt: `click_data_table_row` has been
    defending against it since #835, in a closure that catches
    ``StaleElementReferenceException, AssertionError`` with the note "a row
    mid-render exposes neither its cell nor its card title". The defence just
    lived in one branch of one helper. This class is that knowledge promoted to
    a name so the other readers can share it.

    A ``StaleElementReferenceException`` **subclass**, for the same reason
    ``ElementReResolutionError`` is one: the mechanisms already built around that
    class are exactly the ones this needs. ``retry_on_stale`` re-runs the whole
    acquisition, and ``POLL_TRANSIENTS`` treats it as "not yet" inside a poll
    that carries its own budget. The reference is *not* dead, which is the one
    respect in which the name overstates -- what both states share, and all a
    caller can act on, is "re-acquire and look again".

    **What it costs when the row is not mid-render at all.** A row that renders
    no such cell because the caller named a column this table does not have is
    indistinguishable from a mid-render row *at one instant*; the two are only
    told apart over time, which is what a bounded retry does. So a genuinely
    wrong ``col_id`` now surfaces after the retry budget instead of immediately.
    It stays just as loud, and it carries the original assertion's message
    verbatim plus both hypotheses -- see
    :meth:`BasePage.require_row_primary_text`.
    """


# ── Why the *plural* path is not wrapped ──────────────────────────────────
# The three element-returning waits hand back a `ReResolvingElement` (#835 P3).
# `driver.find_elements(...)` -- 804 call sites -- deliberately does **not**, and
# this is the reasoned decision, not an omission left for later (#835 P4).
#
# A singular reference can re-acquire itself because it knows *what it was
# asked for*: a locator plus the condition that accepted it. A list element has
# no such key. The only key available to a generic wrapper would be
# `(locator, index)` -- and re-resolving a row by its index after a re-render is
# precisely the recovery this module already refuses, three screens down in
# `click_data_table_row`: #871 measured it turning a loud
# `StaleElementReferenceException` into four journey tests that opened the
# globally-first plant and then asserted against the one they meant to create.
# Wrapping the plural path would reinstate that recovery *below* the guard that
# rejects it, at 804 sites, where the guard cannot see it. A wrong element that
# reads as success is worse than the exception it replaces.
#
# It would also buy nothing at most of those sites. The dominant shape there is
# a count or an emptiness probe -- `is_present`, `has_alert_notification`,
# `close_mui_dropdown`, `is_select_open`, `is_card_layout` -- which reads
# `len(...)` or `next(iter(...), None)` and never touches the elements at all.
# Healing is undefined for an empty list and irrelevant for a length.
#
# The complementary mechanism for the plural path is therefore the one that was
# already here: `retry_on_stale`, which re-runs an *action that re-acquires what
# it touches*. Where it may sit follows from that clause and from nothing else:
# a closure over an element the caller already resolved would retry the same
# dead reference (its own docstring says so). That rules out every row *reader*
# whose row comes from its caller -- `get_row_cell_text`,
# `get_row_text_fragments`, `get_row_chip_texts`, `resolve_row_click_target`,
# `click_row_via_column` -- and it rules *in* every helper that does its own
# `find_elements` **and then reads through the elements it found**.
#
# #835 P4 applied that rule instead of restating it, and it selects six helpers,
# not the three that had it. The three it already occupied (`get_column_texts`,
# `find_row_by_text`, `click_data_table_row`) plus three that qualified just as
# squarely and were simply never revisited: `get_all_row_text_fragments`,
# `get_column_chip_texts` and `get_column_chip_colors`. Each owns its row lookup
# and then reads `.text`, a class attribute or a child element off every row it
# found, so a re-render mid-scan let a raw `StaleElementReferenceException` out
# of a pure read -- the same shape as the three, at eight page objects' worth of
# list assertions (`get_visible_*` on harvest batches, planting runs,
# substrates, treatments, tanks, watering logs, pests, diseases).
#
# "Six" is checkable rather than asserted: `retry_on_stale` has exactly six call
# expressions under `tests/e2e/`, all in this module. Count them from the AST,
# not with a grep -- see `IMPLICIT_WAIT_EQUIVALENT` for what a grep does to a
# figure like this one.
#
# What the rule keeps *out* is as load-bearing as what it lets in. A helper that
# only counts or probes emptiness -- `get_all_table_row_count`,
# `get_watering_log_row_count`, `is_present` -- never touches an element, so
# there is nothing to go stale; and `get_watering_log_rows`, which hands its raw
# rows to the caller, is the "the retry covers the scan, not the use" case
# `find_row_by_text` documents, where wrapping the lookup would buy the caller
# nothing.
#
# The second thing P4 closed is a different gap, and a measured one: a
# re-rendering `DataTable` emits **two** signals, and the retry only ever
# covered one. See `TableNotSettled`.


# ── Staleness as a *verdict*, and how to keep it one ──────────────────────
# `POLL_TRANSIENTS` above states the majority rule: inside a poll, a stale
# reference means "look again". A handful of reads mean the opposite -- they
# catch `StaleElementReferenceException` and *answer* with it ("the element is
# gone, so: not displayed / not open / already closed"). For those, a
# re-resolving reference would change the answer rather than stabilise it: the
# healed replacement would report on the node that came back, where the caller
# asked about the node that left.
#
# Re-run after P4 against the code as it now stands. The six verdict *sites* P3
# counted are four verdict *implementations* now -- three page objects had
# written the same dialog probe out for themselves and now share
# `is_any_displayed` -- and all four still read their element from
# `driver.find_elements(...)`, which is still not wrapped, so, as in P3, **no
# verdict is reachable by a proxy today**. That
# fact has now been re-derived twice and reversed once (P1 predicted
# reachability, P3 refuted it), which is the argument for not relying on it a
# third time: every verdict site is opted out **structurally**, so its answer no
# longer depends on which paths happen to be wrapped this week.
#
#   Reads it as a VERDICT -- each opted out, each with the decision at the site:
#     * `BasePage.is_displayed_in_scroll_container`  (False)  `raw_reference`
#     * `BasePage._read_select_value`                (None -> loud) `raw_reference`
#     * `BasePage.is_any_displayed`                  (False)  `raw_reference`,
#       and the three page-object dialog probes that each used to write this
#       loop out for themselves now route through it:
#       `phase_transition_page.PlantInstanceDetailExt.is_transition_dialog_open`
#       and `.is_confirm_dialog_visible` (the class name P3 recorded here as
#       `PhaseTransitionPage` was wrong -- there is no such class in that
#       module), plus `FeedingEventListPage.is_create_dialog_open`
#     * `TaskDetailPage._submit_registered`          (**True**) `raw_reference`
#       -- the one whose verdict is a *success* signal ("the submit went
#       through"), so a healed reference would not merely change an answer, it
#       would manufacture a pass. Guarded first for that reason.
#
# All four opt-outs are exercised against a deliberately proxied element by
# `tests/e2e_selftest/test_row_helpers.py::TestVerdictsStayVerdicts`, so none of
# them rests on being unreachable.
#
#   Reads it as a TRANSIENT (retry, or consult a second signal) -- healing is an
#   improvement there, so these stay wired:
#     * `BasePage.retry_on_stale`, `.get_text_stable`, `.close_mui_dropdown`,
#       `.row_primary_text_or_none` (used by `click_data_table_row`)
#     * `BasePage._aria_expanded` -- see its docstring for why it deliberately
#       does not opt out
#     * `WorkflowDetailPage.get_workflow_title`, `SiteListPageExt.open`,
#       `_journey_helpers.create_care_task` (P3 recorded this one as
#       `_journey_helpers.provision_task`; no such function exists -- the
#       staleness handler is in `create_care_task`, and the module sits at
#       `tests/e2e/_journey_helpers.py`, not under `pages/`)
#
# The list above is the whole population, re-derived by walking the AST of
# `tests/e2e/` for `except` handlers naming `StaleElementReferenceException` --
# a text grep misses the ones written as a multi-line tuple, which is how
# `close_mui_dropdown` and `create_care_task` spell theirs.


def raw_reference(element: WebElement) -> WebElement:
    """Return a plain reference to the node *element* points at **right now**.

    The opt-out from re-resolution, for the few reads that treat staleness as an
    answer rather than as a transient (see the block above). A
    :class:`~._element_proxy.ReResolvingElement` handed to one of those would
    heal and let the replacement answer, silently converting "this element is
    gone" into "an element matching its locator is here" -- the one way this
    change could make an assertion pass without it staying true.

    Wrapping happens in exactly one place (``_element_proxy.resolve_element``),
    which is what makes unwrapping expressible at all: the proxy holds the live
    id in the plain ``_id`` attribute rather than in a second source of truth, so
    a bare ``WebElement`` over that id is the same node, minus the healing. The
    public ``id`` property is deliberately *not* used here -- reading it probes
    liveness and would perform the very re-resolution being opted out of.

    A raw ``WebElement`` is returned unchanged, so this is safe to apply
    defensively at a verdict site regardless of where its element came from.
    """
    if isinstance(element, ReResolvingElement):
        return WebElement(element.parent, element._id)
    return element


# German ``d.m.Y`` date, tolerant of zero-padded and numeric parts alike.
DE_DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")

# ── Dialog scoping ────────────────────────────────────────────────────────
# A MUI Dialog's paper carries ``role="dialog"`` -- but so does a *temporary*
# MUI Drawer's paper. Below the `md` breakpoint (900px, i.e. BOTH the mobile
# and the tablet profile) the Sidebar renders as `variant="temporary"` with
# `ModalProps={{ keepMounted: true }}`, so its paper is portalled to
# ``document.body`` at app mount and stays in the DOM with
# ``visibility: hidden`` while the drawer is closed.
#
# An unscoped ``div[role='dialog']`` therefore resolves to that invisible
# drawer paper FIRST (document order), and ``visibility_of_element_located``
# -- which uses ``find_element``, i.e. first match only -- never becomes true.
# CSS selector *lists* are no protection either: they also match in document
# order, so a ``[data-testid='x'], div[role='dialog']`` fallback chain still
# picks the drawer.
#
# Always scope dialog lookups to the MuiDialog subtree (or, better, to the
# dialog's own data-testid). The Drawer root is ``.MuiDrawer-root`` and never
# carries ``.MuiDialog-root``, so this scoping is exact.
DIALOG_SELECTOR = ".MuiDialog-root [role='dialog']"
DIALOG_XPATH = "//*[contains(@class, 'MuiDialog-root')]//*[@role='dialog']"


@dataclass(frozen=True)
class SettledState:
    """Which of the accepted settled branches a route actually reached.

    Returned by :meth:`BasePage.wait_for_settled` and its wrappers so the reached
    branch is *queryable* rather than implicit. Waiting for a disjunction without
    reporting the disjunct is how a test ends up accepting any outcome: a detail
    route that rendered an `ErrorDisplay` instead of its page root satisfies
    "one of these appeared" just as well as the happy path, and the assertion
    that follows then reads an error surface it never meant to accept.

    ``present`` carries *every* branch that was in the DOM at the moment the wait
    returned, in the order the caller declared them, so a caller can distinguish
    "only the error branch" from "the page root plus a section-level error".
    """

    #: The winning branch name -- the first *declared* branch found present.
    branch: str
    #: The locator that branch was declared with.
    locator: Locator
    #: Every branch found present, in declared order (``branch`` is its head).
    present: tuple[str, ...]

    def is_branch(self, name: str) -> bool:
        """Return whether the reached branch is *name*."""
        return self.branch == name


class SidebarNavigationFallback(UserWarning):
    """Emitted when :meth:`BasePage.navigate_via_sidebar` had to navigate by URL.

    A warning rather than silence: the fallback means the suite stopped
    exercising sidebar navigation for that call and the test still passed. It
    surfaces in pytest's warnings summary, so a fallback that starts firing is
    visible without turning every profile red at once.
    """


class BasePage:
    """Shared helpers inherited by every page object."""

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    # ── Navigation ────────────────────────────────────────────────────────

    def navigate(self, path: str) -> None:
        """Navigate to *path* relative to the base URL.

        **Low-level: a bare ``navigate()`` outside a page object's ``open()`` is
        a review finding.** It returns as soon as the document is loaded, which
        for this SPA means "the app shell exists" -- the route's lazily-imported
        chunk and its first fetch are both still in flight, so *every* read that
        follows is a race. Use a page object's ``open()``, or
        :meth:`navigate_direct` when the target key is deliberately invalid and
        no ``open()`` accepts it. ``tests/e2e_selftest/test_navigation_contract.py``
        holds the (shrink-only) list of the sites that still violate this.
        """
        self.driver.get(f"{self.base_url}{path}")

    def navigate_direct(
        self,
        path: str,
        settled: Locator,
        *,
        what: str | None = None,
        extra: Mapping[str, Locator] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> SettledState:
        """Navigate to an arbitrary *path* and wait until the route settled.

        *settled* is mandatory rather than optional: the callers of this helper
        are the "deliberately invalid key" and "no-access-control" tests, and
        every one of them asserts that the route rendered a *particular* shape.
        "No error is on screen" is trivially true of a route that has not
        mounted yet -- a lazily-imported chunk still in flight leaves the app
        chrome alone in the DOM, so an unwaited negative assertion cannot fail.

        Returns the reached :class:`SettledState` rather than ``None`` so the
        caller can assert *which* branch it got (``require_branch``) instead of
        accepting the page root and the error surface interchangeably.
        """
        self.navigate(path)
        return self.wait_for_page_settled(
            settled, what or f"route {path}", extra=extra, timeout=timeout
        )

    # ── Waits ─────────────────────────────────────────────────────────────

    def poll(self, timeout: int = DEFAULT_TIMEOUT) -> WebDriverWait:
        """A ``WebDriverWait`` that treats every transient DOM state as "not yet".

        The single place the polling contract is stated — see
        :data:`POLL_TRANSIENTS` for why Selenium's own default is too narrow.
        """
        return WebDriverWait(self.driver, timeout, ignored_exceptions=POLL_TRANSIENTS)

    # ── The three element-returning waits ─────────────────────────────────
    # All three go through `resolve_element`, which is what makes the reference
    # they hand back survive a re-render: it re-runs its own
    # `(locator, condition)` when the node underneath it dies (see
    # `_element_proxy`). Every capture site in this suite reaches the proxy
    # through one of these three -- there is no fourth singular capture helper --
    # so this is the single wiring point rather than 459 call-site changes.
    #
    # `resolve_element` takes the condition *factory*, never a ready-made
    # condition, and uses it for the first capture and for every re-resolution
    # alike. That is what keeps "waited for clickable" and "healed to clickable"
    # the same predicate **by construction**: there is no way to write a helper
    # here that waits for one condition and heals to another without passing two
    # different factories, and each helper below passes exactly one. Pinned by
    # `tests/e2e_selftest/test_element_proxy.py`
    # (`test_a_clickable_capture_only_heals_to_a_clickable_element`).
    #
    # The declared return type is the concrete `ReResolvingElement`, not
    # `WebElement`: it is a `WebElement` subclass, so all 62 page objects keep
    # type-checking unchanged, while the narrower annotation states at the
    # signature what the caller is actually holding. A caller that must reason
    # about the *node* rather than about the *locator* -- a staleness-as-verdict
    # read -- can strip the healing back off with `raw_reference` (see there).

    def wait_for_element(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> ReResolvingElement:
        """Wait until an element is present in the DOM and return it.

        The returned reference re-resolves through
        ``EC.presence_of_element_located`` -- the same condition this wait used
        -- if the node it points at is replaced by a re-render.
        """
        return resolve_element(self.poll, locator, EC.presence_of_element_located, timeout)

    def wait_for_element_visible(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> ReResolvingElement:
        """Wait until an element is visible and return it.

        The returned reference re-resolves through
        ``EC.visibility_of_element_located``, so a healed replacement is visible
        too -- it can never quietly decay into a merely present element.
        """
        return resolve_element(self.poll, locator, EC.visibility_of_element_located, timeout)

    def wait_for_element_clickable(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> ReResolvingElement:
        """Wait until an element is clickable and return it.

        The returned reference re-resolves through ``EC.element_to_be_clickable``
        -- the strongest of the three -- so a click retried after a re-render is
        still aimed at something the same predicate accepted.
        """
        return resolve_element(self.poll, locator, EC.element_to_be_clickable, timeout)

    def wait_for_element_hidden(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> None:
        """Wait until an element is no longer visible (e.g. MUI Dialog fade-out).

        Deliberately **not** re-resolving, and it never will be: it returns
        ``None``. There is no reference to hand back, hence none to heal -- and
        an absence wait is precisely where healing would be wrong, since
        re-acquiring the element is the outcome this wait exists to rule out.
        """
        self.poll(timeout).until(EC.invisibility_of_element_located(locator))

    #: The Suspense/query loading placeholder every page renders while its data
    #: (or, for a lazily-imported route, its chunk) is still in flight.
    LOADING_SKELETON = (By.CSS_SELECTOR, "[data-testid='loading-skeleton']")
    #: `ErrorDisplay` — the "this entity could not be loaded" branch of a detail
    #: page. Rendered *instead of* the page root, so it is one of the two
    #: legitimate settled states of a detail route.
    ERROR_DISPLAY = (By.CSS_SELECTOR, "[data-testid='error-display']")
    #: `ErrorPage` — the whole-route error/not-found surface (404, 500, ...).
    ERROR_PAGE = (By.CSS_SELECTOR, "[data-testid='error-page']")
    #: `EmptyState` — the "this collection has no entries" branch. A legitimate
    #: settled state of a list route, and emphatically *not* the same thing as
    #: "not loaded yet", which is why it has to be a *named branch* rather than
    #: an absence: a reader that treats both as "no rows" cannot fail.
    EMPTY_STATE = (By.CSS_SELECTOR, "[data-testid='empty-state']")

    # ── Branch names ──────────────────────────────────────────────────────
    # Constants rather than bare strings so an assertion on a reached branch
    # cannot typo the name into a comparison that is silently never true.
    BRANCH_CONTENT = "content"
    BRANCH_ERROR = "error-display"
    BRANCH_ERROR_PAGE = "error-page"
    BRANCH_EMPTY = "empty-state"

    def wait_for_loading_complete(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until no ``[data-testid='loading-skeleton']`` is visible.

        **This is a weak signal and proves nothing about the target content.**
        It is kept because ~340 call sites pair it with a durable wait that does
        the real work (typically ``wait_for_element(self.PAGE)`` in a page
        object's ``open()``); on its own it must not gate a read.

        Two reasons it under-delivers, both observed in this suite:

        * ``invisibility_of_element_located`` is satisfied by an element that is
          **absent**, and it cannot tell "the skeleton has not mounted yet" from
          "the skeleton is gone because loading finished". Right after
          ``navigate()`` the document is loaded but React has not yet reached the
          suspended route, so no skeleton exists and this returns *immediately* —
          `e2e-test-stability` §D calls exactly that ("a poll that can never
          distinguish 'not yet loaded' from 'correctly absent'") an invalid
          assertion. Observed on TC-REQ-001-005, where the body read back held
          nothing but the app chrome (``Mein Garten 16 M``) while
          ``NotFoundPage``'s lazy chunk was still resolving.
        * It says nothing about *which* branch a page then renders. A detail
          route settles into a page root **or** an `ErrorDisplay`; the skeleton
          being gone is common to both and to neither-yet.

        Prefer :meth:`wait_for_content` / :meth:`wait_for_page_settled` (or a
        plain :meth:`wait_for_element` on the content itself) to key the read on
        the content that must actually be there. :meth:`wait_for_skeleton_gone`
        is the *meaningful* form of this wait: identical poll, but only legal
        once a settled branch is already present, which is what makes the
        absence it observes falsifiable.
        """
        self.poll(timeout).until(EC.invisibility_of_element_located(self.LOADING_SKELETON))

    # ── Branch-aware settling ─────────────────────────────────────────────
    # The strong replacement for `wait_for_loading_complete`. Three properties
    # the weak wait lacks, per `e2e-test-stability` §D:
    #
    #   1. It keys on the **presence** of the content the caller is about to
    #      read, so it cannot be satisfied before that content exists. An
    #      absence poll cannot distinguish "not loaded yet" from "correctly
    #      absent" and is therefore not a valid assertion.
    #   2. It accepts an explicit **disjunction of named outcomes** -- a route
    #      legitimately settles into its page root *or* an `ErrorDisplay` *or*
    #      an `EmptyState` -- and reports **which** one was reached, so a test
    #      asserts the branch it meant instead of accepting any of them.
    #   3. It fails loudly, naming every branch it probed and the branch it did
    #      find, instead of returning and letting the following read report a
    #      cause that is nowhere near the real one.

    #: Probes every CSS branch selector in ONE driver round-trip and returns the
    #: indices that matched. Deliberately JS rather than N× ``find_elements``.
    #:
    #: The original reason was cost: the session ran with a driver-level implicit
    #: wait, which applied to every *empty* ``find_elements`` result, so an
    #: N-branch probe spent N×3 s per poll cycle and burned the whole budget in
    #: two cycles. #835 removed that wait, so the arithmetic no longer holds --
    #: an empty ``find_elements`` now returns at once.
    #:
    #: It stays JS for the reason that outlived the wait: N separate lookups are
    #: N separate instants, so a branch that appears midway through the sweep can
    #: be reported alongside one that has already gone. One round-trip reads all
    #: branches against a single DOM state, which is what makes "exactly one
    #: branch matched" a statement about the page rather than about the sweep.
    _PROBE_CSS_BRANCHES = (
        "var sels = arguments[0], out = [];"
        "for (var i = 0; i < sels.length; i++) {"
        "  if (document.querySelector(sels[i]) !== null) { out.push(i); }"
        "}"
        "return out;"
    )

    def probe_branches(self, branches: Mapping[str, Locator]) -> tuple[str, ...]:
        """Return the names of every *branches* entry present in the DOM.

        Order follows the caller's declaration order, not DOM order, so the
        winner picked by :meth:`resolve_settled_branch` is a property of the
        caller's contract rather than of the page's markup.
        """
        names = list(branches)
        css_idx = [i for i, name in enumerate(names) if branches[name][0] == By.CSS_SELECTOR]
        found: set[str] = set()
        if css_idx:
            matched = self.driver.execute_script(
                self._PROBE_CSS_BRANCHES, [branches[names[i]][1] for i in css_idx]
            )
            found |= {names[css_idx[int(i)]] for i in (matched or [])}
        for i, name in enumerate(names):
            if i not in css_idx and self.driver.find_elements(*branches[name]):
                found.add(name)
        return tuple(name for name in names if name in found)

    @staticmethod
    def resolve_settled_branch(
        branches: Mapping[str, Locator], present: Sequence[str]
    ) -> SettledState | None:
        """Pick the winning branch out of the ones *present*, or ``None``.

        Pure: no driver, no clock -- which is what makes the branch contract
        unit-testable (``tests/e2e_selftest/``) instead of only observable in a
        full browser run.

        Resolution is by **declared order**, and that is a deliberate contract
        rather than an implementation detail. Two branches can be present at
        once -- a detail page root that renders a section-level `ErrorDisplay`
        inside one of its tabs is the common case -- and a caller that declares
        ``{content: PAGE, error: ERROR_DISPLAY}`` is saying "if the page root is
        there, that is the outcome I am reading; the error only wins when the
        root is *not* there". Reversing the declaration reverses the precedence.
        """
        found = tuple(name for name in branches if name in present)
        if not found:
            return None
        return SettledState(branch=found[0], locator=branches[found[0]], present=found)

    def wait_for_settled(
        self,
        branches: Mapping[str, Locator],
        what: str,
        timeout: int = DEFAULT_TIMEOUT,
        *,
        require_no_skeleton: bool = True,
    ) -> SettledState:
        """Wait until one of the named *branches* is present; return which one.

        *branches* maps a branch name onto the locator that proves it. At least
        one entry is required -- an empty disjunction is a wait that can never
        be satisfied *and* never be falsified, so it is rejected outright rather
        than left to time out with a confusing message.

        With ``require_no_skeleton`` (the default) the wait continues, on the
        remaining budget, until no `LoadingSkeleton` is visible. That second
        phase is the *legal* use of the skeleton-absence poll: a settled branch
        is already on screen, so "no skeleton" now means "the data this page
        renders has arrived" rather than "React has not got here yet". A page
        root can mount while its own query skeleton is still up -- that is
        exactly the window a read must not land in.
        """
        if not branches:
            raise ValueError(
                "wait_for_settled() needs at least one branch. An empty "
                "disjunction can neither be satisfied nor falsified."
            )
        deadline = time.time() + timeout
        state: list[SettledState] = []

        def _settled(_driver: WebDriver) -> bool:
            resolved = self.resolve_settled_branch(branches, self.probe_branches(branches))
            if resolved is None:
                return False
            state.append(resolved)
            return True

        try:
            self.poll(timeout).until(_settled)
        except TimeoutException as exc:
            probed = ", ".join(f"{name}={value!r}" for name, (_by, value) in branches.items())
            raise AssertionError(
                f"{what}: none of the expected settled states appeared within "
                f"{timeout}s (probed {probed}). The route is most likely still "
                "resolving its lazily-imported chunk or its first fetch -- "
                "reading the page here would assert against the app chrome alone."
            ) from exc

        if require_no_skeleton:
            self.wait_for_skeleton_gone(
                f"{what} (branch {state[0].branch!r} reached)",
                timeout=max(1, int(deadline - time.time())),
            )
        return state[0]

    def wait_for_skeleton_gone(self, what: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until no `LoadingSkeleton` is visible, and fail loudly if one stays.

        Only meaningful **after** a settled branch is known to be present: on its
        own this is the unfalsifiable poll of
        :meth:`wait_for_loading_complete`. With the branch already on screen the
        absence is falsifiable, so a timeout is a real finding ("the page
        rendered but its data never arrived") and is raised rather than
        swallowed.
        """
        try:
            self.poll(timeout).until(EC.invisibility_of_element_located(self.LOADING_SKELETON))
        except TimeoutException as exc:
            raise AssertionError(
                f"{what}: a loading skeleton is still visible after {timeout}s. "
                "The page root rendered but a fetch it displays never resolved, "
                "so any read here would see placeholder content."
            ) from exc

    def page_branches(
        self, page: Locator, *, extra: Mapping[str, Locator] | None = None
    ) -> dict[str, Locator]:
        """Return the standard settled-branch map of a data-backed route.

        ``content`` first (see :meth:`resolve_settled_branch` on why order is the
        contract), then the two error surfaces. *extra* is appended, which is
        where a list route adds ``{BRANCH_EMPTY: self.EMPTY_STATE}``.
        """
        branches = {
            self.BRANCH_CONTENT: page,
            self.BRANCH_ERROR: self.ERROR_DISPLAY,
            self.BRANCH_ERROR_PAGE: self.ERROR_PAGE,
        }
        branches.update(extra or {})
        return branches

    def wait_for_page_settled(
        self,
        page: Locator,
        what: str,
        *,
        extra: Mapping[str, Locator] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        require_no_skeleton: bool = True,
    ) -> SettledState:
        """Wait until *page* **or** one of the error surfaces settled; report which.

        The everyday form of :meth:`wait_for_settled`: use it whenever the test
        is willing to see either the page or an error and wants to *assert* on
        the difference (``state.branch``), and :meth:`wait_for_content` when only
        the page is acceptable.
        """
        return self.wait_for_settled(
            self.page_branches(page, extra=extra),
            what,
            timeout=timeout,
            require_no_skeleton=require_no_skeleton,
        )

    def wait_for_content(
        self,
        page: Locator,
        what: str,
        *,
        extra: Mapping[str, Locator] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        require_no_skeleton: bool = True,
    ) -> SettledState:
        """Wait until *page* rendered, failing loudly if an error surface won instead.

        The right gate for the overwhelmingly common "navigate, then read the
        page" flow. It differs from ``wait_for_element(page)`` in what happens on
        the unhappy path: a bare element wait times out after the full budget
        with "element not found", while this reports *what the app actually
        showed* -- including the `ErrorDisplay`'s own message -- so the cause is
        in the first failure line instead of in a screenshot nobody opened yet.
        """
        state = self.wait_for_page_settled(
            page,
            what,
            extra=extra,
            timeout=timeout,
            require_no_skeleton=require_no_skeleton,
        )
        self.require_branch(state, self.BRANCH_CONTENT, what)
        return state

    def require_branch(self, state: SettledState, expected: str, what: str) -> None:
        """Fail loudly unless *state* reached the *expected* branch.

        Separate from the wait so a test that legitimately accepts several
        outcomes can still make the accepted one explicit at the point it reads,
        which is the difference between "I waited for a disjunction" and "I
        asserted an outcome".
        """
        if state.is_branch(expected):
            return
        detail = ""
        if state.branch in (self.BRANCH_ERROR, self.BRANCH_ERROR_PAGE):
            detail = f" It reads: {self.get_error_text()!r}."
        raise AssertionError(
            f"{what}: expected the {expected!r} branch, but the route settled "
            f"into {state.branch!r} (present: {', '.join(state.present)}).{detail}"
        )

    ERROR_MESSAGE = (By.CSS_SELECTOR, "[data-testid='error-message']")

    def get_error_text(self) -> str:
        """Return the rendered text of whichever error surface is on screen, or ``''``."""
        for locator in (self.ERROR_MESSAGE, self.ERROR_DISPLAY, self.ERROR_PAGE):
            elements = self.driver.find_elements(*locator)
            if elements:
                return (elements[0].get_attribute("textContent") or "").strip()
        return ""

    def wait_for_any_present(
        self,
        locators: tuple[Locator, ...],
        what: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Locator:
        """Wait until at least one of *locators* is in the DOM; return which one.

        The positional, un-named form of :meth:`wait_for_settled`, kept for the
        callers that only need "one of these exists". Prefer the named form when
        the *identity* of the reached state matters -- which is most of the time,
        because a disjunction whose disjunct is never inspected accepts the
        error branch as readily as the happy one.
        """
        branches = {f"branch-{i}": locator for i, locator in enumerate(locators)}
        state = self.wait_for_settled(branches, what, timeout=timeout, require_no_skeleton=False)
        return state.locator

    def wait_for_url_contains(self, fragment: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the current URL contains *fragment*.

        Satisfied immediately when the URL *already* contains it, so this is only
        a sound post-condition for a navigation that leaves a URL family the test
        was not already inside. To await a transition *within* one family — one
        detail page to another — use :meth:`wait_for_url_change`.
        """
        self.poll(timeout).until(EC.url_contains(fragment))

    def wait_for_url_change(
        self, previous: str, fragment: str, timeout: int = DEFAULT_TIMEOUT
    ) -> str:
        """Wait until the URL both differs from *previous* and contains *fragment*.

        The post-condition :meth:`wait_for_url_contains` cannot express. Waiting
        for a fragment that is already present is a check that cannot fail: it
        returns at once and the caller reads the URL it was *leaving*. #835 found
        that in `provision_plant`, which derived a plant key that way — the
        implicit wait had been delaying the click just enough that the URL was
        usually the new one by the time it was read, so the journeys asserted
        against a plant from an earlier test.
        """
        self.poll(timeout).until(lambda d: d.current_url != previous and fragment in d.current_url)
        return self.driver.current_url

    # ── Queries ───────────────────────────────────────────────────────────

    def find_present(
        self, locator: Locator, timeout: int = IMPLICIT_WAIT_EQUIVALENT
    ) -> ReResolvingElement:
        """Find an element the caller expects to be rendered already.

        The explicit counterpart to the driver-level implicit wait #835 removed:
        same budget, but visible at the call site and no longer silently added to
        every lookup *inside* a ``WebDriverWait``, where the two wait kinds
        compounded into timeouts nobody could predict — the reason one
        post-condition (``TaskDetailPage.SUBMIT_REGISTERED_TIMEOUT``) was given
        an 8 s budget where 3 s should have done. That budget has *not* been
        re-cut here: its size was justified by a cost that no longer exists, but
        shrinking it is a measurement, not a docstring edit.

        Use :meth:`wait_for_element` instead when the element is genuinely
        expected to *appear*. That is a page transition, not a lookup, and
        deserves the full ``DEFAULT_TIMEOUT``.

        Its 48 call sites — an AST call count, for the reason
        :data:`IMPLICIT_WAIT_EQUIVALENT` sets out; the 49 carried here before
        #835 P6 had counted this definition as one of them — inherit the
        re-resolving reference from the `return`
        below rather than from a rule anybody has to remember: this **is**
        :meth:`wait_for_element` on a shorter budget, so there is no second code
        path here that could be left un-wired. The narrowed return type is what
        makes that structural instead of incidental -- widen the body back to a
        raw lookup and the signature stops type-checking.
        """
        return self.wait_for_element(locator, timeout)

    def retry_on_stale[T](
        self, action: Callable[[], T], timeout: int = IMPLICIT_WAIT_EQUIVALENT
    ) -> T:
        """Run *action*, re-running it from scratch if the DOM moved underneath.

        For the capture-then-use shape that :meth:`poll` cannot cover: a row
        reference is taken, then a cell is read or clicked *through* it. When
        React re-renders the table in between, the reference is stale and the
        whole capture has to be redone — ``ignored_exceptions`` retries the
        condition inside one poll, but it cannot un-stale a reference the caller
        is already holding.

        *action* must therefore re-acquire what it touches; passing a closure
        over an already-resolved element would retry the same dead reference.
        """
        deadline = time.time() + timeout
        while True:
            try:
                return action()
            except StaleElementReferenceException:
                if time.time() >= deadline:
                    raise

    def find_by_testid(self, testid: str) -> ReResolvingElement:
        """Shorthand for finding an element by its ``data-testid``.

        Re-resolving for the same structural reason as :meth:`find_present`: it
        builds a locator and delegates, so it has no lookup of its own to wire.
        """
        return self.find_present((By.CSS_SELECTOR, f"[data-testid='{testid}']"))

    def find_all_by_testid(self, testid: str) -> list[WebElement]:
        """Return all elements matching the given ``data-testid``."""
        return self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{testid}']")

    def click_column_header(self, header_text: str) -> None:
        """Sort a ``DataTable`` by clicking the column header labelled *header_text*.

        Clicks the ``TableSortLabel`` inside the header cell, **not** the cell
        itself. The click handler sits on the label, and Selenium clicks an
        element's centre point -- so on any column wider than its own label the
        click landed on empty cell padding and sorted nothing. That stayed
        invisible because the sort chip is rendered from ``defaultSort``
        regardless of whether a click ever arrived, so tests asserting only on
        the chip passed while verifying nothing (#802).

        Fourteen page objects carried a byte-identical copy of the broken
        version; they now delegate here.
        """
        headers = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='data-table'] th")
        for h in headers:
            if h.text != header_text:
                continue
            # `sort-<column id>` is emitted by DataTable for every sortable
            # column. Falling back to clicking the cell would reinstate the
            # silent no-op this method exists to remove, so a header without the
            # label is an error rather than a degraded click.
            labels = h.find_elements(By.CSS_SELECTOR, "[data-testid^='sort-']")
            if not labels:
                raise ValueError(
                    f"Column header '{header_text}' carries no sort label "
                    "(data-testid='sort-<column>') -- the column is not sortable, "
                    "so clicking it cannot sort the table"
                )
            self.scroll_and_click(labels[0])
            return
        raise ValueError(f"Column header '{header_text}' not found")

    #: Overflow trigger rendered by ``PageHeaderActions`` on ``xs``.
    PAGE_HEADER_OVERFLOW = (By.CSS_SELECTOR, "[data-testid='page-header-overflow']")

    def _header_action_element(self, testid: str) -> WebElement | None:
        """Return the element behind a header action, opening the overflow if needed.

        Returns ``None`` when the action does not exist at this viewport at all —
        which for several pages is meaningful rather than accidental
        (UI-NFR-018 R-012 omits a delete action for system data instead of
        disabling it).

        Leaves the menu open when it had to be opened; callers that only inspect
        state can close it with ``close_mui_dropdown``.
        """
        direct = self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{testid}']")
        if direct:
            return direct[0]
        trigger = self.driver.find_elements(*self.PAGE_HEADER_OVERFLOW)
        if not trigger:
            return None
        self.scroll_and_click(trigger[0])
        entries = self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{testid}-menu-item']")
        return entries[0] if entries else None

    def has_header_action(self, testid: str) -> bool:
        """Whether a page-header action exists, as button (``sm``+) or menu entry (``xs``)."""
        found = self._header_action_element(testid) is not None
        self.close_mui_dropdown()
        return found

    def is_header_action_enabled(self, testid: str) -> bool:
        """Whether a page-header action is actionable at the current viewport.

        A disabled `MenuItem` reports ``is_enabled() == True`` to Selenium — it
        is a list item, not a form control — so the ``aria-disabled`` attribute
        MUI sets is the reliable signal there, while real buttons carry
        ``disabled``. Both are checked, which keeps this correct on either side
        of the breakpoint.
        """
        el = self._header_action_element(testid)
        if el is None:
            self.close_mui_dropdown()
            return False
        enabled = (
            el.is_enabled()
            and not el.get_attribute("disabled")
            and el.get_attribute("aria-disabled") != "true"
        )
        self.close_mui_dropdown()
        return enabled

    def click_header_action(self, testid: str) -> None:
        """Trigger a page-header action by its ``data-testid``, at any viewport.

        UI-NFR-021 R-024 leaves only the primary action directly visible on
        ``xs``; the others move into a ``⋮`` menu, where ``PageHeaderActions``
        renders them as ``<testid>-menu-item``. A page object that clicks the
        plain testid therefore works on desktop and silently stops finding its
        button on the mobile profiles.

        Order matters: the direct control is tried first, so desktop keeps its
        single click and no menu is opened that would then have to be closed
        again.
        """
        direct = self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{testid}']")
        if direct and direct[0].is_displayed():
            self.scroll_and_click(direct[0])
            return

        trigger = self.driver.find_elements(*self.PAGE_HEADER_OVERFLOW)
        if not trigger:
            raise ValueError(
                f"Header action '{testid}' is neither visible nor behind an overflow menu "
                "(no [data-testid='page-header-overflow'] on the page)"
            )
        self.scroll_and_click(trigger[0])
        item = self.wait_for_element_clickable(
            (By.CSS_SELECTOR, f"[data-testid='{testid}-menu-item']")
        )
        self.click_menu_option(item)

    def is_present(self, locator: tuple[str, str]) -> bool:
        """Return True if at least one element matching *locator* exists in the DOM."""
        return len(self.driver.find_elements(*locator)) > 0

    # ── Honest negatives after a client-side navigation ───────────────────
    # `driver.find_elements(...) -> [] -> False` is an *instantaneous* read, and
    # right after a route change, a tab switch or a drawer opening it cannot
    # tell "React has not committed the destination yet" from "this element is
    # genuinely absent" -- the unfalsifiable-absence shape `e2e-test-stability`
    # §D forbids. The driver-level implicit wait had been granting every such
    # read up to 3 s; #835 removed it and six assertions that had always been
    # asking one render too early started failing (tank tabs "found 0 tabs",
    # `workflow-detail-page` not visible, the tenant-settings create-link
    # button, the notification drawer's action buttons).
    #
    # The two helpers below are the honest form: wait for the element to appear
    # first, and answer "absent" only once the budget is spent. That removes the
    # false negative without weakening the true one -- an element that never
    # renders still yields `False`/`[]` and the caller's assertion still fails.

    def await_presence(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> list[WebElement]:
        """Every element matching *locator*, after waiting for the first to appear.

        Returns ``[]`` when none appears within *timeout* -- a genuine negative,
        because the wait has been spent, unlike the bare ``find_elements`` this
        replaces.
        """
        try:
            self.poll(timeout).until(lambda d: len(d.find_elements(*locator)) > 0)
        except TimeoutException:
            return []
        return self.driver.find_elements(*locator)

    def is_visible_within(self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Whether *locator* is displayed, waiting for it to appear first.

        The honest counterpart of ``find_elements(...)[0].is_displayed()``: a
        ``False`` here means "not displayed after waiting *timeout*", not "not
        displayed in this millisecond".
        """
        try:
            self.poll(timeout).until(EC.visibility_of_element_located(locator))
        except TimeoutException:
            return False
        return True

    def is_any_displayed(self, locator: tuple[str, str]) -> bool:
        """Return whether any element matching *locator* is displayed right now.

        The plural counterpart of a staleness *verdict*, and the shape three
        page objects had each written out for themselves: a dialog animating
        out can unmount between the ``find_elements`` and the
        ``is_displayed()``, and a reference that dies in that window means the
        dialog is **gone** -- not "look again". The three copies
        (`PhaseTransitionPage.is_transition_dialog_open` /
        `.is_confirm_dialog_visible`, `FeedingEventListPage.is_create_dialog_open`)
        now delegate here, so the decision is recorded in one place instead of
        being re-made per page.

        :func:`raw_reference` is applied even though ``find_elements`` yields
        raw elements today. The point is that the verdict must not depend on
        that: this is a *negative* answer built out of an exception, so if the
        plural path ever started healing, every "the dialog closed" assertion
        would quietly start waiting for the replacement instead -- and pass or
        fail on the node that came back rather than on the one that left. The
        strip is a no-op on a raw element (it returns it unchanged), so the
        guard costs nothing to hold.

        Deliberately *not* a poll: callers use it as an instantaneous read
        inside their own waits.
        """
        for element in self.driver.find_elements(*locator):
            node = raw_reference(element)
            try:
                if node.is_displayed():
                    return True
            except StaleElementReferenceException:
                continue
        return False

    def get_text_stable(self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT) -> str:
        """Return text of *locator*, retrying on StaleElementReferenceException."""
        deadline = time.time() + timeout
        while True:
            try:
                el = self.wait_for_element_visible(
                    locator, timeout=min(5, max(1, int(deadline - time.time())))
                )
                return el.text
            except StaleElementReferenceException:
                if time.time() >= deadline:
                    raise
                time.sleep(0.2)

    def get_page_title(self) -> str:
        """Return the text content of the ``[data-testid='page-title']`` element."""
        return self.get_text_stable((By.CSS_SELECTOR, "[data-testid='page-title']"))

    def is_error_displayed(self) -> bool:
        """Check whether ``[data-testid='error-display']`` is visible."""
        elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='error-display']")
        return len(elements) > 0 and elements[0].is_displayed()

    def has_alert_notification(self) -> bool:
        """Check whether any ``[role='alert']`` notification is present (e.g. an error snackbar)."""
        return len(self.driver.find_elements(By.CSS_SELECTOR, "[role='alert']")) > 0

    def get_body_text(self) -> str:
        """Return the full text content of the page body (for keyword assertions)."""
        return self.find_present((By.TAG_NAME, "body")).text

    def page_shows_text(self, needle: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Whether *needle* appears in the page body within *timeout*.

        Waits rather than sampling once: the caller usually asks right after a
        navigation, and the answer "no" one render too early is indistinguishable
        from "no" — which is how a missing wait becomes a confident wrong answer.
        """
        try:
            self.poll(timeout).until(lambda _d: needle in self.get_body_text())
        except TimeoutException:
            return False
        return True

    # ── Interactions ─────────────────────────────────────────────────────

    OPTIONS = (By.CSS_SELECTOR, "li[role='option']")
    LISTBOX = (By.CSS_SELECTOR, "[role='listbox']")

    def _wait_options_gone(self, timeout: float) -> bool:
        """Wait (bounded) until no ``li[role='option']`` is left; return the outcome."""
        try:
            self.poll(timeout).until(lambda d: len(d.find_elements(*self.OPTIONS)) == 0)
            return True
        except TimeoutException:
            return False

    def close_mui_dropdown(self, timeout: int = 5) -> None:
        """Close any open MUI Select dropdown, or fail loudly if it stays open.

        Fails loudly by design: an open popover is a full-screen click-away
        overlay, so returning while it is still up pushes the failure onto the
        *next* interaction, which then reports "button not clickable" for a
        cause that is nowhere near it (observed in
        ``FAILURE_test_ended_cycle_spawns_no_new_instance.png``). The previous
        ``except TimeoutException: pass`` swallowed exactly that.

        The Escape key goes to the listbox rather than to ``<body>``: a blind
        body-level Escape is delivered to whatever modal currently has focus,
        so it closes the *surrounding dialog* when the popover happens to have
        closed itself in the meantime.
        """
        from selenium.webdriver.common.keys import Keys

        if not self.driver.find_elements(*self.OPTIONS):
            return  # Already closed

        # After an option click MUI closes the popover on its own — give the
        # close a bounded moment before touching the keyboard at all.
        if self._wait_options_gone(2):
            return

        # Dropdown is genuinely open (opened without selecting) — close it via
        # Escape on the menu itself, which is where MUI's key handler sits.
        target = next(iter(self.driver.find_elements(*self.LISTBOX)), None)
        if target is None:
            target = next(iter(self.driver.find_elements(*self.OPTIONS)), None)
        if target is None:
            return  # raced to closed between the two lookups
        try:
            target.send_keys(Keys.ESCAPE)
        except (
            ElementNotInteractableException,
            StaleElementReferenceException,
        ):
            self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)

        if not self._wait_options_gone(timeout):
            raise AssertionError(
                f"MUI dropdown did not close within {timeout}s — "
                f"{len(self.driver.find_elements(*self.OPTIONS))} option(s) are "
                "still in the DOM. Its click-away overlay will intercept every "
                "following click."
            )

    #: Controls whose menu/popover opens on ``mousedown`` rather than on
    #: ``click``: the MUI Select display div (``[role='combobox']`` since v5,
    #: ``.MuiSelect-select`` as the legacy class hook).
    MENU_TRIGGER_CSS = "[role='combobox'], .MuiSelect-select"

    def opens_on_mousedown(self, element: WebElement) -> bool:
        """Return True if *element* is a control that opens on ``mousedown``."""
        return bool(
            self.driver.execute_script(
                "return arguments[0].matches(arguments[1]);",
                element,
                self.MENU_TRIGGER_CSS,
            )
        )

    def dispatch_menu_trigger_open(self, element: WebElement) -> None:
        """Dispatch a ``mousedown``/``mouseup`` pair straight onto a menu trigger.

        MUI opens a Select **only** from its ``onMouseDown`` handler -- there is
        no ``onClick`` opener. A JS ``element.click()`` dispatches a lone
        ``click`` event, so it can never open one; it merely *reports* success.
        This sends the pair a real pointer would.

        Deliberately dispatched on the element rather than through
        ``ActionChains``: ActionChains is coordinate-based and, unlike
        ``WebElement.click()``, performs no interactability hit-test, so under
        an overlay it silently delivers the events to the overlay -- the same
        class of silent-success defect this replaces. Also deliberately without
        a trailing ``click``: MUI has already opened the menu on ``mousedown``,
        and a bubbling ``click`` can be read as a click-away.
        """
        self.driver.execute_script(
            "var el = arguments[0];"
            "['mousedown', 'mouseup'].forEach(function (type) {"
            "  el.dispatchEvent(new MouseEvent(type, {"
            "    bubbles: true, cancelable: true, view: window, button: 0,"
            "  }));"
            "});",
            element,
        )

    def scroll_into_view(self, element: WebElement) -> None:
        """Scroll *element* into view, inside **every** scrollable ancestor.

        ``scrollIntoView`` walks the whole ancestor chain, not just the
        document's scrolling element, which is what makes it the right
        primitive for content inside an ``overflow: auto`` container (the
        Sidebar's nav box, a MUI Popover paper).
        """
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            element,
        )

    def is_displayed_in_scroll_container(self, element: WebElement) -> bool:
        """Return whether *element* is displayed once scrolled into view.

        Selenium's displayedness check reports ``False`` both for "not
        rendered" and for "rendered but clipped by a scrollable ancestor", so a
        bare ``is_displayed()`` on content inside an ``overflow: auto``
        container silently answers a question about *rendering* with the
        container's *scroll position*. Scrolling first collapses the two cases
        onto the one the caller actually asks about.

        A stale element is genuinely gone, hence ``False`` -- and that verdict is
        held open deliberately. Both callers drive a *hidden*-ness decision from
        it (``ExpertiseLevelPage.wait_for_nav_item_hidden``,
        :meth:`navigate_via_sidebar`'s "the item is not there, so warn and route
        by URL"), so an element that re-resolved itself and answered ``True``
        would turn "the app correctly hides this nav item" into "it is visible"
        and "the drawer was not exercised" into a silent pass.

        Hence :func:`raw_reference`: the reference is stripped of its healing
        *before* it is read, so the question stays "did **this** node survive"
        rather than "does something matching its locator exist now". Today both
        callers pass a raw element out of ``find_elements``, and #835 P4 decided
        *not* to wrap that path -- so the strip guards a case that cannot arise
        yet. It is kept, and pinned by a test that hands this method a proxy on
        purpose (`tests/e2e_selftest/test_row_helpers.py`), because an opt-out
        that is only correct while nothing exercises it is a coincidence rather
        than a guard.
        """
        node = raw_reference(element)
        try:
            self.scroll_into_view(node)
            return node.is_displayed()
        except StaleElementReferenceException:
            return False

    def click_menu_option(self, element: WebElement) -> None:
        """Click an open menu's option coordinate-independently.

        A MUI ``MenuItem`` activates from its ``onClick`` handler, so a
        synthetic ``element.click()`` drives it exactly as a real pointer does.
        This is **not** in tension with :meth:`dispatch_menu_trigger_open`: a
        Select *trigger* opens only from ``onMouseDown``, which a JS ``click()``
        never dispatches, so there the same call would be a silent no-op.

        Coordinate independence is the whole point. A native click resolves the
        element's centre and *then* dispatches at those coordinates; in between,
        the menu can still move — and both motion sources are JavaScript layout
        effects rather than CSS transitions, so no animation or reduced-motion
        setting removes them:

        * ``Menu`` scrolls its paper to the selected item on open
          (``handleEntering`` -> ``MenuList`` under the default
          ``variant='selectedMenu'``). That moves every option while leaving the
          paper's own ``top``/``left``/``height`` bit-identical.
        * ``Popover`` clamps a menu that does not fit below its anchor upward.

        Observed on the mobile profile as a uniform, directional two-option
        offset: clicks aimed at ``FREQ=WEEKLY`` committed ``FREQ=MONTHLY``, and
        one aimed at the last option committed nothing at all. Dispatching on
        the already-resolved element cannot miss.
        """
        self._dispatch_click(element)

    def _dispatch_click(self, element: WebElement) -> None:
        """Dispatch a synthetic ``click`` straight onto the resolved *element*.

        The one place this suite's coordinate-independent clicks go through, so
        the soundness argument lives in exactly one docstring per activation
        model (:meth:`click_menu_option`, :meth:`click_coordinate_free`) instead
        of being re-derived at every call site.
        """
        self.driver.execute_script("arguments[0].click();", element)

    def click_coordinate_free(self, element: WebElement) -> None:
        """Click a ``click``-activated control without going through coordinates.

        Use this for the submit/confirm button of a long in-page form. A native
        ``WebElement.click()`` resolves the element's in-view centre point and
        only *then* dispatches at those coordinates, and on a 393x852 viewport a
        form's action row sits at the very bottom of a page far taller than the
        viewport: ``scrollIntoView({block: 'center'})`` cannot centre it (the
        document is already scrolled to its maximum), so the button ends up
        within a few pixels of the fold, where any residual scrolling between
        the interactability check and the dispatch is enough to put the
        resolved point off the button. Nothing raises when that happens -- the
        hit-test passed, the events went out, and no ``submit`` event was ever
        produced.

        Observed on the mobile profile as the whole ``TestTaskUpdatePropagation``
        class failing with a still-dirty form, an enabled submit button and no
        field errors (run ``20260725_113337``), while every desktop profile
        wrote its eight ``PUT /tasks/{key}`` 200s.

        Sound for a ``<button type='submit'>``: ``HTMLElement.click()`` runs the
        element's default activation behaviour, i.e. it submits the owning form
        exactly as a pointer does. Explicitly **not** sound for a MUI Select
        trigger, which opens only from ``onMouseDown`` -- a lone ``click`` there
        is a silent no-op, so those are rejected here and must go through
        :meth:`dispatch_menu_trigger_open` / :meth:`open_select_in`.

        A disabled control is rejected for the same reason: the browser drops
        the default action, so the call would report success without having
        done anything.
        """
        if self.opens_on_mousedown(element):
            raise AssertionError(
                "click_coordinate_free() was called on a control that opens on "
                "mousedown (a MUI Select trigger). A synthetic click cannot open "
                "it and would silently report success -- use open_select() / "
                "open_select_by_testid() instead."
            )
        self.scroll_into_view(element)
        if not element.is_enabled():
            raise AssertionError(
                "click_coordinate_free() was called on a disabled control: the "
                "browser suppresses its default action, so the click would be a "
                "silent no-op. Wait for the control to become enabled first."
            )
        self._dispatch_click(element)

    def wait_and_click_coordinate_free(
        self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT
    ) -> None:
        """Wait until *locator* is clickable, then click it coordinate-free.

        The counterpart of :meth:`wait_and_click` for form submits; see
        :meth:`click_coordinate_free` for why coordinates are the hazard there.
        """
        self.click_coordinate_free(self.wait_for_element_clickable(locator, timeout=timeout))

    def scroll_and_click(self, element: WebElement) -> None:
        """Scroll an element into view and click it, with a sound JS fallback.

        The fallback is chosen by target: a bare JS ``click()`` is fine for
        buttons and links, but is a *silent no-op* on a MUI Select trigger
        (which opens on ``mousedown``), so those get an explicit
        mousedown/mouseup pair instead — see
        :meth:`dispatch_menu_trigger_open`. Menu *options* never belong here:
        they are clicked coordinate-independently via
        :meth:`click_menu_option`.
        """
        self.scroll_into_view(element)
        try:
            element.click()
        except ElementNotInteractableException, ElementClickInterceptedException:
            if self.opens_on_mousedown(element):
                self.dispatch_menu_trigger_open(element)
            else:
                self._dispatch_click(element)

    def wait_and_click(self, locator: tuple[str, str], timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until *locator* is clickable, scroll it into view, then click it.

        The scroll step is not cosmetic: below the `sm` breakpoint MUI dialogs
        render ``fullScreen``, so a form's action row is the last child of a
        scrolling ``DialogContent`` and sits *below the fold*.
        ``element_to_be_clickable`` is satisfied by a displayed+enabled element
        regardless of whether it is inside the viewport, so a naked ``.click()``
        on such a button raises ``ElementNotInteractableException`` (or, once
        ChromeDriver's own scroll puts it under the fixed AppBar,
        ``ElementClickInterceptedException``).

        Use this for every submit/cancel-style action; ``scroll_and_click``
        stays available for callers that already hold the element.

        Exception: the submit button of a **long in-page form** (a detail page's
        edit tab, not a dialog) is scroll-clamped against the bottom of the
        document, where the coordinate dispatch this helper ends in silently
        misses. Those go through :meth:`wait_and_click_coordinate_free`.
        """
        self.scroll_and_click(self.wait_for_element_clickable(locator, timeout=timeout))

    # ── Robust form-select / table helpers (prefer dedicated testids) ──────
    # These replace brittle `.MuiSelect-select` clicks, i18n-fragile
    # `contains(text(), label)` option XPaths, and position-based `cells[N]`
    # access with the dedicated data-testids emitted by FormSelectField and
    # DataTable. They fall back to the legacy selectors so page objects can be
    # migrated incrementally.

    #: Trigger sub-selectors probed inside a select container, in order: the
    #: ARIA display (stable across MUI versions), then the legacy class hook.
    SELECT_TRIGGER_SUBSELECTORS = ("[role='combobox']", ".MuiSelect-select")

    def is_select_open(self, trigger: WebElement) -> bool:
        """Return True while *trigger*'s dropdown is open.

        Keyed on the trigger's own ``aria-expanded`` (durable, and true even for
        a menu that legitimately renders zero options), with the rendered
        listbox as a second signal for triggers that don't carry the attribute
        or that went stale on the re-render the open caused.
        """
        if self._aria_expanded(trigger) == "true":
            return True
        return len(self.driver.find_elements(By.CSS_SELECTOR, "li[role='option']")) > 0

    @staticmethod
    def _aria_expanded(trigger: WebElement) -> str:
        """Return *trigger*'s ``aria-expanded``, or ``'<stale>'`` if it unmounted.

        The one staleness handler in this module that deliberately keeps its
        healing (no :func:`raw_reference` here), because ``'<stale>'`` was never
        a verdict: it is neither ``'true'`` nor ``'false'``, and
        :meth:`is_select_open` falls through to the rendered listbox precisely
        because a trigger that unmounted on the re-render its own opening caused
        has *no* answer to give. A re-resolving trigger supplies the real one
        from the re-rendered node -- which is what the listbox fallback was
        approximating in the first place.

        Its callers hand it a proxy (:meth:`open_select_in` resolves the trigger
        through :meth:`wait_for_element_clickable`), so this path is live rather
        than hypothetical. A trigger that is genuinely gone still reaches
        ``'<stale>'``: the proxy raises ``ElementReResolutionError``, a
        ``StaleElementReferenceException`` subclass, once its own budget is out.
        It costs that budget to say so, which is why the answer is a fallback
        signal and not something a poll spins on.
        """
        try:
            return trigger.get_attribute("aria-expanded") or ""
        except StaleElementReferenceException:
            return "<stale>"

    def _settle_listbox(self, timeout: int = 2) -> None:
        """Wait until an opened dropdown's options are queryable.

        ``aria-expanded`` can be observed a beat before the portalled menu's
        ``li[role='option']`` nodes are queryable, which would make an
        immediately following ``find_elements`` return ``[]``. A Select whose
        option list is legitimately empty is not an error condition -- it stays
        open with zero options, so callers that require options assert on them
        and this returns.

        Deliberately no geometry-settling step: the menu's *position* stopped
        mattering once options are clicked on the resolved element rather than
        at resolved coordinates (:meth:`click_menu_option`). The removed guard
        compared the popover paper's ``top``/``left``/``height`` — which is
        blind to the dominant motion source, ``Menu`` scrolling *inside* that
        paper to the selected item, since that leaves the paper's own rect
        bit-identical. A guard that cannot see the motion it was built to catch
        only mis-attributes later failures.
        """
        try:
            self.poll(timeout).until(lambda d: len(d.find_elements(*self.OPTIONS)) > 0)
        except TimeoutException:
            return

    def _wait_until_select_open(self, trigger: WebElement, timeout: int = 5) -> bool:
        """Wait (bounded) until *trigger*'s dropdown is open; return the outcome."""
        try:
            self.poll(timeout).until(lambda _d: self.is_select_open(trigger))
            return True
        except TimeoutException:
            return False

    def open_select(self, field_name: str) -> None:
        """Open a FormSelectField dropdown and verify that it actually opened."""
        self.open_select_in(f"[data-testid='form-field-{field_name}']", f"field '{field_name}'")

    def open_select_by_testid(self, testid: str) -> None:
        """Open a MUI Select addressed by the data-testid on its TextField root.

        MUI spreads ``...other`` onto the **root** ``FormControl`` (label +
        input + helper text), not onto the ``[role='combobox']`` display div, so
        a click on the root's centre can land on the label or the helper text —
        a silent no-op, because the ``<p>`` is a descendant of the clicked root
        and Chrome therefore raises no interception. Resolve the combobox first.
        """
        self.open_select_in(f"[data-testid='{testid}']", f"select '{testid}'")

    def open_select_in(self, container: str, what: str) -> None:
        """Open the MUI Select inside *container*, or fail loudly.

        Fails loudly by design: a helper that reports success without having
        opened anything pushes the failure to a later, unrelated line (the
        option lookup) and hides the real cause.
        """
        trigger: WebElement | None = None
        for sub in self.SELECT_TRIGGER_SUBSELECTORS:
            locator = (By.CSS_SELECTOR, f"{container} {sub}")
            if self.driver.find_elements(*locator):
                trigger = self.wait_for_element_clickable(locator)
                break
        if trigger is None:
            raise AssertionError(f"Select trigger for {what} not found")

        self.scroll_and_click(trigger)
        if self._wait_until_select_open(trigger):
            self._settle_listbox()
            return
        # The click did not open the menu (e.g. it was swallowed while the
        # trigger was still moving). Retry with the explicit mousedown pair.
        self.dispatch_menu_trigger_open(trigger)
        if self._wait_until_select_open(trigger):
            self._settle_listbox()
            return
        raise AssertionError(
            f"Select for {what} did not open (aria-expanded stayed "
            f"{self._aria_expanded(trigger)!r} and no li[role='option'] appeared)"
        )

    #: The Select display div of the dropdown that is currently open. Captured
    #: *before* the option click so the resulting value can be read back even
    #: when the caller gave no field name.
    OPEN_SELECT_TRIGGER = (
        By.CSS_SELECTOR,
        "[role='combobox'][aria-expanded='true'], .MuiSelect-select[aria-expanded='true']",
    )

    #: Reads the committed value of a MUI Select: its hidden
    #: ``.MuiSelect-nativeInput`` inside the same ``.MuiInputBase-root``.
    _SELECT_VALUE_FROM_TRIGGER = (
        "var el = arguments[0];"
        "var base = el.closest('.MuiInputBase-root') || el.parentElement;"
        "var input = base ? base.querySelector('input, select, textarea') : null;"
        "return input ? input.value : null;"
    )
    _SELECT_VALUE_FROM_CONTAINER = (
        "var root = document.querySelector(arguments[0]);"
        "if (!root) { return null; }"
        "var input = root.querySelector('input, select, textarea');"
        "return input ? input.value : null;"
    )

    def select_option_by_value(self, value: str, field_name: str | None = None) -> None:
        """Click an open dropdown option by its data-value and verify the effect.

        Waits briefly (bounded) for each candidate selector to become
        clickable rather than gating on an instant ``is_present`` check --
        the MUI popover open animation can still be in flight when this runs,
        so an unwaited check can miss an option that renders a beat later.

        The option is clicked via :meth:`click_menu_option` (a JS click on the
        already-resolved element), never at resolved coordinates: an open MUI
        menu still moves under its own layout effects, so a coordinate click
        lands on whichever option slid into that spot.

        Reads the resulting Select value back and raises on a mismatch. Without
        that, this helper returned unconditionally after *dispatching* a click,
        so a click that landed on a neighbouring option was reported as a
        success -- and the two-attempt retry in :meth:`choose_select_value` was
        inert, because nothing ever raised. The expectation is taken from the
        clicked option's own ``data-value``, not from *value*, because the option
        testid suffix and the value differ for the empty option
        (``form-option-<field>-none`` / ``-empty`` both commit ``''``).
        """
        trigger = next(iter(self.driver.find_elements(*self.OPEN_SELECT_TRIGGER)), None)
        selectors = []
        if field_name:
            selectors.append(f"[data-testid='form-option-{field_name}-{value}']")
        selectors.append(f"li[role='option'][data-value='{value}']")
        for selector in selectors:
            locator = (By.CSS_SELECTOR, selector)
            try:
                el = self.wait_for_element_clickable(locator, timeout=3)
            except TimeoutException:
                continue
            expected = el.get_attribute("data-value")
            self.click_menu_option(el)
            self.close_mui_dropdown()
            self._verify_select_committed(trigger, expected, value, field_name)
            return
        raise AssertionError(f"Option with value '{value}' not found in the open dropdown")

    def select_option_by_label(self, label: str) -> None:
        """Pick the open dropdown's option whose visible text matches *label*.

        For a MUI ``Select`` whose ``MenuItem``s carry an entity key as their
        value and a human-readable, translated string as their text (the species
        and family pickers of the companion-planting / crop-rotation dialogs).
        The label is resolved to the option's own ``data-value`` here and the
        actual selection then goes through :meth:`select_option_by_value`, so it
        inherits both guarantees the hand-rolled predecessors lacked: the click
        is dispatched on the resolved element (an open MUI popover still
        repositions, so a coordinate click lands on whichever option slid into
        the spot) and the committed value is read back.

        Matching is whitespace-normalised, because an option renders its label
        across two stacked ``Typography`` blocks (``"Name\\nGenus species"``) —
        which is also why an XPath ``contains(text(), …)`` could not see it: the
        XPath string-value carries no newline. An exact match wins over a
        substring match irrespective of DOM order, so a label that is the prefix
        of another entry cannot shadow the requested one.
        """
        target = " ".join(label.split())
        options = self.driver.find_elements(*self.OPTIONS)
        # ``textContent``, not ``.text``: WebElement.text yields only *rendered*
        # text, so an option scrolled outside the popover's visible area reads
        # back as "". MUI scrolls an open Select to its selected item, which
        # pushes the leading entries out of view -- observed on the tablet
        # profile as ``Rendered options: ['', '', 'Osmosewasser', ...]`` for a
        # dropdown whose first entry was the one being asked for.
        rendered = [" ".join((o.get_attribute("textContent") or "").split()) for o in options]
        exact = [o for o, text in zip(options, rendered) if text == target]
        partial = [
            o
            for o, text in zip(options, rendered)
            if text and text != target and (target in text or text in target)
        ]
        for option in exact + partial:
            value = option.get_attribute("data-value")
            if value is None:
                raise AssertionError(
                    f"The option matching '{label}' carries no data-value, so the "
                    "selection could not be verified. Address a MUI MenuItem "
                    "rendered inside a Select."
                )
            self.select_option_by_value(value)
            return
        raise AssertionError(
            f"No option matching '{label}' in the open dropdown. Rendered options: {rendered}"
        )

    def _read_select_value(self, trigger: WebElement | None, field_name: str | None) -> str | None:
        """Return the committed value of the Select that was just operated on.

        The trigger read is a staleness *verdict*: ``None`` here makes
        :meth:`_verify_select_committed` raise "cannot read back the value",
        which is the loud outcome the whole verify-the-click mechanism exists
        for. :func:`raw_reference` keeps it that way. A proxied trigger would
        instead be marshalled through the liveness probe in
        ``ReResolvingElement.id`` and re-resolve through
        :data:`OPEN_SELECT_TRIGGER` -- a locator that requires
        ``aria-expanded='true'``, i.e. a *still-open* dropdown, while this runs
        after the option click has closed it. So healing could only ever spend
        its 3 s budget and end in the same ``None``; stripping it keeps the
        failure as fast as it is loud.

        Today's only caller (:meth:`select_option_by_value`) resolves the trigger
        with ``find_elements`` and hands over a raw element, and #835 P4 decided
        that path stays unwrapped -- so this is a guard on the contract rather
        than on present behaviour. Exercised anyway by
        `tests/e2e_selftest/test_row_helpers.py`, which hands it a proxy.
        """
        if field_name:
            value = self.driver.execute_script(
                self._SELECT_VALUE_FROM_CONTAINER,
                f"[data-testid='form-field-{field_name}']",
            )
            if value is not None:
                return str(value)
        if trigger is None:
            return None
        try:
            value = self.driver.execute_script(
                self._SELECT_VALUE_FROM_TRIGGER, raw_reference(trigger)
            )
        except StaleElementReferenceException:
            return None
        return None if value is None else str(value)

    def _verify_select_committed(
        self,
        trigger: WebElement | None,
        expected: str | None,
        requested: str,
        field_name: str | None,
    ) -> None:
        """Raise unless the clicked option actually became the Select's value."""
        what = f"field '{field_name}'" if field_name else "the open select"
        if expected is None:
            raise AssertionError(
                f"The option clicked for {what} (requested '{requested}') carries "
                "no data-value, so the selection cannot be verified. Address a "
                "MUI MenuItem rendered inside a Select."
            )
        actual = self._read_select_value(trigger, field_name)
        if actual is None:
            raise AssertionError(
                f"Cannot read back the value of {what} after selecting "
                f"'{requested}': no native input was found for it. Verifying the "
                "click is mandatory — an unverified option click silently "
                "selects a neighbouring entry when the popover is still moving."
            )
        # Multi-selects commit a comma-joined list.
        if actual != expected and expected not in actual.split(","):
            raise AssertionError(
                f"Selecting '{requested}' on {what} did not take effect: expected "
                f"the value {expected!r}, but the field holds {actual!r}. The "
                "click most likely landed on a neighbouring option."
            )

    def choose_select_value(self, field_name: str, value: str) -> None:
        """Open a FormSelectField and pick the option with the given value.

        Retries once, re-opening the select, if the listbox never appeared or
        the option click didn't register on the first attempt -- a bounded
        guard against the MUI popover animation racing the option lookup
        (observed as a one-off timeout on an otherwise-passing code path,
        TC-006-J077). The retry spans the *open* too: ``open_select`` verifies
        the dropdown really opened and raises when it did not, and
        ``select_option_by_value`` verifies the clicked option really became
        the value -- so this retry only became reachable once those two started
        raising, rather than reporting success unconditionally.
        """
        from contextlib import suppress

        last_error: AssertionError | None = None
        for _attempt in range(2):
            try:
                self.open_select(field_name)
                self.select_option_by_value(value, field_name)
                return
            except AssertionError as exc:
                last_error = exc
                # Recovery only: a stuck popover here is a *symptom* of the
                # failure being carried in `last_error`, which is the one worth
                # reporting. `close_mui_dropdown` stays loud for every other
                # caller.
                with suppress(AssertionError):
                    self.close_mui_dropdown()
        assert last_error is not None
        raise last_error

    def get_row_cell_text(self, row: WebElement, col_id: str) -> str:
        """Return a DataTable row cell's text addressed by column id (not position).

        Resolves the *same* column id in both layouts: ``cell-<col_id>`` on the
        desktop table, else `MobileCard`'s ``card-field-<col_id>`` /
        ``card-chip-<col_id>``.

        Raises when the row demonstrably *is* a `MobileCard` (it carries a
        ``card-title``) but keys none of them: returning ``''`` there makes an
        assertion like "the supplemental column must be empty" pass without
        ever having read anything.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        if cells:
            return cells[0].text
        field = self.get_card_field(row, col_id)
        if field is not None:
            return field
        chips = row.find_elements(By.CSS_SELECTOR, f"[data-testid='card-chip-{col_id}']")
        if chips:
            return chips[0].text
        if row.find_elements(*self.CARD_TITLE):
            raise AssertionError(
                f"Column '{col_id}' is not readable on this MobileCard: it keys "
                f"neither 'card-field-{col_id}' nor 'card-chip-{col_id}'. Key the "
                "field/chip in the page's mobileCardRenderer, or read the column "
                "on a desktop-only test."
            )
        return ""

    # ── Layout-tolerant DataTable row access ──────────────────────────────
    # `DataTable` emits ``[data-testid='data-table-row']`` in BOTH layouts, but
    # only the desktop table renders ``<td data-testid='cell-<col_id>'>``. Below
    # the table's `mobileBreakpoint` it renders a `MobileCard` inside the same
    # row container. Position-based `cells[0]` access is doubly wrong there: it
    # yields `[]` on mobile, and on desktop it picks whatever column happens to
    # come first (a favourite star, a conditionally prepended chip column, ...)
    # rather than the identifying one.
    #
    # `MobileCard` now carries its own hooks (UI-NFR-022 R-016):
    #   ``card-title``            -- always present
    #   ``card-subtitle``         -- only when the caller sets a subtitle
    #   ``card-field-<col_id>``   -- only when the caller keys the field
    #   ``card-chip-<col_id>``    -- only when the caller keys the chip
    # The last two use exactly the `Column.id` of the column they mirror, so a
    # single key addresses the same value in both layouts (``cell-<id>`` on the
    # desktop table, ``card-field-<id>``/``card-chip-<id>`` on the card).

    DATA_TABLE_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")
    #: Container `DataTable` emits *only* in the mobile card layout.
    DATA_TABLE_CARDS = (By.CSS_SELECTOR, "[data-testid='data-table-cards']")

    def is_card_layout(self, section: str | None = None) -> bool:
        """Return True while a `DataTable` renders its mobile card layout.

        `DataTable` wraps the cards in ``[data-testid='data-table-cards']`` and
        renders that container in no other branch, so this is a durable signal
        -- no viewport arithmetic, no breakpoint duplication in the tests.

        Pass *section* on a page that renders more than one table (#778 C3).
        Without it the answer is page-global, while `DataTable` decides the
        layout **per instance**: a page with two tables where only one declares
        a ``mobileCardRenderer`` reports "card layout" for both, so a reader
        gated on it would skip a table that is in fact still a table. No current
        caller hits that shape, which is why this was latent rather than firing
        -- but the pages that grew a second table since (LocationDetail, TankDetail)
        make it reachable.

        Args:
            section: The ``data-table-section`` qualifier of one table
                (UI-NFR-022 §2.5.1). ``None`` keeps the page-global answer.
        """
        if section is None:
            return len(self.driver.find_elements(*self.DATA_TABLE_CARDS)) > 0
        scoped = (
            By.CSS_SELECTOR,
            f"[data-testid='data-table'][data-table-section='{section}'] "
            "[data-testid='data-table-cards']",
        )
        return len(self.driver.find_elements(*scoped)) > 0

    def require_table_layout(self, what: str) -> None:
        """Fail loudly when a column-position-based read is attempted on cards.

        Position-based readers (``cells[N]``) have no meaning in the card
        layout: `MobileCard` renders no ``<td>`` -- it addresses values by
        column id (``card-field-<id>`` / ``card-chip-<id>``), never by
        position -- so such a reader silently yields ``[]``/``""`` there, and
        an assertion like "the deleted entry is no longer listed" then passes
        for the wrong reason. Callers that genuinely need column positions must
        be desktop-only; this guard turns the silent pass into a hard failure.
        """
        if self.is_card_layout():
            raise AssertionError(
                f"{what} reads DataTable cells by column position, but the mobile "
                "card layout is active (no <td> cells). Use a layout-tolerant "
                "reader (get_row_primary_text / get_row_text_fragments) or mark "
                "the test 'requires_desktop'."
            )

    def get_row_text_fragments(self, row: WebElement) -> list[str]:
        """Return a row's readable text fragments in *both* layouts.

        Desktop: one entry per ``<td>``. Mobile card layout: one entry per
        rendered text line of the card, except that the card's title and
        subtitle are taken from their ``card-title``/``card-subtitle`` hooks
        via ``textContent`` -- `MobileCard` renders both ``noWrap``, so the
        *rendered* line drops the ellipsised tail of a long value (e.g. the
        ``— watering`` suffix of a care-reminder task name).

        Reading the remaining lines from the card's rendered text is deliberate
        and not a fallback: it is what keeps this reader complete for the many
        `MobileCard` callers that key no ``card-field-*``/``card-chip-*`` yet.
        Intended for membership assertions ("… is/is not listed").
        """
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells:
            return [c.text for c in cells]
        lines = [line.strip() for line in (row.text or "").splitlines() if line.strip()]
        exact = [
            self._text_content(els[0])
            for locator in (self.CARD_TITLE, self.CARD_SUBTITLE)
            if (els := row.find_elements(*locator))
        ]
        # `MobileCard` renders title and subtitle as the card's first text
        # lines (the optional `leading` slot carries a preview image, no text),
        # so the exact readings replace exactly those leading entries.
        return exact + lines[len(exact) :]

    def get_all_row_text_fragments(self) -> list[list[str]]:
        """Return :meth:`get_row_text_fragments` for every visible DataTable row.

        Re-read as a whole while the table moves (#835 P4), for the reason
        :meth:`get_column_texts` gives: this owns its row lookup *and* reads
        through every row it found, so a re-render mid-scan let a raw
        ``StaleElementReferenceException`` out of what callers use as a plain
        list assertion. Retrying the scan as a unit is also what keeps a partial
        list mixed from two renders from escaping as a legitimate-looking result.
        """
        return self.retry_on_stale(
            lambda: [
                self.get_row_text_fragments(row)
                for row in self.driver.find_elements(*self.DATA_TABLE_ROWS)
            ]
        )

    #: `MobileCard`'s own hooks. ``card-title`` is unconditional, so its
    #: absence means "this row renders no card" -- never "the title is
    #: missing". ``card-subtitle`` is emitted only when a subtitle is set.
    CARD_TITLE = (By.CSS_SELECTOR, "[data-testid='card-title']")
    CARD_SUBTITLE = (By.CSS_SELECTOR, "[data-testid='card-subtitle']")
    #: Any keyed card chip, used to tell an *unadopted* page (no keyed chips at
    #: all) apart from a row whose conditional chip simply is not rendered.
    CARD_ANY_CHIP = (By.CSS_SELECTOR, "[data-testid^='card-chip-']")

    @staticmethod
    def _text_content(element: WebElement) -> str:
        """Return an element's ``textContent``, not its rendered text.

        `MobileCard` renders title and subtitle as ``<Typography noWrap>``
        (``overflow: hidden; text-overflow: ellipsis``), so the tail of a long
        value — e.g. the ``— watering`` suffix of a care-reminder task name —
        is not part of the element's *rendered* text and ``WebElement.text``
        drops it. ``textContent`` carries the full string.
        """
        return (element.get_attribute("textContent") or "").strip()

    def get_card_title(self, row: WebElement) -> str:
        """Return the `MobileCard` title of *row*, or ``''`` outside the card layout."""
        els = row.find_elements(*self.CARD_TITLE)
        return self._text_content(els[0]) if els else ""

    def get_card_subtitle(self, row: WebElement) -> str:
        """Return the `MobileCard` subtitle of *row*, or ``''`` if it has none."""
        els = row.find_elements(*self.CARD_SUBTITLE)
        return self._text_content(els[0]) if els else ""

    def get_card_field(self, row: WebElement, col_id: str) -> str | None:
        """Return the card's ``card-field-<col_id>`` value, or ``None`` if unkeyed.

        ``None`` is the "this caller has not keyed that field yet" signal and
        must be handled by the caller -- returning ``''`` would be
        indistinguishable from a field that is rendered but empty.
        """
        els = row.find_elements(By.CSS_SELECTOR, f"[data-testid='card-field-{col_id}']")
        return self._text_content(els[0]) if els else None

    def get_row_chip_texts(self, row: WebElement) -> list[str]:
        """Return the labels of a row's *keyed* chips, in DOM order.

        Only keyed chips (``card-chip-<col_id>``) count: the previous
        ``.MuiChip-label`` sweep returned every chip of the row, including
        those a caller renders outside the chip slot, so an index into the
        result addressed a different chip per page and per row. Use
        :meth:`get_column_chip_texts` when the column is known -- it is exact.
        """
        return [c.text for c in row.find_elements(*self.CARD_ANY_CHIP)]

    #: MUI Chip palette suffixes, in the order they are probed.
    CHIP_COLORS = ("success", "warning", "error", "info", "secondary", "primary", "default")

    def _column_chip_scopes(self, row: WebElement, col_id: str) -> list[WebElement]:
        """Return the elements holding column *col_id*'s chip(s) in either layout.

        Desktop: the ``cell-<col_id>`` ``<td>``. Card layout: the keyed chip
        ``card-chip-<col_id>`` -- which `MobileCard` clones the hook straight
        onto, so the returned element *is* the Chip.

        Fails loudly when the row exposes neither hook: on the desktop table
        that means the column is not rendered at all, and in the card layout
        that the page's `MobileCard` caller has not keyed its chips yet. The
        previous behaviour -- falling back to *every* chip of the row --
        answered a question about column *A* with the chips of column *B*.

        A row that merely lacks this one conditional chip while carrying other
        keyed chips is a legitimate empty result, not a failure.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        if cells:
            return cells
        chips = row.find_elements(By.CSS_SELECTOR, f"[data-testid='card-chip-{col_id}']")
        if chips:
            return chips
        if not row.find_elements(*self.CARD_ANY_CHIP):
            raise AssertionError(
                f"Column '{col_id}' is not addressable on this row: it renders "
                f"neither a 'cell-{col_id}' <td> (desktop table) nor any keyed "
                "'card-chip-*' (mobile card layout). Either the column is not "
                "rendered at all, or the page's mobileCardRenderer still passes "
                "its chips as a plain node instead of a keyed { id, content } list."
            )
        return []

    CHIP_ROOT_CSS = ".MuiChip-root"

    def _chip_elements(self, scope: WebElement) -> list[WebElement]:
        """Return the Chips *scope* holds, or *scope* itself when it is one.

        `MobileCard` clones ``card-chip-<id>`` straight onto the Chip, so a
        card scope *is* the chip; a desktop ``cell-<id>`` ``<td>`` wraps it.
        ``.MuiChip-root`` is used here only to separate chips from a cell's
        other content **inside an already hook-addressed scope** -- never to
        locate a column, which is what the removed fallbacks did.
        """
        if "MuiChip-root" in (scope.get_attribute("class") or ""):
            return [scope]
        return scope.find_elements(By.CSS_SELECTOR, self.CHIP_ROOT_CSS)

    def get_column_chip_texts(self, col_id: str) -> list[str]:
        """Return the chip labels of column *col_id*, across all visible rows.

        Re-read as a whole while the table moves (#835 P4) — see
        :meth:`get_all_row_text_fragments`. This one reaches *two* levels
        through the captured row (row -> chip scope -> chip), so it has the
        longest window of the three in which a re-render can kill the reference.
        """

        def _scan() -> list[str]:
            texts: list[str] = []
            for row in self.driver.find_elements(*self.DATA_TABLE_ROWS):
                for scope in self._column_chip_scopes(row, col_id):
                    texts.extend(c.text for c in self._chip_elements(scope))
            return texts

        return self.retry_on_stale(_scan)

    def get_column_chip_colors(self, col_id: str) -> list[str]:
        """Return the MUI palette name of column *col_id*'s chips, across all rows.

        The palette is only ever expressed as MUI's ``MuiChip-color<Palette>``
        class -- there is no product hook for a chip's colour -- so this reads
        the class by design. What it no longer does is *find* the chip by
        class: the scope comes from ``cell-<col_id>`` / ``card-chip-<col_id>``.

        Re-read as a whole while the table moves (#835 P4) — see
        :meth:`get_column_chip_texts`, whose scan shape this shares exactly.
        """

        def _scan() -> list[str]:
            colors: list[str] = []
            for row in self.driver.find_elements(*self.DATA_TABLE_ROWS):
                for scope in self._column_chip_scopes(row, col_id):
                    colors.extend(self._chip_colors(self._chip_elements(scope)))
            return colors

        return self.retry_on_stale(_scan)

    def _chip_colors(self, chips: list[WebElement]) -> list[str]:
        """Map each Chip onto its MUI palette name (``MuiChip-colorSuccess`` -> ``success``)."""
        colors: list[str] = []
        for chip in chips:
            cls = chip.get_attribute("class") or ""
            colors.append(
                next(
                    (c for c in self.CHIP_COLORS if f"MuiChip-color{c.capitalize()}" in cls),
                    "default",
                )
            )
        return colors

    def get_row_chip_colors(self, row: WebElement) -> list[str]:
        """Return the MUI palette name of each chip in a row, in DOM order."""
        return self._chip_colors(self._chip_elements(row))

    def get_row_primary_text(self, row: WebElement, col_id: str) -> str:
        """Return a row's identifying text, addressed by column id in both layouts.

        Reads ``[data-testid='cell-<col_id>']`` when the desktop table is
        rendered, otherwise the column's ``card-field-<col_id>`` and finally
        the card's ``card-title`` -- fed from the same field the identifying
        column renders on every page using this helper. The card title is
        addressed by its hook rather than as "the first text line", which
        happened to work only as long as no `leading`/`trailing` slot carried
        text.

        Fails loudly in the card layout when the row exposes no ``card-title``
        at all: that is a `MobileCard` that did not render, and returning
        ``''`` there turns "the deleted entry is gone" into a pass for the
        wrong reason.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        if cells:
            return cells[0].text
        field = self.get_card_field(row, col_id)
        if field is not None:
            return field
        titles = row.find_elements(*self.CARD_TITLE)
        if not titles:
            raise AssertionError(
                f"Row exposes neither a 'cell-{col_id}' <td> nor a 'card-field-"
                f"{col_id}' nor a 'card-title' -- it renders no readable "
                "identifier in either layout."
            )
        return self._text_content(titles[0])

    def require_row_primary_text(self, row: WebElement, col_id: str) -> str:
        """:meth:`get_row_primary_text`, with an unreadable row as a *transient*.

        The reader to use inside anything wrapped in :meth:`retry_on_stale`. A
        row that renders none of its three identifying hooks is either mid-render
        or wrongly addressed, and at one instant those are the same observation
        (see :class:`TableNotSettled`); raising a retryable exception lets the
        enclosing retry tell them apart by outliving the first. Without it the
        ``AssertionError`` walks straight out through ``retry_on_stale``, which
        catches only staleness -- measured as a hard failure in both
        :meth:`get_column_texts` and :meth:`click_data_table_row`.

        The original assertion's message is carried verbatim and kept as
        ``__cause__``, so the diagnosis that survives the retry budget is the
        specific one ("this row exposes neither 'cell-x' nor ...") rather than a
        generic timeout.
        """
        try:
            return self.get_row_primary_text(row, col_id)
        except AssertionError as exc:
            raise TableNotSettled(
                f"{exc} Either the table is mid-render -- in which case the "
                "enclosing retry will re-read it -- or the column id is wrong "
                "for this table, in which case this message repeats until the "
                "retry budget is out and is then the answer."
            ) from exc

    def row_primary_text_or_none(self, row: WebElement, col_id: str) -> str | None:
        """*row*'s identifying text, or ``None`` while it is unreadable.

        The sampling form, for a predicate that is polled: ``None`` means "this
        row cannot be compared *yet*", covering both the row that went stale and
        the row that is mid-render. Unreadable is not "different" -- treating it
        as a mismatch is what made :meth:`click_data_table_row` reject a row that
        was still there and merely further along (#835).
        """
        try:
            return self.require_row_primary_text(row, col_id)
        except StaleElementReferenceException:
            # Includes `TableNotSettled`, which is the mid-render half.
            return None

    def get_column_texts(self, col_id: str) -> list[str]:
        """Return the identifying text of every visible DataTable row.

        Re-read as a whole while the table moves: a partial list mixed from two
        renders would be worse than a retry, because it reads as a legitimate
        result. That covers a row that went stale *and* -- since #835 P4, via
        :meth:`require_row_primary_text` -- a row that is in the DOM but has not
        rendered its cell yet, which used to escape as an ``AssertionError``.

        An unreadable row is never answered with ``''``: an empty string is
        indistinguishable from a legitimately blank cell, and would turn "the
        deleted entry is gone" into a pass for the wrong reason.
        """
        return self.retry_on_stale(
            lambda: [
                self.require_row_primary_text(row, col_id)
                for row in self.driver.find_elements(*self.DATA_TABLE_ROWS)
            ]
        )

    def find_row_by_text(self, needle: str) -> WebElement | None:
        """Return the first DataTable row whose rendered text contains *needle*.

        Layout-tolerant: matches against the row/card text rather than against
        a positional cell, so it behaves identically for the desktop table and
        the mobile card list.

        Reading ``.text`` off a captured row is itself a capture-then-use, so the
        scan is retried as a whole rather than returning ``None`` — "no such row"
        and "the table re-rendered mid-scan" must not collapse into one answer.

        **The retry covers the scan, not the use.** The row handed back is a raw
        reference to the render that was live when the scan ended, so a caller
        that keeps it across a re-render holds a dead one and no mechanism here
        can help -- ``retry_on_stale`` re-runs an action, and the action is over.
        A caller that needs to *act* on the row wants
        :meth:`click_data_table_row`, which keeps the lookup and the use inside
        one retryable unit and re-finds by identity. This helper currently has no
        call sites at all (checked across `tests/e2e/`, #835 P4), so the caveat
        is a warning to the next caller rather than a live defect.
        """

        def _scan() -> WebElement | None:
            for row in self.driver.find_elements(*self.DATA_TABLE_ROWS):
                if needle in (row.text or ""):
                    return row
            return None

        return self.retry_on_stale(_scan)

    # ── Truthful post-search settling ─────────────────────────────────────
    # A `DataTable`'s search is **client-side**, behind a 300 ms input debounce
    # (`DataTable.tsx`: `useDebounce(searchInput, 300)` feeding
    # `tableState.setSearch`). Nothing is fetched, so no `loading-skeleton` ever
    # mounts -- and `wait_for_loading_complete()`, which every search call site
    # paired with the search, is therefore satisfied *immediately*, while the
    # table still renders the previous, unfiltered rows. It is the
    # unfalsifiable-absence poll its own docstring warns about, standing exactly
    # where the strongest statement was needed.
    #
    # #835 measured the consequence. `provision_plant` searched for its own
    # unique instance id, read `get_row_count()` off the still-unfiltered table
    # and clicked row 0 -- the globally-first plant, a *stranger's* record. 19 of
    # the 34 `--profile light` failures of run 31113673507 were that one gap, in
    # two shapes: a `TimeoutException` out of `click_data_table_row` when the
    # filter landed mid-click (the identity read before the click no longer
    # exists after it), and `provision_plant`'s identity guard catching a
    # foreign detail page when it landed just after. The driver-level implicit
    # wait had been papering over it by delaying every lookup by up to 3 s,
    # which was usually enough for the debounce to have fired first.
    #
    # The two waits below are the truthful replacements, and they are ordered:
    # the chip proves the *filter* reached the table, the identity proves the
    # *row* is the caller's. Neither can be satisfied by the state the table is
    # leaving, which is the property `wait_for_loading_complete` lacked.

    #: `DataTable`'s search chip. Rendered exactly when `tableState.search` is
    #: non-empty -- i.e. in the first commit *after* the debounce propagated,
    #: which is the same commit that recomputes the filtered `processedData`.
    #: That coincidence is what makes the chip a statement about the rendered
    #: **rows** rather than merely about the input box, whose value changes one
    #: debounce earlier and therefore proves nothing.
    SEARCH_CHIP = (By.CSS_SELECTOR, "[data-testid='search-chip']")

    def wait_for_search_applied(
        self, term: str, what: str = "DataTable", timeout: int = DEFAULT_TIMEOUT
    ) -> None:
        """Wait until the table has re-rendered *filtered by* ``term``.

        The post-condition of a `DataTable` search, and the one
        :meth:`wait_for_loading_complete` cannot express (see the section
        comment above). Keyed on the presence of the search chip carrying the
        term, so it cannot be true before the filter exists.

        Matches on the quoted term inside the chip's text because the chip reads
        ``<i18n label>: "<term>"`` -- the label is translated, the quoted term is
        not, so this stays locale-independent.
        """
        needle = f'"{term}"'

        def _applied(driver: WebDriver) -> bool:
            return any(
                needle in (chip.get_attribute("textContent") or "")
                for chip in driver.find_elements(*self.SEARCH_CHIP)
            )

        try:
            self.poll(timeout).until(_applied)
        except TimeoutException as exc:
            chips = [
                (chip.get_attribute("textContent") or "").strip()
                for chip in self.driver.find_elements(*self.SEARCH_CHIP)
            ]
            mechanism = (
                "No search chip is rendered at all, so `tableState.search` is "
                "still empty: the term never arrived in the input, or this "
                "table renders no searchable toolbar and must not be searched."
                if not chips
                else f"The rendered chip(s) read {chips!r}, so the table is "
                "filtered by a *different* term. A React-controlled search box "
                "keeps its previous value when `WebElement.clear()` is used "
                "instead of `clear_and_fill`, and the new term is appended."
            )
            raise AssertionError(
                f"{what}: the search for {term!r} never reached the table within "
                f"{timeout}s. {mechanism} Reading rows here would read the "
                "*unfiltered* table and act on whatever record happens to sort "
                "first."
            ) from exc

    def wait_for_row_identity(
        self,
        index: int,
        col_id: str,
        expected: str,
        rows_locator: Locator | None = None,
        what: str = "DataTable row",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Wait until the row at *index* identifies as *expected*.

        The check that makes an index-based row click sound: an index only means
        anything relative to one render, so before capturing ``rows[index]`` a
        caller that knows *which* record it wants must confirm the render it is
        indexing into is the one it expects. :meth:`click_data_table_row`
        protects the click by re-finding the row by identity, but it can only
        protect the identity it was handed -- if that first read already came off
        the wrong render, the guard faithfully defends the wrong row.

        Matching is containment, not equality, because the identifying text is
        read through :meth:`get_row_primary_text`, whose mobile fallback is the
        card *title*. For the unique, per-run ids this is used with, containment
        is exactly as falsifiable as equality: no other record's identifier can
        contain them.

        An unreadable row counts as "not yet", never as a mismatch -- see
        :meth:`row_primary_text_or_none`.
        """
        locator = rows_locator or self.DATA_TABLE_ROWS

        def _matches(driver: WebDriver) -> bool:
            rows = driver.find_elements(*locator)
            if not 0 <= index < len(rows):
                return False
            text = self.row_primary_text_or_none(rows[index], col_id)
            return text is not None and expected in text

        try:
            self.poll(timeout).until(_matches)
        except TimeoutException as exc:
            rows = self.driver.find_elements(*locator)
            found = [self.row_primary_text_or_none(row, col_id) for row in rows]
            if not rows:
                mechanism = (
                    "The table renders no rows at all, so either the record was "
                    "never created, or the filter in force excludes it."
                )
            elif not 0 <= index < len(rows):
                mechanism = (
                    f"Only {len(rows)} row(s) are rendered, so index {index} does "
                    "not exist in this render."
                )
            elif any(text is not None and expected in text for text in found):
                at = next(i for i, text in enumerate(found) if text and expected in text)
                mechanism = (
                    f"The expected record is rendered, but at index {at}, not "
                    f"{index}. The table is sorted or filtered differently from "
                    "what the caller assumed."
                )
            else:
                mechanism = (
                    f"Row {index} identifies as {found[index]!r}. The table is "
                    "showing a render that does not contain the expected record "
                    "-- typically the previous, unfiltered one, because the "
                    "search has not been applied yet."
                )
            raise AssertionError(
                f"{what}: row {index} never identified as {expected!r} within "
                f"{timeout}s. Column {col_id!r} of the {len(rows)} rendered "
                f"row(s) reads {found!r}. {mechanism} Clicking here would "
                "activate a different record and every assertion after it would "
                "be about that one."
            ) from exc

    # ── Guarded row/card activation ───────────────────────────────────────
    # Two defects that kept re-entering the suite as per-page copies:
    #
    #   1. ``self.scroll_and_click(rows[index])`` clicks the row's *geometric
    #      centre*. A `DataTable` row is a click target as a whole, but its
    #      cells routinely contain their own interactive nodes -- a plant chip
    #      rendered as a `RouterLink`, a favourite `IconButton`, an actions
    #      menu -- and every one of them calls ``e.stopPropagation()``, so the
    #      row's own ``onRowClick`` never fires. Whether the centre lands on
    #      such a node is pure geometry: at 1920px the row is wide enough that
    #      it misses, at 820px it hits. Observed on the tablet profile as
    #      TC-REQ-004-J090 landing on the *plant* detail page instead of the
    #      watering-log detail (run ``20260725_173409``) -- the click did
    #      navigate, just to the chip's target.
    #   2. ``if index < len(rows): ...`` with no ``else`` turns an out-of-range
    #      index into a silent no-op that reports success; the assertion that
    #      follows then tests the page the test never left.
    #
    # Both are fixed once, here: address the row through one named, inert
    # column, and fail loudly on an index that does not exist.

    def require_index(self, items: list[WebElement], index: int, what: str) -> WebElement:
        """Return ``items[index]``, or fail loudly naming index and count.

        The loud failure is the point: a guarded interaction that quietly does
        nothing when the index is out of range cannot fail, so the assertion
        after it silently asserts against the previous page.
        """
        if not 0 <= index < len(items):
            raise AssertionError(
                f"{what}: index {index} is out of range -- {len(items)} "
                "element(s) are rendered. Doing nothing here would report "
                "success and leave the following assertion testing the page "
                "the test never left."
            )
        return items[index]

    #: Descendants that swallow a row click. `DataTable` puts ``onRowClick`` on
    #: the row, but a link/button inside a cell handles the click first and
    #: (in every current caller) calls ``stopPropagation``, so the row handler
    #: never runs. A cell containing one of these is not a usable click target.
    ROW_CLICK_SWALLOWERS = (
        "a[href], button, [role='button'], [role='link'], "
        "input, select, textarea, .MuiChip-clickable"
    )

    def _swallows_row_click(self, element: WebElement) -> bool:
        """Return True if *element* is, or contains, a row-click swallower."""
        return bool(
            self.driver.execute_script(
                "var el = arguments[0], sel = arguments[1];"
                "return el.matches(sel) || el.querySelector(sel) !== null;",
                element,
                self.ROW_CLICK_SWALLOWERS,
            )
        )

    def resolve_row_click_target(self, row: WebElement, col_id: str) -> WebElement:
        """Return the inert element through which *row* is activated.

        Resolves the *same* column id in both layouts, exactly as
        :meth:`get_row_primary_text` does its reading: ``cell-<col_id>`` on the
        desktop table, else `MobileCard`'s ``card-field-<col_id>``, else the
        card's unconditional ``card-title``. The click then bubbles to the
        row's own ``onRowClick`` from a point that is not a function of the
        viewport width.

        Fails loudly rather than falling back to the row element, on all three
        conditions that would otherwise reintroduce the geometry bet:

        * the column is not rendered at all (wrong column id for this table),
        * it is rendered but not displayed (a ``hideBelowBreakpoint`` column at
          a narrow viewport -- a JS click would still *fire* on a
          ``display: none`` ``<td>`` and report success, which is exactly the
          unsound-fallback class `e2e-test-stability` §G forbids),
        * it contains an interactive node, i.e. the caller picked a column that
          swallows the row click on some rows.
        """
        cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='cell-{col_id}']")
        source = f"cell-{col_id}"
        if not cells:
            cells = row.find_elements(By.CSS_SELECTOR, f"[data-testid='card-field-{col_id}']")
            source = f"card-field-{col_id}"
        if not cells:
            cells = row.find_elements(*self.CARD_TITLE)
            source = "card-title"
        if not cells:
            raise AssertionError(
                f"Row exposes neither a 'cell-{col_id}' <td> (desktop table) "
                f"nor a 'card-field-{col_id}' nor a 'card-title' (mobile card "
                "layout), so there is no column-addressed click target. Name a "
                "column this table actually renders."
            )
        target = next((c for c in cells if c.is_displayed()), None)
        if target is None:
            raise AssertionError(
                f"The click target '{source}' exists but is not displayed. "
                "Most likely the column carries `hideBelowBreakpoint` and this "
                "viewport hides it; pick a column rendered at every breakpoint."
            )
        if self._swallows_row_click(target):
            raise AssertionError(
                f"The click target '{source}' is, or contains, an interactive "
                "node (link, button or clickable chip). Those call "
                "stopPropagation, so the row's own onRowClick would never "
                "fire -- pick a column that renders inert content."
            )
        return target

    def click_row_via_column(self, row: WebElement, col_id: str) -> None:
        """Activate *row* by clicking its inert *col_id* cell.

        Use instead of clicking the row element: see the section comment above
        for why the row's geometric centre is a viewport-dependent bet.

        `scroll_and_click`'s JS fallback is sound for this target class. The
        resolved cell/field has no default activation behaviour of its own --
        the only thing that must happen is that a bubbling ``click`` reaches
        the row's React ``onRowClick``, which ``HTMLElement.click()`` produces
        exactly as a pointer does. It matters in the card layout, where a
        ``noWrap`` title can render wider than its clipping parent and the
        native click point can therefore fall outside it; Chrome then raises
        `ElementClickInterceptedException` and the fallback dispatches on the
        already-resolved element instead of guessing at coordinates.
        """
        self.scroll_and_click(self.resolve_row_click_target(row, col_id))

    def click_data_table_row(
        self,
        index: int,
        col_id: str,
        rows_locator: tuple[str, str] | None = None,
        what: str = "DataTable row",
    ) -> None:
        """Activate the *index*-th `DataTable` row through its *col_id* cell.

        The lookup and the click are one retryable unit, because a re-rendering
        table makes a row captured from the previous render stale before the click
        resolves its cell.

        **The retry re-selects by row identity, never by index again.** An index
        only means anything relative to one render: re-taking ``rows[index]``
        after a re-render is how an index-based click silently opens a *different*
        record. #835 measured exactly that — retrying by index turned a loud
        `StaleElementReferenceException` into four journey tests that opened the
        globally-first plant and then asserted against the one they meant to
        create. A wrong row that reads as success is worse than the exception it
        replaced, so failing to re-find the same row raises instead of falling
        back.

        Identity is the *identifying cell*, not ``row.text``. The full row text
        is not stable across renders — a row carries cells that fill in
        asynchronously (a last-watering date, a next-task chip render as ``—``
        first), so matching on it rejected rows that were still there and merely
        further along. #835 hit that too, one fix later.

        And the re-find *waits*. Mid-re-render the table briefly exposes no rows
        at all, so a first non-match means "not yet", not "gone" — raising on it
        immediately was the third thing #835 got wrong here.

        **What the guard does not cover, measured (#835 P4).** It protects the
        *click*, and it can only protect an identity it has already read. If the
        table re-renders during that very first read, ``identity`` is never
        assigned, the whole attempt is retried, and the index is resolved against
        the new render — so a re-render that *reorders* the rows in that window
        activates a different record. This is not a hole that can be closed here:
        before the first read there is no identity to re-find by, and the
        caller's ``index`` was itself derived from a render this method never
        saw. It is bounded to that one window and pinned as a test
        (`tests/e2e_selftest/test_row_helpers.py`) so the claim above is not read
        as covering more than it does.
        """
        locator = rows_locator or self.DATA_TABLE_ROWS
        identity: str | None = None

        def _click() -> None:
            nonlocal identity
            if identity is None:
                # First attempt: nothing has been clicked yet, so the index is
                # still the caller's own selection and safe to resolve.
                row = self.require_index(self.driver.find_elements(*locator), index, what)
                # `require_` and not the bare reader: a row that has not rendered
                # its cell yet must send us round the retry, not out of the
                # helper with an AssertionError.
                identity = self.require_row_primary_text(row, col_id)
            else:
                row = self.poll(IMPLICIT_WAIT_EQUIVALENT).until(
                    lambda d: next(
                        (
                            r
                            for r in d.find_elements(*locator)
                            if self.row_primary_text_or_none(r, col_id) == identity
                        ),
                        False,
                    ),
                    f"{what} identified by {identity!r} went stale mid-click and did not "
                    f"come back. Refusing to fall back to index {index}, which after a "
                    f"re-render would activate a different record.",
                )
            self.click_row_via_column(row, col_id)

        self.retry_on_stale(_click)

    def clear_and_fill(self, element: WebElement, value: str) -> None:
        """Reliably clear an input element and type a new value.

        Uses JavaScript to clear the field value and dispatch native input/change
        events so that React controlled components pick up the change.  After
        the JS clear, verifies the field is actually empty — if React restored
        the old value, falls back to Ctrl+A to select all before typing so
        the new value replaces whatever is in the field.
        """
        from selenium.webdriver.common.keys import Keys

        self.driver.execute_script(
            "var el = arguments[0];"
            "var proto = el.tagName === 'TEXTAREA'"
            "  ? window.HTMLTextAreaElement.prototype"
            "  : window.HTMLInputElement.prototype;"
            "var nativeInputValueSetter = Object.getOwnPropertyDescriptor(proto, 'value').set;"
            "nativeInputValueSetter.call(el, '');"
            "el.dispatchEvent(new Event('input', {bubbles: true}));"
            "el.dispatchEvent(new Event('change', {bubbles: true}));",
            element,
        )
        time.sleep(0.15)

        # Verify the field was actually cleared — React may have restored the
        # old value from state before send_keys runs.
        current = element.get_attribute("value") or ""
        if current:
            element.send_keys(Keys.CONTROL + "a")
            time.sleep(0.05)

        element.send_keys(value)

    # ── Sidebar navigation ─────────────────────────────────────────────────

    SIDEBAR_ROOT = (By.CSS_SELECTOR, "[data-testid='sidebar']")
    SIDEBAR_TOGGLE = (By.CSS_SELECTOR, "[data-testid='sidebar-toggle']")
    SIDEBAR_PAPER = (By.CSS_SELECTOR, "[data-testid='sidebar'] .MuiDrawer-paper")

    def is_sidebar_open(self) -> bool:
        """Return True if the sidebar drawer's paper is actually visible."""
        papers = self.driver.find_elements(*self.SIDEBAR_PAPER)
        return len(papers) > 0 and papers[0].is_displayed()

    def ensure_sidebar_open(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Open the sidebar drawer if it is closed, and wait until it is visible.

        Viewport-aware and idempotent. Below the `md` breakpoint (900px --
        i.e. BOTH the mobile and the tablet profile) the Sidebar renders as a
        *temporary* Drawer with ``ModalProps={{ keepMounted: true }}``, so its
        nav items stay in the DOM while the drawer is closed, merely hidden via
        ``visibility: hidden``. `uiSlice` seeds ``sidebarOpen`` from
        ``window.innerWidth >= 768``, so at 393px the drawer starts closed.

        Any assertion on nav-item *visibility* must therefore open the drawer
        first -- a presence-only wait on the sidebar stays green and masks the
        closed drawer. Returns immediately when the paper is already visible
        (desktop `persistent` variant, or the tablet width where the drawer
        starts open).

        No-ops when no sidebar is mounted at all (e.g. the login route, which
        renders outside `MainLayout`) -- "the sidebar is missing" is a distinct
        condition that the caller's own assertion reports.
        """
        if self.is_sidebar_open() or not self.is_present(self.SIDEBAR_ROOT):
            return
        toggle = self.wait_for_element_clickable(self.SIDEBAR_TOGGLE, timeout=timeout)
        self.scroll_and_click(toggle)
        self.poll(timeout).until(EC.visibility_of_element_located(self.SIDEBAR_PAPER))

    def navigate_via_sidebar(
        self, path: str, timeout: int = DEFAULT_TIMEOUT, *, strict: bool = False
    ) -> bool:
        """Navigate by clicking a sidebar link; return whether the link was used.

        The point of this helper is to exercise the *drawer* rather than the
        router, so the two conditions that used to divert it into a silent URL
        navigation are now handled instead of tripped over:

        * **The drawer was closed.** Below the `md` breakpoint the Sidebar is a
          `temporary` Drawer with ``keepMounted``, so its items are in the DOM
          but ``visibility: hidden``, and `uiSlice` seeds ``sidebarOpen`` from
          ``window.innerWidth >= 768``. Every mobile-profile call therefore took
          the fallback. :meth:`ensure_sidebar_open` is idempotent and no-ops when
          no sidebar is mounted at all.
        * **The item sat below the drawer's scroll fold.** Selenium reports
          ``is_displayed() == False`` for an element clipped by a scrollable
          ancestor, and the Sidebar's nav box is ``overflow: auto``, so a
          perfectly clickable item further down the list answered "not
          displayed" -- the suite stopped testing sidebar navigation and the test
          still passed. :meth:`is_displayed_in_scroll_container` scrolls first and
          so answers the question the caller is actually asking.

        A genuine miss (an item hidden by expertise level or module visibility)
        still falls back to URL navigation, because that is a legitimate reason
        for the link not to exist -- but it now *warns* instead of staying
        silent, and ``strict=True`` turns it into a failure for tests whose
        subject **is** the drawer.

        Note the behavioural consequence of actually clicking: on mobile and
        tablet a nav click also closes the temporary drawer, so a caller that
        asserts on drawer state afterwards must re-open it.
        """
        locator = (By.CSS_SELECTOR, f"[data-testid='nav-{path}']")
        self.ensure_sidebar_open(timeout=timeout)
        item = next(
            (
                i
                for i in self.driver.find_elements(*locator)
                if self.is_displayed_in_scroll_container(i)
            ),
            None,
        )
        if item is not None:
            self.scroll_and_click(item)
            self.poll(timeout).until(EC.url_contains(path))
            return True
        message = (
            f"Sidebar item 'nav-{path}' is not clickable (not rendered, or hidden "
            "by expertise level / module visibility), so this navigation went "
            "through the URL instead and exercised the router rather than the "
            "drawer."
        )
        if strict:
            raise AssertionError(message)
        warnings.warn(message, SidebarNavigationFallback, stacklevel=2)
        self.navigate(path)
        return False

    # ── Expertise level helpers ─────────────────────────────────────────────

    SHOW_ALL_FIELDS_TOGGLE = (By.CSS_SELECTOR, "[data-testid='show-all-fields-toggle']")

    def expand_all_fields(self, timeout: int = 5) -> None:
        """Click the 'Show all fields' toggle if present (for beginner mode)."""
        toggles = self.driver.find_elements(*self.SHOW_ALL_FIELDS_TOGGLE)
        if toggles and toggles[0].is_displayed():
            self.scroll_and_click(toggles[0])
            time.sleep(0.3)

    # ── Browser environment ───────────────────────────────────────────────

    def get_browser_today(self) -> tuple[int, int, int]:
        """Return today's ``(day, month, year)`` as the *browser* renders it (de-DE).

        Resolved inside the browser (``toLocaleDateString('de-DE')``) rather than
        from the test runner's ``datetime``: browser and runner can sit in
        different timezones in the containerised stack, and a date cell rendered
        by the frontend must be compared against the browser's own notion of
        today. Zero-padding is normalised away, so the result compares equal to a
        parsed cell value regardless of which formatter produced it.

        Raises ``ValueError`` if the browser returns something that is not a
        German ``d.m.Y`` date — that would mean the page ran under a different
        locale and any comparison against it would be meaningless.
        """
        rendered = self.driver.execute_script("return new Date().toLocaleDateString('de-DE');")
        match = DE_DATE_RE.search(rendered or "")
        if not match:
            raise ValueError(
                f"Browser did not return a German d.m.Y date for today (got {rendered!r})"
            )
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    # ── Screenshots ───────────────────────────────────────────────────────

    def take_screenshot(self, name: str, output_dir: Path) -> Path:
        """Save a PNG screenshot and return the file path."""
        filepath = output_dir / f"{name}.png"
        self.driver.save_screenshot(str(filepath))
        return filepath
