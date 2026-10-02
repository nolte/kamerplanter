"""Page-object clicks wait for their effect instead of sleeping (#1902).

## What #1902 found

Three page-object clicks were followed by a fixed ``time.sleep`` and a return,
whatever had happened -- the spelling #1897 removed from ``expand_all_fields``:

* ``ExpertiseLevelPage.click_show_all_fields`` (``time.sleep(0.5)``);
* ``OnboardingWizardPage.click_kit`` (``time.sleep(0.5)``);
* ``OnboardingWizardPage._deselect_all_kits`` (``time.sleep(0.3)``, with a comment
  claiming "no distinct DOM signal" -- ``StarterKitStep`` renders ``data-selected``).

All three controls expose the effect as an attribute that flips in the commit that
changes the UI (``aria-expanded`` / ``data-selected``), so each click now reads the
state before, clicks, and waits for it to change. A click that never takes effect
fails **in the helper**, naming the state.

## What is pinned

* each helper returns once the state has flipped, however late the flip comes;
* each helper fails in itself when the click has no effect (the red case: the old
  code returned silently here);
* a static guard: no page object may follow a click with a fixed sleep within four
  lines, except the one allowlisted site that has its own reason.

Browser-free; the page methods that touch the wire are stubbed, the waiting is the
real ``WebDriverWait`` the page objects use.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.e2e.pages.expertise_level_page import ExpertiseLevelPage
from tests.e2e.pages.onboarding_wizard_page import OnboardingWizardPage


class _Node:
    """A control whose ``attr`` flips ``flip_after`` reads after the click."""

    def __init__(self, attr: str, value: str, *, flips: bool, flip_after: int = 0) -> None:
        self.attr = attr
        self.value = value
        self.flips = flips
        self.flip_after = flip_after
        self.clicked = False
        self.reads_since_click = 0

    def get_attribute(self, name: str) -> str | None:
        if name == "data-testid":
            return "kit-x"
        if name != self.attr:
            return None
        if self.clicked and self.flips:
            self.reads_since_click += 1
            if self.reads_since_click > self.flip_after:
                return "false" if self.value == "true" else "true"
        return self.value

    def is_displayed(self) -> bool:
        return True


class _Driver:
    def __init__(self, node: _Node) -> None:
        self.node = node

    def find_elements(self, _by: str, value: str) -> list[_Node]:
        if value == "[data-selected='true']":
            return [self.node] if self.node.get_attribute("data-selected") == "true" else []
        return [self.node]


def _click(node: _Node):
    def _do(_element: object) -> None:
        node.clicked = True

    return _do


def _expertise(node: _Node) -> ExpertiseLevelPage:
    page = ExpertiseLevelPage(_Driver(node), "http://app.invalid")  # type: ignore[arg-type]
    page.find_show_all_fields_button = lambda: node  # type: ignore[method-assign]
    page.scroll_and_click = _click(node)  # type: ignore[method-assign]
    return page


def _wizard(node: _Node) -> OnboardingWizardPage:
    page = OnboardingWizardPage(_Driver(node), "http://app.invalid")  # type: ignore[arg-type]
    page.wait_for_element_clickable = lambda _loc: node  # type: ignore[method-assign]
    page.scroll_and_click = _click(node)  # type: ignore[method-assign]
    return page


def test_show_all_fields_returns_once_aria_expanded_has_flipped_late() -> None:
    node = _Node("aria-expanded", "false", flips=True, flip_after=2)

    _expertise(node).click_show_all_fields(timeout=2)

    assert node.clicked


def test_show_all_fields_fails_in_the_helper_when_the_click_has_no_effect() -> None:
    node = _Node("aria-expanded", "false", flips=False)

    with pytest.raises(AssertionError, match="aria-expanded stayed 'false'"):
        _expertise(node).click_show_all_fields(timeout=1)


def test_show_all_fields_refuses_a_toggle_that_exposes_no_state() -> None:
    node = _Node("aria-expanded", "", flips=False)
    node.get_attribute = lambda _name: None  # type: ignore[method-assign]

    with pytest.raises(AssertionError, match="exposes no aria-expanded"):
        _expertise(node).click_show_all_fields(timeout=1)


@pytest.mark.parametrize("start", ["false", "true"])
def test_click_kit_waits_for_the_selection_to_flip_in_either_direction(start: str) -> None:
    node = _Node("data-selected", start, flips=True, flip_after=2)

    _wizard(node).click_kit("x", timeout=2)

    assert node.clicked


def test_click_kit_fails_in_the_helper_when_the_click_has_no_effect() -> None:
    node = _Node("data-selected", "false", flips=False)

    with pytest.raises(AssertionError, match="data-selected stayed 'false'"):
        _wizard(node).click_kit("x", timeout=1)


def test_deselect_all_kits_waits_for_each_card_to_report_unselected() -> None:
    node = _Node("data-selected", "true", flips=True, flip_after=2)

    _wizard(node)._deselect_all_kits()

    assert node.clicked


def test_deselect_all_kits_fails_when_a_card_stays_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node = _Node("data-selected", "true", flips=False)
    monkeypatch.setattr("tests.e2e.pages.onboarding_wizard_page.DEFAULT_TIMEOUT", 1)

    with pytest.raises(AssertionError, match="stayed selected"):
        _wizard(node)._deselect_all_kits()


# -- static guard ----------------------------------------------------------

PAGES = Path(__file__).resolve().parents[1] / "e2e" / "pages"
CLICK = re.compile(r"(\.click\(|_click\(|\bclick_\w+\()")
SLEEP = re.compile(r"\bsleep\(")

#: ``(file, text of the sleep line)`` of the clicks that may still be followed by a
#: fixed sleep, with the reason. Do not add to this list: wait for the effect.
ALLOWED: dict[tuple[str, str], str] = {
    ("pflege_dashboard_page.py", "time.sleep(0.3)"): (
        "select_care_style_no_escape: the click either opens a confirm dialog or does "
        "not; there is no positive signal for the second branch. Tracked as a follow-up."
    ),
}


def click_followed_by_sleep(window: int = 4) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for path in sorted(PAGES.glob("*.py")):
        lines = path.read_text().splitlines()
        for i, line in enumerate(lines):
            code = line.split("#", 1)[0]
            if not CLICK.search(code) or code.lstrip().startswith("def "):
                continue
            for j in range(i + 1, min(i + 1 + window, len(lines))):
                if SLEEP.search(lines[j].split("#", 1)[0]):
                    hits.append((path.name, j + 1, lines[j].split("#", 1)[0].strip()))
                    break
    return hits


def test_no_page_object_follows_a_click_with_a_fixed_sleep() -> None:
    offenders = [
        f"{name}:{lineno}: {text}"
        for name, lineno, text in click_followed_by_sleep()
        if (name, text) not in ALLOWED
    ]
    assert not offenders, (
        "A click followed by a fixed sleep is a bet, not a wait (#1902). Wait for the "
        "effect (an aria-*/data-* state, the next step's anchor):\n  " + "\n  ".join(offenders)
    )


def test_the_guard_still_sees_the_defect_it_exists_for() -> None:
    """The scan is not vacuous: run on the pre-fix spelling it reports the click."""
    src = ["    self.scroll_and_click(btn)", "    time.sleep(0.5)  # wait for React"]
    assert CLICK.search(src[0]) and SLEEP.search(src[1].split("#", 1)[0])
