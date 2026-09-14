"""#1435 — ``importorskip`` may not be pointed at a dependency the backend installs.

``pytest.importorskip`` exists for a genuinely optional import. Applied to a package
the environment is guaranteed to have, it converts "your environment is broken" into
"these tests silently did not run", and a silent skip is indistinguishable from a
pass in every summary anyone reads.

That is not hypothetical. ``tests/unit/migrations/test_seed_schema_conformance.py``
and its two siblings guarded on ``jsonschema`` and ``referencing`` while neither
package was declared in ``pyproject.toml`` nor present in ``uv.lock``. CI installs
exactly the lock, so it installed neither, and **all 35 cases skipped in every run
since the suite was written** — 32 seed files validated by nothing.

**This file has now been the same mistake twice, which is why it is shaped as it
is.** Review round 1 found five ways around the scanner: two call shapes it did not
recognise, an import-name/distribution-name mismatch, a condition narrower than the
stated rule, and a scan that skipped every ``conftest.py``. Round 2 found worse —
with all six real guards converted, ``_importorskip_targets()`` returned an empty
list, so the rule's loop body never executed. Breaking the lock parser outright still
left the file reporting six passes. A check that cannot fail is precisely the class
this file exists to catch, and it had reached the third layer of itself.

So the rule now runs on planted input in every run (see
``test_the_rule_reports_a_guard_on_a_locked_package``), not only over whatever the
codebase happens to contain.

**Scope: the backend test tree.** The comparison is against ``src/backend/uv.lock``,
which describes one environment. ``tests/e2e/`` is built from its own
``requirements.txt`` in its own image, and ``src/knowledge-service``,
``src/inference-service`` and ``src/libs/kp_vectordb`` carry their own dependency
sets — a guard on PyYAML is *correct* in an e2e file, and demanding a plain import
there would crash that container. Extending the rule to those trees means giving each
one its own lock to compare against, not widening this one.

**What this does not cover.** ``try: import X / except ImportError`` plus
``pytest.mark.skipif`` produces the identical silent skip and is not detected.
``tests/integration/`` uses exactly that shape for ArangoDB, deliberately, and
whether that tier should run at all is #1432. This bans the spelling that caused
#1435, not every possible way to express it.

Related: #1432 (the integration tier self-skips to green without ArangoDB) and #1434
(the same class reached through the wrong interpreter).
"""

from __future__ import annotations

import ast
import re
import sys
from importlib import metadata
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[2]
_LOCK = _BACKEND / "uv.lock"

#: The tree this rule governs — see "Scope" above for why it is only this one.
#:
#: Every ``*.py``, not ``test_*.py``: a guard moved into a ``conftest.py`` fixture is
#: exactly where the three ``moto`` guards this change converted used to live, and
#: five conftest files under here were never opened by the narrower glob.
_SCAN_ROOTS: tuple[Path, ...] = (_BACKEND / "tests",)

#: This module, so a control can repoint ``_SCAN_ROOTS`` at a temp directory.
#: Rebinding a module global from inside one of its own functions would not be seen
#: by the helper, which reads it at call time.
_module = sys.modules[__name__]


def _locked_distributions() -> set[str]:
    """Every distribution name ``uv.lock`` pins, normalised for comparison."""
    names = re.findall(r'^name = "([^"]+)"', _LOCK.read_text(encoding="utf-8"), flags=re.M)
    return {name.lower().replace("_", "-") for name in names}


