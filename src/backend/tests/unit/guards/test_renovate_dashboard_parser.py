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

``renovate_dashboard_expected_after_1374.md`` is derived from it mechanically —
the two service ``pyproject.toml`` moved from ``poetry`` to ``pep621``, the four
deleted ``requirements.txt`` dropped, the two lock-less libraries left where
``task renovate:dry-run`` measured them. It WAS the healthy state; since #1464 it
is a drift fixture, and ``TestThePre1464BodyIsNowCorrectlyRed`` below is the
red-first proof for that change — six findings, each named.

``renovate_dashboard_expected_after_1464.md`` is derived from it the same way and
is the healthy state today: both libraries under ``pep621`` (seven trees), no
``poetry`` at all, and the three ``tests/e2e`` manifests that the ``ignorePaths``
override in ``renovate.json5`` admitted. Every number in it comes from
``task renovate:dry-run`` run before and after that override on 2026-09-17 —
``pep621`` 5 -> 7 files, ``poetry`` 2 -> absent, ``pip_requirements`` 2 -> 3,
``npm`` 1 -> 2, ``dockerfile`` 8 -> 9, total 80 -> 83 — not from a guess about
what Renovate would do.

**Two measurements corrected the plan, in this order.** The #1383 analysis said
``poetry`` read "exactly the two side-service pyproject.toml". The real body
shows **four**: ``src/libs/kp_errortracking`` and ``src/libs/kp_vectordb`` were
in there too. The first version of this file then assumed those two would move
under ``pep621`` once ``poetry`` was disabled repository-wide. ``task
renovate:dry-run`` (Renovate 44.94.1, 2026-09-16) says they do not —
``enabled: false`` disables a manager's dependencies without stopping its
extraction, so ``poetry`` keeps extracting exactly those two and ``pep621``
claims exactly the five trees that have a ``uv.lock``. A rule of the form
"``poetry`` must not appear" would have alerted on a correct repository every
day. The rule that survives the measurement is "no second manager inside a
LOCKED tree", and the two lock-less libraries were enumerated in
``LOCKLESS_PYTHON_PROJECTS`` rather than waved through.

**#1464 then removed the premise rather than the rule.** Both libraries got a
hash-bearing ``uv.lock``, so ``pep621`` claims them and ``poetry`` — which only
ever extracted trees without one — leaves the inventory entirely. That is a
CONSEQUENCE of locking them, measured after the fact, not a rule that
``poetry`` must be absent: the rule is still "no second manager inside a locked
tree", now over seven trees instead of five, and ``LOCKLESS_PYTHON_PROJECTS`` is
empty.

The healthy fixture is built to that measurement, not to the guess.

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
_PRE_1464 = _FIXTURES / "renovate_dashboard_expected_after_1374.md"
_HEALTHY = _FIXTURES / "renovate_dashboard_expected_after_1464.md"


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


@pytest.fixture
def pre_1464_body() -> str:
    """The state that was healthy BEFORE #1464 — and must not be, after it."""
    return _PRE_1464.read_text()


def _report(body: str) -> dict:
    return check.build_report(body, repo_root=_REPO_ROOT)


