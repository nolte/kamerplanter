"""One reading of "bounded on both sides" for every guard that enforces NFR-009 §2.1.

Three guards ask the same question of a PEP 440 specifier — does it close the
range at the bottom AND at the top:

* ``tests/unit/guards/test_pre_commit_dependency_bounds.py`` — the declarative
  half of class (b), ``additional_dependencies:`` (#1572);
* ``tests/unit/guards/test_workflow_install_bounds.py`` — the free-form half,
  ``pip install`` in a command block (#1602);
* ``tests/unit/guards/test_docs_requirements_source_bounds.py`` — the compile
  source of a class (a) list (#1601).

Each carried its own copy, with a comment in two of them saying the readings
"must not differ". A rule written three times is a rule with three futures: the
day one of them starts counting ``!=`` or stops counting ``~=``, two halves of
the same MUSS disagree and nothing is red. So the copies are gone and this is
the single reading they all import.
"""

from __future__ import annotations

from packaging.specifiers import SpecifierSet

#: Operators that close the range from BELOW. ``==``/``===``/``~=`` close both
#: sides by themselves: an exact pin is a floor and a ceiling at once, and
#: ``~=1.4`` means ``>=1.4, ==1.*``.
_FLOOR_OPERATORS = frozenset({">=", ">", "==", "===", "~="})

#: Operators that close the range from ABOVE. See above for the three that
#: appear in both sets.
_CEILING_OPERATORS = frozenset({"<=", "<", "==", "===", "~="})


def bounds(specifier: SpecifierSet) -> tuple[bool, bool]:
    """``(has_floor, has_ceiling)`` for *specifier*.

    Args:
        specifier: The version specifier set of one requirement.

    Returns:
        A pair of booleans. An empty specifier set yields ``(False, False)`` —
        naming a package with no version at all is the weakest form there is,
        not a neutral one.
    """
    has_floor = any(clause.operator in _FLOOR_OPERATORS for clause in specifier)
    has_ceiling = any(clause.operator in _CEILING_OPERATORS for clause in specifier)
    return has_floor, has_ceiling


def missing_bound(specifier: SpecifierSet) -> str | None:
    """The side *specifier* leaves open, phrased for an assertion message.

    Returns:
        ``None`` when the range is closed on both sides, otherwise one of
        ``"no version bound at all"``, ``"no ceiling"``, ``"no floor"``.
    """
    has_floor, has_ceiling = bounds(specifier)
    if has_floor and has_ceiling:
        return None
    if not specifier:
        return "no version bound at all"
    return "no ceiling" if has_floor else "no floor"