def _providers_of(module: str) -> set[str]:
    """Distributions providing this *import* name, as installed here.

    ``importorskip`` takes an import name; the lock records distributions, and for
    five of this project's direct dependencies the two differ — ``yaml`` is PyYAML,
    ``arango`` is python-arango, ``PIL`` is pillow, ``dateutil`` is python-dateutil,
    ``attr`` is attrs. Comparing the import name straight against the lock reported
    none of them.

    **A set, not ``providers[0]``.** ``packages_distributions()`` maps a top-level
    name to a *list*, and for a namespace package or a shadowed top-level the order
    follows metadata iteration and is not stable across environments. Taking the
    first would make the rule pass or fail by install order.

    Resolved against what is actually installed, which does the work of a second
    condition: ``uv.lock`` also pins packages that install only under a marker —
    ``uvloop`` off Windows, ``colorama`` and ``tzdata`` on it, ``psycopg-binary``,
    ``brotlicffi``. Those are legitimately absent here, a guard on them is correct,
    and the plain import this rule demands would hard-fail the suite on the platform
    where the package rightly is not there. An empty result therefore means "not
    guaranteed present", which is exactly the optional case.
    """
    top_level = module.split(".")[0]
    providers = metadata.packages_distributions().get(top_level) or []
    return {name.lower().replace("_", "-") for name in providers}


def _importorskip_targets() -> list[tuple[Path, int, str]]:
    """``(file, line, module)`` for every ``importorskip`` call with a literal module.

    Three call shapes, because two were missed in round 1 and both are ordinary
    pytest:

    * ``pytest.importorskip("x")`` — the attribute form;
    * ``importorskip("x")`` after ``from pytest import importorskip`` — a bare name,
      which an attribute-only scan does not see at all;
    * ``pytest.importorskip(modname="x")`` — ``modname`` is the real parameter name,
      and a positional-only scan skips it.

    A non-literal target (``importorskip(MODNAME)``) cannot be resolved statically and
    is *reported*, not dropped — quietly losing the hit is how a guard walks past the
    check meant to find it.

    Still not covered, and named here rather than left to be discovered: an aliased
    import, ``from pytest import importorskip as _skip``. The ``ast.Name`` branch
    compares on the bound name, so a rename escapes it. Following aliases means
    tracking imports per module, which is more machinery than the one spelling that
    caused #1435 warrants — but it is a hole, not a decision that there is none.
    """
    found: list[tuple[Path, int, str]] = []
    for root in _module._SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (SyntaxError, UnicodeDecodeError) as exc:
                # Named, not swallowed. A deliberately-broken fixture file is ordinary
                # in a test tree, and letting this raise would take the rule offline
                # behind a traceback that never says which file did it.
                pytest.fail(f"{path}: unparseable while scanning for importorskip ({exc})")
            for node in ast.walk(tree):
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
                else:
                    # A non-literal target — ``pytest.importorskip(MODNAME)`` — cannot
                    # be resolved statically. Reported rather than dropped: silently
                    # losing the hit is how a guard walks past the check that exists
                    # to find it, which is what review round 1 found twice.
                    pytest.fail(
                        f"{path}:{node.lineno}: importorskip with a non-literal module "
                        f"cannot be checked against the lock. Spell the module out, or "
                        f"add it to the exemptions in this file with a reason (#1435)."
                    )
    return found


def _offenders() -> list[str]:
    """Guards sitting on a package this environment is guaranteed to have."""
    locked = _locked_distributions()
    return [
        # ``relative_to`` only when the file really is under the backend, so the
        # planted-input controls below (which scan a temp directory) exercise this
        # function rather than dying in its formatting.
        f"{path.relative_to(_BACKEND) if path.is_relative_to(_BACKEND) else path}:{line} guards {module!r}"
        for path, line, module in _importorskip_targets()
        if _providers_of(module) & locked
    ]


# ── the rule ─────────────────────────────────────────────────────────────────


def test_no_importorskip_guards_a_locked_dependency():
    """A skip guard on a guaranteed package hides a broken environment as a pass."""
    offenders = _offenders()

    assert not offenders, (
        "these guards skip on a dependency the backend installs from its lock, so a "
        "broken environment reports as a pass instead of a failure:\n  "
        + "\n  ".join(offenders)
        + "\n\nUse a plain import. `importorskip` is for a genuinely optional package "
        "— one this environment does not install (#1435)."
    )


# ── and the proof that the rule can still fail ───────────────────────────────