class TestTheFixturesAreTheRealThing:
    """A fixture that drifted from the source is a certificate of nothing."""

    def test_both_fixtures_exist_and_are_substantial(self) -> None:
        for fixture in (_TODAY, _PRE_1464, _HEALTHY):
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

    def test_the_healthy_fixture_matches_the_dry_run_measurement(self, healthy_body: str) -> None:
        """`task renovate:dry-run`, Renovate 44.94.1, 2026-09-17 — the numbers this fixture encodes.

        Compared as SETS, not as lists. The dashboard's ordering within a manager
        is Renovate's rendering detail and differs from the order the same run's
        JSON extract dump uses (measured on 2026-09-17: the dump sorts by path,
        the dashboard does not). :func:`check.build_report` reads membership and
        never order, so asserting a list here would make a correct repository red
        on a day Renovate changed how it sorts — a defect in the measuring tool,
        not in the thing measured.
        """
        inventory = check.manager_inventory(healthy_body)
        assert set(inventory["pep621"]) == set(check.EXPECTED_PEP621_FILES), (
            "the dry-run measured pep621 extracting exactly the seven locked trees; "
            f"the fixture says {inventory['pep621']}"
        )
        assert "poetry" not in inventory, (
            "the dry-run measured poetry leaving the inventory entirely once both shared libraries got a "
            "uv.lock (#1464) — it only ever extracted the two lock-less ones; "
            f"the fixture says {inventory.get('poetry')}"
        )
        assert inventory["pip_requirements"] == [
            "docs/requirements.txt",
            "tests/e2e/requirements.txt",
            "tools/rag-eval/requirements.txt",
        ]
        assert inventory["npm"] == ["src/frontend/package.json", "tests/e2e/package.json"]

    def test_no_python_tree_in_the_checkout_is_lockless(self) -> None:
        """#1464's own acceptance criterion, measured against the filesystem."""
        assert check.lockless_python_trees(_REPO_ROOT) == [], (
            "a pyproject.toml without a uv.lock beside it. LOCKLESS_PYTHON_PROJECTS is empty on purpose: "
            "every Python tree here installs from a hash-bearing lock (NFR-009 §2.3)."
        )

    def test_the_lockless_allowance_is_still_empty(self) -> None:
        """An allowance register is how a workaround becomes the design (CI spec §H)."""
        assert check.LOCKLESS_PYTHON_PROJECTS == (), (
            f"LOCKLESS_PYTHON_PROJECTS has grown back to {check.LOCKLESS_PYTHON_PROJECTS}. #1464 emptied it; "
            "a tree added here needs its argument in writing, not a line in a tuple."
        )

    def test_the_sweep_sees_every_python_tree_in_the_checkout(self) -> None:
        """Otherwise `lockless_python_trees() == []` could be green having looked at nothing."""
        swept = {
            path.relative_to(_REPO_ROOT).as_posix()
            for path in _REPO_ROOT.rglob("pyproject.toml")
            if not check._SWEEP_EXCLUDED.intersection(path.relative_to(_REPO_ROOT).parts)
        }
        assert swept == set(check.EXPECTED_PEP621_FILES), (
            f"the checkout holds {sorted(swept)} but EXPECTED_PEP621_FILES names "
            f"{sorted(check.EXPECTED_PEP621_FILES)}. A Python tree that is in one and not the other is "
            "either unobserved by Renovate or an expectation with nothing behind it."
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
        assert "pip-compile" not in report["managers"]
        assert "poetry" not in report["managers"], (
            "the healthy state has NO poetry manager since #1464: it only ever extracted the two shared "
            "libraries, and it extracted them because they had no lock. A poetry that reappears means a "
            "lock was removed."
        )
        assert report["observed_files"]["npm"] == ["src/frontend/package.json", "tests/e2e/package.json"], (
            "green because it looked at the E2E suite too — `tests/e2e` sat behind an inherited "
            "`ignorePaths` rule until #1464 and its absence produced no signal at all."
        )
        assert len(report["managers"]) > 5, f"only {report['managers']} — suspiciously few managers parsed"

    def test_the_render_says_so(self, healthy_body: str) -> None:
        assert "healthy" in check.render(_report(healthy_body))


class TestTodaysRealBodyIsCorrectlyRed:
    """Issue #12 as of 2026-09-16 — before #1374 reached develop."""

    def test_it_alerts(self, todays_body: str) -> None:
        report = _report(todays_body)
        assert report["alert"] is True

    def test_it_names_poetry_on_the_locked_trees_and_the_missing_ones(self, todays_body: str) -> None:
        findings = "\n".join(_report(todays_body)["findings"])
        assert "`poetry` reads src/inference-service/pyproject.toml" in findings
        assert "`poetry` reads src/knowledge-service/pyproject.toml" in findings
        assert "docker/reranker-service/pyproject.toml" in findings

    def test_it_now_blames_poetry_for_the_two_shared_libraries_as_well(self, todays_body: str) -> None:
        """Tolerated until #1464, a finding after it — the libraries have locks now."""
        findings = "\n".join(_report(todays_body)["findings"])
        for library in ("src/libs/kp_vectordb/pyproject.toml", "src/libs/kp_errortracking/pyproject.toml"):
            assert f"`poetry` reads {library}" in findings, (
                f"{library} carries a uv.lock since #1464, so a second manager on it is #1371 verbatim — "
                "the same rule that already covered the four service images"
            )

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


class TestThePre1464BodyIsNowCorrectlyRed:
    """The RED-FIRST proof for #1464, and it is a whole fixture rather than a flag.

    ``renovate_dashboard_expected_after_1374.md`` was the healthy state until
    #1464: two shared libraries under ``poetry`` with no lock, and no ``tests/e2e``
    anywhere. Every rule this change adds has to turn exactly that body red, and
    each for its own named reason — otherwise the new green fixture certifies
    only that a fixture was written to match a checker.
    """

    def test_it_alerts(self, pre_1464_body: str) -> None:
        assert _report(pre_1464_body)["alert"] is True

    def test_it_names_the_two_libraries_as_missing_from_pep621(self, pre_1464_body: str) -> None:
        findings = "\n".join(_report(pre_1464_body)["findings"])
        assert "`pep621` does not list: src/libs/kp_vectordb/pyproject.toml" in findings
        assert "src/libs/kp_errortracking/pyproject.toml" in findings

    def test_it_names_poetry_on_both_libraries(self, pre_1464_body: str) -> None:
        """They are LOCKED trees now, so a second manager on them is #1371 verbatim."""
        findings = "\n".join(_report(pre_1464_body)["findings"])
        assert "`poetry` reads src/libs/kp_vectordb/pyproject.toml" in findings
        assert "`poetry` reads src/libs/kp_errortracking/pyproject.toml" in findings

    @pytest.mark.parametrize(
        ("manager", "package_file"),
        [
            ("pip_requirements", "tests/e2e/requirements.txt"),
            ("npm", "tests/e2e/package.json"),
            ("dockerfile", "tests/e2e/Dockerfile"),
        ],
    )
    def test_it_names_every_unobserved_e2e_manifest(self, pre_1464_body: str, manager: str, package_file: str) -> None:
        """An ignored path emits nothing at all; this is the only side it is visible from."""
        findings = "\n".join(_report(pre_1464_body)["findings"])
        assert f"`{manager}` does not read {package_file}" in findings

    def test_it_is_red_for_exactly_the_reasons_this_change_closes(self, pre_1464_body: str) -> None:
        """No stray extra finding — otherwise the fixture is describing a second defect."""
        assert len(_report(pre_1464_body)["findings"]) == 6, _report(pre_1464_body)["findings"]


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

    def test_poetry_reaching_into_a_locked_tree_alerts(self, healthy_body: str) -> None:
        """#1371 verbatim: a second manager on a tree that has a lock."""
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
        assert any("`poetry` reads src/backend/pyproject.toml" in f for f in report["findings"])

    def test_pip_compile_reappearing_alerts(self, healthy_body: str) -> None:
        """The manager whose six silent weeks this whole lane exists for."""
        body = healthy_body.replace(
            "<details><summary>pre-commit (1)</summary>",
            "<details><summary>pip-compile (1)</summary>\n<blockquote>\n\n"
            "<details><summary>src/backend/requirements.txt (1)</summary>\n\n - `fastapi ==0.115.0`\n\n"
            "</details>\n\n</blockquote>\n</details>\n\n"
            "<details><summary>pre-commit (1)</summary>",
            1,
        )
        report = _report(body)
        assert report["alert"] is True
        assert any("`pip-compile` appears in the inventory" in f for f in report["findings"])

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
        # Every tree but the backend gets a lock; the backend deliberately does not.
        for package_file in check.EXPECTED_PEP621_FILES[1:]:
            (tmp_path / package_file).with_name("uv.lock").write_text("version = 1\n")

        report = check.build_report(healthy_body, repo_root=tmp_path)

        assert report["alert"] is True
        assert any("No uv.lock beside: src/backend/pyproject.toml" in f for f in report["findings"])
        assert report["locks_verified_on_disk"] == list(check.EXPECTED_PEP621_FILES[1:])


class TestTheBodyArrivesThroughAFile:
    """The ~900-line body is passed by PATH, not as one env/argv string.

    ``MAX_ARG_STRLEN`` caps a single argument (and, in practice, a single
    environment entry) at 128 KiB on Linux. The dashboard body is ~30 KiB today
    and grows with every package file Renovate learns about, so the env route
    has a ceiling that would be reached on a day nothing in this repository
    changed — an ``E2BIG`` in a lane whose whole purpose is to notice silence.
    """

    def test_body_file_is_read_and_the_report_is_written(self, tmp_path: Path) -> None:
        body_file = tmp_path / "dashboard-body.md"
        body_file.write_text(_HEALTHY.read_text(), encoding="utf-8")
        report_path = tmp_path / "report.json"

        assert check.main(["--body-file", str(body_file), str(report_path)], repo_root=_REPO_ROOT) == 0

        written = json.loads(report_path.read_text())
        assert written["alert"] is False, f"the healthy fixture read from a file alerted: {written['findings']}"
        assert set(written["pep621_files"]) == set(check.EXPECTED_PEP621_FILES)

    def test_a_body_far_past_the_env_ceiling_still_goes_through(self, tmp_path: Path) -> None:
        """The ceiling the file route exists to clear, exercised rather than asserted in prose.

        The padding is plain prose placed BEFORE the first heading, so the parser
        sees the same sections — the point under test is the transport, not the
        grammar.
        """
        padding = ("Renovate prose that is not a heading and carries no WARN or ERROR token.\n") * 2000
        body = padding + _HEALTHY.read_text()
        assert len(body.encode()) > 128 * 1024, (
            "the padded body is smaller than MAX_ARG_STRLEN, so this test would pass through the env "
            "route as well and prove nothing about the file route"
        )

        body_file = tmp_path / "huge-dashboard-body.md"
        body_file.write_text(body, encoding="utf-8")
        report_path = tmp_path / "report.json"

        assert check.main(["--body-file", str(body_file), str(report_path)], repo_root=_REPO_ROOT) == 0
        assert json.loads(report_path.read_text())["alert"] is False

    def test_an_unreadable_body_file_is_undetermined_and_writes_no_report(self, tmp_path: Path) -> None:
        report_path = tmp_path / "report.json"
        with pytest.raises(check.DashboardError, match="could not be read"):
            check.main(["--body-file", str(tmp_path / "never-fetched.md"), str(report_path)], repo_root=_REPO_ROOT)
        assert not report_path.exists(), (
            "a report was written although the body file was never fetched — the workflow's issue step "
            "keys on that file's existence, so this would open an alert issue off a failed download"
        )

    def test_the_workflow_really_invokes_the_script_that_way(self) -> None:
        """The lane and this suite must reach the script through the SAME door.

        Without this, the tests above could certify a ``--body-file`` path that
        the workflow does not use — the recurring failure class here (a test that
        reaches the rule by a route production never takes).
        """
        workflow = (_REPO_ROOT / ".github" / "workflows" / "renovate-health.yml").read_text()
        assert "--body-file dashboard-body.md" in workflow, (
            "renovate-health.yml does not hand the body to check_renovate_dashboard.py by file path; the "
            "--body-file tests above would then measure a door nobody walks through"
        )
        assert "RENOVATE_DASHBOARD_BODY=" not in workflow, (
            "renovate-health.yml still builds RENOVATE_DASHBOARD_BODY from the body — that is the "
            "MAX_ARG_STRLEN route this change removed"
        )


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
