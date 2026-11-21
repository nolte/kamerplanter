"""E2E accessibility journey — axe-core against the composed app (#1095, UI-NFR-002).

Spec-TC Mapping (test TC -> spec/e2e-testcases/):
  TC-UINFR002-001  ->  spec/e2e-testcases/TC-UI-NFR-002.md  Composed-page axe pass across the core route
  TC-UINFR002-002  ->  spec/e2e-testcases/TC-UI-NFR-002.md  Negative control — a seeded violation is reported
  TC-UINFR002-003  ->  spec/e2e-testcases/TC-UI-NFR-002.md  Dark-mode axe pass across the main pages (#3047)

Why an E2E pass at all, next to the component-level `vitest-axe`: a component
test renders one component into a bare container, so it cannot see landmark
structure, heading order across a page, or the contrast between a component's
colour and the background an ancestor painted. Those exist only once the page is
assembled, which is what this journey walks.

WHAT MAKES THIS NOT VACUOUS
---------------------------
Two things, and both are the point rather than decoration:

* the helper RAISES whenever the scan could not be performed — missing bundle,
  CSP-blocked injection, `axe.run` throwing — so a journey that skipped its scan
  cannot report green (NFR-018 §2);
* TC-UINFR002-002 seeds a guaranteed WCAG failure and asserts the pass reports
  it. A scan never shown to fail is indistinguishable from one that cannot, and
  #1095's acceptance criteria ask for that control explicitly.

ADVISORY FOR NOW
----------------
Findings are asserted only on the seeded control; the real-page scan records
what it found and does not fail the run (see `_assert_no_new_violations`).
Promotion to blocking is a decision on measured history, per NFR-018 §4 — a
gate switched on before anyone knows its false-positive rate gets disabled
again, which is worse than starting advisory.

The dark-mode pass (TC-UINFR002-003, #3047) blocks on exactly one rule:
`color-contrast` at serious/critical impact — the criterion that is specific to
the dark theme and that jsdom cannot measure (it computes no colour contrast,
which left the dark theme entirely unmeasured until this pass; the static half
of the same check is `src/frontend/src/test/theme/darkSurfaceContrast.test.tsx`).
Every other serious/critical finding is reported as ADVISORY, exactly like the
light pass: rules such as `nested-interactive`, `link-name`, `button-name` or
the `aria-*` family do not depend on the colour scheme, have no measured
history here yet, and would otherwise turn a dark-mode gate red for a defect
the light pass reports only advisory.
"""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._a11y_helpers import (
    format_violations,
    run_axe,
    seed_contrast_violation,
    violations_json,
)
from ._journey_helpers import provision_plant, unique_suffix
from .pages.base_page import BasePage
from .pages.calendar_page import CalendarPage
from .pages.dashboard_page import DashboardPage
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.site_list_page import SiteListPage
from .pages.species_list_page import SpeciesListPage
from .pages.task_queue_page import TaskQueuePage

# Feature-axis marker(s) for machine-selectable test identification.
FEATURES = ("plant", "journey")

#: Rules whose violations are reported but do not fail the journey while the
#: pass is advisory. Empty on purpose: an allowlist added before any measurement
#: would encode today's defects as tomorrow's baseline.
KNOWN_ADVISORY_RULES: frozenset[str] = frozenset()

#: The localStorage key and value `ThemeContext.tsx` reads for a manual theme
#: pick. Seeded before the page loads, so the app starts dark instead of being
#: toggled mid-test (which would scan a frame still transitioning colours).
THEME_STORAGE_KEY = "kamerplanter-theme"
DARK_MODE = "dark"

#: `background.default` of the dark palette, as the browser reports the body
#: colour CssBaseline paints. The proof that the scan measured the dark theme.
DARK_BODY_BACKGROUND = "rgb(18, 18, 18)"

#: Impacts the dark pass reports at all (#3047 acceptance: no serious or critical).
BLOCKING_IMPACTS: frozenset[str] = frozenset({"serious", "critical"})

#: The only rules whose serious/critical findings fail the dark pass: the
#: dark-specific criterion of #3047. Everything else is advisory (module doc).
DARK_BLOCKING_RULES: frozenset[str] = frozenset({"color-contrast"})


