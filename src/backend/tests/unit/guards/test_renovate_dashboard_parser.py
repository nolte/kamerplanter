"""#1383 — the Renovate-health check, driven against a real dashboard body.

**What this guards.** ``scripts/ci/check_renovate_dashboard.py`` decides whether
Renovate is still reading the files it is supposed to read. That decision is the
one nothing in this repository could make between 2026-08-02 and 2026-09-10,
while the ``pip-compile`` manager extracted nothing at all and every lane stayed
green.

**The fixtures are real, and there are two of them, for a measured reason.**

``renovate_dashboard_2026-09-16.md`` is the verbatim body of issue #12 on the day
this was written (``gh issue view 12 --json body``). It is **not** the healthy
state: #1374 had not reached ``develop`` yet, so Renovate had not re-scanned, and
the body still shows ``poetry`` reading four ``pyproject.toml`` files and
``pip_requirements`` reading four side-service ``requirements.txt`` that the
working tree no longer contains. That makes it the most honest drift fixture
available — it is what the lane really would say today, and saying it would be
correct.

``renovate_dashboard_expected_after_1374.md`` is derived from it mechanically
(the ``poetry`` block removed, its files moved under ``pep621``, the deleted
requirements files dropped) and is the healthy state the lane must accept in
silence.

**A measurement that corrected the plan.** The #1383 analysis said ``poetry``
read "exactly the two side-service pyproject.toml". The real body shows **four**:
``src/libs/kp_errortracking`` and ``src/libs/kp_vectordb`` were in there too.
With ``poetry`` disabled repository-wide those two land under ``pep621`` — which
would have made the "strong expectation" fire on a correct repository. They are
enumerated in ``KNOWN_LOCKLESS_PEP621_FILES`` with the reason they carry no lock,
rather than the expectation being loosened to "at least the five".

**What is NOT under test here.** Whether Renovate's dashboard format is stable —
that is upstream's. This file pins the parser against one real body and against
injected problems; the format changing shows up as a :class:`DashboardError`,
which is a red run, not a silent pass. Traces to #1383 (no TC-ID: a CI observer
is not a user-facing case).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_SCRIPT = _REPO_ROOT / "scripts" / "ci" / "check_renovate_dashboard.py"
_FIXTURES = Path(__file__).parent / "fixtures"
_TODAY = _FIXTURES / "renovate_dashboard_2026-09-16.md"
_HEALTHY = _FIXTURES / "renovate_dashboard_expected_after_1374.md"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_renovate_dashboard_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_renovate_dashboard_under_test"] = module
    spec.loader.exec_module(module)
    return module


check = _load()


@pytest.fixture
def healthy_body() -> str:
    return _HEALTHY.read_text()


@pytest.fixture
def todays_body() -> str:
    return _TODAY.read_text()


def _report(body: str) -> dict:
    return check.build_report(body, repo_root=_REPO_ROOT)


class TestTheFixturesAreTheRealThing:
    """A fixture that drifted from the source is a certificate of nothing."""

    def test_both_fixtures_exist_and_are_substantial(self) -> None:
        for fixture in (_TODAY, _HEALTHY):
            assert fixture.is_file(), f"{fixture} is missing"
            assert len(fixture.read_text().splitlines()) > 500, (
                f"{fixture} is far shorter than a real dashboard body (~880 lines). A truncated fixture "
                "would exercise the parser on a shape Renovate never emits."
            )

    def test_the_healthy_fixture_really_is_the_repository_it_claims_to_describe(self, healthy_body: str) -> None:
        """Every pyproject the healthy fixture lists must exist in the checkout.

        The recurring failure here is a fixture that invents an impossible shape:
        the positive case then certifies nothing. This ties the fixture to the
        working tree.
        """
        inventory = check.manager_inventory(healthy_body)
        for package_file in inventory["pep621"]:
            assert (_REPO_ROOT / package_file).is_file(), (
                f"the healthy fixture lists {package_file} under pep621, but no such file exists in the "
                "checkout — the fixture describes a repository that is not this one"
            )

    def test_the_expected_locked_trees_all_carry_a_lock_on_disk(self) -> None:
        for package_file in check.EXPECTED_PEP621_FILES:
            assert (_REPO_ROOT / package_file).is_file(), f"{package_file} does not exist"
            assert (_REPO_ROOT / package_file).with_name("uv.lock").is_file(), (
                f"no uv.lock beside {package_file} — the expectation in check_renovate_dashboard.py is "
                "unsatisfiable against this checkout"
            )

    def test_the_known_lockless_trees_really_have_no_lock(self) -> None:
        """An allowlist entry that is no longer needed must not sit there unnoticed."""
        for package_file in check.KNOWN_LOCKLESS_PEP621_FILES:
            assert (_REPO_ROOT / package_file).is_file(), f"{package_file} does not exist"
            assert not (_REPO_ROOT / package_file).with_name("uv.lock").is_file(), (
                f"{package_file} now HAS a uv.lock, so it belongs in EXPECTED_PEP621_FILES, not in the "
                "lock-less allowlist. An allowlist entry nobody revisits is how an exception outlives its "
                "reason (#1456)."
            )


class TestTheUnchangedHealthyBodyIsGreen:
    """The positive control. Everything below is measured against this."""

    def test_no_alert(self, healthy_body: str) -> None:
        report = _report(healthy_body)
        assert report["alert"] is False, "findings: " + json.dumps(report["findings"], indent=2)

    def test_it_really_read_the_inventory(self, healthy_body: str) -> None:
        """Green because it looked, not because it found nothing to look at."""
        report = _report(healthy_body)
        assert set(report["pep621_files"]) >= set(check.EXPECTED_PEP621_FILES)
        assert "poetry" not in report["managers"]
        assert len(report["managers"]) > 5, f"only {report['managers']} — suspiciously few managers parsed"

    def test_the_render_says_so(self, healthy_body: str) -> None:
        assert "healthy" in check.render(_report(healthy_body))


class TestTodaysRealBodyIsCorrectlyRed:
    """Issue #12 as of 2026-09-16 — before #1374 reached develop."""

    def test_it_alerts(self, todays_body: str) -> None:
        report = _report(todays_body)
        assert report["alert"] is True

    def test_it_names_poetry_and_the_missing_trees(self, todays_body: str) -> None:
        findings = "\n".join(_report(todays_body)["findings"])
        assert "`poetry` appears in the inventory" in findings
        assert "src/inference-service/pyproject.toml" in findings
        assert "docker/reranker-service/pyproject.toml" in findings

    def test_it_names_the_side_service_requirements_files(self, todays_body: str) -> None:
        findings = "\n".join(_report(todays_body)["findings"])
        for requirements in (
            "docker/embedding-service/requirements.txt",
            "docker/reranker-service/requirements.txt",
            "src/inference-service/requirements.txt",
            "src/knowledge-service/requirements.txt",
        ):
            assert requirements in findings, f"{requirements} is read by pip_requirements but not reported"

    def test_it_does_not_report_unrelated_requirements_files(self, todays_body: str) -> None:
        """`docs/` and `tools/rag-eval/` are other trees and deliberately untouched (#1374)."""
        findings = "\n".join(_report(todays_body)["findings"])
        assert "docs/requirements.txt" not in findings
        assert "tools/rag-eval/requirements.txt" not in findings