#: One planted file per call shape. ``yaml`` is the right bait: locked, installed,
#: and its distribution is spelled ``PyYAML``, so a regression in either the scanner
#: or the name mapping turns these red.
_CALL_SHAPES: dict[str, str] = {
    "attribute": "import pytest\n\n\ndef test_x():\n    pytest.importorskip('yaml')\n",
    "bare-name": "from pytest import importorskip\n\n\ndef test_x():\n    importorskip('yaml')\n",
    "keyword": "import pytest\n\n\ndef test_x():\n    pytest.importorskip(modname='yaml')\n",
}


@pytest.mark.parametrize("shape", sorted(_CALL_SHAPES))
def test_the_rule_reports_a_guard_on_a_locked_package(tmp_path, monkeypatch, shape: str):
    """The rule itself, exercised — the finding that made round 2 worth having.

    With all six real guards converted, ``_importorskip_targets()`` returns an empty
    list, so ``test_no_importorskip_guards_a_locked_dependency`` asserts ``not []``
    and passes without running its own logic. Measured in review: breaking the lock
    parser so it returned an empty set still left this file reporting six passes. The
    lock format has already been rewritten once here (the uv migration, #1377); a
    second change would have disabled the rule in silence.

    So the whole path runs on planted input every time: scan, name resolution, lock
    comparison, offender list.
    """
    (tmp_path / "helper_not_named_like_a_test.py").write_text(_CALL_SHAPES[shape], encoding="utf-8")
    monkeypatch.setattr(_module, "_SCAN_ROOTS", (tmp_path,))

    offenders = _offenders()

    assert len(offenders) == 1, f"the {shape!r} shape produced {offenders}"
    assert "'yaml'" in offenders[0]


def test_the_rule_leaves_a_genuinely_optional_package_alone(tmp_path, monkeypatch):
    """The control against a rule that simply reports everything.

    Without it, an ``_offenders`` that returned every guard it found would satisfy
    the three cases above — and would then demand a plain import for packages this
    environment correctly does not install.
    """
    (tmp_path / "conftest.py").write_text(
        "import pytest\n\npytest.importorskip('a_package_nobody_installed')\n", encoding="utf-8"
    )
    monkeypatch.setattr(_module, "_SCAN_ROOTS", (tmp_path,))

    assert _offenders() == []


def test_a_guard_in_a_conftest_is_not_invisible(tmp_path, monkeypatch):
    """``rglob("test_*.py")`` skipped all five conftest files under the backend tests.

    Not a hypothetical location: the three ``moto`` guards this change converted lived
    in fixtures, and moving one into a shared ``conftest.py`` is the ordinary next
    refactor.
    """
    (tmp_path / "conftest.py").write_text(_CALL_SHAPES["attribute"], encoding="utf-8")
    monkeypatch.setattr(_module, "_SCAN_ROOTS", (tmp_path,))

    assert len(_offenders()) == 1


#: A sample of distributions the ``dev`` extra installs, and the import name each
#: provides. Load-bearing for the precondition below, not for the rule.
_EXPECTED_DEV_IMPORTS: dict[str, str] = {
    "yaml": "pyyaml",
    "jsonschema": "jsonschema",
    "moto": "moto",
    "arango": "python-arango",
}


def test_this_environment_can_judge_the_rule_at_all():
    """The precondition, and the reason it has to exist.

    ``_providers_of`` resolves against what is **installed**, which is deliberate —
    it is how a marker-gated lock entry (``colorama`` off Windows, ``uvloop`` on it)
    is correctly treated as not-guaranteed. The cost is that the rule goes quiet in
    an environment where nothing is installed: every guard resolves to no provider,
    ``_offenders()`` returns ``[]``, and the check reports a pass.

    That is the failure mode this file exists to catch, aimed at itself for the
    fourth time — and the environment in question is not hypothetical. Running
    ``python3 -m pytest`` instead of ``.venv/bin/python -m pytest`` produces exactly
    it (#1434), and review round 3 reached this file that way.

    So: refuse rather than pass. If the packages the ``dev`` extra guarantees are not
    importable, the environment cannot judge the rule and says so.
    """
    missing = sorted(
        f"{module} (from {distribution})"
        for module, distribution in _EXPECTED_DEV_IMPORTS.items()
        if distribution not in _providers_of(module)
    )

    assert not missing, (
        "this interpreter is not the environment `uv sync --locked --extra dev` "
        f"builds — {', '.join(missing)} cannot be resolved. Every check in this file "
        "would pass vacuously here, because a guard on an absent package resolves to "
        "no provider. Run `.venv/bin/python -m pytest`, not the global interpreter "
        "(#1434)."
    )


