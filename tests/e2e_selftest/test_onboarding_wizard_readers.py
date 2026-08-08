"""Unit tests for the onboarding-wizard readers fixed in #946 wave 12.

## Scope

Wave 12 of the #946 absence-check campaign (`.audits/absence-check-campaign/plan.md`)
is the UNDETERMINED-bucket recon wave for `tests/e2e/pages/onboarding_wizard_page.py`
(44 readers, the largest single page-object in the whole `tests/e2e/pages/` tree). A
wizard is not one container: each step mounts its own content, some behind an async
fetch, some purely synchronous, so the campaign plan explicitly calls for per-step
rather than per-file classification.

Reading the frontend (`OnboardingWizard.tsx` + `steps/*.tsx`) against every reader's
call sites found exactly two live defects, both fixed in this wave:

1. **Step 2 (Starter Kit) — the vacuous-count/skip-gate shape.** `StarterKitStep`
   has no loading branch of its own (unlike `FavoriteSpeciesStep`'s spinner) -- it
   renders `kits.map(...)` directly. The wizard-level `loading` flag that looks like
   it should protect this is shared between `fetchOnboardingState` and
   `fetchStarterKits` (both flip it on `.pending`/`.fulfilled`, and both are
   dispatched together on mount), so `loading` can go false as soon as *either*
   settles -- the `STEP_KIT` container can mount with an empty `kits` array while the
   catalog fetch is still in flight. `get_kit_card_count()`/`has_kit()`/
   `kit_has_toxicity_warning()` read right after `advance_to_step_kit()` hit exactly
   this window; `has_kit("indoor-growzelt")` additionally gated a `pytest.skip(...)`
   in `test_req020_onboarding_steps.py` -- the literal shape the campaign plan cites
   as the paradigm case for this whole bucket. Fixed with
   `wait_for_kit_step_settled()`, anchored on *any* kit card rendering (kits are
   static seed data -- 11 entries in `starter_kits.yaml` -- never legitimately empty
   in this environment, unlike the favorites step's genuine no-results branch), wired
   into `advance_to_step_kit()`.
2. **The forbidden fixed-sleep anti-pattern, closed at the source rather than in the
   reader.** `is_experience_selected()` used to carry a bare `time.sleep(0.2)` to
   paper over the gap between a click returning and `ExperienceLevelStep`'s
   React commit landing (that step has no `data-selected` attribute the way the kit
   cards do, so there is no dedicated DOM signal). Rather than turning the *reader*
   into a wait -- which would be wrong, since half its call sites assert True and
   half assert False, and a directional wait cannot serve both -- the verification
   moved to `select_experience_level()`, which polls its own known-direction effect
   before returning (the same shape `click_favorite_tile` already uses in this file).
   `is_experience_selected()` itself stays a plain, immediate, bidirectional read.

Every other reader in the file was either already anchored by its call sites (the
favorites step's `wait_for_favorites_settled`, the kit-selection `is_kit_selected`'s
own `poll`), reads synchronous state with no fetch behind it (steps 1, 4, 5, 7 --
`SiteSetupStep`'s own fields, `PlantSelectionStep`, `SummaryStep`), or is dead code
with zero call sites anywhere under `tests/e2e/` (`get_existing_site_cards`,
`click_existing_site`, `is_new_site_selected`, `get_favorites_no_results_visible`,
`is_step_nutrient_plans_visible`) and was left untouched per this campaign's
"do not speculatively convert" rule. See the wave-12 PR description for the full
per-step breakdown.

## Why the driver is stubbed and nothing else is

Same technique and reason as `test_row_helpers.py` and prior waves' files: a
**real** `selenium.webdriver.remote.webdriver.WebDriver` runs over a fake command
executor, so `WebDriverWait`, `resolve_settled_branch`/`wait_for_any_present`, and
the real page objects all run unmodified. Only the wire is fake.

## The one command the shared stub genuinely cannot host

`StubConnection.execute()` raises `AssertionError("stub driver got an unmodelled
command")` for anything outside its documented shape list, *by design* -- unlike
an unmatched selector (which resolves to an empty, valid result), an unmodelled
W3C *command* is not something that degrades gracefully. `is_experience_selected`
is the one reader in this file that calls `value_of_css_property` (`Command.
GET_ELEMENT_VALUE_OF_CSS_PROPERTY`), which the shared stub does not implement at
all, so it cannot run through `test_row_helpers.Harness` even in principle -- not
a "compound selector" gap the way wave 9/10's unmatchable shapes were. Rather than
extend the shared stub (`test_row_helpers.py` is shared across parallel #946 waves
and is explicitly off-limits for edits, per every prior wave's own file), this
module defines `_CssAwareConnection`, a small local subclass adding exactly that
one command, used only by the tests in this file. Everything else (`FIND_ELEMENTS`,
`CLICK_ELEMENT`, `is_displayed`/`is_enabled` for `EC.element_to_be_clickable`,
`scrollIntoView`) is already modelled by the shared `StubConnection` and is
exercised unmodified.

## Why this is a *separate* file from `test_row_helpers.py` and prior waves' files

Per the wave-12 task brief, matching waves 7-10: `test_row_helpers.py` is shared
across parallel absence-check waves and edits to it collide, and each prior wave's
own file is a sibling PR's file for the same reason. This module imports the
`Harness`/`StubConnection`/`TableDom`/`_w3c_error` stub pieces from `test_row_helpers`
and adds no classes to it, and does not touch any other wave's file either.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` -- see `tests/e2e_selftest/README.md`.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import pytest
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver

from tests.e2e.pages.onboarding_wizard_page import OnboardingWizardPage

# The stub itself, not the fixture function -- see wave 7-10's own files for why
# this is a thin local fixture over the same stub rather than a reused fixture
# function (Ruff F811).
from .test_row_helpers import Harness, StubConnection, TableDom, _w3c_error


@pytest.fixture
def harness() -> Harness:
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


#: Slack applied to elapsed-time bounds, mirroring `test_row_helpers.BUDGET_SLACK`
#: and every prior wave's own copy of the same constant.
BUDGET_SLACK = 1.5

#: How many probes an anchor's poll must survive before the content is built,
#: mirroring wave 7-10's own `_render_after`.
PROBES = 3

#: Short enough that the loud-failure/no-hang cases below do not spend
#: `DEFAULT_TIMEOUT`, matching wave 9/10's `SETTLE_TIMEOUT`.
SETTLE_TIMEOUT = 2


def _render_after(harness: Harness, probes: int, build: Callable[[], None]) -> None:
    """Run *build* once the DOM has been probed `probes` times.

    Hooked on `find_elements`: `wait_for_kit_step_settled` polls
    `len(d.find_elements(*self.KIT_CARDS)) > 0` directly (not through
    `wait_for_any_present`'s branch-probe script), so a hook on `FIND_ELEMENTS`
    alone is sufficient here, unlike wave 10's `_render_after`.
    """
    seen: list[int] = []

    def hook(_params: dict[str, Any]) -> None:
        seen.append(1)
        if len(seen) == probes:
            build()

    harness.connection.before[Command.FIND_ELEMENTS] = hook


def _render_kits(harness: Harness, kit_ids: list[str]) -> None:
    for kit_id in kit_ids:
        harness.dom.render_dialog(f"kit-{kit_id}")


# ── 1. wait_for_kit_step_settled / get_kit_card_count / has_kit ─────────────


class TestKitStepSettled:
    """`StarterKitStep` has no loading branch, so `STEP_KIT` mounting proves
    nothing about whether `fetchStarterKits` has resolved -- see the module
    docstring for the full race. `wait_for_kit_step_settled` closes it by
    waiting for any `[data-testid^='kit-']` card, which
    `test_row_helpers._matches`' testid-prefix branch resolves directly.
    """

    def _page(self, harness: Harness) -> OnboardingWizardPage:
        return OnboardingWizardPage(harness.driver, "http://stub.invalid")

    def test_outlives_a_late_render_of_the_catalog(self, harness: Harness) -> None:
        """Regression pin for `test_kit_list_displays_cards`
        (`get_kit_card_count() >= 5` right after `advance_to_step_kit()`) and
        `test_zimmerpflanzen_shows_toxicity_warning`
        (`kit_has_toxicity_warning("zimmerpflanzen")` at the same point).
        """
        kit_ids = ["fensterbank-kraeuter", "zimmerpflanzen", "indoor-growzelt"]
        _render_after(harness, PROBES, lambda: _render_kits(harness, kit_ids))
        page = self._page(harness)

        page.wait_for_kit_step_settled(timeout=SETTLE_TIMEOUT)

        assert page.driver.find_elements(*page.KIT_CARDS), (
            "the anchor returned before the late-rendered kit catalog actually appeared"
        )
        assert page.get_kit_card_count() == len(kit_ids)

    def test_has_kit_true_once_settled(self, harness: Harness) -> None:
        """Regression pin for `test_growzelt_kit_shows_advanced_difficulty`'s
        `if not wizard.has_kit("indoor-growzelt"): pytest.skip(...)` -- the
        literal skip-gate-on-an-unanchored-read shape the campaign plan cites
        as this bucket's paradigm case (`.audits/absence-check-campaign/plan.md`
        section 2, `has_overdue_section` example, same shape on the kit-step
        side).
        """
        _render_after(harness, PROBES, lambda: _render_kits(harness, ["indoor-growzelt"]))
        page = self._page(harness)

        page.wait_for_kit_step_settled(timeout=SETTLE_TIMEOUT)

        assert page.has_kit("indoor-growzelt") is True

    def test_has_kit_reports_a_genuine_absence_once_settled(self, harness: Harness) -> None:
        """A kit id that is genuinely not in a settled catalog -- a real
        'not found', not a premature one. `has_kit` itself stays unwaited
        (matching `has_care_card`'s design): once the step has settled, an
        absent id must report False fast, not spend a budget hunting for it.
        """
        _render_after(harness, PROBES, lambda: _render_kits(harness, ["fensterbank-kraeuter"]))
        page = self._page(harness)
        page.wait_for_kit_step_settled(timeout=SETTLE_TIMEOUT)

        started = time.monotonic()
        assert page.has_kit("indoor-growzelt") is False
        assert time.monotonic() - started < 0.5

    def test_raises_loudly_and_does_not_hang_when_the_catalog_never_renders(
        self, harness: Harness
    ) -> None:
        """No fallback to an empty-but-successful read: kits are static seed
        data, never legitimately empty, so a catalog that never renders is a
        real regression and must fail loudly rather than let `get_kit_card_
        count()` report a silent `0` indistinguishable from "zero kits exist".
        """
        page = self._page(harness)
        started = time.monotonic()

        with pytest.raises(AssertionError, match="No starter-kit card rendered"):
            page.wait_for_kit_step_settled(timeout=SETTLE_TIMEOUT)

        assert time.monotonic() - started <= SETTLE_TIMEOUT + BUDGET_SLACK


# ── 2. select_experience_level / is_experience_selected ─────────────────────


class _CssAwareConnection(StubConnection):
    """`StubConnection` plus `GET_ELEMENT_VALUE_OF_CSS_PROPERTY`.

    Local to this file only -- see the module docstring for why this command
    cannot be added to the shared stub instead. Every other command is
    delegated to `StubConnection.execute()` unmodified.
    """

    def execute(self, command: str, params: dict[str, Any]) -> dict[str, Any]:
        if command != Command.GET_ELEMENT_VALUE_OF_CSS_PROPERTY:
            return super().execute(command, params)

        self.calls.append((command, params))
        hook = self.before.get(command)
        if hook is not None:
            hook(params)

        node = self.nodes.get(str(params["id"]))
        if node is None or not node.attached:
            return _w3c_error("stale element reference", f"{params['id']} is detached")
        css: dict[str, str] = getattr(node, "css", {})
        return {"value": css.get(params["propertyName"], "")}


def _css_harness() -> Harness:
    dom = TableDom()
    connection = _CssAwareConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


class TestSelectExperienceLevelVerifiesItsOwnEffect:
    """`select_experience_level`'s post-click poll replaces the fixed
    `time.sleep(0.2)` that used to live on `is_experience_selected` -- see the
    module docstring for why the wait belongs on the action (known direction)
    rather than on the reader (bidirectional call sites).
    """

    def test_outlives_a_late_border_commit(self) -> None:
        """A React commit landing after the click must still be observed --
        not papered over by a fixed sleep that could have been too short.
        Regression pin for `test_select_intermediate_shows_smart_home_toggle`
        (`select_experience_level("intermediate")` immediately followed by
        `assert wizard.is_experience_selected("intermediate")`).
        """
        harness = _css_harness()
        node = harness.dom.render_dialog("experience-intermediate")
        node.css = {}
        samples: dict[str, int] = {"n": 0}

        def _land_border(params: dict[str, Any]) -> None:
            if params.get("propertyName") != "border-width":
                return
            samples["n"] += 1
            if samples["n"] >= 3:
                node.css["border-width"] = "2px"

        harness.connection.before[Command.GET_ELEMENT_VALUE_OF_CSS_PROPERTY] = _land_border
        page = OnboardingWizardPage(harness.driver, "http://stub.invalid")

        page.select_experience_level("intermediate")  # must not raise

        assert samples["n"] >= 3, "the poll must have sampled the border more than once"
        assert page.is_experience_selected("intermediate") is True

    def test_raises_loudly_when_the_border_never_lands(self) -> None:
        """A click whose handler never ran (or whose re-render never landed)
        must fail loudly and by name, not silently leave the wizard one step
        behind what the test believes happened.
        """
        harness = _css_harness()
        node = harness.dom.render_dialog("experience-expert")
        node.css = {}  # never flips
        page = OnboardingWizardPage(harness.driver, "http://stub.invalid")

        with pytest.raises(AssertionError, match="had no visible effect"):
            page.select_experience_level("expert")


class TestIsExperienceSelectedStaysImmediateAndBidirectional:
    """The reader itself must not become a wait: half its call sites assert
    True (`test_select_intermediate_shows_smart_home_toggle`), half assert
    False (`assert not wizard.is_experience_selected("beginner")` in the same
    test, and the default-selection check in `test_beginner_is_default_
    selection`, which never clicks anything at all).
    """

    def test_reports_both_polarities_fast(self) -> None:
        harness = _css_harness()
        node = harness.dom.render_dialog("experience-beginner")
        node.css = {"border-width": "2px"}
        page = OnboardingWizardPage(harness.driver, "http://stub.invalid")

        started = time.monotonic()
        assert page.is_experience_selected("beginner") is True
        # No card rendered for "intermediate" at all -- a real absence, not a
        # premature one, and it must not block on it.
        assert page.is_experience_selected("intermediate") is False
        assert time.monotonic() - started < 1.0, (
            "is_experience_selected does not call any wait_for*/poll primitive -- "
            "an elapsed time anywhere near IMPLICIT_WAIT_EQUIVALENT would mean it "
            "regressed into blocking"
        )