class TestInjectedRepositoryProblems:
    """The `⚠️ WARN: pip-compile error` line, put back where nobody read it."""

    @staticmethod
    def _with_problems(body: str, *lines: str) -> str:
        block = "## Repository problems\n\nThese problems occurred while renovating this repository.\n\n"
        block += "".join(f"-   {line}\n" for line in lines)
        block += "\n"
        return body.replace("## Detected Dependencies", block + "## Detected Dependencies", 1)

    def test_a_warn_line_alerts(self, healthy_body: str) -> None:
        body = self._with_problems(healthy_body, "`WARN: pip-compile error`")
        report = _report(body)
        assert report["alert"] is True
        assert any("pip-compile error" in finding for finding in report["findings"])

    def test_an_error_line_alerts(self, healthy_body: str) -> None:
        body = self._with_problems(healthy_body, "`ERROR: Failed to look up dependency`")
        assert _report(body)["alert"] is True

    def test_the_line_is_quoted_verbatim(self, healthy_body: str) -> None:
        """Paraphrasing a Renovate diagnostic loses the only clue it carries."""
        body = self._with_problems(healthy_body, "`WARN: Package lookup failures` (`some-package`)")
        report = _report(body)
        assert any("`WARN: Package lookup failures` (`some-package`)" in f for f in report["findings"])

    def test_a_problems_section_without_a_severity_does_not_alert(self, healthy_body: str) -> None:
        """Renovate writes prose in that section too; only WARN/ERROR is a finding."""
        body = self._with_problems(healthy_body, "Renovate had nothing of note to report.")
        assert _report(body)["alert"] is False

    def test_a_warn_mentioned_outside_the_section_is_ignored(self, healthy_body: str) -> None:
        """Otherwise a pull-request title containing 'WARN' would alert forever."""
        body = healthy_body.replace(
            "## Detected Dependencies",
            "## Open\n\n - [ ] chore(deps): update WARN-detector to v2\n\n## Detected Dependencies",
            1,
        )
        assert _report(body)["alert"] is False


