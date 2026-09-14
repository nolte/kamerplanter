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
import sys
from importlib import metadata
from pathlib import Path

import pytest

#: This module itself, so the control can repoint ``_SCAN_ROOTS`` at a temp
#: directory. Rebinding a module global from inside one of its own functions
#: would not be seen by the helper, which reads it at call time.
_module = sys.modules[__name__]

_BACKEND = Path(__file__).resolve().parents[2]
_REPO = _BACKEND.parents[1]
_PYPROJECT = _BACKEND / "pyproject.toml"
_LOCK = _BACKEND / "uv.lock"

#: Every tree that may contain a skip guard.
#:
#: Not just ``src/backend/tests``, and not just ``test_*.py``. A guard moved into a
#: ``conftest.py`` fixture — which is exactly where the three ``moto`` guards this
#: change converted used to live — would otherwise be invisible to the check that
#: exists to find it. ``tests/e2e/`` sits at the repository root, outside the backend
#: package entirely.
_SCAN_ROOTS: tuple[Path, ...] = tuple(root for root in (_BACKEND / "tests", _REPO / "tests") if root.is_dir())


def _locked_distributions() -> set[str]:
    """Every distribution name ``uv.lock`` pins, normalised for comparison."""
    names = re.findall(r'^name = "([^"]+)"', _LOCK.read_text(encoding="utf-8"), flags=re.M)
    return {name.lower().replace("_", "-") for name in names}


def _distribution_for(module: str) -> str:
    """The distribution that provides this *import* name.

    ``importorskip`` takes an import name; the lock records distributions, and for
    six of this project's direct dependencies the two differ — ``yaml`` is PyYAML,
    ``arango`` is python-arango, ``PIL`` is pillow, ``dateutil`` is python-dateutil,
    ``attr`` is attrs. Comparing the import name against the lock, as the first
    version did, therefore reported none of them: precisely the hole this file exists
    to close, reproduced inside it.

    ``packages_distributions()`` resolves the mapping from what is actually installed
    — which is the environment ``uv sync --locked --extra dev`` builds, the same one
    CI runs. A module that resolves to nothing is not installed here, so falling back
    to its own name is right: an absent package is a legitimately optional one.
    """
    top_level = module.split(".")[0]
    providers = metadata.packages_distributions().get(top_level)
    name = providers[0] if providers else top_level
    return name.lower().replace("_", "-")


def _importorskip_targets() -> list[tuple[Path, int, str]]:
    """``(file, line, module)`` for every ``importorskip`` call with a literal module.

    Three call shapes, because two of them were missed and both are ordinary pytest:

    * ``pytest.importorskip("x")`` — the attribute form;
    * ``importorskip("x")`` after ``from pytest import importorskip`` — a bare name,
      which the attribute-only scan did not see at all;
    * ``pytest.importorskip(modname="x")`` — ``modname`` is the real parameter name,
      and a positional-only scan skipped it.

    Verified empirically during review: a file using either of the last two produced
    an empty detection list.
    """
    found: list[tuple[Path, int, str]] = []
    for root in _SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                is_call = (isinstance(func, ast.Attribute) and func.attr == "importorskip") or (
                    isinstance(func, ast.Name) and func.id == "importorskip"
                )
                if not is_call:
                    continue
                literal: str | None = None
                if node.args and isinstance(node.args[0], ast.Constant):
                    value = node.args[0].value
                    literal = value if isinstance(value, str) else None
                else:
                    for keyword in node.keywords:
                        if keyword.arg == "modname" and isinstance(keyword.value, ast.Constant):
                            value = keyword.value.value
                            literal = value if isinstance(value, str) else None
                if literal is not None:
                    found.append((path, node.lineno, literal))
    return found


#: The call shapes the scanner must recognise, one planted file each.
#:
#: The first version of this control planted only the attribute form. Review then
#: showed empirically that the other two produced an empty detection list — so the
#: guard meant to make this rule mechanical could be walked around by writing
#: ``from pytest import importorskip``, which is ordinary pytest.
_CALL_SHAPES: dict[str, str] = {
    "attribute": "import pytest\n\n\ndef test_x():\n    pytest.importorskip('planted_module')\n",
    "bare-name": ("from pytest import importorskip\n\n\ndef test_x():\n    importorskip('planted_module')\n"),
    "keyword": "import pytest\n\n\ndef test_x():\n    pytest.importorskip(modname='planted_module')\n",
}


