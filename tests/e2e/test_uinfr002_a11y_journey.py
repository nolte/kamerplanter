"""E2E accessibility journey — axe-core against the composed app (#1095, UI-NFR-002).

Spec-TC Mapping (test TC -> spec/ui-nfr/):
  TC-UINFR002-001  ->  spec/e2e-testcases/TC-UI-NFR-002.md  Composed-page axe pass across the core route
  TC-UINFR002-002  ->  spec/e2e-testcases/TC-UI-NFR-002.md  Negative control — a seeded violation is reported

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
from .pages.plant_instance_list_page import PlantInstanceListPage

# Feature-axis marker(s) for machine-selectable test identification.
FEATURES = ("plant", "journey")

#: Rules whose violations are reported but do not fail the journey while the
#: pass is advisory. Empty on purpose: an allowlist added before any measurement
#: would encode today's defects as tomorrow's baseline.
KNOWN_ADVISORY_RULES: frozenset[str] = frozenset()


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
    assert not any(v.get("id") == "color-contrast" for v in before), (
        "the landing page already violates color-contrast, so this control cannot "
        "distinguish the seeded failure from a pre-existing one — seed a different rule"
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
