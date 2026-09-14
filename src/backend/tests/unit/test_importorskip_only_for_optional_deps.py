"""#1435 — ``importorskip`` may not be pointed at a dependency the project locks.

``pytest.importorskip`` exists for a genuinely optional import. Applied to a package
the project declares and pins, it converts "your environment is broken" into "these
tests silently did not run", and a silent skip is indistinguishable from a pass in
every summary anyone reads.

That is not hypothetical here. ``tests/unit/migrations/test_seed_schema_conformance.py``
and its two siblings guarded on ``jsonschema`` and ``referencing`` while neither
package was declared in ``pyproject.toml`` nor present in ``uv.lock``. CI installs
exactly the lock, so it installed neither, and **all 35 cases skipped in every run
since the suite was written** — 32 seed files validated by nothing, a tier that looked
like coverage and was not. They executed only on machines that happened to carry
``jsonschema`` from an unrelated tool.

This test does not ban ``importorskip``. It bans the combination that made the gap
invisible: a skip guard on a package the lock guarantees to be there.

Related: #1432 (the integration tier self-skips to green without ArangoDB) and #1434
(the same class, reached through the wrong interpreter). Three instances of "a check
that reports green without running" in one session is why this one is mechanical.
"""

from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2]
_TESTS = _BACKEND / "tests"
_PYPROJECT = _BACKEND / "pyproject.toml"
_LOCK = _BACKEND / "uv.lock"


def _locked_distributions() -> set[str]:
    """Every distribution name ``uv.lock`` pins, normalised for comparison."""
    names = re.findall(r'^name = "([^"]+)"', _LOCK.read_text(encoding="utf-8"), flags=re.M)
    return {name.lower().replace("_", "-") for name in names}


def _declared_requirements() -> set[str]:
    """Distribution names ``pyproject.toml`` asks for, main dependencies and extras."""
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    project = data.get("project", {})
    requirements: list[str] = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        requirements.extend(extra)
    found = set()
    for requirement in requirements:
        # "moto[s3]>=5.0,<6.0.0" -> "moto"
        name = re.split(r"[\[<>=!~;\s]", requirement, maxsplit=1)[0]
        if name:
            found.add(name.lower().replace("_", "-"))
    return found


def _importorskip_targets() -> list[tuple[Path, int, str]]:
    """``(file, line, module)`` for every ``pytest.importorskip("...")`` literal."""
    found: list[tuple[Path, int, str]] = []
    for path in sorted(_TESTS.rglob("test_*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "importorskip"):
                continue
            if not node.args:
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                found.append((path, node.lineno, first.value))
    return found


def test_the_scan_actually_finds_an_importorskip(tmp_path):
    """The control, driven over a file written here rather than over the codebase.

    The real check passes trivially when the scan returns nothing, and after #1435
    there may legitimately be no guard left to find — so anchoring the control on a
    module that happens to be guarded today would make it evaporate the moment that
    guard is (correctly) removed. This plants one and requires the scanner to see it.

    Measured need: the earlier version of this control asserted ``moto`` was still
    guarded. Converting the moto guards — the right fix, since moto is locked too —
    would have silently turned this file into an assertion about an empty list.
    """
    planted = tmp_path / "test_planted.py"
    planted.write_text(
        "import pytest\n\n\ndef test_x():\n    pytest.importorskip('some_optional_thing')\n",
        encoding="utf-8",
    )

    global _TESTS
    original, _TESTS = _TESTS, tmp_path
    try:
        found = {module for _path, _line, module in _importorskip_targets()}
    finally:
        _TESTS = original

    assert found == {"some_optional_thing"}, (
        f"the importorskip scanner did not see a call it was pointed straight at "
        f"(found {sorted(found)}); every other assertion in this file consumes it"
    )


def test_no_importorskip_guards_a_locked_dependency():
    """A skip guard on a pinned package hides a broken environment as a pass."""
    locked = _locked_distributions()
    declared = _declared_requirements()

    offenders = []
    for path, line, module in _importorskip_targets():
        # ``importorskip`` takes an *import* name; the distribution may differ
        # (``moto[s3]`` installs ``moto``). Compare on the top-level package.
        distribution = module.split(".")[0].lower().replace("_", "-")
        if distribution in locked and distribution in declared:
            offenders.append(f"{path.relative_to(_BACKEND)}:{line} guards {module!r}")

    assert not offenders, (
        "these guards skip on a dependency the project declares and locks, so a broken "
        "environment reports as a pass instead of a failure:\n  "
        + "\n  ".join(offenders)
        + "\n\nUse a plain import. `importorskip` is for a genuinely optional package "
        "— one the project does not install (#1435)."
    )