class TestInjectedInventoryDrift:
    """One injected defect at a time, each red for its own reason."""

    def test_a_poetry_entry_alerts(self, healthy_body: str) -> None:
        body = healthy_body.replace(
            "<details><summary>pre-commit (1)</summary>",
            "<details><summary>poetry (1)</summary>\n<blockquote>\n\n"
            "<details><summary>src/backend/pyproject.toml (1)</summary>\n\n - `fastapi >=0.115.0`\n\n"
            "</details>\n\n</blockquote>\n</details>\n\n"
            "<details><summary>pre-commit (1)</summary>",
            1,
        )
        report = _report(body)
        assert report["alert"] is True
        assert "poetry" in report["managers"]
        assert any("`poetry` appears in the inventory" in f for f in report["findings"])

    @pytest.mark.parametrize("dropped", check.EXPECTED_PEP621_FILES)
    def test_a_missing_side_service_file_alerts(self, healthy_body: str, dropped: str) -> None:
        """Every one of the five, not just a representative — that is the point of a strong expectation."""
        body = healthy_body.replace(f"<summary>{dropped} (", "<summary>some/other/pyproject.toml (", 1)
        report = _report(body)
        assert report["alert"] is True
        assert any(dropped in f and "does not list" in f for f in report["findings"]), report["findings"]

    def test_an_unknown_pep621_file_alerts(self, healthy_body: str) -> None:
        """A new Python tree must be declared, not absorbed silently."""
        body = healthy_body.replace(
            "<details><summary>src/backend/pyproject.toml (42)</summary>",
            "<details><summary>src/brand-new-service/pyproject.toml (1)</summary>\n\n - `fastapi >=0.1`\n\n"
            "</details>\n\n<details><summary>src/backend/pyproject.toml (42)</summary>",
            1,
        )
        report = _report(body)
        assert report["alert"] is True
        assert any("does not know about" in f for f in report["findings"])

    def test_a_reappearing_side_service_requirements_file_alerts(self, healthy_body: str) -> None:
        body = healthy_body.replace(
            "<details><summary>docs/requirements.txt (12)</summary>",
            "<details><summary>src/knowledge-service/requirements.txt (3)</summary>\n\n - `fastapi >=0.1`\n\n"
            "</details>\n\n<details><summary>docs/requirements.txt (12)</summary>",
            1,
        )
        report = _report(body)
        assert report["alert"] is True
        assert any("src/knowledge-service/requirements.txt" in f for f in report["findings"])

    def test_pep621_vanishing_entirely_alerts_loudly(self, healthy_body: str) -> None:
        """The exact shape of the six silent weeks."""
        body = healthy_body.replace("<summary>pep621 (7)</summary>", "<summary>pep666 (7)</summary>", 1)
        report = _report(body)
        assert report["alert"] is True
        assert any("absent from the inventory entirely" in f for f in report["findings"])

    def test_a_missing_lock_on_disk_alerts(self, healthy_body: str, tmp_path: Path) -> None:
        """The one fact the dashboard cannot carry, so it is read from the checkout."""
        for package_file in check.EXPECTED_PEP621_FILES:
            target = tmp_path / package_file
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("[project]\nname = 'x'\n")
        # Four of five get a lock; the backend deliberately does not.
        for package_file in check.EXPECTED_PEP621_FILES[1:]:
            (tmp_path / package_file).with_name("uv.lock").write_text("version = 1\n")

        report = check.build_report(healthy_body, repo_root=tmp_path)

        assert report["alert"] is True
        assert any("No uv.lock beside: src/backend/pyproject.toml" in f for f in report["findings"])
        assert report["locks_verified_on_disk"] == list(check.EXPECTED_PEP621_FILES[1:])


class TestUndeterminedIsNeverClean:
    """NFR-018 §2 — a check that cannot decide must go red, not green."""

    def test_an_empty_body_raises(self) -> None:
        with pytest.raises(check.DashboardError, match="empty"):
            _report("   \n  ")

    def test_a_body_without_the_detected_section_raises(self) -> None:
        with pytest.raises(check.DashboardError, match="Detected Dependencies"):
            _report("# Some issue\n\nNothing to see here.\n")

    def test_an_empty_detected_section_raises(self) -> None:
        with pytest.raises(check.DashboardError, match="no manager blocks"):
            _report("## Detected Dependencies\n\n(nothing)\n")

    def test_main_writes_no_report_when_undetermined(self, tmp_path: Path) -> None:
        report_path = tmp_path / "report.json"
        with pytest.raises(check.DashboardError):
            check.main([str(report_path)], body="", repo_root=_REPO_ROOT)
        assert not report_path.exists(), (
            "a report was written for an undetermined run — the workflow's issue step keys on the file's "
            "existence, so this would open an alert issue off a parse failure"
        )

    def test_main_writes_the_report_and_exits_zero_on_drift(self, todays_body: str, tmp_path: Path) -> None:
        """Drift is reported through the ISSUE, not through a red run (operator decision)."""
        report_path = tmp_path / "report.json"
        assert check.main([str(report_path)], body=todays_body, repo_root=_REPO_ROOT) == 0
        written = json.loads(report_path.read_text())
        assert written["alert"] is True
        assert written["findings"]