@pytest.fixture
def plant_list(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    return PlantInstanceListPage(browser, base_url)


def _scan(browser: WebDriver, label: str) -> list[dict]:
    violations = run_axe(browser)
    print(f"[a11y] {label}: {len(violations)} violation(s) {violations_json(violations)}")
    return violations


def test_uinfr002_a01_composed_pages_are_scanned(
    browser: WebDriver, plant_list: PlantInstanceListPage
) -> None:
    """TC-UINFR002-001 — walk the core route and scan each composed page.

    Self-provisioning (NFR-008a §2): the plant this journey visits is created
    through the real UI, so the detail page always exists and the scan never
    degrades into "the list page twice".
    """
    suffix = unique_suffix()
    plant_list.open()
    scanned: dict[str, list[dict]] = {"plant-list": _scan(browser, "plant list")}

    _plant_key, instance_id = provision_plant(plant_list, id_prefix=f"A11Y{suffix}")
    scanned["plant-detail"] = _scan(browser, "plant detail")

    # The detail page is the one this journey adds over a bare landing-page scan,
    # so it has to be the page that was actually scanned. `provision_plant`
    # returns a tuple and never None, so an `is not None` check here would be
    # vacuous — the instance id being on screen is the property that is not.
    assert instance_id in browser.page_source, (
        f"expected to be scanning the detail page of {instance_id}; provisioning "
        "returned but the page does not show it, so the second scan measured something else"
    )
    assert set(scanned) == {"plant-list", "plant-detail"}

    reportable = {
        page: [v for v in violations if v.get("id") not in KNOWN_ADVISORY_RULES]
        for page, violations in scanned.items()
    }
    for page, violations in reportable.items():
        if violations:
            print(f"[a11y] ADVISORY — {page}:\n{format_violations(violations)}")


def test_uinfr002_a02_a_seeded_violation_is_reported(browser: WebDriver, base_url: str) -> None:
    """TC-UINFR002-002 — the negative control.

    Without this, a green journey would prove only that `run_axe` returned a
    list. The seeded element fails `color-contrast` (wcag2aa) by a wide margin
    and disappears on the next navigation, so it cannot leak into TC-UINFR002-001.
    """
    browser.get(base_url)
    before = run_axe(browser)
    pre_existing = [v for v in before if v.get("id") == "color-contrast"]
    assert not pre_existing, (
        "the landing page itself violates color-contrast, so this control can no longer "
        "tell the seeded failure apart from a pre-existing one. Read this as a product "
        "regression first — the page is what changed, not the control. Fix the page; "
        "only if the finding is genuinely unfixable does seeding a different rule become "
        f"the answer. Found:\n{format_violations(pre_existing)}"
    )

    seed_contrast_violation(browser)
    after = run_axe(browser)

    seeded = [v for v in after if v.get("id") == "color-contrast"]
    assert seeded, (
        "the seeded contrast failure was not reported — the axe pass cannot fail, "
        f"so a green TC-UINFR002-001 means nothing. Found: {format_violations(after)}"
    )
    targets = [t for v in seeded for n in v.get("nodes", []) for t in n.get("target", [])]
    assert any("a11y-negative-control" in t for t in targets), (
        f"color-contrast fired, but not on the seeded element: {targets}"
    )


#: The main pages of the dark pass: what a grower sees every day. Each opens
#: through its page object's ``open()`` and then waits for its own content
#: signal, so a scan never measures a skeleton: `open()` returns once the page
#: root mounted, which is before the first fetch resolved
#: (`site_list_page.py`, `wait_for_list_content`).
_DARK_PAGES: tuple[tuple[str, type[BasePage], str], ...] = (
    ("dashboard", DashboardPage, "wait_for_quick_actions_widget"),
    ("plant-list", PlantInstanceListPage, "wait_for_list_content"),
    ("species-list", SpeciesListPage, "wait_for_list_settled"),
    ("site-list", SiteListPage, "wait_for_sites_settled"),
    ("task-queue", TaskQueuePage, "wait_for_queue_content"),
    ("calendar", CalendarPage, "wait_for_month_settled"),
)


def _body_background(browser: WebDriver) -> str:
    return browser.execute_script("return getComputedStyle(document.body).backgroundColor;")


def test_uinfr002_a03_dark_mode_main_pages_have_no_serious_findings(
    browser: WebDriver, base_url: str
) -> None:
    """TC-UINFR002-003 — axe against the dark theme on the main pages (#3047).

    The theme is chosen the way a user's manual pick is stored, before the first
    page of the pass loads. Every page then has to *show* the dark theme (body
    background) before its scan counts — a pass that silently ran in light mode
    would report the light palette as dark-mode compliant.

    Blocking: serious/critical `color-contrast` only. Every other serious or
    critical finding is printed as ADVISORY, the way TC-UINFR002-001 does.
    """
    browser.get(base_url)
    browser.execute_script(
        "window.localStorage.setItem(arguments[0], arguments[1]);", THEME_STORAGE_KEY, DARK_MODE
    )

    blocking: dict[str, list[dict]] = {}
    advisory: dict[str, list[dict]] = {}
    for label, page_class, settle in _DARK_PAGES:
        page = page_class(browser, base_url)
        page.open()
        getattr(page, settle)()
        background = _body_background(browser)
        assert background == DARK_BODY_BACKGROUND, (
            f"{label}: the page is not in dark mode (body background {background}, expected "
            f"{DARK_BODY_BACKGROUND}) — the scan would measure the light theme. Did the "
            f"`{THEME_STORAGE_KEY}` key or the dark palette's background change?"
        )
        violations = _scan(browser, f"dark {label}")
        serious = [
            v
            for v in violations
            if v.get("impact") in BLOCKING_IMPACTS and v.get("id") not in KNOWN_ADVISORY_RULES
        ]
        found = [v for v in serious if v.get("id") in DARK_BLOCKING_RULES]
        rest = [v for v in serious if v.get("id") not in DARK_BLOCKING_RULES]
        if found:
            blocking[label] = found
        if rest:
            advisory[label] = rest

    for label, violations in advisory.items():
        print(f"[a11y] ADVISORY — dark {label}:\n{format_violations(violations)}")

    assert not blocking, "dark mode has serious/critical colour-contrast findings:\n" + "\n".join(
        f"{label}:\n{format_violations(violations)}" for label, violations in blocking.items()
    )