def test_a_marker_gated_lock_entry_is_not_reported(tmp_path, monkeypatch):
    """``uv.lock`` pins packages that install only under a platform marker.

    ``colorama`` and ``tzdata`` on Windows, ``uvloop`` off it, ``psycopg-binary``,
    ``brotlicffi``. They are in the lock and legitimately absent on the other
    platform, so a guard on them is correct — and the plain import this rule demands
    would hard-fail the suite exactly where the package rightly is not installed.

    Driven over planted input against a name that is in the lock and not installed
    here, because the previous version of this test was a tautology: it collected the
    names with no provider and then asserted that their (empty) provider set did not
    intersect the lock. ``set() & locked`` is empty by construction, so it could not
    fail in any environment.
    """
    locked = _locked_distributions()
    absent = [
        name for name in ("colorama", "tzdata", "uvloop", "brotlicffi") if name in locked and not _providers_of(name)
    ]
    if not absent:
        pytest.skip("every marker-gated candidate happens to be installed on this platform")

    (tmp_path / "conftest.py").write_text(f"import pytest\n\npytest.importorskip({absent[0]!r})\n", encoding="utf-8")
    monkeypatch.setattr(_module, "_SCAN_ROOTS", (tmp_path,))

    assert _offenders() == [], (
        f"{absent[0]!r} is in the lock but not installed here, so a guard on it is "
        f"correct; reporting it would demand an import that crashes on this platform"
    )


def test_an_import_name_resolves_to_its_distribution():
    """The mapping the rule depends on, checked where the two names differ.

    Comparing the import name straight against the lock — the first version — missed
    every dependency whose distribution is spelled differently, five of this project's
    direct ones.
    """
    assert _providers_of("yaml") == {"pyyaml"}
    assert _providers_of("arango") == {"python-arango"}
    assert _providers_of("PIL") == {"pillow"}
    assert _providers_of("dateutil") == {"python-dateutil"}
    assert _providers_of("attr") == {"attrs"}
    # A submodule resolves through its top-level package.
    assert _providers_of("yaml.parser") == {"pyyaml"}
    # Installed nowhere: no provider, so not guaranteed, so genuinely optional.
    assert _providers_of("a_package_nobody_installed") == set()


def test_the_lock_parser_still_reads_this_lock_format():
    """``_locked_distributions`` against a fact independent of its own regex.

    The uv migration (#1377) rewrote this file's format once already. If the parser
    stops matching, every comparison above silently compares against an empty set —
    which is how review found the rule inert.
    """
    text = _LOCK.read_text(encoding="utf-8")
    locked = _locked_distributions()
    blocks = text.count("[[package]]")

    # ``>=`` on a *distinct* count, not ``==`` on the block count: uv may record the
    # same distribution twice at different versions when resolution forks under
    # divergent markers. That is a correct lock, and the previous equality would have
    # reported it as "uv.lock's format changed" — a false alarm arriving precisely
    # when someone adds a platform-dependent dependency.
    assert locked, "the lock parser found no names at all; uv.lock's format changed"
    assert len(locked) <= blocks, (
        f"the parser found {len(locked)} distinct names for {blocks} [[package]] "
        f"blocks, which cannot happen — the regex is matching something else"
    )
    assert len(locked) >= blocks * 0.9, (
        f"the parser found only {len(locked)} distinct names for {blocks} blocks; "
        f"either uv.lock's format changed or an implausible number of duplicates "
        f"appeared"
    )
    assert {"pyyaml", "jsonschema", "referencing", "moto"} <= locked
