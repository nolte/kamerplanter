"""Regression tests for the scope of the E2E traceability gate (#1273).

**The defect being locked down.** The gate that is supposed to notice an E2E
test claiming no — or a nonexistent — test case was scoped to the REQ family by
two independent exclusions, either of which alone was enough to hide the whole
NFR family:

* ``scripts/check_bdd_traceability.py::collect_docstring_claims`` globbed
  ``test_req*.py``, so a test module named anything else was never read;
* ``tests/e2e/protocol_plugin.py::TC_ID_PATTERN`` — loaded by that script as
  *the* strict ID shape — was ``TC-(?:REQ-)?\\d{3}-\\d{3}``, which cannot express
  ``TC-NFR008-001`` or ``TC-UINFR002-001``. 230 of the 2276 cases the
  specification declares were therefore unclaimable: a test naming one of them
  was reported as declaring **no** ID.

The second exclusion had a quieter half. ``tests/e2e/conftest.py::_TC_ID_SCAN``
— the pattern behind the machine-readable junit ``tc_id`` property — restated
the family alternation instead of sharing it, so widening only the strict
pattern would have produced a test whose ID the gate accepted while its
``tc_id`` property stayed empty. :class:`TestBroadScanSharesTheFamilySet` is
what keeps the two halves together.

**Why the tests live here and not under ``tests/e2e/``.** ``tests/e2e/`` runs
only through ``scripts/run-e2e.sh`` (Docker plus the full stack), so a test
placed there would never execute in the ordinary gate, whereas
``pytest tests/unit/`` from ``src/backend`` is a PR-gating CI check. The price
is that both modules under test sit outside the backend package and have to be
loaded **by path** — the mechanism
``scripts/check_bdd_traceability.py::_load_module_by_path`` already uses, and
that ``test_gherkin_line_classification.py`` next door already copies.

**What is exercised, and what stands in for what.** ``tests/e2e/conftest.py``
cannot be imported here: it imports Selenium at module scope, and adding
Selenium to the backend unit tier would violate its no-outside-world rule for
the sake of one regex. So the ``_TC_ID_SCAN`` test does *not* rebuild the
pattern from its parts — rebuilding it would test the rebuild, not the
production line. It extracts the **assignment expression as written** with
``ast`` and evaluates that, so a hard-coded family list in conftest fails the
test even if it happens to agree today.

Traces to issue #1273 (no TC-ID: the E2E test harness is not a requirement).
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

# ── Loading the modules under test by path ───────────────────────────────────


def _find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* to the checkout root, identified by its markers.

    A marker walk rather than ``parents[N]``: a hard-coded index silently breaks
    the moment the test file moves, which has bitten this repository before.

    Args:
        start: Any path inside the checkout.

    Returns:
        The directory holding both ``Taskfile.yaml`` and ``tests/e2e``, or None.
    """
    for candidate in (start, *start.parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "tests" / "e2e").is_dir():
            return candidate
    return None


