"""#1489 review (SCR-005) — the production care service is built WITH the family resolver.

``CareReminderService`` takes ``family_name_resolver`` as an optional keyword: some
thirty tests construct the service directly and requiring it there would be churn
without a defect behind it. But optional plus a ``None`` fallback is precisely the
#1042/#948 shape this repository keeps paying for — the collaborator that decides
the outcome, injected by exactly one caller, and nothing that notices when that one
caller stops injecting it.

The consequence is not an error: a service without the resolver resolves no family,
hands the engine ``None``, and every generated profile is ``TROPICAL`` again. That is
#1489 restored, wearing a different cause, with no failing test to show for it — the
profile it writes is well-formed.

So this guard reads the one production factory and requires the keyword to be there.
It is a structural check, not a behavioural one: the service's own unit tests cover
what the resolver *does*, and nothing there can notice that ``dependencies.py``
stopped passing it.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.support.execution_guards import find_project_root

_DEPENDENCIES = find_project_root(Path(__file__)) / "app" / "common" / "dependencies.py"

#: The factory that wires the production service, and the keyword it must pass.
_FACTORY = "get_care_reminder_service"
_CONSTRUCTOR = "CareReminderService"
_REQUIRED_KEYWORD = "family_name_resolver"


def keywords_of_construction(source: str, *, factory: str = _FACTORY) -> set[str] | None:
    """The keywords ``factory`` passes to ``CareReminderService(...)``.

    ``None`` when the factory does not construct one at all — which is itself a
    finding, and a different one from "constructs it without the resolver".
    """
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.FunctionDef) or node.name != factory:
            continue
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            func = call.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name == _CONSTRUCTOR:
                return {keyword.arg for keyword in call.keywords if keyword.arg}
    return None


class TestTheProductionServiceGetsTheResolver:
    def test_dependencies_passes_the_family_name_resolver(self) -> None:
        keywords = keywords_of_construction(_DEPENDENCIES.read_text(encoding="utf-8"))

        assert keywords is not None, f"{_FACTORY} no longer constructs a {_CONSTRUCTOR}"
        assert _REQUIRED_KEYWORD in keywords, (
            f"{_FACTORY} builds the care service without `{_REQUIRED_KEYWORD}`. It then resolves no "
            "botanical family, hands the engine None, and every generated care profile is TROPICAL "
            "again — #1489, with no failing test to show for it (SCR-005)."
        )

    def test_the_factory_also_passes_the_repositories_the_resolution_needs(self) -> None:
        """The resolver alone is not enough: the plant and species repositories are
        how the service reaches the species whose family is resolved."""
        keywords = keywords_of_construction(_DEPENDENCIES.read_text(encoding="utf-8")) or set()

        assert {"plant_repo", "species_repo"} <= keywords


class TestTheScannerItself:
    """Both directions. A matcher that returned the keyword unconditionally would
    satisfy the guard above forever."""

    _WIRED = """
def get_care_reminder_service():
    return CareReminderService(
        repo(),
        Engine(),
        plant_repo=plants(),
        species_repo=species(),
        family_name_resolver=get_family_name_resolver(),
    )
"""

    _UNWIRED = """
def get_care_reminder_service():
    return CareReminderService(repo(), Engine(), plant_repo=plants(), species_repo=species())
"""

    _ABSENT = """
def get_care_reminder_service():
    return None
"""

    def test_a_wired_factory_reports_the_keyword(self) -> None:
        assert _REQUIRED_KEYWORD in (keywords_of_construction(self._WIRED) or set())

    def test_an_unwired_factory_does_not(self) -> None:
        keywords = keywords_of_construction(self._UNWIRED)

        assert keywords is not None
        assert _REQUIRED_KEYWORD not in keywords

    def test_a_factory_that_builds_nothing_is_distinguishable(self) -> None:
        assert keywords_of_construction(self._ABSENT) is None

    @pytest.mark.parametrize("factory", ["get_other_service"])
    def test_another_factory_is_not_read(self, factory: str) -> None:
        assert keywords_of_construction(self._WIRED, factory=factory) is None