@pytest.mark.parametrize("shape", sorted(_CALL_SHAPES))
def test_the_scan_actually_finds_an_importorskip(tmp_path, monkeypatch, shape: str):
    """The control, driven over files written here rather than over the codebase.

    The real check passes trivially when the scan returns nothing, and after #1435
    there may legitimately be no guard left to find — so anchoring the control on a
    module that happens to be guarded today would make it evaporate the moment that
    guard is (correctly) removed. This plants one and requires the scanner to see it.

    Measured need: an earlier version asserted ``moto`` was still guarded. Converting
    the moto guards — the right fix, since moto is locked too — would have silently
    turned this file into an assertion about an empty list.
    """
    planted = tmp_path / "helper_not_named_like_a_test.py"
    planted.write_text(_CALL_SHAPES[shape], encoding="utf-8")
    monkeypatch.setattr(_module, "_SCAN_ROOTS", (tmp_path,))

    found = {module for _path, _line, module in _importorskip_targets()}

    assert found == {"planted_module"}, (
        f"the scanner did not see an importorskip written in the {shape!r} shape "
        f"(found {sorted(found)}); every other assertion in this file consumes it"
    )


def test_the_scan_reaches_files_that_are_not_named_test_something(tmp_path, monkeypatch):
    """A guard in a ``conftest.py`` must not be invisible.

    That is not a hypothetical location: the three ``moto`` guards this change
    converted lived in fixtures, and moving one into a shared ``conftest.py`` is the
    ordinary next refactor. ``rglob("test_*.py")`` would have skipped all five
    conftest files under ``src/backend/tests``.
    """
    (tmp_path / "conftest.py").write_text(_CALL_SHAPES["attribute"], encoding="utf-8")
    monkeypatch.setattr(_module, "_SCAN_ROOTS", (tmp_path,))

    found = {module for _path, _line, module in _importorskip_targets()}

    assert found == {"planted_module"}


def test_an_import_name_resolves_to_its_distribution():
    """The mapping the rule depends on, checked against names that actually differ.

    Comparing the import name straight against the lock — the first version — missed
    every dependency whose distribution is spelled differently, which is six of this
    project's direct ones.
    """
    assert _distribution_for("yaml") == "pyyaml"
    assert _distribution_for("arango") == "python-arango"
    assert _distribution_for("PIL") == "pillow"
    assert _distribution_for("dateutil") == "python-dateutil"
    assert _distribution_for("attr") == "attrs"
    # Same name on both sides: the case the first version got right by accident.
    assert _distribution_for("moto") == "moto"
    # A submodule resolves through its top-level package.
    assert _distribution_for("yaml.parser") == "pyyaml"
    # Not installed anywhere: falls back to its own name, so it cannot be in the lock
    # and is treated as genuinely optional.
    assert _distribution_for("a_package_nobody_installed") == "a-package-nobody-installed"


def test_no_importorskip_guards_a_locked_dependency():
    """A skip guard on a pinned package hides a broken environment as a pass.

    Gated on the **lock** alone. The first version also required the package to be
    named in ``pyproject.toml``, which is narrower than the rule this file states: a
    transitively locked dependency — ``botocore``, ``attrs``, ``rpds-py`` — is
    installed just as reliably as a declared one, and a guard on it hides a broken
    environment exactly the same way.
    """
    locked = _locked_distributions()

    offenders = []
    for path, line, module in _importorskip_targets():
        if _distribution_for(module) in locked:
            offenders.append(f"{path.relative_to(_REPO)}:{line} guards {module!r}")

    assert not offenders, (
        "these guards skip on a dependency the project declares and locks, so a broken "
        "environment reports as a pass instead of a failure:\n  "
        + "\n  ".join(offenders)
        + "\n\nUse a plain import. `importorskip` is for a genuinely optional package "
        "— one the project does not install (#1435)."
    )