def _load_module_by_path(module_name: str, path: Path) -> ModuleType:
    """Execute the module at *path* under *module_name* and return it.

    Mirrors ``scripts/check_bdd_traceability.py::_load_module_by_path``. The
    registration in ``sys.modules`` must happen **before** ``exec_module``: both
    modules define dataclasses, and ``@dataclass`` resolves its own module via
    ``sys.modules`` while the module body is still running.

    Args:
        module_name: Private name to register under; must not collide with the
            name the module carries when the E2E suite imports it normally.
        path: The ``.py`` file to execute.

    Returns:
        The executed module.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        pytest.skip(f"{path} cannot be loaded as a Python module", allow_module_level=True)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip(
        "checkout root not found (no ancestor holds both Taskfile.yaml and tests/e2e); "
        "the E2E traceability modules are unreachable from here",
        allow_module_level=True,
    )

_PLUGIN_PATH = _REPO_ROOT / "tests" / "e2e" / "protocol_plugin.py"
_TRACEABILITY_PATH = _REPO_ROOT / "scripts" / "check_bdd_traceability.py"
_E2E_CONFTEST_PATH = _REPO_ROOT / "tests" / "e2e" / "conftest.py"
_SPEC_TESTCASE_DIR = _REPO_ROOT / "spec" / "e2e-testcases"

for _required in (_PLUGIN_PATH, _TRACEABILITY_PATH, _E2E_CONFTEST_PATH, _SPEC_TESTCASE_DIR):
    if not _required.exists():  # pragma: no cover — only in a partial checkout
        pytest.skip(f"{_required} does not exist in this checkout", allow_module_level=True)

protocol_plugin = _load_module_by_path("_kamerplanter_protocol_plugin_under_test", _PLUGIN_PATH)
traceability = _load_module_by_path("_kamerplanter_tc_id_scope_traceability", _TRACEABILITY_PATH)

#: The shape the gate accepts, read the way the gate reads it — by path, from
#: the plugin — rather than restated here.
STRICT = traceability.load_tc_id_pattern(_PLUGIN_PATH)

#: The exclusion this file removed, kept verbatim so the tests below can show
#: red against it instead of only green against the replacement.
PRE_1273_STRICT = re.compile(r"(TC-(?:REQ-)?\d{3}-\d{3})")


# ── The strict shape ─────────────────────────────────────────────────────────


class TestStrictPatternCoversEveryFamilyInUse:
    """All four ID spellings the repository actually writes must be expressible."""

    @pytest.mark.parametrize(
        ("tc_id", "family"),
        [
            ("TC-004-092", "bare — spec documents and the Gherkin tags derived from them"),
            ("TC-REQ-001-006", "REQ, which carries its own separating dash"),
            ("TC-NFR008-001", "NFR, dashless"),
            ("TC-UINFR002-001", "UI-NFR, dashless"),
        ],
    )
    def test_family_spelling_is_accepted(self, tc_id: str, family: str) -> None:
        assert STRICT.fullmatch(tc_id), f"the {family} spelling {tc_id} is not expressible"

    @pytest.mark.parametrize("tc_id", ["TC-NFR008-001", "TC-UINFR002-001"])
    def test_the_pattern_this_replaced_rejected_the_nfr_families(self, tc_id: str) -> None:
        """Red-first, kept as evidence: the old pattern could not express these.

        Without this the four green assertions above would be equally green
        against a pattern that never excluded anything, and the test would prove
        nothing about the change.
        """
        assert not PRE_1273_STRICT.fullmatch(tc_id)

    @pytest.mark.parametrize(
        ("text", "why"),
        [
            ("TC-NFR-008", "a document-level section heading, not a case"),
            ("TC-UI-NFR-002", "likewise a section heading"),
            ("TC-REQ-004-W001", "a test-local shape the strict pattern rejects on purpose"),
            ("TC-XYZ001-002", "a family nobody declared — the typo guard"),
            ("TC-NFR-008-001", "the dash-separated spelling that was rejected in #1273"),
            ("TCNFR008001", "no separators at all"),
        ],
    )
    def test_non_case_shapes_stay_rejected(self, text: str, why: str) -> None:
        """Widening the family set must not turn the strict pattern into a sieve.

        ``fullmatch`` is the operation ``conftest._is_known_tag`` and
        ``_tc_id_from_markers`` perform, so it is the one asserted here.
        """
        assert not STRICT.fullmatch(text), f"{text} should stay rejected: {why}"

    @pytest.mark.parametrize("text", ["TC-NFR-008", "TC-UI-NFR-002", "TC-REQ-004-W001", "TCNFR008001"])
    def test_non_case_shapes_yield_no_substring_match_either(self, text: str) -> None:
        """The gate reads IDs with ``search``, not ``fullmatch``.

        A pattern that rejects ``TC-NFR-008`` under ``fullmatch`` but finds some
        substring under ``search`` would let a section heading be claimed as a
        case, so both operations are pinned.
        """
        assert STRICT.search(text) is None


class TestEveryDeclaredSpecCaseIsExpressible:
    """No case the specification declares may be unclaimable by a test.

    This is the invariant the two exclusions broke, and it is the one that keeps
    the fix from rotting: a future family added to ``spec/e2e-testcases/``
    without widening ``TC_FAMILY_PREFIX`` fails here rather than silently
    dropping out of the gate again.
    """

    def test_the_strict_pattern_expresses_every_declared_case(self) -> None:
        cases, _duplicates, _documents = traceability.collect_spec_cases([_SPEC_TESTCASE_DIR])
        assert cases, "no declared cases found — the spec root moved or is empty"
        unexpressible = sorted(tc_id for tc_id in cases if not STRICT.fullmatch(tc_id))
        assert not unexpressible, (
            f"{len(unexpressible)} declared test case(s) cannot be named by any test, because "
            f"protocol_plugin.TC_ID_PATTERN cannot express them: {unexpressible[:10]}. "
            "Either widen TC_FAMILY_PREFIX for the new family or renumber the cases onto a "
            "spelling already in use — but do not leave them unclaimable, which is what made "
            "the whole NFR family invisible to the gate before #1273."
        )

    def test_the_pattern_this_replaced_left_cases_unexpressible(self) -> None:
        """Red-first: the same invariant, measured against the old pattern.

        Locks in *what* was broken rather than only that it is fixed now. If
        this ever passes, the spec no longer declares an NFR-family case and the
        assertion above has stopped being load-bearing.
        """
        cases, _duplicates, _documents = traceability.collect_spec_cases([_SPEC_TESTCASE_DIR])
        unexpressible = {tc_id for tc_id in cases if not PRE_1273_STRICT.fullmatch(tc_id)}
        assert unexpressible, "expected the pre-#1273 pattern to miss the NFR families"
        assert all(tc_id.startswith(("TC-NFR", "TC-UINFR")) for tc_id in unexpressible)


# ── The broad scan, which must share the family set ──────────────────────────


def _tc_id_scan_expression() -> str:
    """Return ``conftest._TC_ID_SCAN``'s value expression, as written in the file.

    Reading the source rather than importing it: ``tests/e2e/conftest.py``
    imports Selenium at module scope.

    Returns:
        The unparsed right-hand side of the ``_TC_ID_SCAN`` assignment.
    """
    tree = ast.parse(_E2E_CONFTEST_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_TC_ID_SCAN" for target in node.targets
        ):
            return ast.unparse(node.value)
    raise AssertionError(f"{_E2E_CONFTEST_PATH} assigns no _TC_ID_SCAN")


class TestBroadScanSharesTheFamilySet:
    """The junit ``tc_id`` channel must not know a narrower family set than the gate."""

    def test_the_scan_is_built_from_the_shared_family_prefix(self) -> None:
        """A hard-coded family list in conftest is the drift this guards against.

        Asserted on the expression rather than on behaviour, because two
        patterns can agree today and diverge on the next family — which is
        exactly how ``_TC_ID_SCAN`` came to reject ``TC-NFR008-001`` while
        nobody noticed.
        """
        expression = _tc_id_scan_expression()
        assert "TC_FAMILY_PREFIX" in expression, (
            "conftest._TC_ID_SCAN no longer derives its family alternation from "
            f"protocol_plugin.TC_FAMILY_PREFIX; it reads: {expression}"
        )

    @pytest.mark.parametrize(
        "tc_id",
        [
            "TC-004-092",
            "TC-REQ-001-006",
            "TC-REQ-004-W001",
            "TC-NFR008-001",
            "TC-UINFR002-001",
        ],
    )
    def test_the_expression_as_written_captures_every_family(self, tc_id: str) -> None:
        """Evaluate conftest's own expression — not a reconstruction of it.

        ``_pp_mod`` is the name conftest binds ``protocol_plugin`` to; supplying
        the real module means the family half comes from production code and
        only the surrounding ``re.compile`` call is re-executed here.
        """
        scan = eval(  # noqa: S307 — the expression comes from the checked-in conftest
            _tc_id_scan_expression(), {"re": re, "_pp_mod": protocol_plugin}
        )
        match = scan.search(f"{tc_id}: a docstring first line")
        assert match is not None and match.group(0) == tc_id


# ── The file glob ────────────────────────────────────────────────────────────


class TestGateScansEveryTestModule:
    """The gate must read every ``test_*.py``, not only the REQ family."""

    @staticmethod
    def _write(root: Path, name: str, body: str) -> None:
        (root / name).write_text(body, encoding="utf-8")

    def test_a_non_req_module_is_read(self, tmp_path: Path) -> None:
        self._write(
            tmp_path,
            "test_uinfr002_probe.py",
            '"""module"""\n\n\ndef test_probe():\n    """TC-UINFR002-001 — a claim."""\n',
        )
        claims = traceability.collect_docstring_claims([tmp_path], STRICT)
        assert [(c.func, c.tc_id) for c in claims] == [("test_probe", "TC-UINFR002-001")]

    def test_a_non_req_module_declaring_nothing_is_a_defect(self, tmp_path: Path) -> None:
        """Being read is only half of it — the untagged case has to reach the report.

        Without this, a glob that finds the file but a report that ignores it
        would look identical to a working gate.
        """
        self._write(
            tmp_path,
            "test_nfr008_probe.py",
            '"""module"""\n\n\ndef test_probe():\n    """No case named here."""\n',
        )
        claims = traceability.collect_docstring_claims([tmp_path], STRICT)
        assert [c.tc_id for c in claims] == [None]
        assert traceability.report_docstring_channel(claims, {}) == 1

    def test_bdd_step_modules_stay_excluded(self, tmp_path: Path) -> None:
        """``pytest_bdd`` overwrites ``__doc__``; those IDs live in the Gherkin tag.

        The wider glob must not start reading a channel that is structurally
        dead, or every scenario module would report as untagged.
        """
        self._write(
            tmp_path,
            "test_req004_thing_bdd.py",
            '"""module"""\n\n\ndef test_scenario():\n    """No docstring ID by design."""\n',
        )
        assert traceability.collect_docstring_claims([tmp_path], STRICT) == []

    def test_the_glob_this_replaced_did_not_see_the_module(self, tmp_path: Path) -> None:
        """Red-first for the glob half, measured rather than asserted from memory."""
        self._write(
            tmp_path,
            "test_uinfr002_probe.py",
            '"""module"""\n\n\ndef test_probe():\n    """TC-UINFR002-001 — a claim."""\n',
        )
        assert sorted(p.name for p in tmp_path.glob("test_req*.py")) == []
        assert sorted(p.name for p in tmp_path.glob("test_*.py")) == ["test_uinfr002_probe.py"]
