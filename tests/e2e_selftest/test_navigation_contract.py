"""The structural invariant behind #785: navigation is encapsulated, and waited.

``BasePage.navigate()`` returns as soon as the document has loaded, which for
this SPA means the app shell exists and nothing else -- the route's lazily
imported chunk and its first fetch are both still in flight. Every read that
follows a bare ``navigate()`` is therefore a race, and the pairing that used to
be written for it (``navigate()`` + ``wait_for_loading_complete()``) is the
non-assertion `e2e-test-stability` §D rules out: no skeleton has mounted yet, so
the absence poll is satisfied instantly.

The invariant, from #785's sweep:

    A ``navigate()`` call outside an ``open()``-shaped method is a review
    finding. Test modules navigate through a page object's ``open()``, or --
    where the target key is deliberately invalid and no ``open()`` accepts it --
    through ``navigate_direct(path, settled)``, which makes the settle locator a
    mandatory parameter.

This is a **ratchet**, not a clean gate: the tree still holds the sites listed in
`KNOWN_BARE_NAVIGATE`. The test fails when a *new* one appears and when a listed
one is fixed without being removed from the list, so the number can only go down.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

E2E = pathlib.Path(__file__).resolve().parents[1] / "e2e"

#: Page-object method names that legitimately own a ``navigate()`` call: the
#: encapsulated entry points. ``open`` and its variants are the contract;
#: ``navigate_direct`` is the sanctioned escape (it takes a mandatory settle
#: locator); the private ``_ensure_*`` helpers re-enter a wizard step.
NAVIGATING_METHOD_PREFIXES = ("open", "navigate", "_ensure_")

#: Test-module functions that still call ``navigate()`` directly. Every entry is
#: a real finding awaiting migration to ``navigate_direct(path, settled)``; the
#: majority are "deliberately invalid key shows an error" tests, whose negative
#: assertion is exactly the one an unwaited navigation cannot falsify.
#:
#: **Shrink only.** Removing an entry is the fix; adding one needs a reason that
#: does not exist yet.
KNOWN_BARE_NAVIGATE = {
    "test_req001_botanical_family_detail.py::test_detail_page_nonexistent_key_shows_error",
    "test_req001_error_handling.py::test_nonexistent_detail_page_shows_error",
    "test_req001_navigation.py::test_navigate_to_botanical_families",
    "test_req001_navigation.py::test_navigate_to_companion_planting",
    "test_req001_navigation.py::test_navigate_to_crop_rotation",
    "test_req001_navigation.py::test_navigate_to_species",
    "test_req001_navigation.py::test_nonexistent_route_shows_not_found",
    "test_req002_standorte.py::test_site_detail_unknown_key_shows_error",
    "test_req004_fertilizer.py::test_invalid_key_shows_error",
    "test_req013_planting_run.py::test_nonexistent_run_key_shows_error",
    "test_req014_tank.py::test_nonexistent_tank_key_shows_error",
    "test_req019_substrate.py::test_nonexistent_substrate_shows_error",
    "test_req020_onboarding_steps.py::test_completed_card_shows_restart_and_dashboard_buttons",
    "test_req020_onboarding_steps.py::test_restart_from_completed_card",
    "test_req021_experience_level.py::test_beginner_navigation_minimal",
    "test_req021_experience_level.py::test_expert_navigation_shows_all",
    "test_req021_experience_level.py::test_intermediate_navigation_adds_sections",
    "test_req021_experience_level.py::test_level_persists_after_page_reload",
    "test_req023_login.py::test_authenticated_redirect_from_login_to_dashboard",
    "test_req023_login.py::test_unauthenticated_redirect_to_login",
}


def _bare_navigate_sites(paths: list[pathlib.Path]) -> set[str]:
    """Return ``<file>::<function>`` for every ``…​.navigate(…)`` call found."""
    sites: set[str] = set()
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            if fn.name.startswith(NAVIGATING_METHOD_PREFIXES):
                continue
            for node in ast.walk(fn):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "navigate"
                ):
                    sites.add(f"{path.name}::{fn.name}")
    return sites


def test_the_suite_tree_is_readable() -> None:
    """Guard the guard: an empty glob would make every assertion below vacuous."""
    assert len(list(E2E.glob("test_req*.py"))) > 50
    assert (E2E / "pages" / "base_page.py").is_file()


class TestNavigateIsEncapsulated:
    def test_no_new_bare_navigate_in_a_test_module(self) -> None:
        modules = sorted(E2E.glob("test_req*.py")) + sorted(E2E.glob("_*.py"))
        new = _bare_navigate_sites(modules) - KNOWN_BARE_NAVIGATE
        assert not new, (
            "New bare `navigate()` call(s) in a test module: "
            f"{sorted(new)}. A `navigate()` returns once the document is loaded, "
            "which for this SPA is before the route's chunk and first fetch have "
            "resolved -- so the read that follows is a race. Navigate through the "
            "page object's `open()`, or through `navigate_direct(path, settled)` "
            "when the key is deliberately invalid."
        )

    def test_the_allowlist_has_no_stale_entries(self) -> None:
        """A fixed site must leave the list, so the ratchet cannot rust shut."""
        modules = sorted(E2E.glob("test_req*.py")) + sorted(E2E.glob("_*.py"))
        stale = KNOWN_BARE_NAVIGATE - _bare_navigate_sites(modules)
        assert not stale, (
            f"These sites no longer call `navigate()` directly: {sorted(stale)}. "
            "Remove them from KNOWN_BARE_NAVIGATE -- an allowlist that outlives "
            "its findings stops being a ratchet."
        )

    def test_page_objects_navigate_only_from_open_shaped_methods(self) -> None:
        offenders = _bare_navigate_sites(sorted(E2E.glob("pages/*.py")))
        assert not offenders, (
            "Page-object method(s) calling `navigate()` outside an "
            f"`open`/`navigate`/`_ensure_` entry point: {sorted(offenders)}."
        )


class TestNavigateDirectContract:
    def test_the_settle_locator_is_mandatory(self) -> None:
        """The parameter that makes the sanctioned escape sound.

        `navigate_direct` exists precisely for the routes no ``open()`` accepts;
        making *settled* optional would hand those tests back the unwaited
        navigation the invariant is about.
        """
        import inspect

        from tests.e2e.pages.base_page import BasePage

        settled = inspect.signature(BasePage.navigate_direct).parameters["settled"]
        assert settled.default is inspect.Parameter.empty

    @pytest.mark.parametrize("name", ["wait_for_settled", "wait_for_content", "require_branch"])
    def test_the_strong_waits_are_on_the_shared_base(self, name: str) -> None:
        """Interaction plumbing lives once, per `e2e-test-stability` §C."""
        from tests.e2e.pages.base_page import BasePage

        assert callable(getattr(BasePage, name))
